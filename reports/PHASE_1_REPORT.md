# Phase 1 report — Legal rule research

Date: 2026-09-29

Status: Complete; awaiting user review

Implementation commit: `1aac7eb146bbf0454a93b032534789cbdf89ee16`

Completion tag: `phase-1-done`

## Objective

Research and document a small, India-scoped set of nominee/beneficiary/will consistency rules before building extraction or detection. Every rule must be deterministic, sourced, explainable, narrow, and non-authoritative.

## Completed

- Reviewed current primary material from the Supreme Court of India, IFSCA-hosted Insurance Act, SEBI, and PFRDA.
- Created `backend/rules/RULES.md` as the single source of truth.
- Defined seven candidate rules:
  - `BANK-WILL-001`
  - `LIFE-NOTICE-001`
  - `LIFE-WILL-001`
  - `MF-WILL-001`
  - `NPS-WILL-001`
  - `NPS-VALIDITY-001`
  - `RECORD-SUPERSESSION-001`
- For each rule documented scope, source/reasoning, structured inputs, deterministic pseudocode, severity, fixed summary, legal limitation, suggested actions, and synthetic positive/negative examples.
- Defined strict asset/person matching and rule ordering/suppression.
- Defined the mandatory exact disclaimer and required deterministic finding contract.
- Listed unsupported cases and prohibited legal inferences.
- Identified additional provenance fields Phase 2 must extract or explicitly confirm.
- Added documentation tests that enforce rule count, stable IDs, implementation-ready sections, source-host restrictions, disclaimer, and AI boundary.
- Updated Docker packaging so the rules file is available to in-container tests.

## What was not done

- No Python conflict predicates or engine were implemented.
- No Claude integration, prompt, upload endpoint, extraction schema migration, or UI was added.
- No legal outcome or legal winner was encoded.
- No real personal, financial, insurance, or estate document was requested, downloaded, stored, or used.
- No Phase 2 work was started.

## Legal uncertainty retained intentionally

- `NPS-WILL-001` flags a mismatch because current regulations govern payment to a valid nominee, but does not decide the nominee-versus-will succession result.
- Life-insurance rules exclude MWP Act section 6 and active/unknown assignment cases; close-family nominee treatment is flagged for professional review rather than resolved.
- Mutual-fund wording is based on SEBI's operative 2025 circular/form. A March 2026 consultation draft was not treated as law; final-status re-check is required before Phase 4 and Phase 6.
- Joint holdings, survivorship, lockers, demat shares, general insurance, trusts, foreign assets, creditor claims, and personal-law heirship are outside this candidate set.

## Deviations and research notes

1. Official source PDFs could not be parsed by the web text-fetch tool. `pypdf==6.19.0` was installed only in the ignored local virtual environment for research; it is not an application dependency.
2. The most current accessible consolidated Insurance Act text was hosted by IFSCA rather than an IRDAI page. IFSCA is a Government of India statutory regulator; the document itself shows the operative section text and amendments through 2026.
3. Search results exposed unrelated real complaint documents on an IRDAI subdomain. They were not opened, used, cited, requested, or stored because all project material must remain synthetic.
4. The rules document adds extraction requirements but deliberately leaves the Phase 0 schema unchanged until Phase 2 is approved.

## Validation evidence

| Check | Result |
|---|---|
| Candidate rule count | 7 (within requested 5–8) |
| Rules with source, predicate, summary, scope note, actions, positive/negative examples | 7/7 |
| Primary source URLs | 5/5 returned HTTP 200 on 2026-09-29 |
| Local backend/rules tests | 12 passed |
| Backend/rules tests in rebuilt Docker image | 12 passed |
| Rule decisions requiring Claude | 0 |
| Rules declaring a legal winner | 0 |
| Real documents used | 0 |

## Review this phase

Read `backend/rules/RULES.md`, focusing on:

1. Whether the seven-rule scope is appropriate for the demo.
2. Whether high/medium priorities match the desired pitch.
3. Whether `NPS-VALIDITY-001` should remain in the demo despite requiring explicit synthetic family/marriage context.
4. Whether the unsupported-case list is sufficiently conservative.

To run the documentation tests:

```bash
cd backend
.venv/bin/python -m pytest
```

Or in Docker:

```bash
docker compose build backend
docker compose run --rm backend pytest
```

## Phase boundary

Stop here. Phase 2 must not start until the user replies exactly:

`APPROVED PHASE 1`
