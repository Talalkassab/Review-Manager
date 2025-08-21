#!/usr/bin/env python3
"""
Database seed data script for Restaurant AI Assistant.
Creates initial data including default admin user, sample restaurant, agent personas, and message templates.
"""
import asyncio
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.core.logging import get_logger
from app.database import init_database, db_manager
from app.models import *
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import bcrypt

logger = get_logger(__name__)


class DatabaseSeeder:
    """Handles database seeding with initial data."""
    
    def __init__(self, skip_existing: bool = True, include_samples: bool = False):
        self.skip_existing = skip_existing
        self.include_samples = include_samples
        
    async def create_default_admin_user(self, session: AsyncSession) -> User:
        """Create default admin user."""
        try:
            logger.info("Creating default admin user...")
            
            # Check if admin user already exists
            admin_query = select(User).where(User.email == "admin@restaurant-ai.com")
            result = await session.execute(admin_query)
            existing_admin = result.scalar_one_or_none()
            
            if existing_admin and self.skip_existing:
                logger.info("✓ Default admin user already exists")
                return existing_admin
            
            # Create admin user
            admin_user = User(
                email="admin@restaurant-ai.com",
                first_name="System",
                last_name="Administrator",
                phone_number="+966500000000",
                preferred_language="ar",
                role=UserRoleChoice.SUPER_ADMIN,
                is_active=True,
                is_verified=True,
                is_superuser=True,
                hashed_password=bcrypt.hashpw("admin123!@#".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                bio="Default system administrator account"
            )
            
            session.add(admin_user)
            await session.flush()
            
            logger.info("✓ Default admin user created")
            return admin_user
            
        except Exception as e:
            logger.error(f"Error creating admin user: {str(e)}")
            raise
    
    async def create_default_restaurant(self, session: AsyncSession, admin_user: User) -> Restaurant:
        """Create default restaurant for demo purposes."""
        try:
            logger.info("Creating default restaurant...")
            
            # Check if default restaurant exists
            restaurant_query = select(Restaurant).where(Restaurant.name == "مطعم الذواقة الراقي")
            result = await session.execute(restaurant_query)
            existing_restaurant = result.scalar_one_or_none()
            
            if existing_restaurant and self.skip_existing:
                logger.info("✓ Default restaurant already exists")
                return existing_restaurant
            
            # Operating hours configuration
            operating_hours = {
                "sunday": {"open": "11:00", "close": "23:00"},
                "monday": {"open": "11:00", "close": "23:00"},
                "tuesday": {"open": "11:00", "close": "23:00"},
                "wednesday": {"open": "11:00", "close": "23:00"},
                "thursday": {"open": "11:00", "close": "01:00"},  # Late Friday night
                "friday": {"open": "11:00", "close": "01:00"},   # Late Saturday night
                "saturday": {"open": "11:00", "close": "23:00"}
            }
            
            # Default message templates
            message_templates = {
                "ar": {
                    "greeting": "مرحباً بك في مطعم الذواقة الراقي! نتشرف بزيارتك ونأمل أن تكون تجربتك معنا مميزة.",
                    "follow_up": "نود معرفة رأيك في الوجبة والخدمة التي قدمناها لك اليوم. رضاكم هو هدفنا الأول.",
                    "thank_you": "شكراً جزيلاً لك على الوقت الذي قضيته معنا. نقدر ملاحظاتك القيمة.",
                    "complaint_response": "نعتذر بصدق عن أي إزعاج. سنعمل على حل هذه المشكلة فوراً. يرجى التواصل معنا.",
                    "positive_review_request": "يسعدنا أنك استمتعت بتجربتك! هل يمكنك مشاركة تجربتك الإيجابية على جوجل؟"
                },
                "en": {
                    "greeting": "Welcome to Al-Dhawaqah Fine Restaurant! We're honored by your visit and hope you have an exceptional experience.",
                    "follow_up": "We'd love to hear your thoughts about the food and service we provided today. Your satisfaction is our top priority.",
                    "thank_you": "Thank you so much for the time you spent with us. We appreciate your valuable feedback.",
                    "complaint_response": "We sincerely apologize for any inconvenience. We'll work to resolve this issue immediately. Please contact us.",
                    "positive_review_request": "We're delighted you enjoyed your experience! Could you share your positive experience on Google?"
                }
            }
            
            restaurant = Restaurant(
                name="مطعم الذواقة الراقي",
                name_arabic="مطعم الذواقة الراقي", 
                description="مطعم راقي يقدم أجود الأطباق العربية والعالمية مع خدمة استثنائية",
                description_arabic="مطعم راقي يقدم أجود الأطباق العربية والعالمية مع خدمة استثنائية",
                phone_number="+966112345678",
                email="info@aldhawaqah-restaurant.com",
                website_url="https://aldhawaqah-restaurant.com",
                address="شارع التخصصي، حي الغدير، الرياض 12234",
                address_arabic="شارع التخصصي، حي الغدير، الرياض 12234",
                city="الرياض",
                country="Saudi Arabia",
                postal_code="12234",
                latitude=24.7136,
                longitude=46.6753,
                default_language=LanguageChoice.ARABIC,
                timezone="Asia/Riyadh",
                currency="SAR",
                operating_hours=operating_hours,
                whatsapp_business_phone="+966501234567",
                whatsapp_verified=True,
                whatsapp_active=True,
                ai_enabled=True,
                sentiment_analysis_enabled=True,
                auto_response_enabled=True,
                message_templates=message_templates,
                response_time_target_hours=2,
                review_follow_up_enabled=True,
                max_customers_per_month=5000,
                current_month_customers=0,
                subscription_active=True,
                subscription_expires_at=datetime.utcnow() + timedelta(days=365),
                is_active=True,
                google_business_id="ChIJexample123456789",
                google_reviews_url="https://g.page/aldhawaqah-restaurant/review",
                created_by=admin_user.id
            )
            
            session.add(restaurant)
            await session.flush()
            
            # Associate admin user with restaurant
            admin_user.restaurant_id = restaurant.id
            
            logger.info("✓ Default restaurant created")
            return restaurant
            
        except Exception as e:
            logger.error(f"Error creating default restaurant: {str(e)}")
            raise
    
    async def create_default_agent_personas(self, session: AsyncSession, restaurant: Restaurant, admin_user: User) -> List[AgentPersona]:
        """Create default AI agent personas."""
        try:
            logger.info("Creating default agent personas...")
            
            personas_data = [
                {
                    "name": "سارة - المساعد الودود",
                    "description": "شخصية ودودة ومرحبة، متخصصة في التفاعل مع العملاء الجدد وجمع الملاحظات بأسلوب دافئ",
                    "personality_traits": ["warm", "welcoming", "patient", "culturally_aware", "helpful"],
                    "tone_style": "friendly",
                    "language_style": {
                        "arabic_dialect": "gulf",
                        "english_level": "business", 
                        "emoji_usage": "moderate",
                        "formality_level": "semi_formal"
                    },
                    "response_patterns": {
                        "ar": {
                            "greeting_style": "مرحباً وأهلاً وسهلاً! كيف يمكنني مساعدتك اليوم؟ 😊",
                            "follow_up_style": "نود معرفة رأيك في تجربتك معنا، هل كان كل شيء على ما يرام؟",
                            "thank_you_style": "شكراً جزيلاً لوقتك الثمين! نقدر ملاحظاتك كثيراً 🙏",
                            "complaint_handling": "أعتذر بصدق عن هذه التجربة، سأتأكد من إيصال ملاحظاتك للإدارة فوراً"
                        },
                        "en": {
                            "greeting_style": "Hello and welcome! How can I help you today? 😊",
                            "follow_up_style": "We'd love to hear about your experience with us, was everything satisfactory?",
                            "thank_you_style": "Thank you so much for your valuable time! We really appreciate your feedback 🙏",
                            "complaint_handling": "I sincerely apologize for this experience, I'll make sure to forward your feedback to management immediately"
                        }
                    },
                    "cultural_awareness": {
                        "religious_sensitivity": True,
                        "cultural_holidays": ["eid_al_fitr", "eid_al_adha", "national_day", "ramadan"],
                        "gender_appropriate_interaction": True,
                        "local_customs_awareness": True
                    },
                    "is_default": True
                },
                {
                    "name": "أحمد - المحترف الرسمي", 
                    "description": "شخصية مهنية ورسمية، مناسبة للتعامل مع العملاء المهمين والشكاوى الجدية",
                    "personality_traits": ["professional", "respectful", "solution_focused", "diplomatic", "experienced"],
                    "tone_style": "professional",
                    "language_style": {
                        "arabic_dialect": "standard",
                        "english_level": "advanced",
                        "emoji_usage": "minimal", 
                        "formality_level": "formal"
                    },
                    "response_patterns": {
                        "ar": {
                            "greeting_style": "السلام عليكم ورحمة الله وبركاته، تحية طيبة وبعد",
                            "follow_up_style": "نتشرف بالاستفسار عن مدى رضاكم عن الخدمة المقدمة",
                            "thank_you_style": "نشكركم على منحنا شرف خدمتكم ونقدر ملاحظاتكم القيمة",
                            "complaint_handling": "نعتذر بصدق عن أي قصور، وسنعمل على معالجة الأمر بأسرع وقت ممكن"
                        },
                        "en": {
                            "greeting_style": "Peace be upon you, greetings and salutations",
                            "follow_up_style": "We would be honored to inquire about your satisfaction with our service",
                            "thank_you_style": "We thank you for giving us the honor of serving you and appreciate your valuable feedback",
                            "complaint_handling": "We sincerely apologize for any shortcomings and will work to address the matter as quickly as possible"
                        }
                    },
                    "cultural_awareness": {
                        "religious_sensitivity": True,
                        "cultural_holidays": ["eid_al_fitr", "eid_al_adha", "national_day", "ramadan"],
                        "gender_appropriate_interaction": True,
                        "local_customs_awareness": True
                    },
                    "is_default": False
                }
            ]
            
            created_personas = []
            
            for persona_data in personas_data:
                # Check if persona already exists
                persona_query = select(AgentPersona).where(
                    AgentPersona.name == persona_data["name"],
                    AgentPersona.restaurant_id == restaurant.id
                )
                result = await session.execute(persona_query)
                existing_persona = result.scalar_one_or_none()
                
                if existing_persona and self.skip_existing:
                    logger.info(f"✓ Persona '{persona_data['name']}' already exists")
                    created_personas.append(existing_persona)
                    continue
                
                persona = AgentPersona(
                    name=persona_data["name"],
                    description=persona_data["description"],
                    personality_traits=persona_data["personality_traits"],
                    tone_style=persona_data["tone_style"],
                    language_style=persona_data["language_style"],
                    response_patterns=persona_data["response_patterns"],
                    cultural_awareness=persona_data["cultural_awareness"],
                    is_active=True,
                    is_default=persona_data["is_default"],
                    restaurant_id=restaurant.id,
                    created_by_user_id=admin_user.id
                )
                
                session.add(persona)
                created_personas.append(persona)
                logger.info(f"✓ Created persona: {persona_data['name']}")
            
            await session.flush()
            logger.info(f"✓ Created {len(created_personas)} agent personas")
            return created_personas
            
        except Exception as e:
            logger.error(f"Error creating agent personas: {str(e)}")
            raise
    
    async def create_default_message_flows(self, session: AsyncSession, restaurant: Restaurant, 
                                         personas: List[AgentPersona], admin_user: User) -> List[MessageFlow]:
        """Create default message flows for various scenarios."""
        try:
            logger.info("Creating default message flows...")
            
            default_persona = next((p for p in personas if p.is_default), personas[0])
            
            flows_data = [
                {
                    "name": "متابعة عادية بعد الزيارة",
                    "description": "تدفق رسائل متابعة قياسي للعملاء بعد زيارة المطعم",
                    "flow_type": "standard_followup",
                    "priority": 10,
                    "trigger_conditions": {
                        "customer_type": "all",
                        "time_after_visit": 2,  # 2 hours after visit
                        "previous_sentiment": "none",
                        "visit_amount_range": {"min": 0, "max": 1000}
                    },
                    "message_sequence": [
                        {
                            "step_number": 1,
                            "delay_hours": 2,
                            "message_type": "follow_up",
                            "template_key": "follow_up", 
                            "personalization_variables": ["customer_name", "visit_time"],
                            "expected_response_types": ["feedback", "rating", "complaint"],
                            "escalation_conditions": {
                                "negative_sentiment": True,
                                "no_response_after_hours": 24
                            }
                        },
                        {
                            "step_number": 2,
                            "delay_hours": 48,
                            "message_type": "thank_you",
                            "template_key": "thank_you",
                            "condition": "if_responded",
                            "personalization_variables": ["customer_name", "feedback_summary"]
                        }
                    ],
                    "personalization_rules": {
                        "use_customer_name": True,
                        "consider_previous_visits": True,
                        "adapt_language_preference": True,
                        "respect_time_zone": True
                    },
                    "response_intelligence": {
                        "sentiment_analysis": True,
                        "auto_escalation_threshold": -0.3,
                        "positive_response_actions": ["request_google_review"],
                        "negative_response_actions": ["escalate_to_human", "schedule_follow_up"]
                    }
                },
                {
                    "name": "متابعة العملاء المميزين",
                    "description": "تدفق خاص للعملاء ذوي الإنفاق العالي أو الزيارات المتكررة",
                    "flow_type": "vip_customer",
                    "priority": 20,
                    "trigger_conditions": {
                        "customer_type": "vip",
                        "time_after_visit": 1,  # 1 hour for VIPs
                        "visit_amount_range": {"min": 500, "max": float('inf')},
                        "is_repeat_customer": True
                    },
                    "message_sequence": [
                        {
                            "step_number": 1,
                            "delay_hours": 1,
                            "message_type": "vip_follow_up",
                            "template_key": "vip_greeting",
                            "personalization_variables": ["customer_name", "visit_count", "favorite_items"],
                            "escalation_conditions": {
                                "negative_sentiment": True,
                                "no_response_after_hours": 12
                            }
                        },
                        {
                            "step_number": 2,
                            "delay_hours": 24,
                            "message_type": "personal_touch",
                            "template_key": "vip_personal_message",
                            "condition": "if_positive_response",
                            "personalization_variables": ["customer_name", "manager_name"]
                        }
                    ],
                    "personalization_rules": {
                        "use_customer_name": True,
                        "mention_visit_history": True,
                        "reference_preferences": True,
                        "manager_personal_touch": True
                    },
                    "response_intelligence": {
                        "sentiment_analysis": True,
                        "auto_escalation_threshold": -0.2,  # More sensitive for VIPs
                        "positive_response_actions": ["request_google_review", "offer_exclusive_discount"],
                        "negative_response_actions": ["immediate_escalation", "manager_notification"]
                    }
                },
                {
                    "name": "حل الشكاوى والمشاكل",
                    "description": "تدفق متخصص للتعامل مع الشكاوى والمشاكل",
                    "flow_type": "complaint_resolution",
                    "priority": 30,
                    "trigger_conditions": {
                        "customer_type": "all",
                        "previous_sentiment": "negative",
                        "complaint_detected": True
                    },
                    "message_sequence": [
                        {
                            "step_number": 1,
                            "delay_hours": 0.25,  # 15 minutes immediate response
                            "message_type": "apology",
                            "template_key": "complaint_response",
                            "personalization_variables": ["customer_name", "complaint_summary"],
                            "escalation_conditions": {
                                "always_escalate": True
                            }
                        },
                        {
                            "step_number": 2,
                            "delay_hours": 4,
                            "message_type": "resolution_update",
                            "template_key": "resolution_progress",
                            "condition": "manual_approval",
                            "personalization_variables": ["customer_name", "resolution_steps"]
                        },
                        {
                            "step_number": 3,
                            "delay_hours": 48,
                            "message_type": "follow_up_resolution",
                            "template_key": "post_resolution_check",
                            "condition": "resolution_completed",
                            "personalization_variables": ["customer_name", "resolution_outcome"]
                        }
                    ],
                    "personalization_rules": {
                        "use_formal_tone": True,
                        "acknowledge_specific_issue": True,
                        "provide_direct_contact": True,
                        "timeline_commitments": True
                    },
                    "response_intelligence": {
                        "sentiment_analysis": True,
                        "human_handoff_required": True,
                        "manager_notification": True,
                        "priority_handling": True
                    }
                }
            ]
            
            created_flows = []
            
            for flow_data in flows_data:
                # Check if flow already exists
                flow_query = select(MessageFlow).where(
                    MessageFlow.name == flow_data["name"],
                    MessageFlow.restaurant_id == restaurant.id
                )
                result = await session.execute(flow_query)
                existing_flow = result.scalar_one_or_none()
                
                if existing_flow and self.skip_existing:
                    logger.info(f"✓ Message flow '{flow_data['name']}' already exists")
                    created_flows.append(existing_flow)
                    continue
                
                flow = MessageFlow(
                    name=flow_data["name"],
                    description=flow_data["description"],
                    flow_type=flow_data["flow_type"],
                    is_active=True,
                    priority=flow_data["priority"],
                    trigger_conditions=flow_data["trigger_conditions"],
                    message_sequence=flow_data["message_sequence"],
                    personalization_rules=flow_data["personalization_rules"],
                    response_intelligence=flow_data["response_intelligence"],
                    restaurant_id=restaurant.id,
                    default_persona_id=default_persona.id,
                    created_by_user_id=admin_user.id
                )
                
                session.add(flow)
                created_flows.append(flow)
                logger.info(f"✓ Created message flow: {flow_data['name']}")
            
            await session.flush()
            logger.info(f"✓ Created {len(created_flows)} message flows")
            return created_flows
            
        except Exception as e:
            logger.error(f"Error creating message flows: {str(e)}")
            raise
    
    async def create_sample_data(self, session: AsyncSession, restaurant: Restaurant) -> None:
        """Create sample customers and interactions for demonstration."""
        if not self.include_samples:
            return
            
        try:
            logger.info("Creating sample data...")
            
            # Sample customers
            sample_customers = [
                {
                    "first_name": "أحمد",
                    "last_name": "العثمان", 
                    "phone_number": "+966501111111",
                    "email": "ahmed.othman@example.com",
                    "preferred_language": LanguageChoice.ARABIC,
                    "visit_date": datetime.utcnow() - timedelta(hours=3),
                    "table_number": "T15",
                    "server_name": "سارة أحمد",
                    "party_size": 4,
                    "order_total": 380.0,
                    "special_requests": "بدون بصل في السلطة",
                    "status": CustomerStatusChoice.PENDING
                },
                {
                    "first_name": "فاطمة",
                    "last_name": "المطيري",
                    "phone_number": "+966502222222", 
                    "email": "fatma.almutairi@example.com",
                    "preferred_language": LanguageChoice.ARABIC,
                    "visit_date": datetime.utcnow() - timedelta(days=1, hours=2),
                    "table_number": "T08",
                    "server_name": "محمد علي",
                    "party_size": 2,
                    "order_total": 195.0,
                    "status": CustomerStatusChoice.RESPONDED,
                    "feedback_text": "الطعام كان لذيذ جداً والخدمة ممتازة، شكراً لكم",
                    "feedback_sentiment": SentimentChoice.POSITIVE,
                    "rating": 5,
                    "feedback_received_at": datetime.utcnow() - timedelta(hours=22)
                },
                {
                    "first_name": "John",
                    "last_name": "Smith",
                    "phone_number": "+966503333333",
                    "email": "john.smith@example.com", 
                    "preferred_language": LanguageChoice.ENGLISH,
                    "visit_date": datetime.utcnow() - timedelta(days=2, hours=5),
                    "table_number": "T12",
                    "server_name": "أمين خالد",
                    "party_size": 3,
                    "order_total": 425.0,
                    "status": CustomerStatusChoice.COMPLETED,
                    "feedback_text": "Excellent food and service! The Arabic coffee was outstanding.",
                    "feedback_sentiment": SentimentChoice.POSITIVE,
                    "rating": 5,
                    "feedback_received_at": datetime.utcnow() - timedelta(days=1, hours=8),
                    "google_review_requested_at": datetime.utcnow() - timedelta(days=1, hours=6),
                    "google_review_link_sent": True
                }
            ]
            
            for customer_data in sample_customers:
                customer = Customer(
                    restaurant_id=restaurant.id,
                    **customer_data
                )
                session.add(customer)
            
            await session.flush()
            logger.info("✓ Created sample customer data")
            
        except Exception as e:
            logger.error(f"Error creating sample data: {str(e)}")
            raise
    
    async def seed_database(self) -> bool:
        """Run complete database seeding process."""
        try:
            logger.info("🌱 Starting database seeding...")
            
            await init_database()
            
            async with db_manager.get_session() as session:
                # Create default admin user
                admin_user = await self.create_default_admin_user(session)
                
                # Create default restaurant
                restaurant = await self.create_default_restaurant(session, admin_user)
                
                # Create agent personas
                personas = await self.create_default_agent_personas(session, restaurant, admin_user)
                
                # Create message flows
                flows = await self.create_default_message_flows(session, restaurant, personas, admin_user)
                
                # Create sample data if requested
                if self.include_samples:
                    await self.create_sample_data(session, restaurant)
                
                # Commit all changes
                await session.commit()
                
                logger.info("✅ Database seeding completed successfully")
                logger.info(f"Created: 1 admin user, 1 restaurant, {len(personas)} personas, {len(flows)} message flows")
                
                if self.include_samples:
                    logger.info("Sample customer data included for demonstration")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Database seeding failed: {str(e)}")
            return False
        
        finally:
            await db_manager.close()


async def main():
    """Main seeding function with command line arguments."""
    parser = argparse.ArgumentParser(description="Seed Restaurant AI Assistant database with initial data")
    parser.add_argument("--force", action="store_true", 
                       help="Force recreate existing data")
    parser.add_argument("--samples", action="store_true", 
                       help="Include sample customer data for demonstration")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Enable verbose output")
    
    args = parser.parse_args()
    
    seeder = DatabaseSeeder(
        skip_existing=not args.force,
        include_samples=args.samples
    )
    
    success = await seeder.seed_database()
    
    if success:
        logger.info("🎉 Database seeding completed successfully!")
        if args.samples:
            logger.info("📊 Sample data created for demonstration purposes")
        logger.info("🔑 Admin credentials: admin@restaurant-ai.com / admin123!@#")
        sys.exit(0)
    else:
        logger.error("💥 Database seeding failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())