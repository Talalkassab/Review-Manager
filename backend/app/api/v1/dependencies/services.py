"""
Service Layer Dependencies for FastAPI
Provides dependency injection for service classes.
"""
from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ....database import get_db_session
from ....services import (
    CustomerService,
    WhatsAppService,
    AIService,
    AnalyticsService
)


async def get_customer_service(
    session: AsyncSession = Depends(get_db_session)
) -> CustomerService:
    """Get CustomerService instance with database session."""
    return CustomerService(session)


async def get_whatsapp_service(
    session: AsyncSession = Depends(get_db_session)
) -> WhatsAppService:
    """Get WhatsAppService instance with database session."""
    return WhatsAppService(session)


async def get_ai_service(
    session: AsyncSession = Depends(get_db_session)
) -> AIService:
    """Get AIService instance with database session."""
    return AIService(session)


async def get_analytics_service(
    session: AsyncSession = Depends(get_db_session)
) -> AnalyticsService:
    """Get AnalyticsService instance with database session."""
    return AnalyticsService(session)