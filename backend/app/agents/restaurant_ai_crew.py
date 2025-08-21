"""
Restaurant AI Crew - Main orchestration class that coordinates all AI agents
for comprehensive customer engagement and restaurant management automation.
"""

from crewai import Crew, Task
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime
import json

# Import all specialized agents
from .customer_segmentation import CustomerSegmentationAgent
from .cultural_communication import CulturalCommunicationAgent
from .sentiment_analysis import SentimentAnalysisAgent
from .message_composer import MessageComposerAgent
from .timing_optimization import TimingOptimizationAgent
from .campaign_orchestration import CampaignOrchestrationAgent
from .performance_analyst import PerformanceAnalystAgent
from .learning_optimization import LearningOptimizationAgent
from .chat_assistant import ChatAssistantAgent

from ..tools.database_tool import DatabaseTool
from ..core.logging import get_logger

logger = get_logger(__name__)


class RestaurantAICrew:
    """
    Central orchestration system that coordinates multiple AI agents to provide
    comprehensive restaurant customer engagement automation with Arabic/English support.
    """
    
    def __init__(self, restaurant_id: str, config: Optional[Dict] = None):
        self.restaurant_id = restaurant_id
        self.config = config or {}
        self.db_tool = DatabaseTool()
        
        # Initialize all agents
        self.agents = {
            "customer_segmentation": CustomerSegmentationAgent(),
            "cultural_communication": CulturalCommunicationAgent(),
            "sentiment_analysis": SentimentAnalysisAgent(),
            "message_composer": MessageComposerAgent(),
            "timing_optimization": TimingOptimizationAgent(),
            "campaign_orchestration": CampaignOrchestrationAgent(),
            "performance_analyst": PerformanceAnalystAgent(),
            "learning_optimization": LearningOptimizationAgent(),
            "chat_assistant": ChatAssistantAgent()
        }
        
        # Initialize crew
        self.crew = None
        self._initialize_crew()
        
        logger.info(f"Restaurant AI Crew initialized for restaurant {restaurant_id}")
    
    def _initialize_crew(self):
        """Initialize the CrewAI crew with all agents"""
        try:
            # Convert agent instances to CrewAI Agent objects
            crew_agents = list(self.agents.values())
            
            # Create the crew
            self.crew = Crew(
                agents=crew_agents,
                verbose=True,
                process="sequential"  # Can be changed to "hierarchical" for complex workflows
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize crew: {str(e)}")
            raise
    
    async def process_new_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Complete workflow for processing a new customer"""
        try:
            logger.info(f"Processing new customer for restaurant {self.restaurant_id}")
            
            # Task 1: Analyze and segment the customer
            segmentation_task = Task(
                description=f"""Analyze and segment this new customer for personalized engagement:
                Customer Data: {json.dumps(customer_data, ensure_ascii=False)}
                Restaurant ID: {self.restaurant_id}
                
                Provide detailed customer segment, preferences, and engagement strategy recommendations.""",
                agent=self.agents["customer_segmentation"]
            )
            
            # Execute segmentation
            segmentation_result = await asyncio.to_thread(
                lambda: self.crew.kickoff([segmentation_task])
            )
            
            # Task 2: Determine cultural communication approach
            cultural_task = Task(
                description=f"""Based on customer segmentation, determine the optimal cultural communication approach:
                Customer Segment: {segmentation_result}
                Customer Data: {json.dumps(customer_data, ensure_ascii=False)}
                
                Provide cultural communication strategy, language preference, and greeting style recommendations.""",
                agent=self.agents["cultural_communication"]
            )
            
            # Execute cultural analysis
            cultural_result = await asyncio.to_thread(
                lambda: self.crew.kickoff([cultural_task])
            )
            
            # Task 3: Compose welcome message
            welcome_task = Task(
                description=f"""Compose a personalized welcome message for this new customer:
                Customer Data: {json.dumps(customer_data, ensure_ascii=False)}
                Segmentation: {segmentation_result}
                Cultural Strategy: {cultural_result}
                
                Create a warm, culturally appropriate welcome message in the customer's preferred language.""",
                agent=self.agents["message_composer"]
            )
            
            # Execute message composition
            welcome_message = await asyncio.to_thread(
                lambda: self.crew.kickoff([welcome_task])
            )
            
            # Task 4: Determine optimal timing
            timing_task = Task(
                description=f"""Determine the optimal time to send the welcome message:
                Customer Data: {json.dumps(customer_data, ensure_ascii=False)}
                Segmentation: {segmentation_result}
                
                Consider cultural factors, prayer times, and customer behavior patterns.""",
                agent=self.agents["timing_optimization"]
            )
            
            # Execute timing optimization
            optimal_timing = await asyncio.to_thread(
                lambda: self.crew.kickoff([timing_task])
            )
            
            # Compile complete workflow result
            workflow_result = {
                "customer_id": customer_data.get("id"),
                "restaurant_id": self.restaurant_id,
                "workflow_completed_at": datetime.now().isoformat(),
                "segmentation": segmentation_result,
                "cultural_strategy": cultural_result,
                "welcome_message": welcome_message,
                "optimal_timing": optimal_timing,
                "next_actions": [
                    "Send welcome message at optimal time",
                    "Schedule follow-up engagement",
                    "Monitor customer response"
                ]
            }
            
            # Store workflow result
            await self.db_tool.store_customer_workflow_result(customer_data["id"], workflow_result)
            
            logger.info(f"New customer workflow completed for customer {customer_data.get('id')}")
            return workflow_result
            
        except Exception as e:
            logger.error(f"New customer workflow failed: {str(e)}")
            return {"error": f"Workflow failed: {str(e)}"}
    
    async def create_targeted_campaign(self, campaign_config: Dict[str, Any]) -> Dict[str, Any]:
        """Complete workflow for creating a targeted marketing campaign"""
        try:
            logger.info(f"Creating targeted campaign for restaurant {self.restaurant_id}")
            
            # Task 1: Analyze target audience and create segments
            segmentation_task = Task(
                description=f"""Analyze the target audience and create customer segments for this campaign:
                Campaign Config: {json.dumps(campaign_config, ensure_ascii=False)}
                Restaurant ID: {self.restaurant_id}
                
                Identify the best customer segments to target and their characteristics.""",
                agent=self.agents["customer_segmentation"]
            )
            
            target_segments = await asyncio.to_thread(
                lambda: self.crew.kickoff([segmentation_task])
            )
            
            # Task 2: Develop cultural communication strategy
            cultural_task = Task(
                description=f"""Develop cultural communication strategies for each target segment:
                Target Segments: {target_segments}
                Campaign Goals: {campaign_config.get('goals', {})}
                
                Create culturally appropriate messaging strategies for Arabic and English speakers.""",
                agent=self.agents["cultural_communication"]
            )
            
            cultural_strategies = await asyncio.to_thread(
                lambda: self.crew.kickoff([cultural_task])
            )
            
            # Task 3: Compose campaign messages
            message_task = Task(
                description=f"""Compose personalized campaign messages for different segments:
                Target Segments: {target_segments}
                Cultural Strategies: {cultural_strategies}
                Campaign Config: {json.dumps(campaign_config, ensure_ascii=False)}
                
                Create engaging messages that resonate with each customer segment.""",
                agent=self.agents["message_composer"]
            )
            
            campaign_messages = await asyncio.to_thread(
                lambda: self.crew.kickoff([message_task])
            )
            
            # Task 4: Optimize timing strategy
            timing_task = Task(
                description=f"""Optimize timing strategy for maximum engagement:
                Target Segments: {target_segments}
                Campaign Messages: {campaign_messages}
                
                Determine optimal send times considering cultural factors and customer behavior.""",
                agent=self.agents["timing_optimization"]
            )
            
            timing_strategy = await asyncio.to_thread(
                lambda: self.crew.kickoff([timing_task])
            )
            
            # Task 5: Orchestrate campaign execution
            orchestration_task = Task(
                description=f"""Plan and orchestrate the campaign execution:
                Target Segments: {target_segments}
                Messages: {campaign_messages}
                Timing Strategy: {timing_strategy}
                
                Create detailed execution plan with scheduling, monitoring, and optimization.""",
                agent=self.agents["campaign_orchestration"]
            )
            
            execution_plan = await asyncio.to_thread(
                lambda: self.crew.kickoff([orchestration_task])
            )
            
            # Compile campaign creation result
            campaign_result = {
                "restaurant_id": self.restaurant_id,
                "campaign_created_at": datetime.now().isoformat(),
                "campaign_config": campaign_config,
                "target_segments": target_segments,
                "cultural_strategies": cultural_strategies,
                "campaign_messages": campaign_messages,
                "timing_strategy": timing_strategy,
                "execution_plan": execution_plan,
                "status": "ready_for_launch"
            }
            
            # Store campaign
            campaign_id = await self.db_tool.store_campaign_plan(self.restaurant_id, campaign_result)
            campaign_result["campaign_id"] = campaign_id
            
            logger.info(f"Targeted campaign created with ID {campaign_id}")
            return campaign_result
            
        except Exception as e:
            logger.error(f"Campaign creation failed: {str(e)}")
            return {"error": f"Campaign creation failed: {str(e)}"}
    
    async def analyze_customer_feedback(self, feedback_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Complete workflow for analyzing customer feedback"""
        try:
            logger.info(f"Analyzing customer feedback for restaurant {self.restaurant_id}")
            
            # Task 1: Analyze sentiment of all feedback
            sentiment_task = Task(
                description=f"""Analyze sentiment and emotions in customer feedback:
                Feedback Data: {json.dumps(feedback_data, ensure_ascii=False)}
                Restaurant ID: {self.restaurant_id}
                
                Provide detailed sentiment analysis, emotion detection, and categorization.""",
                agent=self.agents["sentiment_analysis"]
            )
            
            sentiment_analysis = await asyncio.to_thread(
                lambda: self.crew.kickoff([sentiment_task])
            )
            
            # Task 2: Generate performance insights
            performance_task = Task(
                description=f"""Generate performance insights from customer feedback:
                Feedback Data: {json.dumps(feedback_data, ensure_ascii=False)}
                Sentiment Analysis: {sentiment_analysis}
                
                Identify trends, issues, and opportunities for improvement.""",
                agent=self.agents["performance_analyst"]
            )
            
            performance_insights = await asyncio.to_thread(
                lambda: self.crew.kickoff([performance_task])
            )
            
            # Task 3: Generate response strategies
            response_task = Task(
                description=f"""Generate appropriate response strategies for feedback:
                Feedback Data: {json.dumps(feedback_data, ensure_ascii=False)}
                Sentiment Analysis: {sentiment_analysis}
                Performance Insights: {performance_insights}
                
                Create personalized response strategies for different types of feedback.""",
                agent=self.agents["message_composer"]
            )
            
            response_strategies = await asyncio.to_thread(
                lambda: self.crew.kickoff([response_task])
            )
            
            # Task 4: Learn from feedback patterns
            learning_task = Task(
                description=f"""Learn from feedback patterns to improve future engagement:
                Feedback Data: {json.dumps(feedback_data, ensure_ascii=False)}
                Sentiment Analysis: {sentiment_analysis}
                Performance Insights: {performance_insights}
                
                Identify learning opportunities and strategy improvements.""",
                agent=self.agents["learning_optimization"]
            )
            
            learning_insights = await asyncio.to_thread(
                lambda: self.crew.kickoff([learning_task])
            )
            
            # Compile feedback analysis result
            analysis_result = {
                "restaurant_id": self.restaurant_id,
                "analysis_completed_at": datetime.now().isoformat(),
                "feedback_count": len(feedback_data),
                "sentiment_analysis": sentiment_analysis,
                "performance_insights": performance_insights,
                "response_strategies": response_strategies,
                "learning_insights": learning_insights,
                "recommendations": [
                    "Implement suggested response strategies",
                    "Monitor customer satisfaction changes",
                    "Apply learning insights to future campaigns"
                ]
            }
            
            # Store analysis
            await self.db_tool.store_feedback_analysis(self.restaurant_id, analysis_result)
            
            logger.info(f"Customer feedback analysis completed")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Feedback analysis failed: {str(e)}")
            return {"error": f"Feedback analysis failed: {str(e)}"}
    
    async def handle_chat_interaction(
        self, 
        user_id: str, 
        query: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle intelligent chat interactions with restaurant staff"""
        try:
            # Direct interaction with chat assistant
            return await self.agents["chat_assistant"].process_user_query(
                user_id, query, conversation_id
            )
            
        except Exception as e:
            logger.error(f"Chat interaction failed: {str(e)}")
            return {
                "error": True,
                "message": "عذراً، حدث خطأ في المعالجة - Sorry, processing error occurred"
            }
    
    async def optimize_restaurant_strategy(self) -> Dict[str, Any]:
        """Complete workflow for optimizing overall restaurant strategy"""
        try:
            logger.info(f"Optimizing strategy for restaurant {self.restaurant_id}")
            
            # Task 1: Analyze overall performance
            performance_task = Task(
                description=f"""Analyze overall restaurant performance and customer engagement:
                Restaurant ID: {self.restaurant_id}
                Time Period: Last 30 days
                
                Provide comprehensive performance analysis and identify areas for improvement.""",
                agent=self.agents["performance_analyst"]
            )
            
            performance_analysis = await asyncio.to_thread(
                lambda: self.crew.kickoff([performance_task])
            )
            
            # Task 2: Generate optimization strategies
            optimization_task = Task(
                description=f"""Generate optimization strategies based on performance analysis:
                Performance Analysis: {performance_analysis}
                Restaurant ID: {self.restaurant_id}
                
                Create actionable optimization strategies for improving customer engagement.""",
                agent=self.agents["learning_optimization"]
            )
            
            optimization_strategies = await asyncio.to_thread(
                lambda: self.crew.kickoff([optimization_task])
            )
            
            # Task 3: Plan implementation
            implementation_task = Task(
                description=f"""Plan implementation of optimization strategies:
                Optimization Strategies: {optimization_strategies}
                Performance Analysis: {performance_analysis}
                
                Create detailed implementation plan with timelines and success metrics.""",
                agent=self.agents["campaign_orchestration"]
            )
            
            implementation_plan = await asyncio.to_thread(
                lambda: self.crew.kickoff([implementation_task])
            )
            
            # Compile optimization result
            optimization_result = {
                "restaurant_id": self.restaurant_id,
                "optimization_completed_at": datetime.now().isoformat(),
                "performance_analysis": performance_analysis,
                "optimization_strategies": optimization_strategies,
                "implementation_plan": implementation_plan,
                "expected_improvements": {
                    "engagement_rate": "+15-25%",
                    "response_rate": "+10-20%",
                    "customer_satisfaction": "+20-30%"
                }
            }
            
            # Store optimization plan
            await self.db_tool.store_optimization_plan(self.restaurant_id, optimization_result)
            
            logger.info(f"Restaurant strategy optimization completed")
            return optimization_result
            
        except Exception as e:
            logger.error(f"Strategy optimization failed: {str(e)}")
            return {"error": f"Strategy optimization failed: {str(e)}"}
    
    async def get_crew_status(self) -> Dict[str, Any]:
        """Get status and health information for all agents"""
        try:
            agent_statuses = {}
            
            for agent_name, agent in self.agents.items():
                try:
                    if hasattr(agent, 'get_performance_summary'):
                        status = agent.get_performance_summary()
                    elif hasattr(agent, 'get_agent_summary'):
                        status = agent.get_agent_summary()
                    else:
                        status = {"status": "active", "version": "1.0.0"}
                    
                    agent_statuses[agent_name] = {
                        **status,
                        "health": "healthy",
                        "last_activity": datetime.now().isoformat()
                    }
                except Exception as e:
                    agent_statuses[agent_name] = {
                        "health": "error",
                        "error": str(e),
                        "last_activity": datetime.now().isoformat()
                    }
            
            return {
                "restaurant_id": self.restaurant_id,
                "crew_status": "operational",
                "total_agents": len(self.agents),
                "healthy_agents": len([s for s in agent_statuses.values() if s.get("health") == "healthy"]),
                "agent_statuses": agent_statuses,
                "capabilities": [
                    "New customer processing",
                    "Targeted campaign creation", 
                    "Customer feedback analysis",
                    "Chat assistance",
                    "Strategy optimization",
                    "Real-time learning and adaptation"
                ],
                "supported_languages": ["Arabic", "English"],
                "cultural_features": [
                    "Prayer time awareness",
                    "Cultural greeting preferences",
                    "Regional dialect support",
                    "Religious holiday considerations"
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get crew status: {str(e)}")
            return {"error": f"Status check failed: {str(e)}"}

    async def shutdown(self):
        """Gracefully shutdown the crew and all agents"""
        try:
            logger.info(f"Shutting down Restaurant AI Crew for restaurant {self.restaurant_id}")
            
            # Cleanup agents if they have cleanup methods
            for agent_name, agent in self.agents.items():
                try:
                    if hasattr(agent, 'cleanup'):
                        await agent.cleanup()
                except Exception as e:
                    logger.warning(f"Error cleaning up {agent_name}: {str(e)}")
            
            logger.info("Restaurant AI Crew shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during crew shutdown: {str(e)}")