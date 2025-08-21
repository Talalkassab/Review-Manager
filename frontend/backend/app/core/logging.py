"""
Centralized logging configuration for the Restaurant AI system.
"""
import logging
import logging.config
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import settings


class AgentFormatter(logging.Formatter):
    """Custom formatter for agent logging with Arabic support."""
    
    def __init__(self):
        super().__init__()
        self.default_format = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "[Agent: %(agent_name)s] [Task: %(task_name)s] - %(message)s"
        )
    
    def format(self, record):
        # Add default values for agent-specific fields if not present
        if not hasattr(record, 'agent_name'):
            record.agent_name = 'Unknown'
        if not hasattr(record, 'task_name'):
            record.task_name = 'Unknown'
        
        formatter = logging.Formatter(self.default_format)
        return formatter.format(record)


class AgentLogger:
    """Enhanced logger for CrewAI agents with structured logging."""
    
    def __init__(self, name: str, agent_name: str = None):
        self.logger = logging.getLogger(name)
        self.agent_name = agent_name or name
        
        # Don't add handlers multiple times
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup console and file handlers."""
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(AgentFormatter())
        console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
        
        # File handler
        log_dir = Path(settings.LOG_FILE).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(
            settings.LOG_FILE, 
            encoding='utf-8'  # Support for Arabic text
        )
        file_handler.setFormatter(AgentFormatter())
        file_handler.setLevel(logging.DEBUG)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.DEBUG)
    
    def _log_with_context(self, level: int, message: str, task_name: str = None, **kwargs):
        """Log message with agent context."""
        extra = {
            'agent_name': self.agent_name,
            'task_name': task_name or 'default',
            **kwargs
        }
        self.logger.log(level, message, extra=extra)
    
    def info(self, message: str, task_name: str = None, **kwargs):
        """Log info message."""
        self._log_with_context(logging.INFO, message, task_name, **kwargs)
    
    def debug(self, message: str, task_name: str = None, **kwargs):
        """Log debug message."""
        self._log_with_context(logging.DEBUG, message, task_name, **kwargs)
    
    def warning(self, message: str, task_name: str = None, **kwargs):
        """Log warning message."""
        self._log_with_context(logging.WARNING, message, task_name, **kwargs)
    
    def error(self, message: str, task_name: str = None, **kwargs):
        """Log error message."""
        self._log_with_context(logging.ERROR, message, task_name, **kwargs)
    
    def critical(self, message: str, task_name: str = None, **kwargs):
        """Log critical message."""
        self._log_with_context(logging.CRITICAL, message, task_name, **kwargs)
    
    def log_agent_start(self, task_description: str):
        """Log when an agent starts a task."""
        self.info(f"Agent {self.agent_name} starting task: {task_description}")
    
    def log_agent_complete(self, task_description: str, result: str = None):
        """Log when an agent completes a task."""
        msg = f"Agent {self.agent_name} completed task: {task_description}"
        if result:
            msg += f" | Result: {result[:200]}..."
        self.info(msg)
    
    def log_agent_error(self, task_description: str, error: Exception):
        """Log when an agent encounters an error."""
        self.error(
            f"Agent {self.agent_name} error in task '{task_description}': {str(error)}"
        )
    
    def log_llm_call(self, model: str, prompt_length: int, response_length: int = None):
        """Log LLM API calls for monitoring."""
        msg = f"LLM call to {model} | Prompt length: {prompt_length}"
        if response_length:
            msg += f" | Response length: {response_length}"
        self.debug(msg, task_name="llm_call")
    
    def log_whatsapp_message(self, phone: str, message_type: str, success: bool):
        """Log WhatsApp message sending attempts."""
        status = "SUCCESS" if success else "FAILED"
        self.info(
            f"WhatsApp {message_type} to {phone[-4:]} - {status}",
            task_name="whatsapp_messaging"
        )
    
    def log_customer_interaction(self, customer_id: str, interaction_type: str, sentiment: float = None):
        """Log customer interactions."""
        msg = f"Customer {customer_id} - {interaction_type}"
        if sentiment is not None:
            msg += f" | Sentiment: {sentiment:.2f}"
        self.info(msg, task_name="customer_interaction")
    
    def log_performance_metric(self, metric_name: str, value: float, threshold: float = None):
        """Log performance metrics."""
        msg = f"Metric {metric_name}: {value:.3f}"
        if threshold:
            status = "ABOVE" if value >= threshold else "BELOW"
            msg += f" | Threshold: {threshold} ({status})"
        self.info(msg, task_name="performance_tracking")


def get_agent_logger(agent_name: str) -> AgentLogger:
    """Factory function to create agent loggers."""
    logger_name = f"restaurant_ai.agents.{agent_name.lower()}"
    return AgentLogger(logger_name, agent_name)


def setup_logging():
    """Initialize the logging system."""
    # Create logs directory
    log_dir = Path(settings.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(settings.LOG_FILE, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set third-party library log levels
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("crewai").setLevel(logging.INFO)
    
    return logging.getLogger("restaurant_ai")


# Initialize logging on import
main_logger = setup_logging()