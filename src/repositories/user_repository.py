from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from src.models.users import User, UserSession


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def get_by_phone(self, phone: str) -> Optional[User]:
        """Get user by phone number."""
        result = await self.db.execute(select(User).where(User.phone == phone))
        return result.scalars().first()

    async def create(self, user: User) -> User:
        """Create a new user."""
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user: User) -> User:
        """Update an existing user."""
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def increment_token_version(self, user: User) -> User:
        """Increment token version for logout-all functionality."""
        user.token_version += 1
        await self.db.commit()
        await self.db.refresh(user)
        return user


class SessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, session: UserSession) -> UserSession:
        """Create a new session."""
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_by_refresh_token_hash(self, token_hash: str) -> Optional[UserSession]:
        """Get session by refresh token hash."""
        result = await self.db.execute(
            select(UserSession).where(UserSession.refresh_token_hash == token_hash)
        )
        return result.scalars().first()

    async def get_by_session_id(self, session_id: str) -> Optional[UserSession]:
        """Get session by session ID."""
        result = await self.db.execute(
            select(UserSession).where(UserSession.session_id == session_id)
        )
        return result.scalars().first()

    async def list_by_user_id(self, user_id: str) -> list[UserSession]:
        """List all sessions for a user."""
        result = await self.db.execute(
            select(UserSession).where(UserSession.user_id == user_id)
        )
        return list(result.scalars().all())

    async def update(self, session: UserSession) -> UserSession:
        """Update an existing session."""
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def delete_by_session_id(self, session_id: str) -> None:
        """Delete a session by session ID."""
        await self.db.execute(
            delete(UserSession).where(UserSession.session_id == session_id)
        )
        await self.db.commit()

    async def delete_all_by_user_id(self, user_id: str) -> None:
        """Delete all sessions for a user."""
        await self.db.execute(delete(UserSession).where(UserSession.user_id == user_id))
        await self.db.commit()
