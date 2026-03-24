"""
User service.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.base import BaseService


class UserService(BaseService[User]):
    """User service."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, User)
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def create_user(self, data: UserCreate) -> User:
        """Create new user."""
        password_hash = get_password_hash(data.password)
        
        user_data = data.model_dump(exclude={"password"})
        user_data["password_hash"] = password_hash
        
        return await self.create(**user_data)
    
    async def update_user(self, user_id: int, data: UserUpdate) -> Optional[User]:
        """Update user."""
        update_data = data.model_dump(exclude_unset=True)
        return await self.update(user_id, **update_data)
    
    async def update_last_login(self, user_id: int) -> None:
        """Update last login time."""
        await self.update(
            user_id,
            last_login=datetime.now(timezone.utc),
        )
