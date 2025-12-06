from typing import Annotated, AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jwt import PyJWTError
from datetime import datetime, timezone

from src.settings import Settings
from src.utils.db import create_async_engine, create_async_sessionmaker
from src.utils import tokens, redis
from src.models.users import User

settings = Settings()
engine = create_async_engine(settings)
async_session_maker = create_async_sessionmaker(engine)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = tokens.decode_token(token)
        user_id: str = payload.get("sub")
        session_id: str = payload.get("sid")
        if user_id is None or session_id is None:
            raise credentials_exception
    except PyJWTError:
        raise credentials_exception

    # Check Redis for session
    session_data = await redis.get_session(user_id, session_id)
    if not session_data:
        raise credentials_exception

    # Fetch User
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception

    # Validate token_version
    # We assume session_data contains 'token_version' stored at creation time
    session_token_version = session_data.get("token_version")
    if session_token_version is not None and session_token_version != user.token_version:
        raise credentials_exception

    return user

async def require_active_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_fresh_login(max_age_seconds: int = 300):
    async def dependency(token: Annotated[str, Depends(oauth2_scheme)]):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Fresh login required",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = tokens.decode_token(token)
            auth_time = payload.get("auth_time")
            if not auth_time:
                 raise credentials_exception
            
            now = datetime.now(timezone.utc).timestamp()
            if now - auth_time > max_age_seconds:
                raise credentials_exception
            
        except PyJWTError:
             raise credentials_exception
    return dependency
