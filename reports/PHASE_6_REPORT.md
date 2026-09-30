# Phase 6 report — Polish and demo readiness

Date: 2026-09-29

Status: Complete; awaiting user review

Implementation commit: `37f4b478cadf598cbe879dec8200ff8abe4ff3f4`

Completion tag: `phase-6-done`

## Acceptance: fresh clone reproduces the demo in under four minutes

Measured on a clean clone with no `.env` and no API key:

| Step | Elapsed |
|---|---:|
| `git clone` | 1s |
| `docker compose up --build --detach` | 92s |
| Backend healthy | 92s |
| `scripts/seed_demo.py --yes` | 95s |
| Frontend serving | 96s |
| API checks, simulated fix, re-run | 96s |
| **Total** | **96s** |

Verified in that fresh instance: both personas listed, conflict persona scores 75 with one `BANK-WILL-001`, clean persona scores 100 with no conflicts, and a simulated fix plus re-run raises the score to 100. The rendered page showed the score, the conflict card with both named people, the documented next steps, the scope note, the fallback label, and the disclaimer.

This meets PRD section 7: a judge can see extraction, the real conflict with a plain-language explanation and fix, the score, and the score improving after a one-field fix, well inside four minutes.

## Completed

- **Source re-check before freeze.** All five cited primary sources still resolve (HTTP 200) as of 2026-09-29. SEBI's March 2026 item is still a consultation paper with a placeholder circular number, so the operative February 2025 circular remains the source for `MF-WILL-001` and no rule is sourced from a draft. `rules_version` is unchanged.
- **Demo seed and reset.** `backend/app/demo_seed.py` plus `backend/scripts/seed_demo.py` reset the synthetic database and uploads and seed both personas. `--mode live` uses the real Gemini pipeline; the default fallback mode inserts a pre-verified snapshot of previously verified live extraction and records `extraction_source='manual_fallback'`. The reset requires `--yes`.
- **Fallback is visibly labelled.** The vault shows "Pre-verified fallback data, not a live AI extraction" for fallback documents and names the model for live ones, so nothing appears more real than it is.
- **Error handling pass.** Added a sanitized global exception handler that returns a stable `internal_error` payload, logs the exception type, and never leaks internals or document content. Existing honest paths were retained: retained uploads on provider failure, retryable failures, HTTP 409 when a retry would discard a simulated fix, and complete deterministic findings when model wording fails.
- **Disclaimer coverage verified** on the landing page, the persona footer, the score card caveat, every finding card, the vault note, the detection run payload, and the document/fix response payload.
- **README finalized** with the demo script, the four-minute flow, the reset commands, a rule-to-source table, an explicit real-versus-simplified section, known limitations, the API surface, and the architecture boundary.
- **Pitch notes** added at `docs/PITCH.md` with the problem, the demo beats, the credibility answers, the scale argument, and what is explicitly not claimed.

## Validation

- Backend tests: 95 passed locally and in Docker, including five new demo-seed tests that assert the seeded scores, the single expected conflict, and the fallback labelling.
- Frontend: `npm run lint` and `npm run build` clean.
- Fresh-clone timed run: 96 seconds, no API key required.
- Source links: 5/5 returned HTTP 200.

## Not completed

- **No cloud deployment.** The optional live link was not created; it needs hosting accounts and a decision about exposing a keyed, unauthenticated API. D-022 records that this build must not be publicly deployed without access controls. Local Docker Compose remains the demo path.
- No Section 5.6 stretch estate-case view (Phase 7).
- No frontend test runner, consistent with D-047.

## Phase boundary

Stop here. Phase 7 is the stretch feature and must not start until the user replies exactly:

`APPROVED PHASE 6`
