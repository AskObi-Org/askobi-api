# Style guide: db-migrations

Representative files:

- `alembic/env.py`
- `alembic/versions/*.py`

## Project-specific conventions

- `target_metadata` is `Model.metadata`.
- Autogeneration has custom type rendering for Pydantic JSON columns.
