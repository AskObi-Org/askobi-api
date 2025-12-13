# File Categorization (AskObi API)

This document answers the prompt “categorize files” and teaches a new developer how to mentally group the repo.

## What was discovered

The repo is intentionally small and uses a layered backend structure:

- **API entrypoint / app wiring**: creates the FastAPI app, middleware, routers, exception handlers.
- **Configuration**: environment variables via Pydantic settings.
- **Auth module**: request dependencies + router.
- **Services**: business logic (session lifecycle, user registration).
- **Repositories**: DB access (CRUD / queries).
- **Models**: SQLAlchemy ORM definitions.
- **Schemas**: Pydantic request/response models.
- **Utilities**: cross-cutting helpers (JWT, Redis, logging, DB engine setup, etc.).
- **Migrations**: Alembic wiring and migration scripts.
- **Infra docs**: design and hosting docs.

## Why it matters

When a junior dev adds a feature, knowing “where code belongs” prevents:

- Security-critical logic being buried in routers
- Database queries scattered in services and routers
- Duplicate token/session logic
- Inconsistent OpenAPI behavior

## Output

The machine-readable categorization is stored at `.results/2-file-categorization.json`.

If you’re browsing the repo manually, start here:

- App entrypoint: `src/main.py`
- Settings: `src/settings.py`
- Auth endpoints: `src/auth/router.py`
- Auth checks: `src/auth/dependencies.py`
- Session lifecycle: `src/services/auth_service.py`
