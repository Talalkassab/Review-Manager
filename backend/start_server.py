#!/usr/bin/env python3
"""
Start Server Script
==================
Simple script to initialize database and start the FastAPI server
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

def create_database():
    """Create database tables"""
    print("🗄️  Creating database tables...")
    try:
        from app.database import Base, engine, get_async_session
        from app.models import user, restaurant, customer, campaign, whatsapp, ai_agent
        
        # Import asyncio for async operations
        import asyncio
        
        async def create_tables():
            async with engine.begin() as conn:
                # Drop all tables first (for fresh start)
                await conn.run_sync(Base.metadata.drop_all)
                # Create all tables
                await conn.run_sync(Base.metadata.create_all)
                print("✅ Database tables created successfully")
        
        # Run the async function
        asyncio.run(create_tables())
        return True
        
    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        print("📝 Using SQLite database fallback...")
        return False

def create_sample_data():
    """Create sample data for testing"""
    print("📋 Creating sample data...")
    try:
        from app.models.user import User
        from app.models.restaurant import Restaurant
        from app.models.customer import Customer
        from app.database import get_async_session
        import asyncio
        from passlib.context import CryptContext
        import uuid
        
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        async def create_samples():
            async for db in get_async_session():
                try:
                    # Create sample restaurant owner
                    sample_user = User(
                        id=uuid.uuid4(),
                        email="owner@restaurant.com",
                        hashed_password=pwd_context.hash("password123"),
                        is_active=True,
                        role="restaurant_owner",
                        full_name="Ahmed Al-Restaurant"
                    )
                    db.add(sample_user)
                    await db.commit()
                    await db.refresh(sample_user)
                    
                    # Create sample restaurant
                    sample_restaurant = Restaurant(
                        id=uuid.uuid4(),
                        name="مطعم الأصالة",
                        name_english="Al-Asala Restaurant",
                        owner_id=sample_user.id,
                        phone="+966501234567",
                        address="الرياض، المملكة العربية السعودية",
                        cuisine_type="traditional_arabic",
                        is_active=True
                    )
                    db.add(sample_restaurant)
                    await db.commit()
                    
                    # Create sample customers
                    customers = [
                        Customer(
                            id=uuid.uuid4(),
                            name="محمد أحمد",
                            phone="+966501111111",
                            restaurant_id=sample_restaurant.id,
                            language_preference="arabic"
                        ),
                        Customer(
                            id=uuid.uuid4(),
                            name="Sarah Johnson",
                            phone="+966502222222", 
                            restaurant_id=sample_restaurant.id,
                            language_preference="english"
                        ),
                        Customer(
                            id=uuid.uuid4(),
                            name="فاطمة علي",
                            phone="+966503333333",
                            restaurant_id=sample_restaurant.id,
                            language_preference="arabic"
                        )
                    ]
                    
                    for customer in customers:
                        db.add(customer)
                    
                    await db.commit()
                    print("✅ Sample data created successfully")
                    print(f"   📧 Login: owner@restaurant.com")
                    print(f"   🔑 Password: password123")
                    
                except Exception as e:
                    await db.rollback()
                    print(f"⚠️  Sample data creation failed: {e}")
                finally:
                    await db.close()
                break
        
        asyncio.run(create_samples())
        return True
        
    except Exception as e:
        print(f"❌ Sample data creation failed: {e}")
        return False

def start_uvicorn_server():
    """Start the FastAPI server using uvicorn"""
    print("🚀 Starting FastAPI server...")
    try:
        # Try to use uvicorn from the installed packages
        import uvicorn
        
        # Check if main app exists
        app_path = Path(__file__).parent / "app" / "main.py"
        if not app_path.exists():
            print("❌ main.py not found, creating minimal app...")
            create_minimal_app()
        
        print("🌐 Server starting at: http://localhost:8000")
        print("📚 API docs available at: http://localhost:8000/docs")
        print("🛑 Press Ctrl+C to stop the server")
        
        # Start the server
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except ImportError:
        print("❌ uvicorn not found, trying alternative start method...")
        try:
            subprocess.run([
                sys.executable, "-m", "uvicorn", 
                "app.main:app", 
                "--host", "0.0.0.0", 
                "--port", "8000", 
                "--reload"
            ])
        except Exception as e:
            print(f"❌ Failed to start server: {e}")

def create_minimal_app():
    """Create a minimal FastAPI app if main.py is missing"""
    app_dir = Path(__file__).parent / "app"
    main_file = app_dir / "main.py"
    
    minimal_app_content = '''
"""
Minimal FastAPI Application
==========================
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Restaurant AI Customer Agent",
    description="AI-powered customer feedback and engagement system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Restaurant AI Customer Agent API",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "restaurant-ai-agent"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
    
    main_file.write_text(minimal_app_content)
    print("✅ Created minimal FastAPI app")

def main():
    """Main setup and start function"""
    print("🎯 Restaurant AI Customer Agent - Server Setup")
    print("=" * 50)
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Step 1: Create database
    print("\n📋 Step 1: Setting up database...")
    create_database()
    
    # Step 2: Create sample data
    print("\n📋 Step 2: Creating sample data...")
    create_sample_data()
    
    # Step 3: Start server
    print("\n📋 Step 3: Starting server...")
    start_uvicorn_server()

if __name__ == "__main__":
    main()
'''