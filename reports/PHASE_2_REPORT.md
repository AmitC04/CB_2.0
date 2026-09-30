# Phase 2 report — Synthetic upload and AI extraction

Date: 2026-09-29

Status: Complete; awaiting user review

Implementation commit: `8546fde6209c8d2a39542db299f46e029754e82b`

Completion tag: `phase-2-done`

## Objective

Accept synthetic PDF/image/text documents, classify them, extract source-backed structured fields through an external multimodal model, persist the results, and expose an honest retained-upload retry path. No AI may decide legal conflicts.

## Completed

- Added strict Pydantic contracts for document classification and every Phase 1-required extraction field.
- Extended the existing five-table SQLite schema with hashes, sizes, extraction states, registration evidence, source locators/confidence, policy scope, document groups, and synthetic persona context.
- Added secure generated storage keys, a 10 MiB limit, extension/MIME/signature checks, UTF-8 validation, and path-component rejection.
- Required explicit synthetic-data attestation for persona creation and document upload.
- Added persona create/read, document upload/read/list, and retained-file retry routes.
- Added Gemini Developer API structured extraction for text, PDF, PNG, JPEG, and WebP inputs.
- Kept legal status unknown unless expressly supported; preserved exact source text and locator for each row.
- Added five extraction-only synthetic fixtures: will, bank nomination, life-insurance nomination, mutual-fund nomination, and NPS nomination.
- Added an automated live verification runner.
- Added accurate failed/extracted states, sanitized error codes, transient retryability, stale-field cleanup, concurrent-attempt rejection, and interrupted-attempt recovery.
- Bound both Compose services to loopback for this trusted local demo.
- Added explicit legacy-schema detection instead of allowing a partial `CREATE TABLE IF NOT EXISTS` upgrade.

## Approved deviation

The original prompt and PRD required Claude. The user explicitly approved Gemini Developer API free tier for Phase 2 extraction and later explanations because paid Anthropic API access was unavailable. The implementation uses `google-genai==2.25.0` and defaults to `gemini-3.1-flash-lite`; no dormant multi-provider layer was added.

Google states that free-tier content may be used to improve its products. This build therefore remains synthetic-only and is not suitable for real personal or financial documents.

## Live verification

The user delegated manual verification to the assistant. Every stored output was compared with the source fixture.

| Fixture | Classification | Verified extracted rows |
|---|---|---|
| Will | `will` | BANK-FIXTURE-1001 → Mira Test-Kapoor; MF-FIXTURE-2001 → Neel Test-Kapoor |
| Bank nomination | `bank_nomination` | BANK-FIXTURE-3001 → Kabir Test-Mehta, brother, 100% |
| Life insurance | `insurance_nomination` | LIFE-FIXTURE-4001 → Anaya Test-Iyer, spouse, 100%; life policy; MWP/assignment unknown |
| Mutual fund | `mutual_fund_nomination` | MF-FIXTURE-5001 → Veer Test-Patel 60% and Tara Test-Patel 40%, one document group |
| NPS | `nps_nomination` | PRAN-FIXTURE-6001/Tier-I → Naina Test-Rao, mother, 100% |

Every row included a supporting source excerpt, locator, confidence, registration status, and required legal-scope unknowns. No conflict or legal conclusion was generated.

The NPS request initially hit a transient free-tier provider error. The API retained the upload as failed and a later retry succeeded, demonstrating the real failure path without fabricated fallback output.

## Validation

- Local tests: 29 passed (one third-party Google SDK deprecation warning under host Python 3.14).
- Docker/Python 3.12 tests: 29 passed without that host warning.
- Python compile checks passed before live verification.
- Five of five fixtures extracted live and were manually compared.
- Health endpoint and frontend remained operational.
- `.env` is Git-ignored; `.env.example` contains no key.
- No real document or identity was used.

## Semantic review fixes

A pre-commit semantic review initially blocked shipment. All actionable findings were addressed: loopback exposure, stale fields after failed retry, legacy-schema failure clarity, racing/interrupted attempts, overstated retryability, live-model verification, and a foreign-key test that previously matched a different constraint.

## Not completed

- No frontend upload/results UI (Phase 5).
- No polished conflicting/clean demo persona documents (Phase 3).
- No deterministic conflict engine (Phase 4).
- No score, vault, or simulated institution integration.
- No public deployment or claim that caller attestation proves a file is synthetic.

## Run/demo Phase 2

1. Put a Gemini key in the ignored `.env` file.
2. Run `docker compose up --build`.
3. Open http://localhost:8000/docs.
4. Create a synthetic persona with `POST /personas`.
5. Upload only a synthetic fixture using `POST /personas/{id}/documents` with `synthetic_confirmed=true`.
6. Inspect exact source-backed fields with `GET /documents/{id}`.
7. Run all five fixtures with the command documented in README.

## Phase boundary

Stop here. Phase 3 must not start until the user replies exactly:

`APPROVED PHASE 2`
