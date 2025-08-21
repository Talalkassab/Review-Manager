"""
Arabic Language and Cultural Context Handler.
Provides proper handling of Arabic text, RTL support, and cultural context awareness.
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum

from .types import ChatMessage, ConversationContext, RequestParameters, Language, MessageRole

logger = logging.getLogger(__name__)


class ArabicDialect(str, Enum):
    """Arabic dialect classifications."""
    MSA = "msa"                    # Modern Standard Arabic
    GULF = "gulf"                  # Gulf dialect (UAE, Saudi, Kuwait, etc.)
    LEVANTINE = "levantine"        # Levantine dialect (Syria, Lebanon, Jordan, Palestine)
    EGYPTIAN = "egyptian"          # Egyptian dialect
    MAGHREBI = "maghrebi"          # North African dialect (Morocco, Algeria, Tunisia)
    MIXED = "mixed"                # Mixed dialects or unclear


class CulturalContext(str, Enum):
    """Cultural context categories."""
    FORMAL = "formal"              # Formal business context
    CASUAL = "casual"              # Casual conversation
    RELIGIOUS = "religious"        # Religious context or timing
    FAMILY = "family"              # Family-oriented discussion
    HOSPITALITY = "hospitality"    # Hospitality and service context


class ArabicHandler:
    """
    Arabic language and cultural context handler.
    
    Features:
    - Arabic text processing and normalization
    - RTL text handling
    - Cultural context awareness
    - Dialect detection and adaptation
    - Religious and cultural sensitivity
    - Time-aware responses (prayer times, Ramadan, etc.)
    """
    
    def __init__(self):
        """Initialize the Arabic handler."""
        # Arabic text processing patterns
        self.arabic_patterns = {
            # Diacritics (tashkeel)
            "diacritics": re.compile(r'[\u064B-\u065F\u0670\u06D6-\u06ED]'),
            
            # Arabic letters
            "arabic_letters": re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]'),
            
            # Arabic numbers
            "arabic_numbers": re.compile(r'[\u06F0-\u06F9]'),
            
            # Common Arabic prefixes/suffixes
            "prefixes": re.compile(r'^(ال|لل|بال|كال|فال|وال)'),
            "suffixes": re.compile(r'(ها|هم|هن|نا|كم|كن|ني|تم|تن)$')
        }
        
        # Cultural keywords and contexts
        self.cultural_keywords = {
            "greetings": {
                "مرحبا", "أهلا", "سلام", "صباح الخير", "مساء الخير", "تحية",
                "السلام عليكم", "وعليكم السلام", "أهلا وسهلا"
            },
            "gratitude": {
                "شكرا", "شكرًا", "مشكور", "جزاك الله", "الله يعطيك العافية",
                "تسلم", "يعطيك العافية", "بارك الله فيك"
            },
            "apologies": {
                "آسف", "معذرة", "عفوا", "سامحني", "أعتذر", "المعذرة"
            },
            "religious": {
                "إن شاء الله", "الحمد لله", "ما شاء الله", "بسم الله", "جزاك الله خير",
                "الله يعطيك العافية", "ربنا يوفقك", "الله يحفظك", "بإذن الله"
            },
            "hospitality": {
                "تفضل", "تفضلي", "أهلا وسهلا", "مرحب", "حياك الله", "نورت",
                "شرفت", "منور", "عن إذنك", "لو سمحت"
            },
            "food_arabic": {
                "طعام", "أكل", "وجبة", "فطار", "غداء", "عشاء", "مطعم", "كافيه",
                "قهوة", "شاي", "عصير", "ماء", "لذيذ", "طازج", "حار", "بارد",
                "حلو", "مالح", "طبخ", "شيف", "نادل", "قائمة", "طلب", "حجز"
            }
        }
        
        # Dialect-specific variations
        self.dialect_variations = {
            ArabicDialect.GULF: {
                "what": ["شنو", "ايش", "وش"],
                "how": ["كيف", "جيف", "شلون"],
                "want": ["أبي", "أبغى", "ودي"],
                "good": ["زين", "طيب", "حلو"],
                "food": ["أكل", "طعام", "غداء"]
            },
            ArabicDialect.LEVANTINE: {
                "what": ["شو", "إيش", "أيش"],
                "how": ["كيف", "شلون"],
                "want": ["بدي", "عايز"],
                "good": ["منيح", "كويس", "حلو"],
                "food": ["أكل", "طعمة"]
            },
            ArabicDialect.EGYPTIAN: {
                "what": ["إيه", "أيه"],
                "how": ["إزاي", "كيف"],
                "want": ["عايز", "عاوز"],
                "good": ["كويس", "حلو", "جميل"],
                "food": ["أكل", "طعام"]
            }
        }
        
        # Religious and cultural timing awareness
        self.prayer_times = ["فجر", "ظهر", "عصر", "مغرب", "عشاء"]
        self.islamic_months = [
            "محرم", "صفر", "ربيع الأول", "ربيع الثاني", "جمادى الأولى", "جمادى الآخرة",
            "رجب", "شعبان", "رمضان", "شوال", "ذو القعدة", "ذو الحجة"
        ]
        
        logger.info("Arabic handler initialized")
    
    async def enhance_messages(
        self,
        messages: List[ChatMessage],
        context: ConversationContext
    ) -> List[ChatMessage]:
        """
        Enhance messages with Arabic cultural context and processing.
        
        Args:
            messages: List of chat messages
            context: Conversation context
            
        Returns:
            Enhanced messages with cultural context
        """
        enhanced_messages = []
        cultural_context = await self._analyze_cultural_context(messages, context)
        
        for message in messages:
            enhanced_message = await self._enhance_single_message(message, cultural_context, context)
            enhanced_messages.append(enhanced_message)
        
        # Add cultural system message if appropriate
        if messages and cultural_context.get("add_cultural_guidance", False):
            cultural_guidance = await self._generate_cultural_guidance(cultural_context)
            if cultural_guidance:
                system_message = ChatMessage(
                    role=MessageRole.SYSTEM,
                    content=cultural_guidance
                )
                enhanced_messages.insert(0, system_message)
        
        return enhanced_messages
    
    async def _enhance_single_message(
        self,
        message: ChatMessage,
        cultural_context: Dict[str, Any],
        context: ConversationContext
    ) -> ChatMessage:
        """Enhance a single message with Arabic processing."""
        if not message.content:
            return message
        
        # Normalize Arabic text
        normalized_content = self._normalize_arabic_text(message.content)
        
        # Add cultural markers if this is a user message
        if message.role == MessageRole.USER:
            # Detect dialect
            dialect = self._detect_dialect(normalized_content)
            if dialect != ArabicDialect.MIXED:
                cultural_context["detected_dialect"] = dialect
            
            # Mark cultural elements
            normalized_content = self._mark_cultural_elements(normalized_content)
        
        # Create enhanced message
        enhanced_message = ChatMessage(
            role=message.role,
            content=normalized_content,
            name=message.name
        )
        
        return enhanced_message
    
    def _normalize_arabic_text(self, text: str) -> str:
        """Normalize Arabic text for better processing."""
        if not text:
            return text
        
        # Remove excessive diacritics (keep some for context)
        normalized = self.arabic_patterns["diacritics"].sub("", text)
        
        # Normalize Arabic characters
        char_replacements = {
            'ي': 'ي',  # Normalize different forms of yeh
            'ى': 'ى',  # Alef maksura
            'ة': 'ة',  # Teh marbuta
            'ء': 'ء',  # Hamza
            'أ': 'أ',  # Alef with hamza above
            'إ': 'إ',  # Alef with hamza below
            'آ': 'آ',  # Alef with madda above
        }
        
        for old_char, new_char in char_replacements.items():
            normalized = normalized.replace(old_char, new_char)
        
        # Clean up whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _detect_dialect(self, text: str) -> ArabicDialect:
        """Detect Arabic dialect from text."""
        text_lower = text.lower()
        dialect_scores = {dialect: 0 for dialect in ArabicDialect}
        
        # Check for dialect-specific words
        for dialect, variations in self.dialect_variations.items():
            for category, words in variations.items():
                for word in words:
                    if word in text_lower:
                        dialect_scores[dialect] += 1
        
        # Find dialect with highest score
        if max(dialect_scores.values()) > 0:
            return max(dialect_scores, key=dialect_scores.get)
        
        return ArabicDialect.MSA  # Default to Modern Standard Arabic
    
    def _mark_cultural_elements(self, text: str) -> str:
        """Mark cultural elements in text for context awareness."""
        # This is a placeholder for more sophisticated cultural marking
        # In production, you might add metadata or special tokens
        
        # Check for religious expressions
        for phrase in self.cultural_keywords["religious"]:
            if phrase in text:
                # Add subtle marker (could be metadata in a real system)
                text = text.replace(phrase, f"{phrase} [religious]")
        
        return text
    
    async def _analyze_cultural_context(
        self,
        messages: List[ChatMessage],
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Analyze cultural context from messages."""
        cultural_analysis = {
            "formality_level": "casual",
            "religious_context": False,
            "hospitality_context": False,
            "time_sensitivity": False,
            "detected_dialect": ArabicDialect.MSA,
            "cultural_markers": [],
            "add_cultural_guidance": False
        }
        
        # Analyze recent messages
        recent_messages = messages[-5:] if len(messages) > 5 else messages
        all_text = " ".join([msg.content for msg in recent_messages if msg.content])
        
        # Check for cultural keywords
        for category, keywords in self.cultural_keywords.items():
            found_keywords = [kw for kw in keywords if kw in all_text]
            if found_keywords:
                cultural_analysis["cultural_markers"].append({
                    "category": category,
                    "keywords": found_keywords
                })
                
                if category == "religious":
                    cultural_analysis["religious_context"] = True
                elif category == "hospitality":
                    cultural_analysis["hospitality_context"] = True
        
        # Check time context (simplified)
        current_hour = datetime.utcnow().hour
        if 5 <= current_hour <= 7:  # Dawn/Fajr time
            cultural_analysis["time_sensitivity"] = True
            cultural_analysis["suggested_greeting"] = "صباح الخير"
        elif 11 <= current_hour <= 13:  # Noon/Dhuhr time
            cultural_analysis["time_sensitivity"] = True
        elif 17 <= current_hour <= 19:  # Evening/Maghrib time
            cultural_analysis["suggested_greeting"] = "مساء الخير"
        
        # Determine if cultural guidance should be added
        if (cultural_analysis["religious_context"] or 
            cultural_analysis["hospitality_context"]):
            cultural_analysis["add_cultural_guidance"] = True
        
        return cultural_analysis
    
    async def _generate_cultural_guidance(self, cultural_context: Dict[str, Any]) -> Optional[str]:
        """Generate cultural guidance for the AI model."""
        guidance_parts = [
            "أنت مساعد ذكي لمطعم يتحدث العربية بطريقة مهذبة ومحترمة."
        ]
        
        if cultural_context.get("religious_context"):
            guidance_parts.append(
                "كن حساسًا للسياق الديني واستخدم العبارات المناسبة مثل 'إن شاء الله' و'بارك الله فيك'."
            )
        
        if cultural_context.get("hospitality_context"):
            guidance_parts.append(
                "اظهر الضيافة العربية الأصيلة واستخدم عبارات الترحيب مثل 'أهلا وسهلا' و'تفضل'."
            )
        
        dialect = cultural_context.get("detected_dialect")
        if dialect and dialect != ArabicDialect.MSA:
            guidance_parts.append(
                f"تكيف مع اللهجة المحلية ({dialect}) مع الحفاظ على الوضوح والاحترام."
            )
        
        if cultural_context.get("time_sensitivity"):
            guidance_parts.append(
                "كن واعيًا للوقت والسياق الزمني في إجاباتك."
            )
        
        return " ".join(guidance_parts)
    
    async def adjust_parameters(self, params: RequestParameters) -> RequestParameters:
        """Adjust model parameters for Arabic language processing."""
        # Adjust temperature for more culturally appropriate responses
        adjusted_params = params.copy()
        
        # Slightly lower temperature for more consistent Arabic responses
        adjusted_params.temperature = max(0.3, params.temperature - 0.1)
        
        # Adjust frequency penalty to reduce repetition common in Arabic
        adjusted_params.frequency_penalty = min(1.0, params.frequency_penalty + 0.1)
        
        # Add Arabic-specific instructions if not present
        system_messages = [msg for msg in params.messages if msg.role == MessageRole.SYSTEM]
        if not system_messages:
            # Add Arabic context system message
            arabic_system_msg = ChatMessage(
                role=MessageRole.SYSTEM,
                content=(
                    "أنت مساعد ذكي لمطعم يتحدث العربية بطلاقة. "
                    "كن مهذبًا ومحترمًا واستخدم العبارات المناسبة ثقافيًا. "
                    "تذكر قيم الضيافة العربية والاحترام المتبادل."
                )
            )
            adjusted_params.messages.insert(0, arabic_system_msg)
        
        return adjusted_params
    
    def format_arabic_response(self, text: str) -> str:
        """Format Arabic text response for proper display."""
        if not text:
            return text
        
        # Ensure proper RTL markers for Arabic text
        formatted = text
        
        # Add RTL marker at the beginning if text starts with Arabic
        if self.arabic_patterns["arabic_letters"].search(text[:10]):
            formatted = f"\u202B{formatted}\u202C"  # RTL embedding
        
        # Clean up excessive punctuation
        formatted = re.sub(r'[.]{3,}', '...', formatted)
        formatted = re.sub(r'[!]{2,}', '!', formatted)
        formatted = re.sub(r'[?]{2,}', '?', formatted)
        
        # Ensure proper spacing around Arabic text
        formatted = re.sub(r'(\S)([\u0600-\u06FF])', r'\1 \2', formatted)
        formatted = re.sub(r'([\u0600-\u06FF])(\S)', r'\1 \2', formatted)
        
        return formatted.strip()
    
    def extract_arabic_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract Arabic entities like names, places, food items."""
        entities = {
            "food_items": [],
            "places": [],
            "names": [],
            "times": [],
            "numbers": []
        }
        
        # Extract food items
        food_patterns = [
            r'(كبسة|مندي|برياني|شاورما|فلافل|حمص|تبولة|فتوش|كنافة|معمول)',
            r'(قهوة|شاي|عصير|ماء|حليب|لبن)',
            r'(دجاج|لحم|سمك|جمبري|خضار)'
        ]
        
        for pattern in food_patterns:
            matches = re.findall(pattern, text)
            entities["food_items"].extend(matches)
        
        # Extract time expressions
        time_patterns = [
            r'(الفجر|الظهر|العصر|المغرب|العشاء)',
            r'(صباح|مساء|ليل|نهار)',
            r'(\d{1,2}:\d{2})'
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, text)
            entities["times"].extend(matches)
        
        # Extract Arabic numbers
        arabic_numbers = self.arabic_patterns["arabic_numbers"].findall(text)
        entities["numbers"].extend(arabic_numbers)
        
        return entities
    
    def get_cultural_suggestions(
        self, context_type: CulturalContext
    ) -> Dict[str, List[str]]:
        """Get cultural suggestions for different contexts."""
        suggestions = {
            CulturalContext.FORMAL: {
                "greetings": ["السلام عليكم", "أهلا وسهلا", "مرحبا بكم"],
                "closings": ["شكرا لكم", "بارك الله فيكم", "مع السلامة"],
                "courtesy": ["تفضلوا", "إن شاء الله", "بإذنكم"]
            },
            CulturalContext.CASUAL: {
                "greetings": ["مرحبا", "أهلا", "كيف الحال"],
                "closings": ["شكرا", "يسلموا", "مع السلامة"],
                "courtesy": ["تفضل", "يالله", "ان شالله"]
            },
            CulturalContext.HOSPITALITY: {
                "greetings": ["أهلا وسهلا", "مرحب فيك", "نورت المكان"],
                "service": ["تفضل", "خذ راحتك", "شو تحب نجيبلك"],
                "courtesy": ["عن إذنك", "لو سمحت", "كل الاحترام"]
            },
            CulturalContext.RELIGIOUS: {
                "expressions": ["بسم الله", "الحمد لله", "إن شاء الله"],
                "blessings": ["بارك الله فيك", "جزاك الله خير", "الله يعطيك العافية"],
                "timing": ["بعد الصلاة", "بإذن الله", "ربنا يوفقك"]
            }
        }
        
        return suggestions.get(context_type, {})
    
    def is_appropriate_time_for_food(self, current_time: datetime = None) -> Dict[str, Any]:
        """Check if current time is appropriate for different meals."""
        if not current_time:
            current_time = datetime.utcnow()
        
        hour = current_time.hour
        
        # Adjust for Middle East timezone (rough approximation)
        # In production, you'd use proper timezone handling
        middle_east_hour = (hour + 3) % 24
        
        meal_appropriateness = {
            "breakfast": 5 <= middle_east_hour <= 10,
            "lunch": 11 <= middle_east_hour <= 15,
            "dinner": 17 <= middle_east_hour <= 23,
            "late_night": 23 <= middle_east_hour or middle_east_hour <= 2
        }
        
        # Check for prayer times (approximate)
        prayer_considerations = {
            "near_maghrib": 17 <= middle_east_hour <= 19,  # Sunset prayer
            "near_fajr": 4 <= middle_east_hour <= 6,       # Dawn prayer
            "friday_prayer": current_time.weekday() == 4 and 11 <= middle_east_hour <= 13
        }
        
        return {
            "meal_times": meal_appropriateness,
            "prayer_considerations": prayer_considerations,
            "current_middle_east_hour": middle_east_hour
        }
    
    async def generate_culturally_appropriate_response_suggestions(
        self, context: ConversationContext
    ) -> List[str]:
        """Generate culturally appropriate response suggestions."""
        suggestions = []
        
        # Based on conversation context, suggest appropriate responses
        if context.cultural_context.get("hospitality_context"):
            suggestions.extend([
                "أهلا وسهلا، كيف يمكنني مساعدتك؟",
                "مرحب فيك، شو تحب تطلب اليوم؟",
                "نورت المطعم، تفضل شوف القائمة"
            ])
        
        if context.cultural_context.get("religious_context"):
            suggestions.extend([
                "بارك الله فيك، إن شاء الله نقدر نساعدك",
                "جزاك الله خير، شو تحب نحضرلك؟",
                "الله يعطيك العافية، تفضل"
            ])
        
        # Time-based suggestions
        time_info = self.is_appropriate_time_for_food()
        if time_info["meal_times"]["breakfast"]:
            suggestions.append("صباح الخير، عندنا فطار لذيذ اليوم")
        elif time_info["meal_times"]["lunch"]:
            suggestions.append("تفضل للغداء، عندنا أطباق مميزة")
        elif time_info["meal_times"]["dinner"]:
            suggestions.append("مساء الخير، شو رأيك بالعشاء عندنا؟")
        
        return suggestions[:5]  # Return top 5 suggestions