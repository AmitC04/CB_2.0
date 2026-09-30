"""Deterministic Continuity Readiness Score and Phase 5 completeness checks.

The score is arithmetic over findings the Phase 4 engine already produced. No AI is
involved, and the score is not a legal assessment. It is a review-priority indicator
for synthetic demo documents.
"""

from collections.abc import Iterable

from app.detection import (
    SCOPE_GAP,
    FieldRecord,
    Finding,
    FindingSource,
    asset_key,
    normalize_text,
)

BASE_SCORE = 100
SEVERITY_PENALTY = {"high": 25, "medium": 10, "low": 3}

MISSING_NOMINATION_SUMMARY = (
    "The will assigns this asset, but no nomination record for it has been uploaded."
)
MISSING_NOMINATION_NOTE = (
    "A missing nomination is a completeness gap, not a conflict. Institutions generally "
    "settle nomination-based assets through their own records, so an absent nomination "
    "can slow a claim even when the will is clear."
)
MISSING_NOMINATION_ACTIONS = (
    "Check whether a nomination already exists with the institution.",
    "Upload the nomination record if it exists, or ask the institution how to register one.",
)

NOMINATION_MECHANISMS = {"nominee", "beneficiary_nominee"}


def completeness_gaps(
    records: list[FieldRecord],
    existing_findings: list[Finding] | None = None,
) -> list[Finding]:
    """Flag assets a will assigns that have no uploaded nomination record.

    A bequest already covered by a near-match extraction gap is skipped: in that case a
    nomination was uploaded and the reference merely failed to match exactly, so claiming
    the nomination is missing would be wrong and would deduct twice.
    """
    nominated_assets = {
        asset_key(record)
        for record in records
        if record.mechanism_type in NOMINATION_MECHANISMS
        and normalize_text(record.asset_reference)
    }
    near_match_field_ids = {
        source.field_id
        for finding in (existing_findings or [])
        if finding.rule_id == "GAP-ASSET-NEAR-MATCH"
        for source in (finding.source_a, finding.source_b)
        if source is not None and source.field_id is not None
    }

    findings: list[Finding] = []
    seen: set[tuple[str, str, str]] = set()
    for record in records:
        if record.mechanism_type != "bequest":
            continue
        if not normalize_text(record.asset_reference):
            continue
        if record.field_id in near_match_field_ids:
            continue
        key = asset_key(record)
        if key in nominated_assets or key in seen:
            continue
        seen.add(key)
        findings.append(
            Finding(
                rule_id="GAP-MISSING-NOMINATION",
                finding_type=SCOPE_GAP,
                severity="low",
                asset_type=record.asset_type,
                asset_reference=record.asset_reference,
                summary=MISSING_NOMINATION_SUMMARY,
                legal_scope_note=MISSING_NOMINATION_NOTE,
                suggested_actions=MISSING_NOMINATION_ACTIONS,
                source_a=FindingSource(
                    label="Will bequest",
                    locator=record.source_locator,
                    text=record.source_text,
                    field_id=record.field_id,
                ),
            )
        )
    return findings


def breakdown_from_pairs(pairs: Iterable[tuple[str, str]]) -> dict[str, int]:
    """Build the score breakdown from (finding_type, severity) pairs.

    Conflicts and gaps are separated by finding type, not by severity, so a gap can
    never be presented as a conflict or the reverse.
    """
    counts = {"high": 0, "medium": 0, "low": 0}
    conflicts = {"high": 0, "medium": 0, "low": 0}
    gaps = 0
    for finding_type, severity in pairs:
        counts[severity] += 1
        if finding_type == SCOPE_GAP:
            gaps += 1
        else:
            conflicts[severity] += 1
    return {
        "base": BASE_SCORE,
        "high_conflicts": conflicts["high"],
        "medium_conflicts": conflicts["medium"],
        "low_conflicts": conflicts["low"],
        "gaps": gaps,
        "deduction": sum(
            SEVERITY_PENALTY[severity] * count for severity, count in counts.items()
        ),
    }


def score_breakdown(findings: list[Finding]) -> dict[str, int]:
    """Return the deduction that each finding class contributes."""
    return breakdown_from_pairs(
        (finding.finding_type, finding.severity) for finding in findings
    )


def readiness_score(findings: list[Finding]) -> int:
    """Clamp the base score minus severity-weighted deductions to 0-100."""
    deduction = sum(SEVERITY_PENALTY[finding.severity] for finding in findings)
    return max(0, min(BASE_SCORE, BASE_SCORE - deduction))


def conflict_count(findings: list[Finding]) -> int:
    return sum(1 for finding in findings if finding.finding_type != SCOPE_GAP)
