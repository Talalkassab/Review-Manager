#!/usr/bin/env python3
"""
Comprehensive database initialization script for Restaurant AI Assistant.
Creates database, runs migrations, sets up indexes, and performs validations.
"""
import asyncio
import sys
import argparse
from pathlib import Path
from typing import Optional
import time

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.core.logging import get_logger
from app.database import (
    init_database, create_all_tables, drop_all_tables,
    run_migrations, db_manager, get_database_health
)
from app.models import Base
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


class DatabaseInitializer:
    """Comprehensive database initialization and management."""
    
    def __init__(self, force_recreate: bool = False, run_migrations: bool = True, 
                 skip_validation: bool = False, verbose: bool = False):
        self.force_recreate = force_recreate
        self.run_migrations = run_migrations
        self.skip_validation = skip_validation
        self.verbose = verbose
        self.start_time = time.time()
    
    async def check_database_exists(self) -> bool:
        """Check if database exists and is accessible."""
        try:
            logger.info("Checking database connectivity...")
            await init_database()
            health = await get_database_health()
            
            if health["status"] == "healthy":
                logger.info("✓ Database connection successful")
                return True
            else:
                logger.warning(f"✗ Database health check failed: {health.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Database connection failed: {str(e)}")
            return False
    
    async def create_database_if_not_exists(self) -> None:
        """Create database if it doesn't exist."""
        try:
            # Extract database name from URL
            db_url_parts = settings.database.DATABASE_URL.split("/")
            db_name = db_url_parts[-1]
            base_url = "/".join(db_url_parts[:-1]) + "/postgres"
            
            logger.info(f"Attempting to create database '{db_name}' if it doesn't exist...")
            
            # Connect to postgres database to create target database
            from sqlalchemy.ext.asyncio import create_async_engine
            admin_engine = create_async_engine(
                base_url.replace("postgresql://", "postgresql+asyncpg://"),
                isolation_level="AUTOCOMMIT"
            )
            
            async with admin_engine.connect() as conn:
                # Check if database exists
                result = await conn.execute(
                    text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                    {"db_name": db_name}
                )
                
                if not result.fetchone():
                    await conn.execute(text(f"CREATE DATABASE {db_name}"))
                    logger.info(f"✓ Database '{db_name}' created successfully")
                else:
                    logger.info(f"✓ Database '{db_name}' already exists")
            
            await admin_engine.dispose()
            
        except Exception as e:
            logger.warning(f"Could not create database automatically: {str(e)}")
            logger.info("Please ensure the database exists manually")
    
    async def setup_extensions(self) -> None:
        """Set up required PostgreSQL extensions."""
        try:
            logger.info("Setting up PostgreSQL extensions...")
            
            extensions = [
                "uuid-ossp",  # UUID generation
                "pg_trgm",    # Text search and similarity
                "unaccent",   # Remove accents for search
            ]
            
            async with db_manager.get_session() as session:
                for ext in extensions:
                    try:
                        await session.execute(text(f"CREATE EXTENSION IF NOT EXISTS \"{ext}\""))
                        logger.info(f"✓ Extension '{ext}' enabled")
                    except Exception as e:
                        logger.warning(f"Could not enable extension '{ext}': {str(e)}")
                
                await session.commit()
            
        except Exception as e:
            logger.error(f"Error setting up extensions: {str(e)}")
    
    async def create_custom_indexes(self) -> None:
        """Create custom indexes for performance optimization."""
        try:
            logger.info("Creating custom performance indexes...")
            
            async with db_manager.get_session() as session:
                # Custom indexes for performance
                indexes = [
                    # Customer search indexes
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_customers_phone_search ON customers USING gin(phone_number gin_trgm_ops)",
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_customers_name_search ON customers USING gin((first_name || ' ' || COALESCE(last_name, '')) gin_trgm_ops)",
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_customers_visit_date_status ON customers (visit_date DESC, status) WHERE is_deleted = false",
                    
                    # WhatsApp message indexes
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_whatsapp_messages_conversation ON whatsapp_messages (customer_id, created_at DESC) WHERE direction = 'outbound'",
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_whatsapp_messages_status_retry ON whatsapp_messages (status, retry_count) WHERE status = 'failed'",
                    
                    # Campaign performance indexes
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_campaigns_active_scheduled ON campaigns (scheduled_start_at) WHERE status = 'scheduled'",
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_campaign_recipients_pending ON campaign_recipients (campaign_id, status) WHERE status = 'pending'",
                    
                    # AI interaction analytics indexes
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_interactions_performance ON ai_interactions (restaurant_id, created_at DESC, confidence_score)",
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_interactions_review ON ai_interactions (requires_review, created_at) WHERE requires_review = true",
                    
                    # Restaurant operational indexes
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_restaurants_active_subscription ON restaurants (is_active, subscription_active) WHERE is_active = true",
                    
                    # GDPR compliance indexes
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_customers_retention_date ON customers (data_retention_date) WHERE data_retention_date IS NOT NULL",
                ]
                
                for idx_sql in indexes:
                    try:
                        await session.execute(text(idx_sql))
                        logger.info(f"✓ Created index: {idx_sql.split()[5]}")
                    except Exception as e:
                        if "already exists" in str(e).lower():
                            logger.info(f"✓ Index already exists: {idx_sql.split()[5]}")
                        else:
                            logger.warning(f"Could not create index: {str(e)}")
                
                await session.commit()
            
        except Exception as e:
            logger.error(f"Error creating custom indexes: {str(e)}")
    
    async def validate_schema(self) -> bool:
        """Validate database schema integrity."""
        if self.skip_validation:
            logger.info("Skipping schema validation")
            return True
        
        try:
            logger.info("Validating database schema...")
            
            async with db_manager.get_session() as session:
                # Check if all expected tables exist
                inspector = inspect(session.bind)
                existing_tables = await session.run_sync(lambda sync_session: inspector.get_table_names())
                
                expected_tables = [
                    'users', 'restaurants', 'customers', 'whatsapp_messages',
                    'conversation_threads', 'campaigns', 'campaign_recipients',
                    'agent_personas', 'message_flows', 'ai_interactions'
                ]
                
                missing_tables = set(expected_tables) - set(existing_tables)
                if missing_tables:
                    logger.error(f"✗ Missing tables: {missing_tables}")
                    return False
                
                logger.info(f"✓ All {len(expected_tables)} expected tables exist")
                
                # Check critical foreign key constraints
                constraints_check = """
                SELECT COUNT(*) as constraint_count
                FROM information_schema.table_constraints 
                WHERE constraint_type = 'FOREIGN KEY' 
                AND table_schema = 'public'
                """
                
                result = await session.execute(text(constraints_check))
                fk_count = result.scalar()
                
                if fk_count < 10:  # We expect at least 10 foreign keys
                    logger.warning(f"✗ Only {fk_count} foreign key constraints found, expected more")
                else:
                    logger.info(f"✓ {fk_count} foreign key constraints validated")
                
                return True
                
        except Exception as e:
            logger.error(f"Schema validation failed: {str(e)}")
            return False
    
    async def optimize_database(self) -> None:
        """Run database optimization tasks."""
        try:
            logger.info("Running database optimization...")
            
            async with db_manager.get_session() as session:
                # Update table statistics
                await session.execute(text("ANALYZE"))
                logger.info("✓ Table statistics updated")
                
                # Set optimal PostgreSQL settings for the application
                settings_sql = [
                    "SET shared_preload_libraries = 'pg_stat_statements'",
                    # These would typically be set in postgresql.conf
                ]
                
                for setting in settings_sql:
                    try:
                        await session.execute(text(setting))
                    except Exception:
                        pass  # Settings that require restart or are already set
                
                await session.commit()
            
        except Exception as e:
            logger.warning(f"Database optimization completed with warnings: {str(e)}")
    
    async def run_health_diagnostics(self) -> None:
        """Run comprehensive health diagnostics."""
        try:
            logger.info("Running health diagnostics...")
            
            health = await get_database_health()
            
            logger.info(f"Database Status: {health['status']}")
            if 'pool_status' in health:
                pool = health['pool_status']
                logger.info(f"Connection Pool: {pool['checked_out']}/{pool['total_connections']} connections in use")
            
            # Check disk space usage
            async with db_manager.get_session() as session:
                size_query = """
                SELECT 
                    pg_size_pretty(pg_database_size(current_database())) as db_size,
                    pg_size_pretty(pg_total_relation_size('customers')) as customers_size,
                    pg_size_pretty(pg_total_relation_size('whatsapp_messages')) as messages_size
                """
                
                result = await session.execute(text(size_query))
                size_data = result.fetchone()
                
                logger.info(f"Database Size: {size_data[0]}")
                logger.info(f"Customers Table: {size_data[1]}")
                logger.info(f"Messages Table: {size_data[2]}")
            
        except Exception as e:
            logger.error(f"Health diagnostics failed: {str(e)}")
    
    async def initialize(self) -> bool:
        """Run complete database initialization."""
        try:
            logger.info("🚀 Starting comprehensive database initialization...")
            logger.info(f"Environment: {settings.app.ENVIRONMENT}")
            logger.info(f"Database URL: {settings.database.DATABASE_URL.split('@')[0]}@***")
            
            # Step 1: Create database if needed
            await self.create_database_if_not_exists()
            
            # Step 2: Check connectivity
            if not await self.check_database_exists():
                logger.error("❌ Cannot proceed without database connection")
                return False
            
            # Step 3: Handle existing schema
            if self.force_recreate:
                logger.warning("⚠️  Force recreate enabled - dropping all tables")
                if settings.is_production:
                    logger.error("❌ Cannot force recreate in production")
                    return False
                await drop_all_tables()
            
            # Step 4: Create tables
            logger.info("📋 Creating database tables...")
            await create_all_tables()
            
            # Step 5: Set up extensions
            await self.setup_extensions()
            
            # Step 6: Run migrations if requested
            if self.run_migrations:
                logger.info("🔄 Running database migrations...")
                try:
                    run_migrations()
                    logger.info("✓ Migrations completed")
                except Exception as e:
                    logger.warning(f"Migration warning: {str(e)}")
            
            # Step 7: Create performance indexes
            await self.create_custom_indexes()
            
            # Step 8: Validate schema
            if not await self.validate_schema():
                logger.error("❌ Schema validation failed")
                return False
            
            # Step 9: Optimize database
            await self.optimize_database()
            
            # Step 10: Run diagnostics
            if self.verbose:
                await self.run_health_diagnostics()
            
            elapsed = time.time() - self.start_time
            logger.info(f"✅ Database initialization completed successfully in {elapsed:.2f} seconds")
            
            return True
            
        except Exception as e:
            elapsed = time.time() - self.start_time
            logger.error(f"❌ Database initialization failed after {elapsed:.2f} seconds: {str(e)}")
            return False
        
        finally:
            # Clean up connections
            await db_manager.close()


async def main():
    """Main initialization function with command line arguments."""
    parser = argparse.ArgumentParser(description="Initialize Restaurant AI Assistant database")
    parser.add_argument("--force-recreate", action="store_true", 
                       help="Drop and recreate all tables (development only)")
    parser.add_argument("--skip-migrations", action="store_true", 
                       help="Skip running Alembic migrations")
    parser.add_argument("--skip-validation", action="store_true", 
                       help="Skip schema validation")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Enable verbose output with diagnostics")
    
    args = parser.parse_args()
    
    initializer = DatabaseInitializer(
        force_recreate=args.force_recreate,
        run_migrations=not args.skip_migrations,
        skip_validation=args.skip_validation,
        verbose=args.verbose
    )
    
    success = await initializer.initialize()
    
    if success:
        logger.info("🎉 Database is ready for use!")
        sys.exit(0)
    else:
        logger.error("💥 Database initialization failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())