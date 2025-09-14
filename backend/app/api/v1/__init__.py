"""
API Version 1
Main router for all v1 API endpoints with clean architecture.
"""
from fastapi import APIRouter

from .endpoints.customers import router as customers_router
from .endpoints.whatsapp import router as whatsapp_router
from .endpoints.analytics import router as analytics_router

# Create main v1 router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    customers_router,
    prefix="/customers",
    tags=["customers"]
)

api_router.include_router(
    whatsapp_router,
    prefix="/whatsapp",
    tags=["whatsapp"]
)

api_router.include_router(
    analytics_router,
    prefix="/analytics",
    tags=["analytics"]
)

# Health check endpoint for API v1
@api_router.get("/health", tags=["health"])
async def health_check():
    """API v1 health check endpoint."""
    return {
        "status": "healthy",
        "version": "v1",
        "message": "Restaurant AI API v1 is operational"
    }