"""Deterministic conflict detection for the approved rule set.

This module is the only place where a JeevanSetu conflict is decided. It never
calls an AI model. Every predicate, severity, summary, scope note, and suggested
action here mirrors ``backend/rules/RULES.md``.
"""

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date

RULES_VERSION = "1.0.0-candidate"

DISCLAIMER = (
    "Not legal advice. This is a first-pass document consistency check based on a "
    "limited, India-scoped rule set. A licensed legal professional and the relevant "
    "institution should review the documents and current law."
)

CLOSE_FAMILY_RELATIONSHIPS = {
    "spouse": "spouse",
    "husband": "spouse",
    "wife": "spouse",
    "child": "child",
    "son": "child",
    "daughter": "child",
    "parent": "parent",
    "mother": "parent",
    "father": "parent",
}

EXPLICIT_NON_FAMILY_RELATIONSHIPS = {
    "friend",
    "sibling",
    "brother",
    "sister",
    "charity",
    "unrelated",
    "other_non_family",
}

REVIEW_CONFLICT = "review_conflict"
VALIDITY_WARNING = "validity_warning"
SCOPE_GAP = "scope_gap"


@dataclass(frozen=True)
class FieldRecord:
    """One extracted asset/person row with its provenance."""

    field_id: int
    document_id: int
    document_type: str
    document_date: date | None
    document_group_id: str
    asset_type: str
    institution_name: str
    asset_reference: str
    named_person: str
    relationship: str
    mechanism_type: str
    share_percent: float | None
    source_text: str
    source_locator: str
    registration_status: str
    registration_date: date | None
    explicit_nomination_action: str
    policy_kind: str
    mwpa_section_6_applies: str
    assignment_status: str
    holding_pattern: str = "unknown"

    @property
    def group_key(self) -> tuple[int, str]:
        return (self.document_id, self.document_group_id)


@dataclass(frozen=True)
class PersonaContext:
    """Explicitly confirmed synthetic persona context. Never inferred."""

    owner_has_family: str = "unknown"
    marriage_date: date | None = None
    family_context_source_text: str | None = None
    confirmed_aliases: frozenset[frozenset[str]] = frozenset()


@dataclass(frozen=True)
class FindingSource:
    label: str
    locator: str
    text: str
    field_id: int | None = None


@dataclass(frozen=True)
class Finding:
    rule_id: str
    finding_type: str
    severity: str
    asset_type: str
    asset_reference: str
    summary: str
    legal_scope_note: str
    suggested_actions: tuple[str, ...]
    source_a: FindingSource
    source_b: FindingSource | None = None
    rules_version: str = RULES_VERSION
    disclaimer: str = DISCLAIMER


@dataclass
class DetectionResult:
    findings: list[Finding] = field(default_factory=list)

    @property
    def conflicts(self) -> list[Finding]:
        return [f for f in self.findings if f.finding_type != SCOPE_GAP]

    @property
    def scope_gaps(self) -> list[Finding]:
        return [f for f in self.findings if f.finding_type == SCOPE_GAP]


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    decomposed = unicodedata.normalize("NFKD", value)
    without_punctuation = re.sub(r"[^\w\s]", " ", decomposed)
    return re.sub(r"\s+", " ", without_punctuation).strip().casefold()


def asset_key(record: FieldRecord) -> tuple[str, str, str]:
    return (
        record.asset_type,
        normalize_text(record.institution_name),
        normalize_text(record.asset_reference),
    )


def same_asset(left: FieldRecord, right: FieldRecord) -> bool:
    if not normalize_text(left.asset_reference) or not normalize_text(right.asset_reference):
        return False
    return asset_key(left) == asset_key(right)


def same_person(
    left: FieldRecord,
    right: FieldRecord,
    confirmed_aliases: frozenset[frozenset[str]],
) -> bool:
    left_name = normalize_text(left.named_person)
    right_name = normalize_text(right.named_person)
    if left_name and left_name == right_name:
        return True
    return frozenset({left_name, right_name}) in confirmed_aliases


def persons_differ(
    left: FieldRecord,
    right: FieldRecord,
    confirmed_aliases: frozenset[frozenset[str]],
) -> bool:
    if not normalize_text(left.named_person) or not normalize_text(right.named_person):
        return False
    return not same_person(left, right, confirmed_aliases)


def relationship_category(relationship: str) -> str:
    normalized = normalize_text(relationship).replace(" ", "_")
    if normalized in CLOSE_FAMILY_RELATIONSHIPS:
        return CLOSE_FAMILY_RELATIONSHIPS[normalized]
    if normalized in EXPLICIT_NON_FAMILY_RELATIONSHIPS:
        return "non_family"
    return "ambiguous"


def _source(record: FieldRecord, label: str) -> FindingSource:
    return FindingSource(
        label=label,
        locator=record.source_locator,
        text=record.source_text,
        field_id=record.field_id,
    )


def _nominations(records: list[FieldRecord], asset_type: str, mechanism: str) -> list[FieldRecord]:
    return [
        record
        for record in records
        if record.asset_type == asset_type and record.mechanism_type == mechanism
    ]


def _bequests(records: list[FieldRecord]) -> list[FieldRecord]:
    return [record for record in records if record.mechanism_type == "bequest"]


def _dedupe_key(finding: Finding) -> tuple:
    source_ids = frozenset(
        source.field_id
        for source in (finding.source_a, finding.source_b)
        if source is not None and source.field_id is not None
    )
    return (
        finding.rule_id,
        normalize_text(finding.asset_reference),
        source_ids,
        finding.source_b.label if finding.source_b else "",
    )


def _asset_mismatch_finding(
    rule_id: str,
    nomination: FieldRecord,
    bequest: FieldRecord,
    severity: str,
    summary: str,
    scope_note: str,
    actions: tuple[str, ...],
    nomination_label: str,
) -> Finding:
    return Finding(
        rule_id=rule_id,
        finding_type=REVIEW_CONFLICT,
        severity=severity,
        asset_type=nomination.asset_type,
        asset_reference=nomination.asset_reference,
        summary=summary,
        legal_scope_note=scope_note,
        suggested_actions=actions,
        source_a=_source(nomination, nomination_label),
        source_b=_source(bequest, "Will bequest"),
    )


# --- Holding-pattern scope gate -------------------------------------------

JOINT_HOLDING_SUMMARY = (
    "Manual review required: this asset is held jointly, which the approved rules exclude."
)
JOINT_HOLDING_NOTE = (
    "The bank and mutual-fund rules are scoped to individually held accounts and "
    "sole-holder folios. Joint holdings and survivorship mandates are excluded, so no "
    "conflict conclusion is drawn for this asset."
)
JOINT_HOLDING_ACTIONS = (
    "Ask the institution how the joint holding and any survivorship mandate apply.",
    "Ask a licensed advisor to review this asset directly.",
)
HOLDING_SCOPED_ASSETS = {"bank_account", "mutual_fund_folio"}


def _holding_in_scope(nomination: FieldRecord) -> bool:
    """Joint holdings are excluded. Unknown is treated as not excluded, by design."""
    if nomination.asset_type not in HOLDING_SCOPED_ASSETS:
        return True
    return nomination.holding_pattern != "joint"


def _joint_holding_gaps(records: list[FieldRecord]) -> list[Finding]:
    """Report the assets the holding-pattern gate removed from rule scope.

    Restricted to `nominee`, the one mechanism the two gated rules match, so the gap is
    exactly the complement of the skipped rule rather than a wider net. The gap is raised
    whether or not the names agree: the rules do not cover a joint holding at all, so the
    engine has no basis for calling it clean either.
    """
    findings: list[Finding] = []
    for nomination in records:
        if nomination.mechanism_type != "nominee":
            continue
        if nomination.asset_type not in HOLDING_SCOPED_ASSETS:
            continue
        if nomination.holding_pattern != "joint":
            continue
        for bequest_record in _bequests(records):
            if same_asset(nomination, bequest_record):
                findings.append(
                    Finding(
                        rule_id="GAP-JOINT-HOLDING",
                        finding_type=SCOPE_GAP,
                        severity="low",
                        asset_type=nomination.asset_type,
                        asset_reference=nomination.asset_reference,
                        summary=JOINT_HOLDING_SUMMARY,
                        legal_scope_note=JOINT_HOLDING_NOTE,
                        suggested_actions=JOINT_HOLDING_ACTIONS,
                        source_a=_source(nomination, "Nomination record"),
                        source_b=_source(bequest_record, "Will bequest"),
                    )
                )
                break
    return findings


# --- Rule BANK-WILL-001 ---------------------------------------------------

BANK_WILL_SUMMARY = (
    "The bank nomination and will name different people for the same deposit account."
)
BANK_WILL_SCOPE = (
    "The cited Supreme Court judgment distinguishes who the bank may pay from who "
    "inherits under succession law. This result does not decide who owns the money."
)
BANK_WILL_ACTIONS = (
    "Confirm the nomination currently registered with the bank.",
    "Ask a licensed advisor to review the will and the succession position.",
    "After advice, align the bank record or the estate document and keep the acknowledgement.",
)


def rule_bank_will(records: list[FieldRecord], context: PersonaContext) -> list[Finding]:
    findings: list[Finding] = []
    for nomination in _nominations(records, "bank_account", "nominee"):
        if not _holding_in_scope(nomination):
            continue
        for bequest in _bequests(records):
            if same_asset(nomination, bequest) and persons_differ(
                nomination, bequest, context.confirmed_aliases
            ):
                findings.append(
                    _asset_mismatch_finding(
                        "BANK-WILL-001",
                        nomination,
                        bequest,
                        "high",
                        BANK_WILL_SUMMARY,
                        BANK_WILL_SCOPE,
                        BANK_WILL_ACTIONS,
                        "Bank nomination",
                    )
                )
    return findings


# --- Life-insurance scope gate --------------------------------------------

LIFE_SCOPE_GAP_SUMMARY = (
    "Manual review required: this insurance record is outside the supported "
    "life-insurance rule scope."
)
LIFE_SCOPE_GAP_NOTE = (
    "The approved rules exclude general insurance, policies under Married Women's "
    "Property Act section 6, and policies with an active or unknown assignment."
)
LIFE_SCOPE_GAP_ACTIONS = (
    "Confirm the policy type, MWP Act applicability, and assignment status with the insurer.",
    "Ask a licensed advisor to review this policy directly.",
)


def _life_scope_supported(nomination: FieldRecord) -> bool:
    return (
        nomination.policy_kind == "life"
        and nomination.mwpa_section_6_applies == "false"
        and nomination.assignment_status == "none"
    )


def _life_scope_gaps(records: list[FieldRecord], context: PersonaContext) -> list[Finding]:
    findings: list[Finding] = []
    for nomination in _nominations(records, "insurance_policy", "beneficiary_nominee"):
        if _life_scope_supported(nomination):
            continue
        for bequest in _bequests(records):
            if same_asset(nomination, bequest):
                findings.append(
                    Finding(
                        rule_id="GAP-LIFE-SCOPE",
                        finding_type=SCOPE_GAP,
                        severity="low",
                        asset_type=nomination.asset_type,
                        asset_reference=nomination.asset_reference,
                        summary=LIFE_SCOPE_GAP_SUMMARY,
                        legal_scope_note=LIFE_SCOPE_GAP_NOTE,
                        suggested_actions=LIFE_SCOPE_GAP_ACTIONS,
                        source_a=_source(nomination, "Insurance nomination"),
                        source_b=_source(bequest, "Will bequest"),
                    )
                )
                break
    return findings


# --- Rule LIFE-NOTICE-001 -------------------------------------------------

LIFE_NOTICE_SUMMARY = (
    "The will expressly changes this life-policy nomination, but the documents do not "
    "show that the insurer registered or received the change."
)
LIFE_NOTICE_SCOPE = (
    "Section 39 allows a nomination to be changed by will, yet it also protects certain "
    "bona-fide insurer payments until written notice reaches the insurer. This is an "
    "operational and legal review point, not a finding that the change failed."
)
LIFE_NOTICE_ACTIONS = (
    "Request the insurer's current registered nomination record.",
    "Obtain written acknowledgement of any intended change.",
    "Ask an advisor to review section 39, assignments, and the policy terms.",
)


def rule_life_notice(
    records: list[FieldRecord],
    context: PersonaContext,
) -> tuple[list[Finding], set[tuple[int, int]]]:
    findings: list[Finding] = []
    matched_pairs: set[tuple[int, int]] = set()
    for will_action in _bequests(records):
        if will_action.explicit_nomination_action not in {"change", "cancel"}:
            continue
        for nomination in _nominations(records, "insurance_policy", "beneficiary_nominee"):
            if not same_asset(nomination, will_action):
                continue
            if not _life_scope_supported(nomination):
                continue
            # An acknowledgement only proves the change reached the insurer when the
            # registered nominee is the person the will names. A later acknowledgement
            # that still records the previous nominee proves the opposite.
            change_registered = (
                nomination.registration_status == "confirmed"
                and nomination.registration_date is not None
                and will_action.document_date is not None
                and nomination.registration_date > will_action.document_date
                and same_person(nomination, will_action, context.confirmed_aliases)
            )
            if change_registered:
                continue
            matched_pairs.add((nomination.field_id, will_action.field_id))
            findings.append(
                Finding(
                    rule_id="LIFE-NOTICE-001",
                    finding_type=REVIEW_CONFLICT,
                    severity="high",
                    asset_type=nomination.asset_type,
                    asset_reference=nomination.asset_reference,
                    summary=LIFE_NOTICE_SUMMARY,
                    legal_scope_note=LIFE_NOTICE_SCOPE,
                    suggested_actions=LIFE_NOTICE_ACTIONS,
                    source_a=_source(nomination, "Insurance nomination"),
                    source_b=_source(will_action, "Will clause changing the nomination"),
                )
            )
    return findings, matched_pairs


# --- Rule LIFE-WILL-001 ---------------------------------------------------

LIFE_WILL_SUMMARY = (
    "The life-policy nomination and will name different people for the same policy."
)
LIFE_WILL_SCOPE = (
    "Section 39 gives certain close-family nominees special statutory treatment. This "
    "result cannot decide the ultimate effect of the will, policy ownership, personal "
    "law, creditor rights, or other statutory exceptions."
)
LIFE_WILL_ACTIONS = (
    "Confirm the insurer's registered nominee and the policy ownership.",
    "Ask a licensed advisor to review section 39 alongside the will.",
    "Align the documents only after that review.",
)


def rule_life_will(
    records: list[FieldRecord],
    context: PersonaContext,
    suppressed_pairs: set[tuple[int, int]],
) -> list[Finding]:
    findings: list[Finding] = []
    for nomination in _nominations(records, "insurance_policy", "beneficiary_nominee"):
        if not _life_scope_supported(nomination):
            continue
        for bequest in _bequests(records):
            if not same_asset(nomination, bequest):
                continue
            if (nomination.field_id, bequest.field_id) in suppressed_pairs:
                continue
            if not persons_differ(nomination, bequest, context.confirmed_aliases):
                continue
            severity = (
                "high"
                if relationship_category(nomination.relationship)
                in {"parent", "spouse", "child"}
                else "medium"
            )
            findings.append(
                _asset_mismatch_finding(
                    "LIFE-WILL-001",
                    nomination,
                    bequest,
                    severity,
                    LIFE_WILL_SUMMARY,
                    LIFE_WILL_SCOPE,
                    LIFE_WILL_ACTIONS,
                    "Insurance nomination",
                )
            )
    return findings


# --- Rule MF-WILL-001 -----------------------------------------------------

MF_WILL_SUMMARY = (
    "The mutual-fund nomination and will name different people for the same folio."
)
MF_WILL_SCOPE = (
    "SEBI's nomination form frames the nominee as receiving on behalf of legal heirs, "
    "and its process can transmit the folio to that nominee. This result does not "
    "identify the legal heir, validate the will, or award the units."
)
MF_WILL_ACTIONS = (
    "Obtain the AMC or RTA acknowledgement of the current nomination.",
    "Ask a licensed advisor to review the succession plan.",
    "Align the registered nomination and estate documents if advised.",
)


def rule_mf_will(records: list[FieldRecord], context: PersonaContext) -> list[Finding]:
    findings: list[Finding] = []
    for nomination in _nominations(records, "mutual_fund_folio", "nominee"):
        if not _holding_in_scope(nomination):
            continue
        for bequest in _bequests(records):
            if same_asset(nomination, bequest) and persons_differ(
                nomination, bequest, context.confirmed_aliases
            ):
                findings.append(
                    _asset_mismatch_finding(
                        "MF-WILL-001",
                        nomination,
                        bequest,
                        "high",
                        MF_WILL_SUMMARY,
                        MF_WILL_SCOPE,
                        MF_WILL_ACTIONS,
                        "Mutual-fund nomination",
                    )
                )
    return findings


# --- Rule NPS-VALIDITY-001 ------------------------------------------------

NPS_VALIDITY_SUMMARY = (
    "The NPS nomination may be invalid under the current family or post-marriage "
    "nomination conditions."
)
NPS_VALIDITY_SCOPE = (
    "This warning applies only the express PFRDA validity conditions. It does not "
    "identify the correct replacement nominee or the legal heir."
)
NPS_VALIDITY_ACTIONS = (
    "Ask the NPS intermediary or nodal office which nomination is currently valid.",
    "Submit a fresh nomination if advised, and retain the acknowledgement.",
    "Obtain professional review for any ambiguous family status.",
)
NPS_AMBIGUOUS_SUMMARY = (
    "Manual review required: an NPS nominee relationship is not clearly inside or "
    "outside the regulation's family definition."
)
NPS_AMBIGUOUS_SCOPE = (
    "The PFRDA family definition and personal-law qualifications need more context than "
    "these documents provide, so no validity conclusion is drawn."
)
NPS_AMBIGUOUS_ACTIONS = (
    "Confirm the exact relationship and family status with the NPS intermediary.",
    "Ask a licensed advisor to review the nomination's validity.",
)


def rule_nps_validity(
    records: list[FieldRecord],
    context: PersonaContext,
) -> tuple[list[Finding], set[tuple[int, str]]]:
    findings: list[Finding] = []
    flagged_groups: set[tuple[int, str]] = set()
    nominations = _nominations(records, "nps_account", "nominee")
    groups: dict[tuple[int, str], list[FieldRecord]] = {}
    for record in nominations:
        groups.setdefault(record.group_key, []).append(record)

    for group_key, group in groups.items():
        representative = min(group, key=lambda record: record.field_id)
        categories = {relationship_category(record.relationship) for record in group}

        # Only a later confirmed nomination for the same NPS account can replace this one.
        later_confirmed_exists = any(
            other.registration_status == "confirmed"
            and other.registration_date is not None
            and context.marriage_date is not None
            and other.registration_date > context.marriage_date
            and asset_key(other) == asset_key(representative)
            for other in nominations
        )
        marriage_branch = (
            context.marriage_date is not None
            and representative.document_date is not None
            and representative.document_date < context.marriage_date
            and not later_confirmed_exists
        )
        outside_family_branch = context.owner_has_family == "true" and categories == {
            "non_family"
        }

        if marriage_branch or outside_family_branch:
            reason = (
                f"marriage_date={context.marriage_date.isoformat()}"
                if marriage_branch and context.marriage_date
                else "owner_has_family=true"
            )
            flagged_groups.add(group_key)
            findings.append(
                Finding(
                    rule_id="NPS-VALIDITY-001",
                    finding_type=VALIDITY_WARNING,
                    severity="high",
                    asset_type=representative.asset_type,
                    asset_reference=representative.asset_reference,
                    summary=NPS_VALIDITY_SUMMARY,
                    legal_scope_note=NPS_VALIDITY_SCOPE,
                    suggested_actions=NPS_VALIDITY_ACTIONS,
                    source_a=_source(representative, "NPS nomination"),
                    source_b=FindingSource(
                        label="Confirmed synthetic persona context",
                        locator="persona record",
                        text=context.family_context_source_text or reason,
                    ),
                )
            )
            continue

        if context.owner_has_family == "true" and "ambiguous" in categories:
            findings.append(
                Finding(
                    rule_id="GAP-NPS-RELATIONSHIP",
                    finding_type=SCOPE_GAP,
                    severity="low",
                    asset_type=representative.asset_type,
                    asset_reference=representative.asset_reference,
                    summary=NPS_AMBIGUOUS_SUMMARY,
                    legal_scope_note=NPS_AMBIGUOUS_SCOPE,
                    suggested_actions=NPS_AMBIGUOUS_ACTIONS,
                    source_a=_source(representative, "NPS nomination"),
                )
            )
    return findings, flagged_groups


# --- Rule NPS-WILL-001 ----------------------------------------------------

NPS_WILL_SUMMARY = (
    "The NPS nomination and will name different people for the same NPS account."
)
NPS_WILL_SCOPE = (
    "Current PFRDA regulations govern who receives unpaid NPS money under a valid "
    "nomination, but the cited regulation does not resolve every nominee-versus-will "
    "succession dispute. No ownership or precedence is declared."
)
NPS_WILL_ACTIONS = (
    "Confirm the nomination received by the CRA, intermediary, or nodal office.",
    "Ask an NPS specialist or licensed advisor to review the will and current regulations.",
    "Update the records only after that review.",
)


def rule_nps_will(
    records: list[FieldRecord],
    context: PersonaContext,
    flagged_groups: set[tuple[int, str]],
) -> list[Finding]:
    findings: list[Finding] = []
    for nomination in _nominations(records, "nps_account", "nominee"):
        if nomination.group_key in flagged_groups:
            continue
        for bequest in _bequests(records):
            if same_asset(nomination, bequest) and persons_differ(
                nomination, bequest, context.confirmed_aliases
            ):
                findings.append(
                    _asset_mismatch_finding(
                        "NPS-WILL-001",
                        nomination,
                        bequest,
                        "high",
                        NPS_WILL_SUMMARY,
                        NPS_WILL_SCOPE,
                        NPS_WILL_ACTIONS,
                        "NPS nomination",
                    )
                )
    return findings


# --- Rule RECORD-SUPERSESSION-001 ----------------------------------------

SUPERSESSION_SUMMARY = (
    "Two nomination records for the same asset disagree, and the documents do not prove "
    "which one the institution currently recognizes."
)
SUPERSESSION_SCOPE = (
    "Each framework has a registration, receipt, variation, or supersession concept. "
    "A later file date alone does not prove the institution received or registered it."
)
SUPERSESSION_ACTIONS = (
    "Obtain the institution's current registered nomination.",
    "Retain the acknowledgement for the record that applies.",
    "Mark historical forms as superseded in the synthetic vault only after confirmation.",
)
NOMINATION_MECHANISMS = {"nominee", "beneficiary_nominee"}


def _group_signature(group: list[FieldRecord]) -> frozenset[tuple[str, float | None]]:
    # A sole nominee with no stated share means the whole asset (see DECISIONS D-029),
    # so it must compare equal to an explicit 100%.
    sole_nominee = len(group) == 1
    return frozenset(
        (
            normalize_text(record.named_person),
            100.0 if sole_nominee and record.share_percent is None else record.share_percent,
        )
        for record in group
    )


def _group_registered_date(group: list[FieldRecord]) -> date | None:
    """Acknowledgement date for a fully registered group, never a file date."""
    if not all(record.registration_status == "confirmed" for record in group):
        return None
    dates = [record.registration_date for record in group if record.registration_date]
    return max(dates) if len(dates) == len(group) else None


def _group_claimed_date(group: list[FieldRecord]) -> date | None:
    dates = [
        record.registration_date or record.document_date
        for record in group
        if (record.registration_date or record.document_date)
    ]
    return max(dates) if dates else None


SUPERSESSION_ASSET_TYPES = {
    "bank_account",
    "insurance_policy",
    "mutual_fund_folio",
    "nps_account",
}
UNSUPPORTED_SUPERSESSION_SUMMARY = (
    "Manual review required: two nomination records disagree on an asset outside the "
    "supported rule scope."
)
UNSUPPORTED_SUPERSESSION_NOTE = (
    "The approved rules do not cover this asset type, or the asset is held jointly, or the "
    "policy is under the Married Women's Property Act or an active assignment, so no "
    "supersession conclusion is drawn."
)
UNSUPPORTED_SUPERSESSION_ACTIONS = (
    "Ask the institution which nomination record it currently recognizes.",
    "Ask a licensed advisor to review this asset directly.",
)


def _supersession_in_scope(record: FieldRecord) -> bool:
    if record.asset_type not in SUPERSESSION_ASSET_TYPES:
        return False
    if record.asset_type == "insurance_policy":
        return _life_scope_supported(record)
    return _holding_in_scope(record)


def rule_record_supersession(
    records: list[FieldRecord],
    context: PersonaContext,
) -> list[Finding]:
    findings: list[Finding] = []
    buckets: dict[tuple[tuple[str, str, str], str], dict[tuple[int, str], list[FieldRecord]]] = {}
    for record in records:
        if record.mechanism_type not in NOMINATION_MECHANISMS:
            continue
        if not normalize_text(record.asset_reference):
            continue
        bucket = buckets.setdefault((asset_key(record), record.mechanism_type), {})
        bucket.setdefault(record.group_key, []).append(record)

    for groups in buckets.values():
        if len(groups) < 2:
            continue
        signatures = {key: _group_signature(group) for key, group in groups.items()}
        if len(set(signatures.values())) < 2:
            continue

        all_records = [record for group in groups.values() for record in group]
        if not all(_supersession_in_scope(record) for record in all_records):
            representative = min(all_records, key=lambda record: record.field_id)
            findings.append(
                Finding(
                    rule_id="GAP-UNSUPPORTED-SUPERSESSION",
                    finding_type=SCOPE_GAP,
                    severity="low",
                    asset_type=representative.asset_type,
                    asset_reference=representative.asset_reference,
                    summary=UNSUPPORTED_SUPERSESSION_SUMMARY,
                    legal_scope_note=UNSUPPORTED_SUPERSESSION_NOTE,
                    suggested_actions=UNSUPPORTED_SUPERSESSION_ACTIONS,
                    source_a=_source(representative, "Nomination record"),
                )
            )
            continue

        # Only a fully acknowledged group with a real registration date can supersede,
        # and it must post-date every other record. A later file date proves nothing.
        registered_groups = [
            key for key, group in groups.items() if _group_registered_date(group) is not None
        ]
        proven_supersession = False
        if len(registered_groups) == 1:
            winner = registered_groups[0]
            winner_date = _group_registered_date(groups[winner])
            other_dates = [
                _group_claimed_date(group) for key, group in groups.items() if key != winner
            ]
            proven_supersession = winner_date is not None and all(
                other is not None and winner_date > other for other in other_dates
            )
        if proven_supersession:
            continue

        ordered_keys = sorted(groups)
        for index, left_key in enumerate(ordered_keys):
            for right_key in ordered_keys[index + 1 :]:
                if signatures[left_key] == signatures[right_key]:
                    continue
                left = min(groups[left_key], key=lambda record: record.field_id)
                right = min(groups[right_key], key=lambda record: record.field_id)
                findings.append(
                    Finding(
                        rule_id="RECORD-SUPERSESSION-001",
                        finding_type=REVIEW_CONFLICT,
                        severity="medium",
                        asset_type=left.asset_type,
                        asset_reference=left.asset_reference,
                        summary=SUPERSESSION_SUMMARY,
                        legal_scope_note=SUPERSESSION_SCOPE,
                        suggested_actions=SUPERSESSION_ACTIONS,
                        source_a=_source(left, "Nomination record A"),
                        source_b=_source(right, "Nomination record B"),
                    )
                )
    return findings


# --- Missing-reference gap ------------------------------------------------

MISSING_REFERENCE_SUMMARY = (
    "Manual review required: an extracted record has no asset reference, so it cannot be "
    "matched deterministically."
)
MISSING_REFERENCE_SCOPE = (
    "The rules forbid fuzzy asset matching. A missing or truncated reference is recorded "
    "as an extraction gap instead of a conflict."
)
MISSING_REFERENCE_ACTIONS = (
    "Re-check the source document for the account, policy, folio, or PRAN reference.",
    "Correct the extracted reference and run detection again.",
)


def _missing_reference_gaps(records: list[FieldRecord]) -> list[Finding]:
    return [
        Finding(
            rule_id="GAP-ASSET-REFERENCE",
            finding_type=SCOPE_GAP,
            severity="low",
            asset_type=record.asset_type,
            asset_reference="",
            summary=MISSING_REFERENCE_SUMMARY,
            legal_scope_note=MISSING_REFERENCE_SCOPE,
            suggested_actions=MISSING_REFERENCE_ACTIONS,
            source_a=_source(record, f"{record.document_type} record"),
        )
        for record in records
        if not normalize_text(record.asset_reference)
    ]


NEAR_MISS_SUMMARY = (
    "Manual review required: a nomination and a will clause point at nearly the same "
    "asset, so they cannot be matched deterministically."
)
NEAR_MISS_SCOPE = (
    "The rules forbid fuzzy asset matching. A truncated reference or an institution-name "
    "variant is reported as an extraction gap rather than a conflict or a clean result."
)
NEAR_MISS_ACTIONS = (
    "Compare the asset reference and institution name in both source documents.",
    "Correct the extracted values, or confirm they are the same asset, then run detection again.",
)


def _is_near_variant(left: str, right: str) -> bool:
    if left == right:
        return False
    if not left or not right:
        return True
    return left.startswith(right) or right.startswith(left)


def _near_miss_gaps(records: list[FieldRecord]) -> list[Finding]:
    findings: list[Finding] = []
    nominations = [
        record
        for record in records
        if record.mechanism_type in NOMINATION_MECHANISMS
        and normalize_text(record.asset_reference)
    ]
    bequests = [
        record
        for record in _bequests(records)
        if normalize_text(record.asset_reference)
    ]
    for nomination in nominations:
        for bequest_record in bequests:
            if nomination.asset_type != bequest_record.asset_type:
                continue
            nomination_reference = normalize_text(nomination.asset_reference)
            bequest_reference = normalize_text(bequest_record.asset_reference)
            nomination_institution = normalize_text(nomination.institution_name)
            bequest_institution = normalize_text(bequest_record.institution_name)

            reference_matches = nomination_reference == bequest_reference
            institution_matches = nomination_institution == bequest_institution
            if reference_matches and institution_matches:
                continue

            near_reference = institution_matches and _is_near_variant(
                nomination_reference, bequest_reference
            )
            near_institution = reference_matches and _is_near_variant(
                nomination_institution, bequest_institution
            )
            if not (near_reference or near_institution):
                continue

            findings.append(
                Finding(
                    rule_id="GAP-ASSET-NEAR-MATCH",
                    finding_type=SCOPE_GAP,
                    severity="low",
                    asset_type=nomination.asset_type,
                    asset_reference=nomination.asset_reference,
                    summary=NEAR_MISS_SUMMARY,
                    legal_scope_note=NEAR_MISS_SCOPE,
                    suggested_actions=NEAR_MISS_ACTIONS,
                    source_a=_source(nomination, "Nomination record"),
                    source_b=_source(bequest_record, "Will bequest"),
                )
            )
    return findings


SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def finalize(findings: list[Finding]) -> list[Finding]:
    """Deduplicate and order any finding list, including later-stage additions."""
    deduped: dict[tuple, Finding] = {}
    for finding in findings:
        deduped.setdefault(_dedupe_key(finding), finding)
    return sorted(
        deduped.values(),
        key=lambda f: (
            SEVERITY_ORDER[f.severity],
            f.rule_id,
            normalize_text(f.asset_reference),
        ),
    )


def detect(records: list[FieldRecord], context: PersonaContext) -> DetectionResult:
    """Apply every approved rule in the documented order."""
    findings: list[Finding] = []

    validity_findings, flagged_groups = rule_nps_validity(records, context)
    findings.extend(validity_findings)

    notice_findings, suppressed_pairs = rule_life_notice(records, context)
    findings.extend(notice_findings)

    findings.extend(rule_record_supersession(records, context))

    findings.extend(rule_bank_will(records, context))
    findings.extend(rule_life_will(records, context, suppressed_pairs))
    findings.extend(rule_mf_will(records, context))
    findings.extend(rule_nps_will(records, context, flagged_groups))

    findings.extend(_life_scope_gaps(records, context))
    findings.extend(_joint_holding_gaps(records))
    findings.extend(_missing_reference_gaps(records))
    findings.extend(_near_miss_gaps(records))

    return DetectionResult(findings=finalize(findings))
