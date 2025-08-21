"""
Restaurant AI Customer Agent - Simplified Main Application
=========================================================

Simplified main application for testing without full dependencies.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import json

# Create FastAPI application
app = FastAPI(
    title="Restaurant AI Customer Agent",
    description="""
    🤖 **Restaurant AI Customer Agent**
    
    Intelligent customer feedback and engagement system for restaurants with:
    
    - 🌍 **Bilingual Support**: Arabic (RTL) and English
    - 🤖 **AI Agents**: 9 specialized agents for customer interaction
    - 📱 **WhatsApp Integration**: Business API for customer communication  
    - 🧪 **Testing Framework**: Comprehensive agent testing suite
    - 📊 **Analytics**: Performance tracking and insights
    - 🔐 **Authentication**: Role-based access control
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Restaurant AI Customer Agent",
        "message": "🤖 Restaurant AI Customer Agent API",
        "status": "running",
        "version": "1.0.0",
        "features": {
            "ai_agents": True,
            "whatsapp": False,
            "testing": True,
        },
        "docs": "/docs",
        "timestamp": datetime.now().isoformat(),
        "languages": ["Arabic", "English"],
        "supported_languages": ["ar", "en"],
        "environment": "development"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "restaurant-ai-agent",
        "version": "1.0.0",
        "database": "sqlite",
        "ai_agents": "available",
        "testing_framework": "enabled"
    }


# Authentication endpoints
@app.post("/api/v1/auth/login")
async def login(request: Request):
    """Mock login endpoint"""
    try:
        body = await request.json()
    except:
        body = {}
    
    return {
        "access_token": "mock-jwt-token-12345",
        "token_type": "bearer",
        "user": {
            "id": "1",
            "email": body.get("email", "owner@restaurant.com"), 
            "name": "Ahmed Al-Restaurant",
            "role": "restaurant_owner",
            "full_name": "Ahmed Al-Restaurant"
        }
    }


@app.post("/api/v1/auth/register")
async def register(request: Request):
    """Mock register endpoint"""
    try:
        body = await request.json()
    except:
        body = {}
    
    return {
        "message": "User registered successfully",
        "user": {
            "id": "2",
            "email": body.get("email", "new@restaurant.com"),
            "name": body.get("name", "New User"),
            "role": "restaurant_owner"
        }
    }


@app.get("/api/v1/auth/me")
async def get_current_user():
    """Mock current user endpoint"""
    return {
        "id": "1",
        "email": "owner@restaurant.com",
        "name": "Ahmed Al-Restaurant", 
        "full_name": "Ahmed Al-Restaurant",
        "role": "restaurant_owner",
        "is_active": True,
        "restaurant": {
            "id": "1",
            "name": "مطعم الأصالة",
            "name_english": "Al-Asala Restaurant",
            "phone": "+966501234567",
            "address": "الرياض، المملكة العربية السعودية"
        }
    }


# Customer endpoints
@app.get("/api/v1/customers")
async def get_customers():
    """Mock customers list"""
    return {
        "customers": [
            {
                "id": "1",
                "name": "محمد أحمد",
                "phone": "+966501111111",
                "language_preference": "arabic",
                "last_interaction": "2024-01-15T10:30:00",
                "visit_count": 5,
                "sentiment": "positive",
                "total_spent": 450.0,
                "email": "mohammed@example.com"
            },
            {
                "id": "2", 
                "name": "Sarah Johnson",
                "phone": "+966502222222",
                "language_preference": "english",
                "last_interaction": "2024-01-14T15:45:00",
                "visit_count": 3,
                "sentiment": "neutral",
                "total_spent": 280.0,
                "email": "sarah@example.com"
            },
            {
                "id": "3",
                "name": "فاطمة علي", 
                "phone": "+966503333333",
                "language_preference": "arabic",
                "last_interaction": "2024-01-13T19:20:00",
                "visit_count": 8,
                "sentiment": "positive",
                "total_spent": 720.0,
                "email": "fatima@example.com"
            },
            {
                "id": "4",
                "name": "عبدالله محمد",
                "phone": "+966504444444",
                "language_preference": "arabic",
                "last_interaction": "2024-01-12T12:15:00",
                "visit_count": 2,
                "sentiment": "positive",
                "total_spent": 190.0,
                "email": "abdullah@example.com"
            }
        ],
        "total": 4,
        "page": 1,
        "size": 20
    }


@app.post("/api/v1/customers")
async def create_customer(request: Request):
    """Mock customer creation"""
    try:
        body = await request.json()
        name = body.get("name", "New Customer")
    except:
        name = "New Customer"
    
    return {
        "id": "5",
        "name": name,
        "phone": "+966505555555",
        "language_preference": "arabic",
        "message": "Customer created successfully"
    }


@app.get("/api/v1/customers/{customer_id}")
async def get_customer(customer_id: str):
    """Mock get customer by ID"""
    return {
        "id": customer_id,
        "name": "محمد أحمد",
        "phone": "+966501111111",
        "language_preference": "arabic",
        "last_interaction": "2024-01-15T10:30:00",
        "visit_count": 5,
        "sentiment": "positive",
        "feedback_history": [
            {
                "date": "2024-01-15",
                "rating": 5,
                "comment": "الطعام ممتاز والخدمة رائعة",
                "sentiment": "positive"
            }
        ]
    }


# AI Chat endpoints
@app.post("/api/v1/ai-agent/chat")
async def ai_chat(request: Request):
    """Mock AI chat endpoint"""
    try:
        body = await request.json()
        query = body.get("query", "")
    except:
        query = ""
    
    # Simple mock responses based on query content
    if "عملاء" in query or "customers" in query.lower():
        response = {
            "response": {
                "text": f"تم العثور على 4 عملاء نشطين. إليك العملاء الأكثر نشاطاً:\n\n👤 محمد أحمد - 5 زيارات (450 ريال)\n👤 فاطمة علي - 8 زيارات (720 ريال)\n👤 Sarah Johnson - 3 زيارات (280 ريال)\n👤 عبدالله محمد - 2 زيارة (190 ريال)",
                "type": "customer_list",
                "language": "arabic"
            },
            "actions": ["show_customers"],
            "suggestions": [
                "أرسل رسالة ترحيب للعملاء الجدد",
                "أظهر العملاء الذين لم يزوروا مؤخراً",
                "إحصائيات مبيعات العملاء"
            ]
        }
    elif "حملة" in query or "campaign" in query.lower():
        response = {
            "response": {
                "text": "يمكنني مساعدتك في إنشاء حملة تسويقية جديدة. ما نوع الحملة التي تريد إنشاءها؟",
                "type": "campaign_help", 
                "language": "arabic"
            },
            "suggestions": [
                "حملة ترحيب للعملاء الجدد",
                "حملة عروض خاصة", 
                "حملة طلب تقييمات"
            ]
        }
    elif "تقرير" in query or "report" in query.lower():
        response = {
            "response": {
                "text": "📊 تقرير الأداء اليومي:\n\n• العملاء الجدد: 2\n• الرسائل المرسلة: 15\n• معدل الاستجابة: 78%\n• التقييم المتوسط: 4.3/5\n• المشاعر الإيجابية: 85%",
                "type": "performance_report",
                "language": "arabic"
            },
            "suggestions": [
                "تقرير مفصل للأسبوع",
                "مقارنة مع الشهر الماضي",
                "تحليل سلوك العملاء"
            ]
        }
    else:
        response = {
            "response": {
                "text": f"شكراً لك على سؤالك: {query}\n\n🤖 أنا مساعدك الذكي لإدارة المطعم. يمكنني مساعدتك في:\n\n📊 عرض إحصائيات العملاء\n💬 إنشاء حملات التواصل\n📱 إدارة رسائل واتساب\n📈 تحليل الأداء\n🎯 اختبار الوكلاء الذكيين",
                "type": "general_help",
                "language": "arabic"
            },
            "suggestions": [
                "أرني العملاء الجدد",
                "إحصائيات الأداء اليوم",
                "إنشاء حملة جديدة",
                "اختبر الوكيل الذكي"
            ]
        }
    
    return response


# Testing endpoints
@app.post("/api/v1/testing/conversation-playground")
async def test_conversation(request: Request):
    """Mock conversation testing"""
    try:
        body = await request.json()
        message = body.get("message", "مرحبا")
        persona = body.get("persona", "friendly")
    except:
        message = "مرحبا"
        persona = "friendly"
    
    # Generate different responses based on persona
    if persona == "friendly":
        agent_text = f"مرحباً وأهلاً وسهلاً! 😊 شكراً لك على رسالتك: {message}. كيف يمكنني مساعدتك اليوم؟"
        personality_score = 95
    else:
        agent_text = f"السلام عليكم ومرحباً بك. تلقيت رسالتك: {message}. كيف يمكنني خدمتك؟"
        personality_score = 90
    
    return {
        "session_id": f"test-session-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "agent_response": {
            "text": agent_text,
            "language": "arabic",
            "confidence": 0.95,
            "persona": persona
        },
        "performance_metrics": {
            "response_time_ms": 1200,
            "cultural_sensitivity_score": 96,
            "language_appropriateness": 98,
            "persona_consistency": personality_score
        },
        "cultural_analysis": {
            "greeting_style": "traditional_arabic",
            "formality_level": "formal" if persona == "professional" else "friendly",
            "cultural_references": ["traditional_greeting", "respectful_tone"]
        },
        "suggestions": [
            "ممتاز! الرد مناسب ثقافياً",
            "زمن الاستجابة جيد جداً", 
            "يمكن إضافة المزيد من التخصيص"
        ]
    }


@app.post("/api/v1/testing/ab-test")
async def create_ab_test(request: Request):
    """Mock A/B testing creation"""
    try:
        body = await request.json()
        test_name = body.get("name", "Test Campaign")
    except:
        test_name = "Test Campaign"
    
    return {
        "test_id": f"ab-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "status": "launched",
        "name": test_name,
        "created_at": datetime.now().isoformat(),
        "estimated_completion": datetime.now().isoformat(),
        "variants_count": 2,
        "target_sample_size": 100
    }


@app.get("/api/v1/testing/ab-test/{test_id}/status")
async def get_ab_test_status(test_id: str):
    """Mock A/B test status"""
    return {
        "test_id": test_id,
        "status": "running",
        "progress_percentage": 65,
        "participants_enrolled": 85,
        "target_participants": 100,
        "preliminary_results": {
            "variant_a": {
                "name": "Friendly Ahmad",
                "response_rate": 23.5,
                "satisfaction_score": 4.2,
                "participants": 42
            },
            "variant_b": {
                "name": "Professional Sarah",
                "response_rate": 19.8,
                "satisfaction_score": 4.0,
                "participants": 43
            }
        },
        "statistical_significance": {
            "confidence_level": 95,
            "p_value": 0.12,
            "is_significant": False
        }
    }


@app.get("/api/v1/testing/health")
async def testing_health():
    """Testing framework health"""
    return {
        "service": "Agent Testing Framework",
        "status": "healthy", 
        "components": {
            "conversation_playground": {"status": "healthy", "response_time": 150},
            "ab_testing": {"status": "healthy", "active_tests": 3},
            "performance_monitoring": {"status": "healthy", "metrics_collected": 1250},
            "scenario_testing": {"status": "healthy", "scenarios_available": 12}
        },
        "checked_at": datetime.now().isoformat()
    }


# Dashboard stats endpoint
@app.get("/api/v1/dashboard/stats")
async def get_dashboard_stats():
    """Mock dashboard statistics"""
    return {
        "customers": {
            "total": 4,
            "new_today": 2,
            "active_this_week": 4
        },
        "messages": {
            "sent_today": 15,
            "response_rate": 78.5,
            "avg_response_time": "2.3 hours"
        },
        "satisfaction": {
            "average_rating": 4.3,
            "positive_sentiment": 85,
            "negative_sentiment": 5,
            "neutral_sentiment": 10
        },
        "recent_activity": [
            {
                "type": "customer_added",
                "customer": "عبدالله محمد",
                "time": "2024-01-15T10:30:00"
            },
            {
                "type": "message_sent", 
                "customer": "محمد أحمد",
                "time": "2024-01-15T09:15:00"
            },
            {
                "type": "feedback_received",
                "customer": "Sarah Johnson",
                "rating": 5,
                "time": "2024-01-15T08:45:00"
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)