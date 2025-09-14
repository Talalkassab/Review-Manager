"""
Dependency injection module for API v1.
Provides all FastAPI dependencies for routes.
"""
from .database import get_db_session
from .auth import (
    current_active_user,
    get_current_user,
    get_optional_current_user,
    require_permissions,
    require_superuser
)
from .services import (
    get_customer_service,
    get_whatsapp_service,
    get_ai_service,
    get_analytics_service
)
from .repositories import (
    get_customer_repository,
    get_whatsapp_repository,
    get_user_repository
)

__all__ = [
    # Database
    "get_db_session",

    # Authentication
    "current_active_user",
    "get_current_user",
    "get_optional_current_user",
    "require_permissions",
    "require_superuser",

    # Services
    "get_customer_service",
    "get_whatsapp_service",
    "get_ai_service",
    "get_analytics_service",

    # Repositories
    "get_customer_repository",
    "get_whatsapp_repository",
    "get_user_repository"
]