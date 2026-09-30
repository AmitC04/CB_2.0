"""Positive and negative coverage for every approved deterministic rule."""

import inspect
from datetime import date

import pytest

import app.detection as detection_module
from app.detection import (
    DISCLAIMER,
    RULES_VERSION,
    SCOPE_GAP,
    FieldRecord,
    PersonaContext,
    detect,
    normalize_text,
)

NEXT_ID = {"value": 0}


def record(**overrides) -> FieldRecord:
    NEXT_ID["value"] += 1
    defaults = {
        "field_id": NEXT_ID["value"],
        "document_id": NEXT_ID["value"],
        "document_type": "bank_nomination",
        "document_date": date(2025, 1, 1),
        "document_group_id": "1",
        "asset_type": "bank_account",
        "institution_name": "Synthetic Demo Bank",
        "asset_reference": "SB-TEST-1",
        "named_person": "Nominee Person",
        "relationship": "spouse",
        "mechanism_type": "nominee",
        "share_percent": 100.0,
        "source_text": "Nominee: Nominee Person",
        "source_locator": "page 1",
        "registration_status": "confirmed",
        "registration_date": date(2025, 1, 3),
        "explicit_nomination_action": "none",
        "policy_kind": "unknown",
        "mwpa_section_6_applies": "unknown",
        "assignment_status": "unknown",
        "holding_pattern": "single",
    }
    defaults.update(overrides)
    return FieldRecord(**defaults)


def bequest(**overrides) -> FieldRecord:
    defaults = {
        "document_type": "will",
        "mechanism_type": "bequest",
        "named_person": "Will Person",
        "relationship": "child",
        "registration_status": "unknown",
        "registration_date": None,
        "share_percent": None,
        "source_text": "I give this asset to Will Person.",
        "source_locator": "clause 3",
        "document_date": date(2026, 1, 1),
    }
    defaults.update(overrides)
    return record(**defaults)


def rule_ids(findings) -> list[str]:
    return [finding.rule_id for finding in findings]


# --- BANK-WILL-001 --------------------------------------------------------


def test_bank_will_conflict_detected() -> None:
    result = detect([record(), bequest()], PersonaContext())

    assert rule_ids(result.conflicts) == ["BANK-WILL-001"]
    assert result.conflicts[0].severity == "high"
    assert result.conflicts[0].source_a.label == "Bank nomination"
    assert result.conflicts[0].source_b is not None


def test_bank_will_no_conflict_for_same_person_or_other_account() -> None:
    same_person = detect(
        [record(named_person="Shared Person"), bequest(named_person="Shared Person")],
        PersonaContext(),
    )
    other_account = detect(
        [record(asset_reference="SB-TEST-1"), bequest(asset_reference="SB-TEST-9")],
        PersonaContext(),
    )

    assert same_person.conflicts == []
    assert other_account.conflicts == []


# --- LIFE-NOTICE-001 ------------------------------------------------------


def life_nomination(**overrides) -> FieldRecord:
    defaults = {
        "document_type": "insurance_nomination",
        "asset_type": "insurance_policy",
        "asset_reference": "LIFE-TEST-1",
        "institution_name": "Synthetic Demo Life",
        "mechanism_type": "beneficiary_nominee",
        "policy_kind": "life",
        "mwpa_section_6_applies": "false",
        "assignment_status": "none",
        "registration_status": "confirmed",
        "registration_date": date(2025, 2, 1),
        "named_person": "Registered Nominee",
        "relationship": "spouse",
    }
    defaults.update(overrides)
    return record(**defaults)


def test_life_notice_conflict_when_insurer_notice_unproven() -> None:
    result = detect(
        [
            life_nomination(),
            bequest(
                asset_type="insurance_policy",
                asset_reference="LIFE-TEST-1",
                institution_name="Synthetic Demo Life",
                explicit_nomination_action="change",
            ),
        ],
        PersonaContext(),
    )

    assert "LIFE-NOTICE-001" in rule_ids(result.conflicts)
    assert "LIFE-WILL-001" not in rule_ids(result.conflicts)


def test_life_notice_absent_for_later_acknowledgement_or_generic_bequest() -> None:
    acknowledged = detect(
        [
            life_nomination(
                named_person="Will Person",
                registration_date=date(2026, 6, 1),
            ),
            bequest(
                asset_type="insurance_policy",
                asset_reference="LIFE-TEST-1",
                institution_name="Synthetic Demo Life",
                explicit_nomination_action="change",
                document_date=date(2026, 1, 1),
            ),
        ],
        PersonaContext(),
    )
    generic = detect(
        [
            life_nomination(named_person="Registered Nominee"),
            bequest(
                asset_type="insurance_policy",
                asset_reference="LIFE-TEST-1",
                institution_name="Synthetic Demo Life",
                named_person="Registered Nominee",
            ),
        ],
        PersonaContext(),
    )

    assert "LIFE-NOTICE-001" not in rule_ids(acknowledged.conflicts)
    assert "LIFE-NOTICE-001" not in rule_ids(generic.conflicts)


# --- LIFE-WILL-001 --------------------------------------------------------


def test_life_will_severity_depends_on_nominee_relationship() -> None:
    close_family = detect(
        [
            life_nomination(relationship="spouse"),
            bequest(
                asset_type="insurance_policy",
                asset_reference="LIFE-TEST-1",
                institution_name="Synthetic Demo Life",
            ),
        ],
        PersonaContext(),
    )
    distant = detect(
        [
            life_nomination(relationship="friend"),
            bequest(
                asset_type="insurance_policy",
                asset_reference="LIFE-TEST-1",
                institution_name="Synthetic Demo Life",
            ),
        ],
        PersonaContext(),
    )

    assert [f.severity for f in close_family.conflicts if f.rule_id == "LIFE-WILL-001"] == ["high"]
    assert [f.severity for f in distant.conflicts if f.rule_id == "LIFE-WILL-001"] == ["medium"]


def test_life_will_absent_for_same_person_and_unsupported_scope() -> None:
    aligned = detect(
        [
            life_nomination(named_person="Shared Person"),
            bequest(
                asset_type="insurance_policy",
                asset_reference="LIFE-TEST-1",
                institution_name="Synthetic Demo Life",
                named_person="Shared Person",
            ),
        ],
        PersonaContext(),
    )
    unknown_scope = detect(
        [
            life_nomination(mwpa_section_6_applies="unknown"),
            bequest(
                asset_type="insurance_policy",
                asset_reference="LIFE-TEST-1",
                institution_name="Synthetic Demo Life",
            ),
        ],
        PersonaContext(),
    )

    assert aligned.conflicts == []
    assert unknown_scope.conflicts == []
    assert rule_ids(unknown_scope.scope_gaps) == ["GAP-LIFE-SCOPE"]


# --- MF-WILL-001 ----------------------------------------------------------


def mf_nomination(**overrides) -> FieldRecord:
    defaults = {
        "document_type": "mutual_fund_nomination",
        "asset_type": "mutual_fund_folio",
        "asset_reference": "MF-TEST-1",
        "institution_name": "Synthetic Demo AMC",
        "mechanism_type": "nominee",
    }
    defaults.update(overrides)
    return record(**defaults)


def test_mf_will_conflict_and_alignment() -> None:
    conflict = detect(
        [
            mf_nomination(),
            bequest(
                asset_type="mutual_fund_folio",
                asset_reference="MF-TEST-1",
                institution_name="Synthetic Demo AMC",
            ),
        ],
        PersonaContext(),
    )
    aligned = detect(
        [
            mf_nomination(named_person="Shared Person"),
            bequest(
                asset_type="mutual_fund_folio",
                asset_reference="MF-TEST-1",
                institution_name="Synthetic Demo AMC",
                named_person="Shared Person",
            ),
        ],
        PersonaContext(),
    )

    assert rule_ids(conflict.conflicts) == ["MF-WILL-001"]
    assert aligned.conflicts == []


# --- NPS-WILL-001 and NPS-VALIDITY-001 -----------------------------------


def nps_nomination(**overrides) -> FieldRecord:
    defaults = {
        "document_type": "nps_nomination",
        "asset_type": "nps_account",
        "asset_reference": "PRAN-TEST-1/Tier-I",
        "institution_name": "NPS",
        "mechanism_type": "nominee",
    }
    defaults.update(overrides)
    return record(**defaults)


def nps_bequest(**overrides) -> FieldRecord:
    return bequest(
        asset_type="nps_account",
        asset_reference="PRAN-TEST-1/Tier-I",
        institution_name="NPS",
        **overrides,
    )


def test_nps_will_conflict_detected_when_nomination_looks_valid() -> None:
    result = detect([nps_nomination(), nps_bequest()], PersonaContext())

    assert rule_ids(result.conflicts) == ["NPS-WILL-001"]


def test_nps_will_suppressed_when_validity_warning_fires() -> None:
    result = detect(
        [
            nps_nomination(
                document_date=date(2022, 5, 1),
                registration_status="unconfirmed",
                registration_date=None,
            ),
            nps_bequest(),
        ],
        PersonaContext(marriage_date=date(2024, 3, 1)),
    )

    assert rule_ids(result.conflicts) == ["NPS-VALIDITY-001"]
    assert result.conflicts[0].finding_type == "validity_warning"
    assert result.conflicts[0].source_b is not None


def test_nps_validity_outside_family_and_negative_cases() -> None:
    outside_family = detect(
        [nps_nomination(relationship="friend")],
        PersonaContext(owner_has_family="true"),
    )
    post_marriage_confirmed = detect(
        [
            nps_nomination(
                document_date=date(2025, 1, 1),
                registration_status="confirmed",
                registration_date=date(2025, 1, 5),
            )
        ],
        PersonaContext(marriage_date=date(2024, 3, 1)),
    )
    unknown_context = detect([nps_nomination(relationship="friend")], PersonaContext())

    assert rule_ids(outside_family.conflicts) == ["NPS-VALIDITY-001"]
    assert post_marriage_confirmed.conflicts == []
    assert unknown_context.conflicts == []
    assert unknown_context.scope_gaps == []


def test_ambiguous_nps_relationship_becomes_manual_review_gap() -> None:
    result = detect(
        [nps_nomination(relationship="mother-in-law")],
        PersonaContext(owner_has_family="true"),
    )

    assert result.conflicts == []
    assert rule_ids(result.scope_gaps) == ["GAP-NPS-RELATIONSHIP"]


# --- RECORD-SUPERSESSION-001 ---------------------------------------------


def test_supersession_conflict_when_no_acknowledgement_proves_order() -> None:
    result = detect(
        [
            mf_nomination(
                document_id=1,
                document_group_id="1",
                named_person="First Nominee",
                registration_status="unconfirmed",
                registration_date=None,
                document_date=date(2024, 1, 1),
            ),
            mf_nomination(
                document_id=2,
                document_group_id="1",
                named_person="Second Nominee",
                registration_status="unconfirmed",
                registration_date=None,
                document_date=date(2025, 1, 1),
            ),
        ],
        PersonaContext(),
    )

    assert rule_ids(result.conflicts) == ["RECORD-SUPERSESSION-001"]
    assert result.conflicts[0].severity == "medium"


def test_supersession_absent_when_one_registered_record_is_provably_later() -> None:
    result = detect(
        [
            mf_nomination(
                document_id=1,
                document_group_id="1",
                named_person="First Nominee",
                registration_status="unconfirmed",
                registration_date=None,
                document_date=date(2024, 1, 1),
            ),
            mf_nomination(
                document_id=2,
                document_group_id="1",
                named_person="Second Nominee",
                registration_status="confirmed",
                registration_date=date(2025, 6, 1),
                document_date=date(2025, 5, 1),
            ),
        ],
        PersonaContext(),
    )

    assert "RECORD-SUPERSESSION-001" not in rule_ids(result.conflicts)


def test_multiple_nominees_on_one_form_are_not_a_supersession_conflict() -> None:
    result = detect(
        [
            mf_nomination(document_id=7, document_group_id="1", named_person="Child One", share_percent=60.0),
            mf_nomination(document_id=7, document_group_id="1", named_person="Child Two", share_percent=40.0),
        ],
        PersonaContext(),
    )

    assert result.conflicts == []


# --- Cross-cutting guarantees --------------------------------------------


def test_confirmed_alias_resolves_a_name_difference() -> None:
    aliases = frozenset({frozenset({normalize_text("A. Person"), normalize_text("Anita Person")})})
    result = detect(
        [record(named_person="A. Person"), bequest(named_person="Anita Person")],
        PersonaContext(confirmed_aliases=aliases),
    )

    assert result.conflicts == []


def test_missing_asset_reference_is_a_gap_not_a_conflict() -> None:
    result = detect(
        [record(asset_reference=""), bequest(asset_reference="")],
        PersonaContext(),
    )

    assert result.conflicts == []
    assert rule_ids(result.scope_gaps) == [
        "GAP-ASSET-REFERENCE",
        "GAP-ASSET-REFERENCE",
    ]


def test_every_finding_carries_exact_disclaimer_and_rules_version() -> None:
    result = detect(
        [
            record(),
            bequest(),
            nps_nomination(relationship="friend"),
        ],
        PersonaContext(owner_has_family="true"),
    )

    assert result.findings
    for finding in result.findings:
        assert finding.disclaimer == DISCLAIMER
        assert finding.rules_version == RULES_VERSION
        assert finding.summary.strip()
        assert finding.legal_scope_note.strip()
        assert finding.suggested_actions


def test_findings_are_ordered_by_review_priority() -> None:
    result = detect(
        [
            record(),
            bequest(),
            mf_nomination(
                document_id=11,
                document_group_id="1",
                named_person="First",
                registration_status="unconfirmed",
                registration_date=None,
            ),
            mf_nomination(
                document_id=12,
                document_group_id="1",
                named_person="Second",
                registration_status="unconfirmed",
                registration_date=None,
            ),
        ],
        PersonaContext(),
    )

    severities = [finding.severity for finding in result.findings]
    assert severities == sorted(severities, key=lambda s: {"high": 0, "medium": 1, "low": 2}[s])


def test_engine_contains_no_ai_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    source = inspect.getsource(detection_module)
    assert "genai" not in source
    assert "explanations" not in source

    import google.genai as genai_module

    def explode(*args, **kwargs):
        raise AssertionError("the deterministic engine must not construct an AI client")

    monkeypatch.setattr(genai_module, "Client", explode)
    result = detect([record(), bequest()], PersonaContext())

    assert rule_ids(result.conflicts) == ["BANK-WILL-001"]


# --- Regression coverage for suppression precision -----------------------


def test_stale_acknowledgement_does_not_cancel_life_notice() -> None:
    """An acknowledgement that still records the previous nominee proves nothing."""
    result = detect(
        [
            life_nomination(
                named_person="Old Nominee",
                relationship="friend",
                registration_status="confirmed",
                registration_date=date(2026, 6, 1),
            ),
            bequest(
                asset_type="insurance_policy",
                asset_reference="LIFE-TEST-1",
                institution_name="Synthetic Demo Life",
                named_person="New Person",
                explicit_nomination_action="change",
                document_date=date(2026, 1, 1),
            ),
        ],
        PersonaContext(),
    )

    assert "LIFE-NOTICE-001" in rule_ids(result.conflicts)
    assert [f.severity for f in result.conflicts if f.rule_id == "LIFE-NOTICE-001"] == ["high"]


def test_confirmed_nomination_on_another_nps_account_does_not_silence_validity() -> None:
    result = detect(
        [
            nps_nomination(
                document_id=1,
                asset_reference="PRAN-TEST-1/Tier-I",
                document_date=date(2022, 5, 1),
                registration_status="unconfirmed",
                registration_date=None,
            ),
            nps_nomination(
                document_id=2,
                asset_reference="PRAN-TEST-2/Tier-I",
                document_date=date(2025, 1, 1),
                registration_status="confirmed",
                registration_date=date(2025, 1, 5),
            ),
        ],
        PersonaContext(marriage_date=date(2024, 3, 1)),
    )

    flagged = [f for f in result.conflicts if f.rule_id == "NPS-VALIDITY-001"]
    assert [f.asset_reference for f in flagged] == ["PRAN-TEST-1/Tier-I"]


def test_supersession_winner_needs_a_registration_date_not_a_file_date() -> None:
    result = detect(
        [
            mf_nomination(
                document_id=1,
                named_person="First Nominee",
                registration_status="unconfirmed",
                registration_date=None,
                document_date=date(2024, 1, 1),
            ),
            mf_nomination(
                document_id=2,
                named_person="Second Nominee",
                registration_status="confirmed",
                registration_date=None,
                document_date=date(2025, 1, 1),
            ),
        ],
        PersonaContext(),
    )

    assert rule_ids(result.conflicts) == ["RECORD-SUPERSESSION-001"]


def test_supersession_on_unsupported_asset_becomes_a_gap() -> None:
    mwpa_policy = detect(
        [
            life_nomination(
                document_id=1,
                named_person="First Nominee",
                mwpa_section_6_applies="true",
                assignment_status="active",
                registration_status="unconfirmed",
                registration_date=None,
            ),
            life_nomination(
                document_id=2,
                named_person="Second Nominee",
                mwpa_section_6_applies="true",
                assignment_status="active",
                registration_status="unconfirmed",
                registration_date=None,
            ),
        ],
        PersonaContext(),
    )
    other_asset = detect(
        [
            record(
                document_id=1,
                asset_type="other",
                asset_reference="OTHER-1",
                named_person="First Nominee",
                registration_status="unconfirmed",
                registration_date=None,
            ),
            record(
                document_id=2,
                asset_type="other",
                asset_reference="OTHER-1",
                named_person="Second Nominee",
                registration_status="unconfirmed",
                registration_date=None,
            ),
        ],
        PersonaContext(),
    )

    assert mwpa_policy.conflicts == []
    assert "GAP-UNSUPPORTED-SUPERSESSION" in rule_ids(mwpa_policy.scope_gaps)
    assert other_asset.conflicts == []
    assert "GAP-UNSUPPORTED-SUPERSESSION" in rule_ids(other_asset.scope_gaps)


def test_near_miss_asset_reference_or_institution_becomes_a_gap() -> None:
    truncated = detect(
        [record(asset_reference="SB-TEST-4821"), bequest(asset_reference="SB-TEST-482")],
        PersonaContext(),
    )
    institution_variant = detect(
        [
            record(institution_name="Synthetic Demo Bank"),
            bequest(institution_name="Synthetic Demo Bank Ltd"),
        ],
        PersonaContext(),
    )

    assert truncated.conflicts == []
    assert rule_ids(truncated.scope_gaps) == ["GAP-ASSET-NEAR-MATCH"]
    assert institution_variant.conflicts == []
    assert rule_ids(institution_variant.scope_gaps) == ["GAP-ASSET-NEAR-MATCH"]


def test_sole_nominee_share_representation_is_not_a_supersession_conflict() -> None:
    result = detect(
        [
            mf_nomination(
                document_id=1,
                named_person="Same Nominee",
                share_percent=None,
                registration_status="unconfirmed",
                registration_date=None,
            ),
            mf_nomination(
                document_id=2,
                named_person="Same Nominee",
                share_percent=100.0,
                registration_status="unconfirmed",
                registration_date=None,
            ),
        ],
        PersonaContext(),
    )

    assert result.conflicts == []


def test_gap_markers_are_namespaced_and_not_approved_rule_ids() -> None:
    result = detect(
        [
            record(asset_reference=""),
            life_nomination(mwpa_section_6_applies="unknown"),
            bequest(
                asset_type="insurance_policy",
                asset_reference="LIFE-TEST-1",
                institution_name="Synthetic Demo Life",
            ),
        ],
        PersonaContext(),
    )

    assert result.scope_gaps
    for gap in result.scope_gaps:
        assert gap.rule_id.startswith("GAP-")
        assert gap.severity == "low"
        assert gap.finding_type == SCOPE_GAP


# --- Joint-holding scope (previously a recorded gap) ---------------------


def test_joint_bank_account_becomes_a_gap_not_a_conflict() -> None:
    result = detect(
        [record(holding_pattern="joint"), bequest()],
        PersonaContext(),
    )

    assert result.conflicts == []
    assert rule_ids(result.scope_gaps) == ["GAP-JOINT-HOLDING"]
    assert result.scope_gaps[0].severity == "low"
    assert result.scope_gaps[0].source_b is not None


def test_joint_mutual_fund_folio_becomes_a_gap_not_a_conflict() -> None:
    result = detect(
        [
            mf_nomination(holding_pattern="joint"),
            bequest(
                asset_type="mutual_fund_folio",
                asset_reference="MF-TEST-1",
                institution_name="Synthetic Demo AMC",
            ),
        ],
        PersonaContext(),
    )

    assert result.conflicts == []
    assert rule_ids(result.scope_gaps) == ["GAP-JOINT-HOLDING"]


def test_single_and_unknown_holdings_still_report_the_conflict() -> None:
    single = detect([record(holding_pattern="single"), bequest()], PersonaContext())
    unknown = detect([record(holding_pattern="unknown"), bequest()], PersonaContext())

    assert rule_ids(single.conflicts) == ["BANK-WILL-001"]
    assert rule_ids(unknown.conflicts) == ["BANK-WILL-001"]
    assert single.scope_gaps == []


def test_joint_holding_does_not_affect_nps_or_insurance_rules() -> None:
    nps = detect(
        [nps_nomination(holding_pattern="joint"), nps_bequest()],
        PersonaContext(),
    )

    assert rule_ids(nps.conflicts) == ["NPS-WILL-001"]


def test_joint_holding_is_excluded_from_supersession() -> None:
    result = detect(
        [
            mf_nomination(
                document_id=1,
                named_person="First",
                holding_pattern="joint",
                registration_status="unconfirmed",
                registration_date=None,
            ),
            mf_nomination(
                document_id=2,
                named_person="Second",
                holding_pattern="joint",
                registration_status="unconfirmed",
                registration_date=None,
            ),
        ],
        PersonaContext(),
    )

    assert result.conflicts == []
    assert "GAP-UNSUPPORTED-SUPERSESSION" in rule_ids(result.scope_gaps)
    gap = next(
        finding
        for finding in result.scope_gaps
        if finding.rule_id == "GAP-UNSUPPORTED-SUPERSESSION"
    )
    # The note must say why, otherwise it claims the asset type is unsupported when the
    # real reason is the holding pattern.
    assert "held jointly" in gap.legal_scope_note


def test_one_joint_record_pushes_a_mixed_supersession_group_out_of_scope() -> None:
    """Fail closed: a group containing a joint record gets no supersession conclusion."""
    result = detect(
        [
            mf_nomination(
                document_id=1,
                named_person="First",
                holding_pattern="single",
                registration_status="unconfirmed",
                registration_date=None,
            ),
            mf_nomination(
                document_id=2,
                named_person="Second",
                holding_pattern="joint",
                registration_status="unconfirmed",
                registration_date=None,
            ),
        ],
        PersonaContext(),
    )

    assert result.conflicts == []
    assert "GAP-UNSUPPORTED-SUPERSESSION" in rule_ids(result.scope_gaps)


def test_a_joint_holding_where_the_names_agree_is_still_a_gap() -> None:
    """The rules do not cover a joint holding, so the engine cannot call it clean."""
    result = detect(
        [record(holding_pattern="joint"), bequest(named_person="Nominee Person")],
        PersonaContext(),
    )

    assert result.conflicts == []
    assert rule_ids(result.scope_gaps) == ["GAP-JOINT-HOLDING"]


def test_a_joint_holding_with_a_mechanism_the_rules_never_match_is_not_gapped() -> None:
    """The gap is the complement of the skipped rule, not a wider net."""
    result = detect(
        [record(holding_pattern="joint", mechanism_type="beneficiary_nominee"), bequest()],
        PersonaContext(),
    )

    assert "GAP-JOINT-HOLDING" not in rule_ids(result.scope_gaps)
