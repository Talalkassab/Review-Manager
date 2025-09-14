"""
Database dependency providers.
Manages database sessions and connections.
"""
from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ....database import get_db_session as _get_db_session


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session dependency.
    Provides async database session for dependency injection.
    """
    async for session in _get_db_session():
        yield session