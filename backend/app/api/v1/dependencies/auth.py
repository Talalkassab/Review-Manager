"""
Authentication and authorization dependencies.
Provides user authentication and permission checking.
"""
from typing import Optional, List, Callable
from functools import wraps

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from ....models.user import User
from ....core.exceptions import UnauthorizedAccess, InvalidCredentials
from .database import get_db_session

# JWT token extraction
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: AsyncSession = Depends(get_db_session)
) -> Optional[User]:
    """
    Get current user from JWT token.
    Returns None if no valid token is provided.
    """
    if not credentials:
        return None

    try:
        from ....core.jwt_utils import JWTUtils
        from sqlalchemy import select

        # Verify token and extract user ID
        user_id = JWTUtils.get_user_id_from_token(credentials.credentials)
        if not user_id:
            return None

        # Fetch user from database
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        # Verify user is active
        if user and user.is_active:
            return user

        return None

    except Exception:
        return None


async def current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user or raise 401.
    Requires valid authentication.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )

    return current_user


async def get_optional_current_user(
    current_user: Optional[User] = Depends(get_current_user)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.
    Does not require authentication.
    """
    return current_user


def require_permissions(*required_permissions: str) -> Callable:
    """
    Dependency factory for requiring specific permissions.

    Usage:
        @router.get("/admin", dependencies=[Depends(require_permissions("admin"))])
    """
    def permission_dependency(
        current_user: User = Depends(current_active_user)
    ) -> User:
        # Check if user has required permissions
        for permission in required_permissions:
            if not hasattr(current_user, f"can_{permission}") or not getattr(current_user, f"can_{permission}"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission required: {permission}"
                )

        return current_user

    return permission_dependency


def require_superuser() -> Callable:
    """
    Dependency for requiring superuser access.

    Usage:
        @router.get("/super-admin", dependencies=[Depends(require_superuser())])
    """
    def superuser_dependency(
        current_user: User = Depends(current_active_user)
    ) -> User:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Superuser access required"
            )

        return current_user

    return superuser_dependency


def require_restaurant_access(restaurant_id_param: str = "restaurant_id") -> Callable:
    """
    Dependency factory for requiring access to specific restaurant.

    Args:
        restaurant_id_param: Name of the path parameter containing restaurant ID

    Usage:
        @router.get("/restaurant/{restaurant_id}/data")
        async def get_data(
            restaurant_id: UUID,
            user: User = Depends(require_restaurant_access("restaurant_id"))
        ):
    """
    def restaurant_access_dependency(
        current_user: User = Depends(current_active_user)
    ) -> User:
        # This would need to be enhanced with actual restaurant ID checking
        # For now, just ensure user is authenticated
        return current_user

    return restaurant_access_dependency


def require_role(*required_roles: str) -> Callable:
    """
    Dependency factory for requiring specific user roles.

    Usage:
        @router.get("/manager", dependencies=[Depends(require_role("manager", "admin"))])
    """
    def role_dependency(
        current_user: User = Depends(current_active_user)
    ) -> User:
        user_role = getattr(current_user, 'role', None)

        if user_role not in required_roles and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {' or '.join(required_roles)}"
            )

        return current_user

    return role_dependency