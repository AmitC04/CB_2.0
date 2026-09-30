# JeevanSetu progress

Last updated: 2026-09-29

## Phase status

- [x] **Phase 0 — Setup:** approved by user on 2026-09-29.
- [x] **Phase 1 — Legal rule research:** approved by user on 2026-09-29.
- [x] **Phase 2 — Document upload and AI extraction:** approved by user on 2026-09-29.
- [x] **Phase 3 — Synthetic demo documents:** approved by user on 2026-09-29.
- [x] **Phase 4 — Deterministic conflict detection engine:** approved by user on 2026-09-29.
- [x] **Phase 5 — Readiness score and results UI:** approved by user on 2026-09-29.
- [x] **Phase 6 — Polish and demo readiness:** approved by user on 2026-09-29.
- [x] **Phase 7 — Stretch concept estate-case view:** built as a separate, clearly labelled page; awaiting user review.

## Phase 0 checklist

- [x] Initialize Git repository and required directory layout.
- [x] Move the supplied PRD to `docs/PRD.md`.
- [x] Add two-service Docker Compose stack; SQLite remains file-based.
- [x] Add FastAPI application with `GET /health` and explicit CORS allowlist.
- [x] Add idempotent five-table SQLite draft schema.
- [x] Add Next.js/Tailwind landing page that polls backend health.
- [x] Show the synthetic-data and not-legal-advice warning in the Phase 0 UI.
- [x] Pin all direct Python and npm dependencies to exact versions.
- [x] Pass 7 backend tests locally and inside the backend image.
- [x] Pass frontend lint and production build.
- [x] Build both Docker images and start both containers.
- [x] Verify the exact health payload and allowed CORS origin.
- [x] Verify a synthetic SQLite row survives `docker compose down` and restart.
- [x] Verify browser-rendered `Backend connected` and `Backend unreachable` states.
- [x] Write Phase 0 documentation and report.
- [x] User approval received: `APPROVED PHASE 0`.

## Phase 1 checklist

- [x] Review primary India sources for supported asset types.
- [x] Define seven candidate deterministic rules.
- [x] Document source/reasoning, scope, predicates, severity, and examples for every rule.
- [x] Preserve legal uncertainty and prohibit winner/ownership conclusions.
- [x] Define a mandatory disclaimer and deterministic finding contract.
- [x] List unsupported cases and required Phase 2 extraction fields.
- [x] Verify all five primary-source links return HTTP 200.
- [x] Pass 12 local and 12 in-container tests.
- [x] Write Phase 1 decisions and completion report.
- [x] User approval received: `APPROVED PHASE 1`.

## Phase 2 checklist

- [x] Add synthetic-attested PDF/image/text upload validation with a 10 MiB limit.
- [x] Add generated local storage keys and content hashes.
- [x] Add strict structured extraction and source evidence contracts.
- [x] Integrate Gemini 3.1 Flash-Lite after explicit provider deviation.
- [x] Add persona, upload, retrieval, listing, and retry API routes.
- [x] Preserve honest failed status and retained uploads on provider failure.
- [x] Add five extraction-only synthetic fixtures.
- [x] Verify all five fixtures live against Gemini and compare every stored field.
- [x] Demonstrate a transient free-tier failure succeeding through stored retry.
- [x] Bind the local Compose demo to loopback only.
- [x] Add legacy-schema detection and interrupted/racing extraction safeguards.
- [x] Pass 29 tests locally and in Docker.
- [x] Write Phase 2 decisions and completion report.
- [x] User approval received: `APPROVED PHASE 2`.

## Phase 3 checklist

- [x] Define one deliberate-conflict persona and one clean control persona.
- [x] Use invented names, institutions, references, and signature placeholders only.
- [x] Author seven visibly marked synthetic HTML sources.
- [x] Generate seven one-page PDF demo uploads.
- [x] Document exact expected extraction and Phase 4 outcomes.
- [x] Validate every PDF opens, is marked synthetic, and contains expected references.
- [x] Upload every PDF through the real Gemini extraction endpoint.
- [x] Verify all stored classifications and fields against the manifest.
- [x] Confirm the intended mismatch is exactly a `BANK-WILL-001` instance.
- [x] Confirm aligned life-policy and mutual-fund records avoid accidental conflicts.
- [x] Write Phase 3 decisions and completion report.
- [x] User approval received: `APPROVED PHASE 3`.

## Phase 4 checklist

- [x] Implement all seven approved rules as a pure deterministic function.
- [x] Keep every rule decision free of AI involvement, asserted by test.
- [x] Apply the documented ordering, suppression, and deduplication.
- [x] Emit labeled `GAP-*` markers for excluded cases instead of forced conflicts.
- [x] Attach the exact disclaimer to every finding and to the run payload.
- [x] Add Gemini wording that is rejected if it states a legal outcome.
- [x] Preserve complete deterministic content when wording fails.
- [x] Expand the findings schema and enforce the schema-version guard.
- [x] Add detection run and latest-run API routes.
- [x] Cover every rule with positive and negative unit tests.
- [x] Pin engine rule text to `RULES.md` with a test.
- [x] Fix all three suppression defects found by semantic review, with regression tests.
- [x] Pass 72 tests locally and in Docker.
- [x] Verify live: exactly one `BANK-WILL-001` for the conflict persona, nothing for the clean persona.
- [x] Write Phase 4 decisions and completion report.
- [x] User approval received: `APPROVED PHASE 4`.

## Phase 5 checklist

- [x] Add a deterministic, explainable readiness score with a visible breakdown.
- [x] Flag a will-assigned asset with no nomination as a completeness gap, not a conflict.
- [x] Separate conflicts from gaps by finding type in the breakdown.
- [x] Persist the score on each detection run.
- [x] Add persona listing and a simulated field-fix endpoint.
- [x] Refuse to discard simulated fixes on extraction retry without an explicit force.
- [x] Build the results view with score and severity-ordered finding cards.
- [x] Show source A versus source B, explanation, fix, actions, scope note, and disclaimer.
- [x] Build the vault with document list, inline fix editing, and re-run.
- [x] Fix both demo-path defects found by semantic review.
- [x] Pass 90 backend tests locally and in Docker.
- [x] Pass frontend lint and production build.
- [x] Verify the live flow: upload, extract, conflicts, score 75, fix, re-run, score 100.
- [x] Write Phase 5 decisions and completion report.
- [x] User approval received: `APPROVED PHASE 5`.

## Phase 6 checklist

- [x] Re-verify all five primary legal sources before the demo freeze.
- [x] Confirm the SEBI March 2026 consultation is still a draft and source no rule from it.
- [x] Add a demo reset and seed script with live and fallback modes.
- [x] Label fallback data in the UI as not a live AI extraction.
- [x] Require explicit confirmation before resetting synthetic storage.
- [x] Add a sanitized global error handler.
- [x] Verify the disclaimer on every result surface and payload.
- [x] Finalize the README with sources, real-versus-simplified, and the demo script.
- [x] Write the pitch talking-points document.
- [x] Pass 95 backend tests locally and in Docker.
- [x] Pass frontend lint and production build.
- [x] Reproduce the full demo from a fresh clone in 96 seconds without an API key.
- [x] Write Phase 6 decisions and completion report.
- [x] User approval received: `APPROVED PHASE 6`.

## Phase 7 checklist (stretch)

- [x] Build the concept view as a separate page, leaving the core demo surfaces unchanged.
- [x] Derive illustrative steps deterministically from the synthetic vault.
- [x] Return `concept: true` and the concept label in the API payload itself.
- [x] Show a persistent banner, per-card illustrative labels, the disclaimer, and a footer notice.
- [x] State plainly that no institution is connected.
- [x] Keep the generator away from detection, scoring, AI, and the network.
- [x] Exclude the illustrative steps from `RULES.md` because they are not sourced rules.
- [x] Pass 104 backend tests locally and in Docker.
- [x] Pass frontend lint and production build.
- [x] Confirm the core demo still scores 75 with one `BANK-WILL-001` after the change.
- [x] Write Phase 7 decisions and completion report.
- [ ] User review and exact approval phrase: `APPROVED PHASE 7`.

## Phase boundary

All seven phases are implemented. Nothing further is in progress.

## Recorded gap closure (post-Phase 7, requested by the user)

- [x] Gap 1 — joint holdings: added `holding_pattern` to the schema, extraction prompt, and models; gated `BANK-WILL-001`, `MF-WILL-001`, and `RECORD-SUPERSESSION-001`; emit `GAP-JOINT-HOLDING`.
- [x] Gap 1 — documented the new scope and the `unknown` decision in `RULES.md` section 14, and added a test that fails if any gap marker the engine can emit is undocumented.
- [x] Gap 2 — undo: added the `field_edits` audit table, `POST /fields/{id}/undo`, and an Undo button that appears only for an edited field.
- [x] Gap 3 — frontend tests: Vitest, Testing Library, and jsdom at pinned versions; 19 component tests behind `npm test`.
- [x] Gap 4 — deployment readiness: optional `API_TOKEN` gate (off by default, `/health` exempt), server-side proxy route, `docs/DEPLOYMENT.md`.
- [x] Regenerated the fallback snapshot from a live seed with a script that refuses non-live data.
- [x] Pass 120 backend tests and 19 frontend tests; frontend lint and production build clean.
- [x] Re-verified the demo numbers after every change: conflict persona 75 with one `BANK-WILL-001`, clean persona 100, fix raises 75 to 100, undo returns it to 75.
- [ ] Gap 4 — an actual deployment. Blocked on the user's hosting accounts and a decision to expose the API; see `docs/DEPLOYMENT.md`.
