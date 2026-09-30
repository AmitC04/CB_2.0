# Phase 5 report — Readiness score and results UI

Date: 2026-09-29

Status: Complete; awaiting user review

Implementation commit: `92b81ea40e6c0aca2b393862777803854e40f707`

Completion tag: `phase-5-done`

## Completed

- Added `backend/app/scoring.py` with a deterministic Continuity Readiness Score: base 100 minus 25 per high finding, 10 per medium, and 3 per gap, clamped to 0-100.
- Added a Phase 5 completeness check that flags a will-assigned asset with no uploaded nomination as `GAP-MISSING-NOMINATION`.
- Separated conflicts from gaps in the score breakdown by finding type, so a gap can never be displayed as a conflict or the reverse.
- Persisted the score on the existing `detection_runs.readiness_score` column and returned an explainable breakdown.
- Added `GET /personas`, `PATCH /fields/{id}` for a simulated synthetic fix, and a guard that refuses to discard simulated fixes during extraction retry without `force=true`.
- Built the results UI: score card with arithmetic breakdown, severity-ordered finding cards showing source A versus source B with locators, explanation, suggested fix, documented actions, scope note, and the mandatory disclaimer.
- Built the vault panel: per-document field list with inline "Simulate a fix" editing, an edited marker, original-extraction labelling, and a re-run button.

## Acceptance: the full demo flow

Verified live against the real backend and Gemini, end to end:

| Step | Result |
|---|---|
| Upload the seven Phase 3 synthetic PDFs | All extracted, matching the manifest |
| See extraction | Vault lists 4 conflict-persona and 3 clean-persona documents with source quotes |
| See conflicts | One `BANK-WILL-001`, high, with both sources and a Gemini explanation |
| See score | 75 for the conflict persona, 100 for the clean persona |
| Fix one field | `PATCH /fields/4` set the bank nominee to the will's person; `is_user_edited` recorded |
| Re-run | Conflicts 0, score 100 |
| See score improve | 75 → 100 confirmed in the API and in the UI notice |

Rendered-page checks confirmed the score, conflict card, both sources, suggested fix, vault documents, re-run control, and disclaimer are present, and that the clean persona shows the green no-conflict panel with a score of 100.

## Validation

- Backend tests: 90 passed locally and in Docker.
- Frontend: `npm run lint` and `npm run build` clean.
- Retry guard on a document with a simulated fix returns HTTP 409.
- Score breakdown verified for both personas.

## Semantic review and fixes

A pre-commit review blocked the first implementation with two defects on the demo path, both fixed:

1. A run recorded before scoring existed has a null score, and the score card coerced it to `0`, so the clean persona could render "0 / 100 · Several items to review" in red beside the green "No conflicts were found" panel. The card now shows an explicit "not scored, re-run detection" state.
2. `GAP-MISSING-NOMINATION` was appended outside the engine's dedupe, so a near-variant asset reference produced both a near-match gap and a false "no nomination was uploaded" gap, double-deducting. The completeness check now skips any bequest already covered by a near-match gap, and all findings pass through the shared dedupe and severity ordering.

Also fixed: the breakdown now partitions by finding type rather than severity; the shared `score_breakdown` function is used by the read path instead of an inline duplicate; a score decrease is now announced, not only an improvement; the score card is marked stale after an edit until detection is re-run; a failed fix keeps the editor open instead of appearing to succeed; scope gaps no longer show an "AI wording unavailable" message they were never meant to have; the fix response carries the disclaimer; and the vault labels the quote as the original extracted text so an edited value is never mistaken for the source evidence.

## Known limitations (recorded)

- A simulated fix overwrites the extracted value with no undo. The original text remains visible as the source quote, and re-running extraction restores the extracted value from the stored document.
- `PATCH /fields/{id}` is unauthenticated and loopback-only, consistent with D-022.
- The score is a review-priority indicator for synthetic documents, not a legal or financial assessment.
- The frontend has no automated test runner; UI verification was done with lint, production build, rendered-DOM assertions, and a screenshot.

## Not completed

- No demo-reset seed script, deployment, or pitch document (Phase 6).
- No Section 5.6 stretch estate-case view (Phase 7).

## Run/demo

```bash
docker compose up --build --detach
open http://localhost:3000
```

Pick a persona, press "Run detection", read the score and conflict cards, use "Simulate a fix" in the vault to change the bank nominee to the will's person, then press "Re-run detection" and watch the score rise from 75 to 100.

## Phase boundary

Stop here. Phase 6 must not start until the user replies exactly:

`APPROVED PHASE 5`
