"""
API Module
Organizes all API versions and provides main router.
"""
from fastapi import APIRouter

# Legacy imports (for backward compatibility)
from .auth import router as auth_router
from .customers import router as customers_router
from .restaurants import router as restaurants_router
from .ai_agent import router as ai_agent_router
from .campaigns import router as campaigns_router
from .whatsapp import router as whatsapp_router

# New versioned API
from .v1 import api_router as v1_router

# Main API router
api_router = APIRouter()

# Include versioned routers
api_router.include_router(
    v1_router,
    prefix="/v1"
)

# Root health check
@api_router.get("/health")
async def root_health_check():
    """Root API health check."""
    return {
        "status": "healthy",
        "message": "Restaurant AI API is operational",
        "versions": ["v1"],
        "current_version": "v1"
    }

# Version info endpoint
@api_router.get("/version")
async def version_info():
    """API version information."""
    return {
        "current_version": "v1",
        "supported_versions": ["v1"],
        "deprecation_policy": "Versions are supported for 12 months after new version release",
        "migration_guide": "/docs/migration"
    }

# Legacy exports (for backward compatibility)
__all__ = [
    "api_router",  # New main router
    "auth_router",
    "customers_router",
    "restaurants_router",
    "ai_agent_router",
    "campaigns_router",
    "whatsapp_router"
]