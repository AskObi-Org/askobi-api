# Style guide: utils

Representative files:

- `src/utils/tokens.py`
- `src/utils/redis.py`
- `src/utils/db.py`
- `src/utils/logging.py`

## Project-specific conventions

- Utility modules provide simple, reusable functions rather than deep abstraction layers.
- Auth-related helpers live in `tokens.py` and `authorization.py`.
- Redis sessions are JSON-serialized and keyed consistently.
- Logging is structured and configured centrally.

## Review Carefully

- Utilities are widely used. Small changes can have large impact.
