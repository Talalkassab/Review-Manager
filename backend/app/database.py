"""
Database configuration and session management for Restaurant AI Assistant.
Provides async SQLAlchemy setup with PostgreSQL support.
"""
import asyncio
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from alembic import command
from alembic.config import Config

from .core.config import settings
from .core.logging import get_logger, performance_monitor
from .models.base import Base

logger = get_logger(__name__)

# Global engine and session maker
async_engine: Optional[AsyncEngine] = None
AsyncSessionLocal: Optional[async_sessionmaker[AsyncSession]] = None


class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self):
        self.engine: Optional[AsyncEngine] = None
        self.session_maker: Optional[async_sessionmaker[AsyncSession]] = None
        self.is_initialized = False
    
    async def initialize(self) -> None:
        """Initialize database engine and session maker."""
        if self.is_initialized:
            logger.warning("Database already initialized, skipping...")
            return
        
        try:
            logger.info("Initializing database connection...")
            
            # Create async engine
            self.engine = create_async_engine(
                settings.database.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
                pool_size=settings.database.DB_POOL_SIZE,
                max_overflow=settings.database.DB_MAX_OVERFLOW,
                pool_timeout=settings.database.DB_POOL_TIMEOUT,
                pool_pre_ping=True,  # Verify connections before use
                echo=settings.logging.ENABLE_SQL_LOGGING,  # Log SQL queries
                future=True
            )
            
            # Create session maker
            self.session_maker = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False
            )
            
            # Test connection
            await self.test_connection()
            
            self.is_initialized = True
            logger.info(f"Database initialized successfully")
            logger.info(f"Pool size: {settings.database.DB_POOL_SIZE}")
            logger.info(f"Max overflow: {settings.database.DB_MAX_OVERFLOW}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            await self.close()
            raise
    
    @performance_monitor("database_connection_test", threshold_ms=2000)
    async def test_connection(self) -> None:
        """Test database connection."""
        if not self.engine:
            raise RuntimeError("Database engine not initialized")
        
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                value = result.scalar()
                if value != 1:
                    raise RuntimeError("Database connection test failed")
                
            logger.info("Database connection test passed")
            
        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            raise
    
    async def create_tables(self) -> None:
        """Create all database tables."""
        if not self.engine:
            raise RuntimeError("Database engine not initialized")
        
        try:
            logger.info("Creating database tables...")
            
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create database tables: {str(e)}")
            raise
    
    async def drop_tables(self) -> None:
        """Drop all database tables (use with caution!)."""
        if not self.engine:
            raise RuntimeError("Database engine not initialized")
        
        if settings.is_production:
            raise RuntimeError("Cannot drop tables in production environment")
        
        try:
            logger.warning("Dropping all database tables...")
            
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            
            logger.warning("All database tables dropped")
            
        except Exception as e:
            logger.error(f"Failed to drop database tables: {str(e)}")
            raise
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with automatic cleanup."""
        if not self.session_maker:
            raise RuntimeError("Database not initialized")
        
        session = self.session_maker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    async def get_session_for_dependency(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session for FastAPI dependency injection."""
        async with self.get_session() as session:
            yield session
    
    @performance_monitor("database_health_check", threshold_ms=1000)
    async def health_check(self) -> dict:
        """Perform database health check."""
        if not self.is_initialized or not self.engine:
            return {
                "status": "unhealthy",
                "error": "Database not initialized"
            }
        
        try:
            async with self.engine.begin() as conn:
                # Test basic query
                result = await conn.execute(text("SELECT 1 as health_check"))
                health_value = result.scalar()
                
                # Get connection pool info
                pool = self.engine.pool
                pool_status = {
                    "size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                    "total_connections": pool.size() + pool.overflow()
                }
                
                return {
                    "status": "healthy",
                    "health_check_value": health_value,
                    "pool_status": pool_status
                }
                
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def close(self) -> None:
        """Close database connections."""
        try:
            if self.engine:
                logger.info("Closing database connections...")
                await self.engine.dispose()
                logger.info("Database connections closed")
            
            self.engine = None
            self.session_maker = None
            self.is_initialized = False
            
        except Exception as e:
            logger.error(f"Error closing database connections: {str(e)}")


# Global database manager instance
db_manager = DatabaseManager()


async def init_database() -> None:
    """Initialize the database."""
    global async_engine, AsyncSessionLocal
    
    await db_manager.initialize()
    
    # Set global variables for backward compatibility
    async_engine = db_manager.engine
    AsyncSessionLocal = db_manager.session_maker


async def close_database() -> None:
    """Close database connections."""
    global async_engine, AsyncSessionLocal
    
    await db_manager.close()
    
    # Clear global variables
    async_engine = None
    AsyncSessionLocal = None


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency to get database session.
    Usage: async def endpoint(db: AsyncSession = Depends(get_db_session))
    """
    async with db_manager.get_session() as session:
        yield session


async def create_all_tables() -> None:
    """Create all database tables."""
    await db_manager.create_tables()


async def drop_all_tables() -> None:
    """Drop all database tables (development only)."""
    await db_manager.drop_tables()


async def get_database_health() -> dict:
    """Get database health status."""
    return await db_manager.health_check()


class DatabaseTransaction:
    """Context manager for database transactions."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.transaction = None
    
    async def __aenter__(self):
        self.transaction = await self.session.begin()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.transaction.rollback()
            logger.error(f"Transaction rolled back due to error: {exc_val}")
        else:
            await self.transaction.commit()
            logger.debug("Transaction committed successfully")


# Migration utilities
def run_migrations(target_revision: str = "head") -> None:
    """Run Alembic migrations."""
    try:
        logger.info(f"Running database migrations to {target_revision}...")
        
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, target_revision)
        
        logger.info("Database migrations completed successfully")
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise


def create_migration(message: str) -> None:
    """Create a new Alembic migration."""
    try:
        logger.info(f"Creating new migration: {message}")
        
        alembic_cfg = Config("alembic.ini")
        command.revision(alembic_cfg, message=message, autogenerate=True)
        
        logger.info("Migration created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create migration: {str(e)}")
        raise


# Utility functions for testing
async def reset_database_for_testing() -> None:
    """Reset database for testing (test environment only)."""
    if not settings.is_testing:
        raise RuntimeError("Can only reset database in testing environment")
    
    logger.warning("Resetting database for testing...")
    
    await drop_all_tables()
    await create_all_tables()
    
    logger.warning("Database reset completed")


# Export commonly used items
__all__ = [
    "db_manager",
    "init_database",
    "close_database", 
    "get_db_session",
    "create_all_tables",
    "drop_all_tables",
    "get_database_health",
    "DatabaseTransaction",
    "run_migrations",
    "create_migration",
    "reset_database_for_testing"
]