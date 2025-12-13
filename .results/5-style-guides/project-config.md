# Style guide: project-config

Representative files:

- `pyproject.toml`
- `docker-compose.yml`
- `gunicorn.conf.py`
- `DEVELOPMENT.md`

## Project-specific conventions

- Poetry is used with PEP 621 `[project]` metadata and `[tool.poetry]` package include settings.
- Taskipy tasks are the primary DX entrypoint (`task api`, `task db_migrate`, etc.).
- Docker Compose is explicitly “development only” and uses non-default host ports (Postgres 5458, Redis 6383).
