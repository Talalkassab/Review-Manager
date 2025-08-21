"""
Text processing tool for natural language operations
"""
from typing import Dict, Any, List, Optional
import re
from .base_tool import BaseAgentTool, ToolResult


class TextProcessingTool(BaseAgentTool):
    """Tool for text processing and natural language operations"""
    
    name: str = "text_processor"
    description: str = (
        "Process text for language detection, cleaning, tokenization, "
        "keyword extraction, and linguistic analysis."
    )
    
    def _validate_input(self, **kwargs) -> bool:
        """Validate text processing parameters"""
        operation = kwargs.get('operation')
        text = kwargs.get('text')
        
        if not operation:
            self.logger.error("Operation parameter is required")
            return False
            
        if not text and operation != 'batch_process':
            self.logger.error("Text parameter is required for this operation")
            return False
        
        valid_operations = [
            'clean_text', 'detect_language', 'extract_keywords',
            'tokenize', 'extract_entities', 'sentiment_indicators',
            'batch_process', 'normalize_text'
        ]
        
        if operation not in valid_operations:
            self.logger.error(f"Invalid operation: {operation}")
            return False
            
        return True
    
    def _execute(self, **kwargs) -> Dict[str, Any]:
        """Execute text processing operation"""
        operation = kwargs.get('operation')
        text = kwargs.get('text', '')
        
        try:
            if operation == 'clean_text':
                return self._clean_text(text, kwargs.get('cleaning_options', {}))
            elif operation == 'detect_language':
                return self._detect_language(text)
            elif operation == 'extract_keywords':
                return self._extract_keywords(text, kwargs.get('language'), kwargs.get('max_keywords', 10))
            elif operation == 'tokenize':
                return self._tokenize_text(text, kwargs.get('language'))
            elif operation == 'extract_entities':
                return self._extract_entities(text, kwargs.get('language'))
            elif operation == 'sentiment_indicators':
                return self._extract_sentiment_indicators(text, kwargs.get('language'))
            elif operation == 'batch_process':
                return self._batch_process(kwargs.get('texts', []), kwargs.get('operations', []))
            elif operation == 'normalize_text':
                return self._normalize_text(text, kwargs.get('language'))
            else:
                raise ValueError(f"Unsupported operation: {operation}")
                
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Text processing failed: {str(e)}"
            ).dict()
    
    def _clean_text(self, text: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and preprocess text"""
        cleaned = text
        cleaning_steps = []
        
        # Remove extra whitespace
        if options.get('remove_extra_whitespace', True):
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            cleaning_steps.append("removed_extra_whitespace")
        
        # Remove URLs
        if options.get('remove_urls', True):
            url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            cleaned = re.sub(url_pattern, '', cleaned)
            cleaning_steps.append("removed_urls")
        
        # Remove email addresses
        if options.get('remove_emails', True):
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            cleaned = re.sub(email_pattern, '', cleaned)
            cleaning_steps.append("removed_emails")
        
        # Remove phone numbers
        if options.get('remove_phones', True):
            # Saudi phone number patterns
            phone_patterns = [
                r'\+966\s?\d{1,2}\s?\d{3}\s?\d{4}',  # +966 format
                r'05\d{8}',                          # 05xxxxxxxx format
                r'\d{3}-\d{3}-\d{4}'                 # xxx-xxx-xxxx format
            ]
            for pattern in phone_patterns:
                cleaned = re.sub(pattern, '', cleaned)
            cleaning_steps.append("removed_phone_numbers")
        
        # Remove special characters (keep Arabic and English)
        if options.get('remove_special_chars', False):
            # Keep Arabic, English, numbers, and basic punctuation
            cleaned = re.sub(r'[^\u0600-\u06FF\u0750-\u077F\w\s\.\,\!\?\:\;\-\'\"]', '', cleaned)
            cleaning_steps.append("removed_special_characters")
        
        # Convert to lowercase (for English text)
        if options.get('lowercase', False) and not self._contains_arabic(cleaned):
            cleaned = cleaned.lower()
            cleaning_steps.append("converted_to_lowercase")
        
        # Remove diacritics from Arabic text
        if options.get('remove_arabic_diacritics', True) and self._contains_arabic(cleaned):
            diacritics = '\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652\u0653\u0654\u0655\u0656\u0657\u0658\u0659\u065A\u065B\u065C\u065D\u065E\u065F'
            cleaned = ''.join(c for c in cleaned if c not in diacritics)
            cleaning_steps.append("removed_arabic_diacritics")
        
        result_data = {
            "original_text": text,
            "cleaned_text": cleaned,
            "original_length": len(text),
            "cleaned_length": len(cleaned),
            "reduction_percentage": round((len(text) - len(cleaned)) / len(text) * 100, 2) if text else 0,
            "cleaning_steps_applied": cleaning_steps
        }
        
        return ToolResult(
            success=True,
            data=result_data,
            metadata={"operation": "clean_text"}
        ).dict()
    
    def _detect_language(self, text: str) -> Dict[str, Any]:
        """Detect language of text"""
        # Simple language detection based on character sets
        arabic_chars = set('\u0600-\u06FF\u0750-\u077F')
        english_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
        
        arabic_count = sum(1 for c in text if '\u0600' <= c <= '\u06FF' or '\u0750' <= c <= '\u077F')
        english_count = sum(1 for c in text if c in english_chars)
        total_chars = len(text.replace(' ', ''))  # Exclude spaces
        
        if total_chars == 0:
            language = "unknown"
            confidence = 0
        elif arabic_count > english_count and arabic_count > total_chars * 0.3:
            language = "ar"
            confidence = arabic_count / total_chars
        elif english_count > arabic_count and english_count > total_chars * 0.3:
            language = "en"
            confidence = english_count / total_chars
        else:
            language = "mixed"
            confidence = max(arabic_count, english_count) / total_chars if total_chars > 0 else 0
        
        # Additional language indicators
        arabic_indicators = ['في', 'من', 'إلى', 'على', 'هذا', 'التي', 'الله', 'ما']
        english_indicators = ['the', 'and', 'is', 'in', 'to', 'of', 'a', 'that']
        
        arabic_indicator_count = sum(1 for indicator in arabic_indicators if indicator in text)
        english_indicator_count = sum(1 for indicator in english_indicators if indicator.lower() in text.lower())
        
        result_data = {
            "detected_language": language,
            "confidence": round(confidence, 3),
            "character_analysis": {
                "arabic_chars": arabic_count,
                "english_chars": english_count,
                "total_chars": total_chars,
                "arabic_percentage": round(arabic_count / total_chars * 100, 1) if total_chars > 0 else 0,
                "english_percentage": round(english_count / total_chars * 100, 1) if total_chars > 0 else 0
            },
            "language_indicators": {
                "arabic_indicators_found": arabic_indicator_count,
                "english_indicators_found": english_indicator_count
            },
            "is_multilingual": language == "mixed",
            "primary_script": "arabic" if arabic_count > english_count else "latin"
        }
        
        return ToolResult(
            success=True,
            data=result_data,
            metadata={"operation": "detect_language"}
        ).dict()
    
    def _extract_keywords(self, text: str, language: Optional[str] = None, max_keywords: int = 10) -> Dict[str, Any]:
        """Extract keywords from text"""
        if not language:
            lang_detection = self._detect_language(text)
            language = lang_detection['data']['detected_language']
        
        # Clean text first
        clean_result = self._clean_text(text, {"remove_extra_whitespace": True})
        cleaned_text = clean_result['data']['cleaned_text']
        
        # Tokenize
        tokens = self._simple_tokenize(cleaned_text, language)
        
        # Remove stop words
        stop_words = self._get_stop_words(language)
        filtered_tokens = [token for token in tokens if token.lower() not in stop_words and len(token) > 2]
        
        # Count frequency
        word_freq = {}
        for token in filtered_tokens:
            word_freq[token] = word_freq.get(token, 0) + 1
        
        # Sort by frequency and take top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = sorted_words[:max_keywords]
        
        # Calculate keyword scores (TF-IDF simplified)
        total_words = len(filtered_tokens)
        keyword_data = []
        
        for word, freq in keywords:
            tf = freq / total_words
            # Simplified IDF (would use corpus in real implementation)
            idf = 1.0
            score = tf * idf
            
            keyword_data.append({
                "word": word,
                "frequency": freq,
                "tf_score": round(tf, 4),
                "relevance_score": round(score, 4)
            })
        
        result_data = {
            "keywords": keyword_data,
            "total_unique_words": len(word_freq),
            "total_words_processed": total_words,
            "language": language,
            "extraction_method": "frequency_based"
        }
        
        return ToolResult(
            success=True,
            data=result_data,
            metadata={"operation": "extract_keywords"}
        ).dict()
    
    def _tokenize_text(self, text: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Tokenize text into words, sentences, and other units"""
        if not language:
            lang_detection = self._detect_language(text)
            language = lang_detection['data']['detected_language']
        
        # Word tokenization
        words = self._simple_tokenize(text, language)
        
        # Sentence tokenization
        sentences = self._sentence_tokenize(text, language)
        
        # Character-level stats
        char_count = len(text)
        char_count_no_spaces = len(text.replace(' ', ''))
        
        # Punctuation analysis
        punctuation_chars = set('.,!?;:-()[]{}"\'''""')
        punctuation_count = sum(1 for c in text if c in punctuation_chars)
        
        result_data = {
            "words": words,
            "sentences": sentences,
            "statistics": {
                "word_count": len(words),
                "sentence_count": len(sentences),
                "character_count": char_count,
                "character_count_no_spaces": char_count_no_spaces,
                "punctuation_count": punctuation_count,
                "average_word_length": round(sum(len(w) for w in words) / len(words), 2) if words else 0,
                "average_sentence_length": round(len(words) / len(sentences), 2) if sentences else 0
            },
            "language": language
        }
        
        return ToolResult(
            success=True,
            data=result_data,
            metadata={"operation": "tokenize"}
        ).dict()
    
    def _extract_entities(self, text: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Extract named entities from text (simplified implementation)"""
        if not language:
            lang_detection = self._detect_language(text)
            language = lang_detection['data']['detected_language']
        
        entities = {
            "persons": [],
            "locations": [],
            "organizations": [],
            "phone_numbers": [],
            "emails": [],
            "dates": [],
            "times": [],
            "money": []
        }
        
        # Phone numbers
        phone_patterns = [
            r'\+966\s?\d{1,2}\s?\d{3}\s?\d{4}',  # +966 format
            r'05\d{8}',                          # 05xxxxxxxx format
            r'\d{3}-\d{3}-\d{4}'                 # xxx-xxx-xxxx format
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            entities["phone_numbers"].extend(matches)
        
        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        entities["emails"].extend(re.findall(email_pattern, text))
        
        # Dates (simplified patterns)
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',      # DD/MM/YYYY
            r'\d{4}-\d{1,2}-\d{1,2}',      # YYYY-MM-DD
            r'\d{1,2}-\d{1,2}-\d{4}'       # DD-MM-YYYY
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            entities["dates"].extend(matches)
        
        # Times
        time_patterns = [
            r'\d{1,2}:\d{2}\s?(?:AM|PM|am|pm)',  # 12:30 PM
            r'\d{1,2}:\d{2}',                    # 14:30
            r'\d{1,2}\s?(?:AM|PM|am|pm)'         # 2 PM
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, text)
            entities["times"].extend(matches)
        
        # Money (Saudi Riyal and common currencies)
        money_patterns = [
            r'\d+\s?(?:ريال|SR|SAR)',           # Saudi Riyal
            r'\d+\s?(?:درهم|AED)',              # UAE Dirham
            r'\$\d+',                           # US Dollar
            r'\d+\s?(?:USD|EUR|GBP)'            # Other currencies
        ]
        
        for pattern in money_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities["money"].extend(matches)
        
        # Simple location detection (would use NLP library in production)
        if language == 'ar':
            location_keywords = ['الرياض', 'جدة', 'الدمام', 'مكة', 'المدينة', 'الطائف', 'أبها', 'تبوك']
        else:
            location_keywords = ['Riyadh', 'Jeddah', 'Dammam', 'Mecca', 'Medina', 'Taif', 'Abha', 'Tabuk']
        
        for keyword in location_keywords:
            if keyword in text:
                entities["locations"].append(keyword)
        
        # Count total entities found
        total_entities = sum(len(entity_list) for entity_list in entities.values())
        
        result_data = {
            "entities": entities,
            "entity_counts": {key: len(value) for key, value in entities.items()},
            "total_entities_found": total_entities,
            "language": language
        }
        
        return ToolResult(
            success=True,
            data=result_data,
            metadata={"operation": "extract_entities"}
        ).dict()
    
    def _extract_sentiment_indicators(self, text: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Extract words and phrases that indicate sentiment"""
        if not language:
            lang_detection = self._detect_language(text)
            language = lang_detection['data']['detected_language']
        
        sentiment_words = {
            "positive": [],
            "negative": [],
            "neutral": []
        }
        
        # Define sentiment word lists
        if language == 'ar':
            positive_words = [
                'ممتاز', 'رائع', 'جميل', 'حلو', 'مذهل', 'خيالي', 'روعة', 'تحفة', 
                'أعجبني', 'سعيد', 'مسرور', 'راضي', 'شكراً', 'ممكن', 'الله يعطيكم العافية'
            ]
            negative_words = [
                'سيء', 'مقرف', 'كارثة', 'فاشل', 'مو زين', 'خايس', 'مخيب', 'ضعيف',
                'مو حلو', 'ما عجبني', 'زعلان', 'غاضب', 'منزعج', 'محبط', 'مستاء'
            ]
            neutral_words = [
                'عادي', 'متوسط', 'لا بأس', 'مقبول', 'كذا', 'ماشي', 'تمام'
            ]
        else:
            positive_words = [
                'excellent', 'amazing', 'great', 'wonderful', 'fantastic', 'perfect', 
                'love', 'good', 'nice', 'delicious', 'happy', 'satisfied', 'pleased'
            ]
            negative_words = [
                'terrible', 'awful', 'bad', 'horrible', 'worst', 'disappointing',
                'poor', 'unacceptable', 'disgusting', 'angry', 'frustrated', 'upset'
            ]
            neutral_words = [
                'okay', 'average', 'normal', 'regular', 'fine', 'acceptable'
            ]
        
        # Find sentiment words in text
        text_lower = text.lower()
        
        for word in positive_words:
            if word in text_lower:
                sentiment_words["positive"].append(word)
        
        for word in negative_words:
            if word in text_lower:
                sentiment_words["negative"].append(word)
                
        for word in neutral_words:
            if word in text_lower:
                sentiment_words["neutral"].append(word)
        
        # Calculate sentiment scores
        positive_score = len(sentiment_words["positive"])
        negative_score = len(sentiment_words["negative"])
        neutral_score = len(sentiment_words["neutral"])
        
        total_sentiment_words = positive_score + negative_score + neutral_score
        
        # Determine overall sentiment
        if positive_score > negative_score:
            overall_sentiment = "positive"
            confidence = positive_score / total_sentiment_words if total_sentiment_words > 0 else 0
        elif negative_score > positive_score:
            overall_sentiment = "negative"
            confidence = negative_score / total_sentiment_words if total_sentiment_words > 0 else 0
        else:
            overall_sentiment = "neutral"
            confidence = neutral_score / total_sentiment_words if total_sentiment_words > 0 else 0.5
        
        # Detect intensity modifiers
        intensifiers = self._find_intensifiers(text, language)
        
        result_data = {
            "sentiment_words": sentiment_words,
            "sentiment_scores": {
                "positive": positive_score,
                "negative": negative_score,
                "neutral": neutral_score
            },
            "overall_sentiment": overall_sentiment,
            "confidence": round(confidence, 3),
            "intensifiers": intensifiers,
            "total_sentiment_indicators": total_sentiment_words,
            "language": language
        }
        
        return ToolResult(
            success=True,
            data=result_data,
            metadata={"operation": "sentiment_indicators"}
        ).dict()
    
    def _batch_process(self, texts: List[str], operations: List[str]) -> Dict[str, Any]:
        """Process multiple texts with multiple operations"""
        if not texts or not operations:
            return ToolResult(
                success=False,
                error="Both texts and operations are required"
            ).dict()
        
        batch_results = []
        
        for i, text in enumerate(texts):
            text_results = {"text_index": i, "text_preview": text[:50] + "..." if len(text) > 50 else text}
            
            for operation in operations:
                try:
                    result = self._execute(operation=operation, text=text)
                    text_results[operation] = result['data'] if result.get('success') else result.get('error')
                except Exception as e:
                    text_results[operation] = f"Error: {str(e)}"
            
            batch_results.append(text_results)
        
        # Aggregate statistics
        total_processed = len(texts)
        successful_operations = sum(
            1 for result in batch_results 
            for op in operations 
            if not isinstance(result.get(op), str) or not result.get(op, '').startswith('Error')
        )
        
        result_data = {
            "batch_results": batch_results,
            "summary": {
                "total_texts_processed": total_processed,
                "operations_performed": operations,
                "successful_operations": successful_operations,
                "success_rate": round(successful_operations / (total_processed * len(operations)) * 100, 2)
            }
        }
        
        return ToolResult(
            success=True,
            data=result_data,
            metadata={"operation": "batch_process"}
        ).dict()
    
    def _normalize_text(self, text: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Normalize text for consistent processing"""
        if not language:
            lang_detection = self._detect_language(text)
            language = lang_detection['data']['detected_language']
        
        normalized = text
        normalization_steps = []
        
        # Unicode normalization
        import unicodedata
        normalized = unicodedata.normalize('NFKD', normalized)
        normalization_steps.append("unicode_normalization")
        
        # Arabic-specific normalization
        if language == 'ar':
            # Normalize Arabic letters
            arabic_normalizations = {
                'أ': 'ا', 'إ': 'ا', 'آ': 'ا',  # Alif variations
                'ة': 'ه',  # Ta marbuta to Ha
                'ى': 'ي',  # Alif maksura to Ya
            }
            
            for original, replacement in arabic_normalizations.items():
                normalized = normalized.replace(original, replacement)
            
            normalization_steps.append("arabic_letter_normalization")
        
        # English-specific normalization
        elif language == 'en':
            # Convert to lowercase
            normalized = normalized.lower()
            normalization_steps.append("lowercase_conversion")
            
            # Normalize contractions
            contractions = {
                "won't": "will not",
                "can't": "cannot",
                "n't": " not",
                "'re": " are",
                "'ve": " have",
                "'ll": " will",
                "'d": " would",
                "'m": " am"
            }
            
            for contraction, expansion in contractions.items():
                normalized = normalized.replace(contraction, expansion)
            
            normalization_steps.append("contraction_expansion")
        
        # General normalizations
        # Multiple spaces to single space
        normalized = re.sub(r'\s+', ' ', normalized)
        normalization_steps.append("whitespace_normalization")
        
        # Remove leading/trailing whitespace
        normalized = normalized.strip()
        normalization_steps.append("trim_whitespace")
        
        result_data = {
            "original_text": text,
            "normalized_text": normalized,
            "language": language,
            "normalization_steps": normalization_steps,
            "length_change": len(normalized) - len(text)
        }
        
        return ToolResult(
            success=True,
            data=result_data,
            metadata={"operation": "normalize_text"}
        ).dict()
    
    # Helper methods
    def _contains_arabic(self, text: str) -> bool:
        """Check if text contains Arabic characters"""
        arabic_pattern = r'[\u0600-\u06FF\u0750-\u077F]'
        return bool(re.search(arabic_pattern, text))
    
    def _simple_tokenize(self, text: str, language: str) -> List[str]:
        """Simple word tokenization"""
        if language == 'ar':
            # Arabic tokenization - split on spaces and punctuation
            tokens = re.findall(r'[\u0600-\u06FF\u0750-\u077F]+', text)
        else:
            # English tokenization
            tokens = re.findall(r'\b\w+\b', text.lower())
        
        return [token for token in tokens if len(token) > 1]
    
    def _sentence_tokenize(self, text: str, language: str) -> List[str]:
        """Simple sentence tokenization"""
        # Split on sentence-ending punctuation
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def _get_stop_words(self, language: str) -> set:
        """Get stop words for the language"""
        if language == 'ar':
            return {
                'في', 'من', 'إلى', 'على', 'عن', 'مع', 'هذا', 'هذه', 'التي', 'التي',
                'الذي', 'التي', 'كان', 'كانت', 'يكون', 'تكون', 'هو', 'هي', 'أن',
                'إن', 'قد', 'لقد', 'كل', 'بعض', 'غير', 'سوى', 'أم', 'أو', 'لكن',
                'لكن', 'أما', 'إما', 'إذا', 'لو', 'كيف', 'متى', 'أين', 'ماذا'
            }
        else:
            return {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
                'before', 'after', 'above', 'below', 'between', 'among', 'this', 'that',
                'these', 'those', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours',
                'ourselves', 'you', 'your', 'yours', 'yourself', 'yourselves', 'he',
                'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its',
                'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what',
                'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is',
                'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
                'having', 'do', 'does', 'did', 'doing', 'will', 'would', 'should',
                'could', 'can', 'may', 'might', 'must', 'ought', 'shall'
            }
    
    def _find_intensifiers(self, text: str, language: str) -> List[str]:
        """Find words that intensify sentiment"""
        intensifiers = []
        text_lower = text.lower()
        
        if language == 'ar':
            arabic_intensifiers = ['جداً', 'كثير', 'جيد جداً', 'سيء جداً', 'للغاية', 'أكثر من اللازم', 'مفرط']
            for intensifier in arabic_intensifiers:
                if intensifier in text_lower:
                    intensifiers.append(intensifier)
        else:
            english_intensifiers = ['very', 'extremely', 'really', 'quite', 'absolutely', 'completely', 'totally', 'incredibly']
            for intensifier in english_intensifiers:
                if intensifier in text_lower:
                    intensifiers.append(intensifier)
        
        return intensifiers