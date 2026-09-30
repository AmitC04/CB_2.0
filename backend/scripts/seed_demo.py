"""Reset the synthetic demo database and seed both demo personas.

Usage:

    python scripts/seed_demo.py --yes                # pre-verified fallback snapshot
    python scripts/seed_demo.py --yes --mode live    # real Gemini extraction

``--yes`` is required because the reset deletes the generated synthetic database and
uploads under the ignored data directory. Everything seeded here is synthetic.
"""

import argparse
import hashlib
import json
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.demo_seed import (  # noqa: E402
    PERSONA_KEYS,
    reset_storage,
    run_detection,
    seed_fallback,
    seed_root,
)
from app.extraction import extract_document  # noqa: E402
from app.models import PersonaCreate  # noqa: E402
from app.repository import create_document, create_persona, save_extraction  # noqa: E402
from app.uploads import ValidatedUpload, store_upload  # noqa: E402

RETRY_DELAY_SECONDS = 20
MAX_ATTEMPTS = 4


def seed_live() -> dict[str, int]:
    """Upload each synthetic PDF and extract it with the real Gemini pipeline."""
    manifest_root = seed_root()
    manifest = json.loads(
        (manifest_root / "expected_extractions.json").read_text(encoding="utf-8")
    )

    persona_ids: dict[str, int] = {}
    for key in PERSONA_KEYS:
        entry = manifest[key]
        # Persona context is stated in the manifest, not read out of a document: the rules
        # treat marriage and family status as confirmed facts and must never infer them.
        context = entry.get("persona_context") or {}
        marriage_date = context.get("marriage_date")
        persona = create_persona(
            PersonaCreate(
                name=entry["name"],
                description="Synthetic demo persona",
                synthetic_confirmed=True,
                owner_has_family=context.get("owner_has_family") or "unknown",
                marriage_date=date.fromisoformat(marriage_date) if marriage_date else None,
                family_context_source_text=context.get("family_context_source_text"),
            )
        )
        persona_ids[key] = persona.id

        for document in entry["documents"]:
            path = manifest_root / document["path"]
            content = path.read_bytes()
            upload = ValidatedUpload(
                original_filename=path.name,
                mime_type="application/pdf",
                extension=".pdf",
                content=content,
                content_sha256=hashlib.sha256(content).hexdigest(),
            )
            document_id = create_document(persona.id, upload, store_upload(upload))

            for attempt in range(1, MAX_ATTEMPTS + 1):
                try:
                    extracted = extract_document(content, "application/pdf")
                    save_extraction(
                        document_id,
                        extracted.result,
                        model_name=extracted.model_name,
                    )
                    print(f"  extracted {path.name}")
                    break
                except Exception as exc:  # noqa: BLE001
                    if attempt == MAX_ATTEMPTS:
                        raise
                    print(f"  provider error on {path.name}, retrying: {exc}")
                    time.sleep(RETRY_DELAY_SECONDS)
    return persona_ids


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("fallback", "live"), default="fallback")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="confirm deleting the generated synthetic database and uploads",
    )
    args = parser.parse_args()

    if not args.yes:
        parser.error("refusing to reset the synthetic database without --yes")

    started = time.monotonic()
    reset_storage()
    print(f"reset synthetic storage, seeding in {args.mode} mode")

    persona_ids = seed_live() if args.mode == "live" else seed_fallback()
    if args.mode == "fallback":
        print("seeded pre-verified extraction snapshot, labelled manual_fallback")

    for key, persona_id in persona_ids.items():
        score = run_detection(persona_id)
        print(f"{key}: persona {persona_id}, readiness score {score}")

    print(f"done in {time.monotonic() - started:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
