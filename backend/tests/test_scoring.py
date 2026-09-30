"""Deterministic readiness score and Phase 5 completeness checks."""

from datetime import date

from app.detection import Finding, FindingSource, PersonaContext, detect
from app.scoring import (
    BASE_SCORE,
    completeness_gaps,
    conflict_count,
    readiness_score,
    score_breakdown,
)
from tests.test_detection_rules import bequest, mf_nomination, record


def finding(severity: str, finding_type: str = "review_conflict") -> Finding:
    return Finding(
        rule_id="BANK-WILL-001",
        finding_type=finding_type,
        severity=severity,
        asset_type="bank_account",
        asset_reference="SB-TEST-1",
        summary="Summary.",
        legal_scope_note="Scope.",
        suggested_actions=("Check.",),
        source_a=FindingSource("Bank nomination", "page 1", "text", 1),
    )


def test_clean_result_scores_full_marks() -> None:
    assert readiness_score([]) == BASE_SCORE


def test_severity_weights_are_applied() -> None:
    assert readiness_score([finding("high")]) == 75
    assert readiness_score([finding("medium")]) == 90
    assert readiness_score([finding("low", "scope_gap")]) == 97
    assert readiness_score([finding("high"), finding("medium")]) == 65


def test_score_never_falls_below_zero() -> None:
    assert readiness_score([finding("high")] * 10) == 0


def test_breakdown_explains_the_deduction() -> None:
    breakdown = score_breakdown(
        [finding("high"), finding("medium"), finding("low", "scope_gap")]
    )

    assert breakdown == {
        "base": 100,
        "high_conflicts": 1,
        "medium_conflicts": 1,
        "low_conflicts": 0,
        "gaps": 1,
        "deduction": 38,
    }


def test_breakdown_separates_conflicts_from_gaps_by_finding_type() -> None:
    breakdown = score_breakdown(
        [finding("low", "review_conflict"), finding("high", "validity_warning")]
    )

    assert breakdown["gaps"] == 0
    assert breakdown["low_conflicts"] == 1
    assert breakdown["high_conflicts"] == 1


def test_conflict_count_excludes_gaps() -> None:
    findings = [finding("high"), finding("low", "scope_gap")]

    assert conflict_count(findings) == 1


def test_missing_nomination_is_a_completeness_gap() -> None:
    records = [
        bequest(
            asset_type="mutual_fund_folio",
            asset_reference="MF-TEST-404",
            institution_name="Synthetic Demo AMC",
            document_date=date(2026, 1, 1),
        )
    ]

    gaps = completeness_gaps(records)

    assert [gap.rule_id for gap in gaps] == ["GAP-MISSING-NOMINATION"]
    assert gaps[0].severity == "low"
    assert gaps[0].finding_type == "scope_gap"
    assert gaps[0].asset_reference == "MF-TEST-404"


def test_no_completeness_gap_when_a_nomination_exists() -> None:
    records = [
        mf_nomination(named_person="Shared Person"),
        bequest(
            asset_type="mutual_fund_folio",
            asset_reference="MF-TEST-1",
            institution_name="Synthetic Demo AMC",
            named_person="Shared Person",
        ),
    ]

    assert completeness_gaps(records) == []


def test_completeness_gap_lowers_the_score_for_an_otherwise_clean_persona() -> None:
    records = [
        bequest(
            asset_type="bank_account",
            asset_reference="SB-TEST-777",
            institution_name="Synthetic Demo Bank",
        )
    ]
    findings = detect(records, PersonaContext()).findings + completeness_gaps(records)

    assert readiness_score(findings) == 97
    assert conflict_count(findings) == 0


def test_fixing_a_nominee_name_removes_the_conflict_and_restores_the_score() -> None:
    conflicted = [record(named_person="Wrong Person"), bequest(named_person="Right Person")]
    corrected = [record(named_person="Right Person"), bequest(named_person="Right Person")]

    before = detect(conflicted, PersonaContext()).findings
    after = detect(corrected, PersonaContext()).findings

    assert readiness_score(before) == 75
    assert readiness_score(after) == 100


def test_near_match_gap_suppresses_a_duplicate_missing_nomination_gap() -> None:
    records = [
        record(asset_reference="SB-TEST-1"),
        bequest(asset_reference="SB-TEST-1234"),
    ]
    engine_findings = detect(records, PersonaContext()).findings
    gaps = completeness_gaps(records, engine_findings)

    assert [f.rule_id for f in engine_findings] == ["GAP-ASSET-NEAR-MATCH"]
    assert gaps == []
    assert readiness_score(engine_findings + gaps) == 97


def test_missing_nomination_still_reported_without_a_near_match() -> None:
    records = [
        bequest(
            asset_type="nps_account",
            asset_reference="PRAN-TEST-9/Tier-I",
            institution_name="NPS",
        )
    ]
    engine_findings = detect(records, PersonaContext()).findings

    assert [f.rule_id for f in completeness_gaps(records, engine_findings)] == [
        "GAP-MISSING-NOMINATION"
    ]
