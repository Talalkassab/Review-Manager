"""
OpenRouter service exception classes.
Comprehensive error handling for all API operations.
"""

from typing import Optional, Dict, Any


class OpenRouterError(Exception):
    """Base exception for all OpenRouter service errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class APIError(OpenRouterError):
    """API-related errors from OpenRouter."""
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ):
        self.status_code = status_code
        self.response_data = response_data or {}
        self.request_id = request_id
        
        details = {
            "status_code": status_code,
            "response_data": response_data,
            "request_id": request_id
        }
        super().__init__(message, details)


class ModelNotAvailableError(OpenRouterError):
    """Raised when a requested model is not available."""
    
    def __init__(self, model_name: str, available_models: Optional[list] = None):
        self.model_name = model_name
        self.available_models = available_models or []
        
        message = f"Model '{model_name}' is not available"
        if available_models:
            message += f". Available models: {', '.join(available_models[:5])}"
        
        details = {
            "model_name": model_name,
            "available_models": available_models
        }
        super().__init__(message, details)


class RateLimitExceededError(OpenRouterError):
    """Raised when API rate limits are exceeded."""
    
    def __init__(
        self, 
        retry_after: Optional[int] = None,
        limit_type: str = "requests",
        current_usage: Optional[int] = None,
        limit: Optional[int] = None
    ):
        self.retry_after = retry_after
        self.limit_type = limit_type
        self.current_usage = current_usage
        self.limit = limit
        
        message = f"Rate limit exceeded for {limit_type}"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        if current_usage and limit:
            message += f" ({current_usage}/{limit})"
            
        details = {
            "retry_after": retry_after,
            "limit_type": limit_type,
            "current_usage": current_usage,
            "limit": limit
        }
        super().__init__(message, details)


class BudgetExceededError(OpenRouterError):
    """Raised when budget limits are exceeded."""
    
    def __init__(
        self, 
        current_cost: float,
        budget_limit: float,
        period: str = "monthly"
    ):
        self.current_cost = current_cost
        self.budget_limit = budget_limit
        self.period = period
        
        message = f"{period.title()} budget exceeded: ${current_cost:.4f} / ${budget_limit:.2f}"
        details = {
            "current_cost": current_cost,
            "budget_limit": budget_limit,
            "period": period
        }
        super().__init__(message, details)


class ValidationError(OpenRouterError):
    """Raised when request or response validation fails."""
    
    def __init__(self, field: str, value: Any, reason: str):
        self.field = field
        self.value = value
        self.reason = reason
        
        message = f"Validation failed for field '{field}': {reason}"
        details = {
            "field": field,
            "value": value,
            "reason": reason
        }
        super().__init__(message, details)


class TokenLimitExceededError(OpenRouterError):
    """Raised when token limits are exceeded."""
    
    def __init__(
        self, 
        token_count: int,
        token_limit: int,
        token_type: str = "total"
    ):
        self.token_count = token_count
        self.token_limit = token_limit
        self.token_type = token_type
        
        message = f"Token limit exceeded for {token_type}: {token_count} > {token_limit}"
        details = {
            "token_count": token_count,
            "token_limit": token_limit,
            "token_type": token_type
        }
        super().__init__(message, details)


class ModelTimeoutError(OpenRouterError):
    """Raised when model response times out."""
    
    def __init__(self, model_name: str, timeout_seconds: int):
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        
        message = f"Model '{model_name}' timed out after {timeout_seconds} seconds"
        details = {
            "model_name": model_name,
            "timeout_seconds": timeout_seconds
        }
        super().__init__(message, details)