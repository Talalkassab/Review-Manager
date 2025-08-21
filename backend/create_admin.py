#!/usr/bin/env python3
"""
Create admin user directly in database.
"""
import asyncio
import sys
import uuid
from pathlib import Path
from passlib.context import CryptContext

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import init_database, get_db_session
from app.models import User
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_admin_user():
    """Create admin user in database."""
    try:
        # Initialize database
        await init_database()
        
        # User details
        email = "admin@restaurant.com"
        password = "Admin123!"
        
        # Hash password
        hashed_password = pwd_context.hash(password)
        
        # Create user
        admin_user = User(
            id=uuid.uuid4(),
            email=email,
            hashed_password=hashed_password,
            first_name="Admin",
            last_name="User",
            preferred_language="en",
            role="super_admin",
            is_active=True,
            is_verified=True,
            is_superuser=True,
            login_count="0"
        )
        
        # Save to database
        async for session in get_db_session():
            session.add(admin_user)
            await session.commit()
            break
        
        logger.info("✅ Admin user created successfully!")
        logger.info(f"📧 Email: {email}")
        logger.info(f"🔐 Password: {password}")
        logger.info(f"🔑 Role: super_admin")
        logger.info("")
        logger.info("🌟 You can now login at:")
        logger.info("   Frontend: http://localhost:3002")
        logger.info("   API Docs: http://localhost:8000/docs")
        
    except Exception as e:
        logger.error(f"❌ Failed to create admin user: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(create_admin_user())