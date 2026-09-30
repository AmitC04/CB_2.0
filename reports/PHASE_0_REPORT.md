# Phase 0 report — Setup

Date: 2026-09-29

Status: Complete; awaiting user review

Implementation commit: `f37e4007e5c4482482304eb2740b4ce7f9cbc432`

Completion tag: `phase-0-done`

## Objective

Create a minimal two-service foundation for JeevanSetu: a Next.js frontend, FastAPI backend, and file-based SQLite database, with the frontend visibly checking backend/database health.

## Completed

- Initialized a Git repository and the required top-level layout.
- Moved the supplied product requirements to `docs/PRD.md`.
- Created Docker Compose with exactly two services: `frontend` and `backend`.
- Added a FastAPI application with:
  - `GET /health`
  - SQLite readiness query
  - 200 `{"status":"ok","db":"ok"}` on success
  - 503 degraded response on database failure
  - explicit configurable CORS allowlist
- Added an idempotent SQLite schema draft for:
  - `personas`
  - `documents`
  - `extracted_fields`
  - `detection_runs`
  - `conflicts`
- Enforced foreign keys, 0–100 stored score bounds, boolean edit flags, and a nonblank result disclaimer.
- Added a Next.js/Tailwind page with a browser-polled backend health badge.
- Added visible synthetic-data and not-legal-advice language.
- Pinned all direct Python and npm dependencies exactly.
- Added backend tests for health, CORS, table creation, foreign-key rejection, required disclaimers, and idempotent persistence.
- Added README, progress tracker, decision log, and this report.

## Not completed (intentionally out of Phase 0)

- Legal research or `backend/rules/RULES.md`
- Document upload or storage behavior
- Claude API integration
- Structured field extraction behavior
- Conflict detection logic
- Readiness scoring logic
- Vault and simulated-fix workflows
- Synthetic demo documents
- Any institution integration
- Stretch estate-case view

None of these are represented in the UI as working.

## Deviations and issues

1. Docker was not installed during the initial pre-flight. Work continued with local tests only until the user installed and started Docker Desktop; all Compose checks were then completed.
2. The user accepted the plan without separately answering three defaults. Per the plan's wording, Phase 0 proceeded with the recommendations: add `detection_runs`, use stdlib `sqlite3`, and move the PRD under `docs/`.
3. The initial generated frontend used ranged development dependencies. They were replaced with the exact resolved versions and the lockfile was synchronized.
4. FastAPI's `TestClient` emitted a deprecation warning with the newest resolved Starlette version. Tests were changed to HTTPX's direct ASGI transport; the final suite passes without warnings and without adding a dependency.
5. The first backend image did not include test sources. Its Dockerfile was corrected and the required in-container test command was re-run successfully.

## Validation evidence

| Check | Result |
|---|---|
| Local backend tests | `7 passed` |
| Backend tests in image | `7 passed` |
| Frontend lint | Passed |
| Frontend production build | Passed; `/` statically generated |
| Compose image build | Passed for frontend and backend |
| Compose service count | Two services |
| Backend container | Running and healthy |
| Frontend container | Running on port 3000 |
| Health response | HTTP 200, `{"status":"ok","db":"ok"}` |
| Allowed CORS origin | `access-control-allow-origin: http://localhost:3000` |
| Unknown CORS origin | No allow-origin header (automated test) |
| Draft schema | Exactly five expected application tables |
| SQLite persistence | Synthetic marker remained after `docker compose down` and `up` |
| Browser connected state | Headless Chrome rendered `Backend connected` |
| Browser failure state | With backend stopped, headless Chrome rendered `Backend unreachable` |
| Service restoration | Backend restarted and returned healthy response |

## Run and demo only Phase 0

From the repository root:

```bash
docker compose up --build
```

1. Open http://localhost:3000.
2. Confirm the top-right badge says **Backend connected**.
3. Open http://localhost:8000/health and confirm `{"status":"ok","db":"ok"}`.
4. Optionally run `docker compose stop backend`; within five seconds the frontend badge changes to **Backend unreachable**.
5. Restore it with `docker compose start backend`.
6. Stop everything with `docker compose down`.

Run the backend tests in the image:

```bash
docker compose run --rm backend pytest
```

## Phase boundary

Stop here. Phase 1 must not start until the user replies exactly:

`APPROVED PHASE 0`
