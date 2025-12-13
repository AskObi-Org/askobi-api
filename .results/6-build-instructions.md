# Build / Run / Contribute Instructions (AskObi API)

This file consolidates what a new developer needs to build and run the API locally, based on what is actually present in the repo.

## 1) Setup (local dev)

### Requirements

- Python 3.13+
- Poetry
- Docker + Docker Compose (recommended for Postgres + Redis)

### Install dependencies

```powershell
poetry install
```

### Start infrastructure

```powershell
docker-compose up -d
```

This maps:

- Postgres: host `localhost:5458` → container `5432`
- Redis: host `localhost:6383` → container `6379`

### Configure environment

Create `src/conf/.env` with at least:

```env
AUTH_JWT_SECRET_KEY=your-super-secret-key
AUTH_PASSWORD_SALT=your-password-salt

DB_HOST=localhost
DB_PORT=5458
DB_USER=askobi_user
DB_PASSWORD=askobi_password
DB_DATABASE=askobi_db

REDIS_HOST=127.0.0.1
REDIS_PORT=6383
REDIS_DB=0
```

### Run migrations

```powershell
poetry run task db_migrate
```

### Run the API

```powershell
poetry run task api
```

By default the API runs on port `8015`.

## 2) Useful dev URLs

- Health: `http://127.0.0.1:8015/health`
- Swagger: `http://127.0.0.1:8015/swagger`
- ReDoc: `http://127.0.0.1:8015/redoc`

## 3) Production-ish run

Gunicorn is configured in `gunicorn.conf.py` and the task exists:

```powershell
poetry run task production
```

## 4) How to add a feature (scaffold guide)

When adding a new feature, follow the repository’s layering:

1. Add/extend a router module (new endpoints)
2. Add a service method (business flow)
3. Add repository methods (SQL queries)
4. Add/extend models + schemas
5. Add migrations (if DB changes)

## 5) Integration rules (must-follow)

These are “do not break” constraints observed in the code:

- Protected endpoints must use `require_active_user` (or otherwise call `get_current_user`) so Redis + token_version checks apply.
- Revoking sessions must delete both Redis session key and DB row.
- OpenAPI schema generation is centralized via `src/utils/openapi.py` and installed in `configure_production_app()`.

## 6) Notes on repo drift

The repo includes references that may be out of date:

- `README.md` references an `app/` folder and requirements.txt workflow, but the code uses `src/` and Poetry.
- Taskipy lint tasks reference `ruff`, but `ruff` is not listed in `pyproject.toml` dependencies.
