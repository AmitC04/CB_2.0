"""FastAPI entry point for JeevanSetu."""

import logging
import os
import secrets
import sqlite3
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api import router
from app.db import get_connection, init_db

#: Paths that stay reachable without a token so container and UI health checks work.
#: Compared after stripping a trailing slash, because a health check configured as
#: "/health/" must not be told the backend is down.
UNAUTHENTICATED_PATHS = frozenset({"/health"})


def configured_origins() -> list[str]:
    """Read an explicit comma-separated browser origin allowlist."""
    raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


def configured_api_token() -> str | None:
    """Return the shared bearer token, or None when the API is left open.

    The local demo runs on loopback with no token. Setting API_TOKEN is how a hosted
    deployment stops the API from being world-writable; see docs/DEPLOYMENT.md.
    """
    token = os.getenv("API_TOKEN", "").strip()
    return token or None


def seed_on_startup_enabled() -> bool:
    """Whether a fresh instance should seed the demo itself.

    Hosted free-tier instances have no persistent disk, so the database is empty after
    every cold start. Off by default so a local run never seeds behind your back.
    """
    return os.getenv("SEED_ON_STARTUP", "").strip().lower() == "true"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    if seed_on_startup_enabled():
        from app.demo_seed import ensure_demo_seeded

        seeded = ensure_demo_seeded()
        logging.getLogger("jeevansetu").info(
            "SEED_ON_STARTUP: %s",
            f"seeded {len(seeded)} demo personas" if seeded else "database already seeded",
        )
    yield


app = FastAPI(
    title="JeevanSetu API",
    version="0.2.0",
    description=(
        "Synthetic-data-only estate document extraction demo. "
        "Do not upload real documents. Not legal advice."
    ),
    lifespan=lifespan,
)


async def require_api_token(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Gate every route behind a shared bearer token when API_TOKEN is configured.

    Disabled by default, which keeps the loopback-only demo unchanged. This is one shared
    secret, not user authentication. It stops a hosted backend from being reachable
    directly and keeps the token out of the browser; it does not identify a caller. See
    docs/DEPLOYMENT.md, which states what it does not cover.
    """
    expected = configured_api_token()
    if (
        expected is None
        or request.method == "OPTIONS"
        or request.url.path.rstrip("/") in UNAUTHENTICATED_PATHS
    ):
        return await call_next(request)

    presented = request.headers.get("authorization", "")
    if not secrets.compare_digest(presented, f"Bearer {expected}"):
        return JSONResponse(
            status_code=401,
            content={
                "detail": {
                    "code": "unauthorized",
                    "message": "A valid API token is required for this deployment.",
                }
            },
        )
    return await call_next(request)


# Registration order matters. Starlette prepends, so the middleware added last is the
# outermost one. CORS is added last on purpose: a 401 from the token gate must still
# carry CORS headers, or a browser sees an opaque network failure instead of the status.
app.add_middleware(BaseHTTPMiddleware, dispatch=require_api_token)
app.add_middleware(
    CORSMiddleware,
    allow_origins=configured_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["*"],
)
app.include_router(router)


@app.exception_handler(Exception)
async def unhandled_error(_: Request, exc: Exception) -> JSONResponse:
    """Return a sanitized error instead of leaking internals or document content."""
    logging.getLogger("jeevansetu").exception("Unhandled error: %s", type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content={
            "code": "internal_error",
            "message": (
                "Something went wrong on the server. Stored synthetic records were not "
                "changed. Check the backend logs for details."
            ),
        },
    )


@app.get("/health", tags=["system"])
def health() -> JSONResponse:
    """Report API and SQLite readiness."""
    try:
        with get_connection() as connection:
            connection.execute("SELECT 1").fetchone()
    except (OSError, sqlite3.Error):
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "db": "error"},
        )

    return JSONResponse(content={"status": "ok", "db": "ok"})
