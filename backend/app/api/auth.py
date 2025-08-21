"""
Authentication API routes using FastAPI-Users.
Handles user registration, login, password management, and JWT tokens.
"""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.logging import get_logger
from ..database import get_db_session
from ..models import User
from ..schemas import (
    UserCreate, UserUpdate, UserResponse, UserLogin, UserLoginResponse,
    PasswordChangeRequest, PasswordResetRequest, ErrorResponse
)

logger = get_logger(__name__)
router = APIRouter()

# FastAPI-Users setup
class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    """User management class with custom logic."""
    
    reset_password_token_secret = settings.security.SECRET_KEY
    verification_token_secret = settings.security.SECRET_KEY
    
    async def on_after_register(self, user: User, request: Optional[Request] = None):
        """Called after user registration."""
        logger.info(f"User registered: {user.email}")
    
    async def on_after_login(
        self,
        user: User,
        request: Optional[Request] = None,
        response = None,
    ):
        """Called after successful login."""
        user.record_login()
        logger.info(f"User logged in: {user.email}")
    
    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Called after password reset request."""
        logger.info(f"Password reset requested for: {user.email}")
    
    async def on_after_reset_password(self, user: User, request: Optional[Request] = None):
        """Called after password reset."""
        logger.info(f"Password reset completed for: {user.email}")


async def get_user_db(session: AsyncSession = Depends(get_db_session)):
    """Get user database dependency."""
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    """Get user manager dependency."""
    yield UserManager(user_db)


# JWT Authentication setup
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

def get_jwt_strategy() -> JWTStrategy:
    """Get JWT strategy."""
    return JWTStrategy(
        secret=settings.security.SECRET_KEY,
        lifetime_seconds=settings.security.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

# Get current user dependencies
current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)


# Custom authentication routes
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    user_manager: UserManager = Depends(get_user_manager)
):
    """Register a new user."""
    try:
        # Create user with Pydantic model
        user = await user_manager.create(user_data)
        
        # Convert to response format
        return UserResponse.model_validate(user)
        
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed"
        )


@router.post("/login", response_model=UserLoginResponse)
async def login(
    credentials: UserLogin,
    user_manager: UserManager = Depends(get_user_manager)
):
    """Authenticate user and return JWT tokens."""
    try:
        # Get user by email
        user = await user_manager.get_by_email(credentials.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Verify password
        if not user_manager.password_helper.verify_and_update(credentials.password, user.hashed_password)[0]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive"
            )
        
        # Generate JWT token
        strategy = get_jwt_strategy()
        token = await strategy.write_token(user)
        
        # Record login
        await user_manager.on_after_login(user)
        
        return UserLoginResponse(
            access_token=token,
            refresh_token=token,  # In production, implement proper refresh tokens
            token_type="bearer",
            expires_in=settings.security.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(user: User = Depends(current_active_user)):
    """Logout user (client-side token invalidation)."""
    logger.info(f"User logged out: {user.email}")
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user: User = Depends(current_active_user)):
    """Get current user information."""
    return UserResponse.model_validate(user)


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    user: User = Depends(current_active_user),
    user_manager: UserManager = Depends(get_user_manager)
):
    """Update current user information."""
    try:
        update_dict = user_update.model_dump(exclude_unset=True)
        updated_user = await user_manager.update(update_dict, user)
        return UserResponse.model_validate(updated_user)
        
    except Exception as e:
        logger.error(f"User update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User update failed"
        )


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: PasswordChangeRequest,
    user: User = Depends(current_active_user),
    user_manager: UserManager = Depends(get_user_manager)
):
    """Change user password."""
    try:
        # Verify current password
        if not user_manager.password_helper.verify_and_update(
            password_data.current_password, user.hashed_password
        )[0]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Verify password confirmation
        if password_data.new_password != password_data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password confirmation does not match"
            )
        
        # Update password
        user.hashed_password = user_manager.password_helper.hash(password_data.new_password)
        await user_manager.user_db.update(user)
        
        logger.info(f"Password changed for user: {user.email}")
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    request_data: PasswordResetRequest,
    user_manager: UserManager = Depends(get_user_manager)
):
    """Request password reset."""
    try:
        user = await user_manager.get_by_email(request_data.email)
        if user:
            # Generate reset token (implement email sending in production)
            token = await user_manager.forgot_password(user)
            logger.info(f"Password reset token generated for: {request_data.email}")
            
            # In development, return token for testing
            if settings.is_development:
                return {"message": "Password reset email sent", "token": token}
        
        # Always return success to prevent email enumeration
        return {"message": "Password reset email sent if account exists"}
        
    except Exception as e:
        logger.error(f"Password reset request failed: {str(e)}")
        return {"message": "Password reset email sent if account exists"}


@router.get("/verify/{token}")
async def verify_email(
    token: str,
    user_manager: UserManager = Depends(get_user_manager)
):
    """Verify user email address."""
    try:
        user = await user_manager.verify(token)
        return {"message": "Email verified successfully"}
        
    except Exception as e:
        logger.error(f"Email verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )


# Admin routes
@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(current_superuser),
    session: AsyncSession = Depends(get_db_session)
):
    """List all users (admin only)."""
    try:
        from sqlalchemy import select
        
        stmt = select(User).offset(skip).limit(limit)
        result = await session.execute(stmt)
        users = result.scalars().all()
        
        return [UserResponse.model_validate(user) for user in users]
        
    except Exception as e:
        logger.error(f"User list failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    current_user: User = Depends(current_superuser),
    session: AsyncSession = Depends(get_db_session)
):
    """Get user by ID (admin only)."""
    try:
        from sqlalchemy import select
        
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse.model_validate(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )


@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(current_superuser),
    user_manager: UserManager = Depends(get_user_manager)
):
    """Delete user (admin only)."""
    try:
        user = await user_manager.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        await user_manager.delete(user)
        logger.info(f"User deleted: {user.email}")
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User deletion failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User deletion failed"
        )


# Include FastAPI-Users routers for additional functionality
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/jwt",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_register_router(UserResponse, UserCreate),
    prefix="",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_verify_router(UserResponse),
    prefix="",
    tags=["auth"],
)