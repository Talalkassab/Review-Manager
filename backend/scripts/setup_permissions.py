#!/usr/bin/env python3
"""
Database permissions and roles setup script for Restaurant AI Assistant.
Creates database roles, sets permissions, and configures security settings.
"""
import asyncio
import sys
import argparse
from pathlib import Path
from typing import List, Dict

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.core.logging import get_logger
from app.database import init_database, db_manager
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


class DatabasePermissionsManager:
    """Manages database roles and permissions setup."""
    
    def __init__(self, create_roles: bool = True, setup_permissions: bool = True):
        self.create_roles = create_roles
        self.setup_permissions = setup_permissions
        
    async def create_database_roles(self, session: AsyncSession) -> None:
        """Create database roles with appropriate permissions."""
        try:
            logger.info("Creating database roles...")
            
            # Application roles configuration
            roles_config = [
                {
                    "role_name": "restaurant_ai_app",
                    "description": "Main application role with full access to application tables",
                    "permissions": [
                        "CONNECT",
                        "CREATE",
                        "USAGE"
                    ],
                    "table_permissions": "ALL",
                    "can_login": True,
                    "password": settings.database.DATABASE_URL.split(":")[-1].split("@")[0] if "@" in settings.database.DATABASE_URL else "app_password_123"
                },
                {
                    "role_name": "restaurant_ai_readonly",
                    "description": "Read-only role for reporting and analytics",
                    "permissions": [
                        "CONNECT",
                        "USAGE"
                    ],
                    "table_permissions": "SELECT",
                    "can_login": True,
                    "password": "readonly_123"
                },
                {
                    "role_name": "restaurant_ai_backup",
                    "description": "Backup role with read access for backup operations",
                    "permissions": [
                        "CONNECT",
                        "USAGE"
                    ],
                    "table_permissions": "SELECT",
                    "can_login": True,
                    "password": "backup_123"
                },
                {
                    "role_name": "restaurant_ai_analytics",
                    "description": "Analytics role with read access and ability to create temp tables",
                    "permissions": [
                        "CONNECT",
                        "USAGE",
                        "TEMPORARY"
                    ],
                    "table_permissions": "SELECT",
                    "can_login": True,
                    "password": "analytics_123"
                }
            ]
            
            for role_config in roles_config:
                role_name = role_config["role_name"]
                
                # Check if role exists
                check_role_sql = """
                SELECT 1 FROM pg_roles WHERE rolname = :role_name
                """
                result = await session.execute(text(check_role_sql), {"role_name": role_name})
                role_exists = result.fetchone() is not None
                
                if not role_exists:
                    # Create role
                    login_clause = "LOGIN" if role_config["can_login"] else "NOLOGIN"
                    password_clause = f"PASSWORD '{role_config['password']}'" if role_config["can_login"] else ""
                    
                    create_role_sql = f"""
                    CREATE ROLE {role_name} {login_clause} {password_clause}
                    """
                    
                    await session.execute(text(create_role_sql))
                    logger.info(f"✓ Created role: {role_name}")
                else:
                    logger.info(f"✓ Role already exists: {role_name}")
                
                # Grant database permissions
                for permission in role_config["permissions"]:
                    grant_sql = f"GRANT {permission} ON DATABASE {session.bind.url.database} TO {role_name}"
                    try:
                        await session.execute(text(grant_sql))
                    except Exception as e:
                        logger.warning(f"Could not grant {permission} to {role_name}: {str(e)}")
                
                await session.commit()
            
            logger.info("✓ Database roles created successfully")
            
        except Exception as e:
            logger.error(f"Error creating database roles: {str(e)}")
            raise
    
    async def setup_table_permissions(self, session: AsyncSession) -> None:
        """Set up table-specific permissions for roles."""
        try:
            logger.info("Setting up table permissions...")
            
            # Get all application tables
            tables_sql = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            AND table_name NOT LIKE 'alembic_%'
            """
            
            result = await session.execute(text(tables_sql))
            tables = [row[0] for row in result.fetchall()]
            
            if not tables:
                logger.warning("No tables found to set permissions on")
                return
            
            # Permission sets for different roles
            permission_sets = [
                {
                    "role": "restaurant_ai_app",
                    "permissions": ["SELECT", "INSERT", "UPDATE", "DELETE", "REFERENCES", "TRIGGER"]
                },
                {
                    "role": "restaurant_ai_readonly", 
                    "permissions": ["SELECT"]
                },
                {
                    "role": "restaurant_ai_backup",
                    "permissions": ["SELECT"]
                },
                {
                    "role": "restaurant_ai_analytics",
                    "permissions": ["SELECT"]
                }
            ]
            
            for permission_set in permission_sets:
                role = permission_set["role"]
                permissions = ",".join(permission_set["permissions"])
                
                for table in tables:
                    grant_sql = f"GRANT {permissions} ON TABLE {table} TO {role}"
                    try:
                        await session.execute(text(grant_sql))
                    except Exception as e:
                        logger.warning(f"Could not grant permissions on {table} to {role}: {str(e)}")
                
                logger.info(f"✓ Set permissions for role: {role}")
            
            # Grant sequence permissions for roles that need INSERT
            sequences_sql = """
            SELECT sequence_name 
            FROM information_schema.sequences 
            WHERE sequence_schema = 'public'
            """
            
            result = await session.execute(text(sequences_sql))
            sequences = [row[0] for row in result.fetchall()]
            
            for sequence in sequences:
                for role in ["restaurant_ai_app"]:
                    grant_sql = f"GRANT USAGE, SELECT ON SEQUENCE {sequence} TO {role}"
                    try:
                        await session.execute(text(grant_sql))
                    except Exception as e:
                        logger.warning(f"Could not grant sequence permissions on {sequence} to {role}: {str(e)}")
            
            await session.commit()
            logger.info("✓ Table permissions set successfully")
            
        except Exception as e:
            logger.error(f"Error setting up table permissions: {str(e)}")
            raise
    
    async def setup_row_level_security(self, session: AsyncSession) -> None:
        """Set up row-level security policies for multi-tenant data."""
        try:
            logger.info("Setting up row-level security...")
            
            # Tables that need RLS for restaurant isolation
            rls_tables = [
                "customers", "whatsapp_messages", "campaigns", "campaign_recipients",
                "agent_personas", "message_flows", "ai_interactions", "conversation_threads"
            ]
            
            for table in rls_tables:
                # Enable RLS
                enable_rls_sql = f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"
                
                try:
                    await session.execute(text(enable_rls_sql))
                    
                    # Create policy for restaurant isolation
                    # Note: This is a basic example - in production, you'd want more sophisticated policies
                    policy_sql = f"""
                    CREATE POLICY restaurant_isolation ON {table}
                    FOR ALL
                    TO restaurant_ai_app
                    USING (restaurant_id = current_setting('app.current_restaurant_id')::uuid)
                    WITH CHECK (restaurant_id = current_setting('app.current_restaurant_id')::uuid)
                    """
                    
                    try:
                        await session.execute(text(policy_sql))
                        logger.info(f"✓ Created RLS policy for: {table}")
                    except Exception as e:
                        if "already exists" in str(e).lower():
                            logger.info(f"✓ RLS policy already exists for: {table}")
                        else:
                            logger.warning(f"Could not create RLS policy for {table}: {str(e)}")
                    
                except Exception as e:
                    if "already" in str(e).lower():
                        logger.info(f"✓ RLS already enabled for: {table}")
                    else:
                        logger.warning(f"Could not enable RLS for {table}: {str(e)}")
            
            await session.commit()
            logger.info("✓ Row-level security configured")
            
        except Exception as e:
            logger.error(f"Error setting up row-level security: {str(e)}")
            raise
    
    async def setup_database_security(self, session: AsyncSession) -> None:
        """Set up additional database security configurations."""
        try:
            logger.info("Setting up database security configurations...")
            
            security_settings = [
                # Connection and session security
                "ALTER DATABASE CURRENT SET log_connections = on",
                "ALTER DATABASE CURRENT SET log_disconnections = on", 
                "ALTER DATABASE CURRENT SET log_statement = 'mod'",
                
                # Performance and resource limits
                "ALTER DATABASE CURRENT SET shared_preload_libraries = 'pg_stat_statements'",
                "ALTER DATABASE CURRENT SET track_activities = on",
                "ALTER DATABASE CURRENT SET track_counts = on",
                
                # Security settings
                "ALTER DATABASE CURRENT SET ssl = on",
                "ALTER DATABASE CURRENT SET password_encryption = 'scram-sha-256'"
            ]
            
            for setting in security_settings:
                try:
                    await session.execute(text(setting))
                except Exception as e:
                    logger.warning(f"Could not apply setting: {setting.split()[4]} - {str(e)}")
            
            await session.commit()
            logger.info("✓ Database security configurations applied")
            
        except Exception as e:
            logger.error(f"Error setting up database security: {str(e)}")
            raise
    
    async def create_monitoring_views(self, session: AsyncSession) -> None:
        """Create monitoring views for database performance and security."""
        try:
            logger.info("Creating monitoring views...")
            
            monitoring_views = [
                {
                    "name": "v_customer_activity_summary",
                    "sql": """
                    CREATE OR REPLACE VIEW v_customer_activity_summary AS
                    SELECT 
                        r.name as restaurant_name,
                        COUNT(*) as total_customers,
                        COUNT(CASE WHEN c.status = 'pending' THEN 1 END) as pending_customers,
                        COUNT(CASE WHEN c.status = 'completed' THEN 1 END) as completed_customers,
                        AVG(CASE WHEN c.rating IS NOT NULL THEN c.rating END) as avg_rating,
                        COUNT(CASE WHEN c.feedback_sentiment = 'positive' THEN 1 END) as positive_feedback,
                        COUNT(CASE WHEN c.feedback_sentiment = 'negative' THEN 1 END) as negative_feedback
                    FROM customers c
                    JOIN restaurants r ON c.restaurant_id = r.id
                    WHERE c.is_deleted = false
                    GROUP BY r.id, r.name
                    """
                },
                {
                    "name": "v_whatsapp_message_stats",
                    "sql": """
                    CREATE OR REPLACE VIEW v_whatsapp_message_stats AS
                    SELECT 
                        r.name as restaurant_name,
                        COUNT(*) as total_messages,
                        COUNT(CASE WHEN w.direction = 'outbound' THEN 1 END) as outbound_messages,
                        COUNT(CASE WHEN w.direction = 'inbound' THEN 1 END) as inbound_messages,
                        COUNT(CASE WHEN w.status = 'delivered' THEN 1 END) as delivered_messages,
                        COUNT(CASE WHEN w.status = 'failed' THEN 1 END) as failed_messages,
                        ROUND(AVG(w.processing_time_ms), 2) as avg_processing_time_ms
                    FROM whatsapp_messages w
                    JOIN restaurants r ON w.restaurant_id = r.id
                    WHERE w.is_deleted = false
                    GROUP BY r.id, r.name
                    """
                },
                {
                    "name": "v_ai_performance_metrics",
                    "sql": """
                    CREATE OR REPLACE VIEW v_ai_performance_metrics AS
                    SELECT 
                        r.name as restaurant_name,
                        ap.name as persona_name,
                        COUNT(*) as total_interactions,
                        AVG(ai.confidence_score) as avg_confidence,
                        AVG(ai.processing_time_ms) as avg_processing_time,
                        COUNT(CASE WHEN ai.resulted_in_positive_outcome = true THEN 1 END) as positive_outcomes,
                        COUNT(CASE WHEN ai.requires_review = true THEN 1 END) as requires_review,
                        SUM(ai.total_tokens) as total_tokens_used,
                        SUM(ai.estimated_cost_usd) as total_cost_usd
                    FROM ai_interactions ai
                    JOIN restaurants r ON ai.restaurant_id = r.id
                    LEFT JOIN agent_personas ap ON ai.agent_persona_id = ap.id
                    WHERE ai.is_deleted = false
                    GROUP BY r.id, r.name, ap.id, ap.name
                    """
                },
                {
                    "name": "v_campaign_performance",
                    "sql": """
                    CREATE OR REPLACE VIEW v_campaign_performance AS
                    SELECT 
                        r.name as restaurant_name,
                        c.name as campaign_name,
                        c.status,
                        c.recipients_count,
                        c.messages_sent,
                        c.messages_delivered,
                        c.messages_read,
                        c.responses_received,
                        ROUND((c.messages_delivered::numeric / NULLIF(c.messages_sent, 0)) * 100, 2) as delivery_rate,
                        ROUND((c.responses_received::numeric / NULLIF(c.messages_delivered, 0)) * 100, 2) as response_rate,
                        c.actual_cost_usd
                    FROM campaigns c
                    JOIN restaurants r ON c.restaurant_id = r.id
                    WHERE c.is_deleted = false
                    """
                }
            ]
            
            for view in monitoring_views:
                try:
                    await session.execute(text(view["sql"]))
                    logger.info(f"✓ Created monitoring view: {view['name']}")
                except Exception as e:
                    logger.warning(f"Could not create view {view['name']}: {str(e)}")
            
            await session.commit()
            logger.info("✓ Monitoring views created successfully")
            
        except Exception as e:
            logger.error(f"Error creating monitoring views: {str(e)}")
            raise
    
    async def setup_permissions(self) -> bool:
        """Run complete permissions setup process."""
        try:
            logger.info("🔐 Starting database permissions setup...")
            
            await init_database()
            
            async with db_manager.get_session() as session:
                if self.create_roles:
                    await self.create_database_roles(session)
                
                if self.setup_permissions:
                    await self.setup_table_permissions(session)
                    await self.setup_row_level_security(session)
                    await self.setup_database_security(session)
                
                await self.create_monitoring_views(session)
                
                logger.info("✅ Database permissions setup completed successfully")
                return True
                
        except Exception as e:
            logger.error(f"❌ Database permissions setup failed: {str(e)}")
            return False
        
        finally:
            await db_manager.close()


async def main():
    """Main permissions setup function with command line arguments."""
    parser = argparse.ArgumentParser(description="Set up Restaurant AI Assistant database permissions and roles")
    parser.add_argument("--skip-roles", action="store_true", 
                       help="Skip creating database roles")
    parser.add_argument("--skip-permissions", action="store_true", 
                       help="Skip setting up table permissions")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Enable verbose output")
    
    args = parser.parse_args()
    
    manager = DatabasePermissionsManager(
        create_roles=not args.skip_roles,
        setup_permissions=not args.skip_permissions
    )
    
    success = await manager.setup_permissions()
    
    if success:
        logger.info("🎉 Database permissions setup completed successfully!")
        logger.info("🔑 Database roles created:")
        logger.info("  - restaurant_ai_app (full access)")
        logger.info("  - restaurant_ai_readonly (read-only)")
        logger.info("  - restaurant_ai_backup (backup access)")
        logger.info("  - restaurant_ai_analytics (analytics access)")
        sys.exit(0)
    else:
        logger.error("💥 Database permissions setup failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())