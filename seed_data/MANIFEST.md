# Phase 3 synthetic demo document manifest

> **All people, institutions, identifiers, signatures, and events in this folder are fictional. These documents are not valid, are not legal advice, and must never be submitted to a real institution.**

The HTML files under each `source/` directory are the editable sources. The PDFs under `documents/` are the actual Phase 3/4/6 demo uploads. `expected_extractions.json` is the machine-readable verification target.

## Conflict persona — Aarav Demo-Mehta

| Document | Date | Expected assets/people |
|---|---:|---|
| `conflict_persona/documents/01_will.pdf` | 2026-01-12 | SB-DEMO-4821 → Anika Demo-Mehta; LIFE-DEMO-7710 → Anika Demo-Mehta; MF-DEMO-2040 → Anika Demo-Mehta |
| `conflict_persona/documents/02_bank_nomination.pdf` | 2023-05-15 | SB-DEMO-4821 → Kavya Demo-Mehta, spouse, 100%; recorded 2023-05-18 |
| `conflict_persona/documents/03_insurance_nomination.pdf` | 2025-08-10 | LIFE-DEMO-7710 → Anika Demo-Mehta, daughter, 100%; life policy; MWP false; no assignment; recorded 2025-08-12 |
| `conflict_persona/documents/04_mutual_fund_nomination.pdf` | 2025-08-11 | MF-DEMO-2040 → Anika Demo-Mehta, daughter, 100%; recorded 2025-08-13 |

### Intended Phase 4 outcome

Exactly one expected review conflict:

- **Rule:** `BANK-WILL-001`
- **Asset:** Sampurna Demo Bank Ltd. account `SB-DEMO-4821`
- **Source A:** will clause 3.1 names daughter **Anika Demo-Mehta**.
- **Source B:** bank nomination names spouse **Kavya Demo-Mehta**.
- **Why it is an approved rule instance:** the institution, asset type, and exact account reference match, while the named people differ. Per `backend/rules/RULES.md`, this warrants review but does not establish who owns or legally prevails.

No other conflict is intended: the life-policy and mutual-fund nomination names match their will clauses. `RECORD-SUPERSESSION-001` should not fire because each asset has only one nomination form and an explicit demo acknowledgement.

## Clean persona — Rohan Demo-Sen

| Document | Date | Expected assets/people |
|---|---:|---|
| `clean_persona/documents/01_will.pdf` | 2026-01-10 | SB-DEMO-8120 → Mira Demo-Sen; LIFE-DEMO-9912 → Mira Demo-Sen |
| `clean_persona/documents/02_bank_nomination.pdf` | 2025-09-20 | SB-DEMO-8120 → Mira Demo-Sen, spouse, 100%; recorded 2025-09-22 |
| `clean_persona/documents/03_insurance_nomination.pdf` | 2025-09-21 | LIFE-DEMO-9912 → Mira Demo-Sen, spouse, 100%; life policy; MWP false; no assignment; recorded 2025-09-23 |

### Intended Phase 4 outcome

No conflict. The will and registered-looking nomination form name Mira Demo-Sen for each exact asset reference. This is a synthetic control case, not proof that any real estate plan is legally complete.

## NPS validity persona — Priya Demo-Iyer

Added so the demo shows a `validity_warning`, which is a different kind of finding from a conflict: the problem is one document's own standing, not a disagreement between two.

**Persona context, stated not extracted:** `owner_has_family = true`, `marriage_date = 2024-03-01`. The engine may never infer a marriage from a document's silence, so these are confirmed facts on the persona record and the interface shows them as the second source, labelled "Confirmed synthetic persona context".

| Document | Date | Expected assets/people |
|---|---:|---|
| `nps_persona/documents/01_will.pdf` | 2026-01-15 | 1100-DEMO-3301 → Rohit Demo-Iyer, husband, bequest |
| `nps_persona/documents/02_nps_nomination.pdf` | 2022-05-01 | 1100-DEMO-3301 → Nikhil Demo-Sharma, brother, 100%; **no acknowledgement**, so registration is `unconfirmed` |

### Intended outcome

- **Rule:** `NPS-VALIDITY-001`, finding type `validity_warning`, severity high.
- **Why:** the nomination is dated 1 May 2022, before the confirmed marriage date of 1 March 2024, and no later confirmed nomination replaces it. Two independent branches of the rule are satisfied — the pre-marriage date, and a nominee whose relationship is explicitly outside the regulation's family definition — so the finding does not depend on a single extracted value.
- **`NPS-WILL-001` is deliberately suppressed** for this nomination group. When a document's own validity is in doubt, adding "it also disagrees with the will" is noise. This is the rule-ordering behaviour documented in `backend/rules/RULES.md` section 8, made visible in the demo.
- The form must stay unacknowledged. An acknowledgement dated after the marriage would prove a later valid nomination and correctly silence the rule.

## Joint holding persona — Meera Demo-Rao

Added so the demo shows a `scope_gap`: the engine declining to judge an asset its rules do not cover, rather than guessing.

| Document | Date | Expected assets/people |
|---|---:|---|
| `joint_persona/documents/01_will.pdf` | 2026-01-18 | SB-DEMO-6602 → Arjun Demo-Rao, son, bequest |
| `joint_persona/documents/02_bank_nomination.pdf` | 2023-09-12 | SB-DEMO-6602 → Latika Demo-Rao, sister, 100%; **joint holders**, either or survivor; recorded 2023-09-15 |

### Intended outcome

- **Marker:** `GAP-JOINT-HOLDING`, finding type `scope_gap`, severity low.
- **Why:** the nomination and the will name different people for the same account, which would normally be `BANK-WILL-001`. It is not, because the account is held jointly and that rule is scoped to individually held accounts. The engine reports *manual review required* instead.
- The mode-of-holding line is what makes this work. The extraction prompt keys on phrases such as "joint holders" and "either or survivor", never on the number of nominees, so the form states the holding pattern explicitly.
- Score consequence, recorded because it is counterintuitive: a gap deducts 3 where a conflict deducts 25, so this persona scores 97. Leaving rule scope raises the score. A gap never means the asset is fine.

## What the four personas demonstrate together

| Persona | Finding type | Rule or marker | Score |
|---|---|---|---:|
| Aarav Demo-Mehta | `review_conflict` | `BANK-WILL-001` | 75 |
| Rohan Demo-Sen | none | — | 100 |
| Priya Demo-Iyer | `validity_warning` | `NPS-VALIDITY-001` | 75 |
| Meera Demo-Rao | `scope_gap` | `GAP-JOINT-HOLDING` | 97 |

One of each outcome the engine can produce. Three of the seven approved rules remain undemonstrated by seed data and are covered only by unit tests: `LIFE-NOTICE-001`, `LIFE-WILL-001`, `MF-WILL-001`, and `NPS-WILL-001`.

## Regenerating the PDFs

`./seed_data/build.sh` renders every persona's HTML source to its PDF with headless Chrome. Pass persona directory names to render only those. After changing a document, re-seed in live mode and regenerate the fallback snapshot, so the pre-verified data still matches what the model actually extracts:

```bash
./seed_data/build.sh nps_persona
cd backend && .venv/bin/python scripts/seed_demo.py --yes --mode live
.venv/bin/python scripts/export_demo_fallback.py
```

## Safety and scope

- The names use `Demo-` and every identifier contains `DEMO`.
- Institution names are invented and no real logo or address is used.
- Signature areas are labeled synthetic placeholders.
- Every PDF visibly says synthetic/not valid/not legal advice.
- No Aadhaar, PAN, phone, email, physical address, real account number, or real policy/folio/PRAN is present.
- Phase 3 defines expected outcomes only. The deterministic engine does not exist until approved Phase 4.
