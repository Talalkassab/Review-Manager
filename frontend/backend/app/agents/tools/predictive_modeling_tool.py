"""
Predictive modeling tool for customer behavior analysis
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import statistics
import math
from .base_tool import BaseAgentTool, ToolResult


class PredictiveModelingTool(BaseAgentTool):
    """Tool for predictive modeling and customer behavior forecasting"""
    
    name: str = "predictive_modeling"
    description: str = (
        "Perform predictive modeling including customer lifetime value prediction, "
        "churn risk assessment, and behavioral pattern forecasting."
    )
    
    def _validate_input(self, **kwargs) -> bool:
        """Validate predictive modeling parameters"""
        model_type = kwargs.get('model_type')
        if not model_type:
            self.logger.error("model_type parameter is required")
            return False
        
        valid_models = [
            'ltv_prediction', 'churn_risk', 'visit_frequency',
            'spending_forecast', 'satisfaction_prediction', 'response_prediction'
        ]
        
        if model_type not in valid_models:
            self.logger.error(f"Invalid model_type: {model_type}")
            return False
            
        return True
    
    def _execute(self, **kwargs) -> Dict[str, Any]:
        """Execute predictive modeling"""
        model_type = kwargs.get('model_type')
        customer_data = kwargs.get('customer_data', {})
        historical_data = kwargs.get('historical_data', [])
        
        try:
            if model_type == 'ltv_prediction':
                return self._predict_customer_lifetime_value(customer_data, historical_data)
            elif model_type == 'churn_risk':
                return self._assess_churn_risk(customer_data, historical_data)
            elif model_type == 'visit_frequency':
                return self._predict_visit_frequency(customer_data, historical_data)
            elif model_type == 'spending_forecast':
                return self._forecast_customer_spending(customer_data, historical_data)
            elif model_type == 'satisfaction_prediction':
                return self._predict_satisfaction(customer_data, historical_data)
            elif model_type == 'response_prediction':
                return self._predict_response_likelihood(customer_data, historical_data)
            else:
                raise ValueError(f"Unsupported model_type: {model_type}")
                
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Predictive modeling failed: {str(e)}"
            ).dict()
    
    def _predict_customer_lifetime_value(self, 
                                       customer_data: Dict[str, Any], 
                                       historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Predict customer lifetime value using simplified model"""
        
        # Extract key metrics
        visit_count = customer_data.get('visit_count', 0)
        total_spent = customer_data.get('total_spent', 0)
        avg_order_value = customer_data.get('average_order_value', 0)
        first_visit = customer_data.get('first_visit_date')
        last_visit = customer_data.get('last_visit_date')
        
        if visit_count == 0:
            return ToolResult(
                success=False, 
                error="No visit history for LTV prediction"
            ).dict()
        
        # Calculate customer age in months
        if first_visit:
            first_visit_date = datetime.fromisoformat(first_visit)
            customer_age_months = (datetime.now() - first_visit_date).days / 30
        else:
            customer_age_months = 1
        
        # Calculate monthly visit frequency
        monthly_frequency = visit_count / max(customer_age_months, 1)
        
        # Calculate recency factor (how recent was last visit)
        if last_visit:
            last_visit_date = datetime.fromisoformat(last_visit)
            recency_days = (datetime.now() - last_visit_date).days
            recency_factor = max(0.1, 1 - (recency_days / 180))  # Decay over 6 months
        else:
            recency_factor = 0.1
        
        # Calculate frequency trend
        frequency_trend = self._calculate_frequency_trend(historical_data)
        
        # Predict monthly spend
        predicted_monthly_spend = monthly_frequency * avg_order_value * recency_factor * frequency_trend
        
        # Predict customer lifespan (simplified)
        base_lifespan_months = 24  # Base 2 years
        frequency_bonus = min(monthly_frequency * 2, 12)  # Up to 12 months bonus
        spending_bonus = min((total_spent / 1000) * 6, 12)  # Up to 12 months bonus
        
        predicted_lifespan = base_lifespan_months + frequency_bonus + spending_bonus
        
        # Calculate LTV
        predicted_ltv = predicted_monthly_spend * predicted_lifespan
        
        # Calculate confidence based on data quality
        confidence = self._calculate_ltv_confidence(
            customer_data, historical_data, customer_age_months
        )
        
        result_data = {
            "predicted_ltv": round(predicted_ltv, 2),
            "predicted_monthly_spend": round(predicted_monthly_spend, 2),
            "predicted_lifespan_months": round(predicted_lifespan, 1),
            "current_value": total_spent,
            "confidence_score": confidence,
            "value_tier": self._classify_value_tier(predicted_ltv),
            "key_factors": {
                "visit_frequency": monthly_frequency,
                "avg_order_value": avg_order_value,
                "recency_factor": recency_factor,
                "frequency_trend": frequency_trend
            }
        }
        
        return ToolResult(
            success=True,
            data=result_data,
            metadata={"model_type": "ltv_prediction", "prediction_date": datetime.now().isoformat()}
        ).dict()
    
    def _assess_churn_risk(self, 
                          customer_data: Dict[str, Any], 
                          historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess customer churn risk"""
        
        risk_factors = []
        risk_score = 0.0
        
        # Factor 1: Recency of last visit
        last_visit = customer_data.get('last_visit_date')
        if last_visit:
            last_visit_date = datetime.fromisoformat(last_visit)
            days_since = (datetime.now() - last_visit_date).days
            
            if days_since > 90:
                risk_score += 0.4
                risk_factors.append(f"No visit in {days_since} days")
            elif days_since > 60:
                risk_score += 0.3
                risk_factors.append(f"Last visit {days_since} days ago")
            elif days_since > 30:
                risk_score += 0.2
                risk_factors.append(f"Last visit {days_since} days ago")
        else:
            risk_score += 0.3
            risk_factors.append("No visit history")
        
        # Factor 2: Visit frequency decline
        frequency_decline = self._detect_frequency_decline(historical_data)
        if frequency_decline['is_declining']:
            risk_score += 0.3
            risk_factors.append(f"Visit frequency declined by {frequency_decline['decline_percent']:.1f}%")
        
        # Factor 3: Spending decline
        spending_decline = self._detect_spending_decline(historical_data)
        if spending_decline['is_declining']:
            risk_score += 0.2
            risk_factors.append(f"Spending declined by {spending_decline['decline_percent']:.1f}%")
        
        # Factor 4: Negative sentiment
        sentiment_history = customer_data.get('sentiment_history', [])
        if sentiment_history:
            negative_count = sentiment_history.count('negative')
            negative_ratio = negative_count / len(sentiment_history)
            
            if negative_ratio > 0.5:
                risk_score += 0.3
                risk_factors.append("Predominantly negative sentiment")
            elif negative_ratio > 0.3:
                risk_score += 0.2
                risk_factors.append("High negative sentiment ratio")
        
        # Factor 5: Response rate decline
        response_rate = customer_data.get('response_rate', 1.0)
        if response_rate < 0.3:
            risk_score += 0.2
            risk_factors.append("Low response rate to messages")
        elif response_rate < 0.5:
            risk_score += 0.1
            risk_factors.append("Declining response rate")
        
        # Factor 6: Customer tier and value
        total_spent = customer_data.get('total_spent', 0)
        if total_spent > 1000:  # High value customer
            risk_score *= 0.8  # Slightly reduce risk for high-value customers
        
        # Cap risk score at 1.0
        risk_score = min(risk_score, 1.0)
        
        # Classify risk level
        if risk_score >= 0.8:
            risk_level = "critical"
        elif risk_score >= 0.6:
            risk_level = "high"
        elif risk_score >= 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Generate intervention recommendations
        interventions = self._generate_churn_interventions(risk_level, risk_factors, customer_data)
        
        result_data = {
            "churn_risk_score": round(risk_score, 3),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "probability_churn_30_days": round(risk_score * 0.3, 3),
            "probability_churn_90_days": round(risk_score * 0.6, 3),
            "intervention_priority": risk_level,
            "recommended_interventions": interventions,
            "factors_analyzed": len(risk_factors)
        }
        
        return ToolResult(
            success=True,
            data=result_data,
            metadata={"model_type": "churn_risk", "assessment_date": datetime.now().isoformat()}
        ).dict()
    
    def _predict_visit_frequency(self, 
                                customer_data: Dict[str, Any], 
                                historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Predict future visit frequency"""
        
        visit_count = customer_data.get('visit_count', 0)
        if visit_count == 0:
            return ToolResult(success=False, error="No visit history").dict()
        
        # Calculate historical frequency
        first_visit = customer_data.get('first_visit_date')
        if first_visit:
            first_visit_date = datetime.fromisoformat(first_visit)
            days_as_customer = (datetime.now() - first_visit_date).days
            historical_frequency = visit_count / max(days_as_customer, 1) * 30  # Visits per month
        else:
            historical_frequency = visit_count / 30  # Assume 1 month
        
        # Analyze visit pattern trends
        visit_trend = self._analyze_visit_trends(historical_data)
        
        # Apply trend adjustment
        trend_factor = 1.0 + visit_trend['trend_slope']
        predicted_frequency = historical_frequency * trend_factor
        
        # Apply seasonal factors (simplified)
        seasonal_factor = self._estimate_seasonal_factor()
        seasonal_adjusted_frequency = predicted_frequency * seasonal_factor
        
        # Apply external factors (simplified)
        external_factors = self._estimate_external_factors(customer_data)
        final_frequency = seasonal_adjusted_frequency * external_factors
        
        # Ensure reasonable bounds
        final_frequency = max(0.1, min(final_frequency, 30))  # 0.1 to 30 visits per month
        
        # Generate predictions for different time horizons
        predictions = {
            "next_30_days": round(final_frequency, 2),
            "next_60_days": round(final_frequency * 2, 2),
            "next_90_days": round(final_frequency * 3, 2)
        }
        
        # Calculate confidence
        confidence = self._calculate_frequency_confidence(
            customer_data, historical_data, visit_trend
        )
        
        result_data = {
            "predicted_visit_frequency": predictions,
            "historical_frequency_per_month": round(historical_frequency, 2),
            "trend_adjustment": round(trend_factor, 3),
            "seasonal_adjustment": round(seasonal_factor, 3),
            "confidence_score": confidence,
            "next_visit_probability": {
                "within_7_days": min(final_frequency * 0.25, 1.0),
                "within_14_days": min(final_frequency * 0.5, 1.0),
                "within_30_days": min(final_frequency, 1.0)
            }
        }
        
        return ToolResult(
            success=True,
            data=result_data,
            metadata={"model_type": "visit_frequency", "prediction_date": datetime.now().isoformat()}
        ).dict()
    
    def _forecast_customer_spending(self, 
                                  customer_data: Dict[str, Any], 
                                  historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Forecast customer spending patterns"""
        
        total_spent = customer_data.get('total_spent', 0)
        avg_order_value = customer_data.get('average_order_value', 0)
        visit_count = customer_data.get('visit_count', 0)
        
        if visit_count == 0:
            return ToolResult(success=False, error="No purchase history").dict()
        
        # Analyze spending trends
        spending_trend = self._analyze_spending_trends(historical_data)
        
        # Predict visit frequency (use the other model)
        frequency_prediction = self._predict_visit_frequency(customer_data, historical_data)
        if not frequency_prediction.get('success', False):
            predicted_monthly_visits = 1
        else:
            predicted_monthly_visits = frequency_prediction['data']['predicted_visit_frequency']['next_30_days']
        
        # Apply spending trend to average order value
        trend_adjusted_aov = avg_order_value * (1 + spending_trend['trend_slope'])
        
        # Calculate predicted monthly spending
        predicted_monthly_spending = predicted_monthly_visits * trend_adjusted_aov
        
        # Apply confidence-based adjustments
        confidence = self._calculate_spending_confidence(customer_data, historical_data)
        confidence_adjusted_spending = predicted_monthly_spending * confidence
        
        # Generate spending forecasts for different periods
        forecasts = {
            "next_month": round(confidence_adjusted_spending, 2),
            "next_quarter": round(confidence_adjusted_spending * 3, 2),
            "next_year": round(confidence_adjusted_spending * 12, 2)
        }
        
        # Identify spending category
        if predicted_monthly_spending >= 500:
            spending_category = "high_spender"
        elif predicted_monthly_spending >= 200:
            spending_category = "moderate_spender"
        else:
            spending_category = "light_spender"
        
        result_data = {
            "spending_forecasts": forecasts,
            "predicted_monthly_spending": round(predicted_monthly_spending, 2),
            "current_avg_order_value": avg_order_value,
            "trend_adjusted_aov": round(trend_adjusted_aov, 2),
            "spending_category": spending_category,
            "confidence_score": confidence,
            "key_assumptions": {
                "predicted_visits_per_month": predicted_monthly_visits,
                "spending_trend_slope": spending_trend['trend_slope'],
                "confidence_adjustment": confidence
            }
        }
        
        return ToolResult(
            success=True,
            data=result_data,
            metadata={"model_type": "spending_forecast", "prediction_date": datetime.now().isoformat()}
        ).dict()
    
    def _predict_satisfaction(self, 
                            customer_data: Dict[str, Any], 
                            historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Predict customer satisfaction trends"""
        
        # Analyze historical satisfaction
        sentiment_history = customer_data.get('sentiment_history', [])
        if not sentiment_history:
            return ToolResult(success=False, error="No sentiment history").dict()
        
        # Convert sentiments to numeric scores
        sentiment_scores = []
        for sentiment in sentiment_history:
            if sentiment == 'positive':
                sentiment_scores.append(1)
            elif sentiment == 'negative':
                sentiment_scores.append(-1)
            else:
                sentiment_scores.append(0)
        
        # Calculate current satisfaction trend
        if len(sentiment_scores) >= 3:
            recent_scores = sentiment_scores[-3:]
            older_scores = sentiment_scores[:-3] if len(sentiment_scores) > 3 else sentiment_scores[:-1]
            
            recent_avg = statistics.mean(recent_scores)
            older_avg = statistics.mean(older_scores) if older_scores else recent_avg
            
            satisfaction_trend = recent_avg - older_avg
        else:
            satisfaction_trend = 0
            recent_avg = statistics.mean(sentiment_scores)
        
        # Predict future satisfaction
        predicted_satisfaction = recent_avg + satisfaction_trend
        predicted_satisfaction = max(-1, min(predicted_satisfaction, 1))  # Bound between -1 and 1
        
        # Convert to satisfaction level
        if predicted_satisfaction >= 0.5:
            satisfaction_level = "highly_satisfied"
            probability_positive = 0.8 + (predicted_satisfaction - 0.5) * 0.4
        elif predicted_satisfaction >= 0:
            satisfaction_level = "satisfied"
            probability_positive = 0.5 + predicted_satisfaction * 0.3
        elif predicted_satisfaction >= -0.5:
            satisfaction_level = "neutral"
            probability_positive = 0.3 + (predicted_satisfaction + 0.5) * 0.2
        else:
            satisfaction_level = "dissatisfied"
            probability_positive = 0.1 + (predicted_satisfaction + 1) * 0.2
        
        # Risk of negative feedback
        probability_negative = 1 - probability_positive - 0.2  # 20% neutral probability
        probability_negative = max(0, probability_negative)
        
        result_data = {
            "predicted_satisfaction_score": round(predicted_satisfaction, 3),
            "satisfaction_level": satisfaction_level,
            "satisfaction_trend": "improving" if satisfaction_trend > 0.1 else "declining" if satisfaction_trend < -0.1 else "stable",
            "probability_positive_feedback": round(probability_positive, 3),
            "probability_negative_feedback": round(probability_negative, 3),
            "risk_level": "low" if probability_negative < 0.3 else "medium" if probability_negative < 0.6 else "high",
            "historical_sentiment_distribution": {
                "positive": sentiment_history.count('positive'),
                "neutral": sentiment_history.count('neutral'),
                "negative": sentiment_history.count('negative')
            }
        }
        
        return ToolResult(
            success=True,
            data=result_data,
            metadata={"model_type": "satisfaction_prediction", "prediction_date": datetime.now().isoformat()}
        ).dict()
    
    def _predict_response_likelihood(self, 
                                   customer_data: Dict[str, Any], 
                                   historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Predict likelihood of customer responding to messages"""
        
        # Historical response rate
        response_rate = customer_data.get('response_rate', 0.5)
        
        # Analyze factors that influence response
        factors = {}
        
        # Factor 1: Engagement level
        visit_count = customer_data.get('visit_count', 0)
        if visit_count >= 10:
            engagement_bonus = 0.2
            factors['high_engagement'] = True
        elif visit_count >= 5:
            engagement_bonus = 0.1
            factors['medium_engagement'] = True
        else:
            engagement_bonus = 0
            factors['low_engagement'] = True
        
        # Factor 2: Recent activity
        last_visit = customer_data.get('last_visit_date')
        if last_visit:
            last_visit_date = datetime.fromisoformat(last_visit)
            days_since = (datetime.now() - last_visit_date).days
            
            if days_since <= 7:
                recency_bonus = 0.3
                factors['very_recent_visit'] = True
            elif days_since <= 30:
                recency_bonus = 0.1
                factors['recent_visit'] = True
            else:
                recency_bonus = -0.1
                factors['old_visit'] = True
        else:
            recency_bonus = -0.2
            factors['no_visit_history'] = True
        
        # Factor 3: Sentiment
        sentiment_history = customer_data.get('sentiment_history', [])
        if sentiment_history:
            positive_ratio = sentiment_history.count('positive') / len(sentiment_history)
            if positive_ratio >= 0.7:
                sentiment_bonus = 0.2
                factors['positive_sentiment'] = True
            elif positive_ratio <= 0.3:
                sentiment_bonus = -0.2
                factors['negative_sentiment'] = True
            else:
                sentiment_bonus = 0
                factors['neutral_sentiment'] = True
        else:
            sentiment_bonus = 0
        
        # Factor 4: Language preference
        preferred_language = customer_data.get('preferred_language', 'ar')
        if preferred_language == 'ar':
            language_bonus = 0.1  # Assuming Arabic speakers are more responsive in this context
            factors['arabic_speaker'] = True
        else:
            language_bonus = 0
            factors['english_speaker'] = True
        
        # Calculate predicted response rate
        predicted_rate = response_rate + engagement_bonus + recency_bonus + sentiment_bonus + language_bonus
        predicted_rate = max(0.05, min(predicted_rate, 0.95))  # Bound between 5% and 95%
        
        # Predict response time (if they respond)
        if response_rate > 0.7:
            avg_response_hours = 2
        elif response_rate > 0.5:
            avg_response_hours = 6
        else:
            avg_response_hours = 24
        
        # Adjust based on engagement
        if factors.get('high_engagement'):
            avg_response_hours *= 0.5
        elif factors.get('low_engagement'):
            avg_response_hours *= 2
        
        result_data = {
            "predicted_response_rate": round(predicted_rate, 3),
            "historical_response_rate": response_rate,
            "response_likelihood": "very_high" if predicted_rate >= 0.8 else 
                                 "high" if predicted_rate >= 0.6 else 
                                 "medium" if predicted_rate >= 0.4 else "low",
            "predicted_response_time_hours": round(avg_response_hours, 1),
            "influencing_factors": factors,
            "recommendations": {
                "best_contact_time": self._recommend_contact_time(customer_data),
                "message_type": self._recommend_message_type(factors),
                "follow_up_needed": predicted_rate < 0.5
            }
        }
        
        return ToolResult(
            success=True,
            data=result_data,
            metadata={"model_type": "response_prediction", "prediction_date": datetime.now().isoformat()}
        ).dict()
    
    # Helper methods for calculations
    def _calculate_frequency_trend(self, historical_data: List[Dict[str, Any]]) -> float:
        """Calculate visit frequency trend"""
        if len(historical_data) < 4:
            return 1.0
        
        # Split data into periods
        mid = len(historical_data) // 2
        recent = historical_data[mid:]
        older = historical_data[:mid]
        
        recent_frequency = len(recent) / max(1, len(recent) * 30)  # Simplified
        older_frequency = len(older) / max(1, len(older) * 30)
        
        if older_frequency == 0:
            return 1.0
        
        trend = recent_frequency / older_frequency
        return max(0.5, min(trend, 2.0))  # Bound the trend
    
    def _calculate_ltv_confidence(self, 
                                customer_data: Dict[str, Any], 
                                historical_data: List[Dict[str, Any]], 
                                customer_age_months: float) -> float:
        """Calculate confidence in LTV prediction"""
        confidence = 0.5  # Base confidence
        
        # Data completeness
        data_fields = ['visit_count', 'total_spent', 'average_order_value', 'first_visit_date']
        completeness = sum(1 for field in data_fields if customer_data.get(field)) / len(data_fields)
        confidence += completeness * 0.2
        
        # Customer maturity
        if customer_age_months >= 12:
            confidence += 0.2
        elif customer_age_months >= 6:
            confidence += 0.1
        
        # Visit count
        visit_count = customer_data.get('visit_count', 0)
        if visit_count >= 10:
            confidence += 0.2
        elif visit_count >= 5:
            confidence += 0.1
        
        return min(confidence, 0.95)
    
    def _classify_value_tier(self, ltv: float) -> str:
        """Classify customer into value tier based on LTV"""
        if ltv >= 5000:
            return "platinum"
        elif ltv >= 2500:
            return "gold" 
        elif ltv >= 1000:
            return "silver"
        elif ltv >= 500:
            return "bronze"
        else:
            return "standard"
    
    def _detect_frequency_decline(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect if visit frequency is declining"""
        if len(historical_data) < 4:
            return {"is_declining": False, "decline_percent": 0}
        
        # Compare recent vs older periods
        mid = len(historical_data) // 2
        recent_visits = len(historical_data[mid:])
        older_visits = len(historical_data[:mid])
        
        if older_visits == 0:
            return {"is_declining": False, "decline_percent": 0}
        
        decline_percent = ((older_visits - recent_visits) / older_visits) * 100
        is_declining = decline_percent > 20  # 20% threshold
        
        return {
            "is_declining": is_declining,
            "decline_percent": max(0, decline_percent)
        }
    
    def _detect_spending_decline(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect if spending is declining"""
        if len(historical_data) < 2:
            return {"is_declining": False, "decline_percent": 0}
        
        # Extract spending data
        spending_data = [item.get('total_spent', 0) for item in historical_data if item.get('total_spent')]
        
        if len(spending_data) < 2:
            return {"is_declining": False, "decline_percent": 0}
        
        mid = len(spending_data) // 2
        recent_avg = statistics.mean(spending_data[mid:])
        older_avg = statistics.mean(spending_data[:mid])
        
        if older_avg == 0:
            return {"is_declining": False, "decline_percent": 0}
        
        decline_percent = ((older_avg - recent_avg) / older_avg) * 100
        is_declining = decline_percent > 15  # 15% threshold
        
        return {
            "is_declining": is_declining,
            "decline_percent": max(0, decline_percent)
        }
    
    def _generate_churn_interventions(self, 
                                    risk_level: str, 
                                    risk_factors: List[str], 
                                    customer_data: Dict[str, Any]) -> List[str]:
        """Generate intervention recommendations based on churn risk"""
        interventions = []
        
        if risk_level == "critical":
            interventions.extend([
                "Immediate personal call from manager",
                "Offer significant discount or complimentary meal",
                "Request detailed feedback on service issues",
                "Assign dedicated account representative"
            ])
        elif risk_level == "high":
            interventions.extend([
                "Send personalized re-engagement message",
                "Offer exclusive promotion or preview",
                "Invite to special tasting event",
                "Follow up within 48 hours"
            ])
        elif risk_level == "medium":
            interventions.extend([
                "Send friendly check-in message",
                "Share new menu items or seasonal specials",
                "Offer loyalty program benefits",
                "Monitor for 2 weeks"
            ])
        else:  # low risk
            interventions.extend([
                "Include in regular newsletter",
                "Send birthday/anniversary greetings",
                "Quarterly satisfaction survey"
            ])
        
        # Customize based on specific risk factors
        if "negative sentiment" in str(risk_factors):
            interventions.append("Address specific complaints mentioned in feedback")
        
        if "low response rate" in str(risk_factors):
            interventions.append("Try different communication channels")
        
        return interventions
    
    def _analyze_visit_trends(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze visit pattern trends"""
        if len(historical_data) < 3:
            return {"trend_slope": 0, "trend_direction": "stable"}
        
        # Simple trend analysis using visit dates
        visit_counts_by_period = []
        
        # Group by months (simplified)
        monthly_visits = {}
        for item in historical_data:
            if 'visit_date' in item or 'date' in item:
                date_str = item.get('visit_date') or item.get('date')
                try:
                    visit_date = datetime.fromisoformat(date_str)
                    month_key = visit_date.strftime("%Y-%m")
                    monthly_visits[month_key] = monthly_visits.get(month_key, 0) + 1
                except:
                    continue
        
        if len(monthly_visits) < 2:
            return {"trend_slope": 0, "trend_direction": "stable"}
        
        # Calculate trend
        months = sorted(monthly_visits.keys())
        visit_counts = [monthly_visits[month] for month in months]
        
        # Simple linear trend
        n = len(visit_counts)
        sum_x = sum(range(n))
        sum_y = sum(visit_counts)
        sum_xy = sum(i * v for i, v in enumerate(visit_counts))
        sum_x2 = sum(i * i for i in range(n))
        
        if n * sum_x2 - sum_x * sum_x == 0:
            slope = 0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        # Normalize slope
        slope = slope / max(statistics.mean(visit_counts), 1)
        
        trend_direction = "increasing" if slope > 0.1 else "decreasing" if slope < -0.1 else "stable"
        
        return {"trend_slope": slope, "trend_direction": trend_direction}
    
    def _estimate_seasonal_factor(self) -> float:
        """Estimate seasonal adjustment factor (simplified)"""
        current_month = datetime.now().month
        
        # Simple seasonal factors for restaurant industry
        seasonal_factors = {
            1: 0.9,   # January - post-holiday slowdown
            2: 0.95,  # February
            3: 1.0,   # March
            4: 1.05,  # April - spring season
            5: 1.1,   # May
            6: 1.15,  # June - summer increase
            7: 1.2,   # July - peak summer
            8: 1.15,  # August
            9: 1.1,   # September - back to school
            10: 1.05, # October
            11: 1.15, # November - holiday season
            12: 1.25  # December - peak holiday
        }
        
        return seasonal_factors.get(current_month, 1.0)
    
    def _estimate_external_factors(self, customer_data: Dict[str, Any]) -> float:
        """Estimate external factors affecting visit frequency"""
        factor = 1.0
        
        # Customer tier adjustment
        tier = customer_data.get('tier', 'standard')
        if tier == 'vip':
            factor *= 1.2
        elif tier == 'gold':
            factor *= 1.1
        elif tier == 'bronze':
            factor *= 0.9
        
        # Age group adjustment (if available)
        age = customer_data.get('age', 35)
        if age < 25:
            factor *= 1.1  # Young customers tend to visit more
        elif age > 60:
            factor *= 0.9   # Older customers might visit less frequently
        
        return factor
    
    def _calculate_frequency_confidence(self, 
                                      customer_data: Dict[str, Any], 
                                      historical_data: List[Dict[str, Any]], 
                                      visit_trend: Dict[str, Any]) -> float:
        """Calculate confidence in frequency prediction"""
        confidence = 0.5
        
        # Historical data volume
        visit_count = customer_data.get('visit_count', 0)
        if visit_count >= 10:
            confidence += 0.3
        elif visit_count >= 5:
            confidence += 0.2
        elif visit_count >= 2:
            confidence += 0.1
        
        # Trend consistency
        if visit_trend['trend_direction'] != 'stable':
            confidence += 0.1
        
        # Data recency
        last_visit = customer_data.get('last_visit_date')
        if last_visit:
            days_since = (datetime.now() - datetime.fromisoformat(last_visit)).days
            if days_since <= 30:
                confidence += 0.2
            elif days_since <= 60:
                confidence += 0.1
        
        return min(confidence, 0.9)
    
    def _analyze_spending_trends(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze spending trends from historical data"""
        if len(historical_data) < 2:
            return {"trend_slope": 0, "trend_direction": "stable"}
        
        # Extract spending values
        spending_data = []
        for item in historical_data:
            spending = item.get('total_spent') or item.get('amount') or item.get('order_value')
            if spending and isinstance(spending, (int, float)):
                spending_data.append(spending)
        
        if len(spending_data) < 2:
            return {"trend_slope": 0, "trend_direction": "stable"}
        
        # Calculate trend
        n = len(spending_data)
        x_values = list(range(n))
        
        sum_x = sum(x_values)
        sum_y = sum(spending_data)
        sum_xy = sum(x * y for x, y in zip(x_values, spending_data))
        sum_x2 = sum(x * x for x in x_values)
        
        if n * sum_x2 - sum_x * sum_x == 0:
            slope = 0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        # Normalize slope by average spending
        avg_spending = statistics.mean(spending_data)
        normalized_slope = slope / max(avg_spending, 1)
        
        trend_direction = "increasing" if normalized_slope > 0.05 else "decreasing" if normalized_slope < -0.05 else "stable"
        
        return {"trend_slope": normalized_slope, "trend_direction": trend_direction}
    
    def _calculate_spending_confidence(self, 
                                     customer_data: Dict[str, Any], 
                                     historical_data: List[Dict[str, Any]]) -> float:
        """Calculate confidence in spending prediction"""
        confidence = 0.5
        
        # Order history volume
        visit_count = customer_data.get('visit_count', 0)
        if visit_count >= 10:
            confidence += 0.25
        elif visit_count >= 5:
            confidence += 0.15
        elif visit_count >= 2:
            confidence += 0.1
        
        # Spending consistency
        spending_data = [item.get('total_spent', 0) for item in historical_data if item.get('total_spent')]
        if len(spending_data) >= 3:
            cv = statistics.stdev(spending_data) / statistics.mean(spending_data)
            if cv < 0.3:  # Low variability
                confidence += 0.2
            elif cv < 0.5:
                confidence += 0.1
        
        # Recent activity
        last_visit = customer_data.get('last_visit_date')
        if last_visit:
            days_since = (datetime.now() - datetime.fromisoformat(last_visit)).days
            if days_since <= 30:
                confidence += 0.15
        
        return min(confidence, 0.9)
    
    def _recommend_contact_time(self, customer_data: Dict[str, Any]) -> str:
        """Recommend best time to contact customer"""
        # Simplified recommendation based on customer profile
        preferred_language = customer_data.get('preferred_language', 'ar')
        
        if preferred_language == 'ar':
            return "Evening (7-9 PM) or after Maghrib prayer"
        else:
            return "Evening (6-8 PM) or weekend mornings"
    
    def _recommend_message_type(self, factors: Dict[str, Any]) -> str:
        """Recommend message type based on factors"""
        if factors.get('negative_sentiment'):
            return "Apology and service recovery"
        elif factors.get('high_engagement'):
            return "Appreciation and loyalty reward"
        elif factors.get('low_engagement'):
            return "Re-engagement with special offer"
        else:
            return "General check-in and menu update"