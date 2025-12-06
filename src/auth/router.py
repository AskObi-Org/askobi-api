from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_db, get_current_user, require_active_user
from src.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    RefreshRequest,
    SessionResponse,
    UserResponse,
)
from src.models.users import User
from src.services.user_service import UserService
from src.services.auth_service import AuthService
from src.utils import tokens

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


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Authenticate user and create a new session."""
    user_service = UserService(db)
    auth_service = AuthService(db)

    user = await user_service.authenticate_user(credentials.email, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive"
        )

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    device_name = request.headers.get("x-device-name", "Unknown Device")

    token_data = await auth_service.create_session(
        user=user, device_name=device_name, ip_address=ip_address, user_agent=user_agent
    )

    return token_data


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    refresh_data: RefreshRequest, db: Annotated[AsyncSession, Depends(get_db)]
):
    """Refresh access and refresh tokens."""
    auth_service = AuthService(db)
    token_data = await auth_service.refresh_tokens(refresh_data.refresh_token)
    return token_data


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: Annotated[User, Depends(require_active_user)],
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Logout from current session."""
    auth_service = AuthService(db)

    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    token = auth_header.replace("Bearer ", "")
    payload = tokens.decode_token(token)
    session_id = payload.get("sid")

    if session_id:
        await auth_service.revoke_session(current_user.id, session_id)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    current_user: Annotated[User, Depends(require_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Logout from all sessions (panic button)."""
    auth_service = AuthService(db)
    await auth_service.revoke_all_sessions(current_user)


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    current_user: Annotated[User, Depends(require_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all active sessions for the current user."""
    auth_service = AuthService(db)
    sessions = await auth_service.list_sessions(current_user.id)
    return sessions


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session(
    session_id: str,
    current_user: Annotated[User, Depends(require_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Revoke a specific session."""
    auth_service = AuthService(db)
    await auth_service.revoke_session(current_user.id, session_id)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(require_active_user)],
):
    """Get current authenticated user information."""
    return current_user
