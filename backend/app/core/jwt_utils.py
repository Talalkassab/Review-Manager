"""
JWT Token utilities for authentication.
Handles token creation, verification, and user extraction.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID
import jwt
from passlib.context import CryptContext

from .config import settings
from .exceptions import TokenExpired, InvalidCredentials
from ..models.user import User

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.security.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_MINUTES = settings.security.REFRESH_TOKEN_EXPIRE_MINUTES


class JWTUtils:
    """JWT token utilities for authentication."""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash."""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token."""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "token_type": "access"
        })

        encoded_jwt = jwt.encode(
            to_encode,
            settings.security.SECRET_KEY,
            algorithm=ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def create_refresh_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "token_type": "refresh"
        })

        encoded_jwt = jwt.encode(
            to_encode,
            settings.security.SECRET_KEY,
            algorithm=ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        """
        Verify JWT token and return payload.

        Args:
            token: JWT token string
            token_type: Expected token type ('access' or 'refresh')

        Returns:
            Token payload dictionary

        Raises:
            InvalidCredentials: If token is invalid
            TokenExpired: If token has expired
        """
        try:
            payload = jwt.decode(
                token,
                settings.security.SECRET_KEY,
                algorithms=[ALGORITHM]
            )

            # Verify token type
            if payload.get("token_type") != token_type:
                raise InvalidCredentials()

            # Check expiration
            exp = payload.get("exp")
            if exp is None:
                raise InvalidCredentials()

            if datetime.fromtimestamp(exp) < datetime.utcnow():
                raise TokenExpired()

            return payload

        except jwt.ExpiredSignatureError:
            raise TokenExpired()
        except (jwt.DecodeError, jwt.InvalidTokenError):
            raise InvalidCredentials()

    @staticmethod
    def get_user_id_from_token(token: str) -> Optional[UUID]:
        """Extract user ID from JWT token."""
        try:
            payload = JWTUtils.verify_token(token)
            user_id = payload.get("user_id")

            if user_id:
                return UUID(user_id)
            return None

        except (InvalidCredentials, TokenExpired):
            return None

    @staticmethod
    def create_token_pair(user: User) -> Dict[str, str]:
        """Create access and refresh token pair for user."""
        token_data = {
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
            "restaurant_id": str(user.restaurant_id) if user.restaurant_id else None
        }

        access_token = JWTUtils.create_access_token(token_data)
        refresh_token = JWTUtils.create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }

    @staticmethod
    def refresh_access_token(refresh_token: str) -> Dict[str, str]:
        """Create new access token from refresh token."""
        payload = JWTUtils.verify_token(refresh_token, token_type="refresh")

        # Remove exp and iat from payload
        token_data = {k: v for k, v in payload.items() if k not in ["exp", "iat", "token_type"]}

        access_token = JWTUtils.create_access_token(token_data)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }