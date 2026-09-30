# Product Requirements Document (PRD) v3

## Title
JeevanSetu: AI Estate Conflict Detector and Continuity Vault

## 1. Problem Statement (sharpened)
People fill out nominee forms, write wills, and name insurance beneficiaries at different times, for different institutions, usually without any of those documents referencing each other. These documents frequently conflict — a nominee named on a bank account may differ from who the will assigns that same account to, or a will may attempt to override how a nominee-based asset transfers by law. Nobody notices until after a death, when the conflict becomes a legal dispute or a family conflict. This is the actual root cause underneath "settlement is chaotic" — not just a lack of a tracking dashboard.

## 2. Solution
JeevanSetu is an AI tool that:
1. Lets a person upload or describe their financial documents (will, nomination forms per account, insurance beneficiary forms).
2. Extracts, for each document, who is named for each asset and under what legal mechanism (nominee vs. beneficiary vs. bequest).
3. Cross-references all documents for the same person and flags conflicts: same asset, different named person across documents; a will clause that legally cannot override a nomination; missing nomination on an asset the will assumes is covered; outdated documents (dates, name mismatches).
4. Explains each conflict in plain language, with the specific clause/field cited, a plain-language description of the legal risk, and a concrete suggested fix ("update the nominee on Account X to match the will, or update the will").
5. Produces a Continuity Readiness Score and a prioritized fix-it list, so the tool has a reason to be used more than once (re-run after each fix).
6. (Stretch, only after the core is solid) A lightweight "estate case" view that shows what the settlement checklist would look like per institution, generated from the same conflict-free vault data — this is the tie-back to the original proposal's death-settlement idea, but it is explicitly secondary and simulated, not pitched as an institution-integrated product.

## 3. Why this wins over the original approach
- The demo's core value (finding a real conflict) is 100% real and self-contained — no institution, no ledger, no simulated integration is needed to make the "wow" moment land.
- It is narrow enough to build well in a short hackathon window instead of spreading effort across auth, a dashboard, a ledger, and connectors.
- It is technically substantive: multi-document extraction, cross-document reasoning, and legal-rule-based conflict detection are genuinely interesting to demo and to explain to judges.
- It sidesteps the "faked integration" credibility problem entirely — everything shown either truly works or is clearly labeled as a stretch/future feature, never presented as if it's connected to a real institution.

## 3a. Business Scale Narrative (for the pitch, not the build)

The conflict detector is the wedge, not the whole business. The reason this can be pitched as a large, durable company rather than a one-off tool:

**The wedge (what's built for the hackathon):** a sharp, free-to-try AI tool that finds real legal conflicts in a person's estate documents. This works as a standalone product because the value is immediate and self-contained — no institutional partnership needed to deliver it.

**Why it's a platform, not a feature:**
1. Every institution in India (banks, insurers, mutual funds, NPS) independently requires nominee data, and none of them cross-check against a person's will or each other. That structural gap doesn't close on its own — it's not a one-time inefficiency, it's baked into how these systems are legally and operationally separate. A tool that sits above all of them and reconciles the picture has a reason to exist indefinitely, not just once.
2. The conflict detector naturally pulls a user into building a fuller picture over time (upload one more nomination form, add an asset, update after a life event like marriage or a new child) — this is the Living Vault from the earlier version, but now it's an emergent consequence of using the conflict detector repeatedly, not a separate feature you have to convince someone to adopt upfront.
3. Once a user has a structured, conflict-checked estate graph, two expansion paths open naturally, and neither requires institutional integration to start monetizing:
   - B2C: paid deeper reviews, reminders to update documents after life events, a "family access" tier so a spouse or adult child can see the readiness picture.
   - B2B2C: banks, insurers, wealth managers, and estate-planning lawyers want their customers' nominee data to be conflict-free (it reduces disputes and claim delays for them too) — so the product can be offered to them as an embeddable check or referral funnel, without JeevanSetu needing to become the system of record for anyone's actual account data. This avoids the trust/integration problem the original proposal ran into, because JeevanSetu never needs write access to real accounts — only documents the user chooses to upload.
4. The death-settlement workflow (checklist generation, case tracking) becomes viable later specifically because the hard data problem — incomplete, unverified, conflicting nominee/will data — has already been solved earlier in the user's life by the conflict detector. This is the same insight as before (fix the root cause, not just the symptom) but now it's a believable second act built on a working first product, not a simultaneous, harder-to-build second product.

**One line for the pitch:** "Every year, unresolved nominee-vs-will conflicts turn routine claims into disputes and delayed settlements. We built the tool that catches them while someone's still alive to fix them — and that's also the data foundation for making settlement itself instant, later."

## 4. Legal Ground Rules (must hold throughout)
- This tool never gives binding legal advice and never claims to. Every conflict explanation must include a one-line disclaimer that it is not legal advice and a licensed advisor should review real conflicts.
- Nominee-vs-beneficiary rules vary by jurisdiction and asset type (bank accounts, insurance, mutual funds, NPS each have different legal treatment in India). The conflict-detection rule set must be explicitly documented, sourced from publicly available, verifiable explanations of these rules (RBI/IRDAI/PFRDA guidance, or reputable legal explainer sources), and clearly scoped to "rules as commonly understood for these asset types in India" — not asserted as exhaustive or authoritative.
- All demo documents are synthetic. No real wills, IDs, or financial documents are ever used, uploaded, or referenced.

## 5. Core Features (build order)
1. Document upload + AI extraction: classify document type (will / nomination form / insurance beneficiary form) and extract structured fields (asset/account reference, named person, relationship, mechanism type, date).
2. Conflict Detection Engine: a documented, testable rule set that takes extracted structured data across all of a person's documents and outputs a list of conflicts, each with: the two conflicting sources, a plain-language explanation, a severity level, and a suggested fix.
3. Continuity Readiness Score: derived from the conflict list plus basic completeness checks (e.g., an asset with no nomination at all).
4. Results view: per-conflict cards (source A vs source B, explanation, fix suggestion), overall score, "what to fix first" ordering by severity.
5. Vault (lightweight): lets a user store multiple documents over time and re-run detection after edits, so the demo can show the score improving live.
6. Stretch only, after 1-5 are solid and polished: a simulated "estate case" view showing what a settlement checklist would look like per institution type, generated from the (by now conflict-free) vault — explicitly labeled as a concept/future feature in the UI, not a working integration.

## 6. Technology Stack (chosen for hackathon speed + M4 feasibility)
- Frontend: Next.js + React + Tailwind. Single app, minimal auth (or no auth at all for the demo — one seeded "session" is fine and should be explicitly noted as a demo simplification).
- Backend: Python, FastAPI.
- Database: SQLite for the hackathon (Postgres is unnecessary complexity for a single-demo build; note this as a deliberate simplification, easy to swap later).
- AI: Claude API for document classification, structured field extraction (vision for scanned/PDF documents, text for typed ones), and generating the plain-language conflict explanations. The actual conflict LOGIC (which combinations count as a conflict) is deterministic, rule-based Python code that consumes the AI's structured extraction — the AI does not decide what counts as a legal conflict on its own, to keep conflict detection explainable and testable.
- Deployment: Docker Compose (frontend + backend) for local dev on the M4; a single free-tier cloud deploy (Vercel for frontend, Render/Railway for backend) for a live judging link, if time allows.
- Dropped from the previous version: Postgres-backed ledger, hash chaining, InstitutionConnector interfaces, Drunix adapter. These added real build time for a payoff that isn't the demo's core value. If you want the ledger/consent story back in for narrative reasons, it can be reintroduced in a later phase as a simple "audit log" table — flagged in this PRD as intentionally cut for scope.

## 7. Success Criteria for the Demo
- A judge can, in under 4 minutes: watch you upload 2-3 synthetic documents for one persona (a will and two nomination forms with a deliberate conflict built in), see the AI extract the relevant fields, see the Conflict Detection Engine surface the real conflict with a clear plain-language explanation and fix suggestion, see the Readiness Score, then watch the score improve after a one-field fix.
- Every rule used for conflict detection is written down and shown/explainable, not a black box.
- No claim of legal authority, institutional integration, or real data handling is made anywhere in the UI or pitch.
- The repo has a clean README explaining the rule set, what's real vs. simplified for the demo, and a one-command way to run it.

## 8. Risks and Mitigations
- Risk: legal rules are genuinely jurisdiction- and case-specific, and an oversimplified rule set could produce a wrong or misleading conflict. Mitigation: keep the rule set narrow (a handful of well-documented, sourced rules) rather than broad and unverified; disclaimer on every result; document sources in the README.
- Risk: AI extraction is unreliable live. Mitigation: test extensively against the exact demo documents beforehand; have a pre-verified fallback result ready in case of a live API hiccup.
- Risk: scope creep back toward the old dashboard-heavy version. Mitigation: the stretch feature (Section 5.6) is explicitly last, and only attempted once 1-5 are demo-polished.
- Risk: "not legal advice" framing undercuts the pitch's impact. Mitigation: frame it in the pitch as "a first-pass conflict scanner that tells you exactly what to ask a lawyer or your bank about," which is honest and still valuable.