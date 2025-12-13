# Style guide: app-entrypoint

Representative files:

- `src/main.py`

## Project-specific conventions

- The FastAPI app is created via a factory (`get_app(settings)`), then a top-level `app` is assigned.
- The project disables default docs URLs (`docs_url=None`, `redoc_url=None`) and mounts custom `/swagger` and `/redoc` handlers.
- Middleware includes a correlation-id binding via `structlog.contextvars`.
- Database-related exception handlers are registered in one place via `add_exception_handlers`.

## “If you add new global behavior” checklist

- Prefer adding middleware in `get_app`.
- Prefer keeping error handling in `add_exception_handlers`.
