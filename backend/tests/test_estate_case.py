"""The stretch estate-case view must stay a clearly labelled concept."""

import asyncio
import inspect
from pathlib import Path

import httpx
import pytest

import app.estate_case as estate_case_module
from app.detection import DISCLAIMER
from app.estate_case import CONCEPT_LABEL, build_estate_case
from app.main import app
from tests.test_detection_api import database, run_detection, seed_persona  # noqa: F401
from tests.test_detection_rules import bequest, mf_nomination, record


def test_items_are_grouped_per_asset_with_illustrative_steps() -> None:
    case = build_estate_case([record(), mf_nomination()])

    assert case.concept is True
    assert case.label == CONCEPT_LABEL
    assert case.disclaimer == DISCLAIMER
    assert [item.asset_type for item in case.items] == [
        "bank_account",
        "mutual_fund_folio",
    ]
    for item in case.items:
        assert item.illustrative_steps
        assert item.has_nomination_on_record is True


def test_generation_is_deterministic() -> None:
    records = [record(), mf_nomination(), bequest()]

    first = build_estate_case(records)
    second = build_estate_case(records)

    assert first.items == second.items


def test_unresolved_conflicts_and_score_are_carried_through() -> None:
    case = build_estate_case([record()], unresolved_conflicts=2, readiness_score=50)

    assert case.unresolved_conflicts == 2
    assert case.readiness_score == 50


def test_records_without_an_asset_reference_are_skipped() -> None:
    case = build_estate_case([record(asset_reference="")])

    assert case.items == []


def test_bequest_only_asset_is_marked_as_having_no_nomination() -> None:
    case = build_estate_case(
        [bequest(asset_type="nps_account", asset_reference="PRAN-X", institution_name="NPS")]
    )

    assert len(case.items) == 1
    assert case.items[0].has_nomination_on_record is False


def test_concept_module_never_touches_detection_or_scoring() -> None:
    source = inspect.getsource(estate_case_module)

    assert "genai" not in source
    assert "readiness_score(" not in source
    assert "detect(" not in source


def test_endpoint_labels_the_concept_and_carries_the_disclaimer(
    database: None,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    persona_id = seed_persona("conflict_persona")

    async def scenario() -> dict:
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                response = await client.get(f"/personas/{persona_id}/estate-case")
                assert response.status_code == 200
                return response.json()

    payload = asyncio.run(scenario())

    assert payload["concept"] is True
    assert payload["label"] == CONCEPT_LABEL
    assert "No bank, insurer" in payload["notice"]
    assert payload["disclaimer"] == DISCLAIMER
    assert len(payload["items"]) == 3
    assert all(item["illustrative_steps"] for item in payload["items"])


def test_endpoint_reports_unresolved_conflicts_from_the_latest_run(
    database: None,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.api as api_module
    from app.explanations import Explanation

    monkeypatch.setattr(
        api_module,
        "generate_explanation",
        lambda finding: Explanation("wording", "fix", "stub"),
    )
    persona_id = seed_persona("conflict_persona")
    run_detection(persona_id)

    async def scenario() -> dict:
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                return (await client.get(f"/personas/{persona_id}/estate-case")).json()

    payload = asyncio.run(scenario())

    assert payload["unresolved_conflicts"] == 1
    assert payload["readiness_score"] == 75


def test_endpoint_requires_an_existing_persona(database: None) -> None:  # noqa: F811
    async def scenario() -> int:
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                return (await client.get("/personas/999/estate-case")).status_code

    assert asyncio.run(scenario()) == 404
