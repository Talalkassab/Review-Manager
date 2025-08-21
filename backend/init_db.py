#!/usr/bin/env python3
"""
Initialize database with tables and sample data.
"""
import asyncio
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import init_database, get_db_session
from app.models import Base
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_tables():
    """Create all database tables."""
    engine = create_async_engine(
        settings.database.DATABASE_URL,
        echo=True
    )
    
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ All tables created successfully")
    
    await engine.dispose()


async def main():
    """Initialize database with tables."""
    try:
        logger.info("🚀 Starting database initialization...")
        
        # Initialize database connection
        await init_database()
        
        # Create tables
        await create_tables()
        
        logger.info("✅ Database initialization complete!")
        logger.info("📊 You can now:")
        logger.info("   1. Register a user at http://localhost:8000/docs#/Authentication/register_register_api_v1_auth_register_post")
        logger.info("   2. Access the frontend at http://localhost:3002")
        logger.info("   3. Start adding restaurants and customers")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())