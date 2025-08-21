"""
Rate Limiter for OpenRouter API integration.
Manages API rate limits to prevent exceeding quotas and ensure fair usage.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict, deque
from enum import Enum

try:
    import redis.asyncio as redis
except ImportError:
    redis = None

from .exceptions import RateLimitExceededError
from ...core.config import settings

logger = logging.getLogger(__name__)


class LimitType(str, Enum):
    """Types of rate limits."""
    REQUESTS_PER_MINUTE = "requests_per_minute"
    REQUESTS_PER_HOUR = "requests_per_hour"
    REQUESTS_PER_DAY = "requests_per_day"
    TOKENS_PER_MINUTE = "tokens_per_minute"
    TOKENS_PER_HOUR = "tokens_per_hour"


@dataclass
class RateLimit:
    """Rate limit configuration."""
    limit_type: LimitType
    limit: int
    window_seconds: int
    per_user: bool = True


@dataclass
class RateLimitStatus:
    """Current rate limit status."""
    limit_type: LimitType
    current_usage: int
    limit: int
    remaining: int
    reset_time: datetime
    window_seconds: int


class RateLimiter:
    """
    Rate limiting service for OpenRouter API requests.
    
    Features:
    - Multiple rate limit types (requests, tokens, per minute/hour/day)
    - Per-user and global rate limiting
    - Redis-backed for distributed systems
    - Graceful degradation to in-memory
    - Smart wait times and backoff
    """
    
    def __init__(self):
        """Initialize the rate limiter."""
        self.redis_client: Optional[redis.Redis] = None
        
        # In-memory rate limit tracking (fallback)
        self.request_windows: Dict[str, deque] = defaultdict(deque)
        self.token_windows: Dict[str, deque] = defaultdict(deque)
        
        # Rate limit configurations
        self.rate_limits: List[RateLimit] = []
        
        self._initialize_default_limits()
        logger.info("Rate limiter initialized")
    
    def _initialize_default_limits(self):
        """Initialize default rate limits from configuration."""
        # Get limits from settings
        max_requests_per_minute = getattr(settings.openrouter, 'MAX_REQUESTS_PER_MINUTE', 60)
        
        default_limits = [
            # Request-based limits
            RateLimit(
                limit_type=LimitType.REQUESTS_PER_MINUTE,
                limit=max_requests_per_minute,
                window_seconds=60,
                per_user=True
            ),
            RateLimit(
                limit_type=LimitType.REQUESTS_PER_HOUR,
                limit=max_requests_per_minute * 60,
                window_seconds=3600,
                per_user=True
            ),
            RateLimit(
                limit_type=LimitType.REQUESTS_PER_DAY,
                limit=max_requests_per_minute * 60 * 24,
                window_seconds=86400,
                per_user=True
            ),
            
            # Token-based limits
            RateLimit(
                limit_type=LimitType.TOKENS_PER_MINUTE,
                limit=100000,  # 100K tokens per minute per user
                window_seconds=60,
                per_user=True
            ),
            RateLimit(
                limit_type=LimitType.TOKENS_PER_HOUR,
                limit=1000000,  # 1M tokens per hour per user
                window_seconds=3600,
                per_user=True
            ),
            
            # Global limits (across all users)
            RateLimit(
                limit_type=LimitType.REQUESTS_PER_MINUTE,
                limit=max_requests_per_minute * 10,  # 10x individual limit
                window_seconds=60,
                per_user=False
            ),
        ]
        
        self.rate_limits = default_limits
    
    async def initialize(self):
        """Initialize Redis connection for distributed rate limiting."""
        try:
            if redis and hasattr(settings, 'redis') and settings.redis.REDIS_URL:
                self.redis_client = redis.from_url(
                    settings.redis.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=False,  # Keep binary for lua scripts
                    retry_on_timeout=True
                )
                
                # Test connection
                await self.redis_client.ping()
                logger.info("Redis rate limiter backend connected")
            else:
                logger.info("Redis not available, using in-memory rate limiting")
                
        except Exception as e:
            logger.warning(f"Failed to connect to Redis for rate limiting: {str(e)}")
            self.redis_client = None
    
    async def check_and_wait(
        self,
        user_id: str,
        tokens: int = 1,
        max_wait_seconds: int = 60
    ) -> bool:
        """
        Check rate limits and wait if necessary.
        
        Args:
            user_id: User identifier for per-user limits
            tokens: Number of tokens being used
            max_wait_seconds: Maximum time to wait before giving up
            
        Returns:
            True if request can proceed, False if should be rejected
            
        Raises:
            RateLimitExceededError: If limits are exceeded and wait time is too long
        """
        try:
            # Check all configured rate limits
            violations = []
            
            for rate_limit in self.rate_limits:
                status = await self._check_limit(user_id, rate_limit, tokens)
                
                if status.remaining <= 0:
                    violations.append(status)
            
            if not violations:
                # No violations, record usage and proceed
                await self._record_usage(user_id, tokens)
                return True
            
            # Find the violation with the shortest reset time
            next_reset = min(v.reset_time for v in violations)
            wait_seconds = (next_reset - datetime.utcnow()).total_seconds()
            
            if wait_seconds <= 0:
                # Reset time has passed, try again
                await self._record_usage(user_id, tokens)
                return True
            
            if wait_seconds > max_wait_seconds:
                # Wait time too long, reject request
                violation = violations[0]  # Report first violation
                raise RateLimitExceededError(
                    retry_after=int(wait_seconds),
                    limit_type=violation.limit_type,
                    current_usage=violation.current_usage,
                    limit=violation.limit
                )
            
            # Wait for rate limit to reset
            logger.info(f"Rate limit hit for user {user_id}, waiting {wait_seconds:.1f}s")
            await asyncio.sleep(wait_seconds)
            
            # Record usage after waiting
            await self._record_usage(user_id, tokens)
            return True
            
        except RateLimitExceededError:
            raise
        except Exception as e:
            logger.error(f"Rate limit check error: {str(e)}")
            # On error, allow the request to proceed
            return True
    
    async def _check_limit(
        self,
        user_id: str,
        rate_limit: RateLimit,
        tokens: int
    ) -> RateLimitStatus:
        """Check a specific rate limit."""
        key = self._get_limit_key(user_id, rate_limit)
        
        if self.redis_client:
            return await self._check_limit_redis(key, rate_limit, tokens)
        else:
            return await self._check_limit_memory(key, rate_limit, tokens)
    
    async def _check_limit_redis(
        self,
        key: str,
        rate_limit: RateLimit,
        tokens: int
    ) -> RateLimitStatus:
        """Check rate limit using Redis sliding window."""
        try:
            # Use Redis sliding window counter
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=rate_limit.window_seconds)
            
            pipe = self.redis_client.pipeline()
            
            # Remove expired entries
            pipe.zremrangebyscore(key, 0, window_start.timestamp())
            
            # Count current entries in window
            pipe.zcount(key, window_start.timestamp(), now.timestamp())
            
            # Set expiry for cleanup
            pipe.expire(key, rate_limit.window_seconds + 60)
            
            results = await pipe.execute()
            current_count = results[1]
            
            # Calculate usage based on limit type
            if rate_limit.limit_type.value.startswith("tokens"):
                # For token limits, we need to sum the token values
                # This is a simplified approach - in production, you'd store token counts differently
                current_usage = current_count * 10  # Rough estimate
            else:
                current_usage = current_count
            
            remaining = max(0, rate_limit.limit - current_usage)
            reset_time = now + timedelta(seconds=rate_limit.window_seconds)
            
            return RateLimitStatus(
                limit_type=rate_limit.limit_type,
                current_usage=current_usage,
                limit=rate_limit.limit,
                remaining=remaining,
                reset_time=reset_time,
                window_seconds=rate_limit.window_seconds
            )
            
        except Exception as e:
            logger.error(f"Redis rate limit check error: {str(e)}")
            # Fall back to memory-based checking
            return await self._check_limit_memory(key, rate_limit, tokens)
    
    async def _check_limit_memory(
        self,
        key: str,
        rate_limit: RateLimit,
        tokens: int
    ) -> RateLimitStatus:
        """Check rate limit using in-memory sliding window."""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=rate_limit.window_seconds)
        
        # Get appropriate window based on limit type
        if rate_limit.limit_type.value.startswith("tokens"):
            window = self.token_windows[key]
        else:
            window = self.request_windows[key]
        
        # Remove expired entries
        while window and window[0][0] < window_start:
            window.popleft()
        
        # Calculate current usage
        if rate_limit.limit_type.value.startswith("tokens"):
            current_usage = sum(entry[1] for entry in window)
        else:
            current_usage = len(window)
        
        remaining = max(0, rate_limit.limit - current_usage)
        reset_time = now + timedelta(seconds=rate_limit.window_seconds)
        
        return RateLimitStatus(
            limit_type=rate_limit.limit_type,
            current_usage=current_usage,
            limit=rate_limit.limit,
            remaining=remaining,
            reset_time=reset_time,
            window_seconds=rate_limit.window_seconds
        )
    
    async def _record_usage(self, user_id: str, tokens: int):
        """Record API usage for rate limiting."""
        now = datetime.utcnow()
        
        for rate_limit in self.rate_limits:
            key = self._get_limit_key(user_id, rate_limit)
            
            if self.redis_client:
                await self._record_usage_redis(key, rate_limit, tokens, now)
            else:
                await self._record_usage_memory(key, rate_limit, tokens, now)
    
    async def _record_usage_redis(
        self,
        key: str,
        rate_limit: RateLimit,
        tokens: int,
        timestamp: datetime
    ):
        """Record usage in Redis."""
        try:
            # Add entry to sorted set with timestamp as score
            value = tokens if rate_limit.limit_type.value.startswith("tokens") else 1
            await self.redis_client.zadd(key, {str(timestamp.timestamp()): value})
            
            # Set expiry
            await self.redis_client.expire(key, rate_limit.window_seconds + 60)
            
        except Exception as e:
            logger.error(f"Redis usage recording error: {str(e)}")
            # Fall back to memory recording
            await self._record_usage_memory(key, rate_limit, tokens, timestamp)
    
    async def _record_usage_memory(
        self,
        key: str,
        rate_limit: RateLimit,
        tokens: int,
        timestamp: datetime
    ):
        """Record usage in memory."""
        # Get appropriate window
        if rate_limit.limit_type.value.startswith("tokens"):
            window = self.token_windows[key]
            window.append((timestamp, tokens))
        else:
            window = self.request_windows[key]
            window.append((timestamp, 1))
        
        # Keep window size reasonable
        if len(window) > 10000:
            # Remove old entries
            cutoff = timestamp - timedelta(seconds=rate_limit.window_seconds * 2)
            while window and window[0][0] < cutoff:
                window.popleft()
    
    def _get_limit_key(self, user_id: str, rate_limit: RateLimit) -> str:
        """Generate key for rate limit tracking."""
        if rate_limit.per_user:
            return f"rate_limit:{rate_limit.limit_type.value}:{user_id}"
        else:
            return f"rate_limit:{rate_limit.limit_type.value}:global"
    
    async def get_status(self, user_id: str = "default") -> Dict[str, Any]:
        """Get current rate limit status for a user."""
        statuses = {}
        
        for rate_limit in self.rate_limits:
            try:
                status = await self._check_limit(user_id, rate_limit, 0)
                statuses[rate_limit.limit_type.value] = {
                    "current_usage": status.current_usage,
                    "limit": status.limit,
                    "remaining": status.remaining,
                    "reset_time": status.reset_time.isoformat(),
                    "window_seconds": status.window_seconds,
                    "per_user": rate_limit.per_user
                }
            except Exception as e:
                logger.error(f"Error getting status for {rate_limit.limit_type}: {str(e)}")
                statuses[rate_limit.limit_type.value] = {
                    "error": str(e)
                }
        
        return {
            "user_id": user_id,
            "limits": statuses,
            "backend": "redis" if self.redis_client else "memory"
        }
    
    async def reset_limits(self, user_id: str, limit_types: Optional[List[str]] = None):
        """Reset rate limits for a user."""
        limit_types = limit_types or [lt.value for lt in LimitType]
        
        for rate_limit in self.rate_limits:
            if rate_limit.limit_type.value not in limit_types:
                continue
            
            key = self._get_limit_key(user_id, rate_limit)
            
            try:
                if self.redis_client:
                    await self.redis_client.delete(key)
                else:
                    # Clear memory windows
                    if key in self.request_windows:
                        self.request_windows[key].clear()
                    if key in self.token_windows:
                        self.token_windows[key].clear()
                
                logger.info(f"Reset {rate_limit.limit_type.value} limit for user {user_id}")
                
            except Exception as e:
                logger.error(f"Error resetting {rate_limit.limit_type.value} for {user_id}: {str(e)}")
    
    async def update_limits(self, new_limits: List[Dict[str, Any]]):
        """Update rate limit configurations."""
        try:
            updated_limits = []
            
            for limit_config in new_limits:
                rate_limit = RateLimit(
                    limit_type=LimitType(limit_config["limit_type"]),
                    limit=limit_config["limit"],
                    window_seconds=limit_config["window_seconds"],
                    per_user=limit_config.get("per_user", True)
                )
                updated_limits.append(rate_limit)
            
            self.rate_limits = updated_limits
            logger.info(f"Updated rate limits: {len(updated_limits)} configurations")
            
        except Exception as e:
            logger.error(f"Error updating rate limits: {str(e)}")
            raise ValueError(f"Invalid rate limit configuration: {str(e)}")
    
    async def get_top_users(self, limit_type: str, count: int = 10) -> List[Dict[str, Any]]:
        """Get users with highest usage for a specific limit type."""
        # This is a simplified implementation
        # In production, you'd maintain better usage statistics
        
        users = []
        if self.redis_client:
            try:
                # Find all user keys for this limit type
                pattern = f"rate_limit:{limit_type}:*"
                keys = await self.redis_client.keys(pattern)
                
                for key in keys[:count]:
                    user_id = key.split(":")[-1]
                    if user_id != "global":
                        usage = await self.redis_client.zcard(key)
                        users.append({
                            "user_id": user_id,
                            "usage": usage
                        })
                
                # Sort by usage
                users.sort(key=lambda x: x["usage"], reverse=True)
                
            except Exception as e:
                logger.error(f"Error getting top users: {str(e)}")
        
        return users[:count]
    
    async def cleanup_expired_entries(self):
        """Clean up expired rate limit entries."""
        if not self.redis_client:
            # Clean up memory windows
            now = datetime.utcnow()
            
            for key, window in list(self.request_windows.items()):
                cutoff = now - timedelta(seconds=3600)  # Keep 1 hour
                while window and window[0][0] < cutoff:
                    window.popleft()
                
                if not window:
                    del self.request_windows[key]
            
            for key, window in list(self.token_windows.items()):
                cutoff = now - timedelta(seconds=3600)
                while window and window[0][0] < cutoff:
                    window.popleft()
                
                if not window:
                    del self.token_windows[key]
    
    async def estimate_wait_time(self, user_id: str, tokens: int = 1) -> float:
        """Estimate wait time before a request can be made."""
        violations = []
        
        for rate_limit in self.rate_limits:
            status = await self._check_limit(user_id, rate_limit, tokens)
            if status.remaining <= 0:
                violations.append(status)
        
        if not violations:
            return 0.0
        
        # Return the longest wait time
        max_wait = 0.0
        for violation in violations:
            wait_time = (violation.reset_time - datetime.utcnow()).total_seconds()
            max_wait = max(max_wait, wait_time)
        
        return max(0.0, max_wait)