# Domain: routing

## What this domain does

Routing is how HTTP requests get mapped to Python functions (“endpoints”). In FastAPI, routers are grouped into `APIRouter` modules and then included into the main app.

## Key files

- `src/main.py` (app creation + router inclusion)
- `src/auth/router.py` (auth endpoints)

## Observed patterns

### App creation is centralized

The FastAPI app is created in `get_app(settings)` and wired in `configure_production_app()`.

Exact code (from `src/main.py`):

```python
def get_app(settings: Settings) -> FastAPI:
    app = FastAPI(
        lifespan=lifespan,
        root_path=settings.ROOT_PATH,
        root_path_in_servers=False,
        **get_openapi_parameters(settings),
    )

    from src.auth.router import router as auth_router

    app.include_router(auth_router)

    @app.get("/health", include_in_schema=False)
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.add_middleware(LogCorrelationIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
    )
    patch_call(app)
    add_exception_handlers(app)
    return app
```

### Routers use FastAPI dependency injection

The auth router pulls DB sessions and current user via dependencies.

Exact code (from `src/auth/router.py`):

```python
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    user_data: RegisterRequest, db: Annotated[AsyncSession, Depends(get_db)]
):
    """Register a new user account."""
    user_service = UserService(db)
    new_user = await user_service.register_user(user_data)
    return new_user
```

## How to add a new endpoint (in this repo’s style)

1. Decide which module it belongs in (auth vs new module).
2. Put the HTTP handler in a router file (e.g., `src/auth/router.py`).
3. Keep the handler thin: parse input → call a service → return a schema.
4. Use dependencies for cross-cutting concerns (DB session, current user).

## Review Carefully

- Endpoints that change sessions (logout, logout-all) are security-sensitive; changes must keep Redis + DB revocation consistent.
