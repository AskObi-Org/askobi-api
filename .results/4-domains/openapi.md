# Domain: openapi

## What this domain does

OpenAPI drives Swagger/ReDoc documentation and client generation. This repo disables the default FastAPI `/docs` and `/redoc` routes and replaces them with `/swagger` and `/redoc` custom handlers.

## Key files

- `src/utils/openapi.py`
- `src/main.py`

## Observed patterns

### OpenAPI parameters are centralized

From `src/utils/openapi.py`:

```python
def get_openapi_parameters(settings: Settings) -> OpenAPIParameters:
    current_server = settings.ROOT_PATH or "/"
    return {
        "title": "ASKOBI API",
        "summary": "ASKOBI API",
        "version": VERSION,
        "description": "Read the docs at https://docs.askobi.com/",
        "docs_url": None,
        "redoc_url": None,
        ...
    }
```

### A custom generator is installed

From `src/utils/openapi.py`:

```python
def set_openapi_generator(app: FastAPI, settings: Settings) -> None:
    def _openapi_generator() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(
            title=app.title,
            version=app.version,
            ...
        )
        app.openapi_schema = schema
        return app.openapi_schema
    app.openapi = _openapi_generator
```

## Review Carefully

- Any changes to OpenAPI generation affect docs and possibly downstream clients.
