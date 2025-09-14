#!/usr/bin/env python3
"""
Quick test script for the Restaurant AI Agent
Run this to test if OpenRouter integration is working
"""
import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_ai_agent():
    """Test the intelligent AI agent with sample queries"""
    
    print("🤖 Testing Restaurant AI Agent...")
    print("=" * 50)
    
    try:
        # Import the AI agent
        from backend.app.services.restaurant_ai_agent import restaurant_ai_agent
        from backend.app.core.config import settings
        
        # Check if OpenRouter is configured
        api_key = getattr(settings.openrouter, 'OPENROUTER_API_KEY', None)
        if not api_key or api_key == "your-openrouter-api-key-here":
            print("❌ OpenRouter API key not configured")
            print("   Set OPENROUTER_API_KEY environment variable")
            return
        else:
            print(f"✅ OpenRouter API key configured: ***{api_key[-4:]}")
        
        # Test questions
        test_questions = [
            "مرحبا",  # Hello
            "أيش أحسن طبق عندكم؟",  # What's your best dish?
            "كم سعر الكبسة؟",  # How much is kabsa?
            "أريد معرفة قائمة الطعام",  # I want to know the menu
            "ما هو الطبق الأكثر مبيعاً؟",  # What's the best-selling dish?
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n📤 Test {i}: {question}")
            print("-" * 30)
            
            try:
                # Generate AI response
                response = await restaurant_ai_agent.generate_intelligent_response(
                    message=question,
                    conversation_history=[],
                    customer_id="test_customer",
                    language="ar"
                )
                
                print(f"📨 AI Response: {response}")
                
            except Exception as e:
                print(f"❌ Error: {str(e)}")
        
        print("\n" + "=" * 50)
        print("✅ AI Agent test completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("   Make sure you're in the correct directory")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_ai_agent())