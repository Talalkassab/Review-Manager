"""
Test Data Generator
==================

Generates synthetic customer profiles, conversation histories, and test scenarios
for comprehensive agent testing.
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from faker import Faker
import json

from .models import SyntheticCustomer
from .schemas import (
    CustomerProfileType, CustomerDemographics, CustomerBehavioralTraits,
    VisitContext, SyntheticCustomerCreate, SyntheticCustomerResponse,
    CommunicationStyle, ResponseSpeed
)

# Initialize Faker with Arabic locale support
fake = Faker(['ar_SA', 'en_US'])
fake_ar = Faker('ar_SA')
fake_en = Faker('en_US')

class TestDataGenerator:
    """
    Advanced synthetic data generator for creating realistic customer profiles,
    conversation scenarios, and test data for agent testing.
    """
    
    def __init__(self):
        # Regional demographic data for Saudi Arabia/Gulf region
        self.gulf_names_male = [
            'محمد', 'أحمد', 'عبدالله', 'سالم', 'خالد', 'عبدالرحمن', 'عبدالعزيز',
            'فهد', 'عبدالمجيد', 'سعد', 'عمر', 'يوسف', 'إبراهيم', 'عبدالله',
            'ناصر', 'سلمان', 'راشد', 'مشعل', 'تركي', 'بندر'
        ]
        
        self.gulf_names_female = [
            'فاطمة', 'عائشة', 'خديجة', 'مريم', 'سارة', 'نورة', 'هند',
            'ريم', 'لولوة', 'منى', 'عبير', 'أمل', 'رنا', 'دانة',
            'شهد', 'غادة', 'لمى', 'روان', 'جود', 'لين'
        ]
        
        self.gulf_family_names = [
            'آل سعود', 'العتيبي', 'الغامدي', 'القحطاني', 'الحربي', 'المطيري',
            'الدوسري', 'الشمري', 'الزهراني', 'العنزي', 'الرشيد', 'آل الشيخ',
            'الخالد', 'المالك', 'النعيم', 'البصري', 'الجبير', 'السديس'
        ]
        
        self.riyadh_districts = [
            'العليا', 'الملز', 'النرجس', 'الروضة', 'الربوة', 'السليمانية',
            'المرسلات', 'النخيل', 'الياسمين', 'الواحة', 'الحمراء', 'الملقا',
            'الصحافة', 'التعاون', 'الفلاح', 'الخزامى', 'الوشم', 'المونسية'
        ]
        
        self.restaurant_types = [
            'مطعم شعبي', 'مطعم فاخر', 'مقهى', 'مطعم عائلي', 'بوفيه مفتوح',
            'مطعم وجبات سريعة', 'مطعم مأكولات بحرية', 'مطعم شواء'
        ]
        
        self.common_dishes = [
            'كبسة', 'مندي', 'برياني', 'معصوب', 'مرق', 'مسخن', 'منسف',
            'فلافل', 'شاورما', 'برغل', 'كباب', 'مشاوي مشكلة', 'سمك مشوي'
        ]
        
        self.complaint_types = [
            'طعام بارد', 'خدمة بطيئة', 'طلب خاطئ', 'جودة الطعام رديئة',
            'مكان غير نظيف', 'موظف غير مهذب', 'وقت انتظار طويل', 'أسعار مرتفعة'
        ]
        
    async def generate_customers(
        self,
        db,
        count: int,
        profile_types: List[CustomerProfileType],
        user_id: str
    ) -> List[SyntheticCustomerResponse]:
        """Generate synthetic customer profiles"""
        
        generated_customers = []
        
        for _ in range(count):
            # Randomly select profile type
            profile_type = random.choice(profile_types)
            
            # Generate customer profile
            customer_data = await self._generate_single_customer_profile(profile_type)
            
            # Create database record
            db_customer = SyntheticCustomer(
                profile_name=customer_data.profile_name,
                profile_type=customer_data.profile_type,
                age_range=customer_data.demographics.age_range,
                gender=customer_data.demographics.gender,
                language_preference=customer_data.demographics.language_preference,
                cultural_background=customer_data.demographics.cultural_background,
                location=customer_data.demographics.location,
                communication_style=customer_data.behavioral_traits.communication_style.value,
                response_speed=customer_data.behavioral_traits.response_speed.value,
                sentiment_baseline=customer_data.behavioral_traits.sentiment_baseline,
                complaint_likelihood=customer_data.behavioral_traits.complaint_likelihood,
                visit_history=customer_data.visit_context.dict(),
                order_preferences=self._generate_order_preferences(),
                special_requirements=self._generate_special_requirements(),
                user_id=user_id
            )
            
            db.add(db_customer)
            db.commit()
            db.refresh(db_customer)
            
            response = SyntheticCustomerResponse.from_orm(db_customer)
            generated_customers.append(response)
        
        return generated_customers
    
    async def get_customers(
        self,
        db,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
        profile_type: Optional[CustomerProfileType] = None
    ) -> List[SyntheticCustomerResponse]:
        """Retrieve existing synthetic customers"""
        
        query = db.query(SyntheticCustomer).filter(SyntheticCustomer.user_id == user_id)
        
        if profile_type:
            query = query.filter(SyntheticCustomer.profile_type == profile_type)
        
        customers = query.offset(skip).limit(limit).all()
        
        return [SyntheticCustomerResponse.from_orm(customer) for customer in customers]
    
    async def _generate_single_customer_profile(
        self, 
        profile_type: CustomerProfileType
    ) -> SyntheticCustomerCreate:
        """Generate a single realistic customer profile"""
        
        # Generate demographics
        demographics = self._generate_demographics()
        
        # Generate behavioral traits based on profile type
        behavioral_traits = self._generate_behavioral_traits(profile_type)
        
        # Generate visit context
        visit_context = self._generate_visit_context(profile_type)
        
        # Generate profile name
        profile_name = self._generate_profile_name(demographics, profile_type)
        
        return SyntheticCustomerCreate(
            profile_name=profile_name,
            profile_type=profile_type,
            demographics=demographics,
            behavioral_traits=behavioral_traits,
            visit_context=visit_context
        )
    
    def _generate_demographics(self) -> CustomerDemographics:
        """Generate realistic demographic information"""
        
        # Gender distribution
        gender = random.choices(['male', 'female'], weights=[0.6, 0.4])[0]
        
        # Age distribution (weighted towards younger demographics)
        age_ranges = ['18-25', '26-35', '36-45', '46-55', '56-65', '65+']
        age_weights = [0.25, 0.35, 0.20, 0.12, 0.06, 0.02]
        age_range = random.choices(age_ranges, weights=age_weights)[0]
        
        # Language preference (Arabic dominant)
        language_preference = random.choices(
            ['arabic', 'english', 'both'], 
            weights=[0.7, 0.2, 0.1]
        )[0]
        
        # Cultural background
        cultural_backgrounds = ['gulf', 'levantine', 'egyptian', 'maghreb', 'expat']
        cultural_weights = [0.6, 0.15, 0.1, 0.05, 0.1]
        cultural_background = random.choices(cultural_backgrounds, weights=cultural_weights)[0]
        
        # Location (Riyadh focused)
        location = f"{random.choice(self.riyadh_districts)}, الرياض"
        
        return CustomerDemographics(
            age_range=age_range,
            gender=gender,
            language_preference=language_preference,
            cultural_background=cultural_background,
            location=location
        )
    
    def _generate_behavioral_traits(
        self, 
        profile_type: CustomerProfileType
    ) -> CustomerBehavioralTraits:
        """Generate behavioral traits based on customer profile type"""
        
        # Communication style mapping
        style_mapping = {
            CustomerProfileType.HAPPY_CUSTOMER: [CommunicationStyle.POLITE, CommunicationStyle.ANALYTICAL],
            CustomerProfileType.DISSATISFIED_CUSTOMER: [CommunicationStyle.DIRECT, CommunicationStyle.EMOTIONAL],
            CustomerProfileType.FIRST_TIME_VISITOR: [CommunicationStyle.POLITE, CommunicationStyle.ANALYTICAL],
            CustomerProfileType.REPEAT_CUSTOMER: [CommunicationStyle.POLITE, CommunicationStyle.DIRECT],
            CustomerProfileType.VIP_CUSTOMER: [CommunicationStyle.DIRECT, CommunicationStyle.ANALYTICAL],
            CustomerProfileType.COMPLAINT_CUSTOMER: [CommunicationStyle.EMOTIONAL, CommunicationStyle.DIRECT]
        }
        
        communication_style = random.choice(style_mapping.get(profile_type, [CommunicationStyle.POLITE]))
        
        # Response speed based on profile
        speed_mapping = {
            CustomerProfileType.HAPPY_CUSTOMER: [ResponseSpeed.IMMEDIATE, ResponseSpeed.DELAYED],
            CustomerProfileType.DISSATISFIED_CUSTOMER: [ResponseSpeed.IMMEDIATE, ResponseSpeed.IRREGULAR],
            CustomerProfileType.VIP_CUSTOMER: [ResponseSpeed.IMMEDIATE],
            CustomerProfileType.COMPLAINT_CUSTOMER: [ResponseSpeed.IMMEDIATE],
        }
        
        response_speed = random.choice(
            speed_mapping.get(profile_type, [ResponseSpeed.DELAYED, ResponseSpeed.IRREGULAR])
        )
        
        # Sentiment baseline
        sentiment_mapping = {
            CustomerProfileType.HAPPY_CUSTOMER: 'positive',
            CustomerProfileType.DISSATISFIED_CUSTOMER: 'negative',
            CustomerProfileType.FIRST_TIME_VISITOR: 'neutral',
            CustomerProfileType.REPEAT_CUSTOMER: 'positive',
            CustomerProfileType.VIP_CUSTOMER: 'neutral',
            CustomerProfileType.COMPLAINT_CUSTOMER: 'negative'
        }
        
        sentiment_baseline = sentiment_mapping.get(profile_type, 'neutral')
        
        # Complaint likelihood
        complaint_likelihood_mapping = {
            CustomerProfileType.HAPPY_CUSTOMER: random.uniform(0.05, 0.15),
            CustomerProfileType.DISSATISFIED_CUSTOMER: random.uniform(0.6, 0.9),
            CustomerProfileType.FIRST_TIME_VISITOR: random.uniform(0.1, 0.3),
            CustomerProfileType.REPEAT_CUSTOMER: random.uniform(0.1, 0.25),
            CustomerProfileType.VIP_CUSTOMER: random.uniform(0.2, 0.4),
            CustomerProfileType.COMPLAINT_CUSTOMER: random.uniform(0.8, 1.0)
        }
        
        complaint_likelihood = complaint_likelihood_mapping.get(profile_type, 0.2)
        
        return CustomerBehavioralTraits(
            communication_style=communication_style,
            response_speed=response_speed,
            sentiment_baseline=sentiment_baseline,
            complaint_likelihood=complaint_likelihood
        )
    
    def _generate_visit_context(self, profile_type: CustomerProfileType) -> VisitContext:
        """Generate visit context based on customer profile"""
        
        # Visit type
        visit_type_mapping = {
            CustomerProfileType.FIRST_TIME_VISITOR: 'first_time',
            CustomerProfileType.REPEAT_CUSTOMER: 'repeat',
            CustomerProfileType.VIP_CUSTOMER: 'special_occasion',
        }
        
        visit_type = visit_type_mapping.get(profile_type, random.choice(['first_time', 'repeat']))
        
        # Order value (in SAR)
        order_value_ranges = {
            CustomerProfileType.VIP_CUSTOMER: (150, 500),
            CustomerProfileType.HAPPY_CUSTOMER: (80, 200),
            CustomerProfileType.REPEAT_CUSTOMER: (60, 180),
            CustomerProfileType.FIRST_TIME_VISITOR: (40, 120),
            CustomerProfileType.DISSATISFIED_CUSTOMER: (30, 100),
            CustomerProfileType.COMPLAINT_CUSTOMER: (50, 150)
        }
        
        min_val, max_val = order_value_ranges.get(profile_type, (40, 150))
        order_value = random.uniform(min_val, max_val)
        
        # Dining experience
        experience_mapping = {
            CustomerProfileType.HAPPY_CUSTOMER: ['excellent', 'good'],
            CustomerProfileType.DISSATISFIED_CUSTOMER: ['poor', 'average'],
            CustomerProfileType.VIP_CUSTOMER: ['excellent', 'good'],
            CustomerProfileType.COMPLAINT_CUSTOMER: ['poor'],
        }
        
        experiences = experience_mapping.get(profile_type, ['average', 'good'])
        dining_experience = random.choice(experiences)
        
        # Specific issues for dissatisfied customers
        specific_issues = None
        if profile_type in [CustomerProfileType.DISSATISFIED_CUSTOMER, CustomerProfileType.COMPLAINT_CUSTOMER]:
            num_issues = random.randint(1, 3)
            specific_issues = random.sample(self.complaint_types, num_issues)
        
        return VisitContext(
            visit_type=visit_type,
            order_value=round(order_value, 2),
            dining_experience=dining_experience,
            specific_issues=specific_issues
        )
    
    def _generate_profile_name(
        self, 
        demographics: CustomerDemographics, 
        profile_type: CustomerProfileType
    ) -> str:
        """Generate a realistic profile name"""
        
        # Select appropriate name based on gender and cultural background
        if demographics.gender == 'male':
            first_name = random.choice(self.gulf_names_male)
        else:
            first_name = random.choice(self.gulf_names_female)
        
        family_name = random.choice(self.gulf_family_names)
        
        # Add profile type descriptor
        type_descriptors = {
            CustomerProfileType.HAPPY_CUSTOMER: 'العميل الراضي',
            CustomerProfileType.DISSATISFIED_CUSTOMER: 'العميل غير الراضي',
            CustomerProfileType.FIRST_TIME_VISITOR: 'الزائر الجديد',
            CustomerProfileType.REPEAT_CUSTOMER: 'العميل المعتاد',
            CustomerProfileType.VIP_CUSTOMER: 'العميل المميز',
            CustomerProfileType.COMPLAINT_CUSTOMER: 'العميل المتذمر'
        }
        
        descriptor = type_descriptors.get(profile_type, 'العميل')
        
        return f"{first_name} {family_name} ({descriptor})"
    
    def _generate_order_preferences(self) -> Dict[str, Any]:
        """Generate order preferences and history"""
        
        return {
            "favorite_dishes": random.sample(self.common_dishes, random.randint(2, 5)),
            "dietary_restrictions": random.choice([
                None, "vegetarian", "halal_only", "no_spicy", "diabetic_friendly"
            ]),
            "preferred_meal_time": random.choice([
                "breakfast", "lunch", "dinner", "late_night"
            ]),
            "typical_group_size": random.randint(1, 8),
            "average_visit_frequency": random.choice([
                "weekly", "bi-weekly", "monthly", "occasional"
            ])
        }
    
    def _generate_special_requirements(self) -> Dict[str, Any]:
        """Generate special requirements or preferences"""
        
        requirements = {}
        
        # Accessibility needs
        if random.random() < 0.05:  # 5% have accessibility needs
            requirements["accessibility"] = random.choice([
                "wheelchair_access", "hearing_assistance", "visual_assistance"
            ])
        
        # Seating preferences
        requirements["seating_preference"] = random.choice([
            "family_section", "couples_section", "outdoor", "private_dining", "no_preference"
        ])
        
        # Service preferences
        requirements["service_preferences"] = {
            "language": random.choice(["arabic", "english", "no_preference"]),
            "staff_gender_preference": random.choice(["male", "female", "no_preference"]),
            "service_speed": random.choice(["fast", "relaxed", "no_preference"])
        }
        
        return requirements
    
    async def generate_conversation_history(
        self, 
        customer_profile: SyntheticCustomer,
        conversation_count: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate realistic conversation history for a customer"""
        
        conversations = []
        
        for i in range(conversation_count):
            # Generate conversation based on profile type
            conversation = await self._generate_single_conversation(
                customer_profile, 
                conversation_index=i
            )
            conversations.append(conversation)
        
        return conversations
    
    async def _generate_single_conversation(
        self,
        customer_profile: SyntheticCustomer,
        conversation_index: int
    ) -> Dict[str, Any]:
        """Generate a single conversation scenario"""
        
        # Determine conversation topic based on profile
        conversation_topics = {
            CustomerProfileType.HAPPY_CUSTOMER: [
                "positive_feedback", "recommendation_request", "repeat_order"
            ],
            CustomerProfileType.DISSATISFIED_CUSTOMER: [
                "complaint", "refund_request", "service_improvement"
            ],
            CustomerProfileType.COMPLAINT_CUSTOMER: [
                "formal_complaint", "escalation_request", "compensation_demand"
            ],
            CustomerProfileType.VIP_CUSTOMER: [
                "special_request", "reservation_inquiry", "menu_customization"
            ]
        }
        
        topic = random.choice(
            conversation_topics.get(
                customer_profile.profile_type, 
                ["general_inquiry", "menu_question"]
            )
        )
        
        # Generate conversation messages
        messages = await self._generate_conversation_messages(
            customer_profile, topic
        )
        
        return {
            "conversation_id": str(uuid.uuid4()),
            "date": (datetime.utcnow() - timedelta(days=conversation_index*7)).isoformat(),
            "topic": topic,
            "messages": messages,
            "resolution_status": random.choice([
                "resolved", "pending", "escalated", "closed"
            ]),
            "satisfaction_rating": random.randint(1, 5) if topic != "complaint" else random.randint(1, 3)
        }
    
    async def _generate_conversation_messages(
        self,
        customer_profile: SyntheticCustomer,
        topic: str
    ) -> List[Dict[str, Any]]:
        """Generate realistic conversation messages"""
        
        messages = []
        
        # Generate opening message from customer
        opening_message = self._get_opening_message(customer_profile, topic)
        messages.append({
            "sender": "customer",
            "content": opening_message,
            "timestamp": datetime.utcnow().isoformat(),
            "language": customer_profile.language_preference,
            "sentiment": self._get_sentiment_for_topic(topic)
        })
        
        # Generate 2-4 exchange pairs
        exchange_count = random.randint(2, 4)
        
        for _ in range(exchange_count):
            # Agent response
            agent_response = self._generate_agent_response(topic)
            messages.append({
                "sender": "agent",
                "content": agent_response,
                "timestamp": datetime.utcnow().isoformat(),
                "language": "arabic",  # Agents typically respond in Arabic
                "response_time_seconds": random.uniform(10, 45)
            })
            
            # Customer follow-up
            customer_followup = self._generate_customer_followup(customer_profile, topic)
            messages.append({
                "sender": "customer", 
                "content": customer_followup,
                "timestamp": datetime.utcnow().isoformat(),
                "language": customer_profile.language_preference,
                "sentiment": self._get_sentiment_for_topic(topic)
            })
        
        return messages
    
    def _get_opening_message(self, customer_profile: SyntheticCustomer, topic: str) -> str:
        """Generate opening message based on customer profile and topic"""
        
        arabic_messages = {
            "positive_feedback": [
                "السلام عليكم، أريد أن أشكركم على الخدمة الممتازة أمس",
                "مرحباً، كانت تجربتي في مطعمكم رائعة جداً",
                "أهلاً، أردت أن أعبر عن إعجابي بجودة الطعام والخدمة"
            ],
            "complaint": [
                "لدي شكوى بخصوص زيارتي الأخيرة للمطعم",
                "السلام عليكم، واجهت مشكلة في طلبي أمس",
                "مرحباً، لم أكن راضياً عن الخدمة التي تلقيتها"
            ],
            "reservation_inquiry": [
                "أريد حجز طاولة لهذا المساء",
                "هل يمكنني حجز طاولة لـ 6 أشخاص؟",
                "أحتاج حجز عشاء لعائلة من 4 أفراد"
            ]
        }
        
        english_messages = {
            "positive_feedback": [
                "Hi, I wanted to thank you for the excellent service yesterday",
                "Hello, my experience at your restaurant was amazing",
                "Hi there, I wanted to express my appreciation for the quality"
            ],
            "complaint": [
                "I have a complaint about my recent visit",
                "Hello, I experienced an issue with my order yesterday", 
                "Hi, I wasn't satisfied with the service I received"
            ],
            "reservation_inquiry": [
                "I'd like to make a reservation for tonight",
                "Can I book a table for 6 people?",
                "I need to reserve a dinner table for a family of 4"
            ]
        }
        
        if customer_profile.language_preference == "arabic":
            return random.choice(arabic_messages.get(topic, arabic_messages["positive_feedback"]))
        else:
            return random.choice(english_messages.get(topic, english_messages["positive_feedback"]))
    
    def _generate_agent_response(self, topic: str) -> str:
        """Generate typical agent response"""
        
        responses = {
            "positive_feedback": [
                "شكراً جزيلاً لكم على كلماتكم الطيبة، نحن سعداء برضاكم",
                "نقدر تقييمكم الإيجابي ونتطلع لاستقبالكم مرة أخرى",
                "أهلاً وسهلاً، نفرح دائماً بسماع آراء عملائنا الكرام"
            ],
            "complaint": [
                "نعتذر منكم بشدة على هذه التجربة، دعونا نحل هذه المشكلة",
                "أشكركم على إعلامنا بهذا الأمر، سنتأكد من عدم تكراره",
                "نأسف لما حدث، كيف يمكننا تعويضكم عن هذه التجربة؟"
            ],
            "reservation_inquiry": [
                "بالطبع، يسعدنا حجز طاولة لكم، ما الوقت المناسب؟",
                "أهلاً بكم، لدينا أوقات متاحة، أي وقت تفضلون؟",
                "حياكم الله، سنرتب لكم أفضل طاولة متاحة"
            ]
        }
        
        return random.choice(responses.get(topic, responses["positive_feedback"]))
    
    def _generate_customer_followup(self, customer_profile: SyntheticCustomer, topic: str) -> str:
        """Generate customer follow-up message"""
        
        followups = {
            "positive_feedback": [
                "شكراً لكم، سأتأكد من التوصية بمطعمكم لأصدقائي",
                "أقدر ردكم السريع، نراكم قريباً إن شاء الله",
                "ممتاز، هذا سبب عودتنا المستمرة لمطعمكم"
            ],
            "complaint": [
                "أقدر اعتذاركم، كيف ستتأكدون من عدم تكرار هذا؟",
                "شكراً للاهتمام، أتطلع لحل سريع لهذه المشكلة",
                "أريد ضمانات أن هذا لن يحدث مرة أخرى"
            ]
        }
        
        return random.choice(followups.get(topic, followups["positive_feedback"]))
    
    def _get_sentiment_for_topic(self, topic: str) -> str:
        """Get appropriate sentiment for topic"""
        
        sentiment_mapping = {
            "positive_feedback": "positive",
            "complaint": "negative", 
            "reservation_inquiry": "neutral",
            "general_inquiry": "neutral"
        }
        
        return sentiment_mapping.get(topic, "neutral")

# Global instance
test_data_generator = TestDataGenerator()