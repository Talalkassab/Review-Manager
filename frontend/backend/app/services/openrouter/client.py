"""
OpenRouter API Client
Comprehensive async client for OpenRouter API with multi-model support,
cost tracking, rate limiting, and fallback mechanisms.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import aiohttp
import structlog
from pydantic import BaseModel

from app.core.ai_config import AIConfig, ModelType, ai_config
from app.models.ai import AIInteraction, ModelUsage


logger = structlog.get_logger(__name__)


class RateLimiter:
    """Rate limiter for API requests"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = []
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Wait if rate limit would be exceeded"""
        async with self.lock:
            now = time.time()
            # Remove requests older than 1 minute
            self.requests = [req_time for req_time in self.requests 
                           if now - req_time < 60]
            
            if len(self.requests) >= self.requests_per_minute:
                # Wait until the oldest request is more than 1 minute old
                wait_time = 60 - (now - self.requests[0])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    return await self.acquire()
            
            self.requests.append(now)


class CostTracker:
    """Track costs and enforce budget limits"""
    
    def __init__(self, config: AIConfig):
        self.config = config
        self.daily_usage = {}
        self.monthly_usage = {}
        self.lock = asyncio.Lock()
    
    async def check_budget(self, estimated_cost: float) -> bool:
        """
        Check if request would exceed budget limits.
        
        Args:
            estimated_cost: Estimated cost of the request
            
        Returns:
            True if request is within budget
        """
        async with self.lock:
            today = datetime.now().date()
            current_month = datetime.now().replace(day=1).date()
            
            daily_spent = self.daily_usage.get(today, 0.0)
            monthly_spent = self.monthly_usage.get(current_month, 0.0)
            
            # Check daily budget
            if daily_spent + estimated_cost > self.config.cost_limits.daily_budget_usd:
                logger.warning(
                    "Daily budget would be exceeded",
                    daily_spent=daily_spent,
                    estimated_cost=estimated_cost,
                    daily_budget=self.config.cost_limits.daily_budget_usd
                )
                return False
            
            # Check monthly budget
            if monthly_spent + estimated_cost > self.config.cost_limits.monthly_budget_usd:
                logger.warning(
                    "Monthly budget would be exceeded",
                    monthly_spent=monthly_spent,
                    estimated_cost=estimated_cost,
                    monthly_budget=self.config.cost_limits.monthly_budget_usd
                )
                return False
            
            return True
    
    async def record_usage(self, cost: float):
        """Record actual usage"""
        async with self.lock:
            today = datetime.now().date()
            current_month = datetime.now().replace(day=1).date()
            
            self.daily_usage[today] = self.daily_usage.get(today, 0.0) + cost
            self.monthly_usage[current_month] = self.monthly_usage.get(current_month, 0.0) + cost


class OpenRouterResponse(BaseModel):
    """Response from OpenRouter API"""
    content: str
    model_used: str
    input_tokens: int
    output_tokens: int
    cost: float
    response_time: float
    success: bool
    error: Optional[str] = None


class OpenRouterClient:
    """
    Async OpenRouter API client with comprehensive features:
    - Multi-model support with intelligent selection
    - Cost tracking and budget management
    - Rate limiting and retry logic
    - Fallback mechanisms between models
    - Performance monitoring
    """
    
    def __init__(self, config: Optional[AIConfig] = None):
        self.config = config or ai_config
        self.rate_limiter = RateLimiter(
            self.config.performance_thresholds.rate_limit_requests_per_minute
        )
        self.cost_tracker = CostTracker(self.config)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if not self.session or self.session.closed:
            timeout = aiohttp.ClientTimeout(
                total=self.config.performance_thresholds.max_response_time_seconds
            )
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "Authorization": f"Bearer {self.config.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": self.config.site_url,
                    "X-Title": self.config.app_name,
                }
            )
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars per token average)"""
        return max(1, len(text) // 4)
    
    async def _make_request(
        self, 
        model: ModelType, 
        messages: List[Dict[str, str]], 
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        attempt: int = 1
    ) -> OpenRouterResponse:
        """
        Make a request to OpenRouter API.
        
        Args:
            model: The model to use
            messages: List of messages
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            attempt: Current attempt number
            
        Returns:
            OpenRouterResponse with results
        """
        start_time = time.time()
        
        try:
            await self._ensure_session()
            model_config = self.config.get_model_config(model)
            
            # Estimate input tokens
            input_text = " ".join([msg.get("content", "") for msg in messages])
            input_tokens = self._estimate_tokens(input_text)
            estimated_output_tokens = max_tokens or model_config.max_tokens
            
            # Estimate cost
            estimated_cost = self.config.calculate_estimated_cost(
                model, input_tokens, estimated_output_tokens
            )
            
            # Check budget
            if not await self.cost_tracker.check_budget(estimated_cost):
                return OpenRouterResponse(
                    content="",
                    model_used=model.value,
                    input_tokens=input_tokens,
                    output_tokens=0,
                    cost=0.0,
                    response_time=time.time() - start_time,
                    success=False,
                    error="Budget limit exceeded"
                )
            
            # Rate limiting
            await self.rate_limiter.acquire()
            
            # Prepare request
            payload = {
                "model": model.value,
                "messages": messages,
                "max_tokens": max_tokens or model_config.max_tokens,
                "temperature": temperature or model_config.temperature,
                "top_p": model_config.top_p,
                "stream": False
            }
            
            logger.info(
                "Making OpenRouter request",
                model=model.value,
                messages_count=len(messages),
                attempt=attempt
            )
            
            async with self.session.post(
                f"{self.config.openrouter_base_url}/chat/completions",
                json=payload
            ) as response:
                response_data = await response.json()
                
                if response.status != 200:
                    error_msg = response_data.get("error", {}).get("message", "Unknown error")
                    logger.error(
                        "OpenRouter API error",
                        status=response.status,
                        error=error_msg,
                        model=model.value
                    )
                    
                    return OpenRouterResponse(
                        content="",
                        model_used=model.value,
                        input_tokens=input_tokens,
                        output_tokens=0,
                        cost=0.0,
                        response_time=time.time() - start_time,
                        success=False,
                        error=f"API Error: {error_msg}"
                    )
                
                # Extract response data
                choice = response_data["choices"][0]
                content = choice["message"]["content"]
                
                # Get usage data
                usage = response_data.get("usage", {})
                actual_input_tokens = usage.get("prompt_tokens", input_tokens)
                actual_output_tokens = usage.get("completion_tokens", 0)
                
                # Calculate actual cost
                actual_cost = self.config.calculate_estimated_cost(
                    model, actual_input_tokens, actual_output_tokens
                )
                
                # Record usage
                await self.cost_tracker.record_usage(actual_cost)
                
                response_time = time.time() - start_time
                
                logger.info(
                    "OpenRouter request successful",
                    model=model.value,
                    input_tokens=actual_input_tokens,
                    output_tokens=actual_output_tokens,
                    cost=actual_cost,
                    response_time=response_time
                )
                
                return OpenRouterResponse(
                    content=content,
                    model_used=model.value,
                    input_tokens=actual_input_tokens,
                    output_tokens=actual_output_tokens,
                    cost=actual_cost,
                    response_time=response_time,
                    success=True
                )
                
        except asyncio.TimeoutError:
            logger.error(
                "Request timeout",
                model=model.value,
                attempt=attempt
            )
            return OpenRouterResponse(
                content="",
                model_used=model.value,
                input_tokens=0,
                output_tokens=0,
                cost=0.0,
                response_time=time.time() - start_time,
                success=False,
                error="Request timeout"
            )
            
        except Exception as e:
            logger.error(
                "Unexpected error in OpenRouter request",
                model=model.value,
                attempt=attempt,
                error=str(e)
            )
            return OpenRouterResponse(
                content="",
                model_used=model.value,
                input_tokens=0,
                output_tokens=0,
                cost=0.0,
                response_time=time.time() - start_time,
                success=False,
                error=f"Unexpected error: {str(e)}"
            )
    
    async def complete(
        self,
        model: ModelType,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        use_fallback: bool = True
    ) -> OpenRouterResponse:
        """
        Complete a chat request with fallback support.
        
        Args:
            model: Primary model to use
            messages: List of messages
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            use_fallback: Whether to use fallback models on failure
            
        Returns:
            OpenRouterResponse with results
        """
        models_to_try = [model]
        
        if use_fallback:
            fallback_models = self.config.get_fallback_models(model)
            models_to_try.extend(fallback_models)
        
        last_response = None
        
        for attempt, current_model in enumerate(models_to_try, 1):
            if attempt > self.config.performance_thresholds.max_retry_attempts:
                break
                
            response = await self._make_request(
                current_model, messages, max_tokens, temperature, attempt
            )
            
            if response.success:
                return response
            
            last_response = response
            logger.warning(
                "Model failed, trying fallback",
                failed_model=current_model.value,
                error=response.error,
                attempt=attempt
            )
            
            # Wait before retry
            if attempt < len(models_to_try):
                await asyncio.sleep(min(2 ** attempt, 10))
        
        # All models failed
        logger.error(
            "All models failed",
            primary_model=model.value,
            total_attempts=len(models_to_try)
        )
        
        return last_response or OpenRouterResponse(
            content="",
            model_used=model.value,
            input_tokens=0,
            output_tokens=0,
            cost=0.0,
            response_time=0.0,
            success=False,
            error="All models failed"
        )
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        today = datetime.now().date()
        current_month = datetime.now().replace(day=1).date()
        
        return {
            "daily_usage": self.cost_tracker.daily_usage.get(today, 0.0),
            "monthly_usage": self.cost_tracker.monthly_usage.get(current_month, 0.0),
            "daily_budget": self.config.cost_limits.daily_budget_usd,
            "monthly_budget": self.config.cost_limits.monthly_budget_usd,
            "daily_remaining": max(0, self.config.cost_limits.daily_budget_usd - 
                                 self.cost_tracker.daily_usage.get(today, 0.0)),
            "monthly_remaining": max(0, self.config.cost_limits.monthly_budget_usd - 
                                   self.cost_tracker.monthly_usage.get(current_month, 0.0))
        }


# Global client instance
openrouter_client = OpenRouterClient()