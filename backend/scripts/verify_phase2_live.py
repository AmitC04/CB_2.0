"""Upload five synthetic extraction fixtures and print manual-review comparisons."""

import os
import sys
from pathlib import Path

import httpx

BASE_URL = os.getenv("JEEVANSETU_API_URL", "http://localhost:8000")
FIXTURE_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
EXPECTED = {
    "will_extraction_only.txt": ("will", "BANK-FIXTURE-1001", "Mira Test-Kapoor"),
    "bank_nomination_extraction_only.txt": (
        "bank_nomination",
        "BANK-FIXTURE-3001",
        "Kabir Test-Mehta",
    ),
    "life_insurance_nomination_extraction_only.txt": (
        "insurance_nomination",
        "LIFE-FIXTURE-4001",
        "Anaya Test-Iyer",
    ),
    "mutual_fund_nomination_extraction_only.txt": (
        "mutual_fund_nomination",
        "MF-FIXTURE-5001",
        "Veer Test-Patel",
    ),
    "nps_nomination_extraction_only.txt": (
        "nps_nomination",
        "PRAN-FIXTURE-6001/Tier-I",
        "Naina Test-Rao",
    ),
}


def main() -> int:
    with httpx.Client(base_url=BASE_URL, timeout=120) as client:
        persona_response = client.post(
            "/personas",
            json={
                "name": "Phase 2 Synthetic Extraction Reviewer",
                "description": "Extraction-only fixtures; not a Phase 3 demo persona.",
                "owner_has_family": "unknown",
                "marriage_date": None,
                "family_context_source_text": None,
                "manually_confirmed_aliases": [],
                "synthetic_confirmed": True,
            },
        )
        persona_response.raise_for_status()
        persona_id = persona_response.json()["id"]

        failures = 0
        for filename, expected in EXPECTED.items():
            path = FIXTURE_DIR / filename
            with path.open("rb") as fixture:
                response = client.post(
                    f"/personas/{persona_id}/documents",
                    data={"synthetic_confirmed": "true"},
                    files={"file": (filename, fixture, "text/plain")},
                )
            if response.status_code != 201:
                failures += 1
                print(f"FAIL {filename}: HTTP {response.status_code} {response.text}")
                continue

            document = response.json()
            actual_refs = {field["asset_reference"] for field in document["fields"]}
            actual_people = {field["named_person"] for field in document["fields"]}
            checks = {
                "type": document["document_type"] == expected[0],
                "reference": expected[1] in actual_refs,
                "person": expected[2] in actual_people,
                "source_text": all(field["source_text"] for field in document["fields"]),
            }
            passed = all(checks.values())
            failures += int(not passed)
            print(
                f"{'PASS' if passed else 'REVIEW'} {filename}: "
                f"expected={expected}; type={document['document_type']}; "
                f"refs={sorted(actual_refs)}; people={sorted(actual_people)}; checks={checks}"
            )

    print("Review every extracted source_text against the fixture before approval.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
