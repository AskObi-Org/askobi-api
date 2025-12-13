# Tech Stack & Domain Fit (AskObi API)

This document answers the prompt “determine the tech stack” in a beginner-friendly way.

## What this project is

This repository is a backend API service for AskObi. Today, based on the code currently present, it’s primarily an **authentication + session management API** (login, logout, refresh, session listing, `/me`) plus the platform plumbing (logging, OpenAPI docs, migrations, DB + Redis wiring).

Even though the project description says “Medical intelligence engine”, there is **no symptom analysis or ML inference API implemented yet** in the code that exists in this repo.

## Core Technology Analysis

### Language

- **Python** (declared requirement is `>=3.13,<4.0` in `pyproject.toml`).

Why it matters: the code uses modern typing features (e.g., `type` aliases), Pydantic v2, and async/await heavily.

### Web framework

- **FastAPI** for HTTP routing and request/response modeling.
- **Starlette** (under the hood via FastAPI) for the ASGI layer and middleware.

Key evidence:
- The app is created in `src/main.py` via `FastAPI(...)`.
- Routers are included via `app.include_router(...)`.

### Data layer

- **PostgreSQL** as the database.
- **SQLAlchemy 2.x (async)** as the ORM.
- **advanced-alchemy** is present (used for model base and some exceptions).
- **asyncpg** is the Postgres driver.

Key evidence:
- `src/utils/db.py` creates an `AsyncEngine` and an `async_sessionmaker`.
- Repositories in `src/repositories/user_repository.py` issue `select(...)` queries.

### Sessions / caching

- **Redis** is used as a session cache for fast authentication checks.
- `redis.asyncio` is used (async Redis client).

Key evidence:
- `src/utils/redis.py` implements `store_session`, `get_session`, etc.
- `src/auth/dependencies.py` checks Redis before accepting a JWT.

### Auth & security

- **JWT** for short-lived access tokens (`pyjwt` dependency).
- **Rotating refresh tokens**: a raw refresh token is returned to the client, but only a salted SHA-256 hash is stored in the database.
- **Bcrypt** for password hashing (via `pwdlib[bcrypt]`).

Key evidence:
- `src/utils/tokens.py` builds JWT payloads and hashes refresh tokens.
- `src/services/auth_service.py` rotates refresh tokens.
- `src/utils/authorization.py` hashes/verifies passwords.

### Validation / schemas

- **Pydantic v2** for request/response validation.
- A custom `Schema` base class that normalizes input objects into dicts and trims string values.

Key evidence:
- `src/schemas/base.py` defines `Schema` and its `model_validator`.

### Migrations

- **Alembic** for migrations.
- Autogeneration is wired to the project’s SQLAlchemy metadata.

Key evidence:
- `alembic/env.py` sets `target_metadata = Model.metadata`.

### Logging / observability

- **structlog** for structured logging.
- A correlation-id middleware binds a request ID into logging context.
- Optional **Sentry** integration is declared as a dependency (but wiring depends on runtime configuration; see `src/main.py` and `src/settings.py`).

Key evidence:
- `src/utils/logging.py` configures structlog.
- `src/main.py` installs `LogCorrelationIdMiddleware`.

### Process / deployment

- **Uvicorn** for local development.
- **Gunicorn** + `uvicorn.workers.UvicornWorker` for production.
- **Docker Compose** provides local Postgres + Redis.

Key evidence:
- `gunicorn.conf.py` declares worker class and env-driven concurrency.
- `docker-compose.yml` maps Postgres to `5458` and Redis to `6383`.

### Tooling

- **Poetry** is the package manager (repo has `poetry.lock`).
- **Taskipy** defines common tasks (`task api`, migrations, etc.).
- `pyproject.toml` defines tasks and dependency groups.

Note for new devs: the `task lint` commands reference `ruff`, but `ruff` does not appear in the declared dependencies in `pyproject.toml` right now. That may be drift.

## Domain Specificity Analysis

### What domain does this application target?

- The project branding implies “AI-driven health intelligence”.
- The code currently implements **authentication/session management and platform infrastructure**.

So, the “domain” implemented today is: **user identity + security for an API**.

### Core business/security concepts present

- Session-based auth with:
  - Short-lived access tokens
  - Rotating refresh tokens
  - Per-device sessions
  - Server-side session state (Redis + DB)
  - Token invalidation via `token_version`

### User interactions supported

- Register a user
- Log in
- Refresh tokens
- Log out
- Log out of all devices
- List active sessions (“My devices” style UI)
- Fetch current user (`/auth/me`)

### Primary data types / structures

- SQLAlchemy models: `User`, `UserSession`, `AccessLog`
- Pydantic schemas: `RegisterRequest`, `LoginRequest`, `TokenResponse`, etc.
- Redis JSON blobs under keys `session:{user_id}:{session_id}`

## Application Boundaries (What fits vs. conflicts)

### In scope (based on current code)

- Expanding auth features (email verification, password reset, MFA), because settings exist for those toggles.
- Adding more API modules using the same layered structure:
  - Router → Service → Repository → Models/Schemas
- Adding additional Redis-backed ephemeral state.
- Adding other models with Pydantic JSONB fields via `MutableModel(...)`.

### Out of scope / architecturally inconsistent (based on current code)

- A large front-end UI (not present; this is a backend service).
- Heavy data science/ML inference pipelines (no model serving code is present).
- A synchronous ORM or blocking DB access (code is async-first).

## “Review Carefully” areas found during stack analysis

These areas are business/security critical or tricky and should be understood before changing:

- Token/session lifecycle: `src/services/auth_service.py`, `src/auth/dependencies.py`, `src/utils/tokens.py`, `src/utils/redis.py`.
- Logging correlation ID middleware and structlog configuration: `src/main.py`, `src/utils/logging.py`.
- Alembic autogeneration and custom JSON rendering: `alembic/env.py`.

---

## Companion artifact

For downstream prompt steps, this repo also includes a machine-readable tech stack summary at `.results/1-techstack.md`.
