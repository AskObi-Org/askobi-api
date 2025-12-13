# Domain: data-layer

## What this domain does

This domain defines how the API talks to Postgres:

- Create async DB engine
- Create async sessions
- Define models
- Encapsulate SQL in repositories

## Key files

- `src/utils/db.py` (engine + sessionmaker)
- `src/repositories/user_repository.py` (queries)
- `src/models/*.py` (tables)

## Observed patterns

### Engine is created from Settings

From `src/utils/db.py`:

```python
def create_async_engine(
    settings: Settings, process_name: ProcessName = "app", dsn: str | None = None
) -> AsyncEngine:
    return create_async_engine_core(
        dsn=dsn or str(settings.postgres_dsn),
        application_name=f"{settings.ENV.value}.{process_name}",
        debug=settings.DEBUG,
        pool_size=settings.DB_POOL_SIZE,
        pool_recycle=settings.DB_POOL_RECYCLE_SECONDS,
    )
```

### Repositories encapsulate queries

From `src/repositories/user_repository.py`:

```python
result = await self.db.execute(select(User).where(User.email == email))
return result.scalars().first()
```

## Review Carefully

- DB session lifecycle differs across the repo: repositories commit in their methods; `src/utils/db.py` also includes a context manager `get_db_session` that commits/rolls back. Ensure you understand which is used in request paths before changing transaction behavior.
