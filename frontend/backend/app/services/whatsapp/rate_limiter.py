"""
Rate limiting and queue management for WhatsApp Business API.

This module provides sophisticated rate limiting capabilities to ensure compliance
with WhatsApp API limits and prevent service disruption due to excessive requests.
"""

import asyncio
import time
import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any, Callable
from enum import Enum

from .exceptions import RateLimitExceededError


class RateLimitType(str, Enum):
    """Rate limit types for different WhatsApp operations."""
    MESSAGING = "messaging"
    MEDIA_UPLOAD = "media_upload"
    TEMPLATE_SYNC = "template_sync"
    WEBHOOK_PROCESSING = "webhook_processing"


@dataclass
class RateLimitWindow:
    """Rate limiting window configuration."""
    max_requests: int
    window_seconds: int
    burst_allowance: int = 0
    
    def __post_init__(self):
        """Validate window configuration."""
        if self.max_requests <= 0:
            raise ValueError("max_requests must be positive")
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        if self.burst_allowance < 0:
            raise ValueError("burst_allowance cannot be negative")


@dataclass
class RequestRecord:
    """Record of a rate-limited request."""
    timestamp: float
    request_type: RateLimitType
    identifier: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TokenBucket:
    """
    Token bucket algorithm implementation for rate limiting.
    
    This provides smooth rate limiting with burst capability,
    allowing temporary spikes in traffic while maintaining
    overall rate compliance.
    """
    
    def __init__(
        self,
        capacity: int,
        refill_rate: float,
        initial_tokens: Optional[int] = None
    ):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum number of tokens in bucket
            refill_rate: Tokens added per second
            initial_tokens: Initial token count (defaults to capacity)
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = initial_tokens or capacity
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens from bucket.
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            True if tokens acquired successfully, False otherwise
        """
        async with self._lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    async def acquire_blocking(
        self,
        tokens: int = 1,
        timeout: Optional[float] = None
    ) -> bool:
        """
        Acquire tokens, blocking until available or timeout.
        
        Args:
            tokens: Number of tokens to acquire
            timeout: Maximum wait time in seconds
            
        Returns:
            True if tokens acquired, False if timeout
        """
        start_time = time.time()
        
        while True:
            if await self.acquire(tokens):
                return True
            
            # Check timeout
            if timeout and (time.time() - start_time) >= timeout:
                return False
            
            # Calculate wait time until next token
            wait_time = min(tokens / self.refill_rate, 1.0)
            await asyncio.sleep(wait_time)
    
    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now
    
    def get_available_tokens(self) -> float:
        """Get current number of available tokens."""
        self._refill()
        return self.tokens
    
    def time_until_tokens(self, required_tokens: int) -> float:
        """Calculate time until required tokens are available."""
        available = self.get_available_tokens()
        
        if available >= required_tokens:
            return 0.0
        
        deficit = required_tokens - available
        return deficit / self.refill_rate


class SlidingWindowRateLimit:
    """
    Sliding window rate limiter with precise request tracking.
    
    This tracks individual requests and provides exact rate limiting
    based on a sliding time window.
    """
    
    def __init__(self, window: RateLimitWindow):
        """Initialize sliding window rate limiter."""
        self.window = window
        self.requests: deque = deque()
        self._lock = asyncio.Lock()
    
    async def can_proceed(self, identifier: Optional[str] = None) -> bool:
        """
        Check if request can proceed without being rate limited.
        
        Args:
            identifier: Optional request identifier for tracking
            
        Returns:
            True if request can proceed, False if rate limited
        """
        async with self._lock:
            self._cleanup_old_requests()
            return len(self.requests) < self.window.max_requests
    
    async def record_request(
        self,
        request_type: RateLimitType,
        identifier: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Record a new request and check if it should be allowed.
        
        Args:
            request_type: Type of request being made
            identifier: Optional request identifier
            metadata: Additional request metadata
            
        Returns:
            True if request allowed, False if rate limited
        """
        async with self._lock:
            self._cleanup_old_requests()
            
            # Check if we can accept more requests
            if len(self.requests) >= self.window.max_requests:
                return False
            
            # Record the request
            record = RequestRecord(
                timestamp=time.time(),
                request_type=request_type,
                identifier=identifier,
                metadata=metadata
            )
            self.requests.append(record)
            
            return True
    
    def _cleanup_old_requests(self):
        """Remove requests outside the current window."""
        cutoff_time = time.time() - self.window.window_seconds
        
        while self.requests and self.requests[0].timestamp < cutoff_time:
            self.requests.popleft()
    
    def get_current_count(self) -> int:
        """Get current number of requests in window."""
        self._cleanup_old_requests()
        return len(self.requests)
    
    def time_until_next_slot(self) -> float:
        """Calculate time until next request slot is available."""
        if len(self.requests) < self.window.max_requests:
            return 0.0
        
        # Time until oldest request expires
        oldest_request = self.requests[0]
        return (oldest_request.timestamp + self.window.window_seconds) - time.time()


class RateLimiter:
    """
    Comprehensive rate limiter for WhatsApp Business API operations.
    
    Combines multiple rate limiting strategies:
    - Token bucket for smooth rate limiting with bursts
    - Sliding window for precise limit enforcement
    - Per-operation type limits
    - Adaptive backoff strategies
    """
    
    # WhatsApp Business API default limits
    DEFAULT_LIMITS = {
        RateLimitType.MESSAGING: RateLimitWindow(
            max_requests=80,  # 80 messages per second
            window_seconds=60,
            burst_allowance=100
        ),
        RateLimitType.MEDIA_UPLOAD: RateLimitWindow(
            max_requests=100,  # 100 uploads per minute
            window_seconds=60,
            burst_allowance=20
        ),
        RateLimitType.TEMPLATE_SYNC: RateLimitWindow(
            max_requests=5,   # 5 template operations per minute
            window_seconds=60,
            burst_allowance=2
        ),
        RateLimitType.WEBHOOK_PROCESSING: RateLimitWindow(
            max_requests=200,  # 200 webhook processes per minute
            window_seconds=60,
            burst_allowance=50
        )
    }
    
    def __init__(
        self,
        max_requests: int = 80,
        time_window: int = 60,
        burst_limit: int = 1000,
        custom_limits: Optional[Dict[RateLimitType, RateLimitWindow]] = None
    ):
        """
        Initialize rate limiter with configuration.
        
        Args:
            max_requests: Default max requests per window
            time_window: Time window in seconds
            burst_limit: Maximum burst requests
            custom_limits: Custom limits for specific operation types
        """
        self.logger = logging.getLogger(__name__)
        
        # Global token bucket for overall rate limiting
        self.token_bucket = TokenBucket(
            capacity=burst_limit,
            refill_rate=max_requests / time_window,
            initial_tokens=burst_limit
        )
        
        # Per-operation sliding window limiters
        self.limiters: Dict[RateLimitType, SlidingWindowRateLimit] = {}
        
        # Use custom limits if provided, otherwise use defaults
        limits = custom_limits or self.DEFAULT_LIMITS
        
        for rate_type, window in limits.items():
            self.limiters[rate_type] = SlidingWindowRateLimit(window)
        
        # Statistics tracking
        self.stats = {
            'total_requests': 0,
            'rate_limited_requests': 0,
            'burst_requests': 0,
            'average_wait_time': 0.0
        }
        
        # Adaptive backoff configuration
        self.backoff_multiplier = 1.5
        self.max_backoff_seconds = 300  # 5 minutes
        self.current_backoff = 1.0
        
        # Queue for handling rate-limited requests
        self.pending_queue: asyncio.Queue = asyncio.Queue()
        self.queue_processor_task: Optional[asyncio.Task] = None
    
    async def acquire(
        self,
        request_type: RateLimitType = RateLimitType.MESSAGING,
        identifier: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> bool:
        """
        Acquire permission to make a request.
        
        Args:
            request_type: Type of operation being requested
            identifier: Optional identifier for request tracking
            metadata: Additional metadata for the request
            timeout: Maximum time to wait for permission
            
        Returns:
            True if permission granted, False if timeout or permanently denied
            
        Raises:
            RateLimitExceededError: If rate limits are exceeded
        """
        start_time = time.time()
        
        try:
            # Check global token bucket first
            if not await self.token_bucket.acquire_blocking(1, timeout=timeout):
                self.stats['rate_limited_requests'] += 1
                raise RateLimitExceededError(
                    "Global rate limit exceeded",
                    retry_after=int(self.token_bucket.time_until_tokens(1)),
                    limit_type="global"
                )
            
            # Check specific operation limit
            limiter = self.limiters.get(request_type)
            if limiter:
                allowed = await limiter.record_request(
                    request_type, identifier, metadata
                )
                
                if not allowed:
                    # Return token to bucket since we can't proceed
                    self.token_bucket.tokens += 1
                    
                    retry_after = limiter.time_until_next_slot()
                    self.stats['rate_limited_requests'] += 1
                    
                    raise RateLimitExceededError(
                        f"Rate limit exceeded for {request_type}",
                        retry_after=int(retry_after),
                        limit_type=request_type.value
                    )
            
            # Update statistics
            self.stats['total_requests'] += 1
            wait_time = time.time() - start_time
            
            # Update average wait time using exponential moving average
            alpha = 0.1  # Smoothing factor
            self.stats['average_wait_time'] = (
                alpha * wait_time + (1 - alpha) * self.stats['average_wait_time']
            )
            
            # Reset backoff on successful request
            self.current_backoff = 1.0
            
            self.logger.debug(
                f"Rate limit check passed for {request_type} "
                f"(wait: {wait_time:.3f}s, identifier: {identifier})"
            )
            
            return True
            
        except RateLimitExceededError:
            # Apply adaptive backoff
            self.current_backoff = min(
                self.current_backoff * self.backoff_multiplier,
                self.max_backoff_seconds
            )
            raise
    
    async def acquire_with_retry(
        self,
        request_type: RateLimitType = RateLimitType.MESSAGING,
        identifier: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        base_delay: float = 1.0
    ) -> bool:
        """
        Acquire permission with automatic retry on rate limit.
        
        Args:
            request_type: Type of operation
            identifier: Optional identifier
            metadata: Additional metadata
            max_retries: Maximum number of retry attempts
            base_delay: Base delay between retries
            
        Returns:
            True if permission eventually granted, False if all retries exhausted
        """
        for attempt in range(max_retries + 1):
            try:
                return await self.acquire(request_type, identifier, metadata)
            except RateLimitExceededError as e:
                if attempt >= max_retries:
                    self.logger.warning(
                        f"Max retries ({max_retries}) exhausted for {request_type}"
                    )
                    return False
                
                # Calculate delay with exponential backoff
                delay = base_delay * (2 ** attempt) + (e.retry_after or 0)
                
                self.logger.info(
                    f"Rate limited for {request_type}, retrying in {delay:.1f}s "
                    f"(attempt {attempt + 1}/{max_retries + 1})"
                )
                
                await asyncio.sleep(delay)
        
        return False
    
    def get_current_status(self) -> Dict[str, Any]:
        """
        Get current rate limiter status and statistics.
        
        Returns:
            Dictionary containing current status information
        """
        status = {
            'token_bucket': {
                'available_tokens': self.token_bucket.get_available_tokens(),
                'capacity': self.token_bucket.capacity,
                'refill_rate': self.token_bucket.refill_rate
            },
            'operation_limits': {},
            'statistics': self.stats.copy(),
            'adaptive_backoff': {
                'current_backoff': self.current_backoff,
                'max_backoff': self.max_backoff_seconds
            },
            'queue_size': self.pending_queue.qsize()
        }
        
        # Get status for each operation type
        for rate_type, limiter in self.limiters.items():
            status['operation_limits'][rate_type.value] = {
                'current_count': limiter.get_current_count(),
                'max_requests': limiter.window.max_requests,
                'window_seconds': limiter.window.window_seconds,
                'time_until_next_slot': limiter.time_until_next_slot()
            }
        
        return status
    
    def reset_statistics(self):
        """Reset rate limiter statistics."""
        self.stats = {
            'total_requests': 0,
            'rate_limited_requests': 0,
            'burst_requests': 0,
            'average_wait_time': 0.0
        }
        self.current_backoff = 1.0
    
    async def start_queue_processor(self):
        """Start background task to process queued requests."""
        if self.queue_processor_task is None or self.queue_processor_task.done():
            self.queue_processor_task = asyncio.create_task(self._process_queue())
    
    async def stop_queue_processor(self):
        """Stop background queue processor."""
        if self.queue_processor_task and not self.queue_processor_task.done():
            self.queue_processor_task.cancel()
            try:
                await self.queue_processor_task
            except asyncio.CancelledError:
                pass
    
    async def _process_queue(self):
        """Background task to process queued requests."""
        while True:
            try:
                # Get next queued request
                queued_item = await self.pending_queue.get()
                
                # Try to process it
                request_type = queued_item.get('request_type', RateLimitType.MESSAGING)
                callback = queued_item.get('callback')
                
                if callback and callable(callback):
                    try:
                        await self.acquire(request_type)
                        await callback()
                    except Exception as e:
                        self.logger.error(f"Error processing queued request: {e}")
                
                self.pending_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Queue processor error: {e}")
                await asyncio.sleep(1)  # Brief pause before continuing
    
    async def queue_request(
        self,
        callback: Callable,
        request_type: RateLimitType = RateLimitType.MESSAGING,
        priority: int = 0
    ) -> bool:
        """
        Queue a request for later processing when rate limits allow.
        
        Args:
            callback: Async function to call when rate limit permits
            request_type: Type of operation
            priority: Request priority (higher = more priority)
            
        Returns:
            True if successfully queued
        """
        try:
            await self.pending_queue.put({
                'callback': callback,
                'request_type': request_type,
                'priority': priority,
                'queued_at': time.time()
            })
            return True
        except Exception as e:
            self.logger.error(f"Failed to queue request: {e}")
            return False