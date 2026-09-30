# JeevanSetu decisions and deviations

This is a dated, append-only project log. Legal-rule entries must identify a public source and scope. Uncertain rules must be flagged rather than inferred.

## 2026-09-29 — Phase 0

### D-001 — User prompt takes precedence over PRD v3

**Decision:** Follow the user's phase plan where it differs from the supplied PRD.

**Recorded conflicts:**

1. The prompt adds `source clause/field text` to the extraction schema; PRD Section 5.1 omits it. The draft `extracted_fields.source_text` column is included.
2. PRD Section 5 puts extraction first; the prompt requires legal-rule research in Phase 1 before extraction in Phase 2. The prompt order is binding.
3. The prompt names the attachment `PRD_JeevanSetu_v3.md`; the workspace supplied it as `PRD.md`. It is retained as `docs/PRD.md`.

### D-002 — Phase 0 contains no legal or nominee rules

**Decision:** Do not encode, summarize, or assume any nominee-vs-beneficiary-vs-will legal rule during setup. Research and source selection belong exclusively to Phase 1 and require user approval before detection logic is built.

**Legal source:** Not applicable; no legal rule was adopted in Phase 0.

### D-003 — Add `detection_runs` to the draft schema

**Decision:** Add a fifth table to preserve a persona's rules version and score per run. This supports the Phase 5 before/after score demonstration without adding an abstraction layer.

**Alternative:** Store only current conflicts and calculate a transient current score. Rejected because it cannot directly preserve score history.

### D-004 — Use standard-library SQLite access

**Decision:** Use Python's `sqlite3` directly, with an idempotent SQL schema and foreign keys enabled on every connection. Do not add SQLAlchemy or a migration framework.

**Reasoning:** Five small tables do not justify extra hackathon complexity. During development, schema-breaking changes may reset the ignored synthetic database and reseed it.

### D-005 — No authentication in the hackathon scaffold

**Decision:** Do not add users, login, or sessions in Phase 0. A `persona` represents one synthetic person/scenario.

**Reasoning:** PRD Section 6 explicitly permits no authentication for the demo; adding it would not advance the core conflict-detection demonstration.

### D-006 — Browser calls FastAPI directly

**Decision:** `HealthStatus` uses `NEXT_PUBLIC_API_URL` and FastAPI has an explicit `CORS_ORIGINS` allowlist. Do not add a Next.js proxy layer.

**Reasoning:** This remains simple locally and maps cleanly to a possible Vercel/Render split deployment. A proxy would add a layer and may complicate later document upload sizing.

### D-007 — Compose is production-style; local tools provide hot reload

**Decision:** Compose builds production frontend/backend images. Developers who need hot reload run `uvicorn --reload` and `npm run dev` directly.

**Reasoning:** The acceptance path should resemble a reproducible demo, while development remains fast without Docker bind-mount complexity.

### D-008 — SQLite persists through a host bind mount

**Decision:** Mount `./backend/data` at `/app/data`; do not add a database service or named volume.

**Reasoning:** The database file stays visible, resettable, and persistent across `docker compose down` without a third service.

### D-009 — Exact direct dependency versions

**Decision:** Pin every direct Python and npm dependency to the resolved exact version. Commit npm's lockfile for transitive reproducibility.

**Reasoning:** Avoid unexpected version drift during the hackathon. No Claude SDK is added before Phase 2.

### D-010 — Tests are included in the backend image

**Decision:** Copy `backend/tests` and `pytest.ini` into the backend image and keep pytest/httpx in the single pinned requirements file.

**Reasoning:** This enables the required `docker compose run --rm backend pytest` acceptance command. The modest image-size increase is acceptable for this prototype.

### D-011 — Required disclaimer is enforced in storage

**Decision:** The draft `conflicts.disclaimer` column is non-null and rejects blank text.

**Reasoning:** This provides defense in depth for the requirement that every future result carry a not-legal-advice disclaimer. UI/API enforcement will still be required in later phases.

### D-012 — Preserve only synthetic smoke-test data

**Decision:** Docker persistence validation inserts the persona name `Synthetic Persistence Check`; the SQLite file is ignored by Git.

**Reasoning:** No real personal or financial data is needed for infrastructure validation.

## 2026-09-29 — Phase 1

### D-013 — Phase 0 approved; Phase 1 unlocked

**Decision:** The user supplied the exact phrase `APPROVED PHASE 0`. Phase 1 may proceed; Phase 2 remains blocked pending exact Phase 1 approval.

### D-014 — Rules identify review conflicts, not legal winners

**Decision:** Every rule reports document inconsistency, registration uncertainty, or an express validity warning. No rule determines ownership, heirship, will validity, probate effect, or which person legally prevails.

**Reasoning:** Institutional payment/transmission rules and beneficial succession can differ, and outcomes can depend on personal law and facts outside the extracted documents. This is reflected in the mandatory disclaimer and per-rule scope notes.

### D-015 — Seven candidate rules and their controlling sources

**Decision:** Adopt the following candidate set for user review. Full citations, source reasoning, pseudocode, exclusions, and examples are in `backend/rules/RULES.md`.

| Rule | Primary source |
|---|---|
| `BANK-WILL-001` | Supreme Court of India, *Ram Chander Talwar v. Devender Kumar Talwar*, applying Banking Regulation Act section 45ZA |
| `LIFE-NOTICE-001` | Insurance Act, 1938, sections 39(2)–(3), current consolidated text hosted by IFSCA |
| `LIFE-WILL-001` | Insurance Act, 1938, sections 39(6)–(7), with sections 38 and 39(12) as exclusions |
| `MF-WILL-001` | SEBI Circular dated 28 February 2025 and its Annexure A for mutual-fund folios |
| `NPS-WILL-001` | PFRDA NPS Exit Regulations, consolidated through 20 July 2026, Chapter VII |
| `NPS-VALIDITY-001` | Same PFRDA regulation, nomination provisos (iv)–(vi) |
| `RECORD-SUPERSESSION-001` | The registration/receipt/supersession provisions in the bank, insurance, MF, and NPS sources above |

### D-016 — Explicit uncertainty and exclusions

**Decision:** Do not automate outcomes for joint accounts, survivorship clauses, lockers, general insurance, MWP Act section 6 policies, active insurance assignments, demat shares, trusts, foreign assets, legal-heir identity, or ambiguous family relationships. NPS nominee-versus-will beneficial ownership is explicitly unresolved by the cited PFRDA source; `NPS-WILL-001` therefore requires review and declares no winner.

**Reasoning:** A reliable, narrow rule is preferable to an unsupported broad rule. Unknown legal status produces a manual-review/scope gap, not a guessed conflict.

### D-017 — Do not treat the March 2026 SEBI consultation as operative law

**Decision:** Record the consultation as a re-check warning only. Do not source an active rule from its draft circular.

**Reasoning:** The located document requests public comments and contains placeholders. Phase 6 must check whether SEBI has since issued a final superseding circular.

### D-018 — Phase 1 informs Phase 2 extraction fields without changing the schema yet

**Decision:** `RULES.md` records additional provenance/status fields needed by deterministic rules: registration and acknowledgement status, explicit nomination action, policy type, MWP/assignment scope, confirmed family context, marriage date, document grouping, and manually confirmed aliases. Do not alter the Phase 0 database in this research phase.

**Reasoning:** Rule research should drive extraction requirements, but schema/API implementation belongs to Phase 2 and requires Phase 1 approval.

### D-019 — PDF parser is research-only

**Decision:** Install `pypdf==6.19.0` only in the ignored local virtual environment to inspect official PDF sources. Do not add it to application requirements.

**Reasoning:** The official sources were PDF-only and the web text fetcher does not parse PDFs. The package is not needed by the product and no source document or real personal data was saved to the repository.

## 2026-09-29 — Phase 2

### D-020 — User-approved provider deviation: Gemini replaces Claude

**Decision:** Replace the unfinished Claude API adapter with the Gemini Developer API for Phase 2 classification/extraction and future plain-language explanations. Use `google-genai==2.25.0` and default to `gemini-3.1-flash-lite`. Do not retain a second provider abstraction.

**Prompt/PRD conflict:** The original non-negotiable principle and PRD specify Claude. The user subsequently instructed: “use Gemini Developer API free tier instead of Claude for Phase 2 extraction and explanations.” The later explicit instruction wins. The product, configuration, rules documentation, tests, and reports must say Gemini rather than implying Claude remains integrated.

**Reasoning:** The user does not have paid Anthropic API access. Google documents a Gemini Developer API free tier, structured JSON output, and PDF/image understanding. `gemini-3.1-flash-lite` is documented as multimodal and intended for simple extraction. The provider swap does not change the approved legal rules or deterministic conflict boundary.

**Privacy/cost disclosure:** Google states that free-tier content may be used to improve its products. Therefore this free-tier integration is restricted to synthetic documents and must never be used with real personal, identity, financial, insurance, or estate material. A paid/private deployment would require a separate data-handling review.

**Sources checked:**

- Gemini Developer API pricing: https://ai.google.dev/gemini-api/docs/pricing
- Structured outputs: https://ai.google.dev/gemini-api/docs/structured-output
- Document/PDF processing: https://ai.google.dev/gemini-api/docs/document-processing
- Gemini 3.1 Flash-Lite model: https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite

### D-021 — Phase 2 storage and schema reset policy

**Decision:** Keep five SQLite tables and extend the Phase 0 columns directly. Use `PRAGMA user_version = 2`; detect the legacy Phase 0 shape before applying indexes and return a precise synthetic-database reset instruction. Recover any `extracting` rows to `failed/extraction_interrupted` at startup.

**Reasoning:** The database is synthetic and resettable, so a migration framework remains unnecessary. Silent partial upgrades or obscure missing-column crashes are not acceptable.

### D-022 — Local upload service is loopback-only

**Decision:** Bind Compose ports 3000 and 8000 to `127.0.0.1`. The boolean synthetic attestation is a user warning and request gate, not proof that content is synthetic. Do not deploy the keyed upload API publicly without trusted access controls and a separate data-handling review.

**Reasoning:** CORS and caller attestation do not prevent arbitrary network clients from forwarding real material to a free-tier provider.

### D-023 — Extraction failure semantics

**Decision:** Retain the uploaded synthetic file for retry but delete stale extracted-field rows when an attempt fails. Serialize extraction transitions, return HTTP 409 for an already-running attempt, recover interrupted attempts on startup, and distinguish retryable transient provider failures from configuration/permanent provider failures.

### D-024 — Live Gemini acceptance evidence

**Decision:** Treat the user's instruction “you verify and continue” as delegation of the Phase 2 manual comparison. Every stored field from five live synthetic extractions was compared against its source fixture. All classifications, dates, references, people, relationships, mechanisms, shares, registration states, policy scope, unknown legal statuses, and source excerpts were reasonable and source-supported.

**Observed fallback:** The fifth (NPS) request received a transient free-tier provider error. The document remained stored with an honest failed status and succeeded through `POST /documents/11/extract`; no extraction was fabricated.

## 2026-09-29 — Phase 3

### D-025 — Phase 2 approved; Phase 3 unlocked

**Decision:** The user supplied `APPROVED PHASE 2`. Phase 3 may create synthetic demo documents; Phase 4 remains blocked.

### D-026 — One isolated BANK-WILL-001 demo conflict

**Decision:** The conflict persona uses exact account reference `SB-DEMO-4821` at fictional Sampurna Demo Bank Ltd. The will names daughter Anika Demo-Mehta; the bank nomination names spouse Kavya Demo-Mehta. This is an expected `BANK-WILL-001` review conflict, not a statement that either person legally prevails.

**Reasoning/source:** The documents satisfy the approved rule's same-asset/different-person predicate in `backend/rules/RULES.md`. Life policy `LIFE-DEMO-7710` and mutual-fund folio `MF-DEMO-2040` both name Anika across sources so the demo does not accidentally create extra conflicts.

### D-027 — Clean control persona

**Decision:** Rohan Demo-Sen's will and forms all name spouse Mira Demo-Sen for exact bank reference `SB-DEMO-8120` and life-policy reference `LIFE-DEMO-9912`. Expected conflicts are empty, without claiming the estate plan is legally complete.

### D-028 — Reviewable HTML sources and committed PDFs

**Decision:** Keep editable HTML under each persona's `source/` folder and generated one-page PDFs under `documents/`. Every page visibly says synthetic/not valid/not legal advice. Use invented institutions and references containing `DEMO`; include no real IDs, addresses, contact details, signatures, or account data.

### D-029 — Nonnumeric “all” bequests do not require an inferred share

**Decision:** The manifest accepts `share_percent` as null or 100 for will language giving “all” of an asset. Nomination forms retain exact numeric percentages.

**Reasoning:** Both representations preserve the named recipient, but null avoids forcing a numeric fact absent from the clause. Conflict rules compare named people and exact assets, not will share percentages in this demo.

## 2026-09-29 — Phase 4

### D-030 — Phase 3 approved; Phase 4 unlocked

**Decision:** The user supplied `APPROVED PHASE 3` after a full pre-phase audit. Phase 4 may implement the deterministic engine; Phase 5 remains blocked.

### D-031 — The engine is a pure function with no AI dependency

**Decision:** `backend/app/detection.py` decides every conflict from structured records plus explicitly confirmed persona context. It imports no model client. A test asserts the module source contains no AI reference and that constructing a client during detection fails.

**Reasoning:** Conflict results must be explainable and testable without re-calling a model, per PRD section 6 and `RULES.md` section 1.

### D-032 — Excluded cases become labeled gap markers, never forced conflicts

**Decision:** Unsupported cases emit `GAP-LIFE-SCOPE`, `GAP-NPS-RELATIONSHIP`, `GAP-ASSET-REFERENCE`, `GAP-ASSET-NEAR-MATCH`, or `GAP-UNSUPPORTED-SUPERSESSION`, all severity `low` and finding type `scope_gap`. They are documented in `RULES.md` section 12 and are not approved rules.

**Reasoning:** `RULES.md` section 9 requires unsupported cases to be labeled manual review required. A silent clean result would be misleading.

### D-033 — Gap findings are stored in the existing findings table

**Decision:** Persist gaps in the `conflicts` table with `finding_type='scope_gap'` rather than adding a sixth table. API responses separate `conflicts` from `scope_gaps`, and gaps never count as conflicts.

**Reasoning:** Keeps the schema small for the hackathon while making gaps durable and re-readable after a run.

### D-034 — Documented relationship normalization

**Decision:** Free-text relationships are mapped deterministically to spouse/child/parent for `LIFE-WILL-001` severity, and to an explicit non-family set for `NPS-VALIDITY-001`. Anything else is ambiguous, which yields medium severity or a gap rather than a validity conclusion. The tables are recorded in `RULES.md` section 13.

### D-035 — Model wording is rejected if it states a legal outcome

**Decision:** Gemini explanations are validated after generation against a forbidden-claim list. A rejected or failed explanation falls back to `explanation_source='unavailable'`, and the deterministic summary, scope note, actions, and disclaimer are still returned.

**Reasoning:** A system prompt alone is not a control. Explanation wording must never acquire the engine's authority.

### D-036 — Three suppression defects found by review were corrected

**Decision:** An insurer acknowledgement only suppresses `LIFE-NOTICE-001` when it names the will's person; the `NPS-VALIDITY-001` marriage branch only considers the same NPS account; and a supersession winner requires a real registration date rather than a file date.

**Reasoning:** Each original predicate deleted a finding the approved rules require, and the "newest dated document wins" inference is an explicit non-rule.

### D-037 — Known joint-holding limitation is recorded, not worked around

**Decision:** `BANK-WILL-001` and `MF-WILL-001` scope limits for joint accounts and demat-only holdings cannot be enforced because the extraction schema has no holding-pattern field. This is documented in `RULES.md` section 13 instead of being silently ignored or guessed.

### D-038 — Explanation fan-out is capped per request

**Decision:** At most 10 findings per detection run receive a model-generated explanation. Remaining findings still return complete deterministic content.

**Reasoning:** Bounds free-tier usage and request duration on an unauthenticated local endpoint.

## 2026-09-29 — Phase 5

### D-039 — Phase 4 approved; Phase 5 unlocked

**Decision:** The user supplied `APPROVED PHASE 4`. Phase 5 may add scoring and the results UI; Phase 6 remains blocked.

### D-040 — Deterministic score formula

**Decision:** Continuity Readiness Score = 100 − (25 × high findings) − (10 × medium findings) − (3 × gaps), clamped to 0-100. The API returns a breakdown so the subtraction is visible in the UI.

**Reasoning:** The score must be explainable and reproducible without an AI call. The weights are a review-priority heuristic, not a legal or actuarial measure, and the UI says so.

### D-041 — Missing nomination is a Phase 5 completeness gap

**Decision:** A will-assigned asset with no uploaded nomination emits `GAP-MISSING-NOMINATION` as a `scope_gap` at low severity, never as a conflict.

**Reasoning:** `RULES.md` section 9 explicitly classifies a missing nomination as a Phase 5 completeness gap rather than a Phase 4 conflict.

### D-042 — Completeness gaps pass through the engine's dedupe and ordering

**Decision:** The route merges engine findings with completeness gaps and runs the shared `finalize()` pass. A bequest already covered by `GAP-ASSET-NEAR-MATCH` does not also produce `GAP-MISSING-NOMINATION`.

**Reasoning:** Review found that concatenating outside the dedupe double-deducted and produced a card falsely stating no nomination was uploaded when one was.

### D-043 — Conflicts and gaps are separated by finding type, not severity

**Decision:** The score breakdown counts conflicts and gaps by `finding_type`, and reports high, medium, and low conflict counts separately from gaps.

**Reasoning:** A severity-based split displayed a validity warning as a conflict and would display any future low-severity conflict as a review gap.

### D-044 — Simulated fixes never touch source evidence

**Decision:** `PATCH /fields/{id}` changes only the extracted `person_name` or `relationship` and sets `is_user_edited`. The uploaded file, `source_text`, `source_locator`, confidence, and raw extraction payload are untouched. The UI labels the quote as the original extracted text and states that no real institution record changes.

**Known limitation:** there is no undo. Re-running extraction restores the extracted value from the stored synthetic document.

### D-045 — Extraction retry will not silently discard simulated fixes

**Decision:** Retrying extraction on a document with user-edited fields returns HTTP 409 unless `force=true` is supplied.

**Reasoning:** Re-extraction replaces every extracted row for the document, which would erase a demonstrated fix without warning.

### D-046 — Null scores are shown honestly

**Decision:** A detection run recorded before scoring existed has a null score, and the UI shows an explicit "not scored, re-run detection" state rather than rendering zero.

**Reasoning:** Coercing null to zero showed the clean persona as the worst possible result next to a no-conflict panel.

### D-047 — No frontend test runner in this phase

**Decision:** Verify the UI with ESLint, a production build, rendered-DOM assertions, and a screenshot instead of adding a JavaScript test framework now.

**Reasoning:** Adding a second test toolchain is scope the hackathon does not need yet. This is recorded as a gap rather than presented as covered.

## 2026-09-29 — Phase 6

### D-048 — Phase 5 approved; Phase 6 unlocked

**Decision:** The user supplied `APPROVED PHASE 5`. Phase 6 may polish the demo; Phase 7 remains blocked.

### D-049 — Pre-demo source re-check outcome

**Decision:** Re-verified all five primary sources on 2026-09-29. Every link returns HTTP 200. SEBI's March 2026 publication is still a consultation paper containing a draft circular with a placeholder number, so `SRC-MF-01` (the 28 February 2025 circular) remains operative and `rules_version` stays `1.0.0-candidate`.

**Reasoning:** `RULES.md` section 11 requires a re-check before the demo freeze and forbids sourcing a rule from a draft.

### D-050 — Pre-verified fallback seed is labelled, never disguised

**Decision:** The default seed mode inserts a snapshot of previously verified live Gemini extraction, stores `extraction_source='manual_fallback'`, and the vault displays "Pre-verified fallback data, not a live AI extraction". A `--mode live` option performs real extraction.

**Reasoning:** PRD section 8 calls for a pre-verified fallback against a live API hiccup, and the non-negotiable principles forbid presenting anything as more real than it is. The fallback also lets a fresh clone demo without an API key.

### D-051 — Demo reset requires explicit confirmation

**Decision:** `scripts/seed_demo.py` refuses to run without `--yes` because it deletes the generated synthetic database and uploads.

**Reasoning:** The deletion is destructive even though the data is synthetic and gitignored.

### D-052 — Sanitized global error handler

**Decision:** Unhandled server exceptions return a fixed `internal_error` payload and log only the exception type. Document text, model payloads, and stack details are never returned to the client.

### D-053 — No cloud deployment in this build

**Decision:** Skip the optional live deployment. The demo runs on local Docker Compose bound to loopback.

**Reasoning:** The API is unauthenticated and holds a provider key. D-022 requires access controls and a data-handling review before any public exposure, which is out of scope for this hackathon. Recorded as not done rather than partially attempted.

## 2026-09-29 — Phase 7 (stretch)

### D-054 — Phase 6 approved; stretch feature unlocked

**Decision:** The user supplied `APPROVED PHASE 6`. The PRD section 5.6 concept view may be built.

### D-055 — The concept lives on its own page, not inside the results

**Decision:** The estate-case view is a separate route reached from one clearly marked card. No existing result surface changed.

**Reasoning:** The stretch feature must not compromise the core demo's polish or credibility. Keeping it separate means it can be skipped in a time-constrained pitch and cannot be mistaken for a result.

### D-056 — Concept labelling is enforced in the payload and the UI

**Decision:** The endpoint returns `concept: true`, the fixed label `Concept / Future Feature`, and a notice stating that no institution is connected. The page shows a persistent banner, a dashed concept panel, an "Illustrative only" label on every card, the disclaimer, and a footer repeating the limitation.

**Reasoning:** Non-negotiable principle 4 requires the stretch feature to be visibly labelled. Putting the label in the API response means a future consumer cannot drop it.

### D-057 — Illustrative steps are not sourced rules

**Decision:** The per-asset steps are generic placeholders and are deliberately not added to `RULES.md`, given no rule IDs, and excluded from detection and scoring. The generator imports no AI client and makes no network call.

**Reasoning:** Adding unsourced procedural claims to the rule document would undermine the discipline that every rule is sourced. These steps are illustrative interface content, not findings.

## 2026-09-29 — Recorded gap closure

The user asked for all four recorded gaps to be closed. These decisions supersede the limitations noted in D-037 and D-045 and narrow, but do not remove, D-053.

### D-058 — Holding pattern is extracted, and `unknown` stays in scope

**Decision:** `extracted_fields.holding_pattern` carries exactly `single`, `joint`, or `unknown`, populated by the extraction prompt and schema. `BANK-WILL-001`, `MF-WILL-001`, and `RECORD-SUPERSESSION-001` read it from the nomination record and emit `GAP-JOINT-HOLDING` instead of a conflict when it is `joint`. `unknown` is treated as in scope.

**Reasoning:** This closes D-037: the single-holder scope the rules always claimed is now enforced by code rather than described as an unmet limitation. `unknown` had to stay in scope because most real forms do not state a holding pattern; gapping `unknown` would silently skip the majority of records and report manual-review-required where the rules could in fact be applied. The residual risk, that a joint asset extracted as `unknown` can still be reported as a conflict, is documented in `RULES.md` section 14 and the README rather than hidden.

**Rejected:** treating `unknown` as out of scope, and inferring holding pattern from the number of named holders, which would be a guess about the asset dressed as an extraction.

### D-059 — `rules_version` stays `1.0.0-candidate`

**Decision:** Enforcing the holding-pattern scope does not bump `rules_version`.

**Reasoning:** No rule proposition, source, severity, or predicate changed. Sections 7 and 9 already scoped these rules to individually held assets; the engine previously could not enforce that and said so. The version identifies the rule set, and the rule set is the same. The behaviour change and its date are recorded here and in the gap-closure report instead.

### D-060 — Undo is an audit trail, not a field rollback

**Decision:** Every simulated fix that actually changes a value appends a row to a new `field_edits` table holding the previous and new values. `POST /fields/{id}/undo` reverts the most recent edit that has not been undone, marks it `undone_at`, and clears `is_user_edited` only when no earlier edit remains. Undo itself deletes nothing. Undoing a field with no edit returns `409 no_edit_to_undo`, and saving a value identical to the current one is not recorded as an edit at all.

**Boundary, corrected after review:** the log is keyed to the extracted field rows and cascades with them, so a forced re-extraction (`POST /documents/{id}/extract?force=true`) replaces the document's fields and removes their edit history with them. That is the documented way to discard simulated fixes and it already requires an explicit `force=true`, so the loss is deliberate rather than silent, but "nothing is ever deleted" would have been wrong. A test pins this behaviour.

**Reasoning:** This closes the D-045 limitation. A demo that can change a record must be able to show what it changed and put it back; overwriting the value in place would lose exactly the evidence that makes the fix honest. A stack also makes repeated edits reversible one step at a time, which a single `previous_*` column pair could not do.

**Rejected:** `previous_person_name` and `previous_relationship` columns on `extracted_fields`, which support only one level of undo and keep no history.

### D-061 — Frontend tests cover the components that carry the safety labels

**Decision:** Added Vitest, Testing Library, and jsdom at pinned versions with `npm test`, and 19 tests over `ScoreCard`, `FindingCard`, and `VaultPanel`.

**Reasoning:** These three components render everything the project promised never to misstate: the null-score state, the conflict-versus-gap distinction, the disclaimer, the "not a live AI extraction" label, the original extracted quote next to an edited value, and the joint-holding scope notice. A lint and a production build cannot catch a regression in any of those. Pages and the proxy route are still verified by hand, which the README says.

### D-062 — Deployment readiness is built; deployment itself is not done

**Decision:** Added an optional `API_TOKEN` bearer gate, off by default with `/health` exempt, and a Next.js server-side proxy route so a hosted frontend never ships the token to the browser. Wrote `docs/DEPLOYMENT.md`. No environment was provisioned.

**Reasoning:** D-053 refused cloud deployment because it would expose a keyed, unauthenticated API. The gate narrows that: the backend is no longer reachable directly and the key never reaches the browser. Actually deploying still needs the user's hosting accounts, a domain, TLS, and a decision to expose the API, none of which an agent should do on their behalf.

**Scope limit, corrected after review:** the gate is not authentication and the proxy relays anonymously. With the frontend published, the upload path is still open to anyone holding the URL. The first draft of the runbook said the token gate "closes exactly that", which overstated it. `docs/DEPLOYMENT.md` now names the limit in the threat model, repeats it next to the wiring, and lists access control in front of the frontend as a required step rather than an optional hardening. D-053's objection is therefore narrowed, not removed.

**Rejected:** inventing a per-user authentication layer, which this prototype has no accounts for and which would be a far larger change than a gap closure; and putting the token in a `NEXT_PUBLIC_*` variable, which would publish it in the browser bundle.

### D-063 — The fallback snapshot is exported from live output, never hand-edited

**Decision:** `backend/scripts/export_demo_fallback.py` regenerates `app/demo_fallback.json` from a live-seeded database and refuses to export any document whose `extraction_source` is not `gemini`.

**Reasoning:** The snapshot is labelled `manual_fallback` and described as previously verified live extraction. Hand-adding the new `holding_pattern` values would have quietly made that description false.
