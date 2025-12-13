# 1-techstack (machine-readable summary)

## Core Technology Analysis

- Languages: Python (>=3.13)
- Primary framework: FastAPI (ASGI), built on Starlette
- Secondary frameworks/libraries:
  - Pydantic v2 + pydantic-settings
  - SQLAlchemy async + asyncpg
  - advanced-alchemy (model base + exception types)
  - Redis asyncio client (`redis.asyncio`) for session cache
  - Alembic for DB migrations
  - structlog + stdlib logging
  - gunicorn + uvicorn workers for production
  - sentry-sdk dependency present
- State management: not applicable (backend API); server state in Postgres + Redis
- Deployment/dev: Docker Compose for Postgres+Redis; Poetry + Taskipy tasks

## Domain Specificity Analysis

- Domain: backend identity/authentication and session management for AskObi API
- Core concepts: JWT access tokens, rotating refresh tokens, per-device sessions, token invalidation via token_version
- User interactions: register/login/logout/refresh/list sessions/me
- Primary data types:
  - SQLAlchemy models: User, UserSession, AccessLog
  - Pydantic schemas: RegisterRequest, LoginRequest, TokenResponse, SessionResponse, UserResponse
  - Redis JSON session blobs

## Application Boundaries

- In scope: add new API modules following Router→Service→Repository; expand auth flows; add new models/schemas; enrich logging/metrics
- Architecturally inconsistent: synchronous DB calls; front-end UI; ML inference/AI pipelines (not present yet)
