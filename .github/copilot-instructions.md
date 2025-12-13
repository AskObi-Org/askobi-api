# AskObi API – Copilot Instructions & Onboarding Guide

This document is the single onboarding reference for humans and AI assistants working in this repository.

It has two goals:

1. Teach a new/junior developer how the system works (architecture + flows)
2. Make it easy to add features without breaking established patterns

## 1) What this repo is (today)

Even though the project branding describes a “medical intelligence engine”, the code currently present in this repository implements primarily:

- Authentication
- Session management (per-device)
- Token refresh/rotation
- Logging, OpenAPI docs, DB migrations, Postgres/Redis wiring

There are no symptom-analysis or AI inference endpoints implemented yet.

## 2) Tech stack (plain English)

- **FastAPI**: the web framework. You write Python async functions and FastAPI turns them into HTTP endpoints.
- **Pydantic**: validates incoming request bodies and formats outgoing responses.
- **Postgres** + **SQLAlchemy async**: persistent storage.
- **Redis**: fast in-memory store used to validate sessions quickly.
- **JWT access tokens**: short-lived “proof of login” sent on every request.
- **Refresh tokens**: long-lived tokens used to get new access tokens. This repo rotates them.
- **Alembic**: migration tool that evolves the database schema.
- **structlog**: structured logs with correlation IDs for tracing.

## 3) Repository map (where things live)

High level:

```
src/
  main.py                App entrypoint + middleware + router inclusion
  settings.py            Environment variables (Pydantic Settings)
  auth/                  Auth router + request dependencies
  services/              Business logic (session lifecycle, registration)
  repositories/          SQL queries (UserRepository, SessionRepository)
  models/                SQLAlchemy ORM models (tables)
  schemas/               Pydantic schemas (request/response models)
  utils/                 Shared helpers (JWT, redis, logging, etc.)

alembic/                 DB migration wiring + migration scripts
docs/                    Architecture + hosting notes
```

## 4) The most important flows

### 4.1 Registration

Path:

```
POST /auth/register
  -> src/auth/router.py (register endpoint)
  -> src/services/user_service.py (register_user)
  -> src/repositories/user_repository.py (create)
  -> src/models/users.py (User table)
```

What happens:

- Checks for duplicate email/phone
- Hashes password (bcrypt)
- Creates a new `User` row

### 4.2 Login + session creation

Path:

```
POST /auth/login
  -> router
  -> UserService.authenticate_user
  -> AuthService.create_session
     -> DB: insert UserSession (device metadata, refresh hash)
     -> Redis: store session:{user_id}:{session_id} with TTL
     -> Return: access_token + refresh_token
```

Why this design exists (tradeoffs):

- Access tokens are fast and don’t require a DB query by themselves.
- Redis session validation gives strong revocation semantics (logout actually works immediately).
- DB sessions allow “list devices / revoke one device” user experiences.

### 4.3 Auth on protected endpoints

The dependency `get_current_user` does:

1. Decode JWT and extract `sub` and `sid`
2. Check Redis for `session:{sub}:{sid}`
3. Fetch user from DB
4. Compare Redis `token_version` to DB `user.token_version`

If any step fails, request is rejected.

### 4.4 Refresh tokens

Refreshing performs rotation:

- Client submits refresh token
- Server hashes it and finds `UserSession` record
- If valid, it generates a new refresh token hash and stores it
- Redis TTL is refreshed
- New access token is issued

This reduces replay risk if a refresh token is stolen.

## 5) Adding a new feature (how to extend safely)

### 5.1 Decide which “layer” your change belongs in

Use this rule of thumb:

- **Router**: HTTP details only (status codes, headers, dependencies)
- **Service**: business rules and workflow
- **Repository**: database reads/writes
- **Model**: table structure and relationships
- **Schema**: request/response shapes
- **Utils**: reusable helpers that don’t belong to one domain

Analogy: routers are “controllers”, services are “use cases”, repositories are “storage adapters”.

### 5.2 Minimal scaffold for a new domain module

If you add (for example) a “Profile” feature:

- `src/profile/router.py` (endpoints)
- `src/services/profile_service.py` (flow)
- `src/repositories/profile_repository.py` (queries)
- `src/models/profile.py` (table)
- `src/schemas/profile.py` (Pydantic)
- Update `src/main.py` to `include_router(profile_router)`
- Add Alembic migration if DB changes

### 5.3 Integration rules (must follow)

These rules are derived from observed code and should not be bypassed casually.

**Auth**

- Protected endpoints must depend on `require_active_user` or otherwise apply the same checks as `get_current_user`.
- Token/session changes must keep `sub` and `sid` consistent.

**Sessions**

- Revocation must delete Redis session key AND delete DB session row.
- “Logout-all” must increment `token_version` (this invalidates all cached sessions).

**OpenAPI**

- OpenAPI generation is configured in `src/utils/openapi.py` and installed in `configure_production_app()`.
- Docs endpoints are `/swagger` and `/redoc` (default FastAPI docs are disabled).

**Database**

- Keep DB access async.
- Prefer repository methods over writing `select(...)` directly in routers.

**Logging**

- Use structured logging (`logger.info("message", key=value)`).
- Avoid printing directly in production paths.

## 6) Review Carefully (sensitive / intricate areas)

These parts are security-critical or have subtle constraints.

### Token & session lifecycle

- `src/services/auth_service.py`
- `src/auth/dependencies.py`
- `src/utils/tokens.py`
- `src/utils/redis.py`

Why it’s sensitive: mistakes can enable account takeover, session fixation, or make logout ineffective.

### Models metadata + migrations

- `src/models/utils.py` defines naming conventions and base classes
- `alembic/env.py` ties migrations to metadata and custom type rendering

Why it’s sensitive: changing metadata conventions can create dangerous migration diffs.

### Duplicate/parallel implementations

- `src/services/session_service.py` overlaps with `AuthService`

Why it’s sensitive: if both are used in different call paths, behavior can diverge. Confirm intent before changing.

## 7) How to run the project

Use `.results/6-build-instructions.md` as the canonical step-by-step guide.

Quick start (typical):

1. `poetry install`
2. `docker-compose up -d`
3. Create `src/conf/.env`
4. `poetry run task db_migrate`
5. `poetry run task api`

## 8) Notes for Copilot (how to propose changes)

When generating code for this repo:

- Prefer adding new endpoints as new `APIRouter` modules, then include them in `src/main.py`.
- Use Pydantic models from `src/schemas/` for inputs/outputs.
- Use the repository layer for DB access.
- Use the existing auth dependencies rather than hand-rolling token parsing.
- Avoid refactors unless requested; focus on minimal, consistent additions.
