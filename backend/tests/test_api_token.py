"""The optional bearer-token gate used only when the API is not on loopback."""

import asyncio
from pathlib import Path

import httpx
import pytest

from app.main import app, configured_api_token


@pytest.fixture
def database(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "token.db"))
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    from app.db import init_db

    init_db()


def call(
    path: str,
    headers: dict[str, str] | None = None,
    method: str = "GET",
    json_body: dict | None = None,
) -> tuple[int, dict]:
    async def scenario() -> tuple[int, dict]:
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                response = await client.request(
                    method, path, headers=headers, json=json_body
                )
                try:
                    return response.status_code, response.json()
                except ValueError:
                    return response.status_code, {}

    return asyncio.run(scenario())


def test_the_gate_is_off_by_default_so_the_local_demo_is_unchanged(
    database: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("API_TOKEN", raising=False)

    assert configured_api_token() is None
    assert call("/personas")[0] == 200


def test_a_blank_token_is_treated_as_no_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_TOKEN", "   ")

    assert configured_api_token() is None


def test_a_configured_token_is_required_on_data_routes(
    database: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_TOKEN", "demo-token")

    missing_status, missing_body = call("/personas")
    wrong_status, _ = call("/personas", {"Authorization": "Bearer wrong-token"})
    unprefixed_status, _ = call("/personas", {"Authorization": "demo-token"})
    correct_status, _ = call("/personas", {"Authorization": "Bearer demo-token"})

    assert missing_status == 401
    # Same error shape as every router error, so one client parser handles both.
    assert missing_body["detail"]["code"] == "unauthorized"
    assert wrong_status == 401
    assert unprefixed_status == 401
    assert correct_status == 200


def test_write_routes_are_gated_too(
    database: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A read-only check would miss the only thing worth protecting."""
    monkeypatch.setenv("API_TOKEN", "demo-token")

    created = call(
        "/personas",
        method="POST",
        json_body={"name": "X", "description": "y", "synthetic_confirmed": True},
    )
    patched = call("/fields/1", method="PATCH", json_body={"named_person": "X"})
    undone = call("/fields/1/undo", method="POST")

    assert created[0] == 401
    assert patched[0] == 401
    assert undone[0] == 401


def test_a_rejected_request_still_carries_cors_headers(
    database: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without CORS headers a browser reports an opaque failure instead of a 401."""
    monkeypatch.setenv("API_TOKEN", "demo-token")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")

    async def scenario() -> tuple[int, str | None]:
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                response = await client.get(
                    "/personas", headers={"Origin": "http://localhost:3000"}
                )
                return response.status_code, response.headers.get(
                    "access-control-allow-origin"
                )

    status, allow_origin = asyncio.run(scenario())

    assert status == 401
    assert allow_origin == "http://localhost:3000"


def test_a_cors_preflight_is_not_gated(
    database: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_TOKEN", "demo-token")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")

    async def scenario() -> int:
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                response = await client.options(
                    "/personas",
                    headers={
                        "Origin": "http://localhost:3000",
                        "Access-Control-Request-Method": "GET",
                    },
                )
                return response.status_code

    assert asyncio.run(scenario()) == 200


def test_health_stays_open_so_container_checks_keep_working(
    database: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_TOKEN", "demo-token")

    status, body = call("/health")
    with_slash, _ = call("/health/")

    assert status == 200
    assert body["status"] == "ok"
    # A trailing slash must not be answered with 401, which would report the backend down.
    assert with_slash != 401


def test_the_gate_does_not_leak_the_token_in_the_error_body(
    database: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_TOKEN", "demo-token")

    _, body = call("/personas")

    assert "demo-token" not in str(body)
