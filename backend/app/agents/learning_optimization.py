"""
Learning Optimization Agent - Continuously learns from customer interactions,
campaign results, and feedback to improve agent strategies and performance.
"""

from crewai import Agent
from typing import Dict, List, Any, Optional, Tuple
import asyncio
from datetime import datetime, timedelta
import json
import numpy as np
from collections import defaultdict, deque
import statistics

from ..tools.database_tool import DatabaseTool
from ..tools.analytics_tool import AnalyticsTool
from ..tools.predictive_modeling_tool import PredictiveModelingTool
from ..tools.text_processing_tool import TextProcessingTool
from .base_agent import BaseRestaurantAgent


class LearningOptimizationAgent(BaseRestaurantAgent):
    """
    Advanced learning agent that adapts strategies based on customer interactions,
    campaign performance, and cultural insights to continuously improve engagement.
    """
    
    def __init__(self):
        # Initialize tools
        self.db_tool = DatabaseTool()
        self.analytics_tool = AnalyticsTool()
        self.predictive_tool = PredictiveModelingTool()
        self.text_tool = TextProcessingTool()
        
        # Learning memory components
        self.interaction_memory = deque(maxlen=10000)  # Recent interactions
        self.pattern_memory = {}  # Learned patterns
        self.optimization_history = []  # Optimization attempts
        
        super().__init__(
            role="Learning Optimization Specialist",
            goal="Continuously learn and adapt restaurant customer engagement strategies",
            backstory="""You are an advanced AI learning specialist focused on restaurant 
            customer engagement optimization. You have deep expertise in machine learning, 
            pattern recognition, and behavioral analysis for Arabic and English speaking customers.
            
            Your specialty is identifying successful patterns in customer interactions, 
            cultural preferences, and engagement strategies, then applying these insights 
            to continuously improve campaign effectiveness, message personalization, 
            and cultural sensitivity.
            
            You understand the nuances of Gulf Arabic culture, religious considerations, 
            and regional preferences that impact customer engagement success.""",
            tools=[self.db_tool, self.analytics_tool, self.predictive_tool, self.text_tool],
            allow_delegation=False,
            verbose=True
        )
    
    async def learn_from_interactions(
        self, 
        restaurant_id: str,
        lookback_days: int = 30
    ) -> Dict[str, Any]:
        """Learn from recent customer interactions and update strategies"""
        try:
            # Get recent interaction data
            interactions = await self.db_tool.get_interactions_for_learning(
                restaurant_id, lookback_days
            )
            
            if not interactions or len(interactions) < 10:
                return {"status": "insufficient_data", "message": "Need more interaction data"}
            
            # Update interaction memory
            self._update_interaction_memory(interactions)
            
            # Learn successful patterns
            successful_patterns = await self._identify_successful_patterns(interactions)
            
            # Learn cultural preferences
            cultural_insights = await self._learn_cultural_preferences(interactions)
            
            # Learn timing optimizations
            timing_insights = await self._learn_optimal_timing(interactions)
            
            # Learn language preferences
            language_insights = await self._learn_language_preferences(interactions)
            
            # Learn content effectiveness
            content_insights = await self._learn_content_effectiveness(interactions)
            
            # Update agent strategies
            strategy_updates = await self._update_agent_strategies(
                successful_patterns, cultural_insights, timing_insights, 
                language_insights, content_insights
            )
            
            # Generate learning report
            learning_report = {
                "restaurant_id": restaurant_id,
                "learning_date": datetime.now().isoformat(),
                "interactions_analyzed": len(interactions),
                "successful_patterns": successful_patterns,
                "cultural_insights": cultural_insights,
                "timing_insights": timing_insights,
                "language_insights": language_insights,
                "content_insights": content_insights,
                "strategy_updates": strategy_updates,
                "learning_score": await self._calculate_learning_score(interactions)
            }
            
            # Store learning insights
            await self.db_tool.store_learning_insights(restaurant_id, learning_report)
            
            await self._log_metric("learning_cycle_completed", {
                "restaurant_id": restaurant_id,
                "interactions_count": len(interactions)
            })
            
            return learning_report
            
        except Exception as e:
            await self._log_error("interaction_learning", str(e))
            return {"error": f"Learning failed: {str(e)}"}
    
    async def optimize_agent_persona(
        self, 
        agent_persona_id: str,
        performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize agent persona based on performance data"""
        try:
            # Get current persona configuration
            current_persona = await self.db_tool.get_agent_persona(agent_persona_id)
            
            if not current_persona:
                return {"error": "Agent persona not found"}
            
            # Analyze persona performance
            performance_analysis = await self._analyze_persona_performance(
                current_persona, performance_data
            )
            
            # Identify optimization opportunities
            optimization_opportunities = await self._identify_persona_optimization_opportunities(
                current_persona, performance_analysis
            )
            
            # Generate persona improvements
            persona_improvements = await self._generate_persona_improvements(
                current_persona, optimization_opportunities
            )
            
            # Test improvements virtually
            virtual_test_results = await self._virtual_test_persona_improvements(
                current_persona, persona_improvements
            )
            
            # Create optimized persona
            optimized_persona = await self._create_optimized_persona(
                current_persona, persona_improvements, virtual_test_results
            )
            
            optimization_result = {
                "agent_persona_id": agent_persona_id,
                "optimization_date": datetime.now().isoformat(),
                "performance_analysis": performance_analysis,
                "optimization_opportunities": optimization_opportunities,
                "persona_improvements": persona_improvements,
                "virtual_test_results": virtual_test_results,
                "optimized_persona": optimized_persona,
                "expected_improvement": virtual_test_results.get("expected_performance_gain", 0)
            }
            
            # Store optimization results
            await self.db_tool.store_persona_optimization(agent_persona_id, optimization_result)
            
            await self._log_metric("persona_optimized", {
                "persona_id": agent_persona_id,
                "improvement": virtual_test_results.get("expected_performance_gain", 0)
            })
            
            return optimization_result
            
        except Exception as e:
            await self._log_error("persona_optimization", str(e))
            return {"error": f"Persona optimization failed: {str(e)}"}
    
    async def adapt_campaign_strategy(
        self, 
        campaign_id: str,
        real_time_performance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adapt campaign strategy in real-time based on performance"""
        try:
            # Get current campaign configuration
            campaign_config = await self.db_tool.get_campaign_config(campaign_id)
            
            # Analyze real-time performance
            performance_analysis = await self._analyze_realtime_performance(
                campaign_config, real_time_performance
            )
            
            # Detect performance issues
            performance_issues = await self._detect_performance_issues(performance_analysis)
            
            # Generate adaptive strategies
            adaptive_strategies = await self._generate_adaptive_strategies(
                campaign_config, performance_issues, performance_analysis
            )
            
            # Apply immediate optimizations
            immediate_optimizations = await self._apply_immediate_optimizations(
                campaign_id, adaptive_strategies
            )
            
            # Predict strategy effectiveness
            strategy_predictions = await self._predict_strategy_effectiveness(
                adaptive_strategies, performance_analysis
            )
            
            adaptation_result = {
                "campaign_id": campaign_id,
                "adaptation_timestamp": datetime.now().isoformat(),
                "performance_analysis": performance_analysis,
                "performance_issues": performance_issues,
                "adaptive_strategies": adaptive_strategies,
                "immediate_optimizations": immediate_optimizations,
                "strategy_predictions": strategy_predictions,
                "adaptation_success": len(immediate_optimizations) > 0
            }
            
            # Store adaptation results
            await self.db_tool.store_campaign_adaptation(campaign_id, adaptation_result)
            
            await self._log_metric("campaign_adapted", {
                "campaign_id": campaign_id,
                "optimizations_applied": len(immediate_optimizations)
            })
            
            return adaptation_result
            
        except Exception as e:
            await self._log_error("campaign_adaptation", str(e))
            return {"error": f"Campaign adaptation failed: {str(e)}"}
    
    async def predict_customer_behavior(
        self, 
        customer_id: str,
        prediction_horizon_days: int = 30
    ) -> Dict[str, Any]:
        """Predict customer behavior and preferences for personalization"""
        try:
            # Get customer history
            customer_history = await self.db_tool.get_customer_interaction_history(customer_id)
            
            if not customer_history or len(customer_history) < 5:
                return {"status": "insufficient_data", "message": "Need more customer history"}
            
            # Extract behavior patterns
            behavior_patterns = await self._extract_behavior_patterns(customer_history)
            
            # Predict engagement likelihood
            engagement_prediction = await self._predict_engagement_likelihood(
                customer_history, behavior_patterns, prediction_horizon_days
            )
            
            # Predict preferred communication style
            communication_preferences = await self._predict_communication_preferences(
                customer_history, behavior_patterns
            )
            
            # Predict optimal messaging timing
            optimal_timing = await self._predict_optimal_timing(
                customer_history, behavior_patterns
            )
            
            # Predict content preferences
            content_preferences = await self._predict_content_preferences(
                customer_history, behavior_patterns
            )
            
            # Generate personalization recommendations
            personalization_recommendations = await self._generate_personalization_recommendations(
                engagement_prediction, communication_preferences, 
                optimal_timing, content_preferences
            )
            
            behavior_prediction = {
                "customer_id": customer_id,
                "prediction_date": datetime.now().isoformat(),
                "prediction_horizon_days": prediction_horizon_days,
                "behavior_patterns": behavior_patterns,
                "engagement_prediction": engagement_prediction,
                "communication_preferences": communication_preferences,
                "optimal_timing": optimal_timing,
                "content_preferences": content_preferences,
                "personalization_recommendations": personalization_recommendations,
                "confidence_score": await self._calculate_prediction_confidence(customer_history)
            }
            
            # Store behavior prediction
            await self.db_tool.store_behavior_prediction(customer_id, behavior_prediction)
            
            await self._log_metric("behavior_predicted", {
                "customer_id": customer_id,
                "confidence": behavior_prediction["confidence_score"]
            })
            
            return behavior_prediction
            
        except Exception as e:
            await self._log_error("behavior_prediction", str(e))
            return {"error": f"Behavior prediction failed: {str(e)}"}
    
    async def _identify_successful_patterns(self, interactions: List[Dict]) -> Dict[str, Any]:
        """Identify patterns in successful interactions"""
        try:
            successful_interactions = [
                i for i in interactions 
                if i.get('success_score', 0) > 7 or i.get('customer_response_positive', False)
            ]
            
            if not successful_interactions:
                return {}
            
            # Message length patterns
            successful_lengths = [len(i.get('message_content', '')) for i in successful_interactions]
            optimal_message_length = {
                "average": statistics.mean(successful_lengths),
                "median": statistics.median(successful_lengths),
                "range": f"{min(successful_lengths)}-{max(successful_lengths)}"
            }
            
            # Timing patterns
            successful_hours = [
                datetime.fromisoformat(i['sent_at']).hour 
                for i in successful_interactions 
                if 'sent_at' in i
            ]
            optimal_hours = self._find_peak_hours(successful_hours)
            
            # Language patterns
            language_success = defaultdict(list)
            for interaction in successful_interactions:
                lang = interaction.get('language', 'unknown')
                language_success[lang].append(interaction.get('success_score', 0))
            
            language_effectiveness = {
                lang: statistics.mean(scores) 
                for lang, scores in language_success.items()
            }
            
            # Content patterns
            successful_content_features = await self._extract_content_features(successful_interactions)
            
            # Cultural patterns
            cultural_patterns = await self._extract_cultural_patterns(successful_interactions)
            
            return {
                "optimal_message_length": optimal_message_length,
                "optimal_timing": optimal_hours,
                "language_effectiveness": language_effectiveness,
                "content_features": successful_content_features,
                "cultural_patterns": cultural_patterns,
                "success_rate": len(successful_interactions) / len(interactions),
                "confidence_score": min(len(successful_interactions) / 50, 1.0)
            }
            
        except Exception as e:
            await self._log_error("pattern_identification", str(e))
            return {}
    
    async def _learn_cultural_preferences(self, interactions: List[Dict]) -> Dict[str, Any]:
        """Learn cultural preferences from interactions"""
        try:
            cultural_insights = {
                "greeting_preferences": defaultdict(int),
                "religious_consideration_impact": defaultdict(list),
                "formality_preferences": defaultdict(int),
                "local_reference_effectiveness": defaultdict(list)
            }
            
            for interaction in interactions:
                content = interaction.get('message_content', '')
                success_score = interaction.get('success_score', 0)
                
                # Analyze greeting patterns
                if any(greeting in content for greeting in ['السلام عليكم', 'صباح الخير', 'مساء الخير']):
                    cultural_insights["greeting_preferences"]["traditional_arabic"] += 1
                elif any(greeting in content for greeting in ['Hello', 'Good morning', 'Good evening']):
                    cultural_insights["greeting_preferences"]["english"] += 1
                
                # Analyze religious considerations
                sent_time = datetime.fromisoformat(interaction.get('sent_at', datetime.now().isoformat()))
                if self._is_prayer_time(sent_time):
                    cultural_insights["religious_consideration_impact"]["during_prayer"].append(success_score)
                else:
                    cultural_insights["religious_consideration_impact"]["outside_prayer"].append(success_score)
                
                # Analyze formality level
                if any(formal in content for formal in ['حضرتك', 'سيدي', 'أستاذ']):
                    cultural_insights["formality_preferences"]["formal"] += 1
                elif any(informal in content for informal in ['أخي', 'صديقي', 'حبيبي']):
                    cultural_insights["formality_preferences"]["informal"] += 1
            
            # Calculate preferences
            processed_insights = {
                "preferred_greeting_style": max(cultural_insights["greeting_preferences"], 
                                              key=cultural_insights["greeting_preferences"].get, default="traditional_arabic"),
                "prayer_time_impact": {
                    "during_prayer_avg_success": statistics.mean(cultural_insights["religious_consideration_impact"]["during_prayer"]) 
                    if cultural_insights["religious_consideration_impact"]["during_prayer"] else 0,
                    "outside_prayer_avg_success": statistics.mean(cultural_insights["religious_consideration_impact"]["outside_prayer"]) 
                    if cultural_insights["religious_consideration_impact"]["outside_prayer"] else 0
                },
                "preferred_formality": max(cultural_insights["formality_preferences"], 
                                         key=cultural_insights["formality_preferences"].get, default="formal")
            }
            
            return processed_insights
            
        except Exception as e:
            await self._log_error("cultural_learning", str(e))
            return {}
    
    async def _learn_optimal_timing(self, interactions: List[Dict]) -> Dict[str, Any]:
        """Learn optimal timing patterns from interactions"""
        try:
            timing_data = defaultdict(list)
            
            for interaction in interactions:
                if 'sent_at' not in interaction:
                    continue
                
                sent_time = datetime.fromisoformat(interaction['sent_at'])
                success_score = interaction.get('success_score', 0)
                
                # Group by hour
                hour = sent_time.hour
                timing_data[f"hour_{hour}"].append(success_score)
                
                # Group by day of week
                day = sent_time.strftime('%A')
                timing_data[f"day_{day}"].append(success_score)
                
                # Group by time periods
                if 6 <= hour < 12:
                    timing_data["morning"].append(success_score)
                elif 12 <= hour < 17:
                    timing_data["afternoon"].append(success_score)
                elif 17 <= hour < 21:
                    timing_data["evening"].append(success_score)
                else:
                    timing_data["night"].append(success_score)
            
            # Calculate optimal timing
            hourly_performance = {
                hour: statistics.mean(scores)
                for hour, scores in timing_data.items()
                if hour.startswith("hour_") and scores
            }
            
            daily_performance = {
                day: statistics.mean(scores)
                for day, scores in timing_data.items()
                if day.startswith("day_") and scores
            }
            
            period_performance = {
                period: statistics.mean(scores)
                for period, scores in timing_data.items()
                if period in ["morning", "afternoon", "evening", "night"] and scores
            }
            
            # Find best times
            best_hours = sorted(hourly_performance.items(), key=lambda x: x[1], reverse=True)[:3]
            best_days = sorted(daily_performance.items(), key=lambda x: x[1], reverse=True)[:3]
            best_period = max(period_performance.items(), key=lambda x: x[1]) if period_performance else None
            
            return {
                "optimal_hours": [int(h.replace("hour_", "")) for h, _ in best_hours],
                "optimal_days": [d.replace("day_", "") for d, _ in best_days],
                "optimal_period": best_period[0] if best_period else "afternoon",
                "hourly_performance": hourly_performance,
                "daily_performance": daily_performance,
                "period_performance": period_performance
            }
            
        except Exception as e:
            await self._log_error("timing_learning", str(e))
            return {}
    
    async def _update_agent_strategies(
        self, 
        successful_patterns: Dict,
        cultural_insights: Dict,
        timing_insights: Dict,
        language_insights: Dict,
        content_insights: Dict
    ) -> List[Dict[str, Any]]:
        """Update agent strategies based on learning insights"""
        try:
            strategy_updates = []
            
            # Update timing strategy
            if timing_insights.get("optimal_hours"):
                strategy_updates.append({
                    "strategy_type": "timing_optimization",
                    "update_type": "replace",
                    "new_config": {
                        "optimal_send_hours": timing_insights["optimal_hours"],
                        "avoid_hours": [h for h in range(24) if h not in timing_insights["optimal_hours"][:6]]
                    },
                    "expected_improvement": 0.15,
                    "confidence": timing_insights.get("confidence_score", 0.8)
                })
            
            # Update cultural strategy
            if cultural_insights.get("preferred_greeting_style"):
                strategy_updates.append({
                    "strategy_type": "cultural_adaptation",
                    "update_type": "enhance",
                    "new_config": {
                        "preferred_greeting": cultural_insights["preferred_greeting_style"],
                        "formality_level": cultural_insights.get("preferred_formality", "formal"),
                        "prayer_time_avoidance": cultural_insights.get("prayer_time_impact", {}).get("during_prayer_avg_success", 0) < 5
                    },
                    "expected_improvement": 0.12,
                    "confidence": 0.85
                })
            
            # Update language strategy
            if language_insights.get("preferred_language"):
                strategy_updates.append({
                    "strategy_type": "language_optimization",
                    "update_type": "adjust",
                    "new_config": {
                        "primary_language": language_insights["preferred_language"],
                        "fallback_language": language_insights.get("secondary_language", "english"),
                        "language_mix_ratio": language_insights.get("optimal_ratio", 0.7)
                    },
                    "expected_improvement": 0.10,
                    "confidence": 0.9
                })
            
            # Update content strategy
            if content_insights.get("effective_features"):
                strategy_updates.append({
                    "strategy_type": "content_optimization",
                    "update_type": "enhance",
                    "new_config": {
                        "effective_content_features": content_insights["effective_features"],
                        "optimal_message_length": successful_patterns.get("optimal_message_length", {}),
                        "personalization_level": content_insights.get("personalization_effectiveness", 0.8)
                    },
                    "expected_improvement": 0.18,
                    "confidence": 0.75
                })
            
            # Store strategy updates
            for update in strategy_updates:
                await self.db_tool.store_strategy_update(update)
            
            return strategy_updates
            
        except Exception as e:
            await self._log_error("strategy_updates", str(e))
            return []
    
    def _update_interaction_memory(self, interactions: List[Dict]):
        """Update the agent's interaction memory"""
        for interaction in interactions[-1000:]:  # Keep recent interactions
            self.interaction_memory.append({
                "timestamp": interaction.get("sent_at"),
                "success_score": interaction.get("success_score", 0),
                "customer_response": interaction.get("customer_response_positive", False),
                "language": interaction.get("language"),
                "content_features": interaction.get("content_features", {}),
                "cultural_elements": interaction.get("cultural_elements", [])
            })
    
    def _find_peak_hours(self, hours: List[int]) -> List[int]:
        """Find peak engagement hours"""
        if not hours:
            return [10, 14, 19]  # Default peak hours
        
        hour_counts = defaultdict(int)
        for hour in hours:
            hour_counts[hour] += 1
        
        return sorted(hour_counts.keys(), key=hour_counts.get, reverse=True)[:3]
    
    def _is_prayer_time(self, timestamp: datetime) -> bool:
        """Check if timestamp falls during typical prayer times"""
        hour = timestamp.hour
        # Approximate prayer times (varies by location and season)
        prayer_hours = [5, 6, 12, 13, 15, 16, 18, 19, 20]
        return hour in prayer_hours

    def get_learning_summary(self) -> Dict[str, Any]:
        """Get learning agent performance summary"""
        return {
            "agent_type": "Learning Optimization",
            "version": "1.0.0",
            "capabilities": [
                "Pattern recognition from interactions",
                "Real-time campaign adaptation", 
                "Agent persona optimization",
                "Customer behavior prediction",
                "Cultural preference learning",
                "Timing optimization",
                "Content effectiveness analysis"
            ],
            "memory_components": {
                "interaction_memory_size": len(self.interaction_memory),
                "pattern_memory_entries": len(self.pattern_memory),
                "optimization_history_count": len(self.optimization_history)
            },
            "supported_languages": ["Arabic", "English"],
            "cultural_adaptations": [
                "Prayer time awareness",
                "Greeting style preferences", 
                "Formality level optimization",
                "Religious consideration impact"
            ]
        }