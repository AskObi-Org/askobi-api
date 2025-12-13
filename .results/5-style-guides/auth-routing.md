# Style guide: auth-routing

Representative files:

- `src/auth/router.py`

## Project-specific conventions

- Router prefix is `/auth` and tag is `Authentication`.
- Endpoints use Pydantic request/response models from `src/schemas/auth.py`.
- DB access is injected via `Depends(get_db)`.
- Protected endpoints depend on `require_active_user`.

## Review Carefully

- Endpoints like `/logout` and `/logout-all` must keep DB + Redis revocation consistent.
