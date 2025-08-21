"""
Model Manager for OpenRouter service.
Handles multiple AI models, selection logic, and model-specific configurations.
"""

import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass

from .types import (
    ModelInfo, Language, ModelSelection, ConversationContext,
    ModelProvider
)
from .exceptions import ModelNotAvailableError
from ...core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    id: str
    provider: ModelProvider
    name: str
    languages: List[Language]
    max_tokens: int
    cost_per_1k_input: float
    cost_per_1k_output: float
    context_window: int
    supports_functions: bool = False
    supports_vision: bool = False
    is_free: bool = False
    priority: int = 1  # 1=highest, 10=lowest
    cultural_context_aware: bool = False


class ModelManager:
    """
    Manages AI model selection and configuration for the OpenRouter service.
    
    Features:
    - Language-specific model routing
    - Cost-optimized model selection
    - Model availability monitoring
    - Fallback model chains
    - Performance tracking
    """
    
    def __init__(self):
        """Initialize the model manager."""
        self.available_models: Dict[str, ModelInfo] = {}
        self.model_configs: Dict[str, ModelConfig] = {}
        self.model_performance: Dict[str, Dict[str, float]] = {}
        self.unavailable_models: Set[str] = set()
        self.last_availability_check: Optional[datetime] = None
        
        self._initialize_default_configs()
        logger.info("Model manager initialized")
    
    def _initialize_default_configs(self):
        """Initialize default model configurations based on settings."""
        default_configs = [
            # Arabic-optimized models
            ModelConfig(
                id="anthropic/claude-3.5-haiku",
                provider=ModelProvider.ANTHROPIC,
                name="Claude 3.5 Haiku",
                languages=[Language.ARABIC, Language.ENGLISH],
                max_tokens=4000,
                cost_per_1k_input=0.25,
                cost_per_1k_output=1.25,
                context_window=200000,
                priority=1,
                cultural_context_aware=True
            ),
            ModelConfig(
                id="anthropic/claude-3-haiku",
                provider=ModelProvider.ANTHROPIC,
                name="Claude 3 Haiku",
                languages=[Language.ARABIC, Language.ENGLISH],
                max_tokens=4000,
                cost_per_1k_input=0.25,
                cost_per_1k_output=1.25,
                context_window=200000,
                priority=2,
                cultural_context_aware=True
            ),
            
            # English-optimized models
            ModelConfig(
                id="openai/gpt-4o-mini",
                provider=ModelProvider.OPENAI,
                name="GPT-4o Mini",
                languages=[Language.ENGLISH, Language.ARABIC],
                max_tokens=4000,
                cost_per_1k_input=0.15,
                cost_per_1k_output=0.60,
                context_window=128000,
                priority=1
            ),
            ModelConfig(
                id="openai/gpt-3.5-turbo",
                provider=ModelProvider.OPENAI,
                name="GPT-3.5 Turbo",
                languages=[Language.ENGLISH, Language.ARABIC],
                max_tokens=4000,
                cost_per_1k_input=0.50,
                cost_per_1k_output=1.50,
                context_window=16385,
                priority=3
            ),
            
            # Free tier models
            ModelConfig(
                id="meta-llama/llama-3.1-8b-instruct:free",
                provider=ModelProvider.META,
                name="Llama 3.1 8B (Free)",
                languages=[Language.ENGLISH],
                max_tokens=2000,
                cost_per_1k_input=0.0,
                cost_per_1k_output=0.0,
                context_window=8192,
                is_free=True,
                priority=5
            ),
            ModelConfig(
                id="google/gemma-2-9b-it:free",
                provider=ModelProvider.GOOGLE,
                name="Gemma 2 9B (Free)",
                languages=[Language.ENGLISH],
                max_tokens=2000,
                cost_per_1k_input=0.0,
                cost_per_1k_output=0.0,
                context_window=8192,
                is_free=True,
                priority=6
            ),
            
            # Backup models
            ModelConfig(
                id="anthropic/claude-instant-1.2",
                provider=ModelProvider.ANTHROPIC,
                name="Claude Instant 1.2",
                languages=[Language.ARABIC, Language.ENGLISH],
                max_tokens=4000,
                cost_per_1k_input=0.80,
                cost_per_1k_output=2.40,
                context_window=100000,
                priority=4
            )
        ]
        
        for config in default_configs:
            self.model_configs[config.id] = config
    
    async def initialize(self, available_models: List[Dict[str, Any]]):
        """Initialize with available models from OpenRouter API."""
        try:
            # Parse available models and update configurations
            for model_data in available_models:
                model_id = model_data.get("id", "")
                if not model_id:
                    continue
                
                # Create ModelInfo from API data
                model_info = ModelInfo(
                    id=model_id,
                    name=model_data.get("name", model_id),
                    provider=model_data.get("provider", {}).get("name", "unknown"),
                    description=model_data.get("description"),
                    max_tokens=model_data.get("top_provider", {}).get("max_completion_tokens", 4000),
                    input_cost_per_token=float(model_data.get("pricing", {}).get("prompt", "0")) / 1000000,
                    output_cost_per_token=float(model_data.get("pricing", {}).get("completion", "0")) / 1000000,
                    context_length=model_data.get("context_length", 4000)
                )
                
                self.available_models[model_id] = model_info
            
            # Update configurations with real pricing data
            for model_id, config in self.model_configs.items():
                if model_id in self.available_models:
                    api_model = self.available_models[model_id]
                    config.cost_per_1k_input = api_model.input_cost_per_token * 1000
                    config.cost_per_1k_output = api_model.output_cost_per_token * 1000
                    config.max_tokens = api_model.max_tokens
                    config.context_window = api_model.context_length
            
            logger.info(f"Model manager initialized with {len(self.available_models)} available models")
            
        except Exception as e:
            logger.error(f"Error initializing model manager: {str(e)}")
            # Continue with default configurations if API data parsing fails
    
    async def select_model(
        self,
        language: Language = Language.ENGLISH,
        context: Optional[ConversationContext] = None,
        prefer_free: bool = False,
        max_cost_per_1k: Optional[float] = None,
        require_functions: bool = False,
        **kwargs
    ) -> ModelSelection:
        """
        Select the best model for the given requirements.
        
        Args:
            language: Target language for the conversation
            context: Conversation context for context-aware selection
            prefer_free: Prefer free models when possible
            max_cost_per_1k: Maximum cost per 1k tokens
            require_functions: Whether function calling is required
            **kwargs: Additional selection criteria
            
        Returns:
            ModelSelection with selected model and fallbacks
        """
        # Get candidate models
        candidates = self._get_candidate_models(
            language=language,
            prefer_free=prefer_free,
            max_cost_per_1k=max_cost_per_1k,
            require_functions=require_functions
        )
        
        if not candidates:
            raise ModelNotAvailableError(
                model_name="any",
                available_models=list(self.model_configs.keys())
            )
        
        # Score and rank models
        scored_models = []
        for config in candidates:
            score = await self._calculate_model_score(config, language, context)
            scored_models.append((config, score))
        
        # Sort by score (higher is better)
        scored_models.sort(key=lambda x: x[1], reverse=True)
        
        # Select primary model and fallbacks
        primary_config = scored_models[0][0]
        fallback_configs = [config for config, _ in scored_models[1:4]]  # Top 3 fallbacks
        
        # Calculate estimated cost
        estimated_cost = self._estimate_model_cost(primary_config, context)
        
        return ModelSelection(
            selected_model=primary_config.id,
            reason=f"Best match for {language} with score {scored_models[0][1]:.2f}",
            fallback_models=[config.id for config in fallback_configs],
            language=language,
            estimated_cost=estimated_cost
        )
    
    def _get_candidate_models(
        self,
        language: Language,
        prefer_free: bool = False,
        max_cost_per_1k: Optional[float] = None,
        require_functions: bool = False
    ) -> List[ModelConfig]:
        """Get candidate models based on filtering criteria."""
        candidates = []
        
        for config in self.model_configs.values():
            # Skip unavailable models
            if config.id in self.unavailable_models:
                continue
            
            # Check language support
            if language != Language.AUTO_DETECT and language not in config.languages:
                continue
            
            # Check cost constraints
            if max_cost_per_1k and config.cost_per_1k_output > max_cost_per_1k:
                continue
            
            # Check function calling requirement
            if require_functions and not config.supports_functions:
                continue
            
            # Filter by free preference
            if prefer_free and not config.is_free:
                continue
            
            candidates.append(config)
        
        return candidates
    
    async def _calculate_model_score(
        self,
        config: ModelConfig,
        language: Language,
        context: Optional[ConversationContext] = None
    ) -> float:
        """Calculate a score for model selection (higher is better)."""
        score = 0.0
        
        # Base priority score (invert priority: 1=high priority gets high score)
        score += (10 - config.priority) * 10
        
        # Language matching bonus
        if language in config.languages:
            score += 20
            # Extra bonus for Arabic with cultural context awareness
            if language == Language.ARABIC and config.cultural_context_aware:
                score += 15
        
        # Cost efficiency bonus (lower cost = higher score)
        if config.is_free:
            score += 30
        else:
            # Invert cost (lower cost gets higher score)
            cost_score = max(0, 10 - (config.cost_per_1k_output / 0.5))
            score += cost_score
        
        # Context window bonus for long conversations
        if context and len(context.message_history) > 10:
            if config.context_window > 50000:
                score += 10
            elif config.context_window > 20000:
                score += 5
        
        # Performance history bonus
        model_perf = self.model_performance.get(config.id, {})
        if "success_rate" in model_perf:
            score += model_perf["success_rate"] * 15  # 0-1 scale
        if "avg_response_time" in model_perf:
            # Bonus for faster models (lower time = higher score)
            time_score = max(0, 10 - (model_perf["avg_response_time"] / 2))
            score += time_score
        
        # Availability penalty
        if config.id not in self.available_models:
            score -= 50  # Heavy penalty for unavailable models
        
        return score
    
    def _estimate_model_cost(
        self,
        config: ModelConfig,
        context: Optional[ConversationContext] = None
    ) -> float:
        """Estimate the cost for using a model with given context."""
        if config.is_free:
            return 0.0
        
        # Estimate tokens based on context or default
        if context:
            estimated_tokens = context.estimate_context_tokens()
        else:
            estimated_tokens = 500  # Default estimate
        
        # Add estimated completion tokens (usually 20-40% of input)
        completion_tokens = estimated_tokens * 0.3
        
        input_cost = (estimated_tokens / 1000) * config.cost_per_1k_input
        output_cost = (completion_tokens / 1000) * config.cost_per_1k_output
        
        return input_cost + output_cost
    
    async def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Get detailed information about a specific model."""
        return self.available_models.get(model_id)
    
    def get_model_config(self, model_id: str) -> Optional[ModelConfig]:
        """Get configuration for a specific model."""
        return self.model_configs.get(model_id)
    
    async def mark_model_unavailable(self, model_id: str, duration_minutes: int = 30):
        """Mark a model as temporarily unavailable."""
        self.unavailable_models.add(model_id)
        logger.warning(f"Marked model {model_id} as unavailable for {duration_minutes} minutes")
        
        # Schedule re-enabling (in a real implementation, use a proper scheduler)
        # For now, we'll check availability periodically
        self.last_availability_check = datetime.utcnow()
    
    async def update_model_performance(
        self,
        model_id: str,
        success: bool,
        response_time: float,
        error_type: Optional[str] = None
    ):
        """Update performance metrics for a model."""
        if model_id not in self.model_performance:
            self.model_performance[model_id] = {
                "requests": 0,
                "successes": 0,
                "total_response_time": 0.0,
                "errors": {}
            }
        
        perf = self.model_performance[model_id]
        perf["requests"] += 1
        perf["total_response_time"] += response_time
        
        if success:
            perf["successes"] += 1
        elif error_type:
            perf["errors"][error_type] = perf["errors"].get(error_type, 0) + 1
        
        # Update calculated metrics
        perf["success_rate"] = perf["successes"] / perf["requests"]
        perf["avg_response_time"] = perf["total_response_time"] / perf["requests"]
    
    async def get_models_by_language(self, language: Language) -> List[ModelConfig]:
        """Get all available models that support a specific language."""
        return [
            config for config in self.model_configs.values()
            if language in config.languages and config.id not in self.unavailable_models
        ]
    
    async def get_free_models(self) -> List[ModelConfig]:
        """Get all available free models."""
        return [
            config for config in self.model_configs.values()
            if config.is_free and config.id not in self.unavailable_models
        ]
    
    async def check_model_availability(self) -> Dict[str, bool]:
        """Check availability of all configured models."""
        availability = {}
        for model_id in self.model_configs.keys():
            availability[model_id] = (
                model_id in self.available_models and 
                model_id not in self.unavailable_models
            )
        return availability
    
    def get_performance_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get performance statistics for all models."""
        stats = {}
        for model_id, perf in self.model_performance.items():
            stats[model_id] = {
                "requests": perf.get("requests", 0),
                "success_rate": perf.get("success_rate", 0.0),
                "avg_response_time": perf.get("avg_response_time", 0.0),
                "errors": perf.get("errors", {})
            }
        return stats
    
    async def cleanup_unavailable_models(self):
        """Clean up models that have been marked unavailable for too long."""
        if not self.last_availability_check:
            return
        
        # Re-enable models after 30 minutes
        if datetime.utcnow() - self.last_availability_check > timedelta(minutes=30):
            old_count = len(self.unavailable_models)
            self.unavailable_models.clear()
            self.last_availability_check = datetime.utcnow()
            
            if old_count > 0:
                logger.info(f"Re-enabled {old_count} previously unavailable models")
    
    def get_model_recommendations(
        self, language: Language, use_case: str = "general"
    ) -> Dict[str, List[str]]:
        """Get model recommendations for specific use cases."""
        recommendations = {
            "cost_effective": [],
            "high_quality": [],
            "free_tier": []
        }
        
        # Get models for language
        language_models = [
            config for config in self.model_configs.values()
            if language in config.languages
        ]
        
        # Sort by different criteria
        cost_effective = sorted(
            language_models, 
            key=lambda x: (x.cost_per_1k_output, -x.priority)
        )
        high_quality = sorted(
            language_models,
            key=lambda x: (x.priority, x.cost_per_1k_output)
        )
        free_tier = [config for config in language_models if config.is_free]
        
        recommendations["cost_effective"] = [m.id for m in cost_effective[:3]]
        recommendations["high_quality"] = [m.id for m in high_quality[:3]]
        recommendations["free_tier"] = [m.id for m in free_tier[:3]]
        
        return recommendations