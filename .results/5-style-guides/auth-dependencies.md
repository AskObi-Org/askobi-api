# Style guide: auth-dependencies

Representative files:

- `src/auth/dependencies.py`

## Project-specific conventions

- Auth uses `OAuth2PasswordBearer(tokenUrl="auth/login")`.
- `get_current_user` does a three-step check:
  1) decode JWT
  2) check Redis session exists
  3) fetch user from DB and validate `token_version`

## Review Carefully

- This file is security-critical; changes can lock users out or weaken auth.
