# Style guide: models

Representative files:

- `src/models/utils.py`
- `src/models/users.py`
- `src/models/audit.py`

## Project-specific conventions

- Models inherit from custom base classes (`RecordModel`, `IDModel`, etc.).
- IDs are string IDs generated via `unique_id()`.
- The repo uses JSONB columns mapped to Pydantic schemas via `MutableModel(...)`.
- Metadata naming conventions are centralized in `my_metadata`.

## Review Carefully

- `src/models/utils.py` defines metadata naming conventions and a registry; changes can affect migrations.
- `src/models/users.py` contains the `preferences` JSONB mapping; changes can break user preference storage.
