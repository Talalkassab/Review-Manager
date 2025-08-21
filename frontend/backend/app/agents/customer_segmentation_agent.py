"""
Customer Segmentation Agent - Analyzes customer data and creates intelligent segments
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
from .base_agent import BaseRestaurantAgent
from .tools import DatabaseTool, AnalyticsTool, PredictiveModelingTool


class CustomerSegmentationAgent(BaseRestaurantAgent):
    """
    Specialized agent for customer segmentation and analysis.
    Creates dynamic segments based on behavior, preferences, and value.
    """
    
    def __init__(self):
        super().__init__(
            role="Customer Segmentation Specialist",
            goal="Create intelligent customer segments based on behavior, preferences, and lifetime value to enable targeted and personalized communication",
            backstory="""You are an expert data analyst specializing in customer segmentation for the restaurant industry. 
            With deep understanding of customer behavior patterns, demographics, and cultural preferences in the Middle Eastern market, 
            you excel at identifying valuable customer segments and predicting customer lifetime value. 
            Your insights help create highly targeted marketing campaigns that respect cultural nuances while maximizing engagement.""",
            tools=[
                DatabaseTool(),
                AnalyticsTool(),
                PredictiveModelingTool()
            ],
            verbose=True,
            allow_delegation=False,
            max_iter=5
        )
        
        # Define segment templates
        self.segment_templates = {
            "vip_customers": {
                "criteria": {
                    "visit_frequency": {"min": 10, "period_days": 30},
                    "average_order_value": {"min": 200},
                    "sentiment_history": ["positive", "neutral"]
                },
                "priority": "high",
                "communication_style": "exclusive"
            },
            "regular_customers": {
                "criteria": {
                    "visit_frequency": {"min": 4, "max": 9, "period_days": 30},
                    "average_order_value": {"min": 50, "max": 199},
                    "sentiment_history": ["positive", "neutral", "negative"]
                },
                "priority": "medium",
                "communication_style": "friendly"
            },
            "new_customers": {
                "criteria": {
                    "visit_frequency": {"max": 1, "period_days": 7},
                    "first_visit_days_ago": {"max": 7}
                },
                "priority": "high",
                "communication_style": "welcoming"
            },
            "at_risk_customers": {
                "criteria": {
                    "last_visit_days_ago": {"min": 30, "max": 60},
                    "previous_frequency": {"min": 2, "period_days": 30},
                    "sentiment_trend": "declining"
                },
                "priority": "critical",
                "communication_style": "re_engagement"
            },
            "lost_customers": {
                "criteria": {
                    "last_visit_days_ago": {"min": 61},
                    "previous_frequency": {"min": 1}
                },
                "priority": "low",
                "communication_style": "win_back"
            }
        }
        
    def analyze_customer_patterns(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze individual customer patterns and behaviors
        """
        self.log_task_start("analyze_customer_patterns", {"customer_id": customer_data.get("id")})
        
        try:
            analysis = {
                "customer_id": customer_data.get("id"),
                "behavior_patterns": self._identify_behavior_patterns(customer_data),
                "preferences": self._extract_preferences(customer_data),
                "value_metrics": self._calculate_value_metrics(customer_data),
                "risk_indicators": self._identify_risk_indicators(customer_data),
                "segment_recommendation": self._recommend_segment(customer_data)
            }
            
            self.log_task_complete("analyze_customer_patterns", analysis)
            return analysis
            
        except Exception as e:
            self.log_task_error("analyze_customer_patterns", e)
            raise
            
    def create_dynamic_segments(self, customers: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Create dynamic customer segments based on current data
        """
        self.log_task_start("create_dynamic_segments", {"customer_count": len(customers)})
        
        segments = {
            "vip_customers": [],
            "regular_customers": [],
            "new_customers": [],
            "at_risk_customers": [],
            "lost_customers": [],
            "custom_segments": {}
        }
        
        try:
            for customer in customers:
                segment = self._assign_to_segment(customer)
                if segment in segments:
                    segments[segment].append(customer["id"])
                    
            # Create custom segments based on patterns
            custom_segments = self._create_custom_segments(customers)
            segments["custom_segments"] = custom_segments
            
            # Store segment information for learning
            self.update_knowledge("latest_segments", segments)
            self.update_knowledge("segment_timestamp", datetime.now().isoformat())
            
            self.log_task_complete("create_dynamic_segments", {
                "segment_counts": {k: len(v) if isinstance(v, list) else len(v) 
                                  for k, v in segments.items()}
            })
            
            return segments
            
        except Exception as e:
            self.log_task_error("create_dynamic_segments", e)
            raise
            
    def predict_customer_lifetime_value(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict customer lifetime value based on behavior patterns
        """
        self.log_task_start("predict_lifetime_value", {"customer_id": customer_data.get("id")})
        
        try:
            # Calculate historical value
            historical_value = self._calculate_historical_value(customer_data)
            
            # Predict future value based on patterns
            predicted_value = self._predict_future_value(customer_data)
            
            # Calculate confidence score
            confidence = self._calculate_prediction_confidence(customer_data)
            
            ltv_prediction = {
                "customer_id": customer_data.get("id"),
                "historical_value": historical_value,
                "predicted_12_month_value": predicted_value,
                "total_lifetime_value": historical_value + predicted_value,
                "confidence_score": confidence,
                "value_tier": self._determine_value_tier(historical_value + predicted_value),
                "recommendations": self._get_value_recommendations(predicted_value, confidence)
            }
            
            self.log_task_complete("predict_lifetime_value", ltv_prediction)
            return ltv_prediction
            
        except Exception as e:
            self.log_task_error("predict_lifetime_value", e)
            raise
            
    def identify_at_risk_customers(self, customers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify customers at risk of churning
        """
        self.log_task_start("identify_at_risk", {"customer_count": len(customers)})
        
        at_risk = []
        
        try:
            for customer in customers:
                risk_score = self._calculate_churn_risk(customer)
                
                if risk_score > 0.6:  # High risk threshold
                    at_risk.append({
                        "customer_id": customer["id"],
                        "risk_score": risk_score,
                        "risk_factors": self._identify_risk_factors(customer),
                        "last_visit": customer.get("last_visit_date"),
                        "previous_frequency": self._calculate_previous_frequency(customer),
                        "intervention_priority": self._determine_intervention_priority(risk_score),
                        "recommended_actions": self._recommend_retention_actions(customer, risk_score)
                    })
                    
            # Sort by risk score (highest first)
            at_risk.sort(key=lambda x: x["risk_score"], reverse=True)
            
            self.log_task_complete("identify_at_risk", {"at_risk_count": len(at_risk)})
            return at_risk
            
        except Exception as e:
            self.log_task_error("identify_at_risk", e)
            raise
            
    def find_high_value_targets(self, customers: List[Dict[str, Any]], campaign_type: str) -> List[str]:
        """
        Find high-value targets for specific campaign types
        """
        self.log_task_start("find_high_value_targets", {"campaign_type": campaign_type})
        
        targets = []
        
        try:
            targeting_rules = self._get_campaign_targeting_rules(campaign_type)
            
            for customer in customers:
                score = self._calculate_target_score(customer, targeting_rules)
                
                if score > targeting_rules.get("threshold", 0.7):
                    targets.append({
                        "customer_id": customer["id"],
                        "target_score": score,
                        "value_tier": self._determine_value_tier(customer.get("total_spent", 0)),
                        "engagement_level": self._calculate_engagement_level(customer),
                        "personalization_data": self._extract_personalization_data(customer)
                    })
                    
            # Sort by target score
            targets.sort(key=lambda x: x["target_score"], reverse=True)
            
            # Take top performers based on campaign size limits
            max_targets = targeting_rules.get("max_targets", len(targets))
            targets = targets[:max_targets]
            
            self.log_task_complete("find_high_value_targets", {"targets_found": len(targets)})
            return [t["customer_id"] for t in targets]
            
        except Exception as e:
            self.log_task_error("find_high_value_targets", e)
            raise
            
    # Private helper methods
    def _identify_behavior_patterns(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Identify customer behavior patterns"""
        visits = customer_data.get("visits", [])
        
        return {
            "visit_frequency": self._calculate_visit_frequency(visits),
            "preferred_days": self._identify_preferred_days(visits),
            "preferred_times": self._identify_preferred_times(visits),
            "ordering_patterns": self._analyze_ordering_patterns(customer_data.get("orders", [])),
            "response_patterns": self._analyze_response_patterns(customer_data.get("messages", []))
        }
        
    def _extract_preferences(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract customer preferences"""
        return {
            "cuisine_preferences": self._analyze_cuisine_preferences(customer_data.get("orders", [])),
            "communication_preferences": {
                "language": customer_data.get("preferred_language", "ar"),
                "channel": customer_data.get("preferred_channel", "whatsapp"),
                "timing": self._identify_response_timing(customer_data.get("messages", []))
            },
            "dietary_restrictions": customer_data.get("dietary_restrictions", []),
            "special_occasions": self._identify_special_occasions(customer_data)
        }
        
    def _calculate_value_metrics(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate customer value metrics"""
        orders = customer_data.get("orders", [])
        
        return {
            "total_spent": sum(order.get("total", 0) for order in orders),
            "average_order_value": self._calculate_average_order_value(orders),
            "order_frequency": len(orders) / max(1, self._calculate_customer_age_days(customer_data)),
            "profit_contribution": self._estimate_profit_contribution(orders)
        }
        
    def _identify_risk_indicators(self, customer_data: Dict[str, Any]) -> List[str]:
        """Identify risk indicators for customer churn"""
        indicators = []
        
        # Check visit frequency decline
        if self._is_frequency_declining(customer_data):
            indicators.append("declining_visit_frequency")
            
        # Check sentiment trend
        if self._is_sentiment_declining(customer_data):
            indicators.append("declining_sentiment")
            
        # Check last visit date
        last_visit = customer_data.get("last_visit_date")
        if last_visit:
            days_since = (datetime.now() - datetime.fromisoformat(last_visit)).days
            if days_since > 30:
                indicators.append("extended_absence")
                
        # Check for unresolved complaints
        if self._has_unresolved_complaints(customer_data):
            indicators.append("unresolved_complaints")
            
        return indicators
        
    def _recommend_segment(self, customer_data: Dict[str, Any]) -> str:
        """Recommend the best segment for a customer"""
        # This would use more sophisticated logic in production
        risk_indicators = self._identify_risk_indicators(customer_data)
        
        if len(risk_indicators) >= 2:
            return "at_risk_customers"
            
        visits = len(customer_data.get("visits", []))
        if visits == 1:
            return "new_customers"
        elif visits >= 10:
            return "vip_customers"
        elif visits >= 4:
            return "regular_customers"
        else:
            return "occasional_customers"
            
    def _assign_to_segment(self, customer: Dict[str, Any]) -> str:
        """Assign customer to appropriate segment"""
        for segment_name, segment_config in self.segment_templates.items():
            if self._matches_segment_criteria(customer, segment_config["criteria"]):
                return segment_name
        return "uncategorized"
        
    def _matches_segment_criteria(self, customer: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """Check if customer matches segment criteria"""
        # Implement complex matching logic here
        # This is a simplified version
        return True  # Placeholder
        
    def _create_custom_segments(self, customers: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Create custom segments based on detected patterns"""
        custom_segments = {}
        
        # Example: Lunch crowd segment
        lunch_customers = []
        for customer in customers:
            if self._prefers_lunch_time(customer):
                lunch_customers.append(customer["id"])
                
        if lunch_customers:
            custom_segments["lunch_crowd"] = lunch_customers
            
        # Example: Weekend diners
        weekend_diners = []
        for customer in customers:
            if self._prefers_weekends(customer):
                weekend_diners.append(customer["id"])
                
        if weekend_diners:
            custom_segments["weekend_diners"] = weekend_diners
            
        return custom_segments
        
    def _calculate_historical_value(self, customer_data: Dict[str, Any]) -> float:
        """Calculate historical customer value"""
        orders = customer_data.get("orders", [])
        return sum(order.get("total", 0) for order in orders)
        
    def _predict_future_value(self, customer_data: Dict[str, Any]) -> float:
        """Predict future customer value"""
        # Simplified prediction - in production would use ML models
        historical_value = self._calculate_historical_value(customer_data)
        frequency = self._calculate_visit_frequency(customer_data.get("visits", []))
        
        # Basic prediction formula
        predicted_monthly = (historical_value / max(1, len(customer_data.get("visits", [])))) * frequency
        return predicted_monthly * 12  # 12-month prediction
        
    def _calculate_prediction_confidence(self, customer_data: Dict[str, Any]) -> float:
        """Calculate confidence in prediction"""
        # Factors affecting confidence
        visit_count = len(customer_data.get("visits", []))
        data_completeness = self._calculate_data_completeness(customer_data)
        pattern_consistency = self._calculate_pattern_consistency(customer_data)
        
        # Weighted confidence calculation
        confidence = (
            (min(visit_count, 20) / 20) * 0.4 +  # More visits = higher confidence
            data_completeness * 0.3 +
            pattern_consistency * 0.3
        )
        
        return min(confidence, 1.0)
        
    def _determine_value_tier(self, total_value: float) -> str:
        """Determine customer value tier"""
        if total_value >= 10000:
            return "platinum"
        elif total_value >= 5000:
            return "gold"
        elif total_value >= 2000:
            return "silver"
        elif total_value >= 500:
            return "bronze"
        else:
            return "standard"
            
    def _get_value_recommendations(self, predicted_value: float, confidence: float) -> List[str]:
        """Get recommendations based on predicted value"""
        recommendations = []
        
        if predicted_value > 5000 and confidence > 0.7:
            recommendations.append("Assign dedicated account manager")
            recommendations.append("Offer VIP loyalty program")
            recommendations.append("Send exclusive offers and previews")
            
        elif predicted_value > 2000:
            recommendations.append("Include in loyalty program")
            recommendations.append("Send personalized offers")
            recommendations.append("Invite to special events")
            
        else:
            recommendations.append("Send engagement campaigns")
            recommendations.append("Offer first-time visitor incentives")
            
        return recommendations
        
    def _calculate_churn_risk(self, customer: Dict[str, Any]) -> float:
        """Calculate customer churn risk score"""
        risk_score = 0.0
        
        # Factor 1: Days since last visit
        last_visit = customer.get("last_visit_date")
        if last_visit:
            days_since = (datetime.now() - datetime.fromisoformat(last_visit)).days
            risk_score += min(days_since / 60, 0.4)  # Max 0.4 contribution
            
        # Factor 2: Frequency decline
        if self._is_frequency_declining(customer):
            risk_score += 0.3
            
        # Factor 3: Sentiment
        if self._is_sentiment_declining(customer):
            risk_score += 0.2
            
        # Factor 4: Unresolved issues
        if self._has_unresolved_complaints(customer):
            risk_score += 0.1
            
        return min(risk_score, 1.0)
        
    def _identify_risk_factors(self, customer: Dict[str, Any]) -> List[str]:
        """Identify specific risk factors for a customer"""
        factors = []
        
        # Check various risk factors
        if self._is_frequency_declining(customer):
            factors.append("Declining visit frequency")
            
        if self._is_sentiment_declining(customer):
            factors.append("Declining satisfaction")
            
        last_visit = customer.get("last_visit_date")
        if last_visit:
            days_since = (datetime.now() - datetime.fromisoformat(last_visit)).days
            if days_since > 45:
                factors.append(f"No visit in {days_since} days")
                
        if self._has_unresolved_complaints(customer):
            factors.append("Unresolved complaints")
            
        return factors
        
    def _calculate_previous_frequency(self, customer: Dict[str, Any]) -> float:
        """Calculate previous visit frequency"""
        visits = customer.get("visits", [])
        if len(visits) < 2:
            return 0
            
        # Calculate average days between visits
        visit_dates = sorted([datetime.fromisoformat(v["date"]) for v in visits])
        intervals = []
        
        for i in range(1, len(visit_dates)):
            interval = (visit_dates[i] - visit_dates[i-1]).days
            intervals.append(interval)
            
        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            return 30 / max(avg_interval, 1)  # Visits per month
            
        return 0
        
    def _determine_intervention_priority(self, risk_score: float) -> str:
        """Determine intervention priority based on risk score"""
        if risk_score >= 0.8:
            return "critical"
        elif risk_score >= 0.6:
            return "high"
        elif risk_score >= 0.4:
            return "medium"
        else:
            return "low"
            
    def _recommend_retention_actions(self, customer: Dict[str, Any], risk_score: float) -> List[str]:
        """Recommend specific retention actions"""
        actions = []
        
        if risk_score >= 0.8:
            actions.append("Immediate personal outreach from manager")
            actions.append("Offer significant discount or complimentary meal")
            actions.append("Request feedback on issues")
            
        elif risk_score >= 0.6:
            actions.append("Send personalized re-engagement message")
            actions.append("Offer special promotion")
            actions.append("Invite to exclusive event")
            
        else:
            actions.append("Send friendly check-in message")
            actions.append("Share new menu items")
            actions.append("Offer small incentive")
            
        return actions
        
    # Additional helper methods
    def _calculate_visit_frequency(self, visits: List[Dict[str, Any]]) -> float:
        """Calculate visit frequency per month"""
        if not visits:
            return 0
        
        first_visit = min(datetime.fromisoformat(v["date"]) for v in visits)
        days_as_customer = (datetime.now() - first_visit).days
        
        if days_as_customer == 0:
            return len(visits)
            
        months = days_as_customer / 30
        return len(visits) / max(months, 1)
        
    def _identify_preferred_days(self, visits: List[Dict[str, Any]]) -> List[str]:
        """Identify preferred days of the week"""
        day_counts = {}
        
        for visit in visits:
            visit_date = datetime.fromisoformat(visit["date"])
            day_name = visit_date.strftime("%A")
            day_counts[day_name] = day_counts.get(day_name, 0) + 1
            
        # Return top 2 days
        sorted_days = sorted(day_counts.items(), key=lambda x: x[1], reverse=True)
        return [day for day, _ in sorted_days[:2]]
        
    def _identify_preferred_times(self, visits: List[Dict[str, Any]]) -> List[str]:
        """Identify preferred visit times"""
        time_slots = {
            "breakfast": (6, 11),
            "lunch": (11, 15),
            "dinner": (18, 22),
            "late_night": (22, 2)
        }
        
        slot_counts = {slot: 0 for slot in time_slots}
        
        for visit in visits:
            if "time" in visit:
                hour = datetime.fromisoformat(visit["time"]).hour
                for slot, (start, end) in time_slots.items():
                    if start <= hour < end or (start > end and (hour >= start or hour < end)):
                        slot_counts[slot] += 1
                        break
                        
        # Return slots with visits
        return [slot for slot, count in slot_counts.items() if count > 0]
        
    def _analyze_ordering_patterns(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze customer ordering patterns"""
        if not orders:
            return {"patterns": []}
            
        return {
            "favorite_items": self._identify_favorite_items(orders),
            "average_party_size": self._calculate_average_party_size(orders),
            "special_requests_frequency": self._calculate_special_requests_frequency(orders)
        }
        
    def _analyze_response_patterns(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze customer message response patterns"""
        if not messages:
            return {"response_rate": 0}
            
        sent = len([m for m in messages if m.get("direction") == "outbound"])
        received = len([m for m in messages if m.get("direction") == "inbound"])
        
        return {
            "response_rate": received / max(sent, 1),
            "average_response_time": self._calculate_avg_response_time(messages),
            "preferred_response_times": self._identify_response_timing(messages)
        }
        
    def _is_frequency_declining(self, customer: Dict[str, Any]) -> bool:
        """Check if visit frequency is declining"""
        visits = customer.get("visits", [])
        if len(visits) < 4:
            return False
            
        # Compare recent frequency with historical
        recent_visits = visits[-3:]
        older_visits = visits[:-3]
        
        recent_freq = self._calculate_visit_frequency(recent_visits)
        older_freq = self._calculate_visit_frequency(older_visits)
        
        return recent_freq < older_freq * 0.5  # 50% decline threshold
        
    def _is_sentiment_declining(self, customer: Dict[str, Any]) -> bool:
        """Check if customer sentiment is declining"""
        feedbacks = customer.get("feedbacks", [])
        if len(feedbacks) < 2:
            return False
            
        # Compare recent sentiment with historical
        recent = feedbacks[-2:]
        sentiment_scores = {"positive": 1, "neutral": 0, "negative": -1}
        
        recent_score = sum(sentiment_scores.get(f.get("sentiment", "neutral"), 0) for f in recent) / len(recent)
        
        return recent_score < -0.3
        
    def _has_unresolved_complaints(self, customer: Dict[str, Any]) -> bool:
        """Check for unresolved complaints"""
        complaints = customer.get("complaints", [])
        return any(c.get("status") != "resolved" for c in complaints)
        
    def _calculate_average_order_value(self, orders: List[Dict[str, Any]]) -> float:
        """Calculate average order value"""
        if not orders:
            return 0
        return sum(o.get("total", 0) for o in orders) / len(orders)
        
    def _calculate_customer_age_days(self, customer_data: Dict[str, Any]) -> int:
        """Calculate how long customer has been with restaurant"""
        first_visit = customer_data.get("first_visit_date")
        if first_visit:
            return (datetime.now() - datetime.fromisoformat(first_visit)).days
        return 1
        
    def _estimate_profit_contribution(self, orders: List[Dict[str, Any]]) -> float:
        """Estimate profit contribution (simplified)"""
        # Assume 30% profit margin
        total_revenue = sum(o.get("total", 0) for o in orders)
        return total_revenue * 0.3
        
    def _get_campaign_targeting_rules(self, campaign_type: str) -> Dict[str, Any]:
        """Get targeting rules for campaign type"""
        rules = {
            "promotion": {
                "min_visits": 2,
                "max_days_since_visit": 30,
                "min_sentiment": "neutral",
                "threshold": 0.6,
                "max_targets": 100
            },
            "feedback": {
                "min_visits": 1,
                "max_days_since_visit": 7,
                "threshold": 0.5,
                "max_targets": 200
            },
            "vip_event": {
                "min_visits": 10,
                "min_order_value": 200,
                "min_sentiment": "positive",
                "threshold": 0.8,
                "max_targets": 50
            }
        }
        return rules.get(campaign_type, rules["promotion"])
        
    def _calculate_target_score(self, customer: Dict[str, Any], rules: Dict[str, Any]) -> float:
        """Calculate targeting score for customer"""
        score = 0.0
        max_score = 0.0
        
        # Check visit frequency
        visits = len(customer.get("visits", []))
        if visits >= rules.get("min_visits", 0):
            score += 0.3
        max_score += 0.3
        
        # Check recency
        last_visit = customer.get("last_visit_date")
        if last_visit:
            days_since = (datetime.now() - datetime.fromisoformat(last_visit)).days
            if days_since <= rules.get("max_days_since_visit", 30):
                score += 0.3
        max_score += 0.3
        
        # Check sentiment
        sentiment = customer.get("last_sentiment", "neutral")
        min_sentiment = rules.get("min_sentiment", "negative")
        sentiment_scores = {"positive": 3, "neutral": 2, "negative": 1}
        
        if sentiment_scores.get(sentiment, 0) >= sentiment_scores.get(min_sentiment, 0):
            score += 0.2
        max_score += 0.2
        
        # Check order value
        avg_order = self._calculate_average_order_value(customer.get("orders", []))
        if avg_order >= rules.get("min_order_value", 0):
            score += 0.2
        max_score += 0.2
        
        return score / max_score if max_score > 0 else 0
        
    def _calculate_engagement_level(self, customer: Dict[str, Any]) -> str:
        """Calculate customer engagement level"""
        messages = customer.get("messages", [])
        response_rate = 0
        
        if messages:
            sent = len([m for m in messages if m.get("direction") == "outbound"])
            received = len([m for m in messages if m.get("direction") == "inbound"])
            response_rate = received / max(sent, 1)
            
        if response_rate >= 0.7:
            return "high"
        elif response_rate >= 0.3:
            return "medium"
        else:
            return "low"
            
    def _extract_personalization_data(self, customer: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data for message personalization"""
        return {
            "name": customer.get("name"),
            "preferred_language": customer.get("preferred_language", "ar"),
            "favorite_items": self._identify_favorite_items(customer.get("orders", [])),
            "special_occasions": customer.get("special_occasions", []),
            "dietary_preferences": customer.get("dietary_restrictions", [])
        }
        
    def _analyze_cuisine_preferences(self, orders: List[Dict[str, Any]]) -> List[str]:
        """Analyze cuisine preferences from orders"""
        cuisine_counts = {}
        
        for order in orders:
            for item in order.get("items", []):
                cuisine = item.get("cuisine_type", "general")
                cuisine_counts[cuisine] = cuisine_counts.get(cuisine, 0) + 1
                
        # Return top cuisines
        sorted_cuisines = sorted(cuisine_counts.items(), key=lambda x: x[1], reverse=True)
        return [cuisine for cuisine, _ in sorted_cuisines[:3]]
        
    def _identify_response_timing(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Identify when customer typically responds"""
        response_hours = []
        
        for message in messages:
            if message.get("direction") == "inbound" and "timestamp" in message:
                hour = datetime.fromisoformat(message["timestamp"]).hour
                response_hours.append(hour)
                
        if not response_hours:
            return ["anytime"]
            
        # Group into time periods
        morning = sum(1 for h in response_hours if 6 <= h < 12)
        afternoon = sum(1 for h in response_hours if 12 <= h < 18)
        evening = sum(1 for h in response_hours if 18 <= h < 24)
        
        periods = []
        if morning > len(response_hours) * 0.3:
            periods.append("morning")
        if afternoon > len(response_hours) * 0.3:
            periods.append("afternoon")
        if evening > len(response_hours) * 0.3:
            periods.append("evening")
            
        return periods if periods else ["anytime"]
        
    def _identify_special_occasions(self, customer_data: Dict[str, Any]) -> List[str]:
        """Identify special occasions for customer"""
        occasions = []
        
        # Check for birthday visits
        visits = customer_data.get("visits", [])
        for visit in visits:
            if visit.get("occasion") == "birthday":
                occasions.append("birthday")
                break
                
        # Check for anniversary visits
        for visit in visits:
            if visit.get("occasion") == "anniversary":
                occasions.append("anniversary")
                break
                
        # Check for holiday visits
        for visit in visits:
            if visit.get("occasion") in ["eid", "ramadan", "national_day"]:
                if visit.get("occasion") not in occasions:
                    occasions.append(visit.get("occasion"))
                    
        return occasions
        
    def _calculate_data_completeness(self, customer_data: Dict[str, Any]) -> float:
        """Calculate how complete the customer data is"""
        required_fields = ["name", "phone", "email", "visits", "orders", "preferred_language"]
        present_fields = sum(1 for field in required_fields if customer_data.get(field))
        return present_fields / len(required_fields)
        
    def _calculate_pattern_consistency(self, customer_data: Dict[str, Any]) -> float:
        """Calculate how consistent customer patterns are"""
        visits = customer_data.get("visits", [])
        if len(visits) < 3:
            return 0.5  # Not enough data
            
        # Check consistency in visit timing
        visit_days = [datetime.fromisoformat(v["date"]).weekday() for v in visits]
        unique_days = len(set(visit_days))
        consistency = 1.0 - (unique_days / 7)  # More consistent if fewer unique days
        
        return consistency
        
    def _prefers_lunch_time(self, customer: Dict[str, Any]) -> bool:
        """Check if customer prefers lunch time visits"""
        visits = customer.get("visits", [])
        lunch_visits = 0
        
        for visit in visits:
            if "time" in visit:
                hour = datetime.fromisoformat(visit["time"]).hour
                if 11 <= hour < 15:
                    lunch_visits += 1
                    
        return lunch_visits > len(visits) * 0.5
        
    def _prefers_weekends(self, customer: Dict[str, Any]) -> bool:
        """Check if customer prefers weekend visits"""
        visits = customer.get("visits", [])
        weekend_visits = 0
        
        for visit in visits:
            visit_date = datetime.fromisoformat(visit["date"])
            if visit_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                weekend_visits += 1
                
        return weekend_visits > len(visits) * 0.5
        
    def _identify_favorite_items(self, orders: List[Dict[str, Any]]) -> List[str]:
        """Identify customer's favorite menu items"""
        item_counts = {}
        
        for order in orders:
            for item in order.get("items", []):
                item_name = item.get("name")
                if item_name:
                    item_counts[item_name] = item_counts.get(item_name, 0) + 1
                    
        # Return top 3 items
        sorted_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)
        return [item for item, _ in sorted_items[:3]]
        
    def _calculate_average_party_size(self, orders: List[Dict[str, Any]]) -> float:
        """Calculate average party size from orders"""
        party_sizes = [o.get("party_size", 1) for o in orders if "party_size" in o]
        if party_sizes:
            return sum(party_sizes) / len(party_sizes)
        return 1.0
        
    def _calculate_special_requests_frequency(self, orders: List[Dict[str, Any]]) -> float:
        """Calculate how often customer makes special requests"""
        requests = sum(1 for o in orders if o.get("special_requests"))
        return requests / len(orders) if orders else 0
        
    def _calculate_avg_response_time(self, messages: List[Dict[str, Any]]) -> float:
        """Calculate average response time in hours"""
        response_times = []
        
        for i in range(1, len(messages)):
            if (messages[i-1].get("direction") == "outbound" and 
                messages[i].get("direction") == "inbound"):
                
                sent_time = datetime.fromisoformat(messages[i-1]["timestamp"])
                response_time = datetime.fromisoformat(messages[i]["timestamp"])
                hours = (response_time - sent_time).total_seconds() / 3600
                response_times.append(hours)
                
        if response_times:
            return sum(response_times) / len(response_times)
        return 24.0  # Default to 24 hours if no data