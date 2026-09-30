# Phase 4 report — Deterministic conflict detection engine

Date: 2026-09-29

Status: Complete; awaiting user review

Implementation commit: `46c87f4203c14ddd9dafe62965a39ca46342222a`

Completion tag: `phase-4-done`

## Completed

- Added `backend/app/detection.py` as the single place a conflict is decided. It is a pure function over extracted records plus explicitly confirmed persona context and imports no AI client.
- Implemented all seven approved rules with the documented predicates, severities, deterministic summaries, scope notes, and suggested actions.
- Implemented the documented execution order and suppression: `NPS-VALIDITY-001` before `NPS-WILL-001` by nomination group, `LIFE-NOTICE-001` before `LIFE-WILL-001` by source pair, and deduplication by rule, asset, and source pair.
- Emitted labeled `GAP-*` markers for excluded cases instead of forcing them through the nearest rule.
- Added `backend/app/explanations.py`, which only rephrases an already-fixed finding and is rejected outright if it states a legal conclusion.
- Expanded the `conflicts` table to the full finding contract and bumped the schema version with an enforced guard.
- Added `POST /personas/{id}/detections` and `GET /personas/{id}/detections/latest`.

## Acceptance evidence

| Check | Result |
|---|---|
| Conflict persona (live, real extraction) | Exactly one `BANK-WILL-001`, severity high, asset `SB-DEMO-4821` |
| Clean persona (live) | 0 conflicts, 0 gaps |
| Both sources on the conflict | Bank nomination (Kavya Demo-Mehta) and will clause 3.1 (Anika Demo-Mehta) |
| Plain-language explanation | Generated live by Gemini, with no legal conclusion |
| Disclaimer | Exact text on every finding and on the run payload |
| Readiness score | `null` (Phase 5 scope) |
| Tests | 72 passed locally and in Docker |
| AI involvement in rule decisions | None; asserted by test |

Every rule has positive and negative unit coverage. Detection integration tests seed the Phase 3 manifest directly, so no rule decision depends on a model call.

## Semantic review and fixes

An independent pre-commit review blocked the first implementation. Three high-severity defects each deleted a finding the rules require, and all were fixed and covered by regression tests:

1. `LIFE-NOTICE-001` treated any later acknowledgement as proof the change reached the insurer, even when it still recorded the previous nominee. It now also requires the registered nominee to be the person the will names.
2. The `NPS-VALIDITY-001` marriage branch searched every NPS nomination for the persona, so a confirmed nomination on a different PRAN silenced the warning. It is now restricted to the same account.
3. `RECORD-SUPERSESSION-001` could treat a confirmed group with no acknowledgement date as the winner, which is the "newest dated document wins" inference the rules forbid. A winner now requires a real registration date.

Also addressed: a supersession scope gate with `GAP-UNSUPPORTED-SUPERSESSION`; a new `GAP-ASSET-NEAR-MATCH` for truncated references and institution-name variants that previously read as clean; `GAP-` namespacing documented in `RULES.md`; a run-level disclaimer; deterministic rejection of model wording that claims a legal outcome; neutralization of the prompt delimiter; a cap on per-request explanation calls; a real schema-version comparison with tests for the legacy `conflicts` table; a test pinning engine text to `RULES.md`; and share normalization so a sole nominee's omitted share is not read as a different nominee set.

## Known limitations (recorded, not hidden)

- `BANK-WILL-001` and `MF-WILL-001` are scoped to individually held accounts and sole-holder folios, but the extraction schema has no holding-pattern field, so a joint holding cannot yet be excluded. Documented in `RULES.md` section 13.
- Gap markers are engine labels, not approved legal rules.
- Explanation wording is supplementary; the deterministic summary, scope note, actions, and disclaimer are always authoritative.
- The detection endpoint is unauthenticated and loopback-only, consistent with D-022.

## Not completed

- No readiness score, results UI, vault, or simulated fix flow (Phase 5).
- No new legal rule, and no change to the approved rule semantics or `rules_version`.

## Run/demo

```bash
docker compose up --build --detach backend
cd backend && .venv/bin/python scripts/verify_phase3_live.py
curl -s -X POST http://localhost:8000/personas/1/detections | python3 -m json.tool
curl -s -X POST 'http://localhost:8000/personas/2/detections?explain=false' | python3 -m json.tool
```

## Phase boundary

Stop here. Phase 5 must not start until the user replies exactly:

`APPROVED PHASE 4`
