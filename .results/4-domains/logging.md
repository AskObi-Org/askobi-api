# Domain: logging

## What this domain does

This repo configures structured logs and propagates a per-request correlation ID.

## Key files

- `src/utils/logging.py` (structlog + stdlib integration)
- `src/main.py` (middleware binding correlation_id)

## Observed patterns

### Correlation ID middleware

From `src/main.py`:

```python
class LogCorrelationIdMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            correlation_id = generate_correlation_id()
            structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
        await self.app(scope, receive, send)
        structlog.contextvars.unbind_contextvars("correlation_id", "method", "path")
```

### Logging is configured once at startup

From `src/main.py`:

```python
def configure_production_app() -> FastAPI:
    settings = Settings()
    configure_logging(settings=settings)
    app = get_app(settings=settings)
    set_openapi_generator(app, settings=settings)
    return app
```

## Review Carefully

- Correlation IDs are crucial for tracing security incidents and debugging production issues.
