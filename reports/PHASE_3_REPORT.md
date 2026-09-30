# Phase 3 report — Synthetic demo documents

Date: 2026-09-29

Status: Complete; awaiting user review

Implementation commit: `569c6c2972e95d75fb0d1f7e03af3d8218bff8d1`

Completion tag: `phase-3-done`

## Completed

- Created a conflict persona with a will plus bank, life-insurance, and mutual-fund nomination forms.
- Created a clean persona with a will plus bank and life-insurance nomination forms.
- Used only fictional names, institutions, identifiers, dates, and signature placeholders.
- Added prominent synthetic/not-valid/not-legal-advice markings to every document.
- Kept editable HTML sources and generated seven one-page PDF demo uploads.
- Added `seed_data/MANIFEST.md` and machine-readable `expected_extractions.json`.
- Added `backend/scripts/verify_phase3_live.py` for real API/Gemini verification.

## Intended outcome (not yet engine output)

The conflict persona has exactly one intended approved-rule instance: `BANK-WILL-001` for Sampurna Demo Bank account `SB-DEMO-4821`. Will clause 3.1 names Anika Demo-Mehta; the registered-looking bank nomination names Kavya Demo-Mehta. This requires review and does not establish a legal winner.

Life policy `LIFE-DEMO-7710` and mutual-fund folio `MF-DEMO-2040` align on Anika Demo-Mehta. The clean persona aligns on Mira Demo-Sen for `SB-DEMO-8120` and `LIFE-DEMO-9912`, so expected conflicts are empty.

No conflict engine exists yet; these are Phase 4 expected results only.

## Validation

- Seven of seven PDFs parse as one page.
- Seven of seven contain visible synthetic markings and expected references.
- Seven of seven uploaded successfully through the Phase 2 PDF endpoint.
- Seven of seven Gemini classifications and all extracted rows match the manifest.
- Registered-looking forms extracted as `registration_status=confirmed` with dates.
- Insurance forms preserved life-policy type, MWP false, and no-assignment scope.
- All Phase 2 backend tests remain applicable; no detection code was added.

Chrome emitted macOS headless display warnings during generation but returned success and wrote valid PDFs.

## Not completed

- No deterministic conflict detection, severity result, explanation, score, UI, or vault behavior.
- No real person, institution, legal form, account, policy, folio, PRAN, ID, address, or signature.
- No claim that the forms are legally sufficient or realistic for institutional submission.

## Review/demo

Read `seed_data/MANIFEST.md`, then open the PDFs under:

- `seed_data/conflict_persona/documents/`
- `seed_data/clean_persona/documents/`

Run live extraction verification with the keyed backend running:

```bash
cd backend
.venv/bin/python scripts/verify_phase3_live.py
```

## Phase boundary

Stop here. Phase 4 must not start until the user replies exactly:

`APPROVED PHASE 3`
