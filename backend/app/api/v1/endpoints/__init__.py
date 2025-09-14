"""
API v1 endpoints module.
"""
from .customers import router as customers_router
from .whatsapp import router as whatsapp_router
from .analytics import router as analytics_router

__all__ = [
    "customers_router",
    "whatsapp_router",
    "analytics_router"
]