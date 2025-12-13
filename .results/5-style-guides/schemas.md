# Style guide: schemas

Representative files:

- `src/schemas/base.py`
- `src/schemas/auth.py`
- `src/schemas/users.py`

## Project-specific conventions

- A custom `Schema` base class provides `from_attributes` behavior and strips string values.
- Request/response models often use `class Config: from_attributes = True` (legacy style) alongside the custom base.

## Review Carefully

- `Schema.ensure_dict` is a custom adapter; ensure new schemas don’t break attribute iteration.
