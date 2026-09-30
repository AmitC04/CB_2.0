# Deployment

The demo ships as a loopback-only Docker Compose stack with no authentication. That is safe on a laptop and unsafe anywhere else. This document is the runbook for putting it somewhere reachable, and it is deliberately explicit about what is not done for you.

## Status

`render.yaml` in the repository root is a complete Render Blueprint for this stack, and the wiring it describes has been rehearsed locally in containers shaped exactly like the two Render services. What it has not had is a Render account: creating the services requires signing in, connecting the repository and reading one generated password out of the dashboard. Section 1 is that walkthrough.

What is built and verified:

- A bearer-token gate on the API, off by default (`backend/app/main.py`).
- A server-side proxy route so the token never reaches the browser (`frontend/app/api/backend/[...path]/route.ts`).
- A shared-credential gate in front of everything the internet can reach, including the proxy (`frontend/middleware.ts`).
- Self-seeding on a cold start, because the free plan has no persistent disk (`SEED_ON_STARTUP`).

See "Verified behaviour" for exactly what was checked and what was not.

## 1. Deploying to Render

The blueprint provisions two Docker web services on the free plan. Free instances spin down after roughly 15 minutes idle, so the first request after a pause takes about a minute while both services wake and the backend reseeds.

1. **Push the repository** to GitHub, then sign in to Render with the same GitHub account.
2. **New → Blueprint**, pick the repository, and let Render read `render.yaml`. It will show two services: `jeevansetu-backend` and `jeevansetu-frontend`.
3. **Fill the one prompted value.** Render asks for `GEMINI_API_KEY` because it is marked `sync: false`. Leaving it blank is supported: the demo still runs on the pre-verified snapshot, but live extraction and the plain-language wording will be unavailable. Everything else is generated or wired automatically.
4. **Apply**, and wait for both services to go live. The backend must reach `healthy` on `/health` before the frontend is useful.
5. **Read the demo password.** Open `jeevansetu-frontend` → Environment → `BASIC_AUTH_PASSWORD`. The username is `judge`. That pair is what you share with whoever needs access.
6. **Open the frontend URL**, sign in with those credentials, and you should see both personas already seeded: Aarav Demo-Mehta at 75 with one `BANK-WILL-001`, Rohan Demo-Sen at 100.

### What the blueprint does, and why

| Choice | Reason |
|---|---|
| Two web services, not a private service | Private services need a paid plan, so the backend is public and `API_TOKEN` is what protects it. |
| `API_TOKEN` generated on the backend, referenced by the frontend | The browser never holds it; only the Next.js server attaches it. |
| `CORS_ORIGINS` empty | The browser talks only to the frontend's own proxy, so no cross-origin call needs to be allowed. |
| `BASIC_AUTH_USER` / `BASIC_AUTH_PASSWORD` on the frontend | The proxy relays anything that reaches it, so the frontend is where access control has to live. |
| `PUBLIC_DEPLOYMENT=true` | Makes the frontend refuse traffic if those credentials are ever missing, instead of serving an open upload endpoint. |
| `DATABASE_PATH` under `/tmp` | Persistent disks need a paid plan. Nothing stored is worth keeping; every document is synthetic. |
| `SEED_ON_STARTUP=true` | Because storage is ephemeral, a cold start would otherwise show an empty vault. This re-inserts the labelled snapshot. It never overwrites existing data. |
| `region: singapore` | Closest Render region to India. Change it freely; nothing depends on it. |

### If the frontend deploy times out on a health check

The symptom is `Timed out after waiting for internal health check to return a successful response code at: <host>:10000/`, with a build log that otherwise shows Next.js starting normally.

The cause is the health check path being `/`, which the credential gate answers with `401`. Render reads anything other than a 2xx as unhealthy and eventually fails the deploy. The frontend's health check must be `/healthz`, which is the one path the gate lets through.

This is fixed in `render.yaml`. If a service was created before the fix, the blueprint sync updates it, but you can also set it directly: **jeevansetu-frontend → Settings → Health Check Path → `/healthz`**, which takes effect on the next deploy without waiting for a sync.

### If Render rejects the API_TOKEN reference

The frontend copies the backend's token with `fromService` + `envVarKey`. If your Render workspace rejects that field, delete those three lines and set `API_TOKEN` on the frontend by hand to match the value on the backend. Nothing else changes.

### Upgrading to a persistent database

Add a paid instance type and a disk to the backend, then point `DATABASE_PATH` at the mount path and drop `SEED_ON_STARTUP`. Seed once with `python scripts/seed_demo.py --yes` from the service shell. Beyond a demo, replace SQLite with Postgres: there is no migration framework, and a schema change resets the file.

## Threat model, and what the token gate does not do

Every document in this project is synthetic and the API stores nothing sensitive, so the risk is not data theft. The risk is an open write endpoint: anyone who finds the URL could upload documents, spend your Gemini quota, and fill your disk.

The token gate does two things. It stops anyone reaching the backend directly, and it keeps the credential out of the browser bundle. That is worth having, and it is the whole of it.

**It does not make the application authenticated.** Read this before following section 2. Under the recommended wiring the frontend is public and the proxy route attaches the token to whatever arrives, so a public frontend is still a public write path — one hop further away, not closed. Anyone who finds the frontend URL can still upload and still spend your quota.

That is what `frontend/middleware.ts` closes. One shared username and password, checked on every request the internet can make, the proxy route included. Set `BASIC_AUTH_USER` and `BASIC_AUTH_PASSWORD` and the gate is active; leave either blank on an instance marked `PUBLIC_DEPLOYMENT=true` and the service returns 503 rather than serving unprotected. The Render blueprint sets all three, so a blueprint deploy is protected by default.

Be clear about what that is and is not. It is a door with one key, enough to share a demo URL without leaving the upload path open. It is not authentication: there are no accounts, no per-user isolation, no rate limiting, and no record of who called what. Nothing in this repository adds any of that. If you need more, put platform access control in front of it — Cloudflare Access, an identity-aware proxy, an IP allowlist — or do not publish it at all.

## 2. The token gate on the API

Set `API_TOKEN` on the backend to a long random value. The Render blueprint generates one; by hand:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

With it set, every route needs `Authorization: Bearer <token>`. `GET /health` stays open so container and load-balancer health checks keep working; it returns readiness only, no document data. Use the path `/health` exactly — `/health/` gets a `307` from the router, which a checker that does not follow redirects will read as a failure. That is FastAPI's trailing-slash behaviour, not the gate.

Leaving `API_TOKEN` empty disables the gate. That is the default, and it is correct for the loopback demo only.

## 3. Routing the browser through the proxy

Do not put the token in a `NEXT_PUBLIC_*` variable. Anything with that prefix is compiled into the browser bundle and is readable by anyone.

| Variable | Read by | Hosted value |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | the browser bundle, at **build** time | `/api/backend`, which is the Dockerfile's default |
| `BACKEND_URL` | the Next.js server | the backend's address; a bare hostname is treated as `https://` |
| `API_TOKEN` | the Next.js server and the backend | the same value on both |
| `BASIC_AUTH_USER`, `BASIC_AUTH_PASSWORD` | the Next.js server | the shared credential for the demo URL |
| `PUBLIC_DEPLOYMENT` | the Next.js server | `true`, so a missing credential fails closed |
| `CORS_ORIGINS` | the backend | empty, because the browser only ever calls the frontend |

`NEXT_PUBLIC_API_URL` is a build argument rather than a runtime variable, because Render cannot pass environment variables into a Docker build. `docker/frontend.Dockerfile` therefore defaults it to the proxy path, and `docker-compose.yml` overrides it with `http://localhost:8000` for the local demo. A hosted image built with no arguments points the browser at the proxy, which is the safe direction to get wrong.

With this wiring the browser calls a same-origin path, the Next.js server attaches the token, and the credential never reaches the client. On Render's free plan the backend is still publicly reachable, which is exactly why `API_TOKEN` is not optional there. On a paid plan, make the backend a private service and it becomes unreachable from outside.

## 4. Everything else to know before publishing

- **TLS.** Render terminates HTTPS for you. On your own infrastructure, terminate it at a proxy: the token and the Basic credential are both bearer secrets and must never cross plain HTTP.
- **Storage.** SQLite has no migration framework, and a schema change resets the database (`SCHEMA_VERSION` in `backend/app/db.py`). On the free plan there is no disk at all, so `SEED_ON_STARTUP=true` re-inserts the labelled snapshot on every cold start. For anything long-lived, move to Postgres.
- **Uploads.** `UPLOAD_DIR` is local disk, and ephemeral on the free plan. A document uploaded during a demo does not survive a restart. Multiple instances would need shared or object storage.
- **Quota.** The Gemini free tier is rate limited, and its terms allow Google to use submitted content to improve its products. That is acceptable only because every document here is synthetic. The upload path already requires an explicit synthetic attestation; keep that visible.
- **Cold starts.** A free instance spins down after about 15 minutes idle. The first request afterwards takes roughly a minute. If you are demoing live, open the URL a few minutes beforehand.
- **Logs.** The global error handler returns a sanitized message, but tracebacks still go to the backend logs. Do not ship those logs anywhere untrusted.

## 5. Verified behaviour

**The token gate and proxy**, checked against a backend on `127.0.0.1:8100` with `API_TOKEN` set and a Next.js server on `127.0.0.1:3100`:

| Check | Result |
|---|---|
| `GET /personas` directly, no token | `401`, body `{"detail":{"code":"unauthorized",...}}` |
| `GET /health` directly, no token | `200` |
| `GET /api/backend/personas` through the proxy | `200` |
| `POST /api/backend/personas/1/detections` through the proxy | `404` passed through from the backend |
| `POST /api/backend/personas/1/documents` multipart upload | `400` `synthetic_confirmation_required`, so the file and form fields arrived intact |
| `DELETE` through the proxy | `405`, only GET, POST and PATCH are exported |

**The full hosted wiring**, rehearsed in two containers built from the same Dockerfiles Render uses, on an isolated Docker network, with `PORT` assigned by the host as Render does:

| Check | Result |
|---|---|
| `GET /healthz`, no credentials | `200 ok` — the platform health check must not be gated |
| `GET /healthzz`, a lookalike path | `401`, so the exemption is exactly one path |
| Frontend with no credentials | `401` with a `WWW-Authenticate: Basic` challenge |
| `/api/backend/personas` with no credentials | `401` — the proxy is no longer an anonymous relay |
| Frontend with the correct credentials | `200` on `/` and on `/personas/1` |
| Frontend with a wrong password | `401` |
| Startup seeding on an empty ephemeral database | Both personas present; 75 with one `BANK-WILL-001`, and 100 |
| The hosted browser bundle | contains `/api/backend`, and no `localhost:8000` |
| The token in anything the browser receives | absent |

Automated coverage: `backend/tests/test_api_token.py` for the gate (off by default, blank token counts as absent, missing or wrong or unprefixed headers rejected, `POST` and `PATCH` gated, preflight not gated, a 401 still carries CORS headers, `/health` open, the token never echoed); `frontend/app/lib/basicAuth.test.ts` for the credential gate (inert when unconfigured, fails closed when public and unconfigured, wrong user and wrong password and password prefixes rejected, malformed headers do not throw, a password containing colons works); `frontend/app/lib/backendUrl.test.ts` for the bare-hostname default; and `backend/tests/test_demo_seed.py` for startup seeding, including that it leaves an already-seeded database and a demonstrated edit alone.

Not verified: a live Render deployment, a custom domain, Postgres, or object storage. The proxy route and the middleware have no automated route-level tests; both were verified by hand as recorded above.

## 6. Local rehearsal of the hosted wiring

This is the check in the second table, reproducible in one go:

```bash
docker build -t js-be-hosted -f docker/backend.Dockerfile .
docker build -t js-fe-hosted -f docker/frontend.Dockerfile .
docker network create jsrehearsal

docker run -d --name js-be --network jsrehearsal \
  -e PORT=10000 -e API_TOKEN=rehearsal-token -e SEED_ON_STARTUP=true \
  -e DATABASE_PATH=/tmp/js/jeevansetu.db -e UPLOAD_DIR=/tmp/js/uploads \
  -e CORS_ORIGINS= js-be-hosted

docker run -d --name js-fe --network jsrehearsal -p 127.0.0.1:3200:10001 \
  -e PORT=10001 -e BACKEND_URL=http://js-be:10000 -e API_TOKEN=rehearsal-token \
  -e PUBLIC_DEPLOYMENT=true -e BASIC_AUTH_USER=judge -e BASIC_AUTH_PASSWORD=letmein \
  js-fe-hosted

curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3200/                     # 401
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3200/api/backend/personas  # 401
curl -s -u judge:letmein http://127.0.0.1:3200/api/backend/personas                  # both personas

docker rm -f js-be js-fe && docker network rm jsrehearsal
```

Not legal advice, and not a security audit. This is a hackathon prototype that handles synthetic documents.
