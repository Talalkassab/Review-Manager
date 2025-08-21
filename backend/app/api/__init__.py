"""
API routers for Restaurant AI Customer Feedback Agent.
Exports all router modules for easy import.
"""
from .auth import router as auth_router
from .customers import router as customers_router
from .restaurants import router as restaurants_router
from .ai_agent import router as ai_agent_router
from .campaigns import router as campaigns_router
from .whatsapp import router as whatsapp_router

__all__ = [
    "auth_router",
    "customers_router", 
    "restaurants_router",
    "ai_agent_router",
    "campaigns_router",
    "whatsapp_router"
]