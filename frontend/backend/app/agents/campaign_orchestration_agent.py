"""
Campaign Orchestration Agent - Manages bulk messaging campaigns and coordination
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid
from enum import Enum
from .base_agent import BaseRestaurantAgent
from .tools import WhatsAppTool, DatabaseTool, AnalyticsTool


class CampaignStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class CampaignOrchestrationAgent(BaseRestaurantAgent):
    """
    Specialized agent for orchestrating and managing bulk messaging campaigns.
    Coordinates with other agents to execute personalized, timed campaigns at scale.
    """
    
    def __init__(self):
        super().__init__(
            role="Campaign Management Director",
            goal="Execute perfectly timed, personalized campaigns that maximize engagement while coordinating multiple agents and managing resources efficiently",
            backstory="""You are a campaign orchestration expert with extensive experience in large-scale messaging operations. 
            You excel at coordinating complex multi-agent workflows, managing campaign lifecycles, and ensuring optimal resource utilization. 
            Your expertise includes real-time campaign monitoring, dynamic adjustments, and seamless integration with cultural and timing considerations. 
            You ensure every campaign runs smoothly while maintaining high personalization standards and respecting rate limits.""",
            tools=[
                WhatsAppTool(),
                DatabaseTool(),
                AnalyticsTool()
            ],
            verbose=True,
            allow_delegation=True,  # Can delegate to other agents
            max_iter=5
        )
        
        # Campaign types and their configurations
        self.campaign_types = {
            "feedback_request": {
                "priority": "medium",
                "max_batch_size": 100,
                "retry_attempts": 2,
                "response_tracking": True,
                "personalization_level": "high"
            },
            "promotional": {
                "priority": "low",
                "max_batch_size": 500,
                "retry_attempts": 1,
                "response_tracking": False,
                "personalization_level": "medium"
            },
            "service_recovery": {
                "priority": "high",
                "max_batch_size": 50,
                "retry_attempts": 3,
                "response_tracking": True,
                "personalization_level": "high"
            },
            "birthday_greeting": {
                "priority": "medium",
                "max_batch_size": 200,
                "retry_attempts": 1,
                "response_tracking": False,
                "personalization_level": "high"
            },
            "re_engagement": {
                "priority": "medium",
                "max_batch_size": 300,
                "retry_attempts": 2,
                "response_tracking": True,
                "personalization_level": "high"
            }
        }
        
        # Active campaigns tracking
        self.active_campaigns = {}
        
        # Rate limiting settings
        self.rate_limits = {
            "messages_per_minute": 20,
            "messages_per_hour": 1000,
            "messages_per_day": 10000,
            "concurrent_campaigns": 5
        }
        
    def create_campaign(self, campaign_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new campaign with configuration validation
        """
        self.log_task_start("create_campaign", {
            "campaign_type": campaign_config.get("type")
        })
        
        try:
            # Generate unique campaign ID
            campaign_id = str(uuid.uuid4())
            
            # Validate campaign configuration
            validation_result = self._validate_campaign_config(campaign_config)
            if not validation_result["is_valid"]:
                return {
                    "success": False,
                    "error": "Campaign validation failed",
                    "validation_errors": validation_result["errors"]
                }
            
            # Initialize campaign structure
            campaign = {
                "id": campaign_id,
                "status": CampaignStatus.DRAFT,
                "config": campaign_config,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "target_customers": [],
                "message_variants": {},
                "schedule": {},
                "performance": {
                    "total_targeted": 0,
                    "messages_sent": 0,
                    "messages_delivered": 0,
                    "messages_failed": 0,
                    "responses_received": 0,
                    "engagement_rate": 0.0
                },
                "agent_coordination": {
                    "segmentation_agent_used": False,
                    "timing_agent_used": False,
                    "message_composer_used": False,
                    "cultural_agent_used": False
                }
            }
            
            # Store campaign
            self.active_campaigns[campaign_id] = campaign
            
            # Get campaign type configuration
            campaign_type = campaign_config.get("type", "feedback_request")
            type_config = self.campaign_types.get(campaign_type, self.campaign_types["feedback_request"])
            
            result = {
                "success": True,
                "campaign_id": campaign_id,
                "campaign_status": CampaignStatus.DRAFT,
                "type_configuration": type_config,
                "next_steps": [
                    "Define target audience",
                    "Create message variants",
                    "Schedule campaign timing",
                    "Review and launch"
                ]
            }
            
            self.log_task_complete("create_campaign", result)
            return result
            
        except Exception as e:
            self.log_task_error("create_campaign", e)
            raise
            
    def execute_campaign(self, campaign_id: str, execution_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a prepared campaign with full orchestration
        """
        self.log_task_start("execute_campaign", {"campaign_id": campaign_id})
        
        try:
            # Get campaign
            campaign = self.active_campaigns.get(campaign_id)
            if not campaign:
                return {"success": False, "error": "Campaign not found"}
            
            if campaign["status"] != CampaignStatus.SCHEDULED:
                return {"success": False, "error": f"Campaign status is {campaign['status']}, expected SCHEDULED"}
            
            # Update status
            campaign["status"] = CampaignStatus.RUNNING
            campaign["execution_started_at"] = datetime.now().isoformat()
            
            # Execute campaign phases
            execution_results = {
                "campaign_id": campaign_id,
                "execution_phases": [],
                "total_messages_sent": 0,
                "successful_sends": 0,
                "failed_sends": 0,
                "agent_coordination_results": {}
            }
            
            # Phase 1: Final validation and preparation
            prep_result = self._prepare_campaign_execution(campaign)
            execution_results["execution_phases"].append(prep_result)
            
            if not prep_result["success"]:
                campaign["status"] = CampaignStatus.FAILED
                return {"success": False, "error": "Campaign preparation failed", "details": prep_result}
            
            # Phase 2: Agent coordination
            coordination_result = self._coordinate_agent_tasks(campaign)
            execution_results["agent_coordination_results"] = coordination_result
            execution_results["execution_phases"].append(coordination_result)
            
            # Phase 3: Message execution
            if coordination_result["success"]:
                message_execution_result = self._execute_message_delivery(campaign)
                execution_results["execution_phases"].append(message_execution_result)
                execution_results["total_messages_sent"] = message_execution_result.get("messages_sent", 0)
                execution_results["successful_sends"] = message_execution_result.get("successful_sends", 0)
                execution_results["failed_sends"] = message_execution_result.get("failed_sends", 0)
            
            # Phase 4: Post-execution setup
            monitoring_result = self._setup_campaign_monitoring(campaign)
            execution_results["execution_phases"].append(monitoring_result)
            
            # Update campaign status
            if execution_results["total_messages_sent"] > 0:
                campaign["status"] = CampaignStatus.RUNNING
            else:
                campaign["status"] = CampaignStatus.FAILED
            
            campaign["updated_at"] = datetime.now().isoformat()
            
            result = {
                "success": True,
                "campaign_id": campaign_id,
                "execution_results": execution_results,
                "campaign_status": campaign["status"],
                "monitoring_enabled": monitoring_result.get("success", False)
            }
            
            self.log_task_complete("execute_campaign", result)
            return result
            
        except Exception as e:
            # Update campaign status to failed
            if campaign_id in self.active_campaigns:
                self.active_campaigns[campaign_id]["status"] = CampaignStatus.FAILED
            
            self.log_task_error("execute_campaign", e)
            raise
            
    def monitor_campaign_performance(self, campaign_id: str) -> Dict[str, Any]:
        """
        Monitor campaign performance and provide real-time insights
        """
        self.log_task_start("monitor_campaign_performance", {"campaign_id": campaign_id})
        
        try:
            campaign = self.active_campaigns.get(campaign_id)
            if not campaign:
                return {"success": False, "error": "Campaign not found"}
            
            # Gather performance metrics
            current_metrics = self._gather_campaign_metrics(campaign)
            
            # Analyze performance trends
            performance_analysis = self._analyze_campaign_performance(campaign, current_metrics)
            
            # Generate insights and recommendations
            insights = self._generate_performance_insights(campaign, current_metrics, performance_analysis)
            
            # Check for necessary adjustments
            adjustment_recommendations = self._check_for_campaign_adjustments(campaign, current_metrics)
            
            # Update campaign performance data
            campaign["performance"] = current_metrics
            campaign["last_monitored_at"] = datetime.now().isoformat()
            campaign["updated_at"] = datetime.now().isoformat()
            
            result = {
                "campaign_id": campaign_id,
                "campaign_status": campaign["status"],
                "current_metrics": current_metrics,
                "performance_analysis": performance_analysis,
                "insights": insights,
                "adjustment_recommendations": adjustment_recommendations,
                "monitoring_timestamp": datetime.now().isoformat()
            }
            
            self.log_task_complete("monitor_campaign_performance", result)
            return result
            
        except Exception as e:
            self.log_task_error("monitor_campaign_performance", e)
            raise
            
    def pause_campaign(self, campaign_id: str, reason: str = "") -> Dict[str, Any]:
        """
        Pause an active campaign
        """
        self.log_task_start("pause_campaign", {"campaign_id": campaign_id, "reason": reason})
        
        try:
            campaign = self.active_campaigns.get(campaign_id)
            if not campaign:
                return {"success": False, "error": "Campaign not found"}
            
            if campaign["status"] != CampaignStatus.RUNNING:
                return {"success": False, "error": f"Cannot pause campaign with status: {campaign['status']}"}
            
            # Stop message sending
            pause_result = self._pause_message_delivery(campaign)
            
            # Update campaign status
            campaign["status"] = CampaignStatus.PAUSED
            campaign["paused_at"] = datetime.now().isoformat()
            campaign["pause_reason"] = reason
            campaign["updated_at"] = datetime.now().isoformat()
            
            result = {
                "success": True,
                "campaign_id": campaign_id,
                "new_status": CampaignStatus.PAUSED,
                "pause_result": pause_result,
                "paused_at": campaign["paused_at"]
            }
            
            self.log_task_complete("pause_campaign", result)
            return result
            
        except Exception as e:
            self.log_task_error("pause_campaign", e)
            raise
            
    def resume_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """
        Resume a paused campaign
        """
        self.log_task_start("resume_campaign", {"campaign_id": campaign_id})
        
        try:
            campaign = self.active_campaigns.get(campaign_id)
            if not campaign:
                return {"success": False, "error": "Campaign not found"}
            
            if campaign["status"] != CampaignStatus.PAUSED:
                return {"success": False, "error": f"Cannot resume campaign with status: {campaign['status']}"}
            
            # Resume message delivery
            resume_result = self._resume_message_delivery(campaign)
            
            # Update campaign status
            campaign["status"] = CampaignStatus.RUNNING
            campaign["resumed_at"] = datetime.now().isoformat()
            campaign["updated_at"] = datetime.now().isoformat()
            
            result = {
                "success": True,
                "campaign_id": campaign_id,
                "new_status": CampaignStatus.RUNNING,
                "resume_result": resume_result,
                "resumed_at": campaign["resumed_at"]
            }
            
            self.log_task_complete("resume_campaign", result)
            return result
            
        except Exception as e:
            self.log_task_error("resume_campaign", e)
            raise
            
    def manage_concurrent_campaigns(self) -> Dict[str, Any]:
        """
        Manage multiple concurrent campaigns and resource allocation
        """
        self.log_task_start("manage_concurrent_campaigns")
        
        try:
            # Get all active campaigns
            active_campaigns = {
                cid: campaign for cid, campaign in self.active_campaigns.items()
                if campaign["status"] in [CampaignStatus.RUNNING, CampaignStatus.SCHEDULED]
            }
            
            # Resource allocation analysis
            resource_analysis = self._analyze_resource_requirements(active_campaigns)
            
            # Priority management
            priority_adjustments = self._manage_campaign_priorities(active_campaigns, resource_analysis)
            
            # Rate limit distribution
            rate_limit_allocation = self._allocate_rate_limits(active_campaigns, resource_analysis)
            
            # Conflict resolution
            conflict_resolutions = self._resolve_campaign_conflicts(active_campaigns)
            
            # Generate management recommendations
            management_recommendations = self._generate_management_recommendations(
                active_campaigns, resource_analysis, priority_adjustments
            )
            
            result = {
                "active_campaign_count": len(active_campaigns),
                "resource_analysis": resource_analysis,
                "priority_adjustments": priority_adjustments,
                "rate_limit_allocation": rate_limit_allocation,
                "conflict_resolutions": conflict_resolutions,
                "management_recommendations": management_recommendations,
                "system_capacity_usage": self._calculate_system_capacity_usage()
            }
            
            self.log_task_complete("manage_concurrent_campaigns", result)
            return result
            
        except Exception as e:
            self.log_task_error("manage_concurrent_campaigns", e)
            raise
            
    def optimize_campaign_delivery(self, campaign_id: str) -> Dict[str, Any]:
        """
        Optimize campaign delivery based on real-time performance
        """
        self.log_task_start("optimize_campaign_delivery", {"campaign_id": campaign_id})
        
        try:
            campaign = self.active_campaigns.get(campaign_id)
            if not campaign:
                return {"success": False, "error": "Campaign not found"}
            
            # Analyze current performance
            current_performance = self._gather_campaign_metrics(campaign)
            
            # Identify optimization opportunities
            optimization_opportunities = self._identify_optimization_opportunities(campaign, current_performance)
            
            # Apply optimizations
            optimization_results = []
            
            for opportunity in optimization_opportunities:
                if opportunity["type"] == "timing_adjustment":
                    result = self._optimize_message_timing(campaign, opportunity)
                elif opportunity["type"] == "message_variant_adjustment":
                    result = self._optimize_message_variants(campaign, opportunity)
                elif opportunity["type"] == "audience_refinement":
                    result = self._optimize_target_audience(campaign, opportunity)
                elif opportunity["type"] == "rate_adjustment":
                    result = self._optimize_delivery_rate(campaign, opportunity)
                else:
                    result = {"type": opportunity["type"], "applied": False, "reason": "Unknown optimization type"}
                
                optimization_results.append(result)
            
            # Update campaign with optimizations
            campaign["optimization_applied"] = True
            campaign["last_optimized_at"] = datetime.now().isoformat()
            campaign["updated_at"] = datetime.now().isoformat()
            
            result = {
                "success": True,
                "campaign_id": campaign_id,
                "optimization_opportunities": len(optimization_opportunities),
                "optimizations_applied": len([r for r in optimization_results if r.get("applied")]),
                "optimization_results": optimization_results,
                "estimated_performance_improvement": self._estimate_performance_improvement(optimization_results)
            }
            
            self.log_task_complete("optimize_campaign_delivery", result)
            return result
            
        except Exception as e:
            self.log_task_error("optimize_campaign_delivery", e)
            raise
            
    # Private helper methods
    def _validate_campaign_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate campaign configuration"""
        errors = []
        warnings = []
        
        # Required fields
        required_fields = ["type", "name", "target_criteria", "message_template"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")
        
        # Campaign type validation
        if "type" in config and config["type"] not in self.campaign_types:
            errors.append(f"Invalid campaign type: {config['type']}")
        
        # Target criteria validation
        if "target_criteria" in config:
            criteria = config["target_criteria"]
            if not isinstance(criteria, dict):
                errors.append("target_criteria must be a dictionary")
            elif not criteria:
                errors.append("target_criteria cannot be empty")
        
        # Message template validation
        if "message_template" in config:
            template = config["message_template"]
            if not isinstance(template, str) or not template.strip():
                errors.append("message_template must be a non-empty string")
        
        # Schedule validation
        if "schedule" in config:
            schedule = config["schedule"]
            if "send_time" in schedule:
                try:
                    datetime.fromisoformat(schedule["send_time"])
                except ValueError:
                    errors.append("Invalid send_time format in schedule")
        
        # A/B testing validation
        if "ab_testing" in config:
            ab_config = config["ab_testing"]
            if "enabled" in ab_config and ab_config["enabled"]:
                if "variants" not in ab_config or len(ab_config["variants"]) < 2:
                    errors.append("A/B testing requires at least 2 variants")
        
        # Resource constraints
        estimated_size = config.get("estimated_target_size", 0)
        campaign_type = config.get("type", "feedback_request")
        max_batch_size = self.campaign_types.get(campaign_type, {}).get("max_batch_size", 100)
        
        if estimated_size > max_batch_size:
            warnings.append(f"Target size ({estimated_size}) exceeds recommended max for {campaign_type} ({max_batch_size})")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
        
    def _prepare_campaign_execution(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare campaign for execution"""
        try:
            preparation_steps = []
            
            # Validate target audience
            target_validation = self._validate_target_audience(campaign)
            preparation_steps.append(target_validation)
            
            if not target_validation["success"]:
                return {"success": False, "error": "Target audience validation failed", "steps": preparation_steps}
            
            # Prepare message variants
            message_prep = self._prepare_message_variants(campaign)
            preparation_steps.append(message_prep)
            
            if not message_prep["success"]:
                return {"success": False, "error": "Message preparation failed", "steps": preparation_steps}
            
            # Validate rate limits
            rate_limit_check = self._validate_rate_limits(campaign)
            preparation_steps.append(rate_limit_check)
            
            if not rate_limit_check["success"]:
                return {"success": False, "error": "Rate limit validation failed", "steps": preparation_steps}
            
            return {
                "success": True,
                "preparation_steps": preparation_steps,
                "ready_for_execution": True
            }
            
        except Exception as e:
            return {"success": False, "error": f"Preparation failed: {str(e)}"}
            
    def _coordinate_agent_tasks(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate tasks with other agents"""
        coordination_results = {
            "success": True,
            "agent_tasks": {},
            "coordination_errors": []
        }
        
        try:
            # Delegate to Customer Segmentation Agent if needed
            if campaign["config"].get("use_dynamic_segmentation", False):
                segmentation_result = self._delegate_customer_segmentation(campaign)
                coordination_results["agent_tasks"]["segmentation"] = segmentation_result
                campaign["agent_coordination"]["segmentation_agent_used"] = True
                
                if not segmentation_result.get("success"):
                    coordination_results["coordination_errors"].append("Segmentation agent task failed")
            
            # Delegate to Timing Optimization Agent
            timing_result = self._delegate_timing_optimization(campaign)
            coordination_results["agent_tasks"]["timing"] = timing_result
            campaign["agent_coordination"]["timing_agent_used"] = True
            
            if not timing_result.get("success"):
                coordination_results["coordination_errors"].append("Timing optimization failed")
            
            # Delegate to Message Composer Agent
            message_result = self._delegate_message_composition(campaign)
            coordination_results["agent_tasks"]["message_composition"] = message_result
            campaign["agent_coordination"]["message_composer_used"] = True
            
            if not message_result.get("success"):
                coordination_results["coordination_errors"].append("Message composition failed")
            
            # Delegate to Cultural Communication Agent if needed
            if self._requires_cultural_validation(campaign):
                cultural_result = self._delegate_cultural_validation(campaign)
                coordination_results["agent_tasks"]["cultural_validation"] = cultural_result
                campaign["agent_coordination"]["cultural_agent_used"] = True
                
                if not cultural_result.get("success"):
                    coordination_results["coordination_errors"].append("Cultural validation failed")
            
            # Overall success check
            if coordination_results["coordination_errors"]:
                coordination_results["success"] = False
            
            return coordination_results
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Agent coordination failed: {str(e)}",
                "coordination_errors": [str(e)]
            }
            
    def _execute_message_delivery(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the actual message delivery"""
        delivery_results = {
            "messages_sent": 0,
            "successful_sends": 0,
            "failed_sends": 0,
            "delivery_log": [],
            "rate_limit_hits": 0
        }
        
        try:
            # Get finalized message schedule
            schedule = campaign.get("schedule", {})
            target_customers = campaign.get("target_customers", [])
            
            if not target_customers:
                return {"success": False, "error": "No target customers defined", **delivery_results}
            
            # Execute sends in batches
            batch_size = self._calculate_optimal_batch_size(campaign)
            
            for i in range(0, len(target_customers), batch_size):
                batch = target_customers[i:i + batch_size]
                batch_result = self._send_message_batch(campaign, batch)
                
                delivery_results["messages_sent"] += batch_result["messages_sent"]
                delivery_results["successful_sends"] += batch_result["successful_sends"]
                delivery_results["failed_sends"] += batch_result["failed_sends"]
                delivery_results["rate_limit_hits"] += batch_result.get("rate_limit_hits", 0)
                delivery_results["delivery_log"].extend(batch_result.get("delivery_log", []))
                
                # Check for campaign pause/stop
                if campaign["status"] != CampaignStatus.RUNNING:
                    break
                
                # Rate limiting pause
                if batch_result.get("rate_limit_hits", 0) > 0:
                    # Wait before next batch
                    import time
                    time.sleep(60)  # Wait 1 minute
            
            # Update campaign performance
            campaign["performance"]["messages_sent"] = delivery_results["messages_sent"]
            campaign["performance"]["total_targeted"] = len(target_customers)
            
            return {
                "success": True,
                **delivery_results
            }
            
        except Exception as e:
            return {"success": False, "error": f"Message delivery failed: {str(e)}", **delivery_results}
            
    def _setup_campaign_monitoring(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """Setup monitoring for the campaign"""
        try:
            monitoring_config = {
                "campaign_id": campaign["id"],
                "monitoring_frequency": "5_minutes",
                "metrics_to_track": [
                    "delivery_rate",
                    "response_rate",
                    "engagement_rate",
                    "failure_rate"
                ],
                "alert_thresholds": {
                    "failure_rate": 0.1,  # 10% failure rate
                    "response_rate": 0.05  # 5% response rate minimum
                },
                "monitoring_duration_hours": 48
            }
            
            # Start monitoring (would integrate with actual monitoring system)
            campaign["monitoring_config"] = monitoring_config
            campaign["monitoring_started_at"] = datetime.now().isoformat()
            
            return {
                "success": True,
                "monitoring_config": monitoring_config,
                "monitoring_started": True
            }
            
        except Exception as e:
            return {"success": False, "error": f"Monitoring setup failed: {str(e)}"}
            
    def _gather_campaign_metrics(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """Gather current campaign metrics"""
        # This would integrate with actual analytics systems
        # For now, return mock metrics based on campaign data
        
        performance = campaign.get("performance", {})
        
        metrics = {
            "total_targeted": performance.get("total_targeted", 0),
            "messages_sent": performance.get("messages_sent", 0),
            "messages_delivered": performance.get("messages_delivered", performance.get("messages_sent", 0) * 0.95),  # 95% delivery rate
            "messages_failed": performance.get("messages_failed", performance.get("messages_sent", 0) * 0.05),
            "responses_received": performance.get("responses_received", performance.get("messages_sent", 0) * 0.3),  # 30% response rate
            "delivery_rate": 0.95,
            "response_rate": 0.30,
            "engagement_rate": 0.25,
            "failure_rate": 0.05,
            "cost_per_message": 0.05,
            "total_cost": performance.get("messages_sent", 0) * 0.05,
            "last_updated": datetime.now().isoformat()
        }
        
        # Calculate derived metrics
        if metrics["messages_sent"] > 0:
            metrics["delivery_rate"] = metrics["messages_delivered"] / metrics["messages_sent"]
            metrics["response_rate"] = metrics["responses_received"] / metrics["messages_sent"]
            metrics["failure_rate"] = metrics["messages_failed"] / metrics["messages_sent"]
        
        return metrics
        
    def _analyze_campaign_performance(self, campaign: Dict[str, Any], current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze campaign performance trends"""
        
        analysis = {
            "performance_status": "good",
            "trend_direction": "stable",
            "key_insights": [],
            "areas_for_improvement": [],
            "strengths": []
        }
        
        # Delivery rate analysis
        delivery_rate = current_metrics.get("delivery_rate", 0)
        if delivery_rate >= 0.95:
            analysis["strengths"].append("Excellent delivery rate")
        elif delivery_rate < 0.8:
            analysis["areas_for_improvement"].append("Low delivery rate needs investigation")
            analysis["performance_status"] = "needs_attention"
        
        # Response rate analysis
        response_rate = current_metrics.get("response_rate", 0)
        campaign_type = campaign["config"].get("type", "feedback_request")
        
        expected_response_rates = {
            "feedback_request": 0.25,
            "promotional": 0.15,
            "service_recovery": 0.40,
            "birthday_greeting": 0.20,
            "re_engagement": 0.30
        }
        
        expected_rate = expected_response_rates.get(campaign_type, 0.25)
        
        if response_rate >= expected_rate * 1.2:
            analysis["strengths"].append(f"Response rate ({response_rate:.1%}) exceeds expectations")
            analysis["performance_status"] = "excellent"
        elif response_rate < expected_rate * 0.8:
            analysis["areas_for_improvement"].append(f"Response rate ({response_rate:.1%}) below expectations")
            analysis["performance_status"] = "needs_attention"
        
        # Generate insights
        if current_metrics.get("messages_sent", 0) > 0:
            analysis["key_insights"].append(f"Campaign has reached {current_metrics['messages_sent']} customers")
            
        if len(analysis["areas_for_improvement"]) == 0:
            analysis["key_insights"].append("Campaign performing within expected parameters")
        
        return analysis
        
    def _generate_performance_insights(self, 
                                     campaign: Dict[str, Any], 
                                     metrics: Dict[str, Any], 
                                     analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable performance insights"""
        insights = []
        
        # Time-based insights
        created_at = datetime.fromisoformat(campaign["created_at"])
        hours_running = (datetime.now() - created_at).total_seconds() / 3600
        
        if hours_running < 2:
            insights.append("Campaign is in early stages - performance data is preliminary")
        elif hours_running > 48:
            insights.append("Campaign has been running for extended period - consider reviewing effectiveness")
        
        # Performance insights
        if analysis["performance_status"] == "excellent":
            insights.append("Campaign is performing exceptionally well - consider scaling similar campaigns")
        elif analysis["performance_status"] == "needs_attention":
            insights.append("Campaign performance requires attention - review targeting and messaging")
        
        # Cost insights
        total_cost = metrics.get("total_cost", 0)
        responses = metrics.get("responses_received", 0)
        
        if responses > 0:
            cost_per_response = total_cost / responses
            insights.append(f"Cost per response: ${cost_per_response:.2f}")
            
            if cost_per_response < 1.0:
                insights.append("Excellent cost efficiency - campaign is highly profitable")
            elif cost_per_response > 5.0:
                insights.append("High cost per response - consider optimizing targeting")
        
        return insights
        
    def _check_for_campaign_adjustments(self, campaign: Dict[str, Any], metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check if campaign needs adjustments"""
        recommendations = []
        
        # Failure rate check
        failure_rate = metrics.get("failure_rate", 0)
        if failure_rate > 0.1:  # 10%
            recommendations.append({
                "type": "urgent",
                "action": "investigate_delivery_issues",
                "reason": f"High failure rate: {failure_rate:.1%}",
                "priority": "high"
            })
        
        # Response rate check
        response_rate = metrics.get("response_rate", 0)
        if response_rate < 0.1:  # 10%
            recommendations.append({
                "type": "optimization",
                "action": "review_message_content",
                "reason": f"Low response rate: {response_rate:.1%}",
                "priority": "medium"
            })
        
        # Rate limiting check
        if campaign.get("rate_limit_hits", 0) > 5:
            recommendations.append({
                "type": "adjustment",
                "action": "reduce_sending_rate",
                "reason": "Multiple rate limit hits detected",
                "priority": "medium"
            })
        
        return recommendations
        
    def _pause_message_delivery(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """Pause message delivery for campaign"""
        try:
            # Stop any scheduled sends
            paused_sends = self._cancel_scheduled_sends(campaign)
            
            return {
                "success": True,
                "paused_scheduled_sends": paused_sends,
                "pause_timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def _resume_message_delivery(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """Resume message delivery for paused campaign"""
        try:
            # Reschedule remaining sends
            rescheduled_sends = self._reschedule_remaining_sends(campaign)
            
            return {
                "success": True,
                "rescheduled_sends": rescheduled_sends,
                "resume_timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def _validate_target_audience(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """Validate target audience for campaign"""
        try:
            target_criteria = campaign["config"].get("target_criteria", {})
            
            # Mock validation - would integrate with actual customer database
            estimated_size = target_criteria.get("estimated_size", 0)
            
            if estimated_size == 0:
                return {"success": False, "error": "No customers match target criteria"}
            
            if estimated_size > 10000:
                return {"success": False, "error": "Target audience too large for single campaign"}
            
            return {
                "success": True,
                "target_size": estimated_size,
                "validation_passed": True
            }
            
        except Exception as e:
            return {"success": False, "error": f"Target validation failed: {str(e)}"}
            
    def _prepare_message_variants(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare message variants for campaign"""
        try:
            message_template = campaign["config"].get("message_template", "")
            ab_testing = campaign["config"].get("ab_testing", {})
            
            variants = {"default": message_template}
            
            # Add A/B test variants if configured
            if ab_testing.get("enabled", False):
                for i, variant in enumerate(ab_testing.get("variants", [])):
                    variants[f"variant_{i+1}"] = variant
            
            campaign["message_variants"] = variants
            
            return {
                "success": True,
                "variants_prepared": len(variants),
                "variants": list(variants.keys())
            }
            
        except Exception as e:
            return {"success": False, "error": f"Message preparation failed: {str(e)}"}
            
    def _validate_rate_limits(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """Validate campaign against rate limits"""
        try:
            target_size = len(campaign.get("target_customers", []))
            
            # Check against daily limits
            if target_size > self.rate_limits["messages_per_day"]:
                return {
                    "success": False,
                    "error": f"Campaign size ({target_size}) exceeds daily limit ({self.rate_limits['messages_per_day']})"
                }
            
            # Check concurrent campaign limits
            active_count = len([c for c in self.active_campaigns.values() 
                               if c["status"] == CampaignStatus.RUNNING])
            
            if active_count >= self.rate_limits["concurrent_campaigns"]:
                return {
                    "success": False,
                    "error": f"Too many concurrent campaigns ({active_count})"
                }
            
            return {
                "success": True,
                "rate_limit_validation_passed": True
            }
            
        except Exception as e:
            return {"success": False, "error": f"Rate limit validation failed: {str(e)}"}
            
    # Mock delegation methods (would integrate with actual agents)
    def _delegate_customer_segmentation(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to Customer Segmentation Agent"""
        return {"success": True, "segmentation_completed": True, "refined_audience": True}
        
    def _delegate_timing_optimization(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to Timing Optimization Agent"""
        return {"success": True, "timing_optimized": True, "schedule_created": True}
        
    def _delegate_message_composition(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to Message Composer Agent"""
        return {"success": True, "messages_personalized": True, "variants_created": True}
        
    def _delegate_cultural_validation(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to Cultural Communication Agent"""
        return {"success": True, "cultural_validation_passed": True, "messages_appropriate": True}
        
    def _requires_cultural_validation(self, campaign: Dict[str, Any]) -> bool:
        """Check if campaign requires cultural validation"""
        # Check if targeting Arabic-speaking customers
        target_criteria = campaign["config"].get("target_criteria", {})
        return target_criteria.get("language") == "ar" or target_criteria.get("cultural_sensitivity", False)
        
    def _calculate_optimal_batch_size(self, campaign: Dict[str, Any]) -> int:
        """Calculate optimal batch size for message delivery"""
        campaign_type = campaign["config"].get("type", "feedback_request")
        base_batch_size = self.campaign_types.get(campaign_type, {}).get("max_batch_size", 100)
        
        # Adjust based on system load and priority
        priority = self.campaign_types.get(campaign_type, {}).get("priority", "medium")
        
        if priority == "high":
            return min(base_batch_size, 50)  # Smaller batches for high priority
        elif priority == "low":
            return min(base_batch_size, 200)  # Larger batches for low priority
        
        return min(base_batch_size, 100)
        
    def _send_message_batch(self, campaign: Dict[str, Any], batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send a batch of messages"""
        # Mock implementation - would integrate with actual WhatsApp API
        batch_results = {
            "messages_sent": len(batch),
            "successful_sends": int(len(batch) * 0.95),  # 95% success rate
            "failed_sends": int(len(batch) * 0.05),      # 5% failure rate
            "delivery_log": [],
            "rate_limit_hits": 0
        }
        
        # Simulate some delivery logs
        for i, customer in enumerate(batch):
            success = i < batch_results["successful_sends"]
            batch_results["delivery_log"].append({
                "customer_id": customer.get("id"),
                "status": "sent" if success else "failed",
                "timestamp": datetime.now().isoformat(),
                "message_id": f"msg_{campaign['id']}_{i}"
            })
        
        return batch_results
        
    def _analyze_resource_requirements(self, campaigns: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze resource requirements for active campaigns"""
        total_messages = sum(
            len(campaign.get("target_customers", [])) 
            for campaign in campaigns.values()
        )
        
        return {
            "total_campaigns": len(campaigns),
            "total_messages_pending": total_messages,
            "estimated_api_calls": total_messages * 1.2,  # Including retries
            "estimated_completion_time_hours": total_messages / self.rate_limits["messages_per_hour"],
            "resource_utilization": min(total_messages / self.rate_limits["messages_per_day"], 1.0)
        }
        
    def _manage_campaign_priorities(self, 
                                  campaigns: Dict[str, Dict[str, Any]], 
                                  resource_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Manage campaign priorities based on resource constraints"""
        adjustments = []
        
        # Sort campaigns by priority
        priority_order = {"high": 3, "medium": 2, "low": 1}
        
        sorted_campaigns = sorted(
            campaigns.items(),
            key=lambda x: priority_order.get(
                self.campaign_types.get(x[1]["config"].get("type", ""), {}).get("priority", "medium"), 
                2
            ),
            reverse=True
        )
        
        # Apply priority-based adjustments if resource constrained
        if resource_analysis["resource_utilization"] > 0.8:
            for campaign_id, campaign in sorted_campaigns:
                campaign_type = campaign["config"].get("type", "feedback_request")
                priority = self.campaign_types.get(campaign_type, {}).get("priority", "medium")
                
                if priority == "low" and resource_analysis["resource_utilization"] > 0.9:
                    adjustments.append({
                        "campaign_id": campaign_id,
                        "action": "delay_execution",
                        "reason": "Resource constraints - low priority campaign delayed"
                    })
        
        return adjustments
        
    def _allocate_rate_limits(self, 
                            campaigns: Dict[str, Dict[str, Any]], 
                            resource_analysis: Dict[str, Any]) -> Dict[str, int]:
        """Allocate rate limits among active campaigns"""
        total_campaigns = len(campaigns)
        if total_campaigns == 0:
            return {}
        
        # Basic equal allocation
        base_allocation = self.rate_limits["messages_per_minute"] // total_campaigns
        
        allocation = {}
        for campaign_id in campaigns:
            allocation[campaign_id] = base_allocation
        
        # Adjust based on priority
        high_priority_campaigns = [
            cid for cid, campaign in campaigns.items()
            if self.campaign_types.get(campaign["config"].get("type", ""), {}).get("priority") == "high"
        ]
        
        # Give high priority campaigns extra allocation
        if high_priority_campaigns:
            extra_per_high = min(5, base_allocation // 2)
            for cid in high_priority_campaigns:
                allocation[cid] += extra_per_high
        
        return allocation
        
    def _resolve_campaign_conflicts(self, campaigns: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Resolve conflicts between concurrent campaigns"""
        conflicts = []
        
        # Check for audience overlap
        campaign_audiences = {}
        for cid, campaign in campaigns.items():
            target_criteria = campaign["config"].get("target_criteria", {})
            campaign_audiences[cid] = target_criteria
        
        # Simple conflict detection (would be more sophisticated in production)
        campaign_ids = list(campaigns.keys())
        for i in range(len(campaign_ids)):
            for j in range(i + 1, len(campaign_ids)):
                cid1, cid2 = campaign_ids[i], campaign_ids[j]
                
                # Check if both targeting same language
                lang1 = campaign_audiences[cid1].get("language")
                lang2 = campaign_audiences[cid2].get("language")
                
                if lang1 == lang2:
                    conflicts.append({
                        "campaign_1": cid1,
                        "campaign_2": cid2,
                        "conflict_type": "audience_overlap",
                        "resolution": "stagger_timing",
                        "severity": "low"
                    })
        
        return conflicts
        
    def _generate_management_recommendations(self, 
                                          campaigns: Dict[str, Dict[str, Any]], 
                                          resource_analysis: Dict[str, Any], 
                                          adjustments: List[Dict[str, Any]]) -> List[str]:
        """Generate management recommendations"""
        recommendations = []
        
        if resource_analysis["resource_utilization"] > 0.9:
            recommendations.append("System is near capacity - consider scheduling campaigns at different times")
        
        if len(campaigns) > 3:
            recommendations.append("Multiple concurrent campaigns - monitor performance closely")
        
        if adjustments:
            recommendations.append(f"{len(adjustments)} campaigns require priority adjustments")
        
        return recommendations
        
    def _calculate_system_capacity_usage(self) -> Dict[str, float]:
        """Calculate current system capacity usage"""
        active_campaigns = len([c for c in self.active_campaigns.values() 
                               if c["status"] == CampaignStatus.RUNNING])
        
        return {
            "campaign_slots_used": active_campaigns / self.rate_limits["concurrent_campaigns"],
            "estimated_message_capacity_used": 0.3,  # Mock value
            "overall_capacity_used": min((active_campaigns / self.rate_limits["concurrent_campaigns"]) * 0.8, 1.0)
        }
        
    def _identify_optimization_opportunities(self, campaign: Dict[str, Any], performance: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify optimization opportunities for campaign"""
        opportunities = []
        
        # Response rate optimization
        if performance.get("response_rate", 0) < 0.2:
            opportunities.append({
                "type": "message_variant_adjustment",
                "description": "Low response rate - test different message variants",
                "potential_improvement": "15-25% increase in engagement",
                "priority": "high"
            })
        
        # Timing optimization
        if performance.get("delivery_rate", 0) < 0.9:
            opportunities.append({
                "type": "timing_adjustment",
                "description": "Poor delivery rate - adjust send timing",
                "potential_improvement": "5-10% improvement in delivery",
                "priority": "medium"
            })
        
        # Audience refinement
        if performance.get("failure_rate", 0) > 0.1:
            opportunities.append({
                "type": "audience_refinement",
                "description": "High failure rate - refine target audience",
                "potential_improvement": "Reduce failures by 50%",
                "priority": "high"
            })
        
        return opportunities
        
    def _optimize_message_timing(self, campaign: Dict[str, Any], opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize message timing for campaign"""
        # Mock optimization
        return {
            "type": "timing_adjustment",
            "applied": True,
            "changes": "Adjusted send times to avoid peak hours",
            "expected_improvement": "10% better delivery rate"
        }
        
    def _optimize_message_variants(self, campaign: Dict[str, Any], opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize message variants"""
        return {
            "type": "message_variant_adjustment",
            "applied": True,
            "changes": "Switched to higher-performing message variant",
            "expected_improvement": "20% increase in response rate"
        }
        
    def _optimize_target_audience(self, campaign: Dict[str, Any], opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize target audience"""
        return {
            "type": "audience_refinement",
            "applied": True,
            "changes": "Filtered out customers with high failure history",
            "expected_improvement": "50% reduction in failures"
        }
        
    def _optimize_delivery_rate(self, campaign: Dict[str, Any], opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize delivery rate"""
        return {
            "type": "rate_adjustment",
            "applied": True,
            "changes": "Reduced send rate to avoid throttling",
            "expected_improvement": "More consistent delivery"
        }
        
    def _estimate_performance_improvement(self, optimization_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Estimate overall performance improvement from optimizations"""
        applied_optimizations = [r for r in optimization_results if r.get("applied")]
        
        return {
            "optimizations_applied": len(applied_optimizations),
            "estimated_response_rate_improvement": "10-30%",
            "estimated_delivery_improvement": "5-15%",
            "confidence": "medium"
        }
        
    # Additional helper methods for campaign lifecycle management
    def _cancel_scheduled_sends(self, campaign: Dict[str, Any]) -> int:
        """Cancel scheduled sends for a campaign"""
        # Mock implementation
        return len(campaign.get("target_customers", [])) // 2  # Half were scheduled
        
    def _reschedule_remaining_sends(self, campaign: Dict[str, Any]) -> int:
        """Reschedule remaining sends for resumed campaign"""
        # Mock implementation
        return len(campaign.get("target_customers", [])) // 3  # One third need rescheduling