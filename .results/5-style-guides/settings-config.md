# Style guide: settings-config

Representative files:

- `src/settings.py`

## Project-specific conventions

- Settings use Pydantic Settings v2 (`BaseSettings`) with `env_file="src/conf/.env"`.
- Some env variables use `validation_alias` to keep stable env names.
- Derived properties (`postgres_dsn`, `redis_url`) are implemented as `@property`.
- `Environment` is a `StrEnum`.

## Review Carefully

- Auth secrets are required fields; ensure new settings don’t accidentally become required unless necessary.
