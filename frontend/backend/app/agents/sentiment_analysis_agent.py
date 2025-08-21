"""
Sentiment Analysis Agent - Processes customer emotions and context with high accuracy
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
import re
from .base_agent import BaseRestaurantAgent
from .tools import OpenRouterTool, TextProcessingTool, EmotionDetectionTool


class SentimentAnalysisAgent(BaseRestaurantAgent):
    """
    Specialized agent for advanced sentiment analysis with cultural context.
    Detects emotions, urgency, and hidden meanings in customer feedback.
    """
    
    def __init__(self):
        super().__init__(
            role="Customer Emotion Intelligence Specialist",
            goal="Understand customer emotions with high accuracy, detecting sentiment, urgency, sarcasm, and cultural nuances in both Arabic and English feedback",
            backstory="""You are an expert in emotional intelligence and linguistic analysis, specializing in customer feedback interpretation. 
            With deep understanding of both Arabic and English communication patterns, you excel at detecting subtle emotional cues, 
            sarcasm, and hidden meanings. Your expertise in Middle Eastern cultural expressions allows you to accurately interpret 
            feedback that might be misunderstood by standard sentiment analysis. You help the restaurant understand not just what 
            customers are saying, but what they truly mean and feel.""",
            tools=[
                OpenRouterTool(),
                TextProcessingTool(),
                EmotionDetectionTool()
            ],
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
        
        # Sentiment indicators for different languages
        self.sentiment_indicators = {
            "arabic": {
                "positive": {
                    "strong": ["ممتاز", "رائع", "مذهل", "خيالي", "روعة", "تحفة", "الله يعطيكم العافية"],
                    "moderate": ["جيد", "حلو", "لذيذ", "جميل", "مناسب", "كويس"],
                    "mild": ["لا بأس", "مقبول", "عادي", "ماشي الحال"]
                },
                "negative": {
                    "strong": ["سيء جداً", "مقرف", "كارثة", "فاشل", "مو زين", "خايس"],
                    "moderate": ["سيء", "مو حلو", "ما عجبني", "ضعيف", "مخيب للآمال"],
                    "mild": ["يحتاج تحسين", "ممكن أفضل", "متوسط", "عادي"]
                },
                "neutral": ["عادي", "متوسط", "لا بأس", "مقبول"]
            },
            "english": {
                "positive": {
                    "strong": ["excellent", "amazing", "fantastic", "wonderful", "outstanding", "perfect", "love it"],
                    "moderate": ["good", "nice", "delicious", "great", "satisfying", "enjoyable"],
                    "mild": ["okay", "fine", "decent", "not bad", "acceptable"]
                },
                "negative": {
                    "strong": ["terrible", "horrible", "awful", "disgusting", "worst", "unacceptable"],
                    "moderate": ["bad", "poor", "disappointing", "not good", "below average"],
                    "mild": ["could be better", "needs improvement", "average", "mediocre"]
                },
                "neutral": ["okay", "average", "normal", "regular"]
            }
        }
        
        # Emotion categories
        self.emotion_categories = {
            "joy": ["happy", "delighted", "pleased", "satisfied", "سعيد", "مسرور", "فرحان"],
            "anger": ["angry", "frustrated", "annoyed", "irritated", "غاضب", "زعلان", "منزعج"],
            "sadness": ["sad", "disappointed", "unhappy", "upset", "حزين", "مكتئب", "محبط"],
            "fear": ["worried", "concerned", "anxious", "afraid", "قلق", "خائف", "متوتر"],
            "surprise": ["surprised", "shocked", "amazed", "astonished", "مندهش", "متفاجئ", "مذهول"],
            "disgust": ["disgusted", "repulsed", "revolted", "مشمئز", "قرفان", "متقزز"]
        }
        
        # Urgency indicators
        self.urgency_indicators = {
            "high": ["immediately", "urgent", "asap", "now", "emergency", "فوراً", "عاجل", "الآن", "ضروري"],
            "medium": ["soon", "quickly", "when possible", "قريباً", "بأسرع وقت", "لو سمحت"],
            "low": ["whenever", "no rush", "when you can", "متى ما تقدر", "على راحتك"]
        }
        
        # Sarcasm patterns
        self.sarcasm_patterns = {
            "arabic": [
                r"ما شاء الله.*سيء",
                r"روعة.*\!{2,}",
                r"والله.*عجيب",
                r"يا سلام.*",
                r"تمام.*\."
            ],
            "english": [
                r"oh great.*",
                r"wonderful.*\!{2,}",
                r"perfect.*just perfect",
                r"thanks a lot.*",
                r"really.*amazing"
            ]
        }
        
    def analyze_sentiment(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Perform comprehensive sentiment analysis on text
        """
        self.log_task_start("analyze_sentiment", {"text_length": len(text)})
        
        try:
            # Detect language
            language = self._detect_language(text)
            
            # Basic sentiment detection
            basic_sentiment = self._detect_basic_sentiment(text, language)
            
            # Emotion detection
            emotions = self._detect_emotions(text, language)
            
            # Urgency detection
            urgency = self._detect_urgency(text, language)
            
            # Sarcasm detection
            sarcasm = self._detect_sarcasm(text, language, context)
            
            # Context-aware adjustment
            adjusted_sentiment = self._adjust_sentiment_with_context(
                basic_sentiment, emotions, sarcasm, context
            )
            
            # Calculate confidence score
            confidence = self._calculate_confidence(text, language, adjusted_sentiment)
            
            # Extract key phrases
            key_phrases = self._extract_key_phrases(text, language)
            
            # Identify specific issues or compliments
            specific_feedback = self._identify_specific_feedback(text, language)
            
            result = {
                "text": text,
                "language": language,
                "sentiment": adjusted_sentiment["sentiment"],
                "sentiment_score": adjusted_sentiment["score"],
                "confidence": confidence,
                "emotions": emotions,
                "urgency": urgency,
                "sarcasm_detected": sarcasm["detected"],
                "sarcasm_confidence": sarcasm["confidence"],
                "key_phrases": key_phrases,
                "specific_feedback": specific_feedback,
                "requires_immediate_attention": self._requires_immediate_attention(adjusted_sentiment, urgency),
                "recommended_response_tone": self._recommend_response_tone(adjusted_sentiment, emotions),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            # Store in knowledge base for learning
            self.update_knowledge(f"sentiment_analysis_{datetime.now().timestamp()}", result)
            
            self.log_task_complete("analyze_sentiment", result)
            return result
            
        except Exception as e:
            self.log_task_error("analyze_sentiment", e)
            raise
            
    def analyze_conversation_sentiment(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze sentiment across an entire conversation
        """
        self.log_task_start("analyze_conversation_sentiment", {"message_count": len(messages)})
        
        try:
            sentiments = []
            emotions_timeline = []
            
            for message in messages:
                analysis = self.analyze_sentiment(message["content"], {"message_context": message})
                sentiments.append(analysis["sentiment"])
                emotions_timeline.append({
                    "timestamp": message.get("timestamp"),
                    "sentiment": analysis["sentiment"],
                    "emotions": analysis["emotions"]
                })
                
            # Calculate sentiment trend
            sentiment_trend = self._calculate_sentiment_trend(sentiments)
            
            # Identify turning points
            turning_points = self._identify_turning_points(emotions_timeline)
            
            # Overall conversation sentiment
            overall_sentiment = self._calculate_overall_sentiment(sentiments)
            
            # Emotional journey
            emotional_journey = self._map_emotional_journey(emotions_timeline)
            
            result = {
                "message_count": len(messages),
                "overall_sentiment": overall_sentiment,
                "sentiment_trend": sentiment_trend,
                "turning_points": turning_points,
                "emotional_journey": emotional_journey,
                "final_sentiment": sentiments[-1] if sentiments else "neutral",
                "sentiment_improved": sentiment_trend == "improving",
                "requires_follow_up": self._requires_follow_up(overall_sentiment, sentiment_trend)
            }
            
            self.log_task_complete("analyze_conversation_sentiment", result)
            return result
            
        except Exception as e:
            self.log_task_error("analyze_conversation_sentiment", e)
            raise
            
    def detect_escalation_triggers(self, text: str, history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Detect triggers that might require escalation
        """
        self.log_task_start("detect_escalation_triggers")
        
        try:
            triggers = []
            escalation_level = "none"
            
            # Check for explicit complaint words
            complaint_triggers = self._detect_complaint_triggers(text)
            if complaint_triggers:
                triggers.extend(complaint_triggers)
                escalation_level = "medium"
                
            # Check for threat indicators
            threat_triggers = self._detect_threat_indicators(text)
            if threat_triggers:
                triggers.extend(threat_triggers)
                escalation_level = "high"
                
            # Check for legal/health concerns
            legal_health_triggers = self._detect_legal_health_concerns(text)
            if legal_health_triggers:
                triggers.extend(legal_health_triggers)
                escalation_level = "critical"
                
            # Check sentiment history for degradation
            if history:
                sentiment_degradation = self._check_sentiment_degradation(history)
                if sentiment_degradation:
                    triggers.append("Continuous sentiment degradation detected")
                    if escalation_level == "none":
                        escalation_level = "medium"
                        
            result = {
                "triggers_detected": len(triggers) > 0,
                "triggers": triggers,
                "escalation_level": escalation_level,
                "recommended_action": self._recommend_escalation_action(escalation_level, triggers),
                "notify_manager": escalation_level in ["high", "critical"],
                "response_time_requirement": self._get_response_time_requirement(escalation_level)
            }
            
            self.log_task_complete("detect_escalation_triggers", result)
            return result
            
        except Exception as e:
            self.log_task_error("detect_escalation_triggers", e)
            raise
            
    def analyze_feedback_quality(self, text: str) -> Dict[str, Any]:
        """
        Analyze the quality and usefulness of feedback
        """
        self.log_task_start("analyze_feedback_quality")
        
        try:
            # Check specificity
            specificity = self._measure_specificity(text)
            
            # Check constructiveness
            constructiveness = self._measure_constructiveness(text)
            
            # Check actionability
            actionability = self._measure_actionability(text)
            
            # Calculate overall quality score
            quality_score = (specificity * 0.4 + constructiveness * 0.3 + actionability * 0.3)
            
            # Determine feedback category
            category = self._categorize_feedback(text)
            
            # Extract actionable insights
            actionable_insights = self._extract_actionable_insights(text)
            
            result = {
                "text": text,
                "quality_score": quality_score,
                "specificity": specificity,
                "constructiveness": constructiveness,
                "actionability": actionability,
                "category": category,
                "actionable_insights": actionable_insights,
                "is_valuable": quality_score > 0.6,
                "requires_follow_up": len(actionable_insights) > 0
            }
            
            self.log_task_complete("analyze_feedback_quality", result)
            return result
            
        except Exception as e:
            self.log_task_error("analyze_feedback_quality", e)
            raise
            
    def generate_sentiment_insights(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate insights from multiple sentiment analyses
        """
        self.log_task_start("generate_sentiment_insights", {"analysis_count": len(analyses)})
        
        try:
            # Aggregate sentiments
            sentiment_distribution = self._calculate_sentiment_distribution(analyses)
            
            # Common emotions
            common_emotions = self._identify_common_emotions(analyses)
            
            # Recurring themes
            recurring_themes = self._identify_recurring_themes(analyses)
            
            # Time-based patterns
            time_patterns = self._analyze_time_patterns(analyses)
            
            # Language preferences
            language_distribution = self._analyze_language_distribution(analyses)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                sentiment_distribution, 
                common_emotions, 
                recurring_themes
            )
            
            insights = {
                "total_analyses": len(analyses),
                "sentiment_distribution": sentiment_distribution,
                "dominant_sentiment": max(sentiment_distribution, key=sentiment_distribution.get),
                "common_emotions": common_emotions,
                "recurring_themes": recurring_themes,
                "time_patterns": time_patterns,
                "language_distribution": language_distribution,
                "customer_satisfaction_score": self._calculate_satisfaction_score(sentiment_distribution),
                "areas_of_concern": self._identify_areas_of_concern(recurring_themes, sentiment_distribution),
                "recommendations": recommendations,
                "trend": self._determine_overall_trend(analyses)
            }
            
            self.log_task_complete("generate_sentiment_insights", insights)
            return insights
            
        except Exception as e:
            self.log_task_error("generate_sentiment_insights", e)
            raise
            
    # Private helper methods
    def _detect_language(self, text: str) -> str:
        """Detect the language of the text"""
        arabic_chars = set("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
        arabic_count = sum(1 for char in text if char in arabic_chars)
        
        if arabic_count > len(text) * 0.3:
            return "arabic"
        else:
            return "english"
            
    def _detect_basic_sentiment(self, text: str, language: str) -> Dict[str, Any]:
        """Detect basic sentiment from text"""
        text_lower = text.lower()
        indicators = self.sentiment_indicators.get(language, self.sentiment_indicators["english"])
        
        positive_score = 0
        negative_score = 0
        
        # Check positive indicators
        for strength, words in indicators["positive"].items():
            for word in words:
                if word in text_lower:
                    if strength == "strong":
                        positive_score += 3
                    elif strength == "moderate":
                        positive_score += 2
                    else:
                        positive_score += 1
                        
        # Check negative indicators
        for strength, words in indicators["negative"].items():
            for word in words:
                if word in text_lower:
                    if strength == "strong":
                        negative_score += 3
                    elif strength == "moderate":
                        negative_score += 2
                    else:
                        negative_score += 1
                        
        # Determine sentiment
        if positive_score > negative_score:
            sentiment = "positive"
            score = positive_score / (positive_score + negative_score) if negative_score > 0 else 1.0
        elif negative_score > positive_score:
            sentiment = "negative"
            score = -negative_score / (positive_score + negative_score) if positive_score > 0 else -1.0
        else:
            sentiment = "neutral"
            score = 0.0
            
        return {"sentiment": sentiment, "score": score}
        
    def _detect_emotions(self, text: str, language: str) -> List[str]:
        """Detect emotions in text"""
        detected_emotions = []
        text_lower = text.lower()
        
        for emotion, keywords in self.emotion_categories.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    if emotion not in detected_emotions:
                        detected_emotions.append(emotion)
                        
        # If no specific emotions detected, infer from sentiment
        if not detected_emotions:
            sentiment = self._detect_basic_sentiment(text, language)["sentiment"]
            if sentiment == "positive":
                detected_emotions = ["joy"]
            elif sentiment == "negative":
                detected_emotions = ["sadness"]
                
        return detected_emotions
        
    def _detect_urgency(self, text: str, language: str) -> str:
        """Detect urgency level in text"""
        text_lower = text.lower()
        
        for level, indicators in self.urgency_indicators.items():
            for indicator in indicators:
                if indicator.lower() in text_lower:
                    return level
                    
        # Check for exclamation marks and caps
        exclamation_count = text.count("!")
        caps_ratio = sum(1 for c in text if c.isupper()) / len(text) if text else 0
        
        if exclamation_count >= 3 or caps_ratio > 0.5:
            return "high"
        elif exclamation_count >= 1 or caps_ratio > 0.3:
            return "medium"
        else:
            return "low"
            
    def _detect_sarcasm(self, text: str, language: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Detect sarcasm in text"""
        patterns = self.sarcasm_patterns.get(language, self.sarcasm_patterns["english"])
        
        sarcasm_score = 0
        
        # Check regex patterns
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                sarcasm_score += 0.3
                
        # Check for contradiction between words and punctuation
        positive_words = self.sentiment_indicators[language]["positive"]["strong"]
        has_positive = any(word in text.lower() for word in positive_words)
        has_negative_punctuation = "..." in text or "!!!" in text
        
        if has_positive and has_negative_punctuation:
            sarcasm_score += 0.4
            
        # Check context for previous negative experience
        if context and context.get("previous_sentiment") == "negative":
            if has_positive:
                sarcasm_score += 0.3
                
        detected = sarcasm_score > 0.5
        confidence = min(sarcasm_score, 1.0)
        
        return {"detected": detected, "confidence": confidence}
        
    def _adjust_sentiment_with_context(self, basic_sentiment: Dict[str, Any], 
                                      emotions: List[str], sarcasm: Dict[str, Any], 
                                      context: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust sentiment based on context"""
        adjusted_sentiment = basic_sentiment.copy()
        
        # Adjust for sarcasm
        if sarcasm["detected"] and sarcasm["confidence"] > 0.7:
            if adjusted_sentiment["sentiment"] == "positive":
                adjusted_sentiment["sentiment"] = "negative"
                adjusted_sentiment["score"] = -abs(adjusted_sentiment["score"])
                
        # Adjust for emotions
        if "disgust" in emotions or "anger" in emotions:
            if adjusted_sentiment["sentiment"] != "negative":
                adjusted_sentiment["sentiment"] = "negative"
                adjusted_sentiment["score"] = min(adjusted_sentiment["score"] - 0.5, -0.5)
                
        # Adjust based on context
        if context:
            # If customer had previous bad experience, be more cautious
            if context.get("previous_sentiment") == "negative":
                adjusted_sentiment["score"] *= 0.8
                
        return adjusted_sentiment
        
    def _calculate_confidence(self, text: str, language: str, sentiment: Dict[str, Any]) -> float:
        """Calculate confidence in sentiment analysis"""
        confidence = 0.5
        
        # Text length factor
        if len(text) > 100:
            confidence += 0.2
        elif len(text) > 50:
            confidence += 0.1
            
        # Clear sentiment indicators
        if abs(sentiment["score"]) > 0.7:
            confidence += 0.2
            
        # Language detection confidence
        if language == "arabic" and self._contains_arabic(text):
            confidence += 0.1
        elif language == "english" and not self._contains_arabic(text):
            confidence += 0.1
            
        return min(confidence, 1.0)
        
    def _extract_key_phrases(self, text: str, language: str) -> List[str]:
        """Extract key phrases that influenced sentiment"""
        key_phrases = []
        
        # Extract phrases with sentiment indicators
        indicators = self.sentiment_indicators.get(language, self.sentiment_indicators["english"])
        
        for category in ["positive", "negative"]:
            for strength, words in indicators[category].items():
                for word in words:
                    if word in text.lower():
                        # Extract surrounding context
                        pattern = rf".{{0,20}}{re.escape(word)}.{{0,20}}"
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        key_phrases.extend(matches)
                        
        return list(set(key_phrases))[:5]  # Return top 5 unique phrases
        
    def _identify_specific_feedback(self, text: str, language: str) -> Dict[str, List[str]]:
        """Identify specific feedback about food, service, ambiance, etc."""
        feedback = {
            "food": [],
            "service": [],
            "ambiance": [],
            "price": [],
            "cleanliness": [],
            "timing": []
        }
        
        # Keywords for each category
        keywords = {
            "food": ["food", "meal", "dish", "taste", "flavor", "طعام", "وجبة", "طبق", "طعم", "نكهة"],
            "service": ["service", "staff", "waiter", "server", "خدمة", "موظف", "نادل", "عامل"],
            "ambiance": ["atmosphere", "ambiance", "music", "decor", "جو", "أجواء", "موسيقى", "ديكور"],
            "price": ["price", "expensive", "cheap", "value", "سعر", "غالي", "رخيص", "قيمة"],
            "cleanliness": ["clean", "dirty", "hygiene", "نظيف", "وسخ", "نظافة"],
            "timing": ["wait", "time", "slow", "fast", "انتظار", "وقت", "بطيء", "سريع"]
        }
        
        text_lower = text.lower()
        
        for category, words in keywords.items():
            for word in words:
                if word in text_lower:
                    # Extract the sentence containing the keyword
                    sentences = text.split(".")
                    for sentence in sentences:
                        if word in sentence.lower():
                            feedback[category].append(sentence.strip())
                            break
                            
        return feedback
        
    def _requires_immediate_attention(self, sentiment: Dict[str, Any], urgency: str) -> bool:
        """Determine if feedback requires immediate attention"""
        return (
            (sentiment["sentiment"] == "negative" and abs(sentiment["score"]) > 0.7) or
            urgency == "high" or
            sentiment["sentiment"] == "negative" and urgency == "medium"
        )
        
    def _recommend_response_tone(self, sentiment: Dict[str, Any], emotions: List[str]) -> str:
        """Recommend appropriate response tone"""
        if sentiment["sentiment"] == "negative":
            if "anger" in emotions:
                return "apologetic_understanding"
            elif "sadness" in emotions:
                return "empathetic_supportive"
            else:
                return "professional_concerned"
        elif sentiment["sentiment"] == "positive":
            if "joy" in emotions:
                return "enthusiastic_grateful"
            else:
                return "warm_appreciative"
        else:
            return "friendly_professional"
            
    def _calculate_sentiment_trend(self, sentiments: List[str]) -> str:
        """Calculate sentiment trend over time"""
        if len(sentiments) < 2:
            return "stable"
            
        # Convert to numeric scores
        scores = []
        for sentiment in sentiments:
            if sentiment == "positive":
                scores.append(1)
            elif sentiment == "negative":
                scores.append(-1)
            else:
                scores.append(0)
                
        # Calculate trend
        first_half = sum(scores[:len(scores)//2])
        second_half = sum(scores[len(scores)//2:])
        
        if second_half > first_half:
            return "improving"
        elif second_half < first_half:
            return "declining"
        else:
            return "stable"
            
    def _identify_turning_points(self, timeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify turning points in emotional timeline"""
        turning_points = []
        
        for i in range(1, len(timeline) - 1):
            prev_sentiment = timeline[i-1]["sentiment"]
            curr_sentiment = timeline[i]["sentiment"]
            next_sentiment = timeline[i+1]["sentiment"]
            
            # Check for sentiment change
            if prev_sentiment != curr_sentiment or curr_sentiment != next_sentiment:
                turning_points.append({
                    "index": i,
                    "timestamp": timeline[i]["timestamp"],
                    "from_sentiment": prev_sentiment,
                    "to_sentiment": next_sentiment,
                    "emotions": timeline[i]["emotions"]
                })
                
        return turning_points
        
    def _calculate_overall_sentiment(self, sentiments: List[str]) -> str:
        """Calculate overall sentiment from list"""
        if not sentiments:
            return "neutral"
            
        sentiment_counts = {
            "positive": sentiments.count("positive"),
            "negative": sentiments.count("negative"),
            "neutral": sentiments.count("neutral")
        }
        
        # Weight recent sentiments more heavily
        if len(sentiments) > 3:
            recent = sentiments[-3:]
            for sentiment in recent:
                sentiment_counts[sentiment] += 1
                
        return max(sentiment_counts, key=sentiment_counts.get)
        
    def _map_emotional_journey(self, timeline: List[Dict[str, Any]]) -> List[str]:
        """Map the emotional journey of conversation"""
        journey = []
        
        for point in timeline:
            sentiment = point["sentiment"]
            emotions = point["emotions"]
            
            if sentiment == "positive" and "joy" in emotions:
                journey.append("delighted")
            elif sentiment == "positive":
                journey.append("satisfied")
            elif sentiment == "negative" and "anger" in emotions:
                journey.append("frustrated")
            elif sentiment == "negative":
                journey.append("disappointed")
            else:
                journey.append("neutral")
                
        return journey
        
    def _requires_follow_up(self, overall_sentiment: str, trend: str) -> bool:
        """Determine if conversation requires follow-up"""
        return (
            overall_sentiment == "negative" or
            trend == "declining" or
            (overall_sentiment == "neutral" and trend != "improving")
        )
        
    def _detect_complaint_triggers(self, text: str) -> List[str]:
        """Detect complaint trigger words"""
        triggers = []
        
        complaint_words = [
            "complaint", "complain", "terrible", "awful", "worst", "unacceptable",
            "شكوى", "سيء", "مقرف", "فاشل", "غير مقبول"
        ]
        
        text_lower = text.lower()
        for word in complaint_words:
            if word in text_lower:
                triggers.append(f"Complaint word detected: {word}")
                
        return triggers
        
    def _detect_threat_indicators(self, text: str) -> List[str]:
        """Detect threat indicators"""
        triggers = []
        
        threat_words = [
            "lawyer", "sue", "legal", "court", "media", "social media", "review",
            "محامي", "قضية", "محكمة", "إعلام", "تويتر", "انستقرام"
        ]
        
        text_lower = text.lower()
        for word in threat_words:
            if word in text_lower:
                triggers.append(f"Potential escalation threat: {word}")
                
        return triggers
        
    def _detect_legal_health_concerns(self, text: str) -> List[str]:
        """Detect legal or health concerns"""
        triggers = []
        
        concern_words = [
            "poisoning", "sick", "hospital", "allergy", "contaminated", "expired",
            "تسمم", "مريض", "مستشفى", "حساسية", "ملوث", "منتهي"
        ]
        
        text_lower = text.lower()
        for word in concern_words:
            if word in text_lower:
                triggers.append(f"Health/Legal concern: {word}")
                
        return triggers
        
    def _check_sentiment_degradation(self, history: List[Dict[str, Any]]) -> bool:
        """Check if sentiment is degrading over time"""
        if len(history) < 3:
            return False
            
        recent_sentiments = [msg.get("sentiment", "neutral") for msg in history[-3:]]
        negative_count = recent_sentiments.count("negative")
        
        return negative_count >= 2
        
    def _recommend_escalation_action(self, level: str, triggers: List[str]) -> str:
        """Recommend escalation action based on level"""
        actions = {
            "critical": "Immediately notify manager and legal team. Prepare incident report.",
            "high": "Alert manager within 15 minutes. Prepare response strategy.",
            "medium": "Flag for supervisor review. Respond within 1 hour.",
            "none": "Continue normal response process."
        }
        return actions.get(level, "Monitor situation.")
        
    def _get_response_time_requirement(self, level: str) -> str:
        """Get required response time based on escalation level"""
        times = {
            "critical": "Immediate (< 5 minutes)",
            "high": "Within 15 minutes",
            "medium": "Within 1 hour",
            "none": "Within 24 hours"
        }
        return times.get(level, "Standard response time")
        
    def _measure_specificity(self, text: str) -> float:
        """Measure how specific the feedback is"""
        specific_indicators = [
            "specifically", "exactly", "particular", "بالتحديد", "بالضبط", "خاصة"
        ]
        
        score = 0.3  # Base score
        
        # Check for specific indicators
        for indicator in specific_indicators:
            if indicator in text.lower():
                score += 0.2
                
        # Check for details (numbers, names, etc.)
        if re.search(r'\d+', text):  # Contains numbers
            score += 0.2
        if re.search(r'[A-Z][a-z]+', text):  # Contains proper nouns
            score += 0.1
            
        # Length factor (longer usually more specific)
        if len(text) > 100:
            score += 0.2
            
        return min(score, 1.0)
        
    def _measure_constructiveness(self, text: str) -> float:
        """Measure how constructive the feedback is"""
        constructive_indicators = [
            "suggest", "recommend", "should", "could", "better if",
            "أقترح", "أنصح", "يجب", "ممكن", "أفضل لو"
        ]
        
        destructive_indicators = [
            "hate", "never", "worst", "terrible",
            "أكره", "أبداً", "أسوأ", "فظيع"
        ]
        
        constructive_score = sum(1 for ind in constructive_indicators if ind in text.lower())
        destructive_score = sum(1 for ind in destructive_indicators if ind in text.lower())
        
        if constructive_score + destructive_score == 0:
            return 0.5
            
        return constructive_score / (constructive_score + destructive_score)
        
    def _measure_actionability(self, text: str) -> float:
        """Measure how actionable the feedback is"""
        actionable_indicators = [
            "should", "need to", "must", "have to", "please",
            "يجب", "لازم", "ضروري", "من فضلك", "لو سمحت"
        ]
        
        score = 0.2  # Base score
        
        for indicator in actionable_indicators:
            if indicator in text.lower():
                score += 0.2
                
        # Check for specific suggestions
        if "instead" in text.lower() or "بدل" in text:
            score += 0.3
            
        return min(score, 1.0)
        
    def _categorize_feedback(self, text: str) -> str:
        """Categorize the type of feedback"""
        categories = {
            "complaint": ["problem", "issue", "bad", "مشكلة", "سيء"],
            "suggestion": ["suggest", "recommend", "should", "أقترح", "أنصح"],
            "compliment": ["great", "excellent", "love", "ممتاز", "رائع"],
            "question": ["?", "how", "what", "when", "كيف", "متى", "ماذا"],
            "general": []
        }
        
        text_lower = text.lower()
        
        for category, keywords in categories.items():
            if category == "general":
                continue
            for keyword in keywords:
                if keyword in text_lower:
                    return category
                    
        return "general"
        
    def _extract_actionable_insights(self, text: str) -> List[str]:
        """Extract actionable insights from feedback"""
        insights = []
        
        # Look for specific suggestions
        suggestion_patterns = [
            r"should\s+(\w+\s+\w+)",
            r"need[s]?\s+to\s+(\w+\s+\w+)",
            r"please\s+(\w+\s+\w+)",
            r"يجب\s+(\w+\s+\w+)",
            r"لازم\s+(\w+\s+\w+)"
        ]
        
        for pattern in suggestion_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            insights.extend(matches)
            
        return list(set(insights))[:5]  # Return top 5 unique insights
        
    def _calculate_sentiment_distribution(self, analyses: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate distribution of sentiments"""
        total = len(analyses)
        if total == 0:
            return {"positive": 0, "negative": 0, "neutral": 0}
            
        distribution = {
            "positive": sum(1 for a in analyses if a["sentiment"] == "positive") / total,
            "negative": sum(1 for a in analyses if a["sentiment"] == "negative") / total,
            "neutral": sum(1 for a in analyses if a["sentiment"] == "neutral") / total
        }
        
        return distribution
        
    def _identify_common_emotions(self, analyses: List[Dict[str, Any]]) -> List[Tuple[str, int]]:
        """Identify most common emotions"""
        emotion_counts = {}
        
        for analysis in analyses:
            for emotion in analysis.get("emotions", []):
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                
        # Sort by frequency
        sorted_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_emotions[:5]
        
    def _identify_recurring_themes(self, analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify recurring themes in feedback"""
        theme_counts = {}
        
        for analysis in analyses:
            feedback = analysis.get("specific_feedback", {})
            for category, items in feedback.items():
                if items:
                    theme_counts[category] = theme_counts.get(category, 0) + len(items)
                    
        themes = []
        for theme, count in theme_counts.items():
            if count > 2:  # Minimum threshold for recurring
                themes.append({
                    "theme": theme,
                    "frequency": count,
                    "percentage": count / len(analyses) * 100
                })
                
        return sorted(themes, key=lambda x: x["frequency"], reverse=True)
        
    def _analyze_time_patterns(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sentiment patterns over time"""
        if not analyses:
            return {}
            
        # Group by day of week (simplified)
        day_sentiments = {}
        
        for analysis in analyses:
            timestamp = analysis.get("analysis_timestamp")
            if timestamp:
                day = datetime.fromisoformat(timestamp).strftime("%A")
                if day not in day_sentiments:
                    day_sentiments[day] = []
                day_sentiments[day].append(analysis["sentiment"])
                
        # Calculate average sentiment per day
        day_averages = {}
        for day, sentiments in day_sentiments.items():
            positive_ratio = sentiments.count("positive") / len(sentiments)
            day_averages[day] = positive_ratio
            
        return {
            "best_day": max(day_averages, key=day_averages.get) if day_averages else None,
            "worst_day": min(day_averages, key=day_averages.get) if day_averages else None,
            "day_averages": day_averages
        }
        
    def _analyze_language_distribution(self, analyses: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze language distribution in feedback"""
        total = len(analyses)
        if total == 0:
            return {"arabic": 0, "english": 0}
            
        return {
            "arabic": sum(1 for a in analyses if a.get("language") == "arabic") / total,
            "english": sum(1 for a in analyses if a.get("language") == "english") / total
        }
        
    def _generate_recommendations(self, distribution: Dict[str, float], 
                                 emotions: List[Tuple[str, int]], 
                                 themes: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on insights"""
        recommendations = []
        
        # Based on sentiment distribution
        if distribution.get("negative", 0) > 0.3:
            recommendations.append("High negative sentiment detected. Implement service recovery program.")
            
        if distribution.get("positive", 0) > 0.7:
            recommendations.append("Excellent positive sentiment. Leverage for testimonials and reviews.")
            
        # Based on emotions
        top_emotions = [e[0] for e in emotions[:2]]
        if "anger" in top_emotions:
            recommendations.append("Anger is prevalent. Review and address service issues immediately.")
        if "joy" in top_emotions:
            recommendations.append("Customers are happy. Maintain current service standards.")
            
        # Based on themes
        for theme in themes[:2]:
            if theme["theme"] == "service" and theme["percentage"] > 20:
                recommendations.append("Service feedback is frequent. Consider staff training program.")
            elif theme["theme"] == "food" and theme["percentage"] > 20:
                recommendations.append("Food quality mentioned often. Review menu and preparation standards.")
                
        return recommendations
        
    def _calculate_satisfaction_score(self, distribution: Dict[str, float]) -> float:
        """Calculate overall satisfaction score"""
        # Weighted satisfaction score
        score = (
            distribution.get("positive", 0) * 1.0 +
            distribution.get("neutral", 0) * 0.5 +
            distribution.get("negative", 0) * 0.0
        )
        return round(score * 100, 2)
        
    def _identify_areas_of_concern(self, themes: List[Dict[str, Any]], 
                                  distribution: Dict[str, float]) -> List[str]:
        """Identify areas requiring attention"""
        concerns = []
        
        # High negative sentiment
        if distribution.get("negative", 0) > 0.4:
            concerns.append("Overall negative sentiment exceeds acceptable threshold")
            
        # Recurring negative themes
        for theme in themes:
            if theme["frequency"] > 5:
                concerns.append(f"Recurring issues with {theme['theme']}")
                
        return concerns
        
    def _determine_overall_trend(self, analyses: List[Dict[str, Any]]) -> str:
        """Determine overall trend from analyses"""
        if len(analyses) < 2:
            return "insufficient_data"
            
        # Compare first half with second half
        mid = len(analyses) // 2
        first_half = analyses[:mid]
        second_half = analyses[mid:]
        
        first_positive = sum(1 for a in first_half if a["sentiment"] == "positive")
        second_positive = sum(1 for a in second_half if a["sentiment"] == "positive")
        
        if second_positive > first_positive:
            return "improving"
        elif second_positive < first_positive:
            return "declining"
        else:
            return "stable"
            
    def _contains_arabic(self, text: str) -> bool:
        """Check if text contains Arabic characters"""
        arabic_chars = set("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
        return any(char in arabic_chars for char in text)