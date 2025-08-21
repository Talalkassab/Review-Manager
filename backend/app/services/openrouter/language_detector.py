"""
Language Detection Service for OpenRouter integration.
Automatically detects Arabic vs English and routes to appropriate models.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from functools import lru_cache

from .types import Language, LanguageDetectionResult

logger = logging.getLogger(__name__)


class LanguageDetector:
    """
    Language detection service optimized for Arabic and English text.
    
    Features:
    - Fast rule-based detection for Arabic/English
    - Context-aware detection
    - Mixed language handling
    - Cultural context indicators
    """
    
    def __init__(self):
        """Initialize the language detector."""
        # Arabic Unicode ranges
        self.arabic_range = (0x0600, 0x06FF)  # Arabic
        self.arabic_supplement_range = (0x0750, 0x077F)  # Arabic Supplement
        self.arabic_extended_range = (0x08A0, 0x08FF)  # Arabic Extended-A
        
        # Common Arabic words for context
        self.arabic_common_words = {
            'مرحبا', 'أهلا', 'شكرا', 'من', 'في', 'على', 'إلى', 'مع', 'هذا', 'ذلك',
            'التي', 'الذي', 'لكن', 'ولكن', 'أيضا', 'كذلك', 'حتى', 'عند', 'عندما',
            'مطعم', 'طعام', 'خدمة', 'طلب', 'حجز', 'موعد', 'وجبة', 'قائمة', 'أكل',
            'شراب', 'مشروب', 'حلو', 'مالح', 'طازج', 'لذيذ', 'ممتاز', 'جيد', 'سيء',
            'نظيف', 'سريع', 'بطيء', 'ساخن', 'بارد', 'جديد', 'قديم', 'كبير', 'صغير'
        }
        
        # Common English words
        self.english_common_words = {
            'the', 'and', 'to', 'of', 'a', 'in', 'is', 'it', 'you', 'that',
            'he', 'was', 'for', 'on', 'are', 'as', 'with', 'his', 'they', 'i',
            'restaurant', 'food', 'service', 'order', 'booking', 'reservation',
            'meal', 'menu', 'eat', 'drink', 'sweet', 'salty', 'fresh', 'delicious',
            'excellent', 'good', 'bad', 'clean', 'fast', 'slow', 'hot', 'cold'
        }
        
        # Restaurant/food context keywords
        self.food_context_arabic = {
            'مطعم', 'مقهى', 'كافيه', 'مطبخ', 'شيف', 'طباخ', 'نادل', 'خدمة',
            'فطار', 'غداء', 'عشاء', 'وجبة', 'طبق', 'سلطة', 'شوربة', 'لحم',
            'دجاج', 'سمك', 'خضار', 'فواكه', 'حلويات', 'مشروبات', 'عصير',
            'شاي', 'قهوة', 'ماء', 'حليب', 'خبز', 'أرز', 'معكرونة'
        }
        
        self.food_context_english = {
            'restaurant', 'cafe', 'kitchen', 'chef', 'cook', 'waiter', 'service',
            'breakfast', 'lunch', 'dinner', 'meal', 'dish', 'salad', 'soup', 'meat',
            'chicken', 'fish', 'vegetables', 'fruits', 'desserts', 'drinks', 'juice',
            'tea', 'coffee', 'water', 'milk', 'bread', 'rice', 'pasta'
        }
        
        logger.info("Language detector initialized")
    
    async def detect_language(
        self, text: str, context: Optional[Dict] = None
    ) -> LanguageDetectionResult:
        """
        Detect the primary language of the given text.
        
        Args:
            text: Text to analyze
            context: Optional context information
            
        Returns:
            LanguageDetectionResult with detected language and confidence
        """
        if not text or not text.strip():
            return LanguageDetectionResult(
                detected_language=Language.ENGLISH,
                confidence=0.5,
                is_mixed=False
            )
        
        # Clean and normalize text
        cleaned_text = self._clean_text(text)
        
        # Count characters by script
        arabic_chars, latin_chars, other_chars = self._count_character_types(cleaned_text)
        total_chars = arabic_chars + latin_chars + other_chars
        
        if total_chars == 0:
            return LanguageDetectionResult(
                detected_language=Language.ENGLISH,
                confidence=0.5,
                is_mixed=False
            )
        
        # Calculate script ratios
        arabic_ratio = arabic_chars / total_chars
        latin_ratio = latin_chars / total_chars
        
        # Check for mixed language content
        is_mixed = arabic_ratio > 0.1 and latin_ratio > 0.1
        
        # Word-based analysis
        arabic_word_score = self._calculate_word_score(cleaned_text, self.arabic_common_words)
        english_word_score = self._calculate_word_score(cleaned_text, self.english_common_words)
        
        # Context-based scoring
        context_score_ar = self._calculate_context_score(cleaned_text, self.food_context_arabic)
        context_score_en = self._calculate_context_score(cleaned_text, self.food_context_english)
        
        # Combined scoring
        arabic_total_score = (
            arabic_ratio * 0.6 +           # Character ratio weight
            arabic_word_score * 0.3 +      # Word frequency weight
            context_score_ar * 0.1         # Context weight
        )
        
        english_total_score = (
            latin_ratio * 0.6 +
            english_word_score * 0.3 +
            context_score_en * 0.1
        )
        
        # Determine language and confidence
        if arabic_total_score > english_total_score:
            detected_language = Language.ARABIC
            confidence = min(0.95, arabic_total_score)
        else:
            detected_language = Language.ENGLISH
            confidence = min(0.95, english_total_score)
        
        # Boost confidence for clear cases
        if arabic_ratio > 0.7:
            detected_language = Language.ARABIC
            confidence = max(confidence, 0.9)
        elif latin_ratio > 0.8 and arabic_ratio < 0.1:
            detected_language = Language.ENGLISH
            confidence = max(confidence, 0.9)
        
        # Lower confidence for mixed content
        if is_mixed:
            confidence *= 0.8
        
        logger.debug(
            f"Language detection: {detected_language} "
            f"(confidence: {confidence:.2f}, mixed: {is_mixed})"
        )
        
        return LanguageDetectionResult(
            detected_language=detected_language,
            confidence=confidence,
            is_mixed=is_mixed
        )
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for analysis."""
        # Remove URLs, emails, phone numbers
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
        text = re.sub(r'\+?[\d\s\-\(\)]{10,}', '', text)
        
        # Remove excessive whitespace and punctuation
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]', ' ', text)
        
        return text.strip().lower()
    
    def _count_character_types(self, text: str) -> Tuple[int, int, int]:
        """Count Arabic, Latin, and other characters in text."""
        arabic_count = 0
        latin_count = 0
        other_count = 0
        
        for char in text:
            char_code = ord(char)
            if (self.arabic_range[0] <= char_code <= self.arabic_range[1] or
                self.arabic_supplement_range[0] <= char_code <= self.arabic_supplement_range[1] or
                self.arabic_extended_range[0] <= char_code <= self.arabic_extended_range[1]):
                arabic_count += 1
            elif char.isalpha() and char.isascii():
                latin_count += 1
            elif char.isalpha():
                other_count += 1
        
        return arabic_count, latin_count, other_count
    
    @lru_cache(maxsize=1000)
    def _calculate_word_score(self, text: str, word_set: set) -> float:
        """Calculate word frequency score for a given word set."""
        words = text.split()
        if not words:
            return 0.0
        
        matches = sum(1 for word in words if word in word_set)
        return matches / len(words)
    
    @lru_cache(maxsize=1000)
    def _calculate_context_score(self, text: str, context_words: set) -> float:
        """Calculate context-specific score based on domain words."""
        words = text.split()
        if not words:
            return 0.0
        
        matches = sum(1 for word in words if word in context_words)
        # Give higher weight to context matches
        return min(1.0, (matches / max(1, len(words))) * 3)
    
    async def detect_batch(
        self, texts: List[str], context: Optional[Dict] = None
    ) -> List[LanguageDetectionResult]:
        """Detect language for multiple texts efficiently."""
        results = []
        for text in texts:
            result = await self.detect_language(text, context)
            results.append(result)
        return results
    
    def is_arabic_text(self, text: str, threshold: float = 0.7) -> bool:
        """Quick check if text is predominantly Arabic."""
        if not text.strip():
            return False
        
        arabic_chars, latin_chars, _ = self._count_character_types(text.lower())
        total_letters = arabic_chars + latin_chars
        
        if total_letters == 0:
            return False
        
        return (arabic_chars / total_letters) >= threshold
    
    def is_english_text(self, text: str, threshold: float = 0.7) -> bool:
        """Quick check if text is predominantly English."""
        if not text.strip():
            return True  # Default to English for empty text
        
        arabic_chars, latin_chars, _ = self._count_character_types(text.lower())
        total_letters = arabic_chars + latin_chars
        
        if total_letters == 0:
            return True  # Default to English for non-letter text
        
        return (latin_chars / total_letters) >= threshold
    
    def get_language_statistics(self, text: str) -> Dict[str, float]:
        """Get detailed language statistics for text."""
        cleaned_text = self._clean_text(text)
        arabic_chars, latin_chars, other_chars = self._count_character_types(cleaned_text)
        total_chars = arabic_chars + latin_chars + other_chars
        
        if total_chars == 0:
            return {
                "arabic_ratio": 0.0,
                "english_ratio": 0.0,
                "other_ratio": 0.0,
                "arabic_words": 0.0,
                "english_words": 0.0,
                "food_context_arabic": 0.0,
                "food_context_english": 0.0
            }
        
        return {
            "arabic_ratio": arabic_chars / total_chars,
            "english_ratio": latin_chars / total_chars,
            "other_ratio": other_chars / total_chars,
            "arabic_words": self._calculate_word_score(cleaned_text, self.arabic_common_words),
            "english_words": self._calculate_word_score(cleaned_text, self.english_common_words),
            "food_context_arabic": self._calculate_context_score(cleaned_text, self.food_context_arabic),
            "food_context_english": self._calculate_context_score(cleaned_text, self.food_context_english)
        }
    
    def suggest_language_model(
        self, detection_result: LanguageDetectionResult
    ) -> Dict[str, any]:
        """Suggest appropriate model based on language detection."""
        recommendations = {
            "primary_language": detection_result.detected_language,
            "confidence": detection_result.confidence,
            "is_mixed": detection_result.is_mixed
        }
        
        if detection_result.detected_language == Language.ARABIC:
            if detection_result.confidence > 0.8:
                recommendations["suggested_models"] = [
                    "anthropic/claude-3.5-haiku",  # Best for Arabic
                    "anthropic/claude-3-haiku",
                    "openai/gpt-4o-mini"
                ]
            else:
                recommendations["suggested_models"] = [
                    "openai/gpt-4o-mini",  # Better for mixed content
                    "anthropic/claude-3.5-haiku",
                    "anthropic/claude-instant-1.2"
                ]
        else:  # English
            recommendations["suggested_models"] = [
                "openai/gpt-4o-mini",
                "anthropic/claude-3.5-haiku",
                "meta-llama/llama-3.1-8b-instruct:free"
            ]
        
        if detection_result.is_mixed:
            recommendations["note"] = "Mixed language content detected. Consider using a model with strong multilingual capabilities."
        
        return recommendations
    
    async def analyze_conversation_language(
        self, messages: List[str]
    ) -> Dict[str, any]:
        """Analyze language patterns across a conversation."""
        if not messages:
            return {"primary_language": Language.ENGLISH, "language_switches": 0}
        
        detections = await self.detect_batch(messages)
        
        # Count language switches
        language_switches = 0
        prev_language = None
        
        language_counts = {Language.ARABIC: 0, Language.ENGLISH: 0}
        
        for detection in detections:
            language_counts[detection.detected_language] += 1
            
            if prev_language and prev_language != detection.detected_language:
                language_switches += 1
            prev_language = detection.detected_language
        
        # Determine primary language
        primary_language = max(language_counts, key=language_counts.get)
        
        return {
            "primary_language": primary_language,
            "language_counts": language_counts,
            "language_switches": language_switches,
            "is_multilingual": language_switches > 0,
            "consistency_score": max(language_counts.values()) / len(messages),
            "detections": detections
        }