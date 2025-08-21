"""
Customer Profile Simulator
==========================

Generates realistic customer profiles and simulates customer responses
for testing agent interactions with various customer types and scenarios.
"""

import random
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..database import get_db
from .models import SyntheticCustomer
from .schemas import (
    CustomerProfileType, CustomerDemographics, CustomerBehavioralTraits,
    VisitContext, CustomerProfileSimulatorConfig, SyntheticCustomerCreate,
    SyntheticCustomerResponse, CommunicationStyle, ResponseSpeed
)

router = APIRouter(prefix="/testing/customer-simulator", tags=["customer-simulator"])

class CustomerProfile:
    """Individual customer profile for simulation"""
    
    def __init__(
        self,
        profile_type: CustomerProfileType,
        demographics: CustomerDemographics,
        behavioral_traits: CustomerBehavioralTraits,
        visit_context: VisitContext
    ):
        self.profile_type = profile_type
        self.demographics = demographics
        self.behavioral_traits = behavioral_traits
        self.visit_context = visit_context
        self.conversation_history: List[Dict[str, Any]] = []
        self.current_mood = self._determine_initial_mood()
        self.response_patterns = self._generate_response_patterns()

    def _determine_initial_mood(self) -> str:
        """Determine initial customer mood based on profile"""
        
        mood_weights = {
            CustomerProfileType.HAPPY_CUSTOMER: {
                "very_happy": 0.6, "happy": 0.3, "neutral": 0.1
            },
            CustomerProfileType.DISSATISFIED_CUSTOMER: {
                "angry": 0.4, "frustrated": 0.4, "disappointed": 0.2
            },
            CustomerProfileType.FIRST_TIME_VISITOR: {
                "curious": 0.4, "neutral": 0.4, "cautious": 0.2
            },
            CustomerProfileType.REPEAT_CUSTOMER: {
                "satisfied": 0.5, "neutral": 0.3, "happy": 0.2
            },
            CustomerProfileType.VIP_CUSTOMER: {
                "expectant": 0.4, "satisfied": 0.4, "neutral": 0.2
            },
            CustomerProfileType.COMPLAINT_CUSTOMER: {
                "frustrated": 0.5, "angry": 0.3, "disappointed": 0.2
            }
        }
        
        weights = mood_weights.get(self.profile_type, {"neutral": 1.0})
        return random.choices(list(weights.keys()), weights=list(weights.values()))[0]

    def _generate_response_patterns(self) -> Dict[str, Any]:
        """Generate response patterns based on profile characteristics"""
        
        patterns = {
            "greeting_responses": [],
            "complaint_expressions": [],
            "satisfaction_expressions": [],
            "farewell_responses": [],
            "question_styles": []
        }
        
        # Arabic responses based on profile type and communication style
        if self.demographics.language_preference == "arabic":
            patterns.update(self._generate_arabic_patterns())
        else:
            patterns.update(self._generate_english_patterns())
            
        return patterns

    def _generate_arabic_patterns(self) -> Dict[str, List[str]]:
        """Generate Arabic response patterns"""
        
        base_patterns = {
            "greeting_responses": [
                "مرحباً، كيف الحال؟",
                "أهلاً وسهلاً",
                "السلام عليكم"
            ],
            "satisfaction_expressions": [
                "الخدمة ممتازة، شكراً لكم",
                "أعجبني الطعام كثيراً",
                "الأجواء رائعة هنا"
            ],
            "complaint_expressions": [
                "الطعام وصل بارد",
                "الانتظار طويل جداً",
                "الخدمة غير مرضية"
            ]
        }
        
        # Customize based on communication style
        if self.behavioral_traits.communication_style == CommunicationStyle.POLITE:
            base_patterns["complaint_expressions"] = [
                "معذرة، لكن الطعام وصل بارد قليلاً",
                "آسف للإزعاج، لكن هناك تأخير في الطلب",
                "أتمنى لو كانت الخدمة أسرع قليلاً"
            ]
        elif self.behavioral_traits.communication_style == CommunicationStyle.DIRECT:
            base_patterns["complaint_expressions"] = [
                "الطعام بارد!",
                "الانتظار طويل!",
                "الخدمة سيئة"
            ]
        elif self.behavioral_traits.communication_style == CommunicationStyle.EMOTIONAL:
            base_patterns["complaint_expressions"] = [
                "أنا منزعج جداً من الطعام البارد 😠",
                "هذا الانتظار لا يُطاق! 😤",
                "خدمة مخيبة للآمال 😞"
            ]
            
        return base_patterns

    def _generate_english_patterns(self) -> Dict[str, List[str]]:
        """Generate English response patterns"""
        
        base_patterns = {
            "greeting_responses": [
                "Hello, how are you?",
                "Hi there!",
                "Good evening!"
            ],
            "satisfaction_expressions": [
                "The service was excellent, thank you!",
                "I really enjoyed the food",
                "Great atmosphere here"
            ],
            "complaint_expressions": [
                "The food arrived cold",
                "The wait was too long",
                "The service was unsatisfactory"
            ]
        }
        
        # Customize based on communication style
        if self.behavioral_traits.communication_style == CommunicationStyle.POLITE:
            base_patterns["complaint_expressions"] = [
                "I'm sorry to mention this, but the food arrived a bit cold",
                "I hate to bother you, but there's been a delay with my order",
                "I was hoping the service could be a bit faster"
            ]
        elif self.behavioral_traits.communication_style == CommunicationStyle.DIRECT:
            base_patterns["complaint_expressions"] = [
                "The food is cold!",
                "This wait is too long!",
                "Poor service"
            ]
            
        return base_patterns

    def profile_summary(self) -> Dict[str, Any]:
        """Get a summary of the customer profile"""
        return {
            "profile_type": self.profile_type,
            "demographics": self.demographics.dict(),
            "behavioral_traits": self.behavioral_traits.dict(),
            "visit_context": self.visit_context.dict(),
            "current_mood": self.current_mood,
            "language_preference": self.demographics.language_preference
        }

class CustomerProfileSimulator:
    """Main customer profile simulator class"""
    
    def __init__(self):
        self.active_profiles: Dict[str, CustomerProfile] = {}
        
        # Predefined profile templates
        self.profile_templates = {
            CustomerProfileType.HAPPY_CUSTOMER: {
                "demographics": {
                    "age_range": "25-45",
                    "gender": "mixed",
                    "language_preference": "arabic",
                    "cultural_background": "gulf"
                },
                "behavioral_traits": {
                    "communication_style": CommunicationStyle.POLITE,
                    "response_speed": ResponseSpeed.IMMEDIATE,
                    "sentiment_baseline": "positive",
                    "complaint_likelihood": 0.1
                }
            },
            CustomerProfileType.DISSATISFIED_CUSTOMER: {
                "demographics": {
                    "age_range": "30-50",
                    "gender": "mixed",
                    "language_preference": "arabic",
                    "cultural_background": "gulf"
                },
                "behavioral_traits": {
                    "communication_style": CommunicationStyle.DIRECT,
                    "response_speed": ResponseSpeed.IMMEDIATE,
                    "sentiment_baseline": "negative",
                    "complaint_likelihood": 0.8
                }
            },
            CustomerProfileType.FIRST_TIME_VISITOR: {
                "demographics": {
                    "age_range": "20-40",
                    "gender": "mixed",
                    "language_preference": "mixed",
                    "cultural_background": "mixed"
                },
                "behavioral_traits": {
                    "communication_style": CommunicationStyle.ANALYTICAL,
                    "response_speed": ResponseSpeed.DELAYED,
                    "sentiment_baseline": "neutral",
                    "complaint_likelihood": 0.3
                }
            }
        }

    async def create_customer_profile(
        self,
        profile_type: CustomerProfileType,
        demographics: Optional[CustomerDemographics] = None,
        behavioral_traits: Optional[CustomerBehavioralTraits] = None,
        visit_context: Optional[VisitContext] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> CustomerProfile:
        """Create a new customer profile for simulation"""
        
        # Use provided data or generate from templates
        if not demographics:
            template = self.profile_templates.get(profile_type, {})
            demo_data = template.get("demographics", {})
            demographics = CustomerDemographics(
                age_range=demo_data.get("age_range", "25-45"),
                gender=random.choice(["male", "female"]) if demo_data.get("gender") == "mixed" else demo_data.get("gender", "male"),
                language_preference=random.choice(["arabic", "english"]) if demo_data.get("language_preference") == "mixed" else demo_data.get("language_preference", "arabic"),
                cultural_background=demo_data.get("cultural_background", "gulf"),
                location="Riyadh"
            )
        
        if not behavioral_traits:
            template = self.profile_templates.get(profile_type, {})
            trait_data = template.get("behavioral_traits", {})
            behavioral_traits = CustomerBehavioralTraits(
                communication_style=trait_data.get("communication_style", CommunicationStyle.POLITE),
                response_speed=trait_data.get("response_speed", ResponseSpeed.IMMEDIATE),
                sentiment_baseline=trait_data.get("sentiment_baseline", "neutral"),
                complaint_likelihood=trait_data.get("complaint_likelihood", 0.3)
            )
        
        if not visit_context:
            visit_context = VisitContext(
                visit_type=random.choice(["first_time", "repeat", "special_occasion"]),
                order_value=random.uniform(50, 300),
                dining_experience=random.choice(["excellent", "good", "average", "poor"]),
                specific_issues=context.get("issues") if context else None
            )
        
        profile = CustomerProfile(
            profile_type=profile_type,
            demographics=demographics,
            behavioral_traits=behavioral_traits,
            visit_context=visit_context
        )
        
        # Store active profile
        profile_id = f"{profile_type}_{datetime.utcnow().timestamp()}"
        self.active_profiles[profile_id] = profile
        
        return profile

    async def generate_response(
        self,
        agent_message: str,
        customer_profile: CustomerProfile,
        conversation_context: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Generate customer response to agent message"""
        
        # Analyze agent message sentiment and content
        message_analysis = self._analyze_agent_message(agent_message)
        
        # Determine response based on customer profile and current mood
        response_content = self._generate_response_content(
            customer_profile, 
            message_analysis, 
            conversation_context or []
        )
        
        # Calculate response timing based on customer traits
        response_delay = self._calculate_response_delay(customer_profile)
        
        # Update customer mood based on interaction
        new_mood = self._update_customer_mood(customer_profile, message_analysis)
        customer_profile.current_mood = new_mood
        
        response = {
            "content": response_content,
            "language": customer_profile.demographics.language_preference,
            "sentiment": customer_profile.behavioral_traits.sentiment_baseline,
            "mood": customer_profile.current_mood,
            "response_delay_seconds": response_delay,
            "confidence": random.uniform(0.8, 0.95),
            "metadata": {
                "communication_style": customer_profile.behavioral_traits.communication_style,
                "profile_type": customer_profile.profile_type,
                "interaction_count": len(customer_profile.conversation_history) + 1
            }
        }
        
        # Add to conversation history
        customer_profile.conversation_history.append({
            "agent_message": agent_message,
            "customer_response": response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return response

    def _analyze_agent_message(self, message: str) -> Dict[str, Any]:
        """Analyze agent message to determine customer response strategy"""
        
        message_lower = message.lower()
        
        analysis = {
            "is_greeting": any(word in message_lower for word in ["مرحبا", "أهلا", "hello", "hi"]),
            "is_apology": any(word in message_lower for word in ["آسف", "معذرة", "sorry", "apologize"]),
            "is_question": "؟" in message or "?" in message,
            "is_offer": any(word in message_lower for word in ["عرض", "خصم", "offer", "discount"]),
            "is_request_feedback": any(word in message_lower for word in ["رأيك", "تقييم", "feedback", "opinion"]),
            "sentiment": "positive" if any(word in message_lower for word in ["شكرا", "ممتاز", "رائع", "thank", "excellent", "great"]) else "neutral"
        }
        
        return analysis

    def _generate_response_content(
        self, 
        profile: CustomerProfile, 
        message_analysis: Dict[str, Any],
        conversation_context: List[Dict[str, Any]]
    ) -> str:
        """Generate appropriate response content based on profile and context"""
        
        patterns = profile.response_patterns
        current_mood = profile.current_mood
        
        # Select response based on message type and customer mood
        if message_analysis["is_greeting"]:
            responses = patterns["greeting_responses"]
            
        elif message_analysis["is_apology"] and current_mood in ["angry", "frustrated"]:
            if profile.demographics.language_preference == "arabic":
                responses = [
                    "شكراً لاعتذارك، أقدر ذلك",
                    "المهم أن تتحسن الخدمة",
                    "أتمنى ألا يتكرر هذا"
                ]
            else:
                responses = [
                    "Thank you for the apology, I appreciate it",
                    "I hope the service improves",
                    "I trust this won't happen again"
                ]
                
        elif message_analysis["is_request_feedback"]:
            if current_mood in ["very_happy", "happy", "satisfied"]:
                responses = patterns["satisfaction_expressions"]
            elif current_mood in ["angry", "frustrated", "disappointed"]:
                responses = patterns["complaint_expressions"]
            else:
                if profile.demographics.language_preference == "arabic":
                    responses = ["الخدمة عادية", "لا بأس", "يمكن أن تكون أفضل"]
                else:
                    responses = ["The service was okay", "It was fine", "Could be better"]
        
        elif message_analysis["is_offer"] and profile.profile_type == CustomerProfileType.VIP_CUSTOMER:
            if profile.demographics.language_preference == "arabic":
                responses = ["شكراً، هذا عرض جيد", "أقدر اهتمامكم بي", "ممتاز، سأفكر في الأمر"]
            else:
                responses = ["Thank you, that's a good offer", "I appreciate your attention", "Excellent, I'll consider it"]
        
        else:
            # Default responses based on current mood
            if current_mood in ["very_happy", "happy"]:
                if profile.demographics.language_preference == "arabic":
                    responses = ["شكراً لكم", "أقدر اهتمامكم", "خدمة ممتازة"]
                else:
                    responses = ["Thank you", "I appreciate your attention", "Excellent service"]
                    
            elif current_mood in ["angry", "frustrated"]:
                responses = patterns["complaint_expressions"]
                
            else:  # neutral, cautious, etc.
                if profile.demographics.language_preference == "arabic":
                    responses = ["حسناً", "فهمت", "شكراً للمعلومة"]
                else:
                    responses = ["Okay", "I understand", "Thanks for the information"]
        
        # Add personality variations
        response = random.choice(responses if responses else ["حسناً"])
        
        # Add emojis for emotional communication style
        if (profile.behavioral_traits.communication_style == CommunicationStyle.EMOTIONAL and 
            random.random() < 0.6):
            emoji_map = {
                "very_happy": " 😊",
                "happy": " 🙂", 
                "angry": " 😠",
                "frustrated": " 😤",
                "disappointed": " 😞"
            }
            response += emoji_map.get(current_mood, "")
        
        return response

    def _calculate_response_delay(self, profile: CustomerProfile) -> float:
        """Calculate response delay based on customer response speed"""
        
        base_delays = {
            ResponseSpeed.IMMEDIATE: (0.5, 2.0),
            ResponseSpeed.DELAYED: (5.0, 30.0),
            ResponseSpeed.IRREGULAR: (1.0, 60.0)
        }
        
        min_delay, max_delay = base_delays[profile.behavioral_traits.response_speed]
        
        # Add randomness
        delay = random.uniform(min_delay, max_delay)
        
        # Adjust based on mood (angry customers respond faster)
        if profile.current_mood in ["angry", "frustrated"]:
            delay *= 0.5
        elif profile.current_mood in ["cautious", "analytical"]:
            delay *= 1.5
            
        return delay

    def _update_customer_mood(
        self, 
        profile: CustomerProfile, 
        message_analysis: Dict[str, Any]
    ) -> str:
        """Update customer mood based on agent interaction"""
        
        current_mood = profile.current_mood
        
        # Positive interactions improve mood
        if message_analysis["is_apology"] and current_mood in ["angry", "frustrated"]:
            mood_transitions = {
                "angry": "frustrated",
                "frustrated": "disappointed"
            }
            return mood_transitions.get(current_mood, current_mood)
        
        elif message_analysis["sentiment"] == "positive":
            mood_improvements = {
                "disappointed": "neutral",
                "neutral": "satisfied",
                "satisfied": "happy"
            }
            return mood_improvements.get(current_mood, current_mood)
        
        # Default: slight mood degradation over time for complaints
        if (profile.profile_type == CustomerProfileType.COMPLAINT_CUSTOMER and 
            len(profile.conversation_history) > 3):
            return "frustrated"
            
        return current_mood

    async def generate_bulk_profiles(
        self, 
        count: int, 
        profile_types: Optional[List[CustomerProfileType]] = None,
        criteria: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Generate multiple customer profiles for testing"""
        
        if not profile_types:
            profile_types = list(CustomerProfileType)
        
        profiles = []
        
        for _ in range(count):
            profile_type = random.choice(profile_types)
            
            # Apply criteria filters if provided
            demographics_override = None
            if criteria and "demographics" in criteria:
                demo_criteria = criteria["demographics"]
                demographics_override = CustomerDemographics(**demo_criteria)
            
            profile = await self.create_customer_profile(
                profile_type=profile_type,
                demographics=demographics_override
            )
            
            profiles.append(profile.profile_summary())
        
        return profiles

    async def save_synthetic_customer(
        self, 
        profile: CustomerProfile, 
        db: Session
    ) -> SyntheticCustomerResponse:
        """Save synthetic customer profile to database"""
        
        db_customer = SyntheticCustomer(
            profile_name=f"{profile.profile_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            profile_type=profile.profile_type,
            age_range=profile.demographics.age_range,
            gender=profile.demographics.gender,
            language_preference=profile.demographics.language_preference,
            cultural_background=profile.demographics.cultural_background,
            location=profile.demographics.location,
            communication_style=profile.behavioral_traits.communication_style,
            response_speed=profile.behavioral_traits.response_speed,
            sentiment_baseline=profile.behavioral_traits.sentiment_baseline,
            complaint_likelihood=profile.behavioral_traits.complaint_likelihood,
            visit_history=[profile.visit_context.dict()],
            order_preferences={},
            special_requirements={}
        )
        
        db.add(db_customer)
        db.commit()
        db.refresh(db_customer)
        
        return SyntheticCustomerResponse.from_orm(db_customer)

# Initialize API instance
simulator = CustomerProfileSimulator()

# API Routes
@router.post("/profiles", response_model=Dict[str, Any])
async def create_customer_profile(
    profile_type: CustomerProfileType,
    demographics: Optional[CustomerDemographics] = None,
    behavioral_traits: Optional[CustomerBehavioralTraits] = None,
    visit_context: Optional[VisitContext] = None
):
    """Create a new customer profile for simulation"""
    
    profile = await simulator.create_customer_profile(
        profile_type=profile_type,
        demographics=demographics,
        behavioral_traits=behavioral_traits,
        visit_context=visit_context
    )
    
    return profile.profile_summary()

@router.post("/profiles/bulk")
async def generate_bulk_profiles(
    count: int,
    profile_types: Optional[List[CustomerProfileType]] = None,
    criteria: Optional[Dict[str, Any]] = None
):
    """Generate multiple customer profiles for testing"""
    
    profiles = await simulator.generate_bulk_profiles(count, profile_types, criteria)
    return {"profiles": profiles, "count": len(profiles)}

@router.post("/synthetic-customers", response_model=SyntheticCustomerResponse)
async def create_synthetic_customer(
    customer_data: SyntheticCustomerCreate,
    db: Session = Depends(get_db)
):
    """Create and save a synthetic customer profile"""
    
    # Create customer profile
    profile = await simulator.create_customer_profile(
        profile_type=customer_data.profile_type,
        demographics=customer_data.demographics,
        behavioral_traits=customer_data.behavioral_traits,
        visit_context=customer_data.visit_context
    )
    
    # Save to database
    return await simulator.save_synthetic_customer(profile, db)

@router.get("/synthetic-customers", response_model=List[SyntheticCustomerResponse])
async def get_synthetic_customers(
    profile_type: Optional[CustomerProfileType] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get saved synthetic customer profiles"""
    
    query = db.query(SyntheticCustomer)
    
    if profile_type:
        query = query.filter(SyntheticCustomer.profile_type == profile_type)
    
    customers = query.order_by(desc(SyntheticCustomer.created_at)).offset(offset).limit(limit).all()
    
    return [SyntheticCustomerResponse.from_orm(customer) for customer in customers]

@router.post("/simulate-response")
async def simulate_customer_response(
    agent_message: str,
    profile_type: CustomerProfileType,
    conversation_context: Optional[List[Dict[str, Any]]] = None
):
    """Simulate customer response to agent message"""
    
    # Create temporary profile for response
    profile = await simulator.create_customer_profile(profile_type=profile_type)
    
    # Generate response
    response = await simulator.generate_response(
        agent_message=agent_message,
        customer_profile=profile,
        conversation_context=conversation_context
    )
    
    return response