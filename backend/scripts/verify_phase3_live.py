"""Upload and verify every Phase 3 synthetic PDF against its manifest."""

import json
import os
import time
from pathlib import Path

import httpx

BASE_URL = os.getenv("JEEVANSETU_API_URL", "http://localhost:8000")
def _seed_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "seed_data"
        if (candidate / "expected_extractions.json").exists():
            return candidate
    raise FileNotFoundError("seed_data was not found")


SEED_ROOT = _seed_root()
MANIFEST = json.loads((SEED_ROOT / "expected_extractions.json").read_text())


def extract_with_retry(
    client: httpx.Client,
    persona_id: int,
    relative_path: str,
) -> dict:
    path = SEED_ROOT / relative_path
    with path.open("rb") as document:
        response = client.post(
            f"/personas/{persona_id}/documents",
            data={"synthetic_confirmed": "true"},
            files={"file": (path.name, document, "application/pdf")},
        )
    if response.status_code == 201:
        return response.json()

    failure = response.json()
    document_id = failure.get("document_id")
    if response.status_code != 503 or not failure.get("retryable") or not document_id:
        raise RuntimeError(f"Upload failed: {response.status_code} {failure}")

    for _ in range(4):
        time.sleep(20)
        response = client.post(f"/documents/{document_id}/extract")
        if response.status_code == 200:
            return response.json()
        failure = response.json()
        if response.status_code != 503 or not failure.get("retryable"):
            break
    raise RuntimeError(f"Retry failed for {relative_path}: {response.status_code} {failure}")


def verify_document(document: dict, expected: dict) -> None:
    assert document["status"] == "extracted"
    assert document["extraction_source"] == "gemini"
    assert document["document_type"] == expected["document_type"]
    assert document["document_date"] == expected["document_date"]

    actual = document["fields"]
    assert len(actual) == len(expected["fields"]), (expected["path"], actual)
    for asset_type, institution, reference, person, relationship, mechanism, share in expected[
        "fields"
    ]:
        matches = [
            field
            for field in actual
            if field["asset_reference"] == reference
            and field["named_person"] == person
            and field["mechanism_type"] == mechanism
        ]
        assert len(matches) == 1, (expected["path"], reference, person, actual)
        field = matches[0]
        assert field["asset_type"] == asset_type
        assert field["institution_name"].casefold() == institution.casefold()
        assert field["relationship"].casefold() == relationship.casefold()
        if share is None:
            assert field["share_percent"] in {None, 100}
        else:
            assert field["share_percent"] == share
        assert field["source_text"]
        assert field["source_locator"]

    if expected["document_type"] in {
        "bank_nomination",
        "insurance_nomination",
        "mutual_fund_nomination",
    }:
        assert all(field["registration_status"] == "confirmed" for field in actual)
    if expected["document_type"] == "insurance_nomination":
        assert all(field["policy_kind"] == "life" for field in actual)
        assert all(field["mwpa_section_6_applies"] == "false" for field in actual)
        assert all(field["assignment_status"] == "none" for field in actual)


def main() -> None:
    with httpx.Client(base_url=BASE_URL, timeout=150) as client:
        for persona_key in ("conflict_persona", "clean_persona"):
            expected_persona = MANIFEST[persona_key]
            persona = client.post(
                "/personas",
                json={
                    "name": expected_persona["name"],
                    "description": "Phase 3 synthetic PDF validation persona.",
                    "synthetic_confirmed": True,
                },
            )
            persona.raise_for_status()
            persona_id = persona.json()["id"]
            for expected in expected_persona["documents"]:
                document = extract_with_retry(client, persona_id, expected["path"])
                verify_document(document, expected)
                print(
                    "PASS",
                    expected["path"],
                    document["document_type"],
                    len(document["fields"]),
                    "field(s)",
                )
                time.sleep(2)

    print("All Phase 3 PDFs match the synthetic extraction manifest.")


if __name__ == "__main__":
    main()
