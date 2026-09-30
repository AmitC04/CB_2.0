"""The demo reset and seed path must reproduce the pitch numbers without any AI call."""

from pathlib import Path

import pytest

from app.db import get_connection, init_db
from app.demo_seed import PERSONA_KEYS, reset_storage, run_detection, seed_fallback
from app.repository import get_latest_detection_run, list_documents


@pytest.fixture
def storage(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "seed.db"))
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    init_db()


def test_reset_recreates_empty_synthetic_storage(storage: None) -> None:
    seed_fallback()
    reset_storage()

    with get_connection() as connection:
        personas = connection.execute("SELECT COUNT(*) AS n FROM personas").fetchone()["n"]
        documents = connection.execute("SELECT COUNT(*) AS n FROM documents").fetchone()["n"]

    assert personas == 0
    assert documents == 0


def test_fallback_seed_reproduces_the_demo_scores(storage: None) -> None:
    persona_ids = seed_fallback()

    scores = {key: run_detection(persona_ids[key]) for key in PERSONA_KEYS}

    assert scores == {
        "conflict_persona": 75,
        "clean_persona": 100,
        "nps_persona": 75,
        "joint_persona": 97,
    }


def test_fallback_seed_produces_exactly_the_demo_conflict(storage: None) -> None:
    persona_ids = seed_fallback()
    run_detection(persona_ids["conflict_persona"])

    run = get_latest_detection_run(persona_ids["conflict_persona"])

    assert [conflict.rule_id for conflict in run.conflicts] == ["BANK-WILL-001"]
    assert run.conflicts[0].severity == "high"
    assert run.conflicts[0].asset_reference == "SB-DEMO-4821"
    assert run.scope_gaps == []


def test_fallback_documents_are_labelled_as_not_live_ai(storage: None) -> None:
    persona_ids = seed_fallback()

    documents = list_documents(persona_ids["conflict_persona"])

    assert len(documents) == 4
    for document in documents:
        assert document.extraction_source == "manual_fallback"
        assert document.status == "extracted"
        for field in document.fields:
            assert field.source_text
            assert field.source_locator
            assert not field.is_user_edited


def test_clean_persona_seed_has_no_findings(storage: None) -> None:
    persona_ids = seed_fallback()
    run_detection(persona_ids["clean_persona"])

    run = get_latest_detection_run(persona_ids["clean_persona"])

    assert run.conflicts == []
    assert run.scope_gaps == []
    assert run.readiness_score == 100
    assert run.disclaimer.startswith("Not legal advice.")


def test_startup_seed_fills_an_empty_database_with_the_demo(storage: None) -> None:
    """A hosted free-tier instance has no disk, so a cold start must seed itself."""
    from app.demo_seed import ensure_demo_seeded

    seeded = ensure_demo_seeded()

    assert sorted(seeded) == sorted(PERSONA_KEYS)
    scores = {
        key: get_latest_detection_run(persona_id).readiness_score
        for key, persona_id in seeded.items()
    }
    assert scores == {
        "conflict_persona": 75,
        "clean_persona": 100,
        "nps_persona": 75,
        "joint_persona": 97,
    }


def test_startup_seed_leaves_an_already_seeded_database_alone(storage: None) -> None:
    """It must never duplicate personas or wipe an edit someone just demonstrated."""
    from app.demo_seed import ensure_demo_seeded

    ensure_demo_seeded()
    with get_connection() as connection:
        connection.execute(
            "UPDATE extracted_fields SET person_name = 'Edited Person', is_user_edited = 1"
            " WHERE id = (SELECT MIN(id) FROM extracted_fields)"
        )

    second_run = ensure_demo_seeded()

    with get_connection() as connection:
        personas = connection.execute("SELECT COUNT(*) AS n FROM personas").fetchone()["n"]
        edited = connection.execute(
            "SELECT COUNT(*) AS n FROM extracted_fields WHERE person_name = 'Edited Person'"
        ).fetchone()["n"]

    assert second_run == {}
    assert personas == len(PERSONA_KEYS)
    assert edited == 1


def test_startup_seed_is_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    """Off by default, so a local run never seeds behind your back."""
    from app.main import seed_on_startup_enabled

    monkeypatch.delenv("SEED_ON_STARTUP", raising=False)
    assert seed_on_startup_enabled() is False
    monkeypatch.setenv("SEED_ON_STARTUP", "false")
    assert seed_on_startup_enabled() is False
    monkeypatch.setenv("SEED_ON_STARTUP", "TRUE")
    assert seed_on_startup_enabled() is True


def test_nps_persona_demonstrates_the_validity_warning(storage: None) -> None:
    """The one seeded persona that fires a validity_warning rather than a conflict."""
    persona_ids = seed_fallback()
    run_detection(persona_ids["nps_persona"])

    run = get_latest_detection_run(persona_ids["nps_persona"])
    finding = run.conflicts[0]

    assert [c.rule_id for c in run.conflicts] == ["NPS-VALIDITY-001"]
    assert finding.finding_type == "validity_warning"
    assert finding.severity == "high"
    assert finding.asset_reference == "1100-DEMO-3301"
    # NPS-WILL-001 must stay suppressed: the document's own validity is reported first
    # rather than stacking a second finding about the same nomination group.
    assert "NPS-WILL-001" not in [c.rule_id for c in run.conflicts]
    assert run.scope_gaps == []
    assert run.readiness_score == 75


def test_nps_persona_carries_the_confirmed_context_the_rule_depends_on(
    storage: None,
) -> None:
    """Marriage status is stated on the persona record, never inferred from a document."""
    from app.repository import load_persona_context

    persona_ids = seed_fallback()
    context = load_persona_context(persona_ids["nps_persona"])

    assert context.marriage_date is not None
    assert context.owner_has_family == "true"
    assert context.family_context_source_text
    assert "not extracted from any document" in context.family_context_source_text


def test_joint_persona_reports_a_gap_instead_of_a_conflict(storage: None) -> None:
    """The nomination and the will name different people, and it is still not a conflict."""
    persona_ids = seed_fallback()
    run_detection(persona_ids["joint_persona"])

    run = get_latest_detection_run(persona_ids["joint_persona"])
    gap = run.scope_gaps[0]

    assert run.conflicts == []
    assert [g.rule_id for g in run.scope_gaps] == ["GAP-JOINT-HOLDING"]
    assert gap.finding_type == "scope_gap"
    assert gap.severity == "low"
    assert gap.asset_reference == "SB-DEMO-6602"
    assert run.readiness_score == 97


def test_the_joint_seed_document_really_is_extracted_as_jointly_held(
    storage: None,
) -> None:
    """If the extraction said single or unknown, the gap above would be a false positive."""
    persona_ids = seed_fallback()

    nomination = next(
        field
        for document in list_documents(persona_ids["joint_persona"])
        if document.document_type == "bank_nomination"
        for field in document.fields
    )

    assert nomination.holding_pattern.value == "joint"
    assert nomination.named_person == "Latika Demo-Rao"


def test_every_seeded_persona_demonstrates_something_distinct(storage: None) -> None:
    """Guards the pitch claim that the demo shows more than one rule outcome."""
    persona_ids = seed_fallback()
    for persona_id in persona_ids.values():
        run_detection(persona_id)

    outcomes = {
        key: sorted(
            finding.rule_id
            for finding in (
                get_latest_detection_run(persona_id).conflicts
                + get_latest_detection_run(persona_id).scope_gaps
            )
        )
        for key, persona_id in persona_ids.items()
    }

    assert outcomes == {
        "conflict_persona": ["BANK-WILL-001"],
        "clean_persona": [],
        "nps_persona": ["NPS-VALIDITY-001"],
        "joint_persona": ["GAP-JOINT-HOLDING"],
    }
    # One of each kind: a conflict, a clean result, a validity warning, and a scope gap.
    assert len({tuple(value) for value in outcomes.values()}) == len(outcomes)
