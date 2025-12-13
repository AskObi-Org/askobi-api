# Architectural Domains (AskObi API)

This document answers the prompt “identify architecture”.

## What was discovered

This repo uses a **layered backend architecture** with clear responsibilities:

```
HTTP Router (FastAPI)
  -> Service (business logic)
    -> Repository (DB reads/writes)
      -> SQLAlchemy Models (tables)

Cross-cutting concerns:
  Settings (Pydantic)
  Redis session cache
  Token utilities (JWT + refresh token hashing)
  Logging + correlation IDs
  OpenAPI generator
  Alembic migrations
```

## Why it matters

When a new feature is added, the easiest way to keep quality high is to:

- Put HTTP concerns in routers
- Put rules/flows in services
- Put SQL queries in repositories
- Keep auth/session checks centralized

This keeps the code testable, readable, and secure.

## Output

The machine-readable domain definition is stored at `.results/3-architectural-domains.json`.

Domain deep dives are in `.results/4-domains/`.
