"""Reset and seed the synthetic demo personas.

Two modes:

* ``live`` uploads the Phase 3 synthetic PDFs through the real upload and Gemini
  extraction pipeline.
* ``fallback`` inserts a pre-verified snapshot of earlier live extraction output and
  records ``extraction_source='manual_fallback'`` so the interface never presents it as
  a live AI result. This is the documented mitigation for an API outage during a demo.

Everything here is synthetic. The reset deletes only generated files under the ignored
data directory.
"""

import json
import shutil
from pathlib import Path

from app.db import get_connection, get_database_path, init_db
from app.detection import detect, finalize
from app.repository import (
    load_field_records,
    load_persona_context,
    save_detection_run,
)
from app.scoring import completeness_gaps, readiness_score
from app.uploads import get_upload_dir

FALLBACK_PATH = Path(__file__).with_name("demo_fallback.json")
PERSONA_KEYS = ("conflict_persona", "clean_persona", "nps_persona", "joint_persona")


def seed_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "seed_data"
        if (candidate / "expected_extractions.json").exists():
            return candidate
    raise FileNotFoundError("seed_data was not found")


def reset_storage() -> None:
    """Delete the generated synthetic database and uploads, then recreate the schema."""
    database_path = get_database_path()
    database_path.unlink(missing_ok=True)
    upload_dir = get_upload_dir()
    if upload_dir.exists():
        shutil.rmtree(upload_dir)
    init_db()


def _insert_persona(connection, persona: dict) -> int:
    """Insert a persona including its confirmed context.

    ``owner_has_family`` and ``marriage_date`` are stated facts on the persona record, never
    extracted from a document, because the NPS validity rule may not infer a marriage from
    silence. Without them NPS-VALIDITY-001 cannot fire for a seeded persona at all.
    """
    context = persona.get("persona_context") or {}
    return int(
        connection.execute(
            """
            INSERT INTO personas (
                name, description, owner_has_family, marriage_date,
                family_context_source_text
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                persona["name"],
                persona.get("description"),
                context.get("owner_has_family") or "unknown",
                context.get("marriage_date"),
                context.get("family_context_source_text"),
            ),
        ).lastrowid
    )


def seed_fallback() -> dict[str, int]:
    """Insert the pre-verified extraction snapshot. No AI call is made."""
    snapshot = json.loads(FALLBACK_PATH.read_text(encoding="utf-8"))
    persona_ids: dict[str, int] = {}

    with get_connection() as connection:
        for key in PERSONA_KEYS:
            persona = snapshot[key]
            persona_id = _insert_persona(connection, persona)
            persona_ids[key] = persona_id

            for index, document in enumerate(persona["documents"], start=1):
                document_id = int(
                    connection.execute(
                        """
                        INSERT INTO documents (
                            persona_id, original_filename, mime_type, storage_path,
                            content_sha256, size_bytes, synthetic_confirmed,
                            doc_type, document_date, status,
                            extraction_source, model_name
                        ) VALUES (?, ?, 'application/pdf', ?, ?, ?, 1, ?, ?,
                                  'extracted', 'manual_fallback', 'pre-verified snapshot')
                        """,
                        (
                            persona_id,
                            document["original_filename"],
                            f"fallback-{key}-{index}.pdf",
                            f"{persona_id:032d}{index:032d}",
                            1024,
                            document["document_type"],
                            document["document_date"],
                        ),
                    ).lastrowid
                )
                for field in document["fields"]:
                    connection.execute(
                        """
                        INSERT INTO extracted_fields (
                            document_id, document_group_id, asset_type, institution_name,
                            asset_reference, person_name, relationship, mechanism,
                            share_percent, source_text, source_locator, confidence,
                            registration_status, registration_date,
                            explicit_nomination_action, policy_kind,
                            mwpa_section_6_applies, assignment_status,
                            holding_pattern
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            document_id,
                            field["document_group_id"],
                            field["asset_type"],
                            field["institution_name"],
                            field["asset_reference"],
                            field["named_person"],
                            field["relationship"],
                            field["mechanism_type"],
                            field["share_percent"],
                            field["source_text"],
                            field["source_locator"],
                            field["confidence"],
                            field["registration_status"],
                            field["registration_date"],
                            field["explicit_nomination_action"],
                            field["policy_kind"],
                            field["mwpa_section_6_applies"],
                            field["assignment_status"],
                            field["holding_pattern"],
                        ),
                    )
    return persona_ids


def run_detection(persona_id: int) -> int:
    """Run the deterministic engine and store the score. No AI wording is requested."""
    context = load_persona_context(persona_id)
    records = load_field_records(persona_id)
    result = detect(records, context)
    findings = finalize(result.findings + completeness_gaps(records, result.findings))
    score = readiness_score(findings)
    save_detection_run(
        persona_id,
        [(finding, None) for finding in findings],
        readiness_score=score,
    )
    return score


def ensure_demo_seeded() -> dict[str, int]:
    """Seed the fallback demo only if the database holds no personas yet.

    Hosted free-tier instances have no persistent disk, so the SQLite file is lost on
    every restart and cold start. This makes a fresh instance self-seeding instead of
    presenting an empty vault. It never resets or overwrites existing data, and it never
    calls the AI: the data it inserts is the pre-verified snapshot, still labelled
    ``manual_fallback`` so the interface does not present it as a live extraction.
    """
    with get_connection() as connection:
        existing = int(
            connection.execute("SELECT COUNT(*) AS n FROM personas").fetchone()["n"]
        )
    if existing:
        return {}

    persona_ids = seed_fallback()
    for persona_id in persona_ids.values():
        run_detection(persona_id)
    return persona_ids
