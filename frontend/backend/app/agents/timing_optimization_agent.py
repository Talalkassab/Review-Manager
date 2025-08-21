"""
Timing Optimization Agent - Determines optimal message send times
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, time
import calendar
from .base_agent import BaseRestaurantAgent
from .tools import DatabaseTool, AnalyticsTool, PredictiveModelingTool


class TimingOptimizationAgent(BaseRestaurantAgent):
    """
    Specialized agent for optimizing message timing based on customer behavior,
    cultural considerations, and response patterns.
    """
    
    def __init__(self):
        super().__init__(
            role="Timing Optimization Specialist",
            goal="Determine optimal message send times by analyzing customer behavior patterns, cultural considerations, and response rates to maximize engagement and respect cultural norms",
            backstory="""You are a timing optimization expert with deep understanding of customer behavior patterns and cultural considerations in the Middle Eastern market. 
            You excel at analyzing response patterns, identifying optimal communication windows, and respecting religious and cultural timing preferences. 
            Your expertise ensures messages are sent at times that maximize engagement while maintaining cultural sensitivity, 
            particularly regarding prayer times, meal times, and social customs.""",
            tools=[
                DatabaseTool(),
                AnalyticsTool(),
                PredictiveModelingTool()
            ],
            verbose=True,
            allow_delegation=False,
            max_iter=4
        )
        
        # Prayer times (approximate - would integrate with actual API in production)
        self.prayer_times = {
            "fajr": {"start": time(4, 30), "end": time(5, 30)},
            "dhuhr": {"start": time(12, 0), "end": time(13, 0)},
            "asr": {"start": time(15, 30), "end": time(16, 30)},
            "maghrib": {"start": time(18, 0), "end": time(19, 0)},
            "isha": {"start": time(19, 30), "end": time(20, 30)}
        }
        
        # Cultural timing preferences
        self.cultural_preferences = {
            "arabic": {
                "preferred_hours": [10, 11, 14, 15, 20, 21],  # After morning prayers, afternoon, evening
                "avoid_hours": [1, 2, 3, 4, 5, 6, 12, 13, 18, 19],  # Sleep, prayer times
                "weekend_days": [4, 5],  # Thursday-Friday weekend in Saudi
                "family_time": {"start": time(19, 0), "end": time(21, 0)},
                "work_hours": {"start": time(8, 0), "end": time(17, 0)}
            },
            "english": {
                "preferred_hours": [9, 10, 14, 15, 18, 19, 20],
                "avoid_hours": [1, 2, 3, 4, 5, 6, 7, 22, 23],
                "weekend_days": [5, 6],  # Friday-Saturday weekend
                "family_time": {"start": time(18, 0), "end": time(20, 0)},
                "work_hours": {"start": time(9, 0), "end": time(17, 0)}
            }
        }
        
        # Response pattern analysis
        self.response_patterns = {}
        
    def determine_optimal_send_time(self, 
                                   customer_data: Dict[str, Any], 
                                   message_type: str,
                                   target_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Determine the optimal time to send a message to a customer
        """
        self.log_task_start("determine_optimal_send_time", {
            "customer_id": customer_data.get("id"),
            "message_type": message_type
        })
        
        try:
            if not target_date:
                target_date = datetime.now()
            
            # Get customer preferences
            customer_preferences = self._analyze_customer_preferences(customer_data)
            
            # Get cultural constraints
            cultural_constraints = self._get_cultural_constraints(
                customer_data.get("preferred_language", "ar"),
                target_date
            )
            
            # Analyze historical response patterns
            response_patterns = self._analyze_response_patterns(customer_data)
            
            # Consider message type urgency
            urgency_factor = self._get_message_urgency_factor(message_type)
            
            # Calculate optimal time windows
            time_windows = self._calculate_optimal_windows(
                customer_preferences,
                cultural_constraints,
                response_patterns,
                urgency_factor,
                target_date
            )
            
            # Select best time
            optimal_time = self._select_best_time(time_windows, target_date)
            
            # Generate alternative times
            alternatives = self._generate_alternative_times(time_windows, optimal_time)
            
            # Calculate confidence score
            confidence = self._calculate_timing_confidence(
                customer_data, response_patterns, cultural_constraints
            )
            
            result = {
                "optimal_send_time": optimal_time.isoformat(),
                "confidence_score": confidence,
                "alternative_times": [alt.isoformat() for alt in alternatives],
                "reasoning": self._generate_timing_reasoning(
                    optimal_time, customer_preferences, cultural_constraints, response_patterns
                ),
                "cultural_considerations": cultural_constraints,
                "customer_preferences": customer_preferences,
                "urgency_factor": urgency_factor,
                "is_respectful_timing": self._validate_respectful_timing(optimal_time, customer_data)
            }
            
            self.log_task_complete("determine_optimal_send_time", result)
            return result
            
        except Exception as e:
            self.log_task_error("determine_optimal_send_time", e)
            raise
            
    def optimize_campaign_schedule(self, 
                                  campaign_data: Dict[str, Any],
                                  target_customers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Optimize message scheduling for an entire campaign
        """
        self.log_task_start("optimize_campaign_schedule", {
            "campaign_type": campaign_data.get("type"),
            "target_count": len(target_customers)
        })
        
        try:
            campaign_schedule = {}
            scheduling_insights = {
                "total_customers": len(target_customers),
                "time_distribution": {},
                "cultural_considerations": {},
                "rate_limiting": {}
            }
            
            # Group customers by time zones and preferences
            customer_groups = self._group_customers_by_timing_preferences(target_customers)
            
            # Calculate send windows for each group
            for group_name, customers in customer_groups.items():
                group_schedule = self._optimize_group_schedule(
                    customers, campaign_data, group_name
                )
                campaign_schedule[group_name] = group_schedule
                
            # Apply rate limiting
            final_schedule = self._apply_rate_limiting(campaign_schedule, campaign_data)
            
            # Calculate delivery timeline
            delivery_timeline = self._calculate_delivery_timeline(final_schedule)
            
            # Generate scheduling insights
            insights = self._generate_scheduling_insights(final_schedule, target_customers)
            
            result = {
                "campaign_schedule": final_schedule,
                "delivery_timeline": delivery_timeline,
                "scheduling_insights": insights,
                "estimated_completion_time": delivery_timeline["end_time"],
                "total_send_windows": len(final_schedule),
                "rate_limit_compliance": True
            }
            
            self.log_task_complete("optimize_campaign_schedule", result)
            return result
            
        except Exception as e:
            self.log_task_error("optimize_campaign_schedule", e)
            raise
            
    def analyze_response_timing_patterns(self, 
                                       customer_id: str,
                                       historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze when customers typically respond to messages
        """
        self.log_task_start("analyze_response_timing_patterns", {
            "customer_id": customer_id
        })
        
        try:
            if not historical_data:
                return {"error": "No historical data available"}
            
            # Extract response times
            response_times = self._extract_response_times(historical_data)
            
            if not response_times:
                return {"error": "No response time data found"}
            
            # Analyze patterns
            patterns = {
                "hourly_distribution": self._analyze_hourly_distribution(response_times),
                "daily_distribution": self._analyze_daily_distribution(response_times),
                "response_speed": self._analyze_response_speed(response_times),
                "consistency_score": self._calculate_consistency_score(response_times),
                "preferred_timeframes": self._identify_preferred_timeframes(response_times)
            }
            
            # Generate insights
            insights = self._generate_response_insights(patterns)
            
            # Predict future response likelihood
            predictions = self._predict_response_likelihood(patterns, customer_id)
            
            result = {
                "customer_id": customer_id,
                "response_patterns": patterns,
                "insights": insights,
                "predictions": predictions,
                "data_points_analyzed": len(response_times),
                "analysis_reliability": self._assess_analysis_reliability(response_times)
            }
            
            self.log_task_complete("analyze_response_timing_patterns", result)
            return result
            
        except Exception as e:
            self.log_task_error("analyze_response_timing_patterns", e)
            raise
            
    def respect_cultural_timing(self, 
                               send_time: datetime,
                               customer_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and adjust send time for cultural appropriateness
        """
        self.log_task_start("respect_cultural_timing")
        
        try:
            language = customer_profile.get("preferred_language", "ar")
            adjustments_made = []
            original_time = send_time
            
            # Check prayer times
            prayer_adjustment = self._check_prayer_times(send_time, language)
            if prayer_adjustment["needs_adjustment"]:
                send_time = prayer_adjustment["suggested_time"]
                adjustments_made.append(prayer_adjustment["reason"])
            
            # Check meal times
            meal_adjustment = self._check_meal_times(send_time, language)
            if meal_adjustment["needs_adjustment"]:
                send_time = meal_adjustment["suggested_time"]
                adjustments_made.append(meal_adjustment["reason"])
            
            # Check sleep hours
            sleep_adjustment = self._check_sleep_hours(send_time, language)
            if sleep_adjustment["needs_adjustment"]:
                send_time = sleep_adjustment["suggested_time"]
                adjustments_made.append(sleep_adjustment["reason"])
            
            # Check special occasions/holidays
            holiday_adjustment = self._check_holiday_timing(send_time, customer_profile)
            if holiday_adjustment["needs_adjustment"]:
                send_time = holiday_adjustment["suggested_time"]
                adjustments_made.append(holiday_adjustment["reason"])
            
            # Check family time
            family_adjustment = self._check_family_time(send_time, language)
            if family_adjustment["needs_adjustment"]:
                send_time = family_adjustment["suggested_time"]
                adjustments_made.append(family_adjustment["reason"])
            
            result = {
                "original_time": original_time.isoformat(),
                "adjusted_time": send_time.isoformat(),
                "time_changed": send_time != original_time,
                "adjustments_made": adjustments_made,
                "cultural_score": self._calculate_cultural_appropriateness_score(
                    send_time, customer_profile
                ),
                "is_culturally_appropriate": len(adjustments_made) == 0
            }
            
            self.log_task_complete("respect_cultural_timing", result)
            return result
            
        except Exception as e:
            self.log_task_error("respect_cultural_timing", e)
            raise
            
    def predict_engagement_by_time(self, 
                                  customer_data: Dict[str, Any],
                                  time_options: List[datetime]) -> Dict[str, Any]:
        """
        Predict engagement rates for different send times
        """
        self.log_task_start("predict_engagement_by_time")
        
        try:
            predictions = []
            
            for send_time in time_options:
                # Calculate engagement score for this time
                engagement_score = self._calculate_engagement_score(
                    send_time, customer_data
                )
                
                # Consider cultural factors
                cultural_score = self._calculate_cultural_appropriateness_score(
                    send_time, customer_data
                )
                
                # Consider customer behavior patterns
                behavior_score = self._calculate_behavior_alignment_score(
                    send_time, customer_data
                )
                
                # Combine scores
                combined_score = (
                    engagement_score * 0.4 +
                    cultural_score * 0.3 +
                    behavior_score * 0.3
                )
                
                predictions.append({
                    "send_time": send_time.isoformat(),
                    "engagement_score": engagement_score,
                    "cultural_score": cultural_score,
                    "behavior_score": behavior_score,
                    "combined_score": combined_score,
                    "predicted_response_rate": self._score_to_response_rate(combined_score),
                    "confidence": self._calculate_prediction_confidence(customer_data)
                })
            
            # Sort by combined score
            predictions.sort(key=lambda x: x["combined_score"], reverse=True)
            
            # Generate recommendations
            recommendations = self._generate_timing_recommendations(predictions)
            
            result = {
                "predictions": predictions,
                "best_time": predictions[0]["send_time"] if predictions else None,
                "worst_time": predictions[-1]["send_time"] if predictions else None,
                "recommendations": recommendations,
                "analysis_confidence": self._calculate_analysis_confidence(customer_data)
            }
            
            self.log_task_complete("predict_engagement_by_time", result)
            return result
            
        except Exception as e:
            self.log_task_error("predict_engagement_by_time", e)
            raise
            
    # Private helper methods
    def _analyze_customer_preferences(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze customer's timing preferences from historical data"""
        preferences = {
            "preferred_hours": [],
            "avoid_hours": [],
            "preferred_days": [],
            "response_speed": "medium",
            "timezone": "Asia/Riyadh"
        }
        
        # Analyze message history for response patterns
        message_history = customer_data.get("message_history", [])
        
        if message_history:
            response_hours = []
            response_days = []
            
            for message in message_history:
                if message.get("direction") == "inbound" and "timestamp" in message:
                    try:
                        timestamp = datetime.fromisoformat(message["timestamp"])
                        response_hours.append(timestamp.hour)
                        response_days.append(timestamp.weekday())
                    except:
                        continue
            
            if response_hours:
                # Find most common response hours
                hour_counts = {}
                for hour in response_hours:
                    hour_counts[hour] = hour_counts.get(hour, 0) + 1
                
                sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
                preferences["preferred_hours"] = [hour for hour, count in sorted_hours[:6]]
                
                # Hours with no responses are avoided
                all_hours = set(range(24))
                responded_hours = set(response_hours)
                preferences["avoid_hours"] = list(all_hours - responded_hours)
            
            if response_days:
                # Find most common response days
                day_counts = {}
                for day in response_days:
                    day_counts[day] = day_counts.get(day, 0) + 1
                
                sorted_days = sorted(day_counts.items(), key=lambda x: x[1], reverse=True)
                preferences["preferred_days"] = [day for day, count in sorted_days[:4]]
        
        return preferences
        
    def _get_cultural_constraints(self, language: str, target_date: datetime) -> Dict[str, Any]:
        """Get cultural timing constraints"""
        lang_key = "arabic" if language in ["ar", "arabic"] else "english"
        base_constraints = self.cultural_preferences[lang_key].copy()
        
        # Add date-specific constraints
        constraints = {
            **base_constraints,
            "prayer_times": self._get_prayer_times_for_date(target_date),
            "is_friday": target_date.weekday() == 4 and lang_key == "arabic",
            "is_weekend": target_date.weekday() in base_constraints["weekend_days"],
            "special_occasions": self._check_special_occasions(target_date, language)
        }
        
        return constraints
        
    def _analyze_response_patterns(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze customer's response patterns"""
        message_history = customer_data.get("message_history", [])
        
        patterns = {
            "average_response_time_hours": 24,
            "response_rate": 0.5,
            "best_hours": [],
            "worst_hours": [],
            "consistency": "low"
        }
        
        if message_history:
            response_times = []
            
            for i in range(1, len(message_history)):
                prev_msg = message_history[i-1]
                curr_msg = message_history[i]
                
                if (prev_msg.get("direction") == "outbound" and 
                    curr_msg.get("direction") == "inbound"):
                    
                    try:
                        sent_time = datetime.fromisoformat(prev_msg["timestamp"])
                        response_time = datetime.fromisoformat(curr_msg["timestamp"])
                        hours_diff = (response_time - sent_time).total_seconds() / 3600
                        
                        response_times.append({
                            "hours": hours_diff,
                            "sent_hour": sent_time.hour,
                            "response_hour": response_time.hour
                        })
                    except:
                        continue
            
            if response_times:
                patterns["average_response_time_hours"] = sum(r["hours"] for r in response_times) / len(response_times)
                
                # Calculate response rate
                total_sent = len([m for m in message_history if m.get("direction") == "outbound"])
                patterns["response_rate"] = len(response_times) / max(total_sent, 1)
                
                # Find best/worst hours
                hour_performance = {}
                for rt in response_times:
                    hour = rt["sent_hour"]
                    if hour not in hour_performance:
                        hour_performance[hour] = {"responses": 0, "total_sent": 0, "avg_time": 0}
                    hour_performance[hour]["responses"] += 1
                    hour_performance[hour]["avg_time"] += rt["hours"]
                
                # Calculate performance scores
                for hour, data in hour_performance.items():
                    data["avg_time"] /= data["responses"]
                    data["response_rate"] = data["responses"] / data.get("total_sent", 1)
                
                # Sort hours by performance
                sorted_hours = sorted(
                    hour_performance.items(),
                    key=lambda x: x[1]["response_rate"] * (24 - x[1]["avg_time"]),  # Higher response rate, lower response time
                    reverse=True
                )
                
                patterns["best_hours"] = [hour for hour, _ in sorted_hours[:6]]
                patterns["worst_hours"] = [hour for hour, _ in sorted_hours[-6:]]
        
        return patterns
        
    def _get_message_urgency_factor(self, message_type: str) -> float:
        """Get urgency factor for message type"""
        urgency_factors = {
            "complaint_response": 1.0,  # Immediate
            "reservation_confirmation": 0.8,  # High
            "feedback_request": 0.5,  # Medium
            "promotional": 0.3,  # Low
            "birthday_greeting": 0.4,  # Medium-low
            "general_update": 0.2  # Very low
        }
        
        return urgency_factors.get(message_type, 0.5)
        
    def _calculate_optimal_windows(self, 
                                  customer_prefs: Dict[str, Any],
                                  cultural_constraints: Dict[str, Any],
                                  response_patterns: Dict[str, Any],
                                  urgency_factor: float,
                                  target_date: datetime) -> List[Dict[str, Any]]:
        """Calculate optimal time windows"""
        windows = []
        
        # Start with customer's preferred hours
        preferred_hours = customer_prefs.get("preferred_hours", [])
        if not preferred_hours:
            preferred_hours = cultural_constraints.get("preferred_hours", [10, 14, 20])
        
        # Filter by cultural constraints
        cultural_avoid = cultural_constraints.get("avoid_hours", [])
        filtered_hours = [h for h in preferred_hours if h not in cultural_avoid]
        
        # Add response pattern influence
        best_response_hours = response_patterns.get("best_hours", [])
        
        # Combine and score hours
        all_candidate_hours = set(filtered_hours + best_response_hours)
        
        for hour in all_candidate_hours:
            if hour in cultural_avoid:
                continue
                
            # Calculate window score
            score = 0.0
            
            # Customer preference score
            if hour in preferred_hours:
                score += 0.4
                
            # Response pattern score
            if hour in best_response_hours:
                score += 0.3
                
            # Cultural appropriateness score
            if hour not in cultural_constraints.get("avoid_hours", []):
                score += 0.2
                
            # Urgency adjustment
            if urgency_factor > 0.7:  # High urgency
                # Allow earlier/later hours for urgent messages
                if hour in [8, 9, 21, 22]:
                    score += 0.1
                    
            # Create time window
            window_start = target_date.replace(hour=hour, minute=0, second=0, microsecond=0)
            window_end = window_start + timedelta(hours=1)
            
            windows.append({
                "start": window_start,
                "end": window_end,
                "score": score,
                "hour": hour,
                "reasoning": f"Score {score:.2f}: customer pref + response pattern + cultural fit"
            })
        
        # Sort by score
        windows.sort(key=lambda x: x["score"], reverse=True)
        
        return windows[:5]  # Return top 5 windows
        
    def _select_best_time(self, windows: List[Dict[str, Any]], target_date: datetime) -> datetime:
        """Select the best time from available windows"""
        if not windows:
            # Fallback to safe default time
            return target_date.replace(hour=14, minute=0, second=0, microsecond=0)
        
        best_window = windows[0]
        
        # Select specific minute within the hour window
        # Prefer 0, 15, 30, 45 minutes for cleaner scheduling
        preferred_minutes = [0, 15, 30, 45]
        selected_minute = preferred_minutes[0]  # Default to top of hour
        
        optimal_time = best_window["start"].replace(minute=selected_minute)
        
        return optimal_time
        
    def _generate_alternative_times(self, windows: List[Dict[str, Any]], optimal_time: datetime) -> List[datetime]:
        """Generate alternative send times"""
        alternatives = []
        
        # Use other high-scoring windows
        for window in windows[1:4]:  # Skip the optimal (first) window
            alt_time = window["start"].replace(minute=0)
            if alt_time != optimal_time:
                alternatives.append(alt_time)
        
        # If we don't have enough alternatives, generate some
        if len(alternatives) < 3:
            base_time = optimal_time
            additional_alts = [
                base_time + timedelta(hours=2),
                base_time + timedelta(hours=4),
                base_time + timedelta(hours=6)
            ]
            
            for alt in additional_alts:
                if alt not in alternatives and len(alternatives) < 3:
                    alternatives.append(alt)
        
        return alternatives[:3]
        
    def _calculate_timing_confidence(self, 
                                   customer_data: Dict[str, Any],
                                   response_patterns: Dict[str, Any],
                                   cultural_constraints: Dict[str, Any]) -> float:
        """Calculate confidence in timing recommendation"""
        confidence = 0.5  # Base confidence
        
        # Data availability
        message_count = len(customer_data.get("message_history", []))
        if message_count >= 10:
            confidence += 0.3
        elif message_count >= 5:
            confidence += 0.2
        elif message_count >= 2:
            confidence += 0.1
        
        # Response rate
        response_rate = response_patterns.get("response_rate", 0)
        if response_rate >= 0.7:
            confidence += 0.2
        elif response_rate >= 0.5:
            confidence += 0.1
        
        # Pattern consistency
        if len(response_patterns.get("best_hours", [])) >= 3:
            confidence += 0.1
        
        return min(confidence, 0.95)
        
    def _generate_timing_reasoning(self, 
                                  optimal_time: datetime,
                                  customer_prefs: Dict[str, Any],
                                  cultural_constraints: Dict[str, Any],
                                  response_patterns: Dict[str, Any]) -> str:
        """Generate human-readable reasoning for timing choice"""
        reasons = []
        
        hour = optimal_time.hour
        
        if hour in customer_prefs.get("preferred_hours", []):
            reasons.append(f"Customer typically responds at {hour}:00")
        
        if hour in response_patterns.get("best_hours", []):
            reasons.append(f"Highest response rate at {hour}:00 based on history")
        
        if hour in cultural_constraints.get("preferred_hours", []):
            reasons.append(f"Culturally appropriate time ({hour}:00)")
        
        # Prayer time consideration
        prayer_status = self._check_prayer_time_status(optimal_time)
        if not prayer_status["is_prayer_time"]:
            reasons.append("Avoids prayer times")
        
        if not reasons:
            reasons.append("Selected based on general best practices")
        
        return ". ".join(reasons) + "."
        
    def _validate_respectful_timing(self, send_time: datetime, customer_data: Dict[str, Any]) -> bool:
        """Validate if timing is culturally respectful"""
        language = customer_data.get("preferred_language", "ar")
        
        # Check prayer times
        if self._is_prayer_time(send_time):
            return False
        
        # Check sleep hours
        if self._is_sleep_time(send_time, language):
            return False
        
        # Check family time (if applicable)
        if self._is_family_time(send_time, language):
            return False
        
        return True
        
    def _group_customers_by_timing_preferences(self, customers: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group customers by timing preferences for batch optimization"""
        groups = {
            "morning_arabic": [],
            "afternoon_arabic": [],
            "evening_arabic": [],
            "morning_english": [],
            "afternoon_english": [],
            "evening_english": [],
            "high_priority": []
        }
        
        for customer in customers:
            language = customer.get("preferred_language", "ar")
            tier = customer.get("tier", "standard")
            
            # High priority customers get special treatment
            if tier in ["vip", "gold"]:
                groups["high_priority"].append(customer)
                continue
            
            # Analyze preferred hours
            preferred_hours = self._get_customer_preferred_hours(customer)
            
            if not preferred_hours:
                # Default grouping by language
                if language in ["ar", "arabic"]:
                    groups["afternoon_arabic"].append(customer)
                else:
                    groups["afternoon_english"].append(customer)
                continue
            
            # Categorize by preferred time slots
            avg_hour = sum(preferred_hours) / len(preferred_hours)
            
            lang_suffix = "arabic" if language in ["ar", "arabic"] else "english"
            
            if avg_hour < 12:
                groups[f"morning_{lang_suffix}"].append(customer)
            elif avg_hour < 17:
                groups[f"afternoon_{lang_suffix}"].append(customer)
            else:
                groups[f"evening_{lang_suffix}"].append(customer)
        
        # Remove empty groups
        return {k: v for k, v in groups.items() if v}
        
    def _optimize_group_schedule(self, 
                                customers: List[Dict[str, Any]], 
                                campaign_data: Dict[str, Any],
                                group_name: str) -> Dict[str, Any]:
        """Optimize schedule for a group of customers"""
        group_schedule = {
            "group_name": group_name,
            "customer_count": len(customers),
            "send_times": [],
            "time_windows": []
        }
        
        # Determine optimal time range for this group
        if "morning" in group_name:
            base_hours = [9, 10, 11]
        elif "afternoon" in group_name:
            base_hours = [14, 15, 16]
        elif "evening" in group_name:
            base_hours = [19, 20, 21]
        elif "high_priority" in group_name:
            base_hours = [10, 14, 20]  # Multiple windows for VIPs
        else:
            base_hours = [14, 15]  # Default afternoon
        
        # Apply cultural filters
        language = "ar" if "arabic" in group_name else "en"
        cultural_constraints = self._get_cultural_constraints(language, datetime.now())
        
        filtered_hours = [h for h in base_hours if h not in cultural_constraints.get("avoid_hours", [])]
        
        # Distribute customers across available hours
        if filtered_hours:
            customers_per_hour = len(customers) // len(filtered_hours)
            remainder = len(customers) % len(filtered_hours)
            
            customer_index = 0
            for i, hour in enumerate(filtered_hours):
                customers_in_this_hour = customers_per_hour + (1 if i < remainder else 0)
                
                for j in range(customers_in_this_hour):
                    if customer_index < len(customers):
                        # Spread within the hour
                        minute = j * (60 // max(customers_in_this_hour, 1))
                        send_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
                        
                        group_schedule["send_times"].append({
                            "customer_id": customers[customer_index]["id"],
                            "send_time": send_time.isoformat(),
                            "hour": hour,
                            "minute": minute
                        })
                        
                        customer_index += 1
        
        return group_schedule
        
    def _apply_rate_limiting(self, 
                           campaign_schedule: Dict[str, Any], 
                           campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply rate limiting to campaign schedule"""
        # WhatsApp Business API limits (simplified)
        messages_per_minute = 20
        messages_per_hour = 1000
        
        rate_limited_schedule = {}
        
        # Collect all send times
        all_sends = []
        for group_name, group_data in campaign_schedule.items():
            for send_info in group_data.get("send_times", []):
                all_sends.append({
                    "customer_id": send_info["customer_id"],
                    "original_time": datetime.fromisoformat(send_info["send_time"]),
                    "group": group_name
                })
        
        # Sort by original time
        all_sends.sort(key=lambda x: x["original_time"])
        
        # Apply rate limiting
        adjusted_sends = []
        current_time = all_sends[0]["original_time"] if all_sends else datetime.now()
        
        for i, send in enumerate(all_sends):
            # Ensure minimum gap between messages
            min_gap = timedelta(seconds=60 // messages_per_minute)  # 3 seconds for 20/min
            
            if i > 0:
                time_since_last = current_time - adjusted_sends[-1]["adjusted_time"]
                if time_since_last < min_gap:
                    current_time = adjusted_sends[-1]["adjusted_time"] + min_gap
            else:
                current_time = send["original_time"]
            
            adjusted_sends.append({
                **send,
                "adjusted_time": current_time
            })
        
        # Reorganize into groups
        for send in adjusted_sends:
            group_name = send["group"]
            if group_name not in rate_limited_schedule:
                rate_limited_schedule[group_name] = {
                    "group_name": group_name,
                    "send_times": []
                }
            
            rate_limited_schedule[group_name]["send_times"].append({
                "customer_id": send["customer_id"],
                "send_time": send["adjusted_time"].isoformat(),
                "original_time": send["original_time"].isoformat(),
                "delayed": send["adjusted_time"] != send["original_time"]
            })
        
        return rate_limited_schedule
        
    def _calculate_delivery_timeline(self, schedule: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate campaign delivery timeline"""
        all_send_times = []
        
        for group_data in schedule.values():
            for send_info in group_data.get("send_times", []):
                send_time = datetime.fromisoformat(send_info["send_time"])
                all_send_times.append(send_time)
        
        if not all_send_times:
            return {"start_time": None, "end_time": None, "duration_hours": 0}
        
        start_time = min(all_send_times)
        end_time = max(all_send_times)
        duration = (end_time - start_time).total_seconds() / 3600  # Hours
        
        return {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_hours": round(duration, 2),
            "total_messages": len(all_send_times)
        }
        
    def _generate_scheduling_insights(self, 
                                    schedule: Dict[str, Any], 
                                    customers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate insights about the scheduling"""
        insights = {
            "group_distribution": {},
            "time_distribution": {},
            "cultural_considerations": {},
            "optimization_summary": {}
        }
        
        # Group distribution
        for group_name, group_data in schedule.items():
            insights["group_distribution"][group_name] = len(group_data.get("send_times", []))
        
        # Time distribution
        hour_distribution = {}
        for group_data in schedule.values():
            for send_info in group_data.get("send_times", []):
                send_time = datetime.fromisoformat(send_info["send_time"])
                hour = send_time.hour
                hour_distribution[hour] = hour_distribution.get(hour, 0) + 1
        
        insights["time_distribution"] = hour_distribution
        
        # Cultural considerations
        arabic_customers = sum(1 for c in customers if c.get("preferred_language") == "ar")
        english_customers = len(customers) - arabic_customers
        
        insights["cultural_considerations"] = {
            "arabic_customers": arabic_customers,
            "english_customers": english_customers,
            "prayer_time_avoided": True,  # Simplified
            "family_time_respected": True  # Simplified
        }
        
        return insights
        
    # Additional helper methods for cultural timing
    def _is_prayer_time(self, check_time: datetime) -> bool:
        """Check if time falls during prayer hours"""
        current_time = check_time.time()
        
        for prayer, times in self.prayer_times.items():
            if times["start"] <= current_time <= times["end"]:
                return True
        return False
        
    def _is_sleep_time(self, check_time: datetime, language: str) -> bool:
        """Check if time falls during typical sleep hours"""
        hour = check_time.hour
        sleep_hours = [1, 2, 3, 4, 5, 6] if language in ["ar", "arabic"] else [1, 2, 3, 4, 5, 6, 7]
        return hour in sleep_hours
        
    def _is_family_time(self, check_time: datetime, language: str) -> bool:
        """Check if time falls during family time"""
        current_time = check_time.time()
        lang_key = "arabic" if language in ["ar", "arabic"] else "english"
        family_time = self.cultural_preferences[lang_key]["family_time"]
        
        return family_time["start"] <= current_time <= family_time["end"]
        
    def _check_prayer_times(self, send_time: datetime, language: str) -> Dict[str, Any]:
        """Check and adjust for prayer times"""
        if language not in ["ar", "arabic"]:
            return {"needs_adjustment": False, "suggested_time": send_time, "reason": ""}
        
        if self._is_prayer_time(send_time):
            # Find next suitable time after prayer
            adjusted_time = send_time
            for _ in range(24):  # Safety limit
                adjusted_time += timedelta(minutes=30)
                if not self._is_prayer_time(adjusted_time):
                    break
            
            return {
                "needs_adjustment": True,
                "suggested_time": adjusted_time,
                "reason": "Adjusted to avoid prayer time"
            }
        
        return {"needs_adjustment": False, "suggested_time": send_time, "reason": ""}
        
    def _check_meal_times(self, send_time: datetime, language: str) -> Dict[str, Any]:
        """Check and adjust for meal times"""
        hour = send_time.hour
        
        # Universal meal times to avoid
        meal_hours = [13, 14] if language in ["ar", "arabic"] else [12, 13]  # Lunch time
        
        if hour in meal_hours:
            adjusted_time = send_time.replace(hour=15)  # After lunch
            return {
                "needs_adjustment": True,
                "suggested_time": adjusted_time,
                "reason": "Adjusted to avoid meal time"
            }
        
        return {"needs_adjustment": False, "suggested_time": send_time, "reason": ""}
        
    def _check_sleep_hours(self, send_time: datetime, language: str) -> Dict[str, Any]:
        """Check and adjust for sleep hours"""
        if self._is_sleep_time(send_time, language):
            # Adjust to morning time
            adjusted_time = send_time.replace(hour=9, minute=0)
            return {
                "needs_adjustment": True,
                "suggested_time": adjusted_time,
                "reason": "Adjusted from sleep hours to morning"
            }
        
        return {"needs_adjustment": False, "suggested_time": send_time, "reason": ""}
        
    def _check_holiday_timing(self, send_time: datetime, customer_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Check for holidays and special occasions"""
        # Simplified implementation - would integrate with calendar API
        return {"needs_adjustment": False, "suggested_time": send_time, "reason": ""}
        
    def _check_family_time(self, send_time: datetime, language: str) -> Dict[str, Any]:
        """Check and adjust for family time"""
        if self._is_family_time(send_time, language):
            # Adjust to before or after family time
            adjusted_time = send_time.replace(hour=17)  # Before family time
            return {
                "needs_adjustment": True,
                "suggested_time": adjusted_time,
                "reason": "Adjusted to respect family time"
            }
        
        return {"needs_adjustment": False, "suggested_time": send_time, "reason": ""}
        
    def _calculate_cultural_appropriateness_score(self, send_time: datetime, customer_profile: Dict[str, Any]) -> float:
        """Calculate cultural appropriateness score"""
        score = 1.0
        language = customer_profile.get("preferred_language", "ar")
        
        # Deduct for inappropriate times
        if self._is_prayer_time(send_time):
            score -= 0.5
        if self._is_sleep_time(send_time, language):
            score -= 0.4
        if self._is_family_time(send_time, language):
            score -= 0.2
            
        return max(0.0, score)
        
    def _extract_response_times(self, historical_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract response times from historical data"""
        response_times = []
        
        for i in range(1, len(historical_data)):
            prev_msg = historical_data[i-1]
            curr_msg = historical_data[i]
            
            if (prev_msg.get("direction") == "outbound" and 
                curr_msg.get("direction") == "inbound"):
                
                try:
                    sent_time = datetime.fromisoformat(prev_msg["timestamp"])
                    response_time = datetime.fromisoformat(curr_msg["timestamp"])
                    
                    response_times.append({
                        "sent_time": sent_time,
                        "response_time": response_time,
                        "response_hours": (response_time - sent_time).total_seconds() / 3600,
                        "sent_hour": sent_time.hour,
                        "response_hour": response_time.hour,
                        "sent_day": sent_time.weekday(),
                        "response_day": response_time.weekday()
                    })
                except:
                    continue
        
        return response_times
        
    def _analyze_hourly_distribution(self, response_times: List[Dict[str, Any]]) -> Dict[int, int]:
        """Analyze hourly distribution of responses"""
        distribution = {}
        
        for rt in response_times:
            hour = rt["response_hour"]
            distribution[hour] = distribution.get(hour, 0) + 1
        
        return distribution
        
    def _analyze_daily_distribution(self, response_times: List[Dict[str, Any]]) -> Dict[int, int]:
        """Analyze daily distribution of responses"""
        distribution = {}
        
        for rt in response_times:
            day = rt["response_day"]
            distribution[day] = distribution.get(day, 0) + 1
        
        return distribution
        
    def _analyze_response_speed(self, response_times: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze response speed patterns"""
        if not response_times:
            return {"average_hours": 24, "median_hours": 24, "fastest_hours": 24}
        
        hours = [rt["response_hours"] for rt in response_times]
        hours.sort()
        
        return {
            "average_hours": sum(hours) / len(hours),
            "median_hours": hours[len(hours) // 2],
            "fastest_hours": hours[0],
            "slowest_hours": hours[-1]
        }
        
    def _calculate_consistency_score(self, response_times: List[Dict[str, Any]]) -> float:
        """Calculate consistency score for response patterns"""
        if len(response_times) < 2:
            return 0.0
        
        # Check consistency in response hours
        response_hours = [rt["response_hour"] for rt in response_times]
        unique_hours = len(set(response_hours))
        
        # More consistent = fewer unique hours
        consistency = 1.0 - (unique_hours / 24)
        
        return max(0.0, consistency)
        
    def _identify_preferred_timeframes(self, response_times: List[Dict[str, Any]]) -> List[str]:
        """Identify preferred response timeframes"""
        timeframes = {
            "morning": 0,    # 6-12
            "afternoon": 0,  # 12-17
            "evening": 0,    # 17-22
            "night": 0       # 22-6
        }
        
        for rt in response_times:
            hour = rt["response_hour"]
            if 6 <= hour < 12:
                timeframes["morning"] += 1
            elif 12 <= hour < 17:
                timeframes["afternoon"] += 1
            elif 17 <= hour < 22:
                timeframes["evening"] += 1
            else:
                timeframes["night"] += 1
        
        # Return timeframes with significant activity (>20% of responses)
        total_responses = len(response_times)
        threshold = total_responses * 0.2
        
        preferred = [timeframe for timeframe, count in timeframes.items() if count > threshold]
        
        return preferred if preferred else ["afternoon"]  # Default
        
    def _get_customer_preferred_hours(self, customer: Dict[str, Any]) -> List[int]:
        """Get customer's preferred hours from their data"""
        # This would analyze the customer's message history
        # Simplified implementation returns default based on language
        language = customer.get("preferred_language", "ar")
        
        if language in ["ar", "arabic"]:
            return [10, 14, 20]  # Morning, afternoon, evening
        else:
            return [9, 15, 19]   # Slightly different for English speakers
            
    def _get_prayer_times_for_date(self, date: datetime) -> Dict[str, Dict[str, str]]:
        """Get prayer times for specific date (simplified implementation)"""
        # In production, this would call a prayer times API
        return {
            prayer: {
                "start": times["start"].strftime("%H:%M"),
                "end": times["end"].strftime("%H:%M")
            }
            for prayer, times in self.prayer_times.items()
        }
        
    def _check_special_occasions(self, date: datetime, language: str) -> List[str]:
        """Check for special occasions on the date"""
        occasions = []
        
        # Simplified check for common occasions
        if date.weekday() == 4 and language in ["ar", "arabic"]:  # Friday
            occasions.append("Friday prayers")
            
        # Would add more sophisticated holiday detection here
        
        return occasions
        
    def _check_prayer_time_status(self, check_time: datetime) -> Dict[str, Any]:
        """Check prayer time status for a given time"""
        current_time = check_time.time()
        
        for prayer_name, times in self.prayer_times.items():
            if times["start"] <= current_time <= times["end"]:
                return {
                    "is_prayer_time": True,
                    "prayer_name": prayer_name,
                    "start": times["start"].strftime("%H:%M"),
                    "end": times["end"].strftime("%H:%M")
                }
        
        return {"is_prayer_time": False}
        
    def _calculate_engagement_score(self, send_time: datetime, customer_data: Dict[str, Any]) -> float:
        """Calculate predicted engagement score for send time"""
        # Simplified engagement calculation
        score = 0.5  # Base score
        
        hour = send_time.hour
        
        # Historical response patterns
        message_history = customer_data.get("message_history", [])
        if message_history:
            response_hours = []
            for msg in message_history:
                if msg.get("direction") == "inbound" and "timestamp" in msg:
                    try:
                        timestamp = datetime.fromisoformat(msg["timestamp"])
                        response_hours.append(timestamp.hour)
                    except:
                        continue
            
            if response_hours and hour in response_hours:
                score += 0.3  # Boost if customer has responded at this hour before
        
        # Time-based factors
        if 9 <= hour <= 11 or 14 <= hour <= 16 or 19 <= hour <= 21:
            score += 0.2  # Generally good hours
        
        return min(score, 1.0)
        
    def _calculate_behavior_alignment_score(self, send_time: datetime, customer_data: Dict[str, Any]) -> float:
        """Calculate how well the time aligns with customer behavior"""
        # Simplified behavior alignment
        score = 0.5
        
        # Customer tier consideration
        tier = customer_data.get("tier", "standard")
        if tier in ["vip", "gold"]:
            score += 0.2  # VIP customers get priority timing
        
        # Visit patterns (if available)
        visit_count = customer_data.get("visit_count", 0)
        if visit_count >= 10:
            score += 0.1  # Loyal customers
        
        return min(score, 1.0)
        
    def _score_to_response_rate(self, score: float) -> float:
        """Convert combined score to predicted response rate"""
        # Sigmoid-like conversion
        base_rate = 0.3  # Base response rate
        max_boost = 0.4  # Maximum additional response rate
        
        predicted_rate = base_rate + (max_boost * score)
        return min(predicted_rate, 0.8)  # Cap at 80% response rate
        
    def _calculate_prediction_confidence(self, customer_data: Dict[str, Any]) -> float:
        """Calculate confidence in predictions"""
        confidence = 0.5
        
        # Data availability
        message_count = len(customer_data.get("message_history", []))
        if message_count >= 10:
            confidence += 0.3
        elif message_count >= 5:
            confidence += 0.2
        elif message_count >= 2:
            confidence += 0.1
        
        # Customer maturity
        visit_count = customer_data.get("visit_count", 0)
        if visit_count >= 5:
            confidence += 0.1
        
        return min(confidence, 0.9)
        
    def _generate_timing_recommendations(self, predictions: List[Dict[str, Any]]) -> List[str]:
        """Generate timing recommendations based on predictions"""
        recommendations = []
        
        if not predictions:
            return ["No timing data available"]
        
        best_prediction = predictions[0]
        worst_prediction = predictions[-1]
        
        best_time = datetime.fromisoformat(best_prediction["send_time"])
        worst_time = datetime.fromisoformat(worst_prediction["send_time"])
        
        recommendations.append(f"Best time: {best_time.strftime('%H:%M')} (predicted {best_prediction['predicted_response_rate']:.1%} response rate)")
        recommendations.append(f"Avoid: {worst_time.strftime('%H:%M')} (predicted {worst_prediction['predicted_response_rate']:.1%} response rate)")
        
        # Cultural recommendations
        if any(pred["cultural_score"] < 0.7 for pred in predictions):
            recommendations.append("Consider cultural timing constraints for better engagement")
        
        return recommendations
        
    def _calculate_analysis_confidence(self, customer_data: Dict[str, Any]) -> float:
        """Calculate overall analysis confidence"""
        confidence = 0.5
        
        # Data quality factors
        data_completeness = len([v for v in customer_data.values() if v]) / len(customer_data)
        confidence += data_completeness * 0.3
        
        # Interaction history
        message_count = len(customer_data.get("message_history", []))
        if message_count >= 20:
            confidence += 0.2
        elif message_count >= 10:
            confidence += 0.1
        
        return min(confidence, 0.95)
        
    def _generate_response_insights(self, patterns: Dict[str, Any]) -> List[str]:
        """Generate insights from response patterns"""
        insights = []
        
        # Hourly insights
        hourly_dist = patterns.get("hourly_distribution", {})
        if hourly_dist:
            most_active_hour = max(hourly_dist.items(), key=lambda x: x[1])
            insights.append(f"Most responsive at {most_active_hour[0]}:00 ({most_active_hour[1]} responses)")
        
        # Speed insights
        speed = patterns.get("response_speed", {})
        avg_hours = speed.get("average_hours", 24)
        if avg_hours < 2:
            insights.append("Very fast responder (under 2 hours)")
        elif avg_hours < 8:
            insights.append("Quick responder (same day)")
        else:
            insights.append("Delayed responder (next day or later)")
        
        # Consistency insights
        consistency = patterns.get("consistency_score", 0)
        if consistency > 0.7:
            insights.append("Very consistent response timing")
        elif consistency > 0.4:
            insights.append("Moderately consistent response timing")
        else:
            insights.append("Variable response timing")
        
        return insights
        
    def _predict_response_likelihood(self, patterns: Dict[str, Any], customer_id: str) -> Dict[str, float]:
        """Predict response likelihood for different time slots"""
        # Simplified prediction based on patterns
        hourly_dist = patterns.get("hourly_distribution", {})
        total_responses = sum(hourly_dist.values()) if hourly_dist else 1
        
        predictions = {}
        
        for hour in range(24):
            # Base probability
            historical_responses = hourly_dist.get(hour, 0)
            probability = historical_responses / total_responses if total_responses > 0 else 0.04  # 1/24 default
            
            # Apply time-of-day adjustments
            if 9 <= hour <= 21:  # Waking hours
                probability *= 1.2
            elif hour in [1, 2, 3, 4, 5]:  # Sleep hours
                probability *= 0.3
            
            predictions[f"{hour:02d}:00"] = min(probability, 1.0)
        
        return predictions
        
    def _assess_analysis_reliability(self, response_times: List[Dict[str, Any]]) -> str:
        """Assess reliability of timing analysis"""
        count = len(response_times)
        
        if count >= 20:
            return "high"
        elif count >= 10:
            return "medium"  
        elif count >= 5:
            return "low"
        else:
            return "insufficient_data"