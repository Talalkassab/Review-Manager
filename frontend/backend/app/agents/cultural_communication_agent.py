"""
Cultural Communication Agent - Handles Arabic/English cultural nuances and appropriate messaging
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, time
import re
from .base_agent import BaseRestaurantAgent
from .tools import OpenRouterTool, TranslationTool, CulturalValidationTool


class CulturalCommunicationAgent(BaseRestaurantAgent):
    """
    Specialized agent for handling cultural nuances in Arabic and English communication.
    Ensures culturally appropriate, respectful, and effective messaging.
    """
    
    def __init__(self):
        super().__init__(
            role="Cultural Communication Specialist",
            goal="Ensure all customer communications are culturally appropriate, respectful, and effective in both Arabic and English contexts",
            backstory="""You are a cultural communication expert with deep understanding of Middle Eastern and Western cultural norms. 
            Fluent in both Arabic and English, you specialize in crafting messages that resonate with diverse audiences while maintaining 
            cultural sensitivity. You understand the importance of religious observances, social etiquette, and linguistic nuances 
            in the Gulf region. Your expertise ensures that every message strengthens customer relationships through cultural awareness.""",
            tools=[
                OpenRouterTool(),
                TranslationTool(),
                CulturalValidationTool()
            ],
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
        
        # Cultural knowledge base
        self.cultural_rules = {
            "arabic": {
                "greetings": {
                    "formal": ["السلام عليكم ورحمة الله وبركاته", "أهلاً وسهلاً", "حياكم الله"],
                    "casual": ["مرحباً", "أهلاً", "كيف حالك"],
                    "time_based": {
                        "morning": "صباح الخير",
                        "evening": "مساء الخير",
                        "night": "تصبح على خير"
                    }
                },
                "closings": {
                    "formal": ["مع السلامة", "في أمان الله", "دمتم بخير"],
                    "casual": ["مع السلامة", "إلى اللقاء", "نراكم قريباً"]
                },
                "religious_phrases": {
                    "thanks": ["الحمد لله", "جزاكم الله خيراً", "بارك الله فيكم"],
                    "wishes": ["ما شاء الله", "إن شاء الله", "بإذن الله"],
                    "occasions": {
                        "ramadan": ["رمضان مبارك", "رمضان كريم", "تقبل الله صيامكم"],
                        "eid": ["عيد مبارك", "كل عام وأنتم بخير", "عساكم من عواده"],
                        "friday": ["جمعة مباركة", "تقبل الله صلاتكم"]
                    }
                },
                "honorifics": {
                    "male": ["أستاذ", "سيد", "أخ"],
                    "female": ["أستاذة", "سيدة", "أخت"],
                    "respectful": ["حضرتك", "جنابك", "سعادتك"]
                },
                "taboo_topics": ["politics", "personal_relationships", "alcohol", "pork"],
                "communication_style": "indirect_respectful"
            },
            "english": {
                "greetings": {
                    "formal": ["Good day", "Welcome", "Greetings"],
                    "casual": ["Hello", "Hi", "Hey there"],
                    "time_based": {
                        "morning": "Good morning",
                        "afternoon": "Good afternoon",
                        "evening": "Good evening"
                    }
                },
                "closings": {
                    "formal": ["Best regards", "Sincerely", "Kind regards"],
                    "casual": ["Best", "Thanks", "See you soon"]
                },
                "honorifics": {
                    "male": ["Mr.", "Sir"],
                    "female": ["Ms.", "Ma'am"],
                    "neutral": ["Dear"]
                },
                "communication_style": "direct_friendly"
            }
        }
        
        # Prayer times (simplified - would integrate with actual prayer time API)
        self.prayer_times = {
            "fajr": (4, 30, 5, 30),      # 4:30 AM - 5:30 AM
            "dhuhr": (12, 0, 13, 0),     # 12:00 PM - 1:00 PM
            "asr": (15, 30, 16, 30),     # 3:30 PM - 4:30 PM
            "maghrib": (18, 0, 19, 0),   # 6:00 PM - 7:00 PM
            "isha": (19, 30, 20, 30)     # 7:30 PM - 8:30 PM
        }
        
        # Special dates and occasions
        self.cultural_calendar = {
            "ramadan": {"type": "islamic", "greeting": "رمضان مبارك"},
            "eid_al_fitr": {"type": "islamic", "greeting": "عيد مبارك"},
            "eid_al_adha": {"type": "islamic", "greeting": "عيد أضحى مبارك"},
            "national_day": {"type": "national", "greeting": "كل عام والوطن بخير"},
            "friday": {"type": "weekly", "greeting": "جمعة مباركة"}
        }
        
    def validate_cultural_appropriateness(self, message: str, language: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate if a message is culturally appropriate
        """
        self.log_task_start("validate_cultural_appropriateness", {"language": language})
        
        try:
            validation_result = {
                "is_appropriate": True,
                "issues": [],
                "suggestions": [],
                "cultural_score": 1.0
            }
            
            # Check for taboo topics
            if language == "ar" or context.get("target_culture") == "arabic":
                taboo_check = self._check_taboo_topics(message, "arabic")
                if taboo_check["found"]:
                    validation_result["is_appropriate"] = False
                    validation_result["issues"].extend(taboo_check["issues"])
                    validation_result["cultural_score"] -= 0.3
                    
            # Check religious sensitivity
            religious_check = self._check_religious_sensitivity(message, language)
            if religious_check["issues"]:
                validation_result["issues"].extend(religious_check["issues"])
                validation_result["suggestions"].extend(religious_check["suggestions"])
                validation_result["cultural_score"] -= 0.2
                
            # Check timing appropriateness
            timing_check = self._check_timing_appropriateness(context.get("send_time"), language)
            if not timing_check["appropriate"]:
                validation_result["issues"].append(timing_check["issue"])
                validation_result["suggestions"].append(timing_check["suggestion"])
                validation_result["cultural_score"] -= 0.1
                
            # Check formality level
            formality_check = self._check_formality_level(message, language, context)
            if formality_check["issues"]:
                validation_result["issues"].extend(formality_check["issues"])
                validation_result["suggestions"].extend(formality_check["suggestions"])
                
            # Generate improvement suggestions
            if validation_result["cultural_score"] < 1.0:
                improvements = self._generate_cultural_improvements(message, language, validation_result["issues"])
                validation_result["suggestions"].extend(improvements)
                
            self.log_task_complete("validate_cultural_appropriateness", validation_result)
            return validation_result
            
        except Exception as e:
            self.log_task_error("validate_cultural_appropriateness", e)
            raise
            
    def adapt_message_culturally(self, message: str, source_language: str, target_language: str, 
                                 context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adapt a message to be culturally appropriate for the target audience
        """
        self.log_task_start("adapt_message_culturally", {
            "source_language": source_language,
            "target_language": target_language
        })
        
        try:
            # Determine cultural context
            target_culture = "arabic" if target_language == "ar" else "english"
            
            # Add appropriate greeting
            greeting = self._select_appropriate_greeting(target_language, context)
            
            # Translate if needed
            if source_language != target_language:
                translated = self._translate_with_cultural_context(message, source_language, target_language)
            else:
                translated = message
                
            # Add cultural elements
            culturally_adapted = self._add_cultural_elements(translated, target_language, context)
            
            # Add appropriate closing
            closing = self._select_appropriate_closing(target_language, context)
            
            # Combine all parts
            final_message = self._compose_final_message(greeting, culturally_adapted, closing, target_language)
            
            # Validate the final message
            validation = self.validate_cultural_appropriateness(final_message, target_language, context)
            
            result = {
                "original_message": message,
                "adapted_message": final_message,
                "greeting_used": greeting,
                "closing_used": closing,
                "cultural_elements_added": self._identify_cultural_elements(final_message, target_language),
                "validation": validation,
                "language": target_language,
                "culture": target_culture
            }
            
            self.log_task_complete("adapt_message_culturally", result)
            return result
            
        except Exception as e:
            self.log_task_error("adapt_message_culturally", e)
            raise
            
    def handle_language_switching(self, conversation_history: List[Dict[str, Any]], 
                                 new_message: str) -> Dict[str, Any]:
        """
        Handle smooth language switching in conversations
        """
        self.log_task_start("handle_language_switching")
        
        try:
            # Detect language of new message
            detected_language = self._detect_language(new_message)
            
            # Get conversation language history
            language_history = [self._detect_language(msg["content"]) for msg in conversation_history]
            
            # Determine if switch occurred
            last_language = language_history[-1] if language_history else None
            switch_occurred = last_language and last_language != detected_language
            
            response = {
                "detected_language": detected_language,
                "previous_language": last_language,
                "switch_occurred": switch_occurred,
                "recommended_response_language": detected_language
            }
            
            if switch_occurred:
                # Generate transition phrase
                transition = self._generate_language_transition(last_language, detected_language)
                response["transition_phrase"] = transition
                
                # Update communication style
                response["communication_style"] = self._get_communication_style(detected_language)
                
            self.log_task_complete("handle_language_switching", response)
            return response
            
        except Exception as e:
            self.log_task_error("handle_language_switching", e)
            raise
            
    def ensure_religious_sensitivity(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure messages are religiously sensitive
        """
        self.log_task_start("ensure_religious_sensitivity")
        
        try:
            current_time = context.get("send_time", datetime.now())
            is_ramadan = context.get("is_ramadan", False)
            is_friday = current_time.weekday() == 4
            
            adjustments = []
            
            # Check if during prayer time
            prayer_time = self._get_current_prayer_time(current_time)
            if prayer_time:
                adjustments.append({
                    "type": "prayer_time",
                    "action": "delay_sending",
                    "reason": f"Currently during {prayer_time} prayer time",
                    "recommended_delay_minutes": 30
                })
                
            # Add Ramadan considerations
            if is_ramadan:
                if self._is_during_iftar_time(current_time):
                    adjustments.append({
                        "type": "iftar_time",
                        "action": "delay_sending",
                        "reason": "During Iftar time",
                        "recommended_delay_minutes": 60
                    })
                    
                # Add Ramadan greeting if not present
                if "رمضان" not in message:
                    adjustments.append({
                        "type": "ramadan_greeting",
                        "action": "add_greeting",
                        "greeting": "رمضان مبارك"
                    })
                    
            # Add Friday greeting if appropriate
            if is_friday and "جمعة" not in message:
                adjustments.append({
                    "type": "friday_greeting",
                    "action": "add_greeting",
                    "greeting": "جمعة مباركة"
                })
                
            result = {
                "original_message": message,
                "is_religiously_sensitive": len(adjustments) == 0,
                "adjustments_needed": adjustments,
                "final_message": self._apply_religious_adjustments(message, adjustments)
            }
            
            self.log_task_complete("ensure_religious_sensitivity", result)
            return result
            
        except Exception as e:
            self.log_task_error("ensure_religious_sensitivity", e)
            raise
            
    def generate_culturally_aware_response(self, customer_message: str, context: Dict[str, Any]) -> str:
        """
        Generate a culturally aware response to a customer message
        """
        self.log_task_start("generate_culturally_aware_response")
        
        try:
            # Detect language and sentiment
            language = self._detect_language(customer_message)
            sentiment = context.get("sentiment", "neutral")
            customer_profile = context.get("customer_profile", {})
            
            # Select appropriate cultural framework
            cultural_framework = self.cultural_rules[language if language == "ar" else "english"]
            
            # Generate base response
            base_response = self._generate_base_response(customer_message, sentiment, language)
            
            # Add cultural elements
            if language == "ar":
                response = self._add_arabic_cultural_elements(base_response, sentiment, customer_profile)
            else:
                response = self._add_english_cultural_elements(base_response, sentiment, customer_profile)
                
            # Add appropriate honorifics
            response = self._add_honorifics(response, customer_profile, language)
            
            # Ensure religious sensitivity
            religious_check = self.ensure_religious_sensitivity(response, context)
            final_response = religious_check["final_message"]
            
            self.log_task_complete("generate_culturally_aware_response", final_response)
            return final_response
            
        except Exception as e:
            self.log_task_error("generate_culturally_aware_response", e)
            raise
            
    def localize_content(self, content: str, target_region: str) -> Dict[str, Any]:
        """
        Localize content for specific regional variations
        """
        self.log_task_start("localize_content", {"target_region": target_region})
        
        try:
            regional_variations = {
                "saudi": {
                    "dialect": "gulf",
                    "currency": "SAR",
                    "date_format": "hijri_gregorian",
                    "specific_terms": {"restaurant": "مطعم", "bill": "فاتورة"}
                },
                "uae": {
                    "dialect": "gulf",
                    "currency": "AED",
                    "date_format": "gregorian",
                    "specific_terms": {"restaurant": "مطعم", "bill": "حساب"}
                },
                "egypt": {
                    "dialect": "egyptian",
                    "currency": "EGP",
                    "date_format": "gregorian",
                    "specific_terms": {"restaurant": "مطعم", "bill": "فاتورة"}
                },
                "levant": {
                    "dialect": "levantine",
                    "currency": "varies",
                    "date_format": "gregorian",
                    "specific_terms": {"restaurant": "مطعم", "bill": "حساب"}
                }
            }
            
            region_config = regional_variations.get(target_region.lower(), regional_variations["saudi"])
            
            # Apply regional dialect
            localized = self._apply_dialect(content, region_config["dialect"])
            
            # Replace currency symbols
            localized = self._localize_currency(localized, region_config["currency"])
            
            # Apply regional terms
            for general_term, regional_term in region_config["specific_terms"].items():
                localized = localized.replace(general_term, regional_term)
                
            result = {
                "original_content": content,
                "localized_content": localized,
                "region": target_region,
                "dialect_applied": region_config["dialect"],
                "modifications_made": self._track_modifications(content, localized)
            }
            
            self.log_task_complete("localize_content", result)
            return result
            
        except Exception as e:
            self.log_task_error("localize_content", e)
            raise
            
    # Private helper methods
    def _check_taboo_topics(self, message: str, culture: str) -> Dict[str, Any]:
        """Check for culturally taboo topics"""
        taboo_topics = self.cultural_rules[culture].get("taboo_topics", [])
        found_topics = []
        
        for topic in taboo_topics:
            # Simple keyword matching - could be enhanced with NLP
            if topic.lower() in message.lower():
                found_topics.append(topic)
                
        return {
            "found": len(found_topics) > 0,
            "issues": [f"Contains potentially sensitive topic: {topic}" for topic in found_topics]
        }
        
    def _check_religious_sensitivity(self, message: str, language: str) -> Dict[str, Any]:
        """Check for religious sensitivity issues"""
        issues = []
        suggestions = []
        
        # Check for inappropriate use of religious phrases
        if language == "ar":
            # Check if using Allah's name inappropriately
            if "الله" in message and any(neg in message for neg in ["لا", "ليس", "غير"]):
                issues.append("Potential inappropriate use of religious reference")
                suggestions.append("Review religious references for appropriateness")
                
        return {"issues": issues, "suggestions": suggestions}
        
    def _check_timing_appropriateness(self, send_time: Optional[datetime], language: str) -> Dict[str, Any]:
        """Check if timing is culturally appropriate"""
        if not send_time:
            send_time = datetime.now()
            
        current_prayer = self._get_current_prayer_time(send_time)
        
        if current_prayer and language == "ar":
            return {
                "appropriate": False,
                "issue": f"Scheduled during {current_prayer} prayer time",
                "suggestion": f"Delay sending until after {current_prayer} prayer"
            }
            
        # Check for late night messaging
        if send_time.hour >= 22 or send_time.hour < 6:
            return {
                "appropriate": False,
                "issue": "Scheduled during sleeping hours",
                "suggestion": "Schedule for business hours (8 AM - 10 PM)"
            }
            
        return {"appropriate": True}
        
    def _check_formality_level(self, message: str, language: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check if formality level is appropriate"""
        issues = []
        suggestions = []
        
        customer_age = context.get("customer_age")
        is_first_contact = context.get("is_first_contact", False)
        
        if language == "ar":
            # Check for appropriate honorifics with elderly customers
            if customer_age and customer_age > 50:
                if not any(honorific in message for honorific in self.cultural_rules["arabic"]["honorifics"]["respectful"]):
                    issues.append("Missing respectful honorific for elderly customer")
                    suggestions.append("Add respectful honorific like 'حضرتك' or 'سعادتك'")
                    
        # Check for overly casual language in first contact
        if is_first_contact:
            casual_indicators = ["hey", "هاي", "يا"]
            if any(indicator in message.lower() for indicator in casual_indicators):
                issues.append("Too casual for first contact")
                suggestions.append("Use more formal greeting for first contact")
                
        return {"issues": issues, "suggestions": suggestions}
        
    def _generate_cultural_improvements(self, message: str, language: str, issues: List[str]) -> List[str]:
        """Generate suggestions for cultural improvements"""
        suggestions = []
        
        for issue in issues:
            if "taboo" in issue.lower():
                suggestions.append("Remove or rephrase sensitive content")
            elif "honorific" in issue.lower():
                suggestions.append(f"Add appropriate honorific from: {self.cultural_rules[language]['honorifics']}")
            elif "prayer" in issue.lower():
                suggestions.append("Reschedule message to avoid prayer times")
                
        return suggestions
        
    def _select_appropriate_greeting(self, language: str, context: Dict[str, Any]) -> str:
        """Select culturally appropriate greeting"""
        current_time = context.get("current_time", datetime.now())
        formality = context.get("formality", "formal")
        is_special_occasion = context.get("special_occasion")
        
        if language == "ar":
            rules = self.cultural_rules["arabic"]["greetings"]
            
            # Check for special occasions
            if is_special_occasion:
                occasion_greetings = self.cultural_rules["arabic"]["religious_phrases"]["occasions"]
                if is_special_occasion in occasion_greetings:
                    return occasion_greetings[is_special_occasion][0]
                    
            # Time-based greeting
            hour = current_time.hour
            if 5 <= hour < 12:
                return rules["time_based"]["morning"]
            elif 12 <= hour < 18:
                return rules[formality][0]
            else:
                return rules["time_based"]["evening"]
        else:
            rules = self.cultural_rules["english"]["greetings"]
            hour = current_time.hour
            
            if 5 <= hour < 12:
                return rules["time_based"]["morning"]
            elif 12 <= hour < 17:
                return rules["time_based"]["afternoon"]
            else:
                return rules["time_based"]["evening"]
                
    def _select_appropriate_closing(self, language: str, context: Dict[str, Any]) -> str:
        """Select culturally appropriate closing"""
        formality = context.get("formality", "formal")
        sentiment = context.get("sentiment", "neutral")
        
        if language == "ar":
            closings = self.cultural_rules["arabic"]["closings"][formality]
            
            # Add religious closing for positive interactions
            if sentiment == "positive":
                return "بارك الله فيكم"
            else:
                return closings[0]
        else:
            closings = self.cultural_rules["english"]["closings"][formality]
            return closings[0]
            
    def _translate_with_cultural_context(self, text: str, source: str, target: str) -> str:
        """Translate with cultural context preservation"""
        # This would integrate with actual translation API
        # For now, return placeholder
        return f"[Translated from {source} to {target}]: {text}"
        
    def _add_cultural_elements(self, message: str, language: str, context: Dict[str, Any]) -> str:
        """Add appropriate cultural elements to message"""
        enhanced_message = message
        
        if language == "ar":
            # Add religious phrases if appropriate
            if context.get("sentiment") == "positive":
                if "شكر" in message and "الله" not in message:
                    enhanced_message = enhanced_message.replace("شكراً", "شكراً، بارك الله فيكم")
                    
            # Add Inshallah for future references
            future_indicators = ["سوف", "سنقوم", "القادم", "المقبل"]
            if any(indicator in message for indicator in future_indicators):
                if "إن شاء الله" not in message:
                    enhanced_message += " إن شاء الله"
                    
        return enhanced_message
        
    def _compose_final_message(self, greeting: str, body: str, closing: str, language: str) -> str:
        """Compose final message with all parts"""
        if language == "ar":
            return f"{greeting}\n\n{body}\n\n{closing}"
        else:
            return f"{greeting},\n\n{body}\n\n{closing}"
            
    def _identify_cultural_elements(self, message: str, language: str) -> List[str]:
        """Identify cultural elements in a message"""
        elements = []
        
        if language == "ar":
            religious_phrases = ["إن شاء الله", "ما شاء الله", "بارك الله", "الحمد لله"]
            for phrase in religious_phrases:
                if phrase in message:
                    elements.append(f"Religious phrase: {phrase}")
                    
            honorifics = self.cultural_rules["arabic"]["honorifics"]["respectful"]
            for honorific in honorifics:
                if honorific in message:
                    elements.append(f"Respectful honorific: {honorific}")
                    
        return elements
        
    def _detect_language(self, text: str) -> str:
        """Detect language of text"""
        arabic_chars = set("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
        arabic_count = sum(1 for char in text if char in arabic_chars)
        
        if arabic_count > len(text) * 0.3:
            return "ar"
        else:
            return "en"
            
    def _generate_language_transition(self, from_lang: str, to_lang: str) -> str:
        """Generate smooth language transition phrase"""
        transitions = {
            ("en", "ar"): "نكمل بالعربي...",
            ("ar", "en"): "Let me continue in English...",
        }
        return transitions.get((from_lang, to_lang), "")
        
    def _get_communication_style(self, language: str) -> str:
        """Get communication style for language"""
        if language == "ar":
            return self.cultural_rules["arabic"]["communication_style"]
        else:
            return self.cultural_rules["english"]["communication_style"]
            
    def _get_current_prayer_time(self, current_time: datetime) -> Optional[str]:
        """Check if current time is during prayer"""
        hour = current_time.hour
        minute = current_time.minute
        current_minutes = hour * 60 + minute
        
        for prayer_name, (start_hour, start_min, end_hour, end_min) in self.prayer_times.items():
            start_minutes = start_hour * 60 + start_min
            end_minutes = end_hour * 60 + end_min
            
            if start_minutes <= current_minutes <= end_minutes:
                return prayer_name
                
        return None
        
    def _is_during_iftar_time(self, current_time: datetime) -> bool:
        """Check if during Iftar time (sunset during Ramadan)"""
        # Simplified - would use actual sunset calculation
        return 18 <= current_time.hour <= 19
        
    def _apply_religious_adjustments(self, message: str, adjustments: List[Dict[str, Any]]) -> str:
        """Apply religious adjustments to message"""
        adjusted_message = message
        
        for adjustment in adjustments:
            if adjustment["action"] == "add_greeting":
                greeting = adjustment.get("greeting", "")
                if greeting and greeting not in adjusted_message:
                    adjusted_message = f"{greeting}\n{adjusted_message}"
                    
        return adjusted_message
        
    def _generate_base_response(self, customer_message: str, sentiment: str, language: str) -> str:
        """Generate base response before cultural adaptation"""
        # This would use AI to generate appropriate response
        # Placeholder for now
        if sentiment == "positive":
            if language == "ar":
                return "نشكركم على كلماتكم الطيبة"
            else:
                return "Thank you for your kind words"
        elif sentiment == "negative":
            if language == "ar":
                return "نعتذر عن أي إزعاج وسنعمل على تحسين خدماتنا"
            else:
                return "We apologize for any inconvenience and will work to improve"
        else:
            if language == "ar":
                return "شكراً لتواصلكم معنا"
            else:
                return "Thank you for contacting us"
                
    def _add_arabic_cultural_elements(self, response: str, sentiment: str, profile: Dict[str, Any]) -> str:
        """Add Arabic cultural elements to response"""
        enhanced = response
        
        # Add appropriate religious phrases
        if sentiment == "positive":
            enhanced += "، والحمد لله على رضاكم"
        elif sentiment == "negative":
            enhanced += "، ونسأل الله أن يوفقنا لخدمتكم بشكل أفضل"
            
        return enhanced
        
    def _add_english_cultural_elements(self, response: str, sentiment: str, profile: Dict[str, Any]) -> str:
        """Add English cultural elements to response"""
        enhanced = response
        
        # Add personal touch
        if profile.get("name"):
            enhanced = enhanced.replace("you", f"you, {profile['name']}")
            
        return enhanced
        
    def _add_honorifics(self, response: str, profile: Dict[str, Any], language: str) -> str:
        """Add appropriate honorifics to response"""
        name = profile.get("name", "")
        gender = profile.get("gender")
        age = profile.get("age")
        
        if not name:
            return response
            
        if language == "ar":
            if age and age > 50:
                honorific = "حضرة السيد" if gender == "male" else "حضرة السيدة"
            else:
                honorific = "أستاذ" if gender == "male" else "أستاذة"
                
            return response.replace(name, f"{honorific} {name}")
        else:
            honorific = "Mr." if gender == "male" else "Ms."
            return response.replace(name, f"{honorific} {name}")
            
    def _apply_dialect(self, content: str, dialect: str) -> str:
        """Apply regional dialect to content"""
        # Simplified dialect conversion
        dialect_conversions = {
            "gulf": {
                "كيف": "جيف",
                "أيش": "شنو",
                "إزاي": "شلون"
            },
            "egyptian": {
                "كيف": "إزاي",
                "شنو": "إيه",
                "شلون": "إزاي"
            },
            "levantine": {
                "شنو": "شو",
                "شلون": "كيف"
            }
        }
        
        if dialect in dialect_conversions:
            for standard, dialectal in dialect_conversions[dialect].items():
                content = content.replace(standard, dialectal)
                
        return content
        
    def _localize_currency(self, content: str, currency: str) -> str:
        """Localize currency in content"""
        currency_symbols = {
            "SAR": "ر.س",
            "AED": "د.إ",
            "EGP": "ج.م",
            "USD": "$"
        }
        
        # Replace generic currency references
        if currency in currency_symbols:
            content = re.sub(r'\$|USD', currency_symbols[currency], content)
            
        return content
        
    def _track_modifications(self, original: str, modified: str) -> List[str]:
        """Track what modifications were made"""
        modifications = []
        
        if len(modified) != len(original):
            modifications.append("Length changed")
            
        # Check for specific changes
        if original != modified:
            modifications.append("Content modified")
            
        return modifications