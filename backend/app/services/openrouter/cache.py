"""
Response Caching Service for OpenRouter integration.
Caches AI responses for similar queries to reduce costs and improve performance.
"""

import asyncio
import logging
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

try:
    import redis.asyncio as redis
except ImportError:
    redis = None

from .types import OpenRouterResponse, ConversationContext, ChatMessage
from ...core.config import settings

logger = logging.getLogger(__name__)


class CacheStrategy(str, Enum):
    """Cache strategy options."""
    EXACT_MATCH = "exact"         # Exact message match
    SEMANTIC_SIMILAR = "semantic" # Semantic similarity
    FUZZY_MATCH = "fuzzy"        # Fuzzy string matching


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    response: OpenRouterResponse
    context: ConversationContext
    created_at: datetime
    accessed_at: datetime
    access_count: int
    ttl_seconds: int
    tags: List[str]


class ResponseCache:
    """
    Response caching service with multiple storage backends and strategies.
    
    Features:
    - Redis backend with fallback to in-memory
    - Multiple cache strategies (exact, semantic, fuzzy)
    - TTL management
    - Cache statistics and analytics
    - Smart cache invalidation
    """
    
    def __init__(self):
        """Initialize the response cache."""
        self.redis_client: Optional[redis.Redis] = None
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.cache_stats: Dict[str, int] = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "evictions": 0,
            "errors": 0
        }
        
        # Cache configuration
        self.default_ttl = getattr(settings.redis, 'REDIS_CACHE_TTL', 3600)  # 1 hour
        self.max_memory_entries = 1000
        self.similarity_threshold = 0.8
        
        logger.info("Response cache initialized")
    
    async def initialize(self):
        """Initialize cache backend connections."""
        try:
            # Try to connect to Redis
            if redis and hasattr(settings, 'redis') and settings.redis.REDIS_URL:
                self.redis_client = redis.from_url(
                    settings.redis.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    retry_on_timeout=True,
                    socket_keepalive=True,
                    socket_keepalive_options={}
                )
                
                # Test connection
                await self.redis_client.ping()
                logger.info("Redis cache backend connected")
            else:
                logger.info("Redis not available, using in-memory cache only")
                
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {str(e)}. Using in-memory cache.")
            self.redis_client = None
    
    async def close(self):
        """Close cache connections."""
        if self.redis_client:
            try:
                await self.redis_client.close()
                logger.info("Redis cache connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {str(e)}")
    
    async def get(
        self, 
        key: str,
        strategy: CacheStrategy = CacheStrategy.EXACT_MATCH,
        similarity_threshold: Optional[float] = None
    ) -> Optional[Tuple[OpenRouterResponse, ConversationContext]]:
        """
        Get cached response for a given key.
        
        Args:
            key: Cache key to lookup
            strategy: Cache lookup strategy
            similarity_threshold: Similarity threshold for fuzzy matching
            
        Returns:
            Tuple of (response, context) if found, None otherwise
        """
        try:
            # Try different lookup strategies
            cache_entry = None
            
            if strategy == CacheStrategy.EXACT_MATCH:
                cache_entry = await self._get_exact(key)
            elif strategy == CacheStrategy.FUZZY_MATCH:
                cache_entry = await self._get_fuzzy(key, similarity_threshold or self.similarity_threshold)
            elif strategy == CacheStrategy.SEMANTIC_SIMILAR:
                cache_entry = await self._get_semantic(key, similarity_threshold or self.similarity_threshold)
            
            if cache_entry:
                # Update access statistics
                cache_entry.accessed_at = datetime.utcnow()
                cache_entry.access_count += 1
                
                # Update in storage
                await self._update_entry(cache_entry)
                
                self.cache_stats["hits"] += 1
                logger.debug(f"Cache hit for key: {key[:50]}...")
                
                return (cache_entry.response, cache_entry.context)
            
            self.cache_stats["misses"] += 1
            logger.debug(f"Cache miss for key: {key[:50]}...")
            return None
            
        except Exception as e:
            self.cache_stats["errors"] += 1
            logger.error(f"Cache get error: {str(e)}")
            return None
    
    async def set(
        self,
        key: str,
        response: OpenRouterResponse,
        context: ConversationContext,
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        Cache a response with the given key.
        
        Args:
            key: Cache key
            response: AI response to cache
            context: Conversation context
            ttl: Time to live in seconds
            tags: Optional tags for categorization
            
        Returns:
            True if cached successfully, False otherwise
        """
        try:
            ttl = ttl or self.default_ttl
            tags = tags or []
            
            # Create cache entry
            cache_entry = CacheEntry(
                key=key,
                response=response,
                context=context,
                created_at=datetime.utcnow(),
                accessed_at=datetime.utcnow(),
                access_count=1,
                ttl_seconds=ttl,
                tags=tags
            )
            
            # Store in backends
            success = await self._store_entry(cache_entry)
            
            if success:
                self.cache_stats["sets"] += 1
                logger.debug(f"Cached response for key: {key[:50]}...")
            
            return success
            
        except Exception as e:
            self.cache_stats["errors"] += 1
            logger.error(f"Cache set error: {str(e)}")
            return False
    
    async def _get_exact(self, key: str) -> Optional[CacheEntry]:
        """Get entry with exact key match."""
        # Try Redis first
        if self.redis_client:
            try:
                cached_data = await self.redis_client.get(f"openrouter_cache:{key}")
                if cached_data:
                    return self._deserialize_entry(cached_data)
            except Exception as e:
                logger.warning(f"Redis get error: {str(e)}")
        
        # Fallback to memory cache
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            if not self._is_expired(entry):
                return entry
            else:
                # Remove expired entry
                del self.memory_cache[key]
        
        return None
    
    async def _get_fuzzy(self, key: str, threshold: float) -> Optional[CacheEntry]:
        """Get entry using fuzzy string matching."""
        best_match = None
        best_score = 0.0
        
        # Check memory cache for fuzzy matches
        for cached_key, entry in self.memory_cache.items():
            if self._is_expired(entry):
                continue
            
            similarity = self._calculate_string_similarity(key, cached_key)
            if similarity >= threshold and similarity > best_score:
                best_match = entry
                best_score = similarity
        
        # TODO: Implement fuzzy search in Redis using patterns or separate index
        # For now, only check memory cache
        
        return best_match
    
    async def _get_semantic(self, key: str, threshold: float) -> Optional[CacheEntry]:
        """Get entry using semantic similarity (placeholder for future implementation)."""
        # TODO: Implement semantic similarity using embeddings
        # This would require:
        # 1. Generate embeddings for cache keys
        # 2. Store embeddings in vector database or Redis with vector search
        # 3. Find semantically similar keys
        
        # For now, fall back to fuzzy matching
        return await self._get_fuzzy(key, threshold)
    
    async def _store_entry(self, entry: CacheEntry) -> bool:
        """Store cache entry in available backends."""
        success = False
        
        # Try Redis first
        if self.redis_client:
            try:
                serialized_data = self._serialize_entry(entry)
                await self.redis_client.setex(
                    f"openrouter_cache:{entry.key}",
                    entry.ttl_seconds,
                    serialized_data
                )
                success = True
            except Exception as e:
                logger.warning(f"Redis store error: {str(e)}")
        
        # Store in memory cache as backup/fallback
        try:
            # Evict entries if memory cache is full
            if len(self.memory_cache) >= self.max_memory_entries:
                await self._evict_memory_entries()
            
            self.memory_cache[entry.key] = entry
            success = True
        except Exception as e:
            logger.error(f"Memory cache store error: {str(e)}")
        
        return success
    
    async def _update_entry(self, entry: CacheEntry):
        """Update an existing cache entry."""
        # Update in Redis if available
        if self.redis_client:
            try:
                serialized_data = self._serialize_entry(entry)
                # Update without changing TTL
                await self.redis_client.set(
                    f"openrouter_cache:{entry.key}",
                    serialized_data,
                    keepttl=True
                )
            except Exception as e:
                logger.warning(f"Redis update error: {str(e)}")
        
        # Update in memory cache
        self.memory_cache[entry.key] = entry
    
    def _serialize_entry(self, entry: CacheEntry) -> str:
        """Serialize cache entry to JSON string."""
        data = {
            "key": entry.key,
            "response": entry.response.dict(),
            "context": entry.context.dict(),
            "created_at": entry.created_at.isoformat(),
            "accessed_at": entry.accessed_at.isoformat(),
            "access_count": entry.access_count,
            "ttl_seconds": entry.ttl_seconds,
            "tags": entry.tags
        }
        return json.dumps(data, ensure_ascii=False)
    
    def _deserialize_entry(self, data: str) -> CacheEntry:
        """Deserialize JSON string to cache entry."""
        parsed = json.loads(data)
        
        return CacheEntry(
            key=parsed["key"],
            response=OpenRouterResponse(**parsed["response"]),
            context=ConversationContext(**parsed["context"]),
            created_at=datetime.fromisoformat(parsed["created_at"]),
            accessed_at=datetime.fromisoformat(parsed["accessed_at"]),
            access_count=parsed["access_count"],
            ttl_seconds=parsed["ttl_seconds"],
            tags=parsed["tags"]
        )
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if a cache entry has expired."""
        expiry_time = entry.created_at + timedelta(seconds=entry.ttl_seconds)
        return datetime.utcnow() > expiry_time
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity using simple algorithm."""
        if not str1 or not str2:
            return 0.0
        
        # Simple Jaccard similarity on word sets
        words1 = set(str1.lower().split())
        words2 = set(str2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    async def _evict_memory_entries(self, count: int = 100):
        """Evict least recently used entries from memory cache."""
        if len(self.memory_cache) <= count:
            return
        
        # Sort by access time (oldest first)
        sorted_entries = sorted(
            self.memory_cache.items(),
            key=lambda x: x[1].accessed_at
        )
        
        # Remove oldest entries
        for key, _ in sorted_entries[:count]:
            del self.memory_cache[key]
            self.cache_stats["evictions"] += 1
        
        logger.debug(f"Evicted {count} entries from memory cache")
    
    async def clear(self, pattern: Optional[str] = None):
        """Clear cache entries, optionally matching a pattern."""
        try:
            if pattern:
                # Clear matching entries
                if self.redis_client:
                    # Redis pattern matching
                    keys = await self.redis_client.keys(f"openrouter_cache:*{pattern}*")
                    if keys:
                        await self.redis_client.delete(*keys)
                
                # Memory cache pattern matching
                keys_to_remove = [
                    key for key in self.memory_cache.keys()
                    if pattern in key
                ]
                for key in keys_to_remove:
                    del self.memory_cache[key]
                
                logger.info(f"Cleared cache entries matching pattern: {pattern}")
            else:
                # Clear all entries
                if self.redis_client:
                    keys = await self.redis_client.keys("openrouter_cache:*")
                    if keys:
                        await self.redis_client.delete(*keys)
                
                self.memory_cache.clear()
                logger.info("Cleared all cache entries")
                
        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics and performance metrics."""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / max(1, total_requests)) * 100
        
        # Memory cache stats
        memory_entries = len(self.memory_cache)
        memory_size = sum(len(str(entry)) for entry in self.memory_cache.values())
        
        # Redis stats (if available)
        redis_info = {}
        if self.redis_client:
            try:
                redis_info = await self.redis_client.info("memory")
            except Exception:
                redis_info = {"error": "Could not fetch Redis info"}
        
        return {
            "performance": {
                "hit_rate_percent": hit_rate,
                "total_requests": total_requests,
                **self.cache_stats
            },
            "storage": {
                "memory_cache": {
                    "entries": memory_entries,
                    "size_bytes": memory_size,
                    "max_entries": self.max_memory_entries
                },
                "redis_cache": {
                    "connected": self.redis_client is not None,
                    "info": redis_info
                }
            },
            "configuration": {
                "default_ttl_seconds": self.default_ttl,
                "similarity_threshold": self.similarity_threshold
            }
        }
    
    async def get_popular_entries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently accessed cache entries."""
        # Sort memory cache entries by access count
        sorted_entries = sorted(
            self.memory_cache.values(),
            key=lambda x: x.access_count,
            reverse=True
        )
        
        popular = []
        for entry in sorted_entries[:limit]:
            if not self._is_expired(entry):
                popular.append({
                    "key": entry.key[:100],  # Truncate long keys
                    "access_count": entry.access_count,
                    "created_at": entry.created_at.isoformat(),
                    "tags": entry.tags
                })
        
        return popular
    
    async def cleanup_expired(self):
        """Remove expired entries from memory cache."""
        expired_keys = []
        
        for key, entry in self.memory_cache.items():
            if self._is_expired(entry):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.memory_cache[key]
            self.cache_stats["evictions"] += 1
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    async def preload_common_responses(self, common_queries: List[str]):
        """Preload cache with responses for common queries (placeholder)."""
        # TODO: Implement preloading by generating responses for common queries
        # This could be done during off-peak hours
        logger.info(f"Preloading requested for {len(common_queries)} queries")
    
    def generate_cache_key(
        self,
        messages: List[ChatMessage],
        context: ConversationContext,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a consistent cache key for given inputs."""
        # Create hash from message content and context
        key_data = {
            "messages": [
                {"role": msg.role, "content": msg.content}
                for msg in messages[-3:]  # Only last 3 messages
            ],
            "language": context.language,
            "user_id": context.user_id,
            **(additional_params or {})
        }
        
        key_string = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(key_string.encode('utf-8')).hexdigest()[:32]