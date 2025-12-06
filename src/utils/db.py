from collections.abc import AsyncIterator
from typing import Literal

from sqlalchemy import Engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.ext.asyncio import (
    create_async_engine as _create_async_engine,
)

from src.settings import Settings


# Factory to create an AsyncEngine with common settings for the application
# The AsyncEngine is the core interface to the database in SQLAlchemy's async support
def create_async_engine_core(
    *,
    dsn: str,
    application_name: str | None = None,
    pool_size: int | None = None,
    pool_recycle: int | None = None,
    debug: bool = False,
) -> AsyncEngine:
    return _create_async_engine(
        dsn,
        echo=debug,
        connect_args={"server_settings": {"application_name": application_name}} if application_name else {},
        pool_size=pool_size,
        pool_recycle=pool_recycle,
    )


type AsyncSessionMaker = async_sessionmaker[AsyncSession]

type ProcessName = Literal["app", "worker", "test", "migrations"]

# Factory to create an AsyncEngine with settings derived from the application Settings
# This function allows specifying the process name to differentiate connections from different parts of the application
def create_async_engine(settings: Settings, process_name: ProcessName = "app", dsn: str | None = None) -> AsyncEngine:
    return create_async_engine_core(
        dsn=dsn or str(settings.postgres_dsn),
        application_name=f"{settings.ENV.value}.{process_name}",
        debug=settings.DEBUG,
        pool_size=settings.DB_POOL_SIZE,
        pool_recycle=settings.DB_POOL_RECYCLE_SECONDS,
    )

# Factory to create an AsyncSessionMaker bound to a given AsyncEngine
# The AsyncSessionMaker is used to create AsyncSession instances for database interactions
def create_async_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


# Async context manager to provide a database session
# This function yields an AsyncSession and ensures proper commit or rollback based on whether an exception occurred
from collections.abc import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

# Async context manager to provide a database session
# Ensures rollback on exception, commit otherwise, and always closes
async def get_db_session(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with sessionmaker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


__all__ = [
    "AsyncSession",
    "AsyncEngine",
    "Engine",
    "AsyncSessionMaker",
    "create_async_engine",
    "create_async_sessionmaker",
]