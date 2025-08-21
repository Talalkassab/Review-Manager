"""Seed default data and configurations

Revision ID: 003
Revises: 002
Create Date: 2024-01-15 13:00:00.000000

"""
from typing import Sequence, Union
from datetime import datetime, timedelta
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed database with default configuration data."""
    
    # Create a connection to execute raw SQL
    connection = op.get_bind()
    
    # Default admin user ID
    admin_user_id = str(uuid.uuid4())
    
    # Default restaurant ID
    restaurant_id = str(uuid.uuid4())
    
    # Insert default admin user
    connection.execute(sa.text("""
        INSERT INTO users (
            id, created_at, updated_at, is_deleted, deleted_at, created_by, updated_by,
            email, hashed_password, is_active, is_superuser, is_verified, 
            first_name, last_name, phone_number, preferred_language, role,
            restaurant_id, last_login_at, login_count, bio
        ) VALUES (
            :admin_id, :now, :now, false, NULL, NULL, NULL,
            'admin@restaurant-ai.com', 
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LdDMoJCFdnJH9B4s2',  -- 'admin123!@#'
            true, true, true,
            'System', 'Administrator', '+966500000000', 'ar', 'SUPER_ADMIN',
            NULL, NULL, '0', 'Default system administrator account'
        )
    """), {
        'admin_id': admin_user_id,
        'now': datetime.utcnow()
    })
    
    # Insert default restaurant
    connection.execute(sa.text("""
        INSERT INTO restaurants (
            id, created_at, updated_at, is_deleted, deleted_at, created_by, updated_by,
            name, name_arabic, description, description_arabic,
            phone_number, email, website_url,
            address, address_arabic, city, country, postal_code, latitude, longitude,
            default_language, timezone, currency, operating_hours,
            whatsapp_business_phone, whatsapp_verified, whatsapp_active,
            ai_enabled, sentiment_analysis_enabled, auto_response_enabled,
            message_templates, response_time_target_hours, review_follow_up_enabled,
            max_customers_per_month, current_month_customers, 
            subscription_active, subscription_expires_at,
            is_active, is_featured, google_business_id, google_reviews_url
        ) VALUES (
            :restaurant_id, :now, :now, false, NULL, :admin_id, NULL,
            'مطعم الذواقة الراقي', 'مطعم الذواقة الراقي',
            'مطعم راقي يقدم أجود الأطباق العربية والعالمية مع خدمة استثنائية',
            'مطعم راقي يقدم أجود الأطباق العربية والعالمية مع خدمة استثنائية',
            '+966112345678', 'info@aldhawaqah-restaurant.com', 'https://aldhawaqah-restaurant.com',
            'شارع التخصصي، حي الغدير، الرياض 12234', 'شارع التخصصي، حي الغدير، الرياض 12234',
            'الرياض', 'Saudi Arabia', '12234', 24.7136, 46.6753,
            'ar', 'Asia/Riyadh', 'SAR', :operating_hours,
            '+966501234567', true, true,
            true, true, true,
            :message_templates, 2, true,
            5000, 0,
            true, :subscription_expires,
            true, false, 'ChIJexample123456789', 'https://g.page/aldhawaqah-restaurant/review'
        )
    """), {
        'restaurant_id': restaurant_id,
        'admin_id': admin_user_id,
        'now': datetime.utcnow(),
        'subscription_expires': datetime.utcnow() + timedelta(days=365),
        'operating_hours': '''
        {
            "sunday": {"open": "11:00", "close": "23:00"},
            "monday": {"open": "11:00", "close": "23:00"},
            "tuesday": {"open": "11:00", "close": "23:00"},
            "wednesday": {"open": "11:00", "close": "23:00"},
            "thursday": {"open": "11:00", "close": "01:00"},
            "friday": {"open": "11:00", "close": "01:00"},
            "saturday": {"open": "11:00", "close": "23:00"}
        }''',
        'message_templates': '''
        {
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
        }'''
    })
    
    # Update admin user with restaurant_id
    connection.execute(sa.text("""
        UPDATE users SET restaurant_id = :restaurant_id WHERE id = :admin_id
    """), {
        'restaurant_id': restaurant_id,
        'admin_id': admin_user_id
    })
    
    # Default agent personas
    sarah_persona_id = str(uuid.uuid4())
    ahmad_persona_id = str(uuid.uuid4())
    
    # Insert default friendly persona (Sarah)
    connection.execute(sa.text("""
        INSERT INTO agent_personas (
            id, created_at, updated_at, is_deleted, deleted_at, created_by, updated_by,
            name, description, is_active, is_default,
            personality_traits, tone_style, language_style, response_patterns, cultural_awareness,
            usage_count, success_rate, average_response_time_seconds, conversion_metrics,
            restaurant_id, created_by_user_id
        ) VALUES (
            :persona_id, :now, :now, false, NULL, NULL, NULL,
            'سارة - المساعد الودود',
            'شخصية ودودة ومرحبة، متخصصة في التفاعل مع العملاء الجدد وجمع الملاحظات بأسلوب دافئ',
            true, true,
            :personality_traits, 'friendly', :language_style, :response_patterns, :cultural_awareness,
            0, 0.0, 0.0, NULL,
            :restaurant_id, :admin_id
        )
    """), {
        'persona_id': sarah_persona_id,
        'restaurant_id': restaurant_id,
        'admin_id': admin_user_id,
        'now': datetime.utcnow(),
        'personality_traits': '["warm", "welcoming", "patient", "culturally_aware", "helpful"]',
        'language_style': '''
        {
            "arabic_dialect": "gulf",
            "english_level": "business",
            "emoji_usage": "moderate",
            "formality_level": "semi_formal"
        }''',
        'response_patterns': '''
        {
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
        }''',
        'cultural_awareness': '''
        {
            "religious_sensitivity": true,
            "cultural_holidays": ["eid_al_fitr", "eid_al_adha", "national_day", "ramadan"],
            "gender_appropriate_interaction": true,
            "local_customs_awareness": true
        }'''
    })
    
    # Insert professional persona (Ahmad)
    connection.execute(sa.text("""
        INSERT INTO agent_personas (
            id, created_at, updated_at, is_deleted, deleted_at, created_by, updated_by,
            name, description, is_active, is_default,
            personality_traits, tone_style, language_style, response_patterns, cultural_awareness,
            usage_count, success_rate, average_response_time_seconds, conversion_metrics,
            restaurant_id, created_by_user_id
        ) VALUES (
            :persona_id, :now, :now, false, NULL, NULL, NULL,
            'أحمد - المحترف الرسمي',
            'شخصية مهنية ورسمية، مناسبة للتعامل مع العملاء المهمين والشكاوى الجدية',
            true, false,
            :personality_traits, 'professional', :language_style, :response_patterns, :cultural_awareness,
            0, 0.0, 0.0, NULL,
            :restaurant_id, :admin_id
        )
    """), {
        'persona_id': ahmad_persona_id,
        'restaurant_id': restaurant_id,
        'admin_id': admin_user_id,
        'now': datetime.utcnow(),
        'personality_traits': '["professional", "respectful", "solution_focused", "diplomatic", "experienced"]',
        'language_style': '''
        {
            "arabic_dialect": "standard",
            "english_level": "advanced",
            "emoji_usage": "minimal",
            "formality_level": "formal"
        }''',
        'response_patterns': '''
        {
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
        }''',
        'cultural_awareness': '''
        {
            "religious_sensitivity": true,
            "cultural_holidays": ["eid_al_fitr", "eid_al_adha", "national_day", "ramadan"],
            "gender_appropriate_interaction": true,
            "local_customs_awareness": true
        }'''
    })
    
    # Default message flows
    standard_flow_id = str(uuid.uuid4())
    vip_flow_id = str(uuid.uuid4())
    complaint_flow_id = str(uuid.uuid4())
    
    # Standard follow-up flow
    connection.execute(sa.text("""
        INSERT INTO message_flows (
            id, created_at, updated_at, is_deleted, deleted_at, created_by, updated_by,
            name, description, flow_type, is_active, priority,
            trigger_conditions, message_sequence, personalization_rules, response_intelligence,
            execution_count, completion_rate, average_customer_satisfaction,
            restaurant_id, default_persona_id, created_by_user_id
        ) VALUES (
            :flow_id, :now, :now, false, NULL, NULL, NULL,
            'متابعة عادية بعد الزيارة',
            'تدفق رسائل متابعة قياسي للعملاء بعد زيارة المطعم',
            'standard_followup', true, 10,
            :trigger_conditions, :message_sequence, :personalization_rules, :response_intelligence,
            0, 0.0, 0.0,
            :restaurant_id, :default_persona_id, :admin_id
        )
    """), {
        'flow_id': standard_flow_id,
        'restaurant_id': restaurant_id,
        'default_persona_id': sarah_persona_id,
        'admin_id': admin_user_id,
        'now': datetime.utcnow(),
        'trigger_conditions': '''
        {
            "customer_type": "all",
            "time_after_visit": 2,
            "previous_sentiment": "none",
            "visit_amount_range": {"min": 0, "max": 1000}
        }''',
        'message_sequence': '''
        [
            {
                "step_number": 1,
                "delay_hours": 2,
                "message_type": "follow_up",
                "template_key": "follow_up",
                "personalization_variables": ["customer_name", "visit_time"],
                "expected_response_types": ["feedback", "rating", "complaint"],
                "escalation_conditions": {
                    "negative_sentiment": true,
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
        ]''',
        'personalization_rules': '''
        {
            "use_customer_name": true,
            "consider_previous_visits": true,
            "adapt_language_preference": true,
            "respect_time_zone": true
        }''',
        'response_intelligence': '''
        {
            "sentiment_analysis": true,
            "auto_escalation_threshold": -0.3,
            "positive_response_actions": ["request_google_review"],
            "negative_response_actions": ["escalate_to_human", "schedule_follow_up"]
        }'''
    })
    
    # VIP customer flow
    connection.execute(sa.text("""
        INSERT INTO message_flows (
            id, created_at, updated_at, is_deleted, deleted_at, created_by, updated_by,
            name, description, flow_type, is_active, priority,
            trigger_conditions, message_sequence, personalization_rules, response_intelligence,
            execution_count, completion_rate, average_customer_satisfaction,
            restaurant_id, default_persona_id, created_by_user_id
        ) VALUES (
            :flow_id, :now, :now, false, NULL, NULL, NULL,
            'متابعة العملاء المميزين',
            'تدفق خاص للعملاء ذوي الإنفاق العالي أو الزيارات المتكررة',
            'vip_customer', true, 20,
            :trigger_conditions, :message_sequence, :personalization_rules, :response_intelligence,
            0, 0.0, 0.0,
            :restaurant_id, :default_persona_id, :admin_id
        )
    """), {
        'flow_id': vip_flow_id,
        'restaurant_id': restaurant_id,
        'default_persona_id': ahmad_persona_id,
        'admin_id': admin_user_id,
        'now': datetime.utcnow(),
        'trigger_conditions': '''
        {
            "customer_type": "vip",
            "time_after_visit": 1,
            "visit_amount_range": {"min": 500, "max": 999999},
            "is_repeat_customer": true
        }''',
        'message_sequence': '''
        [
            {
                "step_number": 1,
                "delay_hours": 1,
                "message_type": "vip_follow_up",
                "template_key": "vip_greeting",
                "personalization_variables": ["customer_name", "visit_count", "favorite_items"],
                "escalation_conditions": {
                    "negative_sentiment": true,
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
        ]''',
        'personalization_rules': '''
        {
            "use_customer_name": true,
            "mention_visit_history": true,
            "reference_preferences": true,
            "manager_personal_touch": true
        }''',
        'response_intelligence': '''
        {
            "sentiment_analysis": true,
            "auto_escalation_threshold": -0.2,
            "positive_response_actions": ["request_google_review", "offer_exclusive_discount"],
            "negative_response_actions": ["immediate_escalation", "manager_notification"]
        }'''
    })
    
    # Complaint resolution flow
    connection.execute(sa.text("""
        INSERT INTO message_flows (
            id, created_at, updated_at, is_deleted, deleted_at, created_by, updated_by,
            name, description, flow_type, is_active, priority,
            trigger_conditions, message_sequence, personalization_rules, response_intelligence,
            execution_count, completion_rate, average_customer_satisfaction,
            restaurant_id, default_persona_id, created_by_user_id
        ) VALUES (
            :flow_id, :now, :now, false, NULL, NULL, NULL,
            'حل الشكاوى والمشاكل',
            'تدفق متخصص للتعامل مع الشكاوى والمشاكل',
            'complaint_resolution', true, 30,
            :trigger_conditions, :message_sequence, :personalization_rules, :response_intelligence,
            0, 0.0, 0.0,
            :restaurant_id, :default_persona_id, :admin_id
        )
    """), {
        'flow_id': complaint_flow_id,
        'restaurant_id': restaurant_id,
        'default_persona_id': ahmad_persona_id,
        'admin_id': admin_user_id,
        'now': datetime.utcnow(),
        'trigger_conditions': '''
        {
            "customer_type": "all",
            "previous_sentiment": "negative",
            "complaint_detected": true
        }''',
        'message_sequence': '''
        [
            {
                "step_number": 1,
                "delay_hours": 0.25,
                "message_type": "apology",
                "template_key": "complaint_response",
                "personalization_variables": ["customer_name", "complaint_summary"],
                "escalation_conditions": {
                    "always_escalate": true
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
        ]''',
        'personalization_rules': '''
        {
            "use_formal_tone": true,
            "acknowledge_specific_issue": true,
            "provide_direct_contact": true,
            "timeline_commitments": true
        }''',
        'response_intelligence': '''
        {
            "sentiment_analysis": true,
            "human_handoff_required": true,
            "manager_notification": true,
            "priority_handling": true
        }'''
    })


def downgrade() -> None:
    """Remove default seeded data."""
    
    connection = op.get_bind()
    
    # Remove default data in reverse order of dependencies
    connection.execute(sa.text("DELETE FROM message_flows WHERE name IN ('متابعة عادية بعد الزيارة', 'متابعة العملاء المميزين', 'حل الشكاوى والمشاكل')"))
    connection.execute(sa.text("DELETE FROM agent_personas WHERE name IN ('سارة - المساعد الودود', 'أحمد - المحترف الرسمي')"))
    connection.execute(sa.text("DELETE FROM restaurants WHERE name = 'مطعم الذواقة الراقي'"))
    connection.execute(sa.text("DELETE FROM users WHERE email = 'admin@restaurant-ai.com'"))