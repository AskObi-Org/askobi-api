# Domain: migrations

## What this domain does

Alembic manages schema evolution for Postgres.

## Key files

- `alembic/env.py` (migration configuration)
- `alembic/versions/*.py` (migration scripts)
- `src/models/utils.py` (metadata / naming conventions)

## Observed patterns

### Migrations target the shared metadata

From `alembic/env.py`:

```python
target_metadata = Model.metadata
config.set_main_option("sqlalchemy.url", settings.postgres_dsn.replace("%", "%%"))
```

### Custom rendering for Pydantic JSON columns

From `alembic/env.py`:

```python
def render_item(type_: str, obj: Any, autogen_context: Any) -> str | Literal[False]:
    if isinstance(obj, PydanticJSON):
        return "postgresql.JSONB(astext_type=sa.Text())"
    return False
```

## Review Carefully

- Changing naming conventions or metadata behavior can create noisy, risky migrations.
