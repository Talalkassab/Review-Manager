"""
Restaurant AI Agent - Intelligent conversational agent for restaurant customer service.
Provides natural language understanding and contextual responses in Arabic and English.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

from .openrouter_service import OpenRouterService, ModelType
from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)


class ConversationState(Enum):
    """States in the conversation flow"""
    GREETING = "greeting"
    MENU_INQUIRY = "menu_inquiry"
    FEEDBACK_COLLECTION = "feedback_collection"
    COMPLAINT_HANDLING = "complaint_handling"
    GENERAL_CHAT = "general_chat"
    GOOGLE_REVIEW_REQUEST = "google_review_request"
    CLOSING = "closing"


class RestaurantAIAgent:
    """
    Intelligent AI agent for restaurant customer service.
    Handles natural language conversations, menu inquiries, and feedback collection.
    """
    
    def __init__(self):
        self.openrouter = OpenRouterService()
        self.restaurant_context = self._load_restaurant_context()
        self.conversation_memory = {}  # Store conversation history per customer
        
    def _load_restaurant_context(self) -> str:
        """Load comprehensive restaurant information and context"""
        return """
أنت مساعد ذكي لمطعم فاخر في السعودية. اسم المطعم "مطعم الأصالة".

معلومات المطعم:
- الموقع: الرياض، حي العليا
- نوع المطعم: مطعم شعبي فاخر يقدم الأكلات السعودية الأصيلة
- أوقات العمل: من 11 صباحاً إلى 12 منتصف الليل
- رقم الهاتف: 0112345678
- التقييم: 4.8/5 نجوم على جوجل

قائمة الطعام:

الأطباق الرئيسية:
• كبسة لحم - 45 ريال (الأكثر مبيعاً) - لحم غنم طري مع أرز بسمتي والتوابل السعودية الأصيلة
• مندي دجاج - 38 ريال (شعبي جداً) - دجاج مدخن على الحطب مع الأرز المنكه
• كبسة دجاج - 35 ريال - دجاج طازج مع الأرز والخضار
• مضغوط لحم - 48 ريال - لحم مطبوخ بالطريقة اليمنية الأصيلة
• برياني دجاج - 32 ريال - أرز بسمتي مع الدجاج والبهارات الهندية

المقبلات والسلطات:
• فتوش - 18 ريال - سلطة شامية مع الخبز المحمص
• تبولة - 16 ريال - سلطة بقدونس طازجة
• حمص - 14 ريال - حمص بالطحينة
• متبل - 15 ريال - باذنجان مشوي بالطحينة
• ورق عنب - 22 ريال - محشي بالأرز واللحم

المشروبات:
• شاي أحمر - 8 ريال (المشروب الأشهر)
• قهوة عربية - 10 ريال - قهوة بالهيل والزعفران
• عصائر طازجة - 12-15 ريال (برتقال، مانجو، فراولة)
• مياه - 5 ريال
• عصير ليمون نعناع - 14 ريال

الحلويات:
• كنافة - 25 ريال (الحلى الأشهر) - كنافة بالجبن والقشطة
• بقلاوة - 20 ريال - حلى شرقي بالفستق
• أم علي - 18 ريال - حلى مصري بالمكسرات
• مهلبية - 15 ريال - حلى بالحليب والورد

العروض الخاصة:
• وجبة عائلية (تكفي 4 أشخاص): كبسة لحم + مقبلات + مشروبات = 150 ريال
• عرض الغداء (12-3 مساءً): أي طبق رئيسي + سلطة + مشروب = خصم 15%
• عرض نهاية الأسبوع: احصل على حلى مجاني مع أي وجبة تزيد عن 50 ريال

الخدمات المتوفرة:
• توصيل مجاني (للطلبات فوق 40 ريال)
• قاعات مناسبات خاصة
• خدمة كيترينج للفعاليات
• موقف سيارات مجاني
• واي فاي مجاني
• مكان للعائلات وقسم خاص للرجال

أسلوب التواصل:
- تحدث بطريقة مهذبة ومحترمة
- استخدم اللهجة السعودية الودودة
- اظهر الاهتمام الحقيقي بالعميل
- قدم اقتراحات شخصية حسب تفضيلات العميل
- اطلب التقييم والمراجعة بطريقة لطيفة
- تذكر أن هدفك إسعاد العميل وبناء علاقة طويلة الأمد
"""

    async def generate_intelligent_response(
        self,
        message: str,
        conversation_history: List[Dict[str, str]] = None,
        customer_id: str = None,
        language: str = "ar"
    ) -> str:
        """
        Generate intelligent, contextual response using AI.
        
        Args:
            message: Current customer message
            conversation_history: Previous conversation messages
            customer_id: Unique customer identifier
            language: Preferred language ('ar' or 'en')
            
        Returns:
            Intelligent response text
        """
        try:
            # Update conversation memory
            if customer_id and conversation_history:
                self.conversation_memory[customer_id] = conversation_history[-10:]  # Keep last 10 messages
            
            # Analyze message intent and extract context
            intent_analysis = await self._analyze_message_intent(message, language)
            conversation_state = await self._determine_conversation_state(
                message, conversation_history, intent_analysis
            )
            
            # Build comprehensive prompt
            prompt = await self._build_intelligent_prompt(
                message=message,
                conversation_history=conversation_history or [],
                intent_analysis=intent_analysis,
                conversation_state=conversation_state,
                language=language
            )
            
            # Generate response using AI
            model_type = ModelType.CLAUDE_3_5_HAIKU  # Best for Arabic and cultural context
            ai_response = await self.openrouter.generate_response(
                prompt=prompt,
                model_type=model_type,
                language=language,
                context={
                    "task": "restaurant_conversation",
                    "intent": intent_analysis.get("primary_intent"),
                    "state": conversation_state.value,
                    "customer_id": customer_id
                }
            )
            
            if ai_response.get("success", False):
                response_text = ai_response["content"]
                
                # Post-process response for consistency
                processed_response = await self._post_process_response(
                    response_text, intent_analysis, conversation_state, language
                )
                
                logger.info(f"Generated intelligent response for intent: {intent_analysis.get('primary_intent')}")
                return processed_response
            else:
                logger.warning(f"AI response failed, using fallback: {ai_response.get('error')}")
                return await self._generate_fallback_response(message, language)
                
        except Exception as e:
            logger.error(f"Error generating intelligent response: {str(e)}")
            return await self._generate_fallback_response(message, language)
    
    async def _analyze_message_intent(self, message: str, language: str) -> Dict[str, Any]:
        """Analyze the customer message to understand intent and extract entities"""
        
        # Define intent patterns (enhanced for Arabic)
        intent_patterns = {
            "menu_inquiry": [
                # Arabic patterns
                "قائمة", "منيو", "أكل", "طعام", "وجبة", "أطباق", "الأكثر مبيعا", "الأشهر", 
                "أحسن طبق", "أفضل طبق", "تنصحني", "أيش عندكم", "إيش عندكم", "اقترح لي",
                "كبسة", "مندي", "برياني", "مضغوط", "حمص", "فتوش", "كنافة", "بقلاوة",
                # English patterns
                "menu", "food", "dish", "meal", "recommend", "best", "popular", "kabsa", "mandi"
            ],
            "price_inquiry": [
                "كم", "سعر", "ثمن", "تكلفة", "أسعار", "price", "cost", "how much", "كام", "بكام"
            ],
            "ordering": [
                "أريد", "أبغي", "عايز", "طلب", "أطلب", "order", "want", "would like", "احجز", "أحجز"
            ],
            "location_hours": [
                "فين", "وين", "موقع", "عنوان", "ساعات", "أوقات", "مفتوح", "مسكر", 
                "location", "address", "hours", "open", "closed", "where"
            ],
            "feedback_positive": [
                "شكرا", "ممتاز", "رائع", "جميل", "حلو", "لذيذ", "طيب", "أعجبني", 
                "thank", "excellent", "great", "good", "delicious", "amazing", "wonderful"
            ],
            "feedback_negative": [
                "سيء", "مش حلو", "ما عجبني", "تعبان", "مشكلة", "شكوى", 
                "bad", "terrible", "not good", "problem", "complaint", "issue"
            ],
            "google_review": [
                "تقييم", "مراجعة", "جوجل", "نجوم", "review", "rating", "google", "stars"
            ],
            "greeting": [
                "مرحبا", "أهلا", "السلام عليكم", "صباح الخير", "مساء الخير",
                "hello", "hi", "good morning", "good evening", "hey"
            ],
            "goodbye": [
                "باي", "مع السلامة", "شكرا وبس", "خلاص", "تسلم", 
                "bye", "goodbye", "thank you", "that's all"
            ]
        }
        
        message_lower = message.lower()
        detected_intents = []
        
        # Check for intent patterns
        for intent, patterns in intent_patterns.items():
            for pattern in patterns:
                if pattern in message_lower:
                    detected_intents.append(intent)
                    break
        
        # Determine primary intent
        primary_intent = detected_intents[0] if detected_intents else "general_inquiry"
        
        # Extract entities (menu items, prices, etc.)
        entities = await self._extract_entities(message, language)
        
        return {
            "primary_intent": primary_intent,
            "all_intents": detected_intents,
            "entities": entities,
            "confidence": 0.9 if detected_intents else 0.5,
            "message_language": self._detect_language(message)
        }
    
    async def _extract_entities(self, message: str, language: str) -> Dict[str, List[str]]:
        """Extract entities like menu items, numbers, etc. from the message"""
        
        entities = {
            "menu_items": [],
            "numbers": [],
            "locations": [],
            "times": []
        }
        
        # Menu items detection
        menu_items = [
            "كبسة", "مندي", "برياني", "مضغوط", "فتوش", "تبولة", "حمص", "متبل",
            "كنافة", "بقلاوة", "شاي", "قهوة", "kabsa", "mandi", "biryani"
        ]
        
        message_lower = message.lower()
        for item in menu_items:
            if item in message_lower:
                entities["menu_items"].append(item)
        
        # Extract numbers (for quantities, prices, etc.)
        import re
        numbers = re.findall(r'\d+', message)
        entities["numbers"] = numbers
        
        return entities
    
    def _detect_language(self, message: str) -> str:
        """Simple language detection based on Arabic characters"""
        arabic_chars = sum(1 for char in message if '\u0600' <= char <= '\u06FF')
        return "arabic" if arabic_chars > len(message) * 0.3 else "english"
    
    async def _determine_conversation_state(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
        intent_analysis: Dict[str, Any]
    ) -> ConversationState:
        """Determine the current state of conversation"""
        
        primary_intent = intent_analysis["primary_intent"]
        
        # Map intents to conversation states
        intent_to_state = {
            "greeting": ConversationState.GREETING,
            "menu_inquiry": ConversationState.MENU_INQUIRY,
            "price_inquiry": ConversationState.MENU_INQUIRY,
            "ordering": ConversationState.MENU_INQUIRY,
            "location_hours": ConversationState.GENERAL_CHAT,
            "feedback_positive": ConversationState.FEEDBACK_COLLECTION,
            "feedback_negative": ConversationState.COMPLAINT_HANDLING,
            "google_review": ConversationState.GOOGLE_REVIEW_REQUEST,
            "goodbye": ConversationState.CLOSING
        }
        
        return intent_to_state.get(primary_intent, ConversationState.GENERAL_CHAT)
    
    async def _build_intelligent_prompt(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
        intent_analysis: Dict[str, Any],
        conversation_state: ConversationState,
        language: str
    ) -> str:
        """Build comprehensive prompt for AI model"""
        
        # Start with restaurant context
        prompt = f"{self.restaurant_context}\n\n"
        
        # Add conversation history context
        if conversation_history:
            prompt += "المحادثة السابقة:\n" if language == "ar" else "Previous conversation:\n"
            for msg in conversation_history[-5:]:  # Last 5 messages for context
                speaker = "العميل" if msg.get("from") == "customer" else "المطعم"
                if language != "ar":
                    speaker = "Customer" if msg.get("from") == "customer" else "Restaurant"
                prompt += f"{speaker}: {msg.get('body', '')}\n"
            prompt += "\n"
        
        # Add intent-specific instructions
        intent = intent_analysis["primary_intent"]
        state_instructions = {
            ConversationState.GREETING: {
                "ar": "رحب بالعميل بحرارة وأظهر الاهتمام. اسأل عن كيفية المساعدة.",
                "en": "Warmly welcome the customer and show genuine interest. Ask how you can help."
            },
            ConversationState.MENU_INQUIRY: {
                "ar": "اشرح الأطباق المطلوبة بتفصيل. اذكر المكونات والأسعار. اقترح أطباقاً مشابهة.",
                "en": "Explain the requested dishes in detail. Mention ingredients and prices. Suggest similar dishes."
            },
            ConversationState.FEEDBACK_COLLECTION: {
                "ar": "اشكر العميل على التعليق الإيجابي. اطلب منه كتابة مراجعة على جوجل بلطف.",
                "en": "Thank the customer for positive feedback. Politely ask them to write a Google review."
            },
            ConversationState.COMPLAINT_HANDLING: {
                "ar": "اعتذر بصدق واظهر التفهم. اقترح حلولاً عملية واطلب فرصة أخرى.",
                "en": "Apologize sincerely and show understanding. Suggest practical solutions and ask for another chance."
            },
            ConversationState.GENERAL_CHAT: {
                "ar": "كن ودوداً ومساعداً. أجب على الأسئلة بدقة وقدم معلومات إضافية مفيدة.",
                "en": "Be friendly and helpful. Answer questions accurately and provide additional useful information."
            }
        }
        
        instruction = state_instructions.get(conversation_state, state_instructions[ConversationState.GENERAL_CHAT])
        prompt += f"التعليمات الخاصة: {instruction.get(language, instruction['ar'])}\n\n"
        
        # Add the current message
        prompt += f"رسالة العميل الحالية: {message}\n\n" if language == "ar" else f"Current customer message: {message}\n\n"
        
        # Add response guidelines
        guidelines = {
            "ar": """قواعد الرد:
1. اكتب ردك باللغة العربية بأسلوب سعودي ودود
2. كن مختصراً ومفيداً (لا تزيد عن 3 جمل)
3. اذكر أسعار الأطباق إذا سُئلت عنها
4. اقترح الأطباق الأكثر شعبية عند السؤال عن التوصيات
5. كن مهذباً ومحترماً دائماً
6. لا تضع رموز أو علامات خاصة، فقط النص العادي

ردك:""",
            "en": """Response guidelines:
1. Write your response in Arabic with a friendly Saudi style
2. Be concise and helpful (no more than 3 sentences)
3. Mention dish prices if asked about them
4. Suggest the most popular dishes when asked for recommendations
5. Always be polite and respectful
6. Don't use special symbols or marks, just plain text

Your response:"""
        }
        
        prompt += guidelines.get(language, guidelines["ar"])
        
        return prompt
    
    async def _post_process_response(
        self,
        response: str,
        intent_analysis: Dict[str, Any],
        conversation_state: ConversationState,
        language: str
    ) -> str:
        """Post-process AI response for consistency and quality"""
        
        # Clean up response
        response = response.strip()
        
        # Remove any unwanted prefixes or suffixes
        unwanted_prefixes = ["AI:", "Assistant:", "Bot:", "مساعد:", "الرد:"]
        for prefix in unwanted_prefixes:
            if response.startswith(prefix):
                response = response[len(prefix):].strip()
        
        # Ensure response isn't too long (WhatsApp limit consideration)
        if len(response) > 1000:
            sentences = response.split('.')
            response = '. '.join(sentences[:3]) + '.'
        
        # Add contextual closing if appropriate
        if conversation_state == ConversationState.MENU_INQUIRY and "شكرا" not in response:
            if language == "ar":
                response += " 🌟 هل تحتاج معلومات إضافية؟"
            else:
                response += " 🌟 Do you need any additional information?"
        
        return response
    
    async def _generate_fallback_response(self, message: str, language: str = "ar") -> str:
        """Generate fallback response when AI fails"""
        
        fallback_responses = {
            "ar": [
                "أهلاً وسهلاً! 🌟 كيف يمكنني مساعدتك اليوم؟ يمكنني إخبارك عن قائمة الطعام أو أوقات العمل.",
                "مرحباً بك في مطعم الأصالة! 🍽️ تفضل بالسؤال عن أي شيء تريد معرفته عن مطعمنا.",
                "أهلاً بك! 😊 إذا كان لديك سؤال محدد عن الطعام أو الخدمات، سأكون سعيداً بالمساعدة."
            ],
            "en": [
                "Welcome to Asala Restaurant! 🌟 How can I help you today? I can tell you about our menu or hours.",
                "Hello! 🍽️ Feel free to ask me anything about our restaurant.",
                "Welcome! 😊 If you have specific questions about food or services, I'll be happy to help."
            ]
        }
        
        import random
        responses = fallback_responses.get(language, fallback_responses["ar"])
        return random.choice(responses)
    
    async def analyze_customer_satisfaction(
        self,
        conversation_history: List[Dict[str, str]],
        customer_feedback: str = None
    ) -> Dict[str, Any]:
        """Analyze customer satisfaction from conversation"""
        
        try:
            # Prepare text for sentiment analysis
            conversation_text = ""
            if conversation_history:
                customer_messages = [
                    msg.get("body", "") 
                    for msg in conversation_history 
                    if msg.get("from") == "customer"
                ]
                conversation_text = " ".join(customer_messages)
            
            if customer_feedback:
                conversation_text += " " + customer_feedback
            
            if not conversation_text.strip():
                return {"satisfaction": "neutral", "confidence": 0.5}
            
            # Use OpenRouter for sentiment analysis
            sentiment_result = await self.openrouter.analyze_text_sentiment(
                text=conversation_text,
                language="arabic",
                detailed_analysis=True
            )
            
            if sentiment_result.get("sentiment"):
                return {
                    "satisfaction": sentiment_result["sentiment"].get("overall", "neutral"),
                    "confidence": sentiment_result["sentiment"].get("confidence", 0.5),
                    "details": sentiment_result["sentiment"],
                    "analysis_timestamp": datetime.now().isoformat()
                }
            else:
                return {"satisfaction": "neutral", "confidence": 0.5}
                
        except Exception as e:
            logger.error(f"Error analyzing customer satisfaction: {str(e)}")
            return {"satisfaction": "neutral", "confidence": 0.0, "error": str(e)}
    
    async def generate_review_request_message(
        self,
        customer_name: str = None,
        satisfaction_level: str = "positive",
        language: str = "ar"
    ) -> str:
        """Generate personalized Google review request message"""
        
        if satisfaction_level != "positive":
            return ""  # Don't request reviews from unsatisfied customers
        
        templates = {
            "ar": [
                f"{'عزيزي ' + customer_name if customer_name else 'عزيزي العميل'} 🌟\n\nيسعدنا أن تجربتك في مطعم الأصالة كانت مميزة! نتمنى أن تشاركنا تقييمك على جوجل لمساعدة عملاء آخرين في اكتشاف مطعمنا.\n\nشكراً لك! 💚",
                
                f"شكراً {'يا ' + customer_name if customer_name else ''} على زيارتك الجميلة! 🙏\n\nإذا أعجبتك تجربتك معنا، نكون ممتنين لو تقيمنا على جوجل. تقييمك مهم جداً بالنسبة لنا! ⭐"
            ],
            "en": [
                f"Dear {customer_name if customer_name else 'Valued Customer'} 🌟\n\nWe're delighted that your experience at Asala Restaurant was exceptional! We'd love for you to share your review on Google to help other customers discover our restaurant.\n\nThank you! 💚",
                
                f"Thank you {'dear ' + customer_name if customer_name else ''} for your wonderful visit! 🙏\n\nIf you enjoyed your experience with us, we'd be grateful if you could rate us on Google. Your review means a lot to us! ⭐"
            ]
        }
        
        import random
        messages = templates.get(language, templates["ar"])
        return random.choice(messages)
    
    async def get_restaurant_info(self, info_type: str = "general") -> Dict[str, Any]:
        """Get specific restaurant information"""
        
        info_data = {
            "general": {
                "name": "مطعم الأصالة",
                "name_en": "Asala Restaurant",
                "type": "Traditional Saudi Restaurant",
                "location": "Riyadh, Al Olaya District",
                "phone": "0112345678",
                "rating": 4.8,
                "hours": "11:00 AM - 12:00 AM"
            },
            "popular_items": [
                {"name": "كبسة لحم", "price": 45, "popularity": "highest"},
                {"name": "مندي دجاج", "price": 38, "popularity": "very_high"},
                {"name": "شاي أحمر", "price": 8, "popularity": "most_ordered_drink"},
                {"name": "كنافة", "price": 25, "popularity": "most_ordered_dessert"}
            ],
            "services": [
                "Free delivery (orders over 40 SAR)",
                "Private event halls",
                "Catering services",
                "Free parking",
                "Free WiFi",
                "Family and men's sections"
            ],
            "contact": {
                "phone": "0112345678",
                "address": "الرياض، حي العليا",
                "hours": "11:00 صباحاً - 12:00 منتصف الليل"
            }
        }
        
        return info_data.get(info_type, info_data["general"])


# Create global instance
restaurant_ai_agent = RestaurantAIAgent()