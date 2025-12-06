from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from typing import Any, Optional, Tuple
import jwt
from src.settings import Settings

settings = Settings()

def create_access_token(user_id: int | str, session_id: str, auth_time: int) -> str:
    """
    Create a short-lived access token with session ID and auth time.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.AUTH_JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": str(user_id),
        "sid": session_id,
        "auth_time": auth_time,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    }
    encoded_jwt = jwt.encode(to_encode, settings.AUTH_JWT_SECRET_KEY, algorithm=settings.AUTH_JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(user_id: int | str, session_id: str) -> Tuple[str, str]:
    """
    Create a long-lived refresh token.
    Returns (raw_token, hashed_token).
    """
    # Generate a random token
    raw_token = secrets.token_urlsafe(64)
    
    # Hash it
    hashed_token = hash_refresh_token(raw_token)
    
    return raw_token, hashed_token

def hash_refresh_token(token: str) -> str:
    """
    Hash a refresh token using SHA-256 and the configured salt.
    """
    salted_token = f"{token}{settings.AUTH_PASSWORD_SALT}"
    return hashlib.sha256(salted_token.encode()).hexdigest()

def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.
    Raises jwt.PyJWTError on failure.
    """
    try:
        payload = jwt.decode(token, settings.AUTH_JWT_SECRET_KEY, algorithms=[settings.AUTH_JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError as e:
        raise e
