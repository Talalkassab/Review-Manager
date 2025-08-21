"""
Comprehensive logging system for the Restaurant AI Assistant.
Provides structured logging with full traceability for debugging.
"""
import logging
import sys
import json
import traceback
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
from contextlib import contextmanager

import structlog
from loguru import logger
from pythonjsonlogger import jsonlogger

from .config import settings


class RequestContextFilter(logging.Filter):
    """Add request context to log records."""
    
    def filter(self, record):
        # Add request context if available
        record.request_id = getattr(record, 'request_id', 'no-request')
        record.user_id = getattr(record, 'user_id', 'anonymous')
        record.endpoint = getattr(record, 'endpoint', 'unknown')
        return True


class PerformanceLogger:
    """Track performance metrics and slow operations."""
    
    def __init__(self, operation_name: str, threshold_ms: float = 1000.0):
        self.operation_name = operation_name
        self.threshold_ms = threshold_ms
        self.start_time = None
        
    def __enter__(self):
        self.start_time = datetime.now()
        logger.debug(f"Starting operation: {self.operation_name}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (datetime.now() - self.start_time).total_seconds() * 1000
            
            if duration_ms > self.threshold_ms:
                logger.warning(
                    f"Slow operation detected: {self.operation_name}",
                    duration_ms=duration_ms,
                    threshold_ms=self.threshold_ms
                )
            else:
                logger.debug(
                    f"Operation completed: {self.operation_name}",
                    duration_ms=duration_ms
                )


class RestaurantAILogger:
    """Main logging class for the application."""
    
    def __init__(self):
        self.setup_logging()
        self.performance_threshold_ms = 1000.0
        
    def setup_logging(self):
        """Configure logging based on settings."""
        
        # Create logs directory if it doesn't exist
        if settings.logging.LOG_FILE:
            log_dir = Path(settings.logging.LOG_FILE).parent
            log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer() if settings.logging.LOG_FORMAT == "json"
                else structlog.dev.ConsoleRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        # Configure Python's logging
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, settings.logging.LOG_LEVEL.upper()))
        
        # Clear existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.addFilter(RequestContextFilter())
        
        if settings.logging.LOG_FORMAT == "json":
            formatter = jsonlogger.JsonFormatter(
                fmt="%(asctime)s %(name)s %(levelname)s %(request_id)s %(user_id)s %(endpoint)s %(message)s"
            )
        else:
            formatter = logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(request_id)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # File handler (if specified)
        if settings.logging.LOG_FILE:
            file_handler = logging.FileHandler(settings.logging.LOG_FILE)
            file_handler.addFilter(RequestContextFilter())
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        
        # Configure loguru for advanced logging
        logger.remove()  # Remove default handler
        
        loguru_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "{extra[request_id]} | {extra[user_id]} | "
            "<level>{message}</level>"
        )
        
        logger.add(
            sys.stdout,
            format=loguru_format,
            level=settings.logging.LOG_LEVEL.upper(),
            enqueue=True
        )
        
        if settings.logging.LOG_FILE:
            logger.add(
                settings.logging.LOG_FILE,
                format=loguru_format,
                level=settings.logging.LOG_LEVEL.upper(),
                rotation="10 MB",
                retention="30 days",
                compression="zip",
                enqueue=True
            )
    
    def get_logger(self, name: str) -> structlog.stdlib.BoundLogger:
        """Get a structured logger for a specific module."""
        return structlog.get_logger(name)
    
    @contextmanager
    def performance_context(self, operation_name: str, threshold_ms: float = None):
        """Context manager for tracking operation performance."""
        threshold = threshold_ms or self.performance_threshold_ms
        with PerformanceLogger(operation_name, threshold) as perf:
            yield perf
    
    def log_request_start(self, request_id: str, method: str, url: str, user_id: str = None):
        """Log the start of an HTTP request."""
        logger.bind(
            request_id=request_id,
            user_id=user_id or "anonymous",
            endpoint=f"{method} {url}"
        ).info(f"Request started: {method} {url}")
    
    def log_request_end(self, request_id: str, status_code: int, duration_ms: float):
        """Log the end of an HTTP request."""
        level = "error" if status_code >= 400 else "info"
        getattr(logger.bind(request_id=request_id), level)(
            f"Request completed: {status_code}",
            status_code=status_code,
            duration_ms=duration_ms
        )
    
    def log_database_query(self, query: str, params: Dict = None, duration_ms: float = None):
        """Log database queries (if enabled)."""
        if settings.logging.ENABLE_SQL_LOGGING:
            logger.debug(
                "Database query executed",
                query=query[:500],  # Limit query length
                params=params,
                duration_ms=duration_ms
            )
    
    def log_whatsapp_operation(self, operation: str, phone_number: str, 
                             message_id: str = None, status: str = None, error: str = None):
        """Log WhatsApp API operations."""
        log_data = {
            "operation": operation,
            "phone_number": self._mask_phone_number(phone_number),
            "message_id": message_id,
            "status": status
        }
        
        if error:
            logger.error("WhatsApp operation failed", error=error, **log_data)
        else:
            logger.info("WhatsApp operation completed", **log_data)
    
    def log_ai_operation(self, operation: str, model: str, tokens_used: int = None, 
                        cost_usd: float = None, duration_ms: float = None, error: str = None):
        """Log AI/LLM operations with cost tracking."""
        log_data = {
            "operation": operation,
            "model": model,
            "tokens_used": tokens_used,
            "cost_usd": cost_usd,
            "duration_ms": duration_ms
        }
        
        if error:
            logger.error("AI operation failed", error=error, **log_data)
        else:
            logger.info("AI operation completed", **log_data)
    
    def log_customer_interaction(self, customer_id: str, interaction_type: str, 
                               details: Dict = None, sentiment: str = None):
        """Log customer interactions for analysis."""
        logger.info(
            "Customer interaction logged",
            customer_id=customer_id,
            interaction_type=interaction_type,
            sentiment=sentiment,
            details=details
        )
    
    def log_security_event(self, event_type: str, user_id: str = None, 
                          ip_address: str = None, details: Dict = None):
        """Log security-related events."""
        logger.warning(
            f"Security event: {event_type}",
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            details=details
        )
    
    def log_error_with_context(self, error: Exception, context: Dict = None):
        """Log errors with full context and stack trace."""
        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "stack_trace": traceback.format_exc(),
            "context": context or {}
        }
        
        logger.error("Unhandled error occurred", **error_data)
    
    def log_business_metric(self, metric_name: str, value: Any, 
                          customer_id: str = None, restaurant_id: str = None):
        """Log business metrics for monitoring."""
        logger.info(
            f"Business metric: {metric_name}",
            metric_name=metric_name,
            metric_value=value,
            customer_id=customer_id,
            restaurant_id=restaurant_id
        )
    
    def _mask_phone_number(self, phone_number: str) -> str:
        """Mask phone number for privacy."""
        if len(phone_number) > 6:
            return phone_number[:3] + "*" * (len(phone_number) - 6) + phone_number[-3:]
        return "*" * len(phone_number)


# Global logger instance
app_logger = RestaurantAILogger()


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a logger for a specific module."""
    return app_logger.get_logger(name)


def performance_monitor(operation_name: str, threshold_ms: float = 1000.0):
    """Decorator for monitoring function performance."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            with app_logger.performance_context(operation_name, threshold_ms):
                return await func(*args, **kwargs)
                
        def sync_wrapper(*args, **kwargs):
            with app_logger.performance_context(operation_name, threshold_ms):
                return func(*args, **kwargs)
        
        if hasattr(func, '__code__') and 'await' in func.__code__.co_names:
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Export commonly used functions
__all__ = [
    'app_logger',
    'get_logger', 
    'performance_monitor',
    'RestaurantAILogger',
    'PerformanceLogger'
]