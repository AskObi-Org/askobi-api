from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from fastapi import HTTPException, status

from src.models.users import User, UserSession
from src.utils import tokens, redis
from src.settings import Settings
from src.utils.common import unique_id

settings = Settings()

async def create_session(
    db: AsyncSession,
    user: User,
    device_name: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> dict:
    """
    Create a new session for the user.
    Returns a dict with access_token and refresh_token.
    """
    session_id = unique_id()
    
    # Create refresh token
    raw_refresh_token, hashed_refresh_token = tokens.create_refresh_token(user.id, session_id)
    
    # Create access token
    auth_time = int(datetime.now(timezone.utc).timestamp())
    access_token = tokens.create_access_token(user.id, session_id, auth_time)
    
    # Store in DB
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.AUTH_JWT_REFRESH_TOKEN_EXPIRE_MINUTES)
    
    db_session = UserSession(
        user_id=user.id,
        session_id=session_id,
        refresh_token_hash=hashed_refresh_token,
        device_name=device_name,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=expires_at,
        is_active=True
    )
    db.add(db_session)
    await db.commit()
    
    # Store in Redis
    session_data = {
        "user_id": user.id,
        "token_version": user.token_version,
        "device_name": device_name,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "created_at": auth_time
    }
    # TTL in seconds
    ttl = settings.AUTH_JWT_REFRESH_TOKEN_EXPIRE_MINUTES * 60
    await redis.store_session(user.id, session_id, session_data, ttl)
    
    return {
        "access_token": access_token,
        "refresh_token": raw_refresh_token,
        "token_type": "bearer"
    }

async def refresh_tokens(db: AsyncSession, raw_refresh_token: str) -> dict:
    """
    Refresh access and refresh tokens.
    """
    hashed_token = tokens.hash_refresh_token(raw_refresh_token)
    
    result = await db.execute(select(UserSession).where(UserSession.refresh_token_hash == hashed_token))
    user_session = result.scalars().first()
    
    if not user_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        
    if not user_session.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session is inactive")
        
    if user_session.expires_at and user_session.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")
        
    result = await db.execute(select(User).where(User.id == user_session.user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        
    # Check Redis
    redis_session = await redis.get_session(user.id, user_session.session_id)
    if not redis_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or revoked")
        
    if redis_session.get("token_version") != user.token_version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token version mismatch")

    # Rotate refresh token
    new_raw_refresh_token, new_hashed_token = tokens.create_refresh_token(user.id, user_session.session_id)
    
    # Update DB
    user_session.refresh_token_hash = new_hashed_token
    user_session.expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.AUTH_JWT_REFRESH_TOKEN_EXPIRE_MINUTES)
    await db.commit()
    
    # Update Redis TTL
    ttl = settings.AUTH_JWT_REFRESH_TOKEN_EXPIRE_MINUTES * 60
    await redis.store_session(user.id, user_session.session_id, redis_session, ttl)
    
    # Create new access token
    auth_time = int(datetime.now(timezone.utc).timestamp())
    access_token = tokens.create_access_token(user.id, user_session.session_id, auth_time)
    
    return {
        "access_token": access_token,
        "refresh_token": new_raw_refresh_token,
        "token_type": "bearer"
    }

async def revoke_session(db: AsyncSession, user_id: str, session_id: str) -> None:
    """
    Revoke a specific session.
    """
    await redis.delete_session(user_id, session_id)
    await db.execute(delete(UserSession).where(UserSession.session_id == session_id))
    await db.commit()

async def revoke_all_sessions(db: AsyncSession, user: User) -> None:
    """
    Revoke all sessions for a user.
    """
    await redis.delete_all_sessions_for_user(user.id)
    await db.execute(delete(UserSession).where(UserSession.user_id == user.id))
    
    user.token_version += 1
    await db.commit()

async def list_sessions(db: AsyncSession, user_id: str) -> list[UserSession]:
    """
    List all active sessions for a user.
    """
    result = await db.execute(select(UserSession).where(UserSession.user_id == user_id))
    return result.scalars().all()
