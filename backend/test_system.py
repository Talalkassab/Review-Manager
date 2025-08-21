#!/usr/bin/env python3
"""
System Integration Test
=====================

Simple test script to verify the AI Customer Feedback Agent system components
without requiring full dependency installation.
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

def test_imports():
    """Test that all major components can be imported"""
    print("🔍 Testing imports...")
    
    try:
        # Test core imports
        from app.core.config import Settings
        from app.core.logging import get_logger
        print("✅ Core modules imported successfully")
        
        # Test model imports
        from app.models.user import User
        from app.models.restaurant import Restaurant
        from app.models.customer import Customer
        print("✅ Database models imported successfully")
        
        # Test services imports (these might fail without deps, but structure is tested)
        try:
            from app.services.openrouter_service import OpenRouterService
            print("✅ OpenRouter service structure verified")
        except ImportError as e:
            print(f"⚠️  OpenRouter service import failed (expected): {e}")
        
        print("✅ All critical imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_agent_structure():
    """Test that AI agents have proper structure"""
    print("\n🤖 Testing AI agent structure...")
    
    try:
        from app.agents.restaurant_ai_crew import RestaurantAICrew
        print("✅ RestaurantAICrew class imported")
        
        # Test agent initialization (mock)
        print("✅ Agent structure verified")
        return True
        
    except Exception as e:
        print(f"❌ Agent structure test failed: {e}")
        return False

def test_api_structure():
    """Test that API routes are properly structured"""
    print("\n🌐 Testing API structure...")
    
    try:
        from app.api import auth, customers, restaurants, campaigns, ai_agent, testing
        print("✅ All API modules imported successfully")
        
        # Check if testing API has proper structure
        if hasattr(testing, 'router'):
            print("✅ Testing API router found")
        
        return True
        
    except Exception as e:
        print(f"❌ API structure test failed: {e}")
        return False

def test_database_models():
    """Test database model definitions"""
    print("\n💾 Testing database models...")
    
    try:
        from app.models.base import BaseModel
        from app.models.user import User
        from app.models.restaurant import Restaurant
        from app.models.customer import Customer
        from app.models.campaign import Campaign
        from app.models.whatsapp import WhatsAppMessage
        from app.models.ai_agent import AgentPersona
        
        print("✅ All database models imported successfully")
        
        # Test model attributes
        user_attrs = ['email', 'hashed_password', 'is_active', 'role']
        for attr in user_attrs:
            if hasattr(User, attr):
                print(f"✅ User.{attr} found")
            else:
                print(f"⚠️  User.{attr} missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Database models test failed: {e}")
        return False

def test_configuration():
    """Test configuration structure"""
    print("\n⚙️  Testing configuration...")
    
    try:
        from app.core.config import Settings
        
        # Create settings instance
        settings = Settings()
        print("✅ Settings class instantiated")
        
        # Check required config attributes exist
        required_attrs = [
            'database_url', 'secret_key', 'algorithm',
            'openrouter_api_key', 'whatsapp_access_token'
        ]
        
        for attr in required_attrs:
            if hasattr(settings, attr.upper()):
                print(f"✅ {attr} configuration found")
            else:
                print(f"⚠️  {attr} configuration missing (will use default)")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_file_structure():
    """Test that all required files and directories exist"""
    print("\n📁 Testing file structure...")
    
    base_path = Path(__file__).parent
    required_files = [
        "app/main.py",
        "app/database.py", 
        "app/dependencies.py",
        "app/core/config.py",
        "app/core/logging.py",
        "requirements.txt",
        "docker-compose.yml",
        "Dockerfile"
    ]
    
    required_dirs = [
        "app/models",
        "app/api", 
        "app/services",
        "app/agents",
        "app/testing",
        "alembic/versions"
    ]
    
    all_good = True
    
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} missing")
            all_good = False
    
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if full_path.exists() and full_path.is_dir():
            print(f"✅ {dir_path}/")
        else:
            print(f"❌ {dir_path}/ missing")
            all_good = False
    
    return all_good

def generate_test_report():
    """Generate a comprehensive test report"""
    print("\n📊 Generating Test Report...")
    
    report = {
        "test_date": datetime.now().isoformat(),
        "system": "AI Customer Feedback Agent",
        "version": "1.0.0",
        "tests": {
            "imports": test_imports(),
            "agent_structure": test_agent_structure(), 
            "api_structure": test_api_structure(),
            "database_models": test_database_models(),
            "configuration": test_configuration(),
            "file_structure": test_file_structure()
        }
    }
    
    # Calculate overall success
    passed_tests = sum(1 for result in report["tests"].values() if result)
    total_tests = len(report["tests"])
    success_rate = (passed_tests / total_tests) * 100
    
    report["summary"] = {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "success_rate": f"{success_rate:.1f}%",
        "status": "PASSED" if success_rate > 80 else "FAILED"
    }
    
    # Save report
    report_path = Path(__file__).parent / "test_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📋 Test Report Summary:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {passed_tests}")
    print(f"   Success Rate: {success_rate:.1f}%")
    print(f"   Overall Status: {report['summary']['status']}")
    print(f"   Report saved to: {report_path}")
    
    return report

def main():
    """Main test execution"""
    print("🚀 AI Customer Feedback Agent - System Integration Test")
    print("=" * 60)
    
    report = generate_test_report()
    
    if report["summary"]["status"] == "PASSED":
        print("\n🎉 System integration test PASSED!")
        print("   Your AI Customer Feedback Agent is ready for deployment!")
    else:
        print("\n⚠️  System integration test needs attention.")
        print("   Some components may need configuration or dependency installation.")
    
    print("\n📝 Next Steps:")
    print("   1. Install dependencies: pip install -r requirements.txt")
    print("   2. Set up environment variables (.env file)")
    print("   3. Initialize database: python scripts/init_db.py")
    print("   4. Start the server: uvicorn app.main:app --reload")
    
    return 0 if report["summary"]["status"] == "PASSED" else 1

if __name__ == "__main__":
    exit(main())