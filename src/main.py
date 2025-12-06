import asyncio
import contextlib
import sys
import traceback
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

import structlog
from advanced_alchemy.exceptions import AdvancedAlchemyError, NotFoundError

from fastapi import FastAPI, Request
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    FileResponse,
    PlainTextResponse,
)
from sqlalchemy.exc import IntegrityError
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.types import ASGIApp, Receive, Scope, Send

from src.utils.logging import configure as configure_logging
from src.utils.logging import generate_correlation_id, get_logger

from src.settings import Settings
from src.utils.common import excepthook_handler, handle_event_loop_exception
from src.utils.db import AsyncSession
from src.utils.openapi import get_openapi_parameters, set_openapi_generator

logger = get_logger("api")


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    sys.excepthook = excepthook_handler(logger, sys.excepthook)
    asyncio.get_running_loop().set_exception_handler(
        lambda *args, **kwargs: handle_event_loop_exception(logger, *args, **kwargs)
    )

    yield


# This middleware adds a unique correlation ID to each request for logging purposes
class LogCorrelationIdMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            correlation_id = generate_correlation_id()
            structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
        await self.app(scope, receive, send)
        structlog.contextvars.unbind_contextvars("correlation_id", "method", "path")


def patch_call(instance: FastAPI) -> None:
    class _(type(instance)):  # type: ignore[misc]
        async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
            if self.root_path:
                root_path = scope.get("root_path", "")
                if root_path and self.root_path != root_path:
                    logger.warning(
                        f"The ASGI server is using a different root path than the one "
                        f"configured in FastAPI. The configured root path is: "
                        f"{self.root_path}, the ASGI server root path is: {root_path}. "
                        f"The former will be used."
                    )
                scope["root_path"] = self.root_path
                path = scope.get("path")
                if path and not path.startswith(self.root_path):
                    scope["path"] = self.root_path + path
                raw_path: bytes | None = scope.get("raw_path")
                if raw_path and not raw_path.startswith(self.root_path.encode()):
                    scope["raw_path"] = self.root_path.encode() + raw_path
            await Starlette.__call__(self, scope, receive, send)

    instance.__class__ = _


# def with_db_rollback(
#     handler: Callable[[Request, Any], Awaitable[JSONResponse]],
# ) -> Callable[[Request, Any], Awaitable[JSONResponse]]:
#     """
#     Decorator for FastAPI exception handlers that ensures the DB session
#     is rolled back before returning a response.
#     """

#     async def wrapper(request: Request, exc: Any) -> JSONResponse:
#         session: AsyncSession | None = getattr(request.state, "db", None)
#         if session is not None:
#             await session.rollback()
#         return await handler(request, exc)

#     return wrapper


async def db_not_found_error_handler(
    request: Request, exc: NotFoundError
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "detail": str(exc)},
    )


async def db_exception_handler(
    request: Request, exc: AdvancedAlchemyError
) -> JSONResponse:
    logger.error("Database error", exc_info=exc)
    return JSONResponse(
        status_code=422,
        content={"error": "Database error", "detail": exc.detail},
    )


async def db_integrity_error_handler(
    request: Request, exc: IntegrityError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"error": "Database error", "detail": str(exc.orig)},
    )


exception_handlers: dict[
    type[Exception], Callable[[Request, Any], Awaitable[JSONResponse]]
] = {
    IntegrityError: db_integrity_error_handler,
    NotFoundError: db_not_found_error_handler,
    AdvancedAlchemyError: db_exception_handler,
}


# Add exception handlers to the FastAPI app for database-related errors
def add_exception_handlers(app: FastAPI) -> None:
    for exc_type, handler in exception_handlers.items():
        app.add_exception_handler(exc_type, handler)

    @app.exception_handler(500)
    async def exception_handler(request: Request, exc: Exception) -> Response:
        # this happens when exception is during container finalization
        # as it is rare enough, we must log it
        if type(exc) in exception_handlers:
            return await exception_handlers[type(exc)](request, exc)
        logger.error(traceback.format_exc())
        return PlainTextResponse("Internal Server Error", status_code=500)


def get_app(settings: Settings) -> FastAPI:
    app = FastAPI(
        lifespan=lifespan,
        root_path=settings.ROOT_PATH,
        root_path_in_servers=False,
        **get_openapi_parameters(settings),
    )

    @app.get("/swagger", include_in_schema=False)
    async def swagger_docs(req: Request) -> HTMLResponse:
        root_path = req.scope.get("root_path", "").rstrip("/")
        openapi_url = root_path + app.openapi_url
        return get_swagger_ui_html(
            openapi_url=openapi_url,
            title=f"{app.title} - Swagger UI",
            swagger_favicon_url="/favicon.ico",
            swagger_ui_parameters=app.swagger_ui_parameters,
        )

    @app.get("/redoc", include_in_schema=False)
    async def redoc_docs(req: Request) -> HTMLResponse:
        root_path = req.scope.get("root_path", "").rstrip("/")
        openapi_url = root_path + app.openapi_url
        return get_redoc_html(
            openapi_url=openapi_url,
            title=f"{app.title} - ReDoc",
            redoc_favicon_url="/favicon.ico",
        )

    from src.auth.router import router as auth_router

    app.include_router(auth_router)

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


def configure_production_app() -> FastAPI:
    settings = Settings()
    configure_logging(settings=settings)
    app = get_app(settings=settings)
    set_openapi_generator(app, settings=settings)
    return app


app = configure_production_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8015)
