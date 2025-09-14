"""
Repository dependency providers.
Provides repository instances for data access.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ....infrastructure.database.repositories import (
    CustomerRepository,
    WhatsAppMessageRepository,
    UserRepository
)
from .database import get_db_session


async def get_customer_repository(
    session: AsyncSession = Depends(get_db_session)
) -> CustomerRepository:
    """Get CustomerRepository instance with database session."""
    return CustomerRepository(session)


async def get_whatsapp_repository(
    session: AsyncSession = Depends(get_db_session)
) -> WhatsAppMessageRepository:
    """Get WhatsAppMessageRepository instance with database session."""
    return WhatsAppMessageRepository(session)


async def get_user_repository(
    session: AsyncSession = Depends(get_db_session)
) -> UserRepository:
    """Get UserRepository instance with database session."""
    return UserRepository(session)