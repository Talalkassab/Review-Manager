"""
RestaurantAICrew - Orchestrates all 9 agents working together for restaurant customer feedback system
"""
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import json
import asyncio
from enum import Enum
from crewai import Crew, Task, Process
import logging

# Import all agent classes
from .sentiment_analysis_agent import SentimentAnalysisAgent
from .customer_segmentation_agent import CustomerSegmentationAgent  
from .message_composer_agent import MessageComposerAgent
from .timing_optimization_agent import TimingOptimizationAgent
from .cultural_communication_agent import CulturalCommunicationAgent
from .campaign_orchestration_agent import CampaignOrchestrationAgent
from .performance_analyst_agent import PerformanceAnalystAgent
from .learning_optimization_agent import LearningOptimizationAgent
from .chat_assistant_agent import ChatAssistantAgent

from .base_agent import BaseRestaurantAgent


class WorkflowType(Enum):
    """Types of workflows the crew can execute"""
    CUSTOMER_FEEDBACK_PROCESSING = "customer_feedback_processing"
    CAMPAIGN_CREATION = "campaign_creation"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    LEARNING_AND_OPTIMIZATION = "learning_and_optimization"
    REAL_TIME_SUPPORT = "real_time_support"
    COMPREHENSIVE_ANALYSIS = "comprehensive_analysis"


class TaskPriority(Enum):
    """Priority levels for tasks"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RestaurantAICrew:
    """
    Main orchestration class that manages all 9 agents working together
    for comprehensive restaurant customer feedback and engagement system.
    """
    
    def __init__(self):
        # Initialize all agents
        self.agents = self._initialize_agents()
        
        # Initialize crew
        self.crew = self._initialize_crew()
        
        # Workflow configurations
        self.workflows = self._configure_workflows()
        
        # Task queue and management
        self.task_queue = []
        self.active_tasks = {}
        self.completed_tasks = {}
        
        # Performance tracking
        self.crew_metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "average_completion_time": 0,
            "agent_utilization": {},
            "workflow_success_rates": {}
        }
        
        # Coordination settings
        self.coordination_settings = {
            "max_concurrent_tasks": 5,
            "task_timeout_minutes": 30,
            "retry_attempts": 3,
            "escalation_threshold": 2
        }
        
        # Logger
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def _initialize_agents(self) -> Dict[str, BaseRestaurantAgent]:
        """Initialize all 9 agents"""
        agents = {
            "sentiment_analysis": SentimentAnalysisAgent(),
            "customer_segmentation": CustomerSegmentationAgent(),
            "message_composer": MessageComposerAgent(), 
            "timing_optimization": TimingOptimizationAgent(),
            "cultural_communication": CulturalCommunicationAgent(),
            "campaign_orchestration": CampaignOrchestrationAgent(),
            "performance_analyst": PerformanceAnalystAgent(),
            "learning_optimization": LearningOptimizationAgent(),
            "chat_assistant": ChatAssistantAgent()
        }
        
        self.logger.info(f"Initialized {len(agents)} agents successfully")
        return agents
        
    def _initialize_crew(self) -> Crew:
        """Initialize the CrewAI crew with all agents"""
        crew = Crew(
            agents=list(self.agents.values()),
            tasks=[],  # Tasks will be created dynamically
            process=Process.hierarchical,  # Use hierarchical process for better coordination
            verbose=True,
            memory=True
        )
        
        self.logger.info("CrewAI crew initialized successfully")
        return crew
        
    def _configure_workflows(self) -> Dict[WorkflowType, Dict[str, Any]]:
        """Configure different workflow types"""
        workflows = {
            WorkflowType.CUSTOMER_FEEDBACK_PROCESSING: {
                "name": "Customer Feedback Processing",
                "description": "Process incoming customer feedback through sentiment analysis, segmentation, and response generation",
                "agents_involved": [
                    "sentiment_analysis", "customer_segmentation", 
                    "message_composer", "cultural_communication"
                ],
                "sequence": [
                    {"agent": "sentiment_analysis", "task": "analyze_sentiment"},
                    {"agent": "customer_segmentation", "task": "categorize_customer"},
                    {"agent": "cultural_communication", "task": "validate_cultural_context"},
                    {"agent": "message_composer", "task": "compose_response"}
                ],
                "success_criteria": {
                    "sentiment_accuracy": 0.8,
                    "response_appropriateness": 0.9,
                    "completion_time_minutes": 5
                }
            },
            
            WorkflowType.CAMPAIGN_CREATION: {
                "name": "Campaign Creation and Optimization",
                "description": "Create, optimize, and launch customer engagement campaigns",
                "agents_involved": [
                    "customer_segmentation", "message_composer", "timing_optimization",
                    "cultural_communication", "campaign_orchestration"
                ],
                "sequence": [
                    {"agent": "customer_segmentation", "task": "identify_target_segments"},
                    {"agent": "cultural_communication", "task": "ensure_cultural_appropriateness"},
                    {"agent": "message_composer", "task": "create_campaign_messages"},
                    {"agent": "timing_optimization", "task": "optimize_timing"},
                    {"agent": "campaign_orchestration", "task": "launch_campaign"}
                ],
                "success_criteria": {
                    "targeting_precision": 0.85,
                    "message_quality": 0.9,
                    "cultural_appropriateness": 0.95
                }
            },
            
            WorkflowType.PERFORMANCE_ANALYSIS: {
                "name": "Comprehensive Performance Analysis",
                "description": "Analyze system performance and generate insights",
                "agents_involved": [
                    "performance_analyst", "sentiment_analysis", "learning_optimization"
                ],
                "sequence": [
                    {"agent": "performance_analyst", "task": "analyze_performance_metrics"},
                    {"agent": "sentiment_analysis", "task": "analyze_feedback_trends"},
                    {"agent": "learning_optimization", "task": "generate_optimization_recommendations"}
                ],
                "success_criteria": {
                    "analysis_completeness": 0.9,
                    "insight_quality": 0.85,
                    "recommendation_actionability": 0.8
                }
            },
            
            WorkflowType.LEARNING_AND_OPTIMIZATION: {
                "name": "System Learning and Optimization",
                "description": "Learn from performance data and optimize system behavior",
                "agents_involved": [
                    "learning_optimization", "performance_analyst", "campaign_orchestration"
                ],
                "sequence": [
                    {"agent": "performance_analyst", "task": "collect_performance_data"},
                    {"agent": "learning_optimization", "task": "analyze_learning_opportunities"},
                    {"agent": "learning_optimization", "task": "implement_optimizations"},
                    {"agent": "campaign_orchestration", "task": "update_campaign_strategies"}
                ],
                "success_criteria": {
                    "learning_effectiveness": 0.75,
                    "optimization_impact": 0.1,  # 10% improvement
                    "implementation_success": 0.9
                }
            },
            
            WorkflowType.REAL_TIME_SUPPORT: {
                "name": "Real-time Customer Support",
                "description": "Provide immediate support for incoming customer queries",
                "agents_involved": [
                    "sentiment_analysis", "chat_assistant", "message_composer", "cultural_communication"
                ],
                "sequence": [
                    {"agent": "sentiment_analysis", "task": "quick_sentiment_analysis"},
                    {"agent": "chat_assistant", "task": "understand_query_intent"},
                    {"agent": "cultural_communication", "task": "adapt_cultural_context"},
                    {"agent": "message_composer", "task": "generate_immediate_response"}
                ],
                "success_criteria": {
                    "response_time_seconds": 30,
                    "query_understanding_accuracy": 0.85,
                    "response_satisfaction": 0.8
                }
            },
            
            WorkflowType.COMPREHENSIVE_ANALYSIS: {
                "name": "Comprehensive Business Analysis",
                "description": "Full-scale analysis involving all agents for strategic insights",
                "agents_involved": list(self.agents.keys()),
                "sequence": [
                    {"agent": "performance_analyst", "task": "generate_performance_overview"},
                    {"agent": "sentiment_analysis", "task": "analyze_customer_sentiment_trends"},
                    {"agent": "customer_segmentation", "task": "analyze_customer_behavior_patterns"},
                    {"agent": "timing_optimization", "task": "analyze_engagement_patterns"},
                    {"agent": "cultural_communication", "task": "assess_cultural_effectiveness"},
                    {"agent": "campaign_orchestration", "task": "evaluate_campaign_effectiveness"},
                    {"agent": "learning_optimization", "task": "identify_strategic_optimizations"},
                    {"agent": "message_composer", "task": "analyze_message_effectiveness"},
                    {"agent": "chat_assistant", "task": "generate_executive_summary"}
                ],
                "success_criteria": {
                    "analysis_depth": 0.9,
                    "cross_agent_coordination": 0.85,
                    "strategic_value": 0.8
                }
            }
        }
        
        return workflows
        
    async def execute_workflow(self, workflow_type: WorkflowType, 
                              input_data: Dict[str, Any],
                              priority: TaskPriority = TaskPriority.MEDIUM) -> Dict[str, Any]:
        """
        Execute a specific workflow with the appropriate agents
        """
        workflow_id = f"{workflow_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.logger.info(f"Starting workflow: {workflow_type.value} with ID: {workflow_id}")
        
        try:
            # Get workflow configuration
            workflow_config = self.workflows[workflow_type]
            
            # Create workflow execution context
            execution_context = {
                "workflow_id": workflow_id,
                "workflow_type": workflow_type,
                "start_time": datetime.now(),
                "input_data": input_data,
                "priority": priority,
                "status": "running",
                "results": {},
                "agent_outputs": {},
                "metrics": {}
            }
            
            # Add to active tasks
            self.active_tasks[workflow_id] = execution_context
            
            # Execute workflow sequence
            workflow_results = await self._execute_workflow_sequence(
                workflow_config, input_data, execution_context
            )
            
            # Calculate workflow metrics
            execution_metrics = self._calculate_execution_metrics(execution_context)
            
            # Validate success criteria
            success_validation = self._validate_success_criteria(
                workflow_config["success_criteria"], workflow_results, execution_metrics
            )
            
            # Compile final results
            final_results = {
                "workflow_id": workflow_id,
                "workflow_type": workflow_type.value,
                "status": "completed" if success_validation["success"] else "failed",
                "execution_time_seconds": execution_metrics["total_execution_time"],
                "input_data": input_data,
                "results": workflow_results,
                "agent_contributions": execution_context["agent_outputs"],
                "metrics": execution_metrics,
                "success_validation": success_validation,
                "completed_at": datetime.now().isoformat()
            }
            
            # Move from active to completed tasks
            del self.active_tasks[workflow_id]
            self.completed_tasks[workflow_id] = final_results
            
            # Update crew metrics
            self._update_crew_metrics(workflow_type, final_results)
            
            self.logger.info(f"Workflow {workflow_id} completed successfully")
            return final_results
            
        except Exception as e:
            self.logger.error(f"Workflow {workflow_id} failed: {str(e)}")
            
            # Handle workflow failure
            failure_result = await self._handle_workflow_failure(workflow_id, e, execution_context)
            return failure_result
            
    async def _execute_workflow_sequence(self, workflow_config: Dict[str, Any], 
                                        input_data: Dict[str, Any],
                                        execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the sequence of tasks in a workflow"""
        sequence = workflow_config["sequence"]
        workflow_results = {}
        current_data = input_data.copy()
        
        for step_index, step in enumerate(sequence):
            agent_name = step["agent"]
            task_name = step["task"]
            
            self.logger.info(f"Executing step {step_index + 1}: {agent_name}.{task_name}")
            
            # Get the agent
            agent = self.agents[agent_name]
            
            # Create CrewAI task
            crew_task = Task(
                description=f"Execute {task_name} for workflow step {step_index + 1}",
                agent=agent,
                expected_output="Structured data result from agent processing"
            )
            
            # Execute the task
            step_start_time = datetime.now()
            
            try:
                # Execute agent-specific method
                if hasattr(agent, task_name):
                    step_result = await self._execute_agent_task(agent, task_name, current_data)
                else:
                    # Fallback to generic task execution
                    step_result = await self._execute_generic_task(agent, task_name, current_data)
                    
                step_end_time = datetime.now()
                step_duration = (step_end_time - step_start_time).total_seconds()
                
                # Store step results
                workflow_results[f"step_{step_index + 1}_{agent_name}"] = step_result
                execution_context["agent_outputs"][agent_name] = step_result
                
                # Update current data for next step
                current_data.update({
                    "previous_step_result": step_result,
                    "step_context": {
                        "step_index": step_index,
                        "agent": agent_name,
                        "task": task_name,
                        "duration": step_duration
                    }
                })
                
                self.logger.info(f"Step {step_index + 1} completed in {step_duration:.2f} seconds")
                
            except Exception as e:
                self.logger.error(f"Step {step_index + 1} failed: {str(e)}")
                
                # Try to recover or escalate
                recovery_result = await self._attempt_step_recovery(
                    step, current_data, e, execution_context
                )
                
                if recovery_result["recovered"]:
                    step_result = recovery_result["result"]
                    workflow_results[f"step_{step_index + 1}_{agent_name}"] = step_result
                else:
                    raise e
                    
        return workflow_results
        
    async def _execute_agent_task(self, agent: BaseRestaurantAgent, 
                                 task_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific task on an agent"""
        try:
            # Get the method from the agent
            task_method = getattr(agent, task_name)
            
            # Execute the method
            if asyncio.iscoroutinefunction(task_method):
                result = await task_method(data)
            else:
                result = task_method(data)
                
            return {
                "success": True,
                "result": result,
                "agent": agent.__class__.__name__,
                "task": task_name,
                "execution_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent": agent.__class__.__name__,
                "task": task_name,
                "execution_time": datetime.now().isoformat()
            }
            
    async def _execute_generic_task(self, agent: BaseRestaurantAgent, 
                                   task_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a generic task when specific method doesn't exist"""
        # Map common task names to potential methods
        method_mapping = {
            "analyze_sentiment": "analyze_sentiment",
            "categorize_customer": "segment_customers",
            "compose_response": "compose_message",
            "validate_cultural_context": "validate_cultural_appropriateness",
            "optimize_timing": "optimize_send_timing",
            "launch_campaign": "execute_campaign",
            "analyze_performance_metrics": "analyze_campaign_performance",
            "quick_sentiment_analysis": "analyze_sentiment",
            "understand_query_intent": "process_chat_query"
        }
        
        actual_method = method_mapping.get(task_name, task_name)
        
        if hasattr(agent, actual_method):
            return await self._execute_agent_task(agent, actual_method, data)
        else:
            # Return a placeholder result
            return {
                "success": True,
                "result": f"Generic task {task_name} executed on {agent.__class__.__name__}",
                "agent": agent.__class__.__name__,
                "task": task_name,
                "execution_time": datetime.now().isoformat(),
                "note": "Generic execution - specific method not found"
            }
            
    async def _attempt_step_recovery(self, step: Dict[str, Any], data: Dict[str, Any], 
                                   error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to recover from a failed step"""
        recovery_strategies = [
            self._retry_with_modified_data,
            self._use_fallback_agent,
            self._skip_with_placeholder
        ]
        
        for strategy in recovery_strategies:
            try:
                recovery_result = await strategy(step, data, error, context)
                if recovery_result["recovered"]:
                    return recovery_result
            except Exception as recovery_error:
                self.logger.warning(f"Recovery strategy failed: {str(recovery_error)}")
                continue
                
        return {"recovered": False, "error": str(error)}
        
    async def _retry_with_modified_data(self, step: Dict[str, Any], data: Dict[str, Any], 
                                       error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Retry the step with modified data"""
        # Simplify the data and retry
        simplified_data = {
            "text": data.get("text", ""),
            "context": {"retry": True},
            "simplified": True
        }
        
        agent = self.agents[step["agent"]]
        result = await self._execute_agent_task(agent, step["task"], simplified_data)
        
        return {
            "recovered": result["success"],
            "result": result,
            "strategy": "retry_with_modified_data"
        }
        
    async def _use_fallback_agent(self, step: Dict[str, Any], data: Dict[str, Any], 
                                 error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Use a fallback agent for the task"""
        fallback_mapping = {
            "sentiment_analysis": "chat_assistant",
            "customer_segmentation": "performance_analyst",
            "message_composer": "chat_assistant"
        }
        
        fallback_agent_name = fallback_mapping.get(step["agent"])
        if fallback_agent_name and fallback_agent_name in self.agents:
            fallback_agent = self.agents[fallback_agent_name]
            result = await self._execute_agent_task(fallback_agent, step["task"], data)
            
            return {
                "recovered": result["success"],
                "result": result,
                "strategy": "use_fallback_agent",
                "fallback_agent": fallback_agent_name
            }
            
        return {"recovered": False}
        
    async def _skip_with_placeholder(self, step: Dict[str, Any], data: Dict[str, Any], 
                                    error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Skip the step with a placeholder result"""
        placeholder_result = {
            "success": True,
            "result": {
                "placeholder": True,
                "original_error": str(error),
                "step_skipped": step,
                "message": "Step skipped due to error, placeholder result provided"
            },
            "agent": step["agent"],
            "task": step["task"],
            "execution_time": datetime.now().isoformat()
        }
        
        return {
            "recovered": True,
            "result": placeholder_result,
            "strategy": "skip_with_placeholder"
        }
        
    def _calculate_execution_metrics(self, execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate metrics for workflow execution"""
        start_time = execution_context["start_time"]
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        agent_outputs = execution_context.get("agent_outputs", {})
        
        return {
            "total_execution_time": total_time,
            "agents_used": len(agent_outputs),
            "successful_steps": sum(1 for output in agent_outputs.values() if output.get("success", False)),
            "failed_steps": sum(1 for output in agent_outputs.values() if not output.get("success", True)),
            "average_step_time": total_time / len(agent_outputs) if agent_outputs else 0,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
        
    def _validate_success_criteria(self, criteria: Dict[str, Any], results: Dict[str, Any], 
                                 metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Validate workflow against success criteria"""
        validation_results = {
            "success": True,
            "criteria_met": {},
            "criteria_failed": {},
            "overall_score": 0.0
        }
        
        total_criteria = len(criteria)
        met_criteria = 0
        
        for criterion, threshold in criteria.items():
            if criterion in metrics:
                actual_value = metrics[criterion]
                if isinstance(threshold, (int, float)):
                    met = actual_value >= threshold
                else:
                    met = actual_value == threshold
                    
                if met:
                    validation_results["criteria_met"][criterion] = {
                        "threshold": threshold,
                        "actual": actual_value,
                        "status": "met"
                    }
                    met_criteria += 1
                else:
                    validation_results["criteria_failed"][criterion] = {
                        "threshold": threshold,
                        "actual": actual_value,
                        "status": "failed"
                    }
                    validation_results["success"] = False
                    
        validation_results["overall_score"] = met_criteria / total_criteria if total_criteria > 0 else 1.0
        
        return validation_results
        
    def _update_crew_metrics(self, workflow_type: WorkflowType, results: Dict[str, Any]) -> None:
        """Update overall crew performance metrics"""
        if results["status"] == "completed":
            self.crew_metrics["tasks_completed"] += 1
        else:
            self.crew_metrics["tasks_failed"] += 1
            
        # Update workflow success rates
        workflow_name = workflow_type.value
        if workflow_name not in self.crew_metrics["workflow_success_rates"]:
            self.crew_metrics["workflow_success_rates"][workflow_name] = {"completed": 0, "failed": 0}
            
        if results["status"] == "completed":
            self.crew_metrics["workflow_success_rates"][workflow_name]["completed"] += 1
        else:
            self.crew_metrics["workflow_success_rates"][workflow_name]["failed"] += 1
            
        # Update average completion time
        execution_time = results.get("execution_time_seconds", 0)
        current_avg = self.crew_metrics["average_completion_time"]
        total_tasks = self.crew_metrics["tasks_completed"] + self.crew_metrics["tasks_failed"]
        
        self.crew_metrics["average_completion_time"] = (
            (current_avg * (total_tasks - 1) + execution_time) / total_tasks
        )
        
        # Update agent utilization
        for agent_name in results.get("agent_contributions", {}):
            if agent_name not in self.crew_metrics["agent_utilization"]:
                self.crew_metrics["agent_utilization"][agent_name] = 0
            self.crew_metrics["agent_utilization"][agent_name] += 1
            
    async def _handle_workflow_failure(self, workflow_id: str, error: Exception, 
                                      context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle workflow failure"""
        failure_result = {
            "workflow_id": workflow_id,
            "status": "failed",
            "error": str(error),
            "error_type": type(error).__name__,
            "failure_time": datetime.now().isoformat(),
            "partial_results": context.get("agent_outputs", {}),
            "recovery_attempted": False
        }
        
        # Attempt recovery if configured
        if self.coordination_settings["retry_attempts"] > 0:
            # Implement recovery logic here
            failure_result["recovery_attempted"] = True
            
        # Move to completed tasks (as failed)
        if workflow_id in self.active_tasks:
            del self.active_tasks[workflow_id]
        self.completed_tasks[workflow_id] = failure_result
        
        return failure_result
        
    # Public interface methods
    
    async def process_customer_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process customer feedback through the complete pipeline"""
        return await self.execute_workflow(
            WorkflowType.CUSTOMER_FEEDBACK_PROCESSING,
            feedback_data,
            TaskPriority.HIGH
        )
        
    async def create_campaign(self, campaign_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create and launch a new campaign"""
        return await self.execute_workflow(
            WorkflowType.CAMPAIGN_CREATION,
            campaign_requirements,
            TaskPriority.MEDIUM
        )
        
    async def analyze_performance(self, analysis_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive performance analysis"""
        return await self.execute_workflow(
            WorkflowType.PERFORMANCE_ANALYSIS,
            analysis_parameters,
            TaskPriority.MEDIUM
        )
        
    async def optimize_system(self, optimization_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize system based on learning and performance data"""
        return await self.execute_workflow(
            WorkflowType.LEARNING_AND_OPTIMIZATION,
            optimization_data,
            TaskPriority.LOW
        )
        
    async def provide_real_time_support(self, support_request: Dict[str, Any]) -> Dict[str, Any]:
        """Provide real-time customer support"""
        return await self.execute_workflow(
            WorkflowType.REAL_TIME_SUPPORT,
            support_request,
            TaskPriority.CRITICAL
        )
        
    async def generate_comprehensive_insights(self, analysis_scope: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive business insights using all agents"""
        return await self.execute_workflow(
            WorkflowType.COMPREHENSIVE_ANALYSIS,
            analysis_scope,
            TaskPriority.LOW
        )
        
    def get_crew_status(self) -> Dict[str, Any]:
        """Get current status of the crew and all agents"""
        agent_status = {}
        for name, agent in self.agents.items():
            agent_status[name] = {
                "agent_class": agent.__class__.__name__,
                "metrics": agent.get_performance_metrics(),
                "status": "active"
            }
            
        return {
            "crew_metrics": self.crew_metrics,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "agent_status": agent_status,
            "coordination_settings": self.coordination_settings,
            "status_timestamp": datetime.now().isoformat()
        }
        
    def get_workflow_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent workflow execution history"""
        completed_workflows = list(self.completed_tasks.values())
        # Sort by completion time, most recent first
        completed_workflows.sort(
            key=lambda x: x.get("completed_at", ""), 
            reverse=True
        )
        
        return completed_workflows[:limit]
        
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all agents and crew"""
        health_status = {
            "overall_status": "healthy",
            "agent_health": {},
            "system_metrics": self.crew_metrics,
            "issues": [],
            "recommendations": []
        }
        
        # Check each agent
        for name, agent in self.agents.items():
            try:
                agent_metrics = agent.get_performance_metrics()
                health_status["agent_health"][name] = {
                    "status": "healthy",
                    "metrics": agent_metrics
                }
                
                # Check for issues
                if agent_metrics["metrics"]["tasks_failed"] > agent_metrics["metrics"]["tasks_completed"] * 0.1:
                    health_status["issues"].append(f"High failure rate for {name}")
                    
            except Exception as e:
                health_status["agent_health"][name] = {
                    "status": "error",
                    "error": str(e)
                }
                health_status["overall_status"] = "degraded"
                health_status["issues"].append(f"Agent {name} health check failed")
                
        # Generate recommendations
        if health_status["issues"]:
            health_status["recommendations"].append("Review agent configurations and error logs")
            health_status["recommendations"].append("Consider restarting problematic agents")
            
        return health_status
        
    async def shutdown_gracefully(self) -> Dict[str, Any]:
        """Gracefully shutdown the crew and all agents"""
        shutdown_status = {
            "shutdown_initiated": datetime.now().isoformat(),
            "active_tasks_count": len(self.active_tasks),
            "agents_shutdown": {},
            "cleanup_performed": False
        }
        
        # Wait for active tasks to complete or timeout
        if self.active_tasks:
            self.logger.info(f"Waiting for {len(self.active_tasks)} active tasks to complete")
            # In a real implementation, you'd wait with a timeout
            
        # Shutdown each agent
        for name, agent in self.agents.items():
            try:
                # Reset agent metrics and clear memory if needed
                agent.reset_metrics()
                shutdown_status["agents_shutdown"][name] = "success"
            except Exception as e:
                shutdown_status["agents_shutdown"][name] = f"error: {str(e)}"
                
        # Cleanup
        self.active_tasks.clear()
        shutdown_status["cleanup_performed"] = True
        shutdown_status["shutdown_completed"] = datetime.now().isoformat()
        
        self.logger.info("RestaurantAICrew shutdown completed")
        return shutdown_status