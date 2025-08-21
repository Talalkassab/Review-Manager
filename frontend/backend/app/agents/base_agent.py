"""
Base Agent class with common functionality for all agents
"""
from crewai import Agent
from typing import List, Dict, Any, Optional
import logging
from ..core.logging import get_agent_logger
from ..core.ai_config import ai_config


class BaseRestaurantAgent(Agent):
    """Base class for all restaurant AI agents with common functionality"""
    
    def __init__(
        self,
        role: str,
        goal: str,
        backstory: str,
        tools: List[Any] = None,
        verbose: bool = True,
        allow_delegation: bool = False,
        max_iter: int = 3,
        memory: bool = True,
        **kwargs
    ):
        """Initialize base agent with common settings"""
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=tools or [],
            verbose=verbose,
            allow_delegation=allow_delegation,
            max_iter=max_iter,
            memory=memory,
            **kwargs
        )
        
        # Set up logging
        self.logger = get_agent_logger(self.__class__.__name__)
        
        # Store AI configuration
        self.ai_config = ai_config
        
        # Performance tracking
        self.metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "average_response_time": 0,
            "total_tokens_used": 0
        }
        
        # Cultural context
        self.cultural_context = ai_config.cultural_context
        
        # Memory storage for learning
        self.knowledge_base = {}
        
    def log_task_start(self, task_name: str, context: Dict[str, Any] = None) -> None:
        """Log the start of a task"""
        self.logger.info(f"Starting task: {task_name}", extra={"context": context})
        
    def log_task_complete(self, task_name: str, result: Any = None) -> None:
        """Log task completion"""
        self.metrics["tasks_completed"] += 1
        self.logger.info(f"Completed task: {task_name}", extra={"result": str(result)[:200]})
        
    def log_task_error(self, task_name: str, error: Exception) -> None:
        """Log task error"""
        self.metrics["tasks_failed"] += 1
        self.logger.error(f"Task failed: {task_name}", exc_info=error)
        
    def update_knowledge(self, key: str, value: Any) -> None:
        """Update agent's knowledge base for learning"""
        self.knowledge_base[key] = value
        self.logger.debug(f"Knowledge updated: {key}")
        
    def get_knowledge(self, key: str, default: Any = None) -> Any:
        """Retrieve from knowledge base"""
        return self.knowledge_base.get(key, default)
        
    def handle_arabic_text(self, text: str) -> Dict[str, Any]:
        """Handle Arabic text with proper encoding and cultural sensitivity"""
        return {
            "text": text,
            "is_arabic": self._detect_arabic(text),
            "needs_cultural_check": True,
            "encoding": "utf-8"
        }
        
    def _detect_arabic(self, text: str) -> bool:
        """Detect if text contains Arabic characters"""
        arabic_chars = set("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
        return any(char in arabic_chars for char in text)
        
    def validate_cultural_appropriateness(self, content: str) -> Dict[str, Any]:
        """Validate content for cultural appropriateness"""
        issues = []
        
        # Check for controversial topics
        for topic in self.cultural_context.avoid_controversial_topics:
            if topic.lower() in content.lower():
                issues.append(f"Contains potentially controversial topic: {topic}")
                
        return {
            "is_appropriate": len(issues) == 0,
            "issues": issues,
            "recommendations": self._get_cultural_recommendations(issues)
        }
        
    def _get_cultural_recommendations(self, issues: List[str]) -> List[str]:
        """Get recommendations for cultural improvements"""
        recommendations = []
        
        if issues:
            recommendations.append("Consider rephrasing to avoid sensitive topics")
            recommendations.append("Use more formal language if addressing elders")
            recommendations.append("Include appropriate religious greetings if suitable")
            
        return recommendations
        
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        return {
            "agent_name": self.__class__.__name__,
            "role": self.role,
            "metrics": self.metrics,
            "knowledge_items": len(self.knowledge_base)
        }
        
    def reset_metrics(self) -> None:
        """Reset performance metrics"""
        self.metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "average_response_time": 0,
            "total_tokens_used": 0
        }