# Gap closure report

Date: 2026-09-29
Requested after Phase 7 approval: "fixall gaps"
Baseline commit: `67a6cc6` (`phase-7-done`)

Four gaps were recorded across the seven phase reports. Three are closed in code with tests. The fourth is closed as far as an agent can close it: the mechanism is built and verified, the deployment itself is not done and cannot be, because it needs the user's accounts and an explicit decision to expose the API.

## 1. Joint holdings — closed

`RULES.md` scoped `BANK-WILL-001` to individually held accounts and `MF-WILL-001` to sole-holder folios, but the extraction schema had no holding-pattern field, so the engine could report a conflict on a joint asset it had no rule for.

- `extracted_fields.holding_pattern` added with a `CHECK` constraint allowing only `single`, `joint`, `unknown`; `SCHEMA_VERSION` raised to 4 and the required-column guard extended, so a legacy database raises `SchemaVersionError` instead of failing at query time.
- The extraction prompt and the flat Gemini response schema now request holding pattern, with an instruction that it describes how the asset is held and not who is nominated.
- `_holding_in_scope()` gates `rule_bank_will`, `rule_mf_will`, and the supersession scope check. `_joint_holding_gaps()` emits `GAP-JOINT-HOLDING` as a `scope_gap` at severity `low`.
- The engine reads holding pattern from the nomination record, not the will clause, because the nomination form is what states it.
- `unknown` is in scope by decision D-058. Gapping it would have skipped most records and reported manual-review-required where the rules do apply. The residual risk is stated in `RULES.md` section 14 and in the README limitations.
- `RULES.md` section 13's limitation paragraph is replaced by section 14, a three-value behaviour table, and the reasoning. `GAP-JOINT-HOLDING` and the previously undocumented `GAP-MISSING-NOMINATION` were added to the section 12 marker table.

Live check: a full live re-extraction of all seven synthetic PDFs populated the field as nomination forms `single` and will clauses `unknown`, which is faithful to the documents. Scores were unchanged.

Two behaviours review asked to be written down rather than left implicit, now in section 14: the gap is raised even when the nomination and the will name the same person, because the rules cannot call a joint holding clean either; and leaving rule scope raises the score, since a gap deducts 3 where a conflict deducts 25. The gap is restricted to the `nominee` mechanism so it is exactly the complement of the skipped rule.

Not reachable in the demo: no seed document is a joint holding, so `GAP-JOINT-HOLDING` and the amber vault badge are exercised only by tests. Adding one would change the headline 75, so it was left out and recorded in the README instead.

## 2. Simulated-fix undo — closed

A fix was one-way; only re-extraction could restore the extracted value.

- New `field_edits` table storing previous and new values per edit, with `undone_at`.
- `PATCH /fields/{id}` appends a log row. `POST /fields/{id}/undo` reverts the latest edit that has not been undone, marks it undone, and clears `is_user_edited` only when no earlier edit remains. Undo itself deletes nothing.
- Saving a value identical to the current one is not recorded as an edit, so the vault never claims a change that did not happen.
- `409 no_edit_to_undo` when there is nothing to undo; `404` for an unknown field.
- The vault shows "Undo last fix" only for an edited field, and the original extracted quote stays visible either way.
- Durability boundary, found in review: the log is keyed to the extracted field rows and cascades with them, so a forced re-extraction removes a document's edit history along with its fields. That path already requires `force=true`. A test pins it, and D-060 records it rather than claiming the log is permanent.

## 3. Frontend test runner — closed

The frontend had lint, a production build, and manual checks, but no automated tests.

- Vitest 5.0.2, @vitejs/plugin-react 6.1.1, @testing-library/react 16.3.3, @testing-library/dom 10.4.2, @testing-library/jest-dom 7.0.1, @testing-library/user-event 14.6.7, jsdom 30.1.1, all pinned exactly. `@types/node` moved to 24.19.0 to match the Node 24 runtime the Dockerfile already uses.
- 19 tests over the three components that render the safety-critical labels: `ScoreCard` (null score is explained, never shown as 0; stale-after-edit warning; the "not legal readiness" wording), `FindingCard` (disclaimer, both source quotes, the AI-wording fallback, and a scope gap labelled manual review with no fallback notice), `VaultPanel` (save, undo visibility and dispatch, the original-quote label, the `manual_fallback` label, the joint-holding notice, and disabled controls while busy).
- The suite was checked against a deliberate mutation: inverting the joint-holding condition in `VaultPanel` failed a test, confirming the assertions are not vacuous.

Not covered: the persona pages, the estate-case page, and the proxy route. The README says so.

## Review

An independent semantic review of this diff returned NEEDS_CHANGES with two blocking defects and nine smaller ones. Both blocking items are fixed: the CORS ordering, which made a 401 opaque to a browser and which this report had recorded as verified when it was not; and the deployment runbook's claim that the token gate closed the open write path, when the proxy relays anonymously. Also fixed from that review: the fallback exporter now refuses a document with user-edited fields, a no-op save is no longer recorded as an edit, `/health/` with a trailing slash is no longer answered with 401, the 401 body matches every other error shape, the joint-holding gap is restricted to the mechanism the gated rules match, and the D-060 durability claim is corrected. Tests were added for gated write methods, the CORS preflight carve-out, CORS headers on a 401, a supersession group mixing joint and single records, a joint holding where the names agree, a mechanism the rules never match, a no-op save, and the re-extraction cascade.

## 4. Deployment — mechanism built, deployment not done

D-053 refused cloud deployment because it would expose a keyed, unauthenticated API. That specific objection is now answerable.

- Optional `API_TOKEN` bearer gate in `backend/app/main.py`, off by default, `/health` exempt (trailing slash included) so container health checks keep working, constant-time comparison, the same `{"detail": {...}}` error shape as every other route, and a body that does not echo the token. CORS is registered last so it wraps the gate and a 401 carries CORS headers; review caught the reverse order, where a browser saw an opaque failure instead of the status, and a test now pins it.
- `frontend/app/api/backend/[...path]/route.ts` forwards GET, POST, and PATCH to `BACKEND_URL` and attaches the token server-side, so a hosted browser bundle never holds it. Setting `NEXT_PUBLIC_API_URL=/api/backend` is all the client needs.
- **The proxy authenticates nothing.** It relays any request that reaches it. Publishing the frontend therefore leaves the upload path open to anyone with the URL; the token gate only stops direct access to the backend and keeps the credential out of the browser. Review flagged that the first draft of the runbook implied otherwise. `docs/DEPLOYMENT.md` now states it in the threat model, repeats it beside the wiring, and lists access control in front of the frontend as a required step.
- `docs/DEPLOYMENT.md`: threat model and its explicit limits, the token and proxy wiring, the things that must still change (access control, TLS, Postgres, shared upload storage, quota, logs), the verification table, and a local smoke test.
- `API_TOKEN` and `BACKEND_URL` plumbed through `docker-compose.yml` and `.env.example`, both empty or loopback by default so the demo is unchanged.

Verified against a running stack on ports 8100 and 3100: direct `GET /personas` without a token returned 401, `/health` returned 200, the same call through the proxy returned 200, a POST passed a backend 404 through unchanged, and a multipart upload reached the backend intact (rejected with `synthetic_confirmation_required`, which is the expected validation).

Still open, and honestly so: no hosting provider, domain, TLS, or managed database exists. This is the one item that stays unchecked in `PROGRESS.md`.

## Verification

| Check | Result |
|---|---|
| Backend tests | 120 passed, and 120 in Docker |
| Frontend tests | 19 passed |
| Frontend lint and production build | clean |
| Live seed, all seven synthetic PDFs re-extracted | conflict persona 75, clean persona 100 |
| Fallback seed after regenerating the snapshot | conflict persona 75, clean persona 100, one `BANK-WILL-001` |
| Simulated fix then undo | 75 to 100, undo back to 75, `BANK-WILL-001` returns |
| Gap markers in code versus `RULES.md` | all seven documented; enforced by a test |
| Fresh clone to a working demo | 41 s, no API key, with Docker layers already cached locally |
| Token gate and proxy against a running stack | direct 401, proxied 200, multipart forwarded intact |
| Fallback exporter against a database with a simulated fix | refused, snapshot left untouched |

The core demo numbers are unchanged from Phase 5 onward: 75 for the conflict persona with a single `BANK-WILL-001` finding, 100 for the clean persona, 100 after the simulated fix.

## What did not change

No rule was added, removed, reworded, or re-sourced, and `rules_version` stays `1.0.0-candidate` (D-059). `detection.py` still imports no AI client. The estate-case view is still labelled a concept. Every finding still carries the mandatory disclaimer. Nothing here is legal advice.
