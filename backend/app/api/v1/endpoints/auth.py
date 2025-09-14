"""
Authentication endpoints for login, logout, and token management.
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ....core.logging import get_logger
from ....core.jwt_utils import JWTUtils
from ....core.exceptions import InvalidCredentials, TokenExpired
from ....database import get_db_session
from ....models.user import User
from ....schemas.auth import TokenResponse, RefreshTokenRequest
from ..dependencies.auth import current_active_user

logger = get_logger(__name__)
router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Authenticate user and return JWT tokens.

    Args:
        form_data: OAuth2 form with username/password
        session: Database session

    Returns:
        JWT access and refresh tokens
    """
    try:
        # Find user by email
        stmt = select(User).where(User.email == form_data.username)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"Login attempt with non-existent email: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify password
        if not JWTUtils.verify_password(form_data.password, user.hashed_password):
            logger.warning(f"Invalid password attempt for user: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login attempt by inactive user: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )

        # Record login
        user.record_login()
        await session.commit()

        # Create token pair
        token_data = JWTUtils.create_token_pair(user)

        logger.info(f"Successful login for user: {user.email}")

        return TokenResponse(
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            token_type=token_data["token_type"],
            expires_in=token_data["expires_in"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service unavailable"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_request: RefreshTokenRequest
):
    """
    Refresh access token using refresh token.

    Args:
        refresh_request: Contains refresh token

    Returns:
        New access token
    """
    try:
        token_data = JWTUtils.refresh_access_token(refresh_request.refresh_token)

        return TokenResponse(
            access_token=token_data["access_token"],
            refresh_token=refresh_request.refresh_token,  # Keep same refresh token
            token_type=token_data["token_type"],
            expires_in=token_data["expires_in"]
        )

    except TokenExpired:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired"
        )
    except InvalidCredentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout")
async def logout(
    current_user: User = Depends(current_active_user)
):
    """
    Logout user (client should discard tokens).

    Args:
        current_user: Authenticated user

    Returns:
        Success message
    """
    logger.info(f"User logout: {current_user.email}")

    # In a production system, you might want to:
    # 1. Add token to blacklist/revoked tokens table
    # 2. Update user's last logout time
    # 3. Clear any active sessions

    return {"message": "Successfully logged out"}


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(current_active_user)
) -> Dict[str, Any]:
    """
    Get current authenticated user information.

    Args:
        current_user: Authenticated user

    Returns:
        User profile information
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role),
        "restaurant_id": str(current_user.restaurant_id) if current_user.restaurant_id else None,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "permissions": current_user.get_permissions(),
        "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None
    }


@router.post("/verify-token")
async def verify_token(
    current_user: User = Depends(current_active_user)
):
    """
    Verify if current token is valid.

    Args:
        current_user: Authenticated user (validates token)

    Returns:
        Token validity status
    """
    return {
        "valid": True,
        "user_id": str(current_user.id),
        "email": current_user.email
    }