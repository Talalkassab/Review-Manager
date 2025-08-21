"""
Type definitions and data models for OpenRouter service.
"""

from typing import Optional, Dict, List, Any, Union, Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class Language(str, Enum):
    """Supported languages for model selection."""
    ARABIC = "ar"
    ENGLISH = "en"
    AUTO_DETECT = "auto"


class ModelProvider(str, Enum):
    """AI model providers available through OpenRouter."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai" 
    META = "meta-llama"
    GOOGLE = "google"


class MessageRole(str, Enum):
    """Message roles for conversation context."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    """Individual chat message in a conversation."""
    role: MessageRole
    content: str
    name: Optional[str] = None
    
    class Config:
        use_enum_values = True


class ModelInfo(BaseModel):
    """Information about an available AI model."""
    id: str
    name: str
    provider: str
    description: Optional[str] = None
    max_tokens: int = 4000
    input_cost_per_token: float = 0.0
    output_cost_per_token: float = 0.0
    supports_functions: bool = False
    supports_vision: bool = False
    context_length: int = 4000
    languages: List[Language] = [Language.ENGLISH]


class RequestParameters(BaseModel):
    """Parameters for OpenRouter API requests."""
    model: str
    messages: List[ChatMessage]
    max_tokens: Optional[int] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    stop: Optional[Union[str, List[str]]] = None
    stream: bool = False
    
    # OpenRouter specific
    transforms: Optional[List[str]] = None
    route: Optional[str] = None
    
    class Config:
        use_enum_values = True


class Usage(BaseModel):
    """Token usage information from API response."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    @property
    def cost_estimate(self) -> float:
        """Estimate cost based on token usage (approximate)."""
        # This is a rough estimate - actual costs vary by model
        return (self.prompt_tokens * 0.0001 + self.completion_tokens * 0.0002)


class ModelChoice(BaseModel):
    """A single model choice from API response."""
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None
    
    class Config:
        use_enum_values = True


class OpenRouterResponse(BaseModel):
    """Complete response from OpenRouter API."""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ModelChoice]
    usage: Usage
    
    # OpenRouter specific fields
    provider: Optional[str] = None
    request_id: Optional[str] = None


class CostTracking(BaseModel):
    """Cost tracking information for usage monitoring."""
    total_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    daily_cost: float = 0.0
    monthly_cost: float = 0.0
    last_reset: datetime = Field(default_factory=datetime.utcnow)
    
    def reset_daily(self):
        """Reset daily tracking counters."""
        self.daily_cost = 0.0
        self.last_reset = datetime.utcnow()
    
    def add_usage(self, usage: Usage, input_cost: float, output_cost: float):
        """Add usage and cost to tracking."""
        request_cost = (
            usage.prompt_tokens * input_cost + 
            usage.completion_tokens * output_cost
        )
        
        self.total_requests += 1
        self.total_tokens += usage.total_tokens
        self.total_cost += request_cost
        self.daily_cost += request_cost
        self.monthly_cost += request_cost


class RateLimitInfo(BaseModel):
    """Rate limiting information."""
    requests_per_minute: int = 60
    tokens_per_minute: int = 40000
    requests_remaining: int = 60
    tokens_remaining: int = 40000
    reset_time: Optional[datetime] = None


class LanguageDetectionResult(BaseModel):
    """Result from language detection."""
    detected_language: Language
    confidence: float = Field(ge=0.0, le=1.0)
    is_mixed: bool = False
    
    
class ModelSelection(BaseModel):
    """Result from model selection logic."""
    selected_model: str
    reason: str
    fallback_models: List[str] = []
    language: Language
    estimated_cost: float = 0.0


class ConversationContext(BaseModel):
    """Context for maintaining conversation state."""
    user_id: str
    session_id: str
    language: Language = Language.AUTO_DETECT
    cultural_context: Dict[str, Any] = Field(default_factory=dict)
    message_history: List[ChatMessage] = Field(default_factory=list)
    total_tokens_used: int = 0
    
    def add_message(self, message: ChatMessage):
        """Add a message to conversation history."""
        self.message_history.append(message)
    
    def get_recent_messages(self, count: int = 10) -> List[ChatMessage]:
        """Get recent messages from history."""
        return self.message_history[-count:] if self.message_history else []
    
    def estimate_context_tokens(self) -> int:
        """Estimate token count for current context."""
        # Rough estimation: ~4 chars per token
        total_chars = sum(len(msg.content) for msg in self.message_history)
        return total_chars // 4