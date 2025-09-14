"""
User Repository Implementation
Handles data access operations for users and authentication.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from .base_repository import BaseRepository
from ....models.user import User


class UserRepository(BaseRepository[User]):
    """Repository for user data operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    def get_model(self) -> type[User]:
        return User

    async def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email address."""
        stmt = select(User).where(
            and_(
                User.email == email,
                User.is_deleted == False
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_username(self, username: str) -> Optional[User]:
        """Find user by username."""
        stmt = select(User).where(
            and_(
                User.username == username,
                User.is_deleted == False
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_users(
        self,
        restaurant_id: Optional[UUID] = None
    ) -> List[User]:
        """Get all active users."""
        filters = {
            'is_active': True,
            'is_deleted': False
        }

        if restaurant_id:
            filters['restaurant_id'] = restaurant_id

        return await self.get_all(filters=filters)

    async def get_users_by_role(
        self,
        role: str,
        restaurant_id: Optional[UUID] = None
    ) -> List[User]:
        """Get users by role."""
        filters = {
            'role': role,
            'is_deleted': False
        }

        if restaurant_id:
            filters['restaurant_id'] = restaurant_id

        return await self.get_all(filters=filters)

    async def get_users_by_restaurant(
        self,
        restaurant_id: UUID,
        include_inactive: bool = False
    ) -> List[User]:
        """Get users by restaurant."""
        filters = {
            'restaurant_id': restaurant_id,
            'is_deleted': False
        }

        if not include_inactive:
            filters['is_active'] = True

        return await self.get_all(filters=filters)

    async def verify_credentials(
        self,
        email: str,
        password_hash: str
    ) -> Optional[User]:
        """Verify user credentials."""
        user = await self.find_by_email(email)

        if user and user.is_active and user.password_hash == password_hash:
            return user

        return None

    async def update_last_login(self, user_id: UUID) -> Optional[User]:
        """Update user's last login timestamp."""
        from datetime import datetime

        return await self.update(
            user_id,
            last_login_at=datetime.utcnow()
        )

    async def deactivate_user(self, user_id: UUID) -> Optional[User]:
        """Deactivate a user account."""
        return await self.update(
            user_id,
            is_active=False,
            updated_at=datetime.utcnow()
        )

    async def activate_user(self, user_id: UUID) -> Optional[User]:
        """Activate a user account."""
        from datetime import datetime

        return await self.update(
            user_id,
            is_active=True,
            updated_at=datetime.utcnow()
        )

    async def update_permissions(
        self,
        user_id: UUID,
        permissions: Dict[str, bool]
    ) -> Optional[User]:
        """Update user permissions."""
        from datetime import datetime

        update_data = permissions.copy()
        update_data['updated_at'] = datetime.utcnow()

        return await self.update(user_id, **update_data)

    async def search_users(
        self,
        search_term: str,
        restaurant_id: Optional[UUID] = None
    ) -> List[User]:
        """Search users by name or email."""
        from sqlalchemy import or_

        stmt = select(User).where(
            and_(
                User.is_deleted == False,
                or_(
                    User.first_name.ilike(f"%{search_term}%"),
                    User.last_name.ilike(f"%{search_term}%"),
                    User.email.ilike(f"%{search_term}%"),
                    User.username.ilike(f"%{search_term}%")
                )
            )
        )

        if restaurant_id:
            stmt = stmt.where(User.restaurant_id == restaurant_id)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_superusers(self) -> List[User]:
        """Get all superuser accounts."""
        filters = {
            'is_superuser': True,
            'is_deleted': False
        }

        return await self.get_all(filters=filters)

    async def check_email_exists(self, email: str, exclude_user_id: Optional[UUID] = None) -> bool:
        """Check if email already exists."""
        stmt = select(User).where(
            and_(
                User.email == email,
                User.is_deleted == False
            )
        )

        if exclude_user_id:
            stmt = stmt.where(User.id != exclude_user_id)

        result = await self.session.execute(stmt)
        return result.first() is not None

    async def check_username_exists(self, username: str, exclude_user_id: Optional[UUID] = None) -> bool:
        """Check if username already exists."""
        stmt = select(User).where(
            and_(
                User.username == username,
                User.is_deleted == False
            )
        )

        if exclude_user_id:
            stmt = stmt.where(User.id != exclude_user_id)

        result = await self.session.execute(stmt)
        return result.first() is not None