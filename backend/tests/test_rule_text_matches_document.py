"""Pin the engine's user-facing rule text to the approved rules document."""

import re
from pathlib import Path

from app import detection

RULES_PATH = Path(__file__).resolve().parents[1] / "rules" / "RULES.md"
RULES_TEXT = RULES_PATH.read_text(encoding="utf-8")

ENGINE_SUMMARIES = {
    "BANK-WILL-001": detection.BANK_WILL_SUMMARY,
    "LIFE-NOTICE-001": detection.LIFE_NOTICE_SUMMARY,
    "LIFE-WILL-001": detection.LIFE_WILL_SUMMARY,
    "MF-WILL-001": detection.MF_WILL_SUMMARY,
    "NPS-WILL-001": detection.NPS_WILL_SUMMARY,
    "NPS-VALIDITY-001": detection.NPS_VALIDITY_SUMMARY,
    "RECORD-SUPERSESSION-001": detection.SUPERSESSION_SUMMARY,
}


def documented_summaries() -> dict[str, str]:
    sections = re.split(r"^## Rule ", RULES_TEXT, flags=re.MULTILINE)[1:]
    summaries: dict[str, str] = {}
    for section in sections:
        rule_id = section.split(" ", maxsplit=1)[0].strip()
        match = re.search(r"\*\*Deterministic summary:\*\* `([^`]+)`", section)
        if match:
            summaries[rule_id] = match.group(1).strip()
    return summaries


def test_every_approved_rule_has_a_documented_summary() -> None:
    assert set(documented_summaries()) == set(ENGINE_SUMMARIES)


def test_engine_summaries_match_the_document_exactly() -> None:
    documented = documented_summaries()

    for rule_id, engine_summary in ENGINE_SUMMARIES.items():
        assert engine_summary == documented[rule_id], rule_id


def test_engine_disclaimer_matches_the_document_exactly() -> None:
    assert detection.DISCLAIMER in RULES_TEXT


def test_engine_implements_exactly_the_approved_rule_ids() -> None:
    documented_ids = set(re.findall(r"^## Rule ([A-Z0-9-]+)", RULES_TEXT, flags=re.MULTILINE))
    engine_ids = {
        constant
        for constant in (
            "BANK-WILL-001",
            "LIFE-NOTICE-001",
            "LIFE-WILL-001",
            "MF-WILL-001",
            "NPS-WILL-001",
            "NPS-VALIDITY-001",
            "RECORD-SUPERSESSION-001",
        )
    }

    assert engine_ids == documented_ids
