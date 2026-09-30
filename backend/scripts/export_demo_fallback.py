"""Regenerate app/demo_fallback.json from a live-extracted synthetic database.

The fallback snapshot exists so the demo runs without an API key. It must always be a
record of real extraction output, never hand-written values, otherwise the
``manual_fallback`` label would be misleading. Regenerate it after a live seed:

    DATABASE_PATH=... python scripts/seed_demo.py --yes --mode live
    DATABASE_PATH=... python scripts/export_demo_fallback.py

Only synthetic seed documents are ever involved.
"""

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import get_database_path  # noqa: E402
from app.demo_seed import FALLBACK_PATH, PERSONA_KEYS  # noqa: E402

#: Persona order matches PERSONA_KEYS; names come from the seed manifest.
PERSONA_NAMES = {
    "conflict_persona": "Aarav Demo-Mehta",
    "clean_persona": "Rohan Demo-Sen",
    "nps_persona": "Priya Demo-Iyer",
    "joint_persona": "Meera Demo-Rao",
}

FIELD_COLUMNS = (
    ("document_group_id", "document_group_id"),
    ("asset_type", "asset_type"),
    ("institution_name", "institution_name"),
    ("asset_reference", "asset_reference"),
    ("named_person", "person_name"),
    ("relationship", "relationship"),
    ("mechanism_type", "mechanism"),
    ("share_percent", "share_percent"),
    ("source_text", "source_text"),
    ("source_locator", "source_locator"),
    ("confidence", "confidence"),
    ("registration_status", "registration_status"),
    ("registration_date", "registration_date"),
    ("explicit_nomination_action", "explicit_nomination_action"),
    ("policy_kind", "policy_kind"),
    ("mwpa_section_6_applies", "mwpa_section_6_applies"),
    ("assignment_status", "assignment_status"),
    ("holding_pattern", "holding_pattern"),
)


def main() -> int:
    connection = sqlite3.connect(get_database_path())
    connection.row_factory = sqlite3.Row

    personas = connection.execute("SELECT * FROM personas ORDER BY id").fetchall()
    by_name = {row["name"]: row for row in personas}
    missing = [name for name in PERSONA_NAMES.values() if name not in by_name]
    if missing:
        print(f"error: database is missing seeded personas: {missing}", file=sys.stderr)
        return 1

    snapshot: dict[str, dict] = {}
    for key in PERSONA_KEYS:
        persona_row = by_name[PERSONA_NAMES[key]]
        persona_id = int(persona_row["id"])
        documents = []
        for document in connection.execute(
            """
            SELECT id, original_filename, doc_type, document_date, extraction_source
            FROM documents WHERE persona_id = ? ORDER BY id
            """,
            (persona_id,),
        ):
            if document["extraction_source"] != "gemini":
                print(
                    "error: refusing to export a snapshot that is not live extraction "
                    f"output ({document['original_filename']} came from "
                    f"{document['extraction_source']})",
                    file=sys.stderr,
                )
                return 1
            edited = connection.execute(
                """
                SELECT COUNT(*) AS n FROM extracted_fields
                WHERE document_id = ? AND is_user_edited = 1
                """,
                (document["id"],),
            ).fetchone()["n"]
            if edited:
                print(
                    "error: refusing to export a simulated fix as extraction output "
                    f"({document['original_filename']} has {edited} user-edited "
                    "field(s)). Re-seed in live mode first.",
                    file=sys.stderr,
                )
                return 1
            fields = [
                {
                    snapshot_key: row[column]
                    for snapshot_key, column in FIELD_COLUMNS
                }
                for row in connection.execute(
                    "SELECT * FROM extracted_fields WHERE document_id = ? ORDER BY id",
                    (document["id"],),
                )
            ]
            documents.append(
                {
                    "original_filename": document["original_filename"],
                    "document_type": document["doc_type"],
                    "document_date": document["document_date"],
                    "fields": fields,
                }
            )
        snapshot[key] = {
            "name": PERSONA_NAMES[key],
            "description": "Synthetic demo persona",
            # Stated context, carried through so the fallback seed reproduces the same
            # findings as the live seed. NPS-VALIDITY-001 depends entirely on these.
            "persona_context": {
                "owner_has_family": persona_row["owner_has_family"],
                "marriage_date": persona_row["marriage_date"],
                "family_context_source_text": persona_row["family_context_source_text"],
            },
            "documents": documents,
        }

    FALLBACK_PATH.write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    total = sum(
        len(document["fields"])
        for persona in snapshot.values()
        for document in persona["documents"]
    )
    print(f"wrote {FALLBACK_PATH} with {total} extracted fields")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
