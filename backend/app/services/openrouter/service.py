"""
OpenRouter AI Service - Main service class for restaurant AI system.
Provides comprehensive multi-model AI capabilities with language-specific optimization.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json

from .client import OpenRouterClient
from .models import ModelManager
from .language_detector import LanguageDetector
from .cost_tracker import CostTracker
from .cache import ResponseCache
from .rate_limiter import RateLimiter
from .arabic_handler import ArabicHandler
from .prompt_templates import PromptTemplateEngine
from .types import (
    ChatMessage, ConversationContext, RequestParameters, 
    OpenRouterResponse, Language, MessageRole, ModelSelection
)
from .exceptions import (
    OpenRouterError, ModelNotAvailableError, BudgetExceededError,
    RateLimitExceededError, APIError
)
from ...core.config import settings

logger = logging.getLogger(__name__)


class OpenRouterService:
    """
    Comprehensive OpenRouter service for restaurant AI system.
    
    Features:
    - Multi-model management with automatic fallbacks
    - Language detection and routing
    - Cost tracking and budget limits
    - Response caching
    - Rate limiting
    - Arabic language and cultural support
    - Conversation context management
    """
    
    def __init__(self):
        """Initialize the OpenRouter service with all components."""
        self.client = OpenRouterClient()
        self.model_manager = ModelManager()
        self.language_detector = LanguageDetector()
        self.cost_tracker = CostTracker()
        self.cache = ResponseCache()
        self.rate_limiter = RateLimiter()
        self.arabic_handler = ArabicHandler()
        self.template_engine = PromptTemplateEngine()
        
        # Service state
        self.is_initialized = False
        self.available_models: Dict[str, Any] = {}
        
        logger.info("OpenRouter service initialized")
    
    async def initialize(self) -> bool:
        """Initialize the service and verify connectivity."""
        try:
            # Start HTTP client session
            await self.client.start_session()
            
            # Verify API connectivity
            if not await self.client.health_check():
                logger.error("OpenRouter API health check failed")
                return False
            
            # Load available models
            await self._load_available_models()
            
            # Initialize model manager with available models
            await self.model_manager.initialize(self.available_models)
            
            # Initialize other components
            await self.cache.initialize()
            
            self.is_initialized = True
            logger.info("OpenRouter service initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenRouter service: {str(e)}")
            return False
    
    async def shutdown(self):
        """Clean shutdown of all service components."""
        try:
            await self.client.close_session()
            await self.cache.close()
            logger.info("OpenRouter service shutdown complete")
        except Exception as e:
            logger.error(f"Error during service shutdown: {str(e)}")
    
    async def _load_available_models(self):
        """Load and cache available models from OpenRouter."""
        try:
            models_response = await self.client.list_models()
            self.available_models = models_response.get("data", [])
            logger.info(f"Loaded {len(self.available_models)} available models")
        except Exception as e:
            logger.warning(f"Failed to load available models: {str(e)}")
            # Use default models if API call fails
            self.available_models = []
    
    async def generate_response(
        self,
        messages: List[ChatMessage],
        context: Optional[ConversationContext] = None,
        template_name: Optional[str] = None,
        **kwargs
    ) -> Tuple[OpenRouterResponse, ConversationContext]:
        """
        Generate AI response with comprehensive error handling and optimization.
        
        Args:
            messages: List of conversation messages
            context: Optional conversation context
            template_name: Optional prompt template to use
            **kwargs: Additional parameters for model selection
            
        Returns:
            Tuple of (AI response, updated conversation context)
        """
        if not self.is_initialized:
            raise OpenRouterError("Service not initialized. Call initialize() first.")
        
        # Create or update conversation context
        if context is None:
            context = ConversationContext(
                user_id=kwargs.get("user_id", "anonymous"),
                session_id=kwargs.get("session_id", f"session_{datetime.utcnow().timestamp()}")
            )
        
        # Add new messages to context
        for msg in messages:
            context.add_message(msg)
        
        try:
            # Check rate limits
            await self.rate_limiter.check_and_wait(context.user_id)
            
            # Detect language from latest message
            latest_message = messages[-1] if messages else None
            if latest_message and context.language == Language.AUTO_DETECT:
                detection_result = await self.language_detector.detect_language(
                    latest_message.content
                )
                context.language = detection_result.detected_language
                logger.debug(f"Detected language: {context.language}")
            
            # Apply Arabic cultural context if needed
            if context.language == Language.ARABIC:
                messages = await self.arabic_handler.enhance_messages(messages, context)
            
            # Apply prompt template if specified
            if template_name:
                messages = await self.template_engine.apply_template(
                    template_name, messages, context, **kwargs
                )
            
            # Check cache for similar queries
            cache_key = self._generate_cache_key(messages, context)
            cached_response = await self.cache.get(cache_key)
            if cached_response:
                logger.debug("Returning cached response")
                return cached_response, context
            
            # Select appropriate model
            model_selection = await self.model_manager.select_model(
                language=context.language,
                context=context,
                **kwargs
            )
            
            # Check budget limits
            estimated_cost = await self._estimate_request_cost(
                messages, model_selection.selected_model
            )
            await self.cost_tracker.check_budget(estimated_cost)
            
            # Generate response with fallback
            response = await self._generate_with_fallback(
                messages, model_selection, context
            )
            
            # Track usage and costs
            await self.cost_tracker.track_usage(
                response.usage,
                model_selection.selected_model,
                estimated_cost
            )
            
            # Cache successful response
            await self.cache.set(cache_key, (response, context))
            
            # Update conversation context
            if response.choices:
                assistant_message = response.choices[0].message
                context.add_message(assistant_message)
                context.total_tokens_used += response.usage.total_tokens
            
            return response, context
            
        except (BudgetExceededError, RateLimitExceededError) as e:
            logger.warning(f"Service limit exceeded: {str(e)}")
            raise
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise OpenRouterError(f"Failed to generate response: {str(e)}")
    
    async def _generate_with_fallback(
        self,
        messages: List[ChatMessage],
        model_selection: ModelSelection,
        context: ConversationContext
    ) -> OpenRouterResponse:
        """Generate response with automatic fallback to backup models."""
        models_to_try = [model_selection.selected_model] + model_selection.fallback_models
        last_error = None
        
        for model_name in models_to_try:
            try:
                logger.debug(f"Attempting generation with model: {model_name}")
                
                # Build request parameters
                params = RequestParameters(
                    model=model_name,
                    messages=messages,
                    max_tokens=settings.openrouter.MAX_TOKENS_PER_REQUEST,
                    temperature=0.7,
                    top_p=0.9
                )
                
                # Adjust parameters based on context and language
                if context.language == Language.ARABIC:
                    params = await self.arabic_handler.adjust_parameters(params)
                
                # Make API request
                response = await self.client.create_chat_completion(params)
                
                logger.info(f"Successfully generated response using model: {model_name}")
                return response
                
            except ModelNotAvailableError as e:
                logger.warning(f"Model {model_name} not available: {str(e)}")
                last_error = e
                continue
                
            except APIError as e:
                if e.status_code in [500, 502, 503, 504]:  # Server errors, try next model
                    logger.warning(f"Server error with {model_name}: {str(e)}")
                    last_error = e
                    continue
                else:  # Client errors, don't retry
                    raise
                    
            except Exception as e:
                logger.warning(f"Error with model {model_name}: {str(e)}")
                last_error = e
                continue
        
        # If all models failed
        raise OpenRouterError(
            f"All models failed. Last error: {str(last_error)}"
        )
    
    async def _estimate_request_cost(
        self, messages: List[ChatMessage], model_name: str
    ) -> float:
        """Estimate the cost of a request before making it."""
        try:
            model_info = await self.model_manager.get_model_info(model_name)
            if not model_info:
                return 0.01  # Default estimate
            
            # Rough token estimation (4 chars per token)
            total_chars = sum(len(msg.content) for msg in messages)
            estimated_tokens = total_chars // 4
            
            # Add estimated completion tokens (usually 10-50% of prompt)
            estimated_completion_tokens = estimated_tokens * 0.3
            
            cost = (
                estimated_tokens * model_info.input_cost_per_token +
                estimated_completion_tokens * model_info.output_cost_per_token
            )
            
            return max(cost, 0.001)  # Minimum cost estimate
            
        except Exception as e:
            logger.warning(f"Failed to estimate cost: {str(e)}")
            return 0.01  # Fallback estimate
    
    def _generate_cache_key(
        self, messages: List[ChatMessage], context: ConversationContext
    ) -> str:
        """Generate cache key for similar queries."""
        # Create a hash based on message content and key context
        content_hash = hash(
            json.dumps([
                {"role": msg.role, "content": msg.content} 
                for msg in messages[-3:]  # Last 3 messages
            ], ensure_ascii=False, sort_keys=True)
        )
        
        context_hash = hash(f"{context.language}_{context.user_id}")
        return f"openrouter_{content_hash}_{context_hash}"
    
    # Public utility methods
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get comprehensive service status and health information."""
        return {
            "initialized": self.is_initialized,
            "api_health": await self.client.health_check() if self.is_initialized else False,
            "available_models": len(self.available_models),
            "cost_tracking": await self.cost_tracker.get_status(),
            "rate_limiting": await self.rate_limiter.get_status(),
            "cache_stats": await self.cache.get_stats(),
            "client_stats": self.client.get_stats()
        }
    
    async def clear_cache(self, pattern: Optional[str] = None):
        """Clear response cache, optionally matching a pattern."""
        await self.cache.clear(pattern)
        logger.info(f"Cache cleared{f' with pattern: {pattern}' if pattern else ''}")
    
    async def get_conversation_summary(
        self, context: ConversationContext
    ) -> str:
        """Generate a summary of the conversation context."""
        if not context.message_history:
            return "No conversation history"
        
        # Use the service itself to generate a summary
        summary_messages = [
            ChatMessage(
                role=MessageRole.SYSTEM,
                content="Summarize the following conversation in 2-3 sentences:"
            )
        ] + context.get_recent_messages(10)
        
        try:
            response, _ = await self.generate_response(
                messages=summary_messages,
                template_name="conversation_summary",
                user_id=context.user_id
            )
            
            if response.choices:
                return response.choices[0].message.content
            
        except Exception as e:
            logger.warning(f"Failed to generate conversation summary: {str(e)}")
        
        # Fallback to simple summary
        return f"Conversation with {len(context.message_history)} messages"
    
    async def suggest_responses(
        self, context: ConversationContext, count: int = 3
    ) -> List[str]:
        """Suggest possible responses based on conversation context."""
        if not context.message_history:
            return []
        
        suggestion_messages = context.get_recent_messages(5) + [
            ChatMessage(
                role=MessageRole.SYSTEM,
                content=f"Suggest {count} appropriate responses to continue this restaurant conversation. Return only the responses, one per line."
            )
        ]
        
        try:
            response, _ = await self.generate_response(
                messages=suggestion_messages,
                user_id=context.user_id,
                temperature=0.8  # Higher creativity for suggestions
            )
            
            if response.choices:
                suggestions = response.choices[0].message.content.strip().split('\n')
                return [s.strip() for s in suggestions if s.strip()][:count]
                
        except Exception as e:
            logger.warning(f"Failed to generate response suggestions: {str(e)}")
        
        return []