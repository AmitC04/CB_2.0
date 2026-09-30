"""Direct SQLite persistence for personas, documents, and extractions."""

import json
import sqlite3
from datetime import date
from typing import Any

from app.db import get_connection
from app.detection import (
    DISCLAIMER,
    RULES_VERSION,
    FieldRecord,
    Finding,
    PersonaContext,
    normalize_text,
)
from app.models import (
    DetectionRunRead,
    DocumentRead,
    ExtractionResult,
    PersonaCreate,
    PersonaRead,
)
from app.scoring import breakdown_from_pairs
from app.uploads import ValidatedUpload


class RecordNotFoundError(LookupError):
    pass


class ExtractionInProgressError(RuntimeError):
    pass


class NoEditToUndoError(LookupError):
    pass


def create_persona(data: PersonaCreate) -> PersonaRead:
    aliases_json = json.dumps(data.manually_confirmed_aliases)
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO personas (
                name, description, owner_has_family, marriage_date,
                family_context_source_text, manually_confirmed_aliases_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                data.name,
                data.description,
                data.owner_has_family.value,
                data.marriage_date.isoformat() if data.marriage_date else None,
                data.family_context_source_text,
                aliases_json,
            ),
        )
        persona_id = cursor.lastrowid
    return get_persona(int(persona_id))


def get_persona(persona_id: int) -> PersonaRead:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM personas WHERE id = ?",
            (persona_id,),
        ).fetchone()
    if row is None:
        raise RecordNotFoundError(f"Persona {persona_id} not found")
    return PersonaRead(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        owner_has_family=row["owner_has_family"],
        marriage_date=row["marriage_date"],
        family_context_source_text=row["family_context_source_text"],
        manually_confirmed_aliases=json.loads(row["manually_confirmed_aliases_json"]),
        created_at=row["created_at"],
    )


def create_document(
    persona_id: int,
    upload: ValidatedUpload,
    storage_key: str,
) -> int:
    get_persona(persona_id)
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO documents (
                persona_id, original_filename, mime_type, storage_path,
                content_sha256, size_bytes, synthetic_confirmed
            ) VALUES (?, ?, ?, ?, ?, ?, 1)
            """,
            (
                persona_id,
                upload.original_filename,
                upload.mime_type,
                storage_key,
                upload.content_sha256,
                upload.size_bytes,
            ),
        )
        return int(cursor.lastrowid)


def mark_extracting(document_id: int, *, retry: bool = False) -> None:
    retry_increment = 1 if retry else 0
    with get_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            "SELECT status FROM documents WHERE id = ?",
            (document_id,),
        ).fetchone()
        if row is None:
            raise RecordNotFoundError(f"Document {document_id} not found")
        if row["status"] == "extracting":
            raise ExtractionInProgressError(
                f"Document {document_id} extraction is already in progress"
            )
        connection.execute(
            """
            UPDATE documents
            SET status = 'extracting', error_code = NULL,
                retry_count = retry_count + ?
            WHERE id = ?
            """,
            (retry_increment, document_id),
        )


def save_extraction(
    document_id: int,
    result: ExtractionResult,
    *,
    model_name: str,
) -> None:
    validated_json = result.model_dump_json()
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM extracted_fields WHERE document_id = ?",
            (document_id,),
        )
        for field in result.fields:
            connection.execute(
                """
                INSERT INTO extracted_fields (
                    document_id, document_group_id, asset_type, institution_name,
                    asset_reference, person_name, relationship, mechanism,
                    share_percent, source_text, source_locator, confidence,
                    registration_status, registration_date,
                    explicit_nomination_action, policy_kind,
                    mwpa_section_6_applies, assignment_status, holding_pattern
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    field.document_group_id,
                    field.asset_type.value,
                    field.institution_name,
                    field.asset_reference,
                    field.named_person,
                    field.relationship,
                    field.mechanism_type.value,
                    field.share_percent,
                    field.source_text,
                    field.source_locator,
                    field.confidence,
                    field.registration_status.value,
                    field.registration_date.isoformat() if field.registration_date else None,
                    field.explicit_nomination_action.value,
                    field.policy_kind.value,
                    field.mwpa_section_6_applies.value,
                    field.assignment_status.value,
                    field.holding_pattern.value,
                ),
            )
        connection.execute(
            """
            UPDATE documents
            SET doc_type = ?, document_date = ?, status = 'extracted',
                extraction_source = 'gemini', model_name = ?,
                raw_extraction_json = ?, error_code = NULL,
                extracted_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
            WHERE id = ?
            """,
            (
                result.document_type.value,
                result.document_date.isoformat() if result.document_date else None,
                model_name,
                validated_json,
                document_id,
            ),
        )


def mark_extraction_failed(document_id: int, error_code: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM extracted_fields WHERE document_id = ?",
            (document_id,),
        )
        cursor = connection.execute(
            """
            UPDATE documents
            SET status = 'failed', extraction_source = NULL,
                model_name = NULL, raw_extraction_json = NULL,
                error_code = ?, extracted_at = NULL
            WHERE id = ?
            """,
            (error_code, document_id),
        )
        if cursor.rowcount == 0:
            raise RecordNotFoundError(f"Document {document_id} not found")


def get_document(document_id: int) -> DocumentRead:
    with get_connection() as connection:
        document = connection.execute(
            "SELECT * FROM documents WHERE id = ?",
            (document_id,),
        ).fetchone()
        if document is None:
            raise RecordNotFoundError(f"Document {document_id} not found")
        field_rows = connection.execute(
            "SELECT * FROM extracted_fields WHERE document_id = ? ORDER BY id",
            (document_id,),
        ).fetchall()

    raw_result: dict[str, Any] = {}
    if document["raw_extraction_json"]:
        raw_result = json.loads(document["raw_extraction_json"])

    fields = [
        {
            "id": row["id"],
            "document_id": row["document_id"],
            "document_group_id": row["document_group_id"],
            "asset_type": row["asset_type"],
            "institution_name": row["institution_name"],
            "asset_reference": row["asset_reference"],
            "named_person": row["person_name"],
            "relationship": row["relationship"],
            "mechanism_type": row["mechanism"],
            "share_percent": row["share_percent"],
            "source_text": row["source_text"],
            "source_locator": row["source_locator"],
            "confidence": row["confidence"],
            "registration_status": row["registration_status"],
            "registration_date": row["registration_date"],
            "explicit_nomination_action": row["explicit_nomination_action"],
            "policy_kind": row["policy_kind"],
            "mwpa_section_6_applies": row["mwpa_section_6_applies"],
            "assignment_status": row["assignment_status"],
            "holding_pattern": row["holding_pattern"],
            "is_user_edited": bool(row["is_user_edited"]),
        }
        for row in field_rows
    ]
    return DocumentRead(
        id=document["id"],
        persona_id=document["persona_id"],
        original_filename=document["original_filename"],
        mime_type=document["mime_type"],
        content_sha256=document["content_sha256"],
        size_bytes=document["size_bytes"],
        synthetic_confirmed=bool(document["synthetic_confirmed"]),
        document_type=document["doc_type"],
        document_date=document["document_date"],
        status=document["status"],
        extraction_source=document["extraction_source"],
        model_name=document["model_name"],
        error_code=document["error_code"],
        retry_count=document["retry_count"],
        uploaded_at=document["uploaded_at"],
        extracted_at=document["extracted_at"],
        classification_confidence=raw_result.get("classification_confidence"),
        warnings=raw_result.get("warnings", []),
        fields=fields,
        disclaimer=DISCLAIMER,
    )


def list_documents(persona_id: int) -> list[DocumentRead]:
    get_persona(persona_id)
    with get_connection() as connection:
        ids = [
            row["id"]
            for row in connection.execute(
                "SELECT id FROM documents WHERE persona_id = ? ORDER BY uploaded_at, id",
                (persona_id,),
            )
        ]
    return [get_document(document_id) for document_id in ids]


def get_document_storage(document_id: int) -> tuple[str, str]:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT storage_path, mime_type FROM documents WHERE id = ?",
            (document_id,),
        ).fetchone()
    if row is None:
        raise RecordNotFoundError(f"Document {document_id} not found")
    return row["storage_path"], row["mime_type"]


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def load_persona_context(persona_id: int) -> PersonaContext:
    persona = get_persona(persona_id)
    aliases = frozenset(
        frozenset({normalize_text(left), normalize_text(right)})
        for left, right in persona.manually_confirmed_aliases
    )
    return PersonaContext(
        owner_has_family=persona.owner_has_family.value,
        marriage_date=persona.marriage_date,
        family_context_source_text=persona.family_context_source_text,
        confirmed_aliases=aliases,
    )


def load_field_records(persona_id: int) -> list[FieldRecord]:
    get_persona(persona_id)
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT f.*, d.doc_type, d.document_date, d.status
            FROM extracted_fields AS f
            JOIN documents AS d ON d.id = f.document_id
            WHERE d.persona_id = ? AND d.status = 'extracted'
            ORDER BY f.id
            """,
            (persona_id,),
        ).fetchall()

    return [
        FieldRecord(
            field_id=row["id"],
            document_id=row["document_id"],
            document_type=row["doc_type"] or "unknown",
            document_date=_parse_date(row["document_date"]),
            document_group_id=row["document_group_id"],
            asset_type=row["asset_type"],
            institution_name=row["institution_name"],
            asset_reference=row["asset_reference"],
            named_person=row["person_name"],
            relationship=row["relationship"],
            mechanism_type=row["mechanism"],
            share_percent=row["share_percent"],
            source_text=row["source_text"],
            source_locator=row["source_locator"],
            registration_status=row["registration_status"],
            registration_date=_parse_date(row["registration_date"]),
            explicit_nomination_action=row["explicit_nomination_action"],
            policy_kind=row["policy_kind"],
            mwpa_section_6_applies=row["mwpa_section_6_applies"],
            assignment_status=row["assignment_status"],
            holding_pattern=row["holding_pattern"],
        )
        for row in rows
    ]


def save_detection_run(
    persona_id: int,
    findings: list[tuple[Finding, tuple[str | None, str | None, str | None] | None]],
    readiness_score: int | None = None,
) -> int:
    """Persist one detection run and its findings.

    ``findings`` pairs each deterministic finding with an optional
    ``(explanation, suggested_fix, explanation_source)`` triple.
    """
    get_persona(persona_id)
    with get_connection() as connection:
        run_id = int(
            connection.execute(
                """
                INSERT INTO detection_runs (persona_id, rules_version, readiness_score)
                VALUES (?, ?, ?)
                """,
                (persona_id, RULES_VERSION, readiness_score),
            ).lastrowid
        )
        for finding, explanation in findings:
            explanation_text, suggested_fix, explanation_source = (
                explanation if explanation else (None, None, None)
            )
            connection.execute(
                """
                INSERT INTO conflicts (
                    run_id, rules_version, rule_id, finding_type, severity,
                    asset_type, asset_reference,
                    field_a_id, source_a_label, source_a_locator, source_a_text,
                    field_b_id, source_b_label, source_b_locator, source_b_text,
                    summary, legal_scope_note, suggested_actions_json,
                    explanation, suggested_fix, explanation_source, disclaimer
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    finding.rules_version,
                    finding.rule_id,
                    finding.finding_type,
                    finding.severity,
                    finding.asset_type,
                    finding.asset_reference,
                    finding.source_a.field_id,
                    finding.source_a.label,
                    finding.source_a.locator,
                    finding.source_a.text,
                    finding.source_b.field_id if finding.source_b else None,
                    finding.source_b.label if finding.source_b else None,
                    finding.source_b.locator if finding.source_b else None,
                    finding.source_b.text if finding.source_b else None,
                    finding.summary,
                    finding.legal_scope_note,
                    json.dumps(list(finding.suggested_actions)),
                    explanation_text,
                    suggested_fix,
                    explanation_source,
                    finding.disclaimer,
                ),
            )
        return run_id


def _finding_row_to_read(row: Any) -> dict[str, Any]:
    source_b = None
    if row["source_b_label"] is not None:
        source_b = {
            "label": row["source_b_label"],
            "locator": row["source_b_locator"] or "",
            "text": row["source_b_text"] or "",
            "field_id": row["field_b_id"],
        }
    return {
        "id": row["id"],
        "rule_id": row["rule_id"],
        "rules_version": row["rules_version"],
        "finding_type": row["finding_type"],
        "severity": row["severity"],
        "asset_type": row["asset_type"],
        "asset_reference": row["asset_reference"],
        "summary": row["summary"],
        "legal_scope_note": row["legal_scope_note"],
        "suggested_actions": json.loads(row["suggested_actions_json"]),
        "source_a": {
            "label": row["source_a_label"],
            "locator": row["source_a_locator"],
            "text": row["source_a_text"],
            "field_id": row["field_a_id"],
        },
        "source_b": source_b,
        "explanation": row["explanation"],
        "suggested_fix": row["suggested_fix"],
        "explanation_source": row["explanation_source"],
        "disclaimer": row["disclaimer"],
    }


def get_detection_run(run_id: int) -> DetectionRunRead:
    with get_connection() as connection:
        run = connection.execute(
            "SELECT * FROM detection_runs WHERE id = ?",
            (run_id,),
        ).fetchone()
        if run is None:
            raise RecordNotFoundError(f"Detection run {run_id} not found")
        rows = connection.execute(
            "SELECT * FROM conflicts WHERE run_id = ? ORDER BY id",
            (run_id,),
        ).fetchall()

    findings = [_finding_row_to_read(row) for row in rows]
    breakdown = breakdown_from_pairs(
        (finding["finding_type"], finding["severity"]) for finding in findings
    )
    return DetectionRunRead(
        id=run["id"],
        persona_id=run["persona_id"],
        rules_version=run["rules_version"],
        readiness_score=run["readiness_score"],
        score_breakdown=breakdown,
        run_at=run["run_at"],
        disclaimer=DISCLAIMER,
        conflicts=[f for f in findings if f["finding_type"] != "scope_gap"],
        scope_gaps=[f for f in findings if f["finding_type"] == "scope_gap"],
    )


def get_latest_detection_run(persona_id: int) -> DetectionRunRead:
    get_persona(persona_id)
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id FROM detection_runs WHERE persona_id = ? ORDER BY id DESC LIMIT 1",
            (persona_id,),
        ).fetchone()
    if row is None:
        raise RecordNotFoundError(f"No detection run exists for persona {persona_id}")
    return get_detection_run(int(row["id"]))


def list_personas() -> list[PersonaRead]:
    with get_connection() as connection:
        ids = [
            int(row["id"])
            for row in connection.execute("SELECT id FROM personas ORDER BY id")
        ]
    return [get_persona(persona_id) for persona_id in ids]


def update_extracted_field(
    field_id: int,
    *,
    named_person: str | None = None,
    relationship: str | None = None,
) -> tuple[int, int]:
    """Apply a simulated synthetic correction; return (persona_id, document_id)."""
    updates: list[str] = []
    values: list[Any] = []
    if named_person is not None:
        updates.append("person_name = ?")
        values.append(named_person.strip())
    if relationship is not None:
        updates.append("relationship = ?")
        values.append(relationship.strip())
    if not updates:
        raise ValueError("No field values were supplied")

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT d.persona_id AS persona_id, f.document_id AS document_id,
                   f.person_name AS person_name, f.relationship AS relationship
            FROM extracted_fields AS f
            JOIN documents AS d ON d.id = f.document_id
            WHERE f.id = ?
            """,
            (field_id,),
        ).fetchone()
        if row is None:
            raise RecordNotFoundError(f"Extracted field {field_id} not found")

        # Saving the same value is not an edit. Recording one would badge the field as
        # edited and claim the value was changed in this demo when nothing changed.
        unchanged = (
            named_person is None or named_person.strip() == row["person_name"]
        ) and (relationship is None or relationship.strip() == row["relationship"])
        if unchanged:
            return int(row["persona_id"]), int(row["document_id"])

        connection.execute(
            f"""
            UPDATE extracted_fields
            SET {", ".join(updates)},
                is_user_edited = 1,
                updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
            WHERE id = ?
            """,
            (*values, field_id),
        )
        updated = connection.execute(
            "SELECT person_name, relationship FROM extracted_fields WHERE id = ?",
            (field_id,),
        ).fetchone()
        connection.execute(
            """
            INSERT INTO field_edits (
                field_id, previous_person_name, previous_relationship,
                new_person_name, new_relationship
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                field_id,
                row["person_name"],
                row["relationship"],
                updated["person_name"],
                updated["relationship"],
            ),
        )
        return int(row["persona_id"]), int(row["document_id"])


def undo_last_field_edit(field_id: int) -> tuple[int, int]:
    """Revert the most recent simulated fix. Returns (persona_id, document_id)."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT d.persona_id AS persona_id, f.document_id AS document_id
            FROM extracted_fields AS f
            JOIN documents AS d ON d.id = f.document_id
            WHERE f.id = ?
            """,
            (field_id,),
        ).fetchone()
        if row is None:
            raise RecordNotFoundError(f"Extracted field {field_id} not found")

        edit = connection.execute(
            """
            SELECT id, previous_person_name, previous_relationship
            FROM field_edits
            WHERE field_id = ? AND undone_at IS NULL
            ORDER BY id DESC
            LIMIT 1
            """,
            (field_id,),
        ).fetchone()
        if edit is None:
            raise NoEditToUndoError(f"Extracted field {field_id} has no edit to undo")

        remaining = connection.execute(
            """
            SELECT COUNT(*) AS n FROM field_edits
            WHERE field_id = ? AND undone_at IS NULL AND id < ?
            """,
            (field_id, edit["id"]),
        ).fetchone()["n"]

        connection.execute(
            """
            UPDATE extracted_fields
            SET person_name = ?, relationship = ?, is_user_edited = ?,
                updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
            WHERE id = ?
            """,
            (
                edit["previous_person_name"],
                edit["previous_relationship"],
                1 if remaining else 0,
                field_id,
            ),
        )
        connection.execute(
            """
            UPDATE field_edits
            SET undone_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
            WHERE id = ?
            """,
            (edit["id"],),
        )
        return int(row["persona_id"]), int(row["document_id"])


def has_user_edited_fields(document_id: int) -> bool:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT COUNT(*) AS edited
            FROM extracted_fields
            WHERE document_id = ? AND is_user_edited = 1
            """,
            (document_id,),
        ).fetchone()
    return bool(row["edited"])
