# JeevanSetu deterministic conflict rules

**Rules version:** `1.0.0-candidate`
**Jurisdiction snapshot:** India, sources checked 2026-09-29
**Status:** Phase 1 candidate; not approved for implementation until user review

> **Not legal advice.** This is a first-pass document consistency check based on a limited, India-scoped rule set. A licensed legal professional and the relevant institution should review the documents and current law.

## 1. Purpose and hard boundary

This file is the single source of truth for what JeevanSetu may call a conflict or validity warning. Phase 4 must implement these predicates directly in Python. Gemini may classify documents, extract source-backed fields, and turn an already-determined finding into plain language; Gemini must never decide whether a rule matched, set severity, choose a legal winner, or remove the disclaimer.

A finding means **the synthetic records need reconciliation or professional review**. It does not establish ownership, probate validity, heirship, entitlement, or which document prevails. The sources below address institutional payment/transmission and selected nomination effects; personal law, account ownership, policy assignment, trusts, court orders, and document validity can change an actual outcome.

All inputs, examples, seed records, and tests must be synthetic. The product must not request or accept real personal or financial documents for this hackathon build.

## 2. Source register

Source descriptions below are paraphrased. Links point to the primary publication used for the rule; no secondary article controls a rule.

### SRC-BANK-01 — Supreme Court of India: bank nominee and succession

[Ram Chander Talwar & Anr. v. Devender Kumar Talwar & Ors., Civil Appeal No. 1684 of 2004](https://api.sci.gov.in/jonew/judis/36985.pdf), applying section 45ZA(2) of the Banking Regulation Act, 1949.

**Reason used here:** the Court distinguished the nominee's right to receive money from the bank from ownership of that money, and stated that succession still governs the deceased depositor's estate. This supports flagging a nominee/will mismatch without declaring either person the winner.

### SRC-INS-01 — Insurance Act, 1938, current consolidated text

[Insurance Act, 1938, sections 38–39 (consolidated text hosted by IFSCA)](https://ifsca.gov.in/CommonDirect/PreviewPdf?fileName=Insurance_Act_1938_20260717_0231.pdf&id=29709e474fe6b066fc0cb19f7d6ac244), including amendments shown effective through 2026.

**Provisions used here:**

- Section 39(2) permits a life-policy nomination to be cancelled or changed by endorsement, further endorsement, or will, but protects an insurer's bona-fide payment to its registered nominee until written notice reaches the insurer.
- Section 39(3) provides for insurer acknowledgement of registration, cancellation, or change.
- Sections 39(6)–(7) address payment to surviving nominees and provide special beneficial treatment where the nominee is a parent, spouse, or child, subject to the statute's qualifications.
- Section 39(12) excludes policies governed by section 6 of the Married Women's Property Act, 1874, subject to its proviso.
- Section 38 means an assignment or transfer can change the analysis.

These distinctions are why this rule set does not apply one generic “a will overrides insurance” statement.

### SRC-MF-01 — SEBI mutual-fund nomination framework

[SEBI Circular SEBI/HO/OIAE/OIAE_IAD-3/P/ON/2025/0027, 28 February 2025](https://www.sebi.gov.in/sebi_data/attachdocs/feb-2025/1740743883077.pdf), amending and clarifying the 10 January 2025 nomination circular for demat accounts and mutual-fund folios.

**Provisions used here:** Annexure A's mutual-fund nomination form describes receipt by nominees as trustees on behalf of legal heirs, says a submitted nomination supersedes an earlier nomination, permits nomination changes, and describes transmission by the AMC after death documentation and nominee KYC. It also requires percentage shares when an investor elects to specify them and otherwise provides equal allocation.

[SEBI Investor topic: Nomination](https://investor.sebi.gov.in/market-nomination.html) separately explains that a mutual-fund nominee may claim redemption proceeds after the investor's death.

**Current-status caution:** SEBI published a March 2026 consultation paper proposing modified nomination norms. A consultation paper and its draft circular are not treated as operative law here. Phase 6 must re-check whether a final circular has superseded SRC-MF-01 before a public demo.

### SRC-NPS-01 — PFRDA NPS Exit Regulations

[PFRDA (Exits and Withdrawals under the NPS) Regulations, 2015, consolidated through 20 July 2026](https://pfrda.org.in/documents/33652/184762/PFRDA+Exits+and+Withdrawals+under+the+NPS+Regulations+2015+_Last+amended+on+20+July+2026_+(1).pdf), Chapter VII, “Nomination.”

**Provisions used here:** the regulations give a valid nominee the right to receive unpaid NPS money on death; allow distribution among nominees; invalidate a non-family nomination when the subscriber has a family; require a fresh nomination on marriage; invalidate a non-family nomination when the subscriber later acquires a family; and make a modification effective when received by the relevant NPS intermediary or nodal office.

**Unresolved point:** this source does not clearly settle every contest between a valid NPS nomination, a will, and all potentially applicable succession law. Therefore the NPS mismatch rule identifies a high-impact review conflict but never declares beneficial ownership.

## 3. Required structured inputs

Phase 2 must preserve every value's `source_text`, document ID, page/field locator where available, and extraction confidence. The engine may use only structured values with source references.

### Existing Phase 0 fields

- `document_id`
- `document_type`
- `asset_type`
- `institution_name`
- `asset_reference`
- `named_person`
- `relationship`
- `mechanism_type`: `nominee`, `bequest`, or `beneficiary_nominee`
- `document_date`
- `share_percent`
- `source_text`

### Fields Phase 2 must add or explicitly derive

- `registration_status`: `confirmed`, `unconfirmed`, `not_registered`, or `unknown`
- `registration_date`: date on an institution acknowledgement, not merely the form date
- `explicit_nomination_action`: `none`, `change`, or `cancel`
- `policy_kind`: at minimum `life` or `other`
- `mwpa_section_6_applies`: `true`, `false`, or `unknown`
- `assignment_status`: `active`, `none`, or `unknown`
- `owner_has_family`: `true`, `false`, or `unknown`, from explicit synthetic persona context only
- `marriage_date`: confirmed date or `null`, from explicit synthetic persona context only
- `document_group_id`: groups all nominees listed on one form
- `manually_confirmed_aliases`: synthetic persona-level pairs explicitly confirmed to be the same person

Unknown must remain unknown. Gemini must not fill missing legal status from implication or general knowledge.

## 4. Deterministic matching helpers

The helpers below are implementation requirements, not AI judgments.

```text
normalize_text(value):
    Unicode-normalize; trim; case-fold; collapse whitespace and punctuation

same_asset(a, b):
    return a.asset_type == b.asset_type
       and normalize_text(a.institution_name) == normalize_text(b.institution_name)
       and normalize_text(a.asset_reference) == normalize_text(b.asset_reference)

same_person(a, b, confirmed_aliases):
    return normalize_text(a.named_person) == normalize_text(b.named_person)
       or unordered_pair(a.named_person, b.named_person) in confirmed_aliases

persons_differ(a, b):
    return both names are present and not same_person(a, b)
```

Rules must not fuzzy-match assets or people. If an asset reference is missing, truncated differently, or only plausibly similar, the engine returns no conflict and records a separate extraction/manual-review gap for Phase 5. A mere spelling or initials difference can therefore be confirmed as an alias before re-running.

## 5. Finding contract

Every matched rule produces deterministic data before any Gemini call:

```text
Finding:
    rule_id
    rules_version
    finding_type              # review_conflict | validity_warning
    severity                  # high | medium | low
    asset_type
    asset_reference
    source_a: document_id, locator, source_text, structured values
    source_b: document_id/persona_context_id, locator, source_text, structured values
    deterministic_summary
    legal_scope_note
    suggested_actions[]
    disclaimer                # exact mandatory text below
```

**Mandatory exact disclaimer on every result:**

> Not legal advice. This is a first-pass document consistency check based on a limited, India-scoped rule set. A licensed legal professional and the relevant institution should review the documents and current law.

If Gemini explanation generation fails, the deterministic summary, scope note, suggested actions, sources, and disclaimer must still be returned. Gemini output must not add a claim that one person legally wins.

## 6. Severity definitions

- **High:** the documents point the institution and estate plan toward different people, or a primary source makes the nomination potentially invalid. Prompt professional and institutional review first.
- **Medium:** the records are internally inconsistent or registration/supersession is unproven, but the rule does not establish that the current institution record differs.
- **Low:** reserved for non-conflict hygiene findings in Phase 5. No Phase 1 conflict rule currently emits low severity.

Severity represents review priority, not probability of litigation or a legal conclusion.

## 7. Rules

## Rule BANK-WILL-001 — Bank deposit nominee differs from will recipient

**Finding type:** `review_conflict`
**Default severity:** `high`
**Source:** SRC-BANK-01

**Scope:** individually held Indian bank deposit accounts. Joint-account survivorship clauses, lockers, safe custody, trusts, and court orders are excluded.

**Predicate:**

```text
for nomination in fields where asset_type == bank_account
                         and mechanism_type == nominee:
    for bequest in fields where mechanism_type == bequest:
        if same_asset(nomination, bequest)
           and persons_differ(nomination, bequest):
            emit BANK-WILL-001, high
```

**Deterministic summary:** `The bank nomination and will name different people for the same deposit account.`

**Scope note:** the cited judgment distinguishes the bank's payment recipient from succession/ownership. The result must not say the nominee or will recipient automatically owns the money.

**Suggested actions:** confirm the nomination currently registered with the bank; ask a licensed advisor to review the will and succession position; after advice, align the bank record or estate document and keep acknowledgement.

**Positive synthetic example:** Bank form for account `BANK-SYN-4821` names Meera Sen; will clause for the same account names Arjun Sen.

**Negative synthetic example:** both sources name Meera Sen, or the two records identify different accounts.

## Rule LIFE-NOTICE-001 — Will explicitly changes a life-policy nomination but insurer notice is unconfirmed

**Finding type:** `review_conflict`
**Default severity:** `high`
**Source:** SRC-INS-01, sections 39(2)–(3)

**Scope:** a life policy where the will expressly changes or cancels the nomination for that identified policy. A generic bequest is not enough. Policies known to be under Married Women's Property Act section 6 or subject to an active assignment are excluded.

**Predicate:**

```text
for will_action in fields where mechanism_type == bequest
                            and explicit_nomination_action in {change, cancel}:
    nomination = registered-or-present life-policy nomination for same_asset
    if nomination exists
       and mwpa_section_6_applies == false
       and assignment_status == none
       and no insurer acknowledgement proves notice after will_action.document_date:
        emit LIFE-NOTICE-001, high
```

If `mwpa_section_6_applies` or `assignment_status` is unknown, emit no rule finding; record an unsupported-scope gap instead.

**Deterministic summary:** `The will expressly changes this life-policy nomination, but the documents do not show that the insurer registered or received the change.`

**Scope note:** section 39 allows change by will but also protects certain bona-fide insurer payments until written notice is delivered. This is an operational/legal review issue, not a declaration that the change failed.

**Suggested actions:** request the insurer's current nomination record; obtain acknowledgement of any intended change; have an advisor review section 39, assignments, and policy-specific terms.

**Positive synthetic example:** a dated will says “I change the nominee for policy LIFE-SYN-77 to Kavya Rao,” while the policy record still names Dev Rao and no later insurer acknowledgement exists.

**Negative synthetic example:** the insurer acknowledgement post-dates the will and confirms Kavya Rao, or the will merely bequeaths a general residuary estate.

## Rule LIFE-WILL-001 — Life-policy nominee differs from will recipient

**Finding type:** `review_conflict`
**Severity:** `high` for a parent/spouse/child nominee; otherwise `medium`
**Source:** SRC-INS-01, sections 39(6)–(7)

**Scope:** life insurance only, where a will bequest for the identified policy differs from its nominee and LIFE-NOTICE-001 does not apply. Known MWP Act section 6 policies and active assignments are excluded.

**Predicate:**

```text
for nomination in life-policy beneficiary_nominee fields:
    for bequest in will bequest fields:
        if same_asset(nomination, bequest)
           and persons_differ(nomination, bequest)
           and LIFE-NOTICE-001 did not match
           and mwpa_section_6_applies == false
           and assignment_status == none:
            severity = high if relationship in {parent, spouse, child}
                       else medium
            emit LIFE-WILL-001, severity
```

Unknown relationship uses medium. Unknown MWP/assignment status produces an unsupported-scope gap, not this finding.

**Deterministic summary:** `The life-policy nomination and will name different people for the same policy.`

**Scope note:** section 39 gives special statutory treatment to certain close-family nominees. The engine cannot decide the ultimate effect of the will, policy ownership, personal law, creditor rights, or other exceptions.

**Suggested actions:** confirm the insurer's registered nominee and policy ownership; ask a licensed advisor to review section 39 and the will; align documents only after that review.

**Positive synthetic example:** a standard synthetic life policy names the policyholder's spouse, Nila Bose, while a will assigns policy `LIFE-SYN-88` to Tara Bose.

**Negative synthetic example:** both name Nila Bose, the asset references differ, or an active assignment is recorded.

## Rule MF-WILL-001 — Mutual-fund nominee differs from will recipient

**Finding type:** `review_conflict`
**Default severity:** `high`
**Source:** SRC-MF-01

**Scope:** sole-holder Indian mutual-fund folios. Joint holdings and demat-only securities are excluded from this hackathon rule.

**Predicate:**

```text
for nomination in fields where asset_type == mutual_fund_folio
                         and mechanism_type == nominee:
    for bequest in fields where mechanism_type == bequest:
        if same_asset(nomination, bequest)
           and persons_differ(nomination, bequest):
            emit MF-WILL-001, high
```

**Deterministic summary:** `The mutual-fund nomination and will name different people for the same folio.`

**Scope note:** SEBI's form frames the nominee as receiving as trustee/on behalf of legal heirs and its process can transmit the folio to the nominee. The rule flags procedural and succession-plan friction; it does not determine the legal heir, validate the will, or award the units.

**Suggested actions:** obtain the AMC/RTA's current nomination acknowledgement; have an advisor review the succession plan; align the registered nomination and estate documents if advised.

**Positive synthetic example:** folio `MF-SYN-2040` names Rohit Das as nominee, while the will names Leela Das for that folio.

**Negative synthetic example:** both name Rohit Das or one record refers to another AMC/folio.

## Rule NPS-WILL-001 — Valid-looking NPS nominee differs from will recipient

**Finding type:** `review_conflict`
**Default severity:** `high`
**Source:** SRC-NPS-01

**Scope:** NPS balances identified by the same synthetic PRAN/tier where the available fields do not trigger NPS-VALIDITY-001.

**Predicate:**

```text
for nomination in fields where asset_type == nps_account
                         and mechanism_type == nominee:
    for bequest in fields where mechanism_type == bequest:
        if same_asset(nomination, bequest)
           and persons_differ(nomination, bequest)
           and NPS-VALIDITY-001 did not match:
            emit NPS-WILL-001, high
```

**Deterministic summary:** `The NPS nomination and will name different people for the same NPS account.`

**Scope note:** current PFRDA regulations govern who can receive unpaid NPS money under a valid nomination. The cited regulation does not safely resolve every nominee-versus-will succession dispute, so the engine must not declare ownership or precedence.

**Suggested actions:** confirm the nomination received by the CRA/intermediary or nodal office; ask an NPS specialist or licensed advisor to review the will and current regulations; update records only after review.

**Positive synthetic example:** NPS record `PRAN-SYN-9001/Tier-I` names Isha Nair; the will names Kiran Nair for the same account.

**Negative synthetic example:** both name Isha Nair or the will does not identify the NPS account.

## Rule NPS-VALIDITY-001 — NPS nomination appears invalid after marriage or against confirmed family status

**Finding type:** `validity_warning`
**Default severity:** `high`
**Source:** SRC-NPS-01, Chapter VII nomination provisos (iv)–(vi)

**Scope:** only when synthetic persona context explicitly confirms the relevant family event/status. Never infer marriage or family status from a surname, honorific, address, or model guess.

**Predicate:**

```text
for nomination in NPS nomination document groups:
    marriage_branch = marriage_date is known
                      and nomination.document_date < marriage_date
                      and no later nomination with registration_status == confirmed

    outside_family_branch = owner_has_family == true
                            and every nominee relationship is explicitly one of
                                {friend, sibling, charity, unrelated, other_non_family}

    if marriage_branch or outside_family_branch:
        emit NPS-VALIDITY-001, high
```

Do not classify `parent_in_law`, guardianship, adoption, separation, or any ambiguous relationship through this rule; send it to manual review because the regulation's family definition and personal-law qualifications require more context.

**Source B:** the confirmed synthetic persona event/status record, including its provenance—not an inference.

**Deterministic summary:** `The NPS nomination may be invalid under the current family or post-marriage nomination conditions.`

**Scope note:** this warning applies the express PFRDA validity conditions only. It does not identify the proper replacement nominee or legal heir.

**Suggested actions:** ask the NPS intermediary/nodal office which nomination is currently valid; submit a fresh nomination if advised; retain receipt/acknowledgement; obtain professional review for ambiguous family status.

**Positive synthetic example:** a nomination dated 2022 names a friend, a synthetic persona record confirms marriage in 2024, and no later acknowledged nomination exists.

**Negative synthetic example:** a confirmed nomination post-dates the marriage, or family/marriage status is unknown.

## Rule RECORD-SUPERSESSION-001 — Conflicting nomination records have no proven supersession chain

**Finding type:** `review_conflict`
**Default severity:** `medium`
**Sources:** SRC-BANK-01, SRC-INS-01 section 39(2)–(3), SRC-MF-01, SRC-NPS-01 proviso (ix)

**Scope:** two or more nomination document groups for the exact same supported asset and mechanism. Compare groups, not individual co-nominee rows within one form.

**Predicate:**

```text
for each asset + mechanism with two or more nomination document groups:
    if nominee person/share sets differ:
        if exactly one later group has registration_status == confirmed
           and its acknowledgement proves it superseded the earlier group:
            no finding
        else:
            emit one RECORD-SUPERSESSION-001 per conflicting group pair, medium
```

A later document date alone does not prove the institution received or registered it.

**Deterministic summary:** `Two nomination records for the same asset disagree, and the documents do not prove which one the institution currently recognizes.`

**Scope note:** each framework has a registration, receipt, variation, or supersession concept. This rule deliberately refuses to treat “newest file wins” as a legal or operational rule without acknowledgement.

**Suggested actions:** obtain the institution's current registered nomination; retain acknowledgement; mark historical forms as superseded in the synthetic vault only after confirmation.

**Positive synthetic example:** two forms for `MF-SYN-2040` name different nominees and neither has an AMC acknowledgement.

**Negative synthetic example:** the AMC acknowledgement confirms the later form and the form expressly supersedes the earlier nomination.

## 8. Rule ordering and duplicate handling

Run rules in this order:

1. `NPS-VALIDITY-001`
2. `LIFE-NOTICE-001`
3. `RECORD-SUPERSESSION-001`
4. Asset-specific will mismatch rules

Suppression rules:

- Suppress `NPS-WILL-001` for a nomination group that triggered `NPS-VALIDITY-001`; show the validity warning first.
- Suppress `LIFE-WILL-001` for the same source pair when `LIFE-NOTICE-001` matched.
- `RECORD-SUPERSESSION-001` may coexist with a will mismatch because it reports a separate uncertainty about the institution's current record.
- Deduplicate by `(rule_id, asset_reference, unordered source IDs)`.

## 9. Explicit non-rules and unsupported cases

The engine must not infer or claim any of the following:

- “The newest dated document automatically wins.”
- “A nominee always owns the asset.”
- “A will always overrides a nominee,” or the reverse.
- Who is a legal heir or whether a will, signature, witness, probate, marriage, adoption, divorce, or family relationship is valid.
- That possession of a nomination form proves registration.
- That missing nomination is a conflict. It is a Phase 5 completeness gap, not a Phase 4 conflict.
- That a name variation alone proves two different people. Confirmed aliases can resolve it.
- Rules for joint bank accounts, survivorship mandates, lockers, safe custody, general insurance, MWP Act policies, active policy assignments, demat shares, trusts, NPS annuity choices, tax, creditor claims, foreign assets, or non-India jurisdictions.
- Any rule sourced only from the March 2026 SEBI consultation draft.

Unsupported cases must be labeled `manual review required` and must not be silently forced through the nearest rule.

## 10. Phase 4 implementation acceptance map

Each of the seven rules requires at least one positive and one negative unit test. Tests must assert rule ID, severity, both sources, deterministic summary, scope note, suggested actions, and the exact disclaimer. Tests must run with a stub/disabled Gemini client to prove conflict decisions do not call AI.

| Rule | Positive fixture | Minimum negative fixture |
|---|---|---|
| BANK-WILL-001 | Same bank account, different people | Same person or different account |
| LIFE-NOTICE-001 | Explicit will change, no later insurer acknowledgement | Later acknowledgement or generic bequest |
| LIFE-WILL-001 | Same life policy, different people | Same person, MWP, or active assignment |
| MF-WILL-001 | Same folio, different people | Same person or different folio |
| NPS-WILL-001 | Same PRAN/tier, different people | Same person or invalidity rule takes priority |
| NPS-VALIDITY-001 | Pre-marriage nomination, no confirmed replacement | Post-marriage confirmed nomination or unknown status |
| RECORD-SUPERSESSION-001 | Different groups, no acknowledgement | Proven later registered supersession |

## 11. Review cadence

- Re-check every source before Phase 4 implementation and again before the Phase 6 demo freeze.
- If a source has been superseded, increment `rules_version`, document the change in `DECISIONS.md`, and update tests before using the new rule.
- If a proposition cannot be supported by a current primary source, remove or disable the rule; do not fill the gap with model output or an unsupported assumption.

## 12. Engine gap markers (not rules)

The seven rules above are the only approved conflict rules. When the engine meets a case the rules deliberately exclude, it must emit a labeled gap instead of forcing the case through the nearest rule. Gap markers use a `GAP-` prefix so they can never be mistaken for an approved rule ID, always use severity `low`, and always use finding type `scope_gap`.

| Marker | Emitted when |
|---|---|
| `GAP-LIFE-SCOPE` | An insurance nomination matching a will bequest is not a life policy, or its MWP Act section 6 or assignment status is not confirmed as out of scope. |
| `GAP-NPS-RELATIONSHIP` | The owner is confirmed to have a family but a listed NPS nominee relationship is neither clearly inside nor clearly outside the regulation's family definition. |
| `GAP-ASSET-REFERENCE` | An extracted record has no asset reference at all, so deterministic matching is impossible. |
| `GAP-ASSET-NEAR-MATCH` | A nomination and a will clause differ only by a truncated reference or an institution-name variant, so they must not be treated as either the same asset or a clean result. |
| `GAP-UNSUPPORTED-SUPERSESSION` | Two nomination records disagree on an asset type the rules exclude, on a jointly held asset, or on a policy under the MWP Act or an active assignment. |
| `GAP-JOINT-HOLDING` | A nomination record for an asset the rules cover is extracted as a jointly held asset, so the single-holder scope of `BANK-WILL-001`, `MF-WILL-001` and `RECORD-SUPERSESSION-001` does not apply. |
| `GAP-MISSING-NOMINATION` | A will assigns an asset for which no nomination record was uploaded at all, so there is nothing to compare. This is a completeness gap, not a conflict. |

A gap means *manual review required*. It is never a conflict, never carries a severity above `low`, and never implies a legal position. Gaps still carry the mandatory disclaimer.

## 13. Documented deterministic normalization

`relationship` is free text, so the engine maps it before applying the two rules that depend on it. These tables are part of the implementation contract:

- Close family for `LIFE-WILL-001` severity: `spouse`, `husband`, and `wife` map to spouse; `child`, `son`, and `daughter` map to child; `parent`, `mother`, and `father` map to parent.
- Explicitly outside the NPS family definition for `NPS-VALIDITY-001`: `friend`, `sibling`, `brother`, `sister`, `charity`, `unrelated`, and `other_non_family`.
- Anything else is `ambiguous`. Ambiguous relationships use medium severity for `LIFE-WILL-001` and produce `GAP-NPS-RELATIONSHIP` instead of a validity warning.

## 14. Holding pattern and the single-holder scope

`BANK-WILL-001` is scoped to individually held accounts, `MF-WILL-001` to sole-holder folios, and `RECORD-SUPERSESSION-001` to the assets those rules cover. The extraction schema carries a `holding_pattern` field with exactly three values, and the engine reads it from the nomination record, not the will clause, because the nomination form is what states how the asset is held.

| `holding_pattern` | Engine behaviour |
|---|---|
| `single` | In scope. The rule is applied normally. |
| `joint` | Out of scope. No conflict is raised; `GAP-JOINT-HOLDING` is emitted instead. |
| `unknown` | Treated as in scope. |

`unknown` is deliberately in scope. A document that does not state its holding pattern is the common case, and excluding it would silently skip most records and report a clean result where none was checked. The consequence is recorded honestly: if a jointly held asset is extracted as `unknown`, the engine may still report a conflict for it, and that conflict is a prompt to review the documents rather than a statement about who is entitled to the asset. Nothing in this section decides survivorship, which stays outside the rule set under section 9.

Two further consequences, recorded because they are not obvious:

- **The gap is raised whether or not the named people agree.** The rules do not cover a joint holding at all, so the engine has no basis for calling it clean either. A joint nomination and a will naming the same person still reports manual review required. The gap is restricted to the `nominee` mechanism, the one the two gated rules match, so it is the complement of the skipped rule and not a wider net.
- **Leaving rule scope raises the score.** The score charges 25 for a high conflict and 3 for a low gap, so the same joint account that would have scored 75 as a conflict scores 97 as a gap. This is true of every `GAP-` marker, not only this one: a finding the rules cannot judge costs less than one they can. The score is labelled as review priority for synthetic documents and not legal readiness, and a gap is never a statement that the asset is fine.

Demat-only holdings remain outside every rule regardless of holding pattern, per section 9.
