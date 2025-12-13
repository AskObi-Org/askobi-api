# Style guide: services

Representative files:

- `src/services/auth_service.py`
- `src/services/user_service.py`

## Project-specific conventions

- Services are classes instantiated with an `AsyncSession`.
- Services create repositories in `__init__`.
- Services raise `fastapi.HTTPException` for API-facing validation errors.
- `AuthService` coordinates both DB session rows and Redis session cache.

## Review Carefully

- `src/services/session_service.py` is a parallel, function-style implementation. Confirm intent before adding new code there.
