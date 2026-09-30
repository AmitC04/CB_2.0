import re
from pathlib import Path
from urllib.parse import urlparse

RULES_PATH = Path(__file__).resolve().parents[1] / "rules" / "RULES.md"
EXPECTED_RULE_IDS = {
    "BANK-WILL-001",
    "LIFE-NOTICE-001",
    "LIFE-WILL-001",
    "MF-WILL-001",
    "NPS-WILL-001",
    "NPS-VALIDITY-001",
    "RECORD-SUPERSESSION-001",
}
MANDATORY_DISCLAIMER = (
    "Not legal advice. This is a first-pass document consistency check based on a "
    "limited, India-scoped rule set. A licensed legal professional and the relevant "
    "institution should review the documents and current law."
)
ALLOWED_SOURCE_HOSTS = {
    "api.sci.gov.in",
    "ifsca.gov.in",
    "investor.sebi.gov.in",
    "pfrda.org.in",
    "www.sebi.gov.in",
}


def read_rules() -> str:
    return RULES_PATH.read_text(encoding="utf-8")


def rule_sections(document: str) -> dict[str, str]:
    matches = list(
        re.finditer(r"^## Rule ([A-Z0-9-]+) —", document, flags=re.MULTILINE)
    )
    return {
        match.group(1): document[
            match.start() : matches[index + 1].start()
            if index + 1 < len(matches)
            else len(document)
        ]
        for index, match in enumerate(matches)
    }


def test_document_defines_exactly_the_approved_candidate_rules() -> None:
    assert set(rule_sections(read_rules())) == EXPECTED_RULE_IDS


def test_every_rule_is_implementation_ready() -> None:
    required_markers = (
        "**Finding type:**",
        "**Predicate:**",
        "**Deterministic summary:**",
        "**Scope note:**",
        "**Suggested actions:**",
        "**Positive synthetic example:**",
        "**Negative synthetic example:**",
    )

    for rule_id, section in rule_sections(read_rules()).items():
        assert "**Source" in section, rule_id
        for marker in required_markers:
            assert marker in section, f"{rule_id} is missing {marker}"


def test_disclaimer_and_deterministic_ai_boundary_are_explicit() -> None:
    document = read_rules()

    assert MANDATORY_DISCLAIMER in document
    assert "Gemini must never decide whether a rule matched" in document
    assert "must still be returned" in document


def test_all_linked_rule_sources_use_approved_primary_hosts() -> None:
    urls = re.findall(r"\[[^]]+\]\((https://[^)]+)\)", read_rules())

    assert len(urls) >= 5
    assert {urlparse(url).hostname for url in urls} <= ALLOWED_SOURCE_HOSTS


def test_rule_count_remains_within_phase_one_scope() -> None:
    count = len(rule_sections(read_rules()))

    assert 5 <= count <= 8


def test_every_gap_marker_the_engine_can_emit_is_documented() -> None:
    """A gap the code can emit but the document does not describe is an undocumented rule."""
    app_dir = RULES_PATH.parents[1] / "app"
    sources = "".join(
        (app_dir / name).read_text(encoding="utf-8")
        for name in ("detection.py", "scoring.py", "api.py")
    )
    emitted = set(re.findall(r"\bGAP-[A-Z-]+\b", sources))
    documented = set(re.findall(r"`(GAP-[A-Z-]+)`", read_rules()))

    assert emitted, "no gap markers were found in the engine source"
    assert emitted <= documented, f"undocumented gap markers: {sorted(emitted - documented)}"


def test_the_holding_pattern_scope_is_documented_with_all_three_values() -> None:
    document = read_rules()

    assert "holding_pattern" in document
    for value in ("`single`", "`joint`", "`unknown`"):
        assert value in document
    assert "GAP-JOINT-HOLDING" in document
    assert "deliberately in scope" in document
