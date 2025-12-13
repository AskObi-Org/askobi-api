# Domain: configuration

## What this domain does

All runtime configuration is centralized in `Settings`.

New developers should think of `Settings` as the single source of truth for:

- DB connection details
- Redis connection details
- Auth secrets and lifetimes
- Environment (development/testing/production)

## Key files

- `src/settings.py`

## Observed patterns

### Settings load from `src/conf/.env`

From `src/settings.py`:

```python
model_config = SettingsConfigDict(env_file="src/conf/.env", extra="ignore")
```

### Redis URL is derived from fields

From `src/settings.py`:

```python
@property
def redis_url(self) -> str:
    if self.REDIS_URL:
        return self.REDIS_URL
    password = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
    return f"redis://{password}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
```

### Testing database name changes automatically

From `src/settings.py`:

```python
@field_validator("DB_DATABASE", mode="before")
@classmethod
def validate_db_database(cls, v: str, info: ValidationInfo) -> str:
    env = info.data.get("ENV", Environment.DEVELOPMENT)
    if env == Environment.TESTING:
        return "askobi_test_db"
    return v
```

## Review Carefully

- Secrets (JWT key, password salt) are required; missing them will fail app startup.
