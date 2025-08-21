"""
Performance Analyst Agent - Tracks metrics, generates insights, and provides recommendations
for optimizing customer engagement and campaign performance.
"""

from crewai import Agent
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime, timedelta
import statistics
import json

from ..tools.database_tool import DatabaseTool
from ..tools.analytics_tool import AnalyticsTool
from ..tools.text_processing_tool import TextProcessingTool
from .base_agent import BaseRestaurantAgent


class PerformanceAnalystAgent(BaseRestaurantAgent):
    """
    Advanced performance analyst that monitors campaign effectiveness,
    customer engagement metrics, and provides actionable insights for optimization.
    """
    
    def __init__(self):
        # Initialize tools
        self.db_tool = DatabaseTool()
        self.analytics_tool = AnalyticsTool()
        self.text_tool = TextProcessingTool()
        
        super().__init__(
            role="Performance Analyst",
            goal="Monitor, analyze, and optimize restaurant customer engagement performance",
            backstory="""You are an expert performance analyst specialized in restaurant 
            customer engagement metrics. You have deep understanding of Arabic and English 
            customer behavior patterns, cultural preferences, and engagement optimization.
            
            Your expertise includes statistical analysis, A/B testing evaluation, 
            customer journey analytics, and ROI optimization for restaurant marketing campaigns.
            You provide actionable insights that drive business growth while respecting 
            cultural sensitivities and customer preferences.""",
            tools=[self.db_tool, self.analytics_tool, self.text_tool],
            allow_delegation=False,
            verbose=True
        )
    
    async def analyze_campaign_performance(
        self, 
        campaign_id: str,
        time_range: int = 30  # days
    ) -> Dict[str, Any]:
        """Comprehensive campaign performance analysis"""
        try:
            # Get campaign data
            campaign_data = await self.db_tool.get_campaign_metrics(
                campaign_id, 
                days=time_range
            )
            
            if not campaign_data:
                return {"error": "Campaign data not found"}
            
            # Calculate key performance metrics
            performance_metrics = await self._calculate_performance_metrics(campaign_data)
            
            # Analyze engagement patterns
            engagement_analysis = await self._analyze_engagement_patterns(campaign_data)
            
            # Cultural performance insights
            cultural_insights = await self._analyze_cultural_performance(campaign_data)
            
            # Generate recommendations
            recommendations = await self._generate_performance_recommendations(
                performance_metrics, engagement_analysis, cultural_insights
            )
            
            analysis = {
                "campaign_id": campaign_id,
                "analysis_date": datetime.now().isoformat(),
                "time_range_days": time_range,
                "performance_metrics": performance_metrics,
                "engagement_analysis": engagement_analysis,
                "cultural_insights": cultural_insights,
                "recommendations": recommendations,
                "overall_score": performance_metrics.get("overall_performance_score", 0)
            }
            
            # Store analysis results
            await self.db_tool.store_performance_analysis(campaign_id, analysis)
            
            await self._log_metric("campaign_analysis_completed", {"campaign_id": campaign_id})
            return analysis
            
        except Exception as e:
            await self._log_error("campaign_performance_analysis", str(e))
            return {"error": f"Analysis failed: {str(e)}"}
    
    async def generate_daily_insights(self, restaurant_id: str) -> Dict[str, Any]:
        """Generate comprehensive daily performance insights"""
        try:
            yesterday = datetime.now() - timedelta(days=1)
            
            # Get yesterday's metrics
            daily_metrics = await self.db_tool.get_daily_metrics(restaurant_id, yesterday)
            
            # Customer engagement analysis
            engagement_insights = await self._analyze_daily_engagement(daily_metrics)
            
            # Response pattern analysis
            response_patterns = await self._analyze_response_patterns(daily_metrics)
            
            # Cultural timing analysis
            cultural_timing = await self._analyze_cultural_timing_effectiveness(daily_metrics)
            
            # Sentiment trend analysis
            sentiment_trends = await self._analyze_sentiment_trends(daily_metrics)
            
            # Generate actionable insights
            actionable_insights = await self._generate_daily_actionable_insights(
                engagement_insights, response_patterns, cultural_timing, sentiment_trends
            )
            
            daily_report = {
                "restaurant_id": restaurant_id,
                "report_date": yesterday.isoformat(),
                "engagement_insights": engagement_insights,
                "response_patterns": response_patterns,
                "cultural_timing": cultural_timing,
                "sentiment_trends": sentiment_trends,
                "actionable_insights": actionable_insights,
                "overall_performance": await self._calculate_overall_daily_performance(daily_metrics)
            }
            
            # Store daily insights
            await self.db_tool.store_daily_insights(restaurant_id, daily_report)
            
            await self._log_metric("daily_insights_generated", {"restaurant_id": restaurant_id})
            return daily_report
            
        except Exception as e:
            await self._log_error("daily_insights_generation", str(e))
            return {"error": f"Daily insights generation failed: {str(e)}"}
    
    async def compare_ab_test_performance(
        self, 
        test_id: str,
        significance_threshold: float = 0.05
    ) -> Dict[str, Any]:
        """Advanced A/B test performance comparison with statistical analysis"""
        try:
            # Get A/B test data
            test_data = await self.db_tool.get_ab_test_data(test_id)
            
            if not test_data or len(test_data['variants']) < 2:
                return {"error": "Insufficient A/B test data"}
            
            # Statistical significance testing
            statistical_results = await self._perform_statistical_analysis(
                test_data, significance_threshold
            )
            
            # Performance comparison
            variant_comparison = await self._compare_variant_performance(test_data)
            
            # Cultural effectiveness analysis
            cultural_effectiveness = await self._analyze_cultural_ab_effectiveness(test_data)
            
            # Winner determination
            winner_analysis = await self._determine_test_winner(
                statistical_results, variant_comparison, cultural_effectiveness
            )
            
            ab_analysis = {
                "test_id": test_id,
                "analysis_date": datetime.now().isoformat(),
                "statistical_results": statistical_results,
                "variant_comparison": variant_comparison,
                "cultural_effectiveness": cultural_effectiveness,
                "winner_analysis": winner_analysis,
                "confidence_level": (1 - significance_threshold) * 100,
                "recommendation": await self._generate_ab_test_recommendation(winner_analysis)
            }
            
            # Store A/B test analysis
            await self.db_tool.store_ab_test_analysis(test_id, ab_analysis)
            
            await self._log_metric("ab_test_analyzed", {"test_id": test_id})
            return ab_analysis
            
        except Exception as e:
            await self._log_error("ab_test_analysis", str(e))
            return {"error": f"A/B test analysis failed: {str(e)}"}
    
    async def _calculate_performance_metrics(self, campaign_data: Dict) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        try:
            messages_sent = campaign_data.get("messages_sent", 0)
            messages_delivered = campaign_data.get("messages_delivered", 0)
            messages_read = campaign_data.get("messages_read", 0)
            responses_received = campaign_data.get("responses_received", 0)
            positive_responses = campaign_data.get("positive_responses", 0)
            conversions = campaign_data.get("conversions", 0)
            
            # Calculate rates
            delivery_rate = (messages_delivered / messages_sent * 100) if messages_sent > 0 else 0
            read_rate = (messages_read / messages_delivered * 100) if messages_delivered > 0 else 0
            response_rate = (responses_received / messages_read * 100) if messages_read > 0 else 0
            conversion_rate = (conversions / responses_received * 100) if responses_received > 0 else 0
            
            # Calculate engagement score
            engagement_score = await self._calculate_engagement_score(
                delivery_rate, read_rate, response_rate, positive_responses, responses_received
            )
            
            # Calculate ROI if cost data available
            roi = await self._calculate_campaign_roi(campaign_data)
            
            return {
                "messages_sent": messages_sent,
                "delivery_rate": round(delivery_rate, 2),
                "read_rate": round(read_rate, 2),
                "response_rate": round(response_rate, 2),
                "conversion_rate": round(conversion_rate, 2),
                "engagement_score": round(engagement_score, 2),
                "roi_percentage": round(roi, 2) if roi is not None else None,
                "overall_performance_score": await self._calculate_overall_score(
                    delivery_rate, read_rate, response_rate, conversion_rate, engagement_score
                )
            }
            
        except Exception as e:
            await self._log_error("performance_metrics_calculation", str(e))
            return {}
    
    async def _analyze_engagement_patterns(self, campaign_data: Dict) -> Dict[str, Any]:
        """Analyze customer engagement patterns"""
        try:
            engagement_by_time = campaign_data.get("engagement_by_hour", {})
            engagement_by_day = campaign_data.get("engagement_by_day", {})
            engagement_by_language = campaign_data.get("engagement_by_language", {})
            
            # Find peak engagement times
            peak_hours = sorted(engagement_by_time.items(), key=lambda x: x[1], reverse=True)[:3]
            peak_days = sorted(engagement_by_day.items(), key=lambda x: x[1], reverse=True)[:3]
            
            # Language preference analysis
            total_engagements = sum(engagement_by_language.values())
            language_preferences = {
                lang: round((count / total_engagements * 100), 2)
                for lang, count in engagement_by_language.items()
            } if total_engagements > 0 else {}
            
            # Identify engagement trends
            engagement_trend = await self._identify_engagement_trend(campaign_data)
            
            return {
                "peak_engagement_hours": [{"hour": h, "engagement": e} for h, e in peak_hours],
                "peak_engagement_days": [{"day": d, "engagement": e} for d, e in peak_days],
                "language_preferences": language_preferences,
                "engagement_trend": engagement_trend,
                "average_response_time": campaign_data.get("avg_response_time_minutes", 0),
                "repeat_engagement_rate": campaign_data.get("repeat_engagement_rate", 0)
            }
            
        except Exception as e:
            await self._log_error("engagement_pattern_analysis", str(e))
            return {}
    
    async def _analyze_cultural_performance(self, campaign_data: Dict) -> Dict[str, Any]:
        """Analyze performance from cultural perspective"""
        try:
            # Religious timing impact
            ramadan_performance = campaign_data.get("ramadan_period_metrics", {})
            prayer_time_avoidance = campaign_data.get("prayer_time_avoidance_effectiveness", {})
            
            # Cultural content performance
            cultural_content_metrics = campaign_data.get("cultural_content_performance", {})
            
            # Language-specific performance
            arabic_performance = campaign_data.get("arabic_message_performance", {})
            english_performance = campaign_data.get("english_message_performance", {})
            
            cultural_insights = {
                "religious_consideration_impact": {
                    "ramadan_engagement": ramadan_performance.get("engagement_change", 0),
                    "prayer_time_respect": prayer_time_avoidance.get("effectiveness_score", 0),
                    "cultural_timing_optimization": await self._analyze_cultural_timing_optimization(campaign_data)
                },
                "language_performance": {
                    "arabic_effectiveness": arabic_performance.get("engagement_rate", 0),
                    "english_effectiveness": english_performance.get("engagement_rate", 0),
                    "preferred_language_by_segment": await self._analyze_language_preferences(campaign_data)
                },
                "cultural_content_resonance": {
                    "traditional_greetings": cultural_content_metrics.get("traditional_greetings_impact", 0),
                    "local_references": cultural_content_metrics.get("local_references_impact", 0),
                    "cultural_sensitivity_score": await self._calculate_cultural_sensitivity_score(campaign_data)
                }
            }
            
            return cultural_insights
            
        except Exception as e:
            await self._log_error("cultural_performance_analysis", str(e))
            return {}
    
    async def _generate_performance_recommendations(
        self, 
        performance_metrics: Dict, 
        engagement_analysis: Dict, 
        cultural_insights: Dict
    ) -> List[Dict[str, Any]]:
        """Generate actionable performance improvement recommendations"""
        try:
            recommendations = []
            
            # Delivery rate recommendations
            if performance_metrics.get("delivery_rate", 0) < 95:
                recommendations.append({
                    "category": "delivery_optimization",
                    "priority": "high",
                    "title": "تحسين معدل التسليم - Improve Delivery Rate",
                    "description": "معدل التسليم أقل من المتوقع. تحقق من صحة أرقام الهواتف وحالة الحساب",
                    "english_description": "Delivery rate below expected. Verify phone numbers and account status",
                    "action_items": [
                        "Validate phone numbers before sending",
                        "Check WhatsApp Business account status",
                        "Review message template compliance"
                    ],
                    "expected_impact": "5-10% delivery rate improvement"
                })
            
            # Response rate recommendations
            if performance_metrics.get("response_rate", 0) < 20:
                peak_hours = engagement_analysis.get("peak_engagement_hours", [])
                if peak_hours:
                    recommendations.append({
                        "category": "timing_optimization",
                        "priority": "medium",
                        "title": "تحسين توقيت الرسائل - Optimize Message Timing",
                        "description": f"أرسل الرسائل في الساعات الأكثر نشاطاً: {', '.join([str(h['hour']) for h in peak_hours[:2]])}",
                        "english_description": f"Send messages during peak hours: {', '.join([str(h['hour']) for h in peak_hours[:2]])}",
                        "action_items": [
                            "Schedule campaigns during peak engagement hours",
                            "Avoid prayer times and late evening hours",
                            "Test different sending times"
                        ],
                        "expected_impact": "3-7% response rate improvement"
                    })
            
            # Cultural optimization recommendations
            cultural_score = cultural_insights.get("cultural_content_resonance", {}).get("cultural_sensitivity_score", 0)
            if cultural_score < 80:
                recommendations.append({
                    "category": "cultural_optimization",
                    "priority": "high",
                    "title": "تحسين الحساسية الثقافية - Enhance Cultural Sensitivity",
                    "description": "تحسين المحتوى ليكون أكثر ملاءمة للثقافة المحلية",
                    "english_description": "Improve content cultural relevance",
                    "action_items": [
                        "Use more traditional Arabic greetings",
                        "Include local cultural references",
                        "Respect religious observances in messaging"
                    ],
                    "expected_impact": "8-15% engagement improvement"
                })
            
            # Language preference recommendations
            lang_prefs = engagement_analysis.get("language_preferences", {})
            if lang_prefs.get("arabic", 0) > 70:
                recommendations.append({
                    "category": "language_optimization",
                    "priority": "medium",
                    "title": "التركيز على المحتوى العربي - Focus on Arabic Content",
                    "description": "العملاء يفضلون المحتوى العربي بنسبة عالية",
                    "english_description": "Customers strongly prefer Arabic content",
                    "action_items": [
                        "Increase Arabic content ratio",
                        "Improve Arabic message personalization",
                        "Use regional Arabic dialects appropriately"
                    ],
                    "expected_impact": "5-12% engagement improvement"
                })
            
            # Conversion rate recommendations
            if performance_metrics.get("conversion_rate", 0) < 10:
                recommendations.append({
                    "category": "conversion_optimization",
                    "priority": "high",
                    "title": "تحسين معدل التحويل - Improve Conversion Rate",
                    "description": "معدل التحويل يحتاج تحسين من خلال عروض أفضل ودعوات واضحة للعمل",
                    "english_description": "Conversion rate needs improvement through better offers and clear CTAs",
                    "action_items": [
                        "Create more compelling offers",
                        "Use clearer calls-to-action",
                        "Implement urgency in messages",
                        "Provide easy ordering options"
                    ],
                    "expected_impact": "15-25% conversion rate improvement"
                })
            
            # Sort by priority
            priority_order = {"high": 1, "medium": 2, "low": 3}
            recommendations.sort(key=lambda x: priority_order.get(x["priority"], 3))
            
            return recommendations
            
        except Exception as e:
            await self._log_error("recommendation_generation", str(e))
            return []
    
    async def _calculate_engagement_score(
        self, 
        delivery_rate: float, 
        read_rate: float, 
        response_rate: float, 
        positive_responses: int, 
        total_responses: int
    ) -> float:
        """Calculate comprehensive engagement score"""
        try:
            # Weighted engagement score
            delivery_weight = 0.2
            read_weight = 0.3
            response_weight = 0.3
            sentiment_weight = 0.2
            
            # Calculate sentiment score
            sentiment_score = (positive_responses / total_responses * 100) if total_responses > 0 else 50
            
            engagement_score = (
                delivery_rate * delivery_weight +
                read_rate * read_weight +
                response_rate * response_weight +
                sentiment_score * sentiment_weight
            )
            
            return min(100, max(0, engagement_score))
            
        except Exception:
            return 0
    
    async def _calculate_overall_score(
        self, 
        delivery_rate: float, 
        read_rate: float, 
        response_rate: float, 
        conversion_rate: float, 
        engagement_score: float
    ) -> float:
        """Calculate overall campaign performance score"""
        try:
            # Weighted overall score
            weights = {
                "delivery": 0.15,
                "read": 0.25,
                "response": 0.25,
                "conversion": 0.20,
                "engagement": 0.15
            }
            
            overall_score = (
                delivery_rate * weights["delivery"] +
                read_rate * weights["read"] +
                response_rate * weights["response"] +
                conversion_rate * weights["conversion"] +
                engagement_score * weights["engagement"]
            )
            
            return min(100, max(0, overall_score))
            
        except Exception:
            return 0
    
    async def _calculate_campaign_roi(self, campaign_data: Dict) -> Optional[float]:
        """Calculate campaign ROI if cost and revenue data available"""
        try:
            campaign_cost = campaign_data.get("campaign_cost", 0)
            generated_revenue = campaign_data.get("generated_revenue", 0)
            
            if campaign_cost > 0:
                roi = ((generated_revenue - campaign_cost) / campaign_cost) * 100
                return roi
            
            return None
            
        except Exception:
            return None

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get agent performance summary"""
        return {
            "agent_type": "Performance Analyst",
            "version": "1.0.0",
            "capabilities": [
                "Campaign performance analysis",
                "Daily insights generation",
                "A/B testing evaluation",
                "Cultural performance optimization",
                "ROI calculation and tracking",
                "Engagement pattern analysis",
                "Statistical significance testing"
            ],
            "supported_languages": ["Arabic", "English"],
            "cultural_features": [
                "Prayer time consideration",
                "Ramadan period analysis",
                "Cultural content effectiveness",
                "Regional dialect optimization"
            ]
        }