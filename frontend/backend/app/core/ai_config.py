"""
AI Configuration for OpenRouter Integration
Handles model selection, cost management, and cultural context settings.
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import os


class ModelType(str, Enum):
    """Available AI models through OpenRouter"""
    CLAUDE_3_5_HAIKU = "anthropic/claude-3.5-haiku"
    GPT_4O_MINI = "openai/gpt-4o-mini"
    LLAMA_3_1_8B = "meta-llama/llama-3.1-8b-instruct"
    CLAUDE_3_5_SONNET = "anthropic/claude-3.5-sonnet"
    GPT_4O = "openai/gpt-4o"


class Language(str, Enum):
    """Supported languages"""
    ARABIC = "ar"
    ENGLISH = "en"
    AUTO_DETECT = "auto"


class UseCase(str, Enum):
    """Different AI use cases"""
    SENTIMENT_ANALYSIS = "sentiment"
    MESSAGE_GENERATION = "message_gen"
    CULTURAL_CHECK = "cultural"
    CHAT_RESPONSE = "chat"
    PERSONA_MANAGEMENT = "persona"


class ModelConfig(BaseModel):
    """Configuration for a specific model"""
    model_name: ModelType
    cost_per_1k_tokens: float
    max_tokens: int
    temperature: float = 0.7
    top_p: float = 0.9
    supports_arabic: bool = True
    performance_tier: str = Field(..., description="high, medium, low")
    fallback_models: List[ModelType] = []


class CostLimits(BaseModel):
    """Cost management configuration"""
    daily_budget_usd: float = 50.0
    monthly_budget_usd: float = 1000.0
    alert_threshold_percent: float = 80.0
    emergency_stop_percent: float = 95.0
    free_tier_daily_limit: int = 100  # Number of requests


class PerformanceThresholds(BaseModel):
    """Performance monitoring thresholds"""
    max_response_time_seconds: float = 30.0
    min_success_rate_percent: float = 95.0
    max_retry_attempts: int = 3
    rate_limit_requests_per_minute: int = 60


class CulturalContext(BaseModel):
    """Cultural context settings for Arabic users"""
    respect_religious_values: bool = True
    use_formal_language: bool = True
    avoid_controversial_topics: List[str] = [
        "politics", "religion", "personal_relationships"
    ]
    preferred_greetings: Dict[str, List[str]] = {
        "ar": ["السلام عليكم", "أهلاً وسهلاً", "مرحباً"],
        "en": ["Welcome", "Hello", "Good day"]
    }
    time_zone: str = "Asia/Riyadh"


class AIConfig:
    """Main AI configuration class"""
    
    def __init__(self):
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_base_url = "https://openrouter.ai/api/v1"
        self.site_url = os.getenv("SITE_URL", "https://restaurant-ai.com")
        self.app_name = os.getenv("APP_NAME", "Restaurant AI Feedback Agent")
        
        # Model configurations
        self.models = {
            ModelType.CLAUDE_3_5_HAIKU: ModelConfig(
                model_name=ModelType.CLAUDE_3_5_HAIKU,
                cost_per_1k_tokens=0.25,
                max_tokens=4096,
                temperature=0.7,
                supports_arabic=True,
                performance_tier="high",
                fallback_models=[ModelType.GPT_4O_MINI, ModelType.LLAMA_3_1_8B]
            ),
            ModelType.GPT_4O_MINI: ModelConfig(
                model_name=ModelType.GPT_4O_MINI,
                cost_per_1k_tokens=0.15,
                max_tokens=4096,
                temperature=0.7,
                supports_arabic=False,
                performance_tier="medium",
                fallback_models=[ModelType.CLAUDE_3_5_HAIKU, ModelType.LLAMA_3_1_8B]
            ),
            ModelType.LLAMA_3_1_8B: ModelConfig(
                model_name=ModelType.LLAMA_3_1_8B,
                cost_per_1k_tokens=0.08,
                max_tokens=2048,
                temperature=0.8,
                supports_arabic=False,
                performance_tier="low",
                fallback_models=[ModelType.GPT_4O_MINI, ModelType.CLAUDE_3_5_HAIKU]
            ),
            ModelType.CLAUDE_3_5_SONNET: ModelConfig(
                model_name=ModelType.CLAUDE_3_5_SONNET,
                cost_per_1k_tokens=3.0,
                max_tokens=8192,
                temperature=0.7,
                supports_arabic=True,
                performance_tier="high",
                fallback_models=[ModelType.CLAUDE_3_5_HAIKU, ModelType.GPT_4O_MINI]
            ),
            ModelType.GPT_4O: ModelConfig(
                model_name=ModelType.GPT_4O,
                cost_per_1k_tokens=5.0,
                max_tokens=8192,
                temperature=0.7,
                supports_arabic=False,
                performance_tier="high",
                fallback_models=[ModelType.GPT_4O_MINI, ModelType.CLAUDE_3_5_HAIKU]
            )
        }
        
        # Model selection rules
        self.model_selection_rules = {
            (Language.ARABIC, UseCase.SENTIMENT_ANALYSIS): ModelType.CLAUDE_3_5_HAIKU,
            (Language.ARABIC, UseCase.MESSAGE_GENERATION): ModelType.CLAUDE_3_5_HAIKU,
            (Language.ARABIC, UseCase.CULTURAL_CHECK): ModelType.CLAUDE_3_5_HAIKU,
            (Language.ARABIC, UseCase.CHAT_RESPONSE): ModelType.CLAUDE_3_5_HAIKU,
            (Language.ARABIC, UseCase.PERSONA_MANAGEMENT): ModelType.CLAUDE_3_5_HAIKU,
            
            (Language.ENGLISH, UseCase.SENTIMENT_ANALYSIS): ModelType.GPT_4O_MINI,
            (Language.ENGLISH, UseCase.MESSAGE_GENERATION): ModelType.GPT_4O_MINI,
            (Language.ENGLISH, UseCase.CULTURAL_CHECK): ModelType.GPT_4O_MINI,
            (Language.ENGLISH, UseCase.CHAT_RESPONSE): ModelType.GPT_4O_MINI,
            (Language.ENGLISH, UseCase.PERSONA_MANAGEMENT): ModelType.GPT_4O_MINI,
        }
        
        # Free tier fallbacks
        self.free_tier_model = ModelType.LLAMA_3_1_8B
        
        # Cost and performance settings
        self.cost_limits = CostLimits()
        self.performance_thresholds = PerformanceThresholds()
        self.cultural_context = CulturalContext()
    
    def get_model_for_task(
        self, 
        language: Language, 
        use_case: UseCase, 
        is_free_tier: bool = False
    ) -> ModelType:
        """
        Select the best model for a given task and language.
        
        Args:
            language: The language of the content
            use_case: The type of AI task
            is_free_tier: Whether to use free tier model
            
        Returns:
            The recommended model type
        """
        if is_free_tier:
            return self.free_tier_model
        
        # Get the preferred model for this combination
        model = self.model_selection_rules.get(
            (language, use_case), 
            ModelType.CLAUDE_3_5_HAIKU
        )
        
        return model
    
    def get_model_config(self, model_type: ModelType) -> ModelConfig:
        """Get configuration for a specific model"""
        return self.models[model_type]
    
    def get_fallback_models(self, primary_model: ModelType) -> List[ModelType]:
        """Get fallback models for a primary model"""
        return self.models[primary_model].fallback_models
    
    def calculate_estimated_cost(
        self, 
        model_type: ModelType, 
        input_tokens: int, 
        output_tokens: int
    ) -> float:
        """
        Calculate estimated cost for a request.
        
        Args:
            model_type: The model being used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        config = self.models[model_type]
        total_tokens = input_tokens + output_tokens
        cost = (total_tokens / 1000) * config.cost_per_1k_tokens
        return round(cost, 6)


# Global configuration instance
ai_config = AIConfig()