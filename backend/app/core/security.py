"""
Enhanced security utilities for the WhatsApp Customer Agent.
Includes password hashing, JWT handling, input validation, and security monitoring.
"""
import hashlib
import hmac
import secrets
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote

from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, Request, status
from pydantic import BaseModel, validator
import bleach

from .config import settings
from .logging import get_logger

logger = get_logger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Allowed HTML tags for rich text (if needed)
ALLOWED_HTML_TAGS = ['b', 'i', 'u', 'em', 'strong', 'br', 'p']
ALLOWED_HTML_ATTRIBUTES = {}


class SecurityConfig:
    """Security configuration constants."""

    # JWT settings
    ALGORITHM = "HS256"

    # Password validation regex
    PASSWORD_PATTERN = re.compile(
        r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
    )

    # Phone number validation
    PHONE_PATTERN = re.compile(r'^\+[1-9]\d{1,14}$')  # E.164 format

    # Email validation (additional to Pydantic)
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )

    # SQL Injection patterns (basic detection)
    SQL_INJECTION_PATTERNS = [
        r"'.*(\bOR\b|\bAND\b).*'",
        r"'.*\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|CREATE)\b.*'",
        r"--",
        r"/\*.*\*/",
        r"\bxp_cmdshell\b",
        r"\bsp_executesql\b"
    ]

    # XSS patterns
    XSS_PATTERNS = [
        r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe\b',
        r'<object\b',
        r'<embed\b'
    ]


class TokenData(BaseModel):
    """Token data structure."""
    user_id: Optional[str] = None
    username: Optional[str] = None
    permissions: List[str] = []
    expires_at: Optional[datetime] = None


class SecurityManager:
    """Main security manager class."""

    def __init__(self):
        self.secret_key = settings.security.SECRET_KEY

    # Password Management

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """
        Validate password strength and return detailed feedback.
        """
        result = {
            "is_valid": True,
            "score": 0,
            "feedback": [],
            "requirements": {
                "min_length": len(password) >= settings.security.PASSWORD_MIN_LENGTH,
                "has_uppercase": bool(re.search(r'[A-Z]', password)),
                "has_lowercase": bool(re.search(r'[a-z]', password)),
                "has_numbers": bool(re.search(r'\d', password)),
                "has_special": bool(re.search(r'[@$!%*?&]', password)),
                "no_common_patterns": not self._has_common_patterns(password)
            }
        }

        # Calculate score
        for req, met in result["requirements"].items():
            if met:
                result["score"] += 1

        # Add feedback
        if not result["requirements"]["min_length"]:
            result["feedback"].append(f"Password must be at least {settings.security.PASSWORD_MIN_LENGTH} characters long")

        if not result["requirements"]["has_uppercase"]:
            result["feedback"].append("Password must contain at least one uppercase letter")

        if not result["requirements"]["has_lowercase"]:
            result["feedback"].append("Password must contain at least one lowercase letter")

        if not result["requirements"]["has_numbers"]:
            result["feedback"].append("Password must contain at least one number")

        if not result["requirements"]["has_special"]:
            result["feedback"].append("Password must contain at least one special character (@$!%*?&)")

        if not result["requirements"]["no_common_patterns"]:
            result["feedback"].append("Password contains common patterns or dictionary words")

        # Overall validation
        result["is_valid"] = all(result["requirements"].values())

        return result

    def _has_common_patterns(self, password: str) -> bool:
        """Check for common password patterns."""
        common_patterns = [
            "password", "123456", "qwerty", "abc123", "admin",
            "letmein", "welcome", "monkey", "dragon"
        ]

        password_lower = password.lower()
        return any(pattern in password_lower for pattern in common_patterns)

    # JWT Token Management

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.security.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode.update({"exp": expire, "type": "access"})

        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=SecurityConfig.ALGORITHM)

            logger.info(
                "Access token created",
                user_id=data.get("user_id"),
                expires_at=expire.isoformat()
            )

            return encoded_jwt
        except Exception as e:
            logger.error("Failed to create access token", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create access token"
            )

    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(
            minutes=settings.security.REFRESH_TOKEN_EXPIRE_MINUTES
        )

        to_encode.update({"exp": expire, "type": "refresh"})

        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=SecurityConfig.ALGORITHM)

            logger.info(
                "Refresh token created",
                user_id=data.get("user_id"),
                expires_at=expire.isoformat()
            )

            return encoded_jwt
        except Exception as e:
            logger.error("Failed to create refresh token", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create refresh token"
            )

    def verify_token(self, token: str, token_type: str = "access") -> TokenData:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[SecurityConfig.ALGORITHM])

            # Verify token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type}"
                )

            # Extract token data
            user_id = payload.get("user_id")
            username = payload.get("username")
            permissions = payload.get("permissions", [])
            expires_at = datetime.fromtimestamp(payload.get("exp", 0))

            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing user ID"
                )

            return TokenData(
                user_id=user_id,
                username=username,
                permissions=permissions,
                expires_at=expires_at
            )

        except JWTError as e:
            logger.warning("JWT verification failed", error=str(e), token_type=token_type)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    # Input Validation and Sanitization

    def validate_phone_number(self, phone_number: str) -> bool:
        """Validate phone number format (E.164)."""
        if not phone_number:
            return False

        return bool(SecurityConfig.PHONE_PATTERN.match(phone_number))

    def validate_email(self, email: str) -> bool:
        """Additional email validation."""
        if not email:
            return False

        return bool(SecurityConfig.EMAIL_PATTERN.match(email))

    def sanitize_html(self, text: str) -> str:
        """Sanitize HTML content to prevent XSS."""
        if not text:
            return text

        return bleach.clean(
            text,
            tags=ALLOWED_HTML_TAGS,
            attributes=ALLOWED_HTML_ATTRIBUTES,
            strip=True
        )

    def validate_input_security(self, text: str) -> Dict[str, Any]:
        """
        Check input for potential security threats.
        """
        if not text:
            return {"is_safe": True, "threats": []}

        threats = []

        # Check for SQL injection patterns
        for pattern in SecurityConfig.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                threats.append("potential_sql_injection")
                break

        # Check for XSS patterns
        for pattern in SecurityConfig.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                threats.append("potential_xss")
                break

        # Check for directory traversal
        if "../" in text or "..\\{}" in text:
            threats.append("directory_traversal")

        # Check for command injection
        command_patterns = [";", "&", "|", "`", "$", "(", ")", "<", ">"]
        if any(pattern in text for pattern in command_patterns):
            threats.append("potential_command_injection")

        return {
            "is_safe": len(threats) == 0,
            "threats": threats,
            "sanitized_text": self.sanitize_html(text)
        }

    # Webhook Security

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str,
        algorithm: str = "sha256"
    ) -> bool:
        """
        Verify webhook signature (e.g., from Twilio, GitHub, etc.).
        """
        try:
            # Create expected signature
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                payload,
                hashlib.sha256 if algorithm == "sha256" else hashlib.sha1
            ).hexdigest()

            # For Twilio, the signature is base64-encoded
            if "twilio" in signature.lower():
                import base64
                expected_signature = base64.b64encode(
                    hmac.new(secret.encode('utf-8'), payload, hashlib.sha1).digest()
                ).decode()

            # Constant-time comparison to prevent timing attacks
            return hmac.compare_digest(signature, expected_signature)

        except Exception as e:
            logger.error("Webhook signature verification failed", error=str(e))
            return False

    def generate_api_key(self, length: int = 32) -> str:
        """Generate secure API key."""
        return secrets.token_urlsafe(length)

    # Security Monitoring

    def log_security_event(
        self,
        event_type: str,
        request: Request,
        details: Optional[Dict] = None,
        severity: str = "medium"
    ):
        """Log security events for monitoring."""
        event_data = {
            "event_type": event_type,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat(),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", "unknown"),
            "path": request.url.path,
            "method": request.method,
            "details": details or {}
        }

        # Get correlation ID if available
        correlation_id = getattr(request.state, 'correlation_id', None)
        if correlation_id:
            event_data["correlation_id"] = correlation_id

        # Log with appropriate level based on severity
        log_level = {
            "low": "info",
            "medium": "warning",
            "high": "error",
            "critical": "error"
        }.get(severity, "warning")

        getattr(logger, log_level)(
            f"Security event: {event_type}",
            **event_data
        )

        # For high/critical events, also log to security logger
        if severity in ["high", "critical"]:
            security_logger = get_logger("security")
            getattr(security_logger, log_level)(
                f"SECURITY ALERT: {event_type}",
                **event_data
            )

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    # Rate Limiting Helpers

    def generate_rate_limit_key(self, identifier: str, window: str = "minute") -> str:
        """Generate rate limit key for Redis or in-memory storage."""
        return f"rate_limit:{identifier}:{window}"

    def calculate_rate_limit_reset(self, window_seconds: int) -> datetime:
        """Calculate when rate limit resets."""
        return datetime.utcnow() + timedelta(seconds=window_seconds)


# Global security manager instance
security_manager = SecurityManager()

# Export commonly used functions
def hash_password(password: str) -> str:
    """Hash a password."""
    return security_manager.hash_password(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password."""
    return security_manager.verify_password(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create access token."""
    return security_manager.create_access_token(data, expires_delta)

def verify_token(token: str, token_type: str = "access") -> TokenData:
    """Verify token."""
    return security_manager.verify_token(token, token_type)

def validate_input_security(text: str) -> Dict[str, Any]:
    """Validate input for security threats."""
    return security_manager.validate_input_security(text)

def log_security_event(event_type: str, request: Request, details: Optional[Dict] = None, severity: str = "medium"):
    """Log security event."""
    return security_manager.log_security_event(event_type, request, details, severity)


# Export classes and functions
__all__ = [
    'SecurityManager',
    'TokenData',
    'SecurityConfig',
    'security_manager',
    'hash_password',
    'verify_password',
    'create_access_token',
    'verify_token',
    'validate_input_security',
    'log_security_event'
]