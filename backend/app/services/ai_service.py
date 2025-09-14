"""
AI Service Layer
Handles AI-related operations including sentiment analysis and intelligent responses.
"""
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from uuid import UUID
import logging
import json
import traceback

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.customer import Customer
from ..models import WhatsAppMessage
from ..services.openrouter_service import OpenRouterService
from ..services.restaurant_ai_agent import RestaurantAIAgent
from ..core.logging import get_logger

logger = get_logger(__name__)


class AIService:
    """Service class for AI-related business logic."""

    def __init__(self, session: AsyncSession):
        """Initialize the service with a database session."""
        self.session = session
        self.openrouter_service = OpenRouterService()
        self.restaurant_agent = RestaurantAIAgent()

    async def analyze_sentiment(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze sentiment of given text using OpenRouter service."""
        try:
            # Use OpenRouter service for sentiment analysis
            sentiment_result = await self.openrouter_service.analyze_text_sentiment(
                text=text,
                language="arabic" if self._is_arabic_text(text) else "english",
                detailed_analysis=True
            )

            if sentiment_result.get("sentiment"):
                sentiment_data = sentiment_result["sentiment"]
                return {
                    "sentiment_score": sentiment_data.get("overall", 0.5),
                    "sentiment_category": self._categorize_sentiment(sentiment_data.get("overall", 0.5)),
                    "sentiment_details": sentiment_data,
                    "analyzed_at": datetime.utcnow().isoformat()
                }
            else:
                # Fallback to basic analysis
                return self._basic_sentiment_analysis(text)

        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}\n{traceback.format_exc()}")
            return self._basic_sentiment_analysis(text)

    async def generate_intelligent_response(
        self,
        message: str,
        customer: Optional[Customer] = None,
        conversation_history: Optional[List[WhatsAppMessage]] = None
    ) -> str:
        """Generate an intelligent response using Restaurant AI Agent."""
        try:
            # Convert conversation history to the format expected by restaurant agent
            conversation_list = []
            if conversation_history:
                conversation_list = [
                    {
                        "body": msg.message_body,
                        "from": "customer" if msg.direction == "inbound" else "restaurant"
                    }
                    for msg in conversation_history
                ]

            # Use restaurant AI agent for intelligent response generation
            response = await self.restaurant_agent.generate_intelligent_response(
                message=message,
                conversation_history=conversation_list,
                customer_id=str(customer.id) if customer else None,
                language="ar" if self._is_arabic_text(message) else "en"
            )

            # Log the interaction
            await self._log_ai_interaction(
                customer_id=customer.id if customer else None,
                input_message=message,
                generated_response=response,
                context={"customer_id": str(customer.id) if customer else None}
            )

            return response

        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}\n{traceback.format_exc()}")
            # Fallback to a safe default response
            return self._get_fallback_response(message)

    async def analyze_customer_feedback(
        self,
        customer_id: UUID,
        feedback_text: str
    ) -> Dict[str, Any]:
        """Analyze customer feedback and extract insights."""
        try:
            # Get customer context
            customer = await self._get_customer(customer_id)

            # Analyze sentiment
            sentiment_result = await self.analyze_sentiment(
                text=feedback_text,
                context={"customer_name": customer.name if customer else None}
            )

            # Extract key topics and concerns
            topics = await self._extract_topics(feedback_text)

            # Generate actionable insights
            insights = await self._generate_insights(
                feedback_text,
                sentiment_result,
                topics
            )

            # Calculate priority score
            priority_score = self._calculate_priority_score(
                sentiment_result,
                topics,
                customer
            )

            return {
                "sentiment": sentiment_result,
                "topics": topics,
                "insights": insights,
                "priority_score": priority_score,
                "requires_followup": priority_score > 0.7,
                "analyzed_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error analyzing feedback: {str(e)}\n{traceback.format_exc()}")
            raise

    async def classify_message_intent(
        self,
        message: str
    ) -> Dict[str, Any]:
        """Classify the intent of an incoming message."""
        try:
            # Define intent categories
            intent_categories = [
                "reservation",
                "menu_inquiry",
                "complaint",
                "compliment",
                "hours_inquiry",
                "location_inquiry",
                "feedback",
                "general_inquiry",
                "order_status",
                "other"
            ]

            # Use AI to classify intent
            prompt = self._build_intent_classification_prompt(
                message,
                intent_categories
            )

            response = await self.openrouter_service.classify_intent(prompt)

            # Parse classification response
            classification = self._parse_classification_response(
                response,
                intent_categories
            )

            return classification

        except Exception as e:
            logger.error(f"Error classifying message intent: {str(e)}")
            return {
                "primary_intent": "general_inquiry",
                "confidence": 0.5,
                "secondary_intents": []
            }

    async def generate_personalized_message(
        self,
        customer: Customer,
        message_type: str,
        additional_context: Optional[Dict] = None
    ) -> str:
        """Generate a personalized message for a customer."""
        try:
            # Build customer profile
            profile = await self._build_customer_profile(customer)

            # Generate message based on type
            if message_type == "welcome_back":
                message = await self._generate_welcome_back_message(profile)
            elif message_type == "follow_up":
                message = await self._generate_follow_up_message(profile)
            elif message_type == "promotion":
                message = await self._generate_promotional_message(profile)
            elif message_type == "feedback_request":
                message = await self._generate_feedback_request(profile)
            else:
                message = await self._generate_generic_message(profile, message_type)

            return message

        except Exception as e:
            logger.error(f"Error generating personalized message: {str(e)}")
            return self._get_fallback_message(message_type)

    async def analyze_conversation_quality(
        self,
        conversation_messages: List[WhatsAppMessage]
    ) -> Dict[str, Any]:
        """Analyze the quality of a conversation."""
        try:
            # Calculate metrics
            response_times = self._calculate_response_times(conversation_messages)
            sentiment_progression = await self._analyze_sentiment_progression(
                conversation_messages
            )
            resolution_status = self._determine_resolution_status(
                conversation_messages
            )

            # Generate quality score
            quality_score = self._calculate_conversation_quality_score(
                response_times,
                sentiment_progression,
                resolution_status
            )

            return {
                "quality_score": quality_score,
                "average_response_time": sum(response_times) / len(response_times) if response_times else 0,
                "sentiment_progression": sentiment_progression,
                "resolution_status": resolution_status,
                "total_messages": len(conversation_messages),
                "recommendations": self._generate_quality_recommendations(quality_score)
            }

        except Exception as e:
            logger.error(f"Error analyzing conversation quality: {str(e)}")
            raise

    # Private helper methods
    def _build_sentiment_prompt(
        self,
        text: str,
        context: Optional[Dict] = None
    ) -> str:
        """Build prompt for sentiment analysis."""
        prompt = f"""Analyze the sentiment of the following customer message:

Message: "{text}"

Please provide:
1. Overall sentiment (positive, negative, neutral)
2. Sentiment strength (0-1 scale)
3. Key emotional indicators
4. Any specific concerns or compliments mentioned

Response format: JSON"""

        if context:
            prompt += f"\n\nAdditional context: {json.dumps(context)}"

        return prompt

    def _parse_sentiment_response(self, response: str) -> Dict[str, Any]:
        """Parse sentiment analysis response."""
        try:
            # Attempt to parse as JSON
            if isinstance(response, str):
                return json.loads(response)
            return response
        except:
            # Fallback parsing
            return {
                "sentiment": "neutral",
                "strength": 0.5,
                "indicators": [],
                "concerns": []
            }

    def _calculate_sentiment_score(self, sentiment_data: Dict) -> float:
        """Calculate numerical sentiment score."""
        strength = sentiment_data.get("strength", 0.5)
        sentiment = sentiment_data.get("sentiment", "neutral").lower()

        if sentiment == "positive":
            return 0.5 + (strength * 0.5)
        elif sentiment == "negative":
            return 0.5 - (strength * 0.5)
        else:
            return 0.5

    def _categorize_sentiment(self, score: float) -> str:
        """Categorize sentiment based on score."""
        if score >= 0.7:
            return "positive"
        elif score <= 0.3:
            return "negative"
        else:
            return "neutral"

    async def _build_conversation_context(
        self,
        customer: Optional[Customer],
        history: Optional[List[WhatsAppMessage]]
    ) -> Dict[str, Any]:
        """Build conversation context for AI response generation."""
        context = {
            "timestamp": datetime.utcnow().isoformat(),
            "customer": None,
            "conversation_history": [],
            "previous_interactions": 0
        }

        if customer:
            context["customer"] = {
                "name": customer.name,
                "phone": customer.phone_number,
                "previous_visits": len(customer.visit_history) if customer.visit_history else 0,
                "last_sentiment": customer.sentiment_category,
                "vip_status": getattr(customer, "vip_status", False)
            }

        if history:
            context["conversation_history"] = [
                {
                    "message": msg.message_body,
                    "direction": msg.direction,
                    "timestamp": msg.created_at.isoformat()
                }
                for msg in history[-5:]  # Last 5 messages for context
            ]
            context["previous_interactions"] = len(history)

        return context

    async def _get_customer(self, customer_id: UUID) -> Optional[Customer]:
        """Get customer by ID."""
        stmt = select(Customer).where(Customer.id == customer_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _log_ai_interaction(
        self,
        customer_id: Optional[UUID],
        input_message: str,
        generated_response: str,
        context: Dict
    ):
        """Log AI interaction for analysis and improvement."""
        # This could be extended to save to a dedicated AI interactions table
        logger.info(f"AI Interaction - Customer: {customer_id}, Input: {input_message[:50]}...")

    async def _extract_topics(self, text: str) -> List[str]:
        """Extract key topics from text."""
        # Simplified topic extraction
        # Could be enhanced with NLP libraries or AI
        topics = []

        keywords = {
            "food": ["food", "meal", "dish", "menu", "taste", "flavor"],
            "service": ["service", "staff", "waiter", "waitress", "server"],
            "ambiance": ["ambiance", "atmosphere", "environment", "music", "lighting"],
            "price": ["price", "cost", "expensive", "cheap", "value"],
            "cleanliness": ["clean", "dirty", "hygiene", "sanitary"]
        }

        text_lower = text.lower()
        for topic, words in keywords.items():
            if any(word in text_lower for word in words):
                topics.append(topic)

        return topics

    async def _generate_insights(
        self,
        feedback: str,
        sentiment: Dict,
        topics: List[str]
    ) -> List[str]:
        """Generate actionable insights from feedback."""
        insights = []

        if sentiment.get("sentiment_category") == "negative":
            insights.append("Immediate follow-up recommended due to negative sentiment")

        if "service" in topics and sentiment.get("sentiment_score", 0.5) < 0.4:
            insights.append("Service quality issue detected - staff training may be needed")

        if "food" in topics and sentiment.get("sentiment_score", 0.5) < 0.4:
            insights.append("Food quality concern - kitchen review recommended")

        if len(topics) > 3:
            insights.append("Multiple areas of concern - comprehensive review needed")

        return insights

    def _calculate_priority_score(
        self,
        sentiment: Dict,
        topics: List[str],
        customer: Optional[Customer]
    ) -> float:
        """Calculate priority score for feedback."""
        score = 0.5

        # Adjust based on sentiment
        sentiment_score = sentiment.get("sentiment_score", 0.5)
        if sentiment_score < 0.3:
            score += 0.3
        elif sentiment_score > 0.7:
            score -= 0.2

        # Adjust based on number of topics
        score += len(topics) * 0.05

        # Adjust based on customer history
        if customer and customer.visit_history:
            if len(customer.visit_history) > 5:
                score += 0.1  # Loyal customer

        return min(max(score, 0), 1)  # Clamp between 0 and 1

    def _build_intent_classification_prompt(
        self,
        message: str,
        categories: List[str]
    ) -> str:
        """Build prompt for intent classification."""
        return f"""Classify the following message into one of these categories:
{', '.join(categories)}

Message: "{message}"

Provide the primary intent and confidence level (0-1)."""

    def _parse_classification_response(
        self,
        response: str,
        categories: List[str]
    ) -> Dict[str, Any]:
        """Parse intent classification response."""
        # Simplified parsing - could be enhanced
        return {
            "primary_intent": "general_inquiry",
            "confidence": 0.7,
            "secondary_intents": []
        }

    async def _build_customer_profile(self, customer: Customer) -> Dict[str, Any]:
        """Build comprehensive customer profile."""
        return {
            "name": customer.name,
            "phone": customer.phone_number,
            "visit_count": len(customer.visit_history) if customer.visit_history else 0,
            "last_visit": customer.visit_date.isoformat() if customer.visit_date else None,
            "sentiment": customer.sentiment_category,
            "preferences": getattr(customer, "preferences", {})
        }

    async def _generate_welcome_back_message(self, profile: Dict) -> str:
        """Generate welcome back message."""
        name = profile.get("name", "Valued Customer")
        visit_count = profile.get("visit_count", 0)

        if visit_count > 5:
            return f"Welcome back, {name}! As one of our valued regular customers, we're delighted to see you again!"
        else:
            return f"Welcome back, {name}! We're so glad you've chosen to dine with us again."

    async def _generate_follow_up_message(self, profile: Dict) -> str:
        """Generate follow-up message."""
        name = profile.get("name", "Valued Customer")
        return f"Hi {name}, we hope you enjoyed your recent visit. We'd love to hear about your experience!"

    async def _generate_promotional_message(self, profile: Dict) -> str:
        """Generate promotional message."""
        name = profile.get("name", "")
        greeting = f"Hi {name}!" if name else "Hello!"
        return f"{greeting} We have an exclusive offer just for you. Enjoy 20% off your next visit!"

    async def _generate_feedback_request(self, profile: Dict) -> str:
        """Generate feedback request message."""
        name = profile.get("name", "")
        greeting = f"Hi {name}," if name else "Hello,"
        return f"{greeting} your opinion matters to us! Please take a moment to share your feedback about your recent experience."

    async def _generate_generic_message(
        self,
        profile: Dict,
        message_type: str
    ) -> str:
        """Generate generic personalized message."""
        name = profile.get("name", "Valued Customer")
        return f"Hi {name}, thank you for being our customer!"

    def _get_fallback_message(self, message_type: str) -> str:
        """Get fallback message for errors."""
        fallbacks = {
            "welcome_back": "Welcome back! We're glad to see you again.",
            "follow_up": "Thank you for your recent visit. We hope to see you again soon!",
            "promotion": "Check out our latest offers and promotions!",
            "feedback_request": "We'd love to hear your feedback!",
        }
        return fallbacks.get(message_type, "Thank you for contacting us!")

    def _calculate_response_times(
        self,
        messages: List[WhatsAppMessage]
    ) -> List[float]:
        """Calculate response times between messages."""
        response_times = []

        for i in range(1, len(messages)):
            if messages[i].direction != messages[i-1].direction:
                time_diff = (messages[i].created_at - messages[i-1].created_at).total_seconds()
                response_times.append(time_diff)

        return response_times

    async def _analyze_sentiment_progression(
        self,
        messages: List[WhatsAppMessage]
    ) -> List[float]:
        """Analyze how sentiment changes throughout conversation."""
        sentiments = []

        for msg in messages:
            if msg.direction == "inbound":
                result = await self.analyze_sentiment(msg.message_body)
                sentiments.append(result.get("sentiment_score", 0.5))

        return sentiments

    def _determine_resolution_status(
        self,
        messages: List[WhatsAppMessage]
    ) -> str:
        """Determine if conversation reached resolution."""
        if not messages:
            return "unknown"

        last_message = messages[-1]

        # Simple heuristics - could be enhanced
        resolution_keywords = ["thanks", "thank you", "perfect", "great", "solved", "resolved"]
        if any(keyword in last_message.message_body.lower() for keyword in resolution_keywords):
            return "resolved"

        if last_message.direction == "outbound":
            return "pending_customer_response"

        return "ongoing"

    def _calculate_conversation_quality_score(
        self,
        response_times: List[float],
        sentiment_progression: List[float],
        resolution_status: str
    ) -> float:
        """Calculate overall conversation quality score."""
        score = 0.5

        # Factor in response times
        if response_times:
            avg_response = sum(response_times) / len(response_times)
            if avg_response < 60:  # Less than 1 minute
                score += 0.2
            elif avg_response < 300:  # Less than 5 minutes
                score += 0.1

        # Factor in sentiment improvement
        if sentiment_progression and len(sentiment_progression) > 1:
            if sentiment_progression[-1] > sentiment_progression[0]:
                score += 0.2

        # Factor in resolution
        if resolution_status == "resolved":
            score += 0.1

        return min(max(score, 0), 1)

    def _generate_quality_recommendations(self, quality_score: float) -> List[str]:
        """Generate recommendations based on quality score."""
        recommendations = []

        if quality_score < 0.5:
            recommendations.append("Consider additional staff training on customer service")
            recommendations.append("Review response time targets")

        if quality_score < 0.7:
            recommendations.append("Monitor customer satisfaction more closely")

        if quality_score > 0.8:
            recommendations.append("Current performance is excellent - maintain standards")

        return recommendations

    def _is_arabic_text(self, text: str) -> bool:
        """Check if text contains Arabic characters."""
        if not text:
            return False

        arabic_chars = sum(1 for char in text if '\u0600' <= char <= '\u06FF')
        return arabic_chars > len(text) * 0.3

    def _basic_sentiment_analysis(self, text: str) -> Dict[str, Any]:
        """Basic keyword-based sentiment analysis as fallback."""
        if not text:
            return {
                "sentiment_score": 0.5,
                "sentiment_category": "neutral",
                "error": "Empty text"
            }

        text_lower = text.lower()

        positive_words = [
            "excellent", "great", "amazing", "wonderful", "fantastic", "perfect",
            "delicious", "tasty", "fresh", "friendly", "helpful", "fast", "clean",
            "love", "recommend", "satisfied", "happy", "pleased",
            # Arabic positive words
            "ممتاز", "رائع", "جميل", "حلو", "لذيذ", "طيب", "أعجبني", "شكرا"
        ]

        negative_words = [
            "terrible", "awful", "horrible", "disgusting", "slow", "rude", "dirty",
            "cold", "expensive", "bad", "worst", "hate", "never", "disappointed",
            "angry", "upset", "complaint", "problem", "issue",
            # Arabic negative words
            "سيء", "مش حلو", "ما عجبني", "تعبان", "مشكلة", "شكوى"
        ]

        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            sentiment = "positive"
            score = 0.6 + (positive_count * 0.1)
        elif negative_count > positive_count:
            sentiment = "negative"
            score = 0.4 - (negative_count * 0.1)
        else:
            sentiment = "neutral"
            score = 0.5

        # Clamp score between 0 and 1
        score = max(0.0, min(1.0, score))

        return {
            "sentiment_score": score,
            "sentiment_category": sentiment,
            "sentiment_details": {
                "confidence": 0.4,  # Low confidence for basic analysis
                "positive_indicators": positive_count,
                "negative_indicators": negative_count
            },
            "analyzed_at": datetime.utcnow().isoformat()
        }

    def _get_fallback_response(self, message: str) -> str:
        """Get fallback response when AI services fail."""
        if self._is_arabic_text(message):
            return "أهلاً وسهلاً! شكرًا لتواصلكم معنا. سيقوم أحد أعضاء فريقنا بالرد عليكم قريباً."
        else:
            return "Hello! Thank you for contacting us. A team member will respond to you shortly."