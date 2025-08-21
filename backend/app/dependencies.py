"""
FastAPI dependencies for authentication, authorization, and database sessions.
Provides reusable dependency functions for request validation and user management.
"""
import uuid
from typing import Optional, List, Union, Annotated
from datetime import datetime

from fastapi import Depends, HTTPException, status, Request, Query, Path
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt
from pydantic import ValidationError

from .core.config import settings
from .core.logging import get_logger, app_logger
from .database import get_db_session
from .models.user import User
from .models.restaurant import Restaurant
from .models.customer import Customer
from .models.base import UserRoleChoice

logger = get_logger(__name__)

# Security
security = HTTPBearer(auto_error=False)


class AuthenticationError(HTTPException):
    """Custom authentication error."""
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(HTTPException):
    """Custom authorization error."""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class NotFoundError(HTTPException):
    """Custom not found error."""
    def __init__(self, resource: str = "Resource"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} not found"
        )


async def get_current_user_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """Extract and validate JWT token from request headers."""
    if not credentials:
        return None
    
    if not credentials.scheme == "Bearer":
        raise AuthenticationError("Invalid authentication scheme")
    
    return credentials.credentials


async def decode_jwt_token(token: str) -> dict:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.security.SECRET_KEY,
            algorithms=["HS256"]
        )
        
        # Check token expiration
        exp = payload.get("exp")
        if exp is None or datetime.utcnow().timestamp() > exp:
            raise AuthenticationError("Token has expired")
        
        # Validate required fields
        user_id = payload.get("sub")
        if user_id is None:
            raise AuthenticationError("Invalid token payload")
        
        return payload
        
    except JWTError as e:
        logger.warning(f"JWT decode error: {str(e)}")
        raise AuthenticationError("Invalid token")
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        raise AuthenticationError("Token validation failed")


async def get_current_user(
    db: AsyncSession = Depends(get_db_session),
    token: Optional[str] = Depends(get_current_user_token)
) -> Optional[User]:
    """Get current authenticated user from JWT token."""
    if not token:
        return None
    
    try:
        payload = await decode_jwt_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise AuthenticationError("Invalid token payload")
        
        # Get user from database
        result = await db.execute(
            select(User).where(
                User.id == uuid.UUID(user_id),
                User.is_active == True,
                User.is_deleted == False
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            app_logger.log_security_event(
                event_type="invalid_user_token",
                user_id=user_id,
                details={"reason": "user_not_found_or_inactive"}
            )
            raise AuthenticationError("User not found or inactive")
        
        # Update last login time (optional)
        user.last_login = datetime.utcnow()
        await db.commit()
        
        logger.debug(f"User authenticated: {user.email}")
        return user
        
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        app_logger.log_error_with_context(e, {"context": "get_current_user"})
        raise AuthenticationError("Authentication failed")


async def require_authenticated_user(
    current_user: Optional[User] = Depends(get_current_user)
) -> User:
    """Require user to be authenticated."""
    if not current_user:
        raise AuthenticationError("Authentication required")
    
    return current_user


def require_roles(allowed_roles: List[str]):
    """Dependency factory to require specific user roles."""
    async def check_user_role(
        current_user: User = Depends(require_authenticated_user)
    ) -> User:
        if current_user.role not in allowed_roles:
            app_logger.log_security_event(
                event_type="insufficient_permissions",
                user_id=str(current_user.id),
                details={
                    "required_roles": allowed_roles,
                    "user_role": current_user.role
                }
            )
            raise AuthorizationError(
                f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        
        return current_user
    
    return check_user_role


def require_super_admin():
    """Require super admin role."""
    return require_roles([UserRoleChoice.SUPER_ADMIN])


def require_restaurant_owner():
    """Require restaurant owner role or higher."""
    return require_roles([
        UserRoleChoice.SUPER_ADMIN,
        UserRoleChoice.RESTAURANT_OWNER
    ])


def require_manager():
    """Require manager role or higher."""
    return require_roles([
        UserRoleChoice.SUPER_ADMIN,
        UserRoleChoice.RESTAURANT_OWNER,
        UserRoleChoice.MANAGER
    ])


def require_server():
    """Require server role or higher."""
    return require_roles([
        UserRoleChoice.SUPER_ADMIN,
        UserRoleChoice.RESTAURANT_OWNER,
        UserRoleChoice.MANAGER,
        UserRoleChoice.SERVER
    ])


async def get_user_restaurant(
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db_session)
) -> Optional[Restaurant]:
    """Get the restaurant associated with the current user."""
    if not current_user.restaurant_id:
        return None
    
    try:
        result = await db.execute(
            select(Restaurant).where(
                Restaurant.id == current_user.restaurant_id,
                Restaurant.is_deleted == False
            )
        )
        restaurant = result.scalar_one_or_none()
        
        if not restaurant:
            logger.warning(f"Restaurant not found for user {current_user.id}")
            
        return restaurant
        
    except Exception as e:
        logger.error(f"Error getting user restaurant: {str(e)}")
        return None


async def require_restaurant_access(
    restaurant_id: uuid.UUID,
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db_session)
) -> Restaurant:
    """Require user to have access to specific restaurant."""
    try:
        # Super admins have access to all restaurants
        if current_user.role == UserRoleChoice.SUPER_ADMIN:
            result = await db.execute(
                select(Restaurant).where(
                    Restaurant.id == restaurant_id,
                    Restaurant.is_deleted == False
                )
            )
        else:
            # Other users can only access their own restaurant
            result = await db.execute(
                select(Restaurant).where(
                    Restaurant.id == restaurant_id,
                    Restaurant.id == current_user.restaurant_id,
                    Restaurant.is_deleted == False
                )
            )
        
        restaurant = result.scalar_one_or_none()
        
        if not restaurant:
            app_logger.log_security_event(
                event_type="unauthorized_restaurant_access",
                user_id=str(current_user.id),
                details={
                    "requested_restaurant_id": str(restaurant_id),
                    "user_restaurant_id": str(current_user.restaurant_id) if current_user.restaurant_id else None
                }
            )
            raise AuthorizationError("Access denied to restaurant")
        
        return restaurant
        
    except AuthorizationError:
        raise
    except Exception as e:
        logger.error(f"Error checking restaurant access: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Access validation failed"
        )


async def get_customer_by_id(
    customer_id: Annotated[uuid.UUID, Path()],
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db_session)
) -> Customer:
    """Get customer by ID with access control."""
    try:
        # Build query based on user role
        if current_user.role == UserRoleChoice.SUPER_ADMIN:
            # Super admins can access any customer
            query = select(Customer).where(
                Customer.id == customer_id,
                Customer.is_deleted == False
            )
        else:
            # Other users can only access customers from their restaurant
            query = select(Customer).where(
                Customer.id == customer_id,
                Customer.restaurant_id == current_user.restaurant_id,
                Customer.is_deleted == False
            )
        
        result = await db.execute(query)
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise NotFoundError("Customer")
        
        return customer
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Customer lookup failed"
        )


# Pagination dependencies
class PaginationParams:
    """Pagination parameters."""
    def __init__(
        self,
        page: Annotated[int, Query(ge=1, description="Page number")] = 1,
        page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20
    ):
        self.page = page
        self.page_size = min(page_size, settings.app.MAX_PAGE_SIZE)
        self.offset = (page - 1) * self.page_size


def get_pagination_params() -> PaginationParams:
    """Get pagination parameters from query string."""
    return PaginationParams()


# Common query parameters
class CommonQueryParams:
    """Common query parameters for filtering."""
    def __init__(
        self,
        search: Annotated[Optional[str], Query(description="Search term")] = None,
        sort_by: Annotated[Optional[str], Query(description="Sort by field")] = None,
        sort_order: Annotated[Optional[str], Query(description="Sort order", pattern="^(asc|desc)$")] = "asc",
        created_after: Annotated[Optional[datetime], Query(description="Filter by creation date")] = None,
        created_before: Annotated[Optional[datetime], Query(description="Filter by creation date")] = None
    ):
        self.search = search
        self.sort_by = sort_by
        self.sort_order = sort_order
        self.created_after = created_after
        self.created_before = created_before


def get_common_query_params() -> CommonQueryParams:
    """Get common query parameters."""
    return CommonQueryParams()


# Rate limiting dependency (placeholder - implement with Redis)
async def rate_limit_check(request: Request) -> None:
    """Check rate limits for the current request."""
    # TODO: Implement rate limiting with Redis
    # For now, this is a placeholder
    client_ip = request.client.host
    endpoint = request.url.path
    
    logger.debug(f"Rate limit check for {client_ip} on {endpoint}")
    
    # Rate limiting logic would go here
    # Example: check Redis for request count
    # if count > limit: raise HTTPException(429, "Rate limit exceeded")


# Request validation helpers
def validate_uuid(value: str, field_name: str = "ID") -> uuid.UUID:
    """Validate UUID format."""
    try:
        return uuid.UUID(value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name} format"
        )


def validate_language(language: str) -> str:
    """Validate language code."""
    valid_languages = ["ar", "en"]
    if language not in valid_languages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language. Must be one of: {valid_languages}"
        )
    return language


# Export commonly used dependencies
__all__ = [
    # Authentication
    "get_current_user",
    "require_authenticated_user",
    
    # Authorization
    "require_roles",
    "require_super_admin",
    "require_restaurant_owner", 
    "require_manager",
    "require_server",
    
    # Resource access
    "get_user_restaurant",
    "require_restaurant_access",
    "get_customer_by_id",
    
    # Pagination and queries
    "PaginationParams",
    "get_pagination_params",
    "CommonQueryParams",
    "get_common_query_params",
    
    # Validation
    "validate_uuid",
    "validate_language",
    "rate_limit_check",
    
    # Exceptions
    "AuthenticationError",
    "AuthorizationError", 
    "NotFoundError"
]