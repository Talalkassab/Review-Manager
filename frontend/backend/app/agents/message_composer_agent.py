"""
Message Composer Agent - Creates personalized, culturally appropriate messages
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import random
from .base_agent import BaseRestaurantAgent
from .tools import OpenRouterTool, TemplateEngine, PersonalizationTool


class MessageComposerAgent(BaseRestaurantAgent):
    """
    Specialized agent for composing personalized, culturally appropriate messages.
    Creates contextual responses based on customer profile, sentiment, and cultural background.
    """
    
    def __init__(self):
        super().__init__(
            role="Message Personalization Specialist",
            goal="Create highly personalized, culturally sensitive, and emotionally appropriate messages that resonate with individual customers and strengthen relationships",
            backstory="""You are a master communicator with expertise in crafting personalized messages that connect with customers on an emotional level. 
            Your deep understanding of Arabic and English cultures, combined with advanced personalization techniques, allows you to create 
            messages that feel genuinely human and caring. You excel at adapting tone, style, and content to match customer preferences, 
            cultural background, and emotional state. Every message you create strengthens the customer-restaurant relationship.""",
            tools=[
                OpenRouterTool(),
                TemplateEngine(),
                PersonalizationTool()
            ],
            verbose=True,
            allow_delegation=False,
            max_iter=4
        )
        
        # Message templates by category and language
        self.message_templates = {
            "arabic": {
                "welcome_new": [
                    "أهلاً وسهلاً {name}! نسعد بزيارتكم الأولى لمطعمنا. كيف كانت تجربتكم معنا؟",
                    "مرحباً {name}، نتشرف بوجودكم في مطعمنا. نتطلع لسماع انطباعكم عن الزيارة",
                    "حياكم الله {name}! كيف وجدتم الطعام والخدمة في زيارتكم الأولى؟"
                ],
                "follow_up_positive": [
                    "نشكركم {name} على كلماتكم الطيبة! سعادتكم هي هدفنا الأول",
                    "يسعدنا أن التجربة نالت إعجابكم {name}. في انتظار زيارتكم القادمة",
                    "بارك الله فيكم {name} على تشجيعكم. نتطلع لاستقبالكم مرة أخرى"
                ],
                "follow_up_negative": [
                    "نعتذر بصدق {name} عن التجربة التي لم ترق لتوقعاتكم. كيف يمكننا تحسين خدماتنا؟",
                    "أسف جداً {name} لعدم رضاكم التام. نود إصلاح الأمر ومنحكم تجربة أفضل",
                    "نتفهم استياءكم {name} ونأخذ ملاحظاتكم بجدية. متى يمكنكم زيارتنا مرة أخرى لنظهر لكم التحسن؟"
                ],
                "birthday_greeting": [
                    "كل عام وأنتم بخير {name}! يسعدنا الاحتفال معكم بعيد ميلادكم",
                    "عيد ميلاد سعيد {name}! لدينا مفاجأة خاصة لكم",
                    "نبارك لكم {name} عيد ميلادكم ونتمنى لكم عاماً مليئاً بالسعادة"
                ],
                "ramadan_greeting": [
                    "رمضان مبارك {name}! نقدم قوائم خاصة لشهر الخير",
                    "رمضان كريم {name}، لدينا عروض مميزة لوجبات الإفطار والسحور",
                    "بارك الله لكم في شهر رمضان {name}. تفضلوا لتجربة أطباقنا الرمضانية"
                ],
                "eid_greeting": [
                    "عيد مبارك {name}! كل عام وأنتم بخير",
                    "تقبل الله صيامكم {name} وعيد سعيد عليكم وعلى أهلكم",
                    "عيد فطر مبارك {name}! نسعد باستقبالكم للاحتفال معاً"
                ],
                "re_engagement": [
                    "اشتقنا لكم {name}! كيف حالكم؟ متى نراكم مرة أخرى؟",
                    "لم نركم منذ فترة {name}، نتطلع لزيارتكم القادمة",
                    "نود رؤيتكم مرة أخرى {name}. لدينا أطباق جديدة نثق أنها ستعجبكم"
                ]
            },
            "english": {
                "welcome_new": [
                    "Welcome {name}! We're delighted you chose us for your first visit. How was your experience?",
                    "Hello {name}, thank you for dining with us today. We'd love to hear your thoughts!",
                    "Hi {name}! We hope you enjoyed your first meal with us. Any feedback would be appreciated!"
                ],
                "follow_up_positive": [
                    "Thank you {name} for your wonderful feedback! We're thrilled you enjoyed your visit",
                    "We're so glad you had a great experience {name}! Looking forward to serving you again",
                    "Your kind words mean the world to us {name}. Can't wait to welcome you back!"
                ],
                "follow_up_negative": [
                    "We sincerely apologize {name} for not meeting your expectations. How can we make this right?",
                    "Thank you for your feedback {name}. We take all concerns seriously and want to improve",
                    "We're sorry your experience wasn't perfect {name}. May we invite you back to show you our improvements?"
                ],
                "birthday_greeting": [
                    "Happy Birthday {name}! We'd love to help you celebrate your special day",
                    "Wishing you a wonderful birthday {name}! We have something special planned for you",
                    "Many happy returns {name}! Come celebrate with us - it's our treat!"
                ],
                "re_engagement": [
                    "We miss you {name}! It's been a while since your last visit. How have you been?",
                    "Hi {name}, we'd love to see you again soon. We have some exciting new dishes!",
                    "Thinking of you {name}! When can we welcome you back for another great meal?"
                ]
            }
        }
        
        # Personalization variables
        self.personalization_variables = [
            "name", "favorite_dish", "last_visit_date", "visit_count", 
            "dietary_preferences", "special_occasions", "preferred_time",
            "party_size", "preferred_table", "previous_orders"
        ]
        
        # Emotional tone mappings
        self.tone_mappings = {
            "apologetic_understanding": {
                "arabic": ["نتفهم", "نعتذر بصدق", "نأخذ الأمر بجدية", "سنعمل على التحسين"],
                "english": ["we understand", "sincerely apologize", "take this seriously", "will work to improve"]
            },
            "enthusiastic_grateful": {
                "arabic": ["نسعد", "يسرنا", "بارك الله فيكم", "كلماتكم تسعدنا"],
                "english": ["delighted", "thrilled", "grateful", "wonderful to hear"]
            },
            "warm_appreciative": {
                "arabic": ["نشكركم", "نقدر", "كلماتكم الطيبة", "نسعد برضاكم"],
                "english": ["appreciate", "thankful", "kind words", "pleased"]
            },
            "friendly_professional": {
                "arabic": ["نتطلع", "يسعدنا", "نأمل", "في انتظاركم"],
                "english": ["looking forward", "happy to", "hope to", "welcome"]
            },
            "empathetic_supportive": {
                "arabic": ["نتفهم شعوركم", "نهتم براحتكم", "سنبذل قصارى جهدنا"],
                "english": ["understand how you feel", "care about your comfort", "will do our best"]
            }
        }
        
    def compose_personalized_message(self, 
                                   message_type: str,
                                   customer_profile: Dict[str, Any],
                                   context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compose a personalized message based on type and customer profile
        """
        self.log_task_start("compose_personalized_message", {
            "message_type": message_type,
            "customer_language": customer_profile.get("preferred_language")
        })
        
        try:
            # Determine language preference
            language = customer_profile.get("preferred_language", "arabic")
            
            # Select base template
            base_template = self._select_base_template(message_type, language)
            
            # Apply personalization
            personalized_message = self._apply_personalization(
                base_template, customer_profile, context
            )
            
            # Apply emotional tone
            tone = context.get("recommended_tone", "friendly_professional")
            emotionally_tuned = self._apply_emotional_tone(
                personalized_message, tone, language
            )
            
            # Add cultural elements
            culturally_enhanced = self._add_cultural_elements(
                emotionally_tuned, customer_profile, context, language
            )
            
            # Add call to action if appropriate
            with_cta = self._add_call_to_action(
                culturally_enhanced, message_type, customer_profile, language
            )
            
            # Validate message appropriateness
            validation = self._validate_message_appropriateness(
                with_cta, customer_profile, context
            )
            
            result = {
                "message_type": message_type,
                "language": language,
                "original_template": base_template,
                "personalized_message": with_cta,
                "personalization_applied": self._get_applied_personalizations(
                    base_template, with_cta, customer_profile
                ),
                "emotional_tone": tone,
                "cultural_elements": self._identify_cultural_elements(with_cta, language),
                "validation": validation,
                "is_ready_to_send": validation["is_appropriate"],
                "character_count": len(with_cta),
                "estimated_engagement_score": self._estimate_engagement_score(
                    with_cta, customer_profile, context
                )
            }
            
            self.log_task_complete("compose_personalized_message", result)
            return result
            
        except Exception as e:
            self.log_task_error("compose_personalized_message", e)
            raise
            
    def create_campaign_message(self,
                               campaign_config: Dict[str, Any],
                               target_customers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create message variants for campaign targeting
        """
        self.log_task_start("create_campaign_message", {
            "campaign_type": campaign_config.get("campaign_type"),
            "target_count": len(target_customers)
        })
        
        try:
            message_variants = {}
            
            # Create variants for different customer segments
            for customer in target_customers:
                customer_id = customer["id"]
                
                # Determine personalization level
                personalization_level = self._determine_personalization_level(
                    customer, campaign_config
                )
                
                # Create personalized variant
                variant = self.compose_personalized_message(
                    message_type=campaign_config["campaign_type"],
                    customer_profile=customer,
                    context={
                        "is_campaign": True,
                        "campaign_goal": campaign_config.get("goal"),
                        "personalization_level": personalization_level,
                        **campaign_config.get("context", {})
                    }
                )
                
                message_variants[customer_id] = variant
                
            # Generate A/B test variants if requested
            ab_variants = {}
            if campaign_config.get("enable_ab_testing"):
                ab_variants = self._create_ab_test_variants(
                    campaign_config, target_customers[:10]  # Sample for testing
                )
                
            # Calculate campaign metrics
            campaign_metrics = self._calculate_campaign_metrics(
                message_variants, campaign_config
            )
            
            result = {
                "campaign_id": campaign_config.get("campaign_id"),
                "campaign_type": campaign_config.get("campaign_type"),
                "message_variants": message_variants,
                "ab_test_variants": ab_variants,
                "total_messages": len(message_variants),
                "language_distribution": self._calculate_language_distribution(message_variants),
                "campaign_metrics": campaign_metrics,
                "estimated_cost": self._estimate_campaign_cost(message_variants),
                "ready_to_deploy": all(v["is_ready_to_send"] for v in message_variants.values())
            }
            
            self.log_task_complete("create_campaign_message", result)
            return result
            
        except Exception as e:
            self.log_task_error("create_campaign_message", e)
            raise
            
    def adapt_message_for_response(self,
                                  customer_message: str,
                                  sentiment_analysis: Dict[str, Any],
                                  customer_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create adaptive response based on customer message and sentiment
        """
        self.log_task_start("adapt_message_for_response")
        
        try:
            # Determine response strategy
            response_strategy = self._determine_response_strategy(
                sentiment_analysis, customer_profile
            )
            
            # Select appropriate message type
            message_type = self._map_sentiment_to_message_type(
                sentiment_analysis["sentiment"]
            )
            
            # Create context for response
            response_context = {
                "customer_message": customer_message,
                "sentiment": sentiment_analysis["sentiment"],
                "emotions": sentiment_analysis.get("emotions", []),
                "urgency": sentiment_analysis.get("urgency", "low"),
                "recommended_tone": sentiment_analysis.get("recommended_response_tone"),
                "requires_escalation": sentiment_analysis.get("requires_immediate_attention", False)
            }
            
            # Compose response
            response = self.compose_personalized_message(
                message_type=message_type,
                customer_profile=customer_profile,
                context=response_context
            )
            
            # Add specific acknowledgments
            with_acknowledgment = self._add_specific_acknowledgment(
                response["personalized_message"], customer_message, sentiment_analysis
            )
            
            # Apply conversation continuity
            final_response = self._ensure_conversation_continuity(
                with_acknowledgment, customer_profile.get("conversation_history", [])
            )
            
            result = {
                "customer_message": customer_message,
                "response_strategy": response_strategy,
                "adapted_response": final_response,
                "response_reasoning": self._explain_response_reasoning(
                    response_strategy, sentiment_analysis
                ),
                "escalation_required": response_context["requires_escalation"],
                "follow_up_recommended": self._should_schedule_follow_up(sentiment_analysis),
                **response
            }
            
            self.log_task_complete("adapt_message_for_response", result)
            return result
            
        except Exception as e:
            self.log_task_error("adapt_message_for_response", e)
            raise
            
    def generate_template_variations(self,
                                   base_template: str,
                                   variation_count: int = 3) -> List[Dict[str, Any]]:
        """
        Generate variations of a message template for A/B testing
        """
        self.log_task_start("generate_template_variations", {
            "variation_count": variation_count
        })
        
        try:
            variations = []
            
            # Detect language of base template
            language = self._detect_template_language(base_template)
            
            for i in range(variation_count):
                # Apply different variation strategies
                variation_strategy = self._select_variation_strategy(i)
                
                varied_template = self._apply_variation_strategy(
                    base_template, variation_strategy, language
                )
                
                # Analyze variation characteristics
                characteristics = self._analyze_variation_characteristics(
                    varied_template, base_template, language
                )
                
                variations.append({
                    "variation_id": f"var_{i+1}",
                    "variation_strategy": variation_strategy,
                    "template": varied_template,
                    "characteristics": characteristics,
                    "estimated_appeal": characteristics.get("appeal_score", 0.5)
                })
                
            # Sort by estimated appeal
            variations.sort(key=lambda x: x["estimated_appeal"], reverse=True)
            
            result = {
                "base_template": base_template,
                "language": language,
                "variations": variations,
                "recommended_variation": variations[0] if variations else None
            }
            
            self.log_task_complete("generate_template_variations", result)
            return result
            
        except Exception as e:
            self.log_task_error("generate_template_variations", e)
            raise
            
    def optimize_message_timing(self,
                               message: str,
                               customer_profile: Dict[str, Any],
                               current_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize message content based on optimal send timing
        """
        self.log_task_start("optimize_message_timing")
        
        try:
            # Get optimal send time
            optimal_time = current_context.get("optimal_send_time", datetime.now())
            
            # Adjust greeting based on time
            time_appropriate_greeting = self._get_time_appropriate_greeting(
                optimal_time, customer_profile.get("preferred_language", "arabic")
            )
            
            # Add time-specific elements
            time_enhanced_message = self._add_time_specific_elements(
                message, optimal_time, customer_profile
            )
            
            # Check for cultural time considerations
            cultural_time_check = self._check_cultural_time_appropriateness(
                optimal_time, customer_profile
            )
            
            # Apply urgency adjustments if needed
            urgency_adjusted = self._apply_urgency_adjustments(
                time_enhanced_message, current_context.get("urgency", "low")
            )
            
            result = {
                "original_message": message,
                "optimized_message": urgency_adjusted,
                "optimal_send_time": optimal_time.isoformat(),
                "time_appropriate_greeting": time_appropriate_greeting,
                "cultural_time_check": cultural_time_check,
                "timing_adjustments_made": self._get_timing_adjustments(
                    message, urgency_adjusted
                ),
                "is_time_appropriate": cultural_time_check.get("appropriate", True)
            }
            
            self.log_task_complete("optimize_message_timing", result)
            return result
            
        except Exception as e:
            self.log_task_error("optimize_message_timing", e)
            raise
            
    # Private helper methods
    def _select_base_template(self, message_type: str, language: str) -> str:
        """Select appropriate base template"""
        lang_key = "arabic" if language in ["ar", "arabic"] else "english"
        
        templates = self.message_templates[lang_key].get(message_type, [])
        if not templates:
            # Fallback to welcome template
            templates = self.message_templates[lang_key].get("welcome_new", [])
            
        return random.choice(templates) if templates else ""
        
    def _apply_personalization(self, 
                              template: str,
                              customer_profile: Dict[str, Any],
                              context: Dict[str, Any]) -> str:
        """Apply personalization variables to template"""
        personalized = template
        
        # Replace standard variables
        for var in self.personalization_variables:
            placeholder = "{" + var + "}"
            if placeholder in personalized:
                value = customer_profile.get(var, "")
                
                # Special handling for specific variables
                if var == "name":
                    value = value or "عزيزنا العميل" if "arabic" in template else "valued customer"
                elif var == "visit_count":
                    value = self._format_visit_count(value, customer_profile.get("preferred_language"))
                elif var == "last_visit_date":
                    value = self._format_visit_date(value, customer_profile.get("preferred_language"))
                    
                personalized = personalized.replace(placeholder, str(value))
                
        return personalized
        
    def _apply_emotional_tone(self, message: str, tone: str, language: str) -> str:
        """Apply emotional tone to message"""
        lang_key = "arabic" if language in ["ar", "arabic"] else "english"
        tone_words = self.tone_mappings.get(tone, {}).get(lang_key, [])
        
        if tone_words:
            # Add appropriate tone word/phrase
            selected_tone = random.choice(tone_words)
            
            if lang_key == "arabic":
                # Add at appropriate position in Arabic
                message = message + f" {selected_tone}"
            else:
                # Add at beginning or end in English
                message = f"We're {selected_tone} {message.lower()}"
                
        return message
        
    def _add_cultural_elements(self,
                              message: str,
                              customer_profile: Dict[str, Any],
                              context: Dict[str, Any],
                              language: str) -> str:
        """Add culturally appropriate elements"""
        enhanced = message
        
        if language in ["ar", "arabic"]:
            # Add Islamic phrases if appropriate
            current_time = context.get("send_time", datetime.now())
            
            # Check for special occasions
            if context.get("is_ramadan"):
                if "رمضان" not in enhanced:
                    enhanced = "رمضان مبارك! " + enhanced
                    
            elif context.get("is_eid"):
                if "عيد" not in enhanced:
                    enhanced = "عيد مبارك! " + enhanced
                    
            # Add appropriate religious phrase
            if "شكر" in enhanced and "الله" not in enhanced:
                enhanced = enhanced.replace("شكراً", "شكراً، بارك الله فيكم")
                
        # Add personal touches based on customer history
        if customer_profile.get("favorite_dish"):
            dish = customer_profile["favorite_dish"]
            if language in ["ar", "arabic"]:
                enhanced += f". نتذكر حبكم لطبق {dish}"
            else:
                enhanced += f". We remember how much you enjoyed our {dish}"
                
        return enhanced
        
    def _add_call_to_action(self,
                           message: str,
                           message_type: str,
                           customer_profile: Dict[str, Any],
                           language: str) -> str:
        """Add appropriate call to action"""
        cta_templates = {
            "arabic": {
                "feedback_request": "نرجو مشاركة رأيكم معنا",
                "visit_invitation": "نتطلع لزيارتكم القادمة",
                "review_request": "نود إن أعجبتكم تجربتكم أن تشاركوا رأيكم على Google",
                "birthday_offer": "تفضلوا لاستلام هديتكم"
            },
            "english": {
                "feedback_request": "We'd love to hear your thoughts",
                "visit_invitation": "We look forward to your next visit",
                "review_request": "If you enjoyed your experience, please consider leaving us a review",
                "birthday_offer": "Come in to claim your birthday surprise"
            }
        }
        
        lang_key = "arabic" if language in ["ar", "arabic"] else "english"
        
        # Select CTA based on message type
        cta = ""
        if "welcome" in message_type or "follow_up" in message_type:
            cta = cta_templates[lang_key]["feedback_request"]
        elif "birthday" in message_type:
            cta = cta_templates[lang_key]["birthday_offer"]
        elif "re_engagement" in message_type:
            cta = cta_templates[lang_key]["visit_invitation"]
            
        if cta:
            separator = ". " if lang_key == "english" else "، "
            return message + separator + cta
            
        return message
        
    def _validate_message_appropriateness(self,
                                         message: str,
                                         customer_profile: Dict[str, Any],
                                         context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate message appropriateness"""
        issues = []
        suggestions = []
        
        # Check length
        if len(message) > 300:
            issues.append("Message too long for WhatsApp")
            suggestions.append("Consider shortening the message")
            
        # Check for personalization
        if "{" in message and "}" in message:
            issues.append("Unpersonalized variables remain")
            suggestions.append("Complete personalization replacement")
            
        # Check cultural appropriateness
        language = customer_profile.get("preferred_language", "ar")
        if language in ["ar", "arabic"]:
            # Check for appropriate formality
            age = customer_profile.get("age", 30)
            if age > 50 and "حضرتك" not in message:
                suggestions.append("Consider adding respectful honorific for elderly customer")
                
        return {
            "is_appropriate": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
            "cultural_score": 1.0 - (len(issues) * 0.2)
        }
        
    def _get_applied_personalizations(self,
                                     base_template: str,
                                     final_message: str,
                                     customer_profile: Dict[str, Any]) -> List[str]:
        """Identify what personalizations were applied"""
        personalizations = []
        
        for var in self.personalization_variables:
            placeholder = "{" + var + "}"
            if placeholder in base_template and placeholder not in final_message:
                value = customer_profile.get(var)
                if value:
                    personalizations.append(f"{var}: {value}")
                    
        return personalizations
        
    def _identify_cultural_elements(self, message: str, language: str) -> List[str]:
        """Identify cultural elements in message"""
        elements = []
        
        if language in ["ar", "arabic"]:
            # Islamic phrases
            islamic_phrases = ["بارك الله", "إن شاء الله", "ما شاء الله", "الحمد لله"]
            for phrase in islamic_phrases:
                if phrase in message:
                    elements.append(f"Islamic phrase: {phrase}")
                    
            # Respectful terms
            respectful_terms = ["حضرتك", "سعادتك", "أستاذ", "أستاذة"]
            for term in respectful_terms:
                if term in message:
                    elements.append(f"Respectful term: {term}")
                    
        return elements
        
    def _estimate_engagement_score(self,
                                  message: str,
                                  customer_profile: Dict[str, Any],
                                  context: Dict[str, Any]) -> float:
        """Estimate engagement score for message"""
        score = 0.5  # Base score
        
        # Personalization bonus
        name = customer_profile.get("name", "")
        if name and name in message:
            score += 0.2
            
        # Emotional tone bonus
        tone = context.get("recommended_tone", "")
        if tone in ["enthusiastic_grateful", "warm_appreciative"]:
            score += 0.1
            
        # Cultural appropriateness bonus
        language = customer_profile.get("preferred_language", "ar")
        if language in ["ar", "arabic"] and any(phrase in message for phrase in ["بارك الله", "إن شاء الله"]):
            score += 0.1
            
        # Call to action bonus
        cta_indicators = ["نرجو", "نود", "تفضلوا", "please", "would love", "looking forward"]
        if any(indicator in message.lower() for indicator in cta_indicators):
            score += 0.1
            
        return min(score, 1.0)
        
    def _determine_personalization_level(self,
                                        customer: Dict[str, Any],
                                        campaign_config: Dict[str, Any]) -> str:
        """Determine appropriate personalization level"""
        visit_count = customer.get("visit_count", 0)
        data_completeness = len([v for v in customer.values() if v]) / len(customer)
        
        if visit_count >= 5 and data_completeness > 0.7:
            return "high"
        elif visit_count >= 2 and data_completeness > 0.5:
            return "medium"
        else:
            return "basic"
            
    def _create_ab_test_variants(self,
                                campaign_config: Dict[str, Any],
                                sample_customers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create A/B test variants"""
        variants = {}
        
        # Create 2-3 different approaches
        approaches = ["formal", "casual", "emotional"]
        
        for i, approach in enumerate(approaches):
            variant_id = f"variant_{chr(65 + i)}"  # A, B, C
            
            # Modify campaign config for this approach
            variant_config = campaign_config.copy()
            variant_config["tone_approach"] = approach
            
            # Create sample messages
            variant_messages = {}
            for customer in sample_customers[:3]:  # Sample size
                message = self.compose_personalized_message(
                    message_type=campaign_config["campaign_type"],
                    customer_profile=customer,
                    context={
                        "tone_approach": approach,
                        **campaign_config.get("context", {})
                    }
                )
                variant_messages[customer["id"]] = message
                
            variants[variant_id] = {
                "approach": approach,
                "sample_messages": variant_messages,
                "expected_engagement": self._estimate_variant_engagement(approach)
            }
            
        return variants
        
    def _calculate_campaign_metrics(self,
                                   message_variants: Dict[str, Any],
                                   campaign_config: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate campaign metrics"""
        total_messages = len(message_variants)
        
        # Language distribution
        arabic_count = sum(1 for msg in message_variants.values() 
                          if msg.get("language") in ["ar", "arabic"])
        
        # Average engagement score
        avg_engagement = sum(msg.get("estimated_engagement_score", 0.5) 
                           for msg in message_variants.values()) / total_messages
        
        # Character length statistics
        lengths = [msg.get("character_count", 0) for msg in message_variants.values()]
        avg_length = sum(lengths) / len(lengths) if lengths else 0
        
        return {
            "total_messages": total_messages,
            "arabic_messages": arabic_count,
            "english_messages": total_messages - arabic_count,
            "average_engagement_score": round(avg_engagement, 2),
            "average_message_length": round(avg_length, 0),
            "estimated_delivery_time": self._estimate_delivery_time(total_messages)
        }
        
    def _calculate_language_distribution(self, message_variants: Dict[str, Any]) -> Dict[str, int]:
        """Calculate language distribution in campaign"""
        distribution = {"arabic": 0, "english": 0}
        
        for message_data in message_variants.values():
            lang = message_data.get("language", "arabic")
            if lang in ["ar", "arabic"]:
                distribution["arabic"] += 1
            else:
                distribution["english"] += 1
                
        return distribution
        
    def _estimate_campaign_cost(self, message_variants: Dict[str, Any]) -> Dict[str, float]:
        """Estimate campaign cost"""
        # Simplified cost calculation
        whatsapp_cost_per_message = 0.05  # USD
        total_messages = len(message_variants)
        
        return {
            "whatsapp_delivery_cost": total_messages * whatsapp_cost_per_message,
            "ai_processing_cost": total_messages * 0.01,
            "total_estimated_cost": total_messages * (whatsapp_cost_per_message + 0.01)
        }
        
    def _determine_response_strategy(self,
                                   sentiment_analysis: Dict[str, Any],
                                   customer_profile: Dict[str, Any]) -> str:
        """Determine response strategy based on sentiment"""
        sentiment = sentiment_analysis["sentiment"]
        urgency = sentiment_analysis.get("urgency", "low")
        customer_tier = customer_profile.get("tier", "standard")
        
        if sentiment == "negative":
            if urgency == "high" or customer_tier == "vip":
                return "immediate_recovery"
            else:
                return "empathetic_resolution"
        elif sentiment == "positive":
            return "appreciation_reinforcement"
        else:
            return "gentle_engagement"
            
    def _map_sentiment_to_message_type(self, sentiment: str) -> str:
        """Map sentiment to appropriate message type"""
        mapping = {
            "positive": "follow_up_positive",
            "negative": "follow_up_negative",
            "neutral": "follow_up_general"
        }
        return mapping.get(sentiment, "follow_up_general")
        
    def _add_specific_acknowledgment(self,
                                   response: str,
                                   customer_message: str,
                                   sentiment_analysis: Dict[str, Any]) -> str:
        """Add specific acknowledgment of customer's message"""
        # Extract key points from customer message
        key_phrases = sentiment_analysis.get("key_phrases", [])
        
        if key_phrases:
            # Select most relevant phrase
            relevant_phrase = key_phrases[0][:50]  # Limit length
            
            # Add acknowledgment
            if sentiment_analysis["language"] == "arabic":
                acknowledgment = f"نتفهم اهتمامكم بـ {relevant_phrase}"
            else:
                acknowledgment = f"We understand your concern about {relevant_phrase}"
                
            return acknowledgment + ". " + response
            
        return response
        
    def _ensure_conversation_continuity(self,
                                       response: str,
                                       conversation_history: List[Dict[str, Any]]) -> str:
        """Ensure conversation continuity"""
        if not conversation_history:
            return response
            
        # Check if this is a follow-up to previous conversation
        last_message = conversation_history[-1]
        if last_message.get("requires_follow_up"):
            # Add continuity reference
            if "arabic" in response:
                continuity = "كما وعدناكم، "
            else:
                continuity = "As promised, "
            response = continuity + response.lower()
            
        return response
        
    def _explain_response_reasoning(self,
                                   strategy: str,
                                   sentiment_analysis: Dict[str, Any]) -> str:
        """Explain reasoning behind response strategy"""
        sentiment = sentiment_analysis["sentiment"]
        urgency = sentiment_analysis.get("urgency", "low")
        
        reasoning = f"Strategy '{strategy}' selected because: "
        reasoning += f"sentiment is {sentiment}, urgency is {urgency}"
        
        if sentiment_analysis.get("requires_immediate_attention"):
            reasoning += ", immediate attention required"
            
        return reasoning
        
    def _should_schedule_follow_up(self, sentiment_analysis: Dict[str, Any]) -> bool:
        """Determine if follow-up should be scheduled"""
        return (
            sentiment_analysis["sentiment"] == "negative" or
            sentiment_analysis.get("urgency") == "high" or
            "complaint" in sentiment_analysis.get("key_phrases", [])
        )
        
    def _detect_template_language(self, template: str) -> str:
        """Detect language of template"""
        arabic_chars = set("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
        arabic_count = sum(1 for char in template if char in arabic_chars)
        
        return "arabic" if arabic_count > len(template) * 0.3 else "english"
        
    def _select_variation_strategy(self, index: int) -> str:
        """Select variation strategy based on index"""
        strategies = ["tone_variation", "structure_variation", "length_variation"]
        return strategies[index % len(strategies)]
        
    def _apply_variation_strategy(self,
                                 base_template: str,
                                 strategy: str,
                                 language: str) -> str:
        """Apply specific variation strategy to template"""
        if strategy == "tone_variation":
            # Change from formal to casual or vice versa
            if language == "arabic":
                if "حضرتك" in base_template:
                    return base_template.replace("حضرتك", "أنت")
                else:
                    return base_template.replace("أنت", "حضرتك")
            else:
                if "you" in base_template.lower():
                    return base_template.replace("you", "yourself")
                    
        elif strategy == "structure_variation":
            # Rearrange sentence structure
            sentences = base_template.split(".")
            if len(sentences) > 1:
                return ". ".join(reversed(sentences))
                
        elif strategy == "length_variation":
            # Add or remove descriptive words
            if language == "arabic":
                return base_template.replace("جيد", "ممتاز ورائع")
            else:
                return base_template.replace("good", "excellent and wonderful")
                
        return base_template
        
    def _analyze_variation_characteristics(self,
                                          variation: str,
                                          base: str,
                                          language: str) -> Dict[str, Any]:
        """Analyze characteristics of variation"""
        return {
            "length_change": len(variation) - len(base),
            "formality_level": self._assess_formality(variation, language),
            "emotional_intensity": self._assess_emotional_intensity(variation, language),
            "appeal_score": self._calculate_appeal_score(variation, language)
        }
        
    def _get_time_appropriate_greeting(self,
                                      send_time: datetime,
                                      language: str) -> str:
        """Get time-appropriate greeting"""
        hour = send_time.hour
        
        if language in ["ar", "arabic"]:
            if 5 <= hour < 12:
                return "صباح الخير"
            elif 12 <= hour < 17:
                return "مساء الخير"  # Afternoon
            else:
                return "مساء الخير"
        else:
            if 5 <= hour < 12:
                return "Good morning"
            elif 12 <= hour < 17:
                return "Good afternoon"
            else:
                return "Good evening"
                
    def _add_time_specific_elements(self,
                                   message: str,
                                   send_time: datetime,
                                   customer_profile: Dict[str, Any]) -> str:
        """Add time-specific elements to message"""
        hour = send_time.hour
        language = customer_profile.get("preferred_language", "ar")
        
        # Add time-specific context
        if language in ["ar", "arabic"]:
            if 11 <= hour <= 14:  # Lunch time
                message += ". نأمل أن نراكم لوجبة غداء لذيذة"
            elif 18 <= hour <= 22:  # Dinner time
                message += ". ندعوكم لتجربة قائمة العشاء المميزة"
        else:
            if 11 <= hour <= 14:
                message += ". Hope to see you for a delicious lunch"
            elif 18 <= hour <= 22:
                message += ". Join us for our special dinner menu"
                
        return message
        
    def _check_cultural_time_appropriateness(self,
                                           send_time: datetime,
                                           customer_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Check if send time is culturally appropriate"""
        appropriate = True
        reason = ""
        
        # Check prayer times (simplified)
        hour = send_time.hour
        if customer_profile.get("preferred_language") in ["ar", "arabic"]:
            prayer_hours = [5, 12, 15, 18, 19]  # Approximate prayer times
            if hour in prayer_hours:
                appropriate = False
                reason = "During prayer time"
                
        # Check for inappropriate hours
        if hour < 8 or hour > 22:
            appropriate = False
            reason = "Outside appropriate hours (8 AM - 10 PM)"
            
        return {
            "appropriate": appropriate,
            "reason": reason if not appropriate else "Time is appropriate"
        }
        
    def _apply_urgency_adjustments(self, message: str, urgency: str) -> str:
        """Apply urgency adjustments to message"""
        if urgency == "high":
            # Add urgency indicators
            if "arabic" in message:
                message = "عاجل: " + message
            else:
                message = "Urgent: " + message
        elif urgency == "medium":
            if "arabic" in message:
                message = message + " - نأمل ردكم السريع"
            else:
                message = message + " - Hope to hear back soon"
                
        return message
        
    def _get_timing_adjustments(self, original: str, final: str) -> List[str]:
        """Get list of timing adjustments made"""
        adjustments = []
        
        if len(final) != len(original):
            adjustments.append("Length modified")
            
        if "عاجل" in final or "Urgent" in final:
            adjustments.append("Urgency indicator added")
            
        if any(time_word in final for time_word in ["صباح", "مساء", "morning", "evening"]):
            adjustments.append("Time-specific greeting added")
            
        return adjustments
        
    # Additional helper methods
    def _format_visit_count(self, count: int, language: str) -> str:
        """Format visit count appropriately"""
        if not count:
            return ""
            
        if language in ["ar", "arabic"]:
            if count == 1:
                return "زيارتكم الأولى"
            elif count < 5:
                return f"زيارتكم الـ {count}"
            else:
                return f"زيارتكم رقم {count}"
        else:
            if count == 1:
                return "your first visit"
            else:
                return f"visit #{count}"
                
    def _format_visit_date(self, date: str, language: str) -> str:
        """Format visit date appropriately"""
        if not date:
            return ""
            
        try:
            visit_date = datetime.fromisoformat(date)
            days_ago = (datetime.now() - visit_date).days
            
            if language in ["ar", "arabic"]:
                if days_ago == 0:
                    return "اليوم"
                elif days_ago == 1:
                    return "أمس"
                else:
                    return f"منذ {days_ago} أيام"
            else:
                if days_ago == 0:
                    return "today"
                elif days_ago == 1:
                    return "yesterday"
                else:
                    return f"{days_ago} days ago"
                    
        except:
            return date
            
    def _estimate_variant_engagement(self, approach: str) -> float:
        """Estimate engagement for variant approach"""
        engagement_scores = {
            "formal": 0.6,
            "casual": 0.7,
            "emotional": 0.8
        }
        return engagement_scores.get(approach, 0.6)
        
    def _estimate_delivery_time(self, message_count: int) -> str:
        """Estimate delivery time for campaign"""
        # Assuming 10 messages per minute rate limit
        minutes = message_count / 10
        
        if minutes < 60:
            return f"{int(minutes)} minutes"
        else:
            hours = minutes / 60
            return f"{hours:.1f} hours"
            
    def _assess_formality(self, text: str, language: str) -> str:
        """Assess formality level of text"""
        if language in ["ar", "arabic"]:
            formal_indicators = ["حضرتك", "سعادتك", "تفضل"]
            casual_indicators = ["أنت", "هاي", "مرحبا"]
        else:
            formal_indicators = ["please", "would you", "kind regards"]
            casual_indicators = ["hey", "you", "thanks"]
            
        formal_count = sum(1 for ind in formal_indicators if ind in text.lower())
        casual_count = sum(1 for ind in casual_indicators if ind in text.lower())
        
        if formal_count > casual_count:
            return "formal"
        elif casual_count > formal_count:
            return "casual"
        else:
            return "neutral"
            
    def _assess_emotional_intensity(self, text: str, language: str) -> str:
        """Assess emotional intensity of text"""
        exclamation_count = text.count("!")
        caps_ratio = sum(1 for c in text if c.isupper()) / len(text) if text else 0
        
        if exclamation_count >= 2 or caps_ratio > 0.2:
            return "high"
        elif exclamation_count == 1 or caps_ratio > 0.1:
            return "medium"
        else:
            return "low"
            
    def _calculate_appeal_score(self, text: str, language: str) -> float:
        """Calculate appeal score for text"""
        score = 0.5
        
        # Length factor
        if 50 <= len(text) <= 200:
            score += 0.2
            
        # Personalization factor
        if "{" not in text:  # No unpersonalized variables
            score += 0.1
            
        # Emotional words
        if language in ["ar", "arabic"]:
            positive_words = ["سعداء", "نسعد", "يسرنا", "نفتخر"]
        else:
            positive_words = ["happy", "delighted", "pleased", "excited"]
            
        if any(word in text.lower() for word in positive_words):
            score += 0.2
            
        return min(score, 1.0)