"""
Personalization engine for campaign messages.
Provides AI-powered personalization, dynamic content generation, and cultural adaptation.
"""
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from ...core.logging import get_logger
from ...models import Customer, Campaign, CampaignRecipient, WhatsAppMessage, Restaurant
from ..openrouter.client import OpenRouterClient

logger = get_logger(__name__)


class PersonalizationEngine:
    """Engine for personalizing campaign messages using AI and customer data."""
    
    def __init__(self):
        self.openrouter_client = OpenRouterClient()
        
        # Arabic cultural context templates
        self.arabic_cultural_context = {
            "greetings": {
                "formal": ["أهلاً وسهلاً", "مرحباً بك", "السلام عليكم"],
                "casual": ["أهلاً", "مرحبا", "هلا"]
            },
            "honorifics": {
                "male": ["أستاذ", "سيد"],
                "female": ["أستاذة", "سيدة"],
                "neutral": ["عزيزي العميل", "عزيزتي العميلة"]
            },
            "time_expressions": {
                "morning": "صباح الخير",
                "afternoon": "مساء الخير", 
                "evening": "مساء الخير"
            },
            "courtesy_phrases": [
                "شكراً لك",
                "نحن نقدر زيارتك",
                "نتطلع لرؤيتك مرة أخرى",
                "بإذنك"
            ]
        }
        
        # Personalization variables
        self.standard_variables = {
            "customer_name", "first_name", "last_name", "phone", 
            "restaurant_name", "visit_date", "order_total", "party_size",
            "table_number", "server_name", "special_requests"
        }
    
    async def generate_personalization_data(
        self,
        customers: List[Customer],
        campaign: Campaign,
        session: AsyncSession
    ) -> Dict[UUID, Dict[str, Any]]:
        """Generate personalization data for each customer."""
        try:
            personalization_data = {}
            
            for customer in customers:
                # Get additional customer context
                customer_context = await self._get_customer_context(customer, session)
                
                # Generate personalized variables
                variables = await self._generate_customer_variables(
                    customer, campaign, customer_context, session
                )
                
                personalization_data[customer.id] = variables
            
            logger.info(f"Generated personalization data for {len(customers)} customers")
            return personalization_data
            
        except Exception as e:
            logger.error(f"Personalization data generation failed: {str(e)}")
            return {}
    
    async def _get_customer_context(
        self,
        customer: Customer,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Get additional context about the customer."""
        try:
            # Get message history
            stmt = select(WhatsAppMessage).where(
                WhatsAppMessage.customer_id == customer.id
            ).order_by(WhatsAppMessage.created_at.desc()).limit(5)
            
            result = await session.execute(stmt)
            recent_messages = result.scalars().all()
            
            # Get response history
            response_stmt = text("""
                SELECT 
                    COUNT(*) as total_messages,
                    SUM(CASE WHEN cr.has_responded = true THEN 1 ELSE 0 END) as responses,
                    AVG(CASE WHEN cr.has_responded = true THEN 
                        EXTRACT(EPOCH FROM (cr.responded_at - cr.sent_at))/3600 
                        ELSE NULL END) as avg_response_time_hours
                FROM whatsapp_messages wm
                LEFT JOIN campaign_recipients cr ON wm.id = cr.message_id
                WHERE wm.customer_id = :customer_id
            """)
            
            response_result = await session.execute(response_stmt, {"customer_id": customer.id})
            response_stats = response_result.fetchone()
            
            # Calculate customer metrics
            days_since_visit = (datetime.utcnow() - customer.visit_date).days if customer.visit_date else None
            
            context = {
                "recent_messages": [
                    {
                        "content": msg.content[:100],  # Truncate for privacy
                        "direction": msg.direction,
                        "created_at": msg.created_at.isoformat()
                    }
                    for msg in recent_messages
                ],
                "message_history": {
                    "total_messages": response_stats[0] if response_stats else 0,
                    "total_responses": response_stats[1] if response_stats else 0,
                    "avg_response_time_hours": response_stats[2] if response_stats else None,
                    "response_rate": (response_stats[1] / response_stats[0] * 100) if response_stats and response_stats[0] > 0 else 0
                },
                "visit_info": {
                    "days_since_visit": days_since_visit,
                    "is_recent_visitor": days_since_visit is not None and days_since_visit <= 7,
                    "visit_recency": self._categorize_visit_recency(days_since_visit)
                },
                "value_info": {
                    "order_value": customer.order_total or 0,
                    "value_category": self._categorize_customer_value(customer.order_total or 0)
                }
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Customer context retrieval failed: {str(e)}")
            return {}
    
    def _categorize_visit_recency(self, days_since_visit: Optional[int]) -> str:
        """Categorize visit recency."""
        if days_since_visit is None:
            return "unknown"
        elif days_since_visit <= 1:
            return "today_yesterday"
        elif days_since_visit <= 7:
            return "recent"
        elif days_since_visit <= 30:
            return "moderate"
        else:
            return "long_ago"
    
    def _categorize_customer_value(self, order_total: float) -> str:
        """Categorize customer value."""
        if order_total >= 200:
            return "high_value"
        elif order_total >= 100:
            return "medium_value"
        else:
            return "low_value"
    
    async def _generate_customer_variables(
        self,
        customer: Customer,
        campaign: Campaign,
        customer_context: Dict[str, Any],
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Generate personalized variables for a customer."""
        try:
            # Get restaurant info
            await session.refresh(campaign, ["restaurant"])
            restaurant = campaign.restaurant
            
            # Base variables
            variables = {
                "customer_name": self._get_appropriate_name(customer),
                "first_name": customer.first_name or "عزيزي العميل",
                "last_name": customer.last_name or "",
                "phone": customer.phone_number,
                "restaurant_name": restaurant.name if restaurant else "مطعمنا",
                "visit_date": customer.visit_date.strftime("%Y-%m-%d") if customer.visit_date else "",
                "order_total": f"{customer.order_total:.2f}" if customer.order_total else "0",
                "party_size": str(customer.party_size),
                "table_number": customer.table_number or "",
                "server_name": customer.server_name or "",
                "special_requests": customer.special_requests or ""
            }
            
            # Cultural and contextual enhancements
            cultural_variables = await self._generate_cultural_variables(
                customer, campaign, customer_context
            )
            variables.update(cultural_variables)
            
            # Dynamic content based on context
            dynamic_variables = await self._generate_dynamic_variables(
                customer, campaign, customer_context
            )
            variables.update(dynamic_variables)
            
            # Campaign-specific variables
            campaign_variables = self._generate_campaign_specific_variables(
                customer, campaign, customer_context
            )
            variables.update(campaign_variables)
            
            return variables
            
        except Exception as e:
            logger.error(f"Variable generation failed: {str(e)}")
            return {}
    
    def _get_appropriate_name(self, customer: Customer) -> str:
        """Get culturally appropriate name for customer."""
        if customer.first_name:
            if customer.preferred_language == "ar":
                return f"أستاذ {customer.first_name}" if customer.first_name else "عزيزي العميل"
            else:
                return f"Mr./Ms. {customer.first_name}"
        else:
            return "عزيزي العميل" if customer.preferred_language == "ar" else "Dear Customer"
    
    async def _generate_cultural_variables(
        self,
        customer: Customer,
        campaign: Campaign,
        customer_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate culturally appropriate variables."""
        variables = {}
        
        # Time-based greeting
        current_hour = datetime.utcnow().hour
        if customer.preferred_language == "ar":
            if current_hour < 12:
                variables["greeting"] = "صباح الخير"
            elif current_hour < 18:
                variables["greeting"] = "مساء الخير"
            else:
                variables["greeting"] = "مساء الخير"
        else:
            if current_hour < 12:
                variables["greeting"] = "Good morning"
            elif current_hour < 18:
                variables["greeting"] = "Good afternoon"
            else:
                variables["greeting"] = "Good evening"
        
        # Courtesy phrase based on context
        if customer.preferred_language == "ar":
            if customer_context.get("visit_info", {}).get("is_recent_visitor"):
                variables["courtesy"] = "شكراً لزيارتك الأخيرة"
            else:
                variables["courtesy"] = "نحن نقدر تفضيلك لنا"
        
        # Cultural time considerations
        variables["send_time_note"] = self._get_cultural_time_note(customer.preferred_language)
        
        return variables
    
    def _get_cultural_time_note(self, language: str) -> str:
        """Get cultural time consideration note."""
        if language == "ar":
            return "نحترم أوقاتكم"  # We respect your time
        else:
            return "Thank you for your time"
    
    async def _generate_dynamic_variables(
        self,
        customer: Customer,
        campaign: Campaign,
        customer_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate dynamic variables based on customer context."""
        variables = {}
        
        visit_info = customer_context.get("visit_info", {})
        value_info = customer_context.get("value_info", {})
        message_history = customer_context.get("message_history", {})
        
        # Visit-based personalization
        if visit_info.get("is_recent_visitor"):
            variables["visit_context"] = "زيارتك الأخيرة" if customer.preferred_language == "ar" else "your recent visit"
        else:
            variables["visit_context"] = "زيارتك" if customer.preferred_language == "ar" else "your visit"
        
        # Value-based personalization
        if value_info.get("value_category") == "high_value":
            if customer.preferred_language == "ar":
                variables["value_recognition"] = "كعميل مميز"
            else:
                variables["value_recognition"] = "as a valued customer"
        
        # Response history based personalization
        response_rate = message_history.get("response_rate", 0)
        if response_rate > 70:
            variables["engagement_note"] = "نقدر تفاعلك المستمر" if customer.preferred_language == "ar" else "we appreciate your engagement"
        
        # Party size consideration
        if customer.party_size > 5:
            variables["party_note"] = "للمجموعات الكبيرة" if customer.preferred_language == "ar" else "for large groups"
        
        return variables
    
    def _generate_campaign_specific_variables(
        self,
        customer: Customer,
        campaign: Campaign,
        customer_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate campaign-type specific variables."""
        variables = {}
        
        campaign_type = campaign.campaign_type
        language = customer.preferred_language
        
        if campaign_type == "feedback_survey":
            if language == "ar":
                variables["survey_intro"] = "نود معرفة رأيك"
                variables["survey_purpose"] = "لتحسين خدماتنا"
            else:
                variables["survey_intro"] = "We'd like your feedback"
                variables["survey_purpose"] = "to improve our services"
        
        elif campaign_type == "promotion":
            if language == "ar":
                variables["offer_intro"] = "عرض خاص لك"
                variables["urgency"] = "لفترة محدودة"
            else:
                variables["offer_intro"] = "Special offer for you"
                variables["urgency"] = "for a limited time"
        
        elif campaign_type == "welcome":
            if language == "ar":
                variables["welcome_message"] = "مرحباً بك في عائلتنا"
                variables["next_steps"] = "نتطلع لخدمتك"
            else:
                variables["welcome_message"] = "Welcome to our family"
                variables["next_steps"] = "we look forward to serving you"
        
        elif campaign_type == "satisfaction_survey":
            visit_recency = customer_context.get("visit_info", {}).get("visit_recency")
            if visit_recency == "recent":
                if language == "ar":
                    variables["satisfaction_context"] = "بعد زيارتك الأخيرة"
                else:
                    variables["satisfaction_context"] = "following your recent visit"
        
        return variables
    
    async def enhance_personalization(
        self,
        campaign_id: UUID,
        recipient_ids: List[UUID]
    ):
        """Enhance personalization using AI (background task)."""
        try:
            from ...database import db_manager
            
            async with db_manager.get_session() as session:
                # Get recipients with customer data
                stmt = select(CampaignRecipient).where(
                    CampaignRecipient.id.in_(recipient_ids)
                ).options(selectinload(CampaignRecipient.customer))
                
                result = await session.execute(stmt)
                recipients = result.scalars().all()
                
                for recipient in recipients:
                    try:
                        # Generate AI-enhanced personalization
                        enhanced_data = await self._ai_enhance_personalization(
                            recipient, session
                        )
                        
                        # Update recipient personalization data
                        if enhanced_data:
                            current_data = recipient.personalization_data or {}
                            current_data.update(enhanced_data)
                            recipient.personalization_data = current_data
                    
                    except Exception as e:
                        logger.error(f"AI enhancement failed for recipient {recipient.id}: {str(e)}")
                        continue
                
                await session.commit()
                logger.info(f"Enhanced personalization for {len(recipients)} recipients")
        
        except Exception as e:
            logger.error(f"Background personalization enhancement failed: {str(e)}")
    
    async def _ai_enhance_personalization(
        self,
        recipient: CampaignRecipient,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Use AI to enhance personalization data."""
        try:
            customer = recipient.customer
            
            # Prepare context for AI
            context = {
                "customer_profile": {
                    "name": customer.first_name,
                    "language": customer.preferred_language,
                    "order_total": customer.order_total,
                    "party_size": customer.party_size,
                    "visit_date": customer.visit_date.isoformat() if customer.visit_date else None,
                    "special_requests": customer.special_requests
                },
                "current_personalization": recipient.personalization_data or {}
            }
            
            prompt = f"""
            Enhance the personalization for this customer message:
            
            Customer Context: {json.dumps(context, ensure_ascii=False)}
            
            Please suggest 3-5 additional personalization variables that would make the message more relevant and engaging. Consider:
            - Cultural appropriateness for {customer.preferred_language} language
            - Customer behavior patterns
            - Contextual relevance
            - Emotional connection
            
            Return only a JSON object with variable names and values.
            """
            
            response = await self.openrouter_client.generate_text(
                prompt=prompt,
                model="anthropic/claude-3-haiku"
            )
            
            if response:
                # Try to parse JSON response
                try:
                    enhanced_variables = json.loads(response.strip())
                    if isinstance(enhanced_variables, dict):
                        return enhanced_variables
                except json.JSONDecodeError:
                    logger.warning(f"AI response was not valid JSON: {response}")
            
            return {}
            
        except Exception as e:
            logger.error(f"AI personalization enhancement failed: {str(e)}")
            return {}
    
    def validate_message_template(self, template: str) -> Dict[str, Any]:
        """Validate and analyze a message template."""
        try:
            # Find all variables in template
            variables = re.findall(r'\{(\w+)\}', template)
            
            # Check for standard variables
            standard_vars = [var for var in variables if var in self.standard_variables]
            custom_vars = [var for var in variables if var not in self.standard_variables]
            
            # Check for potential issues
            issues = []
            
            if len(template) > 1000:
                issues.append("Template is very long (>1000 characters)")
            
            if not variables:
                issues.append("No personalization variables found")
            
            if "customer_name" not in variables and "first_name" not in variables:
                issues.append("Consider adding customer name for personalization")
            
            # Check for Arabic content
            has_arabic = bool(re.search(r'[\u0600-\u06FF]', template))
            
            return {
                "is_valid": len(issues) == 0,
                "template_length": len(template),
                "total_variables": len(variables),
                "standard_variables": standard_vars,
                "custom_variables": custom_vars,
                "has_arabic_content": has_arabic,
                "issues": issues,
                "recommendations": self._get_template_recommendations(template, variables)
            }
            
        except Exception as e:
            logger.error(f"Template validation failed: {str(e)}")
            return {"is_valid": False, "error": str(e)}
    
    def _get_template_recommendations(
        self,
        template: str,
        variables: List[str]
    ) -> List[str]:
        """Get recommendations for template improvement."""
        recommendations = []
        
        if "greeting" not in variables:
            recommendations.append("Consider adding {greeting} for time-appropriate salutation")
        
        if "courtesy" not in variables:
            recommendations.append("Consider adding {courtesy} for cultural politeness")
        
        if len(template) < 50:
            recommendations.append("Template might be too short for effective engagement")
        
        # Check for Arabic-specific recommendations
        has_arabic = bool(re.search(r'[\u0600-\u06FF]', template))
        if has_arabic:
            if "restaurant_name" not in variables:
                recommendations.append("Consider personalizing with restaurant name")
        
        return recommendations
    
    async def generate_message_variations(
        self,
        base_template: str,
        campaign_type: str,
        target_language: str = "ar",
        variation_count: int = 3
    ) -> List[Dict[str, Any]]:
        """Generate message variations using AI."""
        try:
            prompt = f"""
            Generate {variation_count} variations of this campaign message:
            
            Base Template: {base_template}
            Campaign Type: {campaign_type}
            Target Language: {target_language}
            
            Requirements:
            - Keep the core message and variables intact
            - Vary the tone and approach slightly
            - Maintain cultural appropriateness
            - Preserve personalization variables in {{}} format
            
            Return variations as a JSON array with objects containing 'content', 'tone', and 'description' fields.
            """
            
            response = await self.openrouter_client.generate_text(
                prompt=prompt,
                model="anthropic/claude-3-haiku"
            )
            
            if response:
                try:
                    variations = json.loads(response.strip())
                    if isinstance(variations, list):
                        return variations
                except json.JSONDecodeError:
                    pass
            
            # Fallback to rule-based variations
            return self._generate_rule_based_variations(base_template, variation_count)
            
        except Exception as e:
            logger.error(f"Message variation generation failed: {str(e)}")
            return [{"content": base_template, "tone": "original", "description": "Original template"}]
    
    def _generate_rule_based_variations(
        self,
        base_template: str,
        variation_count: int
    ) -> List[Dict[str, Any]]:
        """Generate variations using rule-based approach."""
        variations = [
            {"content": base_template, "tone": "original", "description": "Original template"}
        ]
        
        # Simple variations by changing opening/closing
        if variation_count > 1:
            # More formal variation
            formal_template = base_template.replace("مرحبا", "أهلاً وسهلاً").replace("شكرا", "نشكرك جزيلاً")
            variations.append({
                "content": formal_template,
                "tone": "formal",
                "description": "More formal version"
            })
        
        if variation_count > 2:
            # More casual variation
            casual_template = base_template.replace("نحن نقدر", "نحنا نحب").replace("نتطلع", "ننتظر")
            variations.append({
                "content": casual_template,
                "tone": "casual",
                "description": "More casual version"
            })
        
        return variations[:variation_count]