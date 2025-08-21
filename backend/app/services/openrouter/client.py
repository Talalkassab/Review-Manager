"""
OpenRouter HTTP client with retry logic and error handling.
Handles all direct communication with OpenRouter API.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import aiohttp
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from ...core.config import settings
from .exceptions import (
    OpenRouterError,
    APIError,
    RateLimitExceededError,
    ModelTimeoutError
)
from .types import OpenRouterResponse, RequestParameters, Usage

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """HTTP client for OpenRouter API with comprehensive error handling."""
    
    def __init__(self):
        self.api_key = settings.openrouter.OPENROUTER_API_KEY
        self.base_url = settings.openrouter.OPENROUTER_BASE_URL
        self.timeout = aiohttp.ClientTimeout(total=60, connect=10)
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Request tracking
        self.request_count = 0
        self.last_request_time: Optional[datetime] = None
        
        if not self.api_key:
            logger.warning("OpenRouter API key not configured")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_session()
    
    async def start_session(self):
        """Initialize HTTP session."""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=self.timeout,
                headers=self._get_default_headers(),
                connector=aiohttp.TCPConnector(limit=100, limit_per_host=30)
            )
            logger.debug("OpenRouter HTTP session started")
    
    async def close_session(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.debug("OpenRouter HTTP session closed")
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for API requests."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"{settings.app.APP_NAME}/{settings.app.APP_VERSION}",
            "HTTP-Referer": "https://your-app-domain.com",
            "X-Title": settings.app.APP_NAME
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers
    
    def _parse_rate_limit_headers(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """Parse rate limit information from response headers."""
        rate_limit_info = {}
        
        # Standard rate limit headers
        for key, header_name in [
            ("requests_remaining", "x-ratelimit-requests-remaining"),
            ("requests_reset", "x-ratelimit-requests-reset"),
            ("tokens_remaining", "x-ratelimit-tokens-remaining"),
            ("tokens_reset", "x-ratelimit-tokens-reset"),
        ]:
            if header_name in headers:
                try:
                    rate_limit_info[key] = int(headers[header_name])
                except (ValueError, TypeError):
                    pass
        
        return rate_limit_info
    
    async def _handle_response_errors(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Handle HTTP response errors and extract data."""
        try:
            response_data = await response.json()
        except (json.JSONDecodeError, aiohttp.ContentTypeError):
            response_data = {"error": await response.text()}
        
        if response.status == 200:
            return response_data
        
        # Extract error information
        error_message = "API request failed"
        if "error" in response_data:
            if isinstance(response_data["error"], dict):
                error_message = response_data["error"].get("message", error_message)
            else:
                error_message = str(response_data["error"])
        
        request_id = response.headers.get("x-request-id")
        
        # Handle specific error types
        if response.status == 429:
            retry_after = response.headers.get("retry-after")
            retry_seconds = int(retry_after) if retry_after else 60
            
            rate_limit_info = self._parse_rate_limit_headers(dict(response.headers))
            
            raise RateLimitExceededError(
                retry_after=retry_seconds,
                current_usage=rate_limit_info.get("requests_remaining"),
                limit=rate_limit_info.get("requests_limit")
            )
        
        elif response.status in [500, 502, 503, 504]:
            # Server errors - retryable
            raise APIError(
                message=f"Server error: {error_message}",
                status_code=response.status,
                response_data=response_data,
                request_id=request_id
            )
        
        elif response.status in [400, 401, 403, 404]:
            # Client errors - not retryable
            raise APIError(
                message=f"Client error: {error_message}",
                status_code=response.status,
                response_data=response_data,
                request_id=request_id
            )
        
        else:
            # Unknown error
            raise APIError(
                message=f"Unexpected error: {error_message}",
                status_code=response.status,
                response_data=response_data,
                request_id=request_id
            )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((APIError, aiohttp.ClientError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic."""
        if not self.session:
            await self.start_session()
        
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Update request tracking
        self.request_count += 1
        self.last_request_time = datetime.utcnow()
        
        request_data = {
            "method": method,
            "url": url,
            "params": params
        }
        
        if data is not None:
            request_data["json"] = data
        
        logger.debug(f"Making {method} request to {url}")
        
        try:
            async with self.session.request(**request_data) as response:
                return await self._handle_response_errors(response)
        
        except asyncio.TimeoutError:
            raise ModelTimeoutError(
                model_name="unknown",
                timeout_seconds=int(self.timeout.total)
            )
        
        except aiohttp.ClientError as e:
            raise APIError(
                message=f"HTTP client error: {str(e)}",
                status_code=None,
                response_data={"client_error": str(e)}
            )
    
    async def create_chat_completion(self, params: RequestParameters) -> OpenRouterResponse:
        """Create a chat completion using OpenRouter API."""
        # Convert parameters to API format
        request_data = {
            "model": params.model,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    **({"name": msg.name} if msg.name else {})
                }
                for msg in params.messages
            ],
            "temperature": params.temperature,
            "top_p": params.top_p,
            "frequency_penalty": params.frequency_penalty,
            "presence_penalty": params.presence_penalty,
            "stream": params.stream
        }
        
        # Add optional parameters
        if params.max_tokens is not None:
            request_data["max_tokens"] = params.max_tokens
        if params.stop is not None:
            request_data["stop"] = params.stop
        if params.transforms:
            request_data["transforms"] = params.transforms
        if params.route:
            request_data["route"] = params.route
        
        logger.info(f"Creating chat completion with model: {params.model}")
        
        try:
            response_data = await self._make_request("POST", "chat/completions", request_data)
            
            # Parse response into our model
            return OpenRouterResponse(**response_data)
        
        except Exception as e:
            logger.error(f"Chat completion failed: {str(e)}")
            raise
    
    async def list_models(self) -> Dict[str, Any]:
        """List available models from OpenRouter."""
        logger.debug("Fetching available models")
        
        try:
            return await self._make_request("GET", "models")
        except Exception as e:
            logger.error(f"Failed to list models: {str(e)}")
            raise
    
    async def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        logger.debug(f"Fetching model info for: {model_id}")
        
        try:
            return await self._make_request("GET", f"models/{model_id}")
        except Exception as e:
            logger.error(f"Failed to get model info for {model_id}: {str(e)}")
            raise
    
    async def health_check(self) -> bool:
        """Check if the OpenRouter API is accessible."""
        try:
            await self.list_models()
            return True
        except Exception as e:
            logger.warning(f"Health check failed: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            "request_count": self.request_count,
            "last_request_time": self.last_request_time.isoformat() if self.last_request_time else None,
            "session_active": self.session is not None and not self.session.closed
        }