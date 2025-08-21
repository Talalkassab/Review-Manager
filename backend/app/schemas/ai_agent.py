"""
AI Agent-related Pydantic schemas.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import Field

from .base import BaseSchema, BaseResponse


class AgentPersonaCreate(BaseSchema):
    """Schema for creating a new agent persona."""
    
    name: str = Field(..., min_length=1, max_length=100, description="Persona name")
    description: Optional[str] = Field(None, description="Persona description")
    
    # Personality configuration
    personality_traits: List[str] = Field(..., min_items=1, description="Personality traits")
    tone_style: str = Field("friendly", description="Tone style")
    
    # Language and communication style
    language_style: Dict[str, Any] = Field(..., description="Language style configuration")
    
    # Response patterns
    response_patterns: Dict[str, Dict[str, str]] = Field(..., description="Response patterns by language")
    
    # Cultural awareness settings
    cultural_awareness: Dict[str, Any] = Field(..., description="Cultural awareness settings")
    
    # Restaurant association
    restaurant_id: UUID = Field(..., description="Restaurant ID")


class AgentPersonaUpdate(BaseSchema):
    """Schema for updating agent persona."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Persona name")
    description: Optional[str] = Field(None, description="Persona description")
    is_active: Optional[bool] = Field(None, description="Active status")
    is_default: Optional[bool] = Field(None, description="Default persona status")
    
    # Personality configuration
    personality_traits: Optional[List[str]] = Field(None, description="Personality traits")
    tone_style: Optional[str] = Field(None, description="Tone style")
    
    # Language and communication style
    language_style: Optional[Dict[str, Any]] = Field(None, description="Language style configuration")
    
    # Response patterns
    response_patterns: Optional[Dict[str, Dict[str, str]]] = Field(None, description="Response patterns")
    
    # Cultural awareness settings
    cultural_awareness: Optional[Dict[str, Any]] = Field(None, description="Cultural awareness settings")


class AgentPersonaResponse(BaseResponse):
    """Schema for agent persona response."""
    
    name: str = Field(..., description="Persona name")
    description: Optional[str] = Field(None, description="Persona description")
    is_active: bool = Field(..., description="Active status")
    is_default: bool = Field(..., description="Default persona status")
    
    # Personality configuration
    personality_traits: List[str] = Field(..., description="Personality traits")
    tone_style: str = Field(..., description="Tone style")
    
    # Language and communication style
    language_style: Dict[str, Any] = Field(..., description="Language style configuration")
    
    # Response patterns
    response_patterns: Dict[str, Dict[str, str]] = Field(..., description="Response patterns")
    
    # Cultural awareness settings
    cultural_awareness: Dict[str, Any] = Field(..., description="Cultural awareness settings")
    
    # Performance tracking
    usage_count: int = Field(..., description="Usage count")
    success_rate: float = Field(..., description="Success rate percentage")
    average_response_time_seconds: float = Field(..., description="Average response time")
    conversion_metrics: Optional[Dict[str, Any]] = Field(None, description="Conversion metrics")
    
    # Relationships
    restaurant_id: UUID = Field(..., description="Restaurant ID")
    created_by_user_id: UUID = Field(..., description="Created by user ID")
    
    # Computed properties
    arabic_dialect: str = Field(..., description="Arabic dialect")
    english_level: str = Field(..., description="English level")
    emoji_usage: str = Field(..., description="Emoji usage level")
    uses_religious_sensitivity: bool = Field(..., description="Uses religious sensitivity")
    respects_cultural_holidays: bool = Field(..., description="Respects cultural holidays")


class MessageFlowCreate(BaseSchema):
    """Schema for creating a message flow."""
    
    name: str = Field(..., min_length=1, max_length=200, description="Flow name")
    description: Optional[str] = Field(None, description="Flow description")
    flow_type: str = Field(..., description="Flow type")
    
    # Trigger conditions
    trigger_conditions: Dict[str, Any] = Field(..., description="Trigger conditions")
    
    # Message sequence
    message_sequence: List[Dict[str, Any]] = Field(..., min_items=1, description="Message sequence steps")
    
    # Optional configurations
    personalization_rules: Optional[Dict[str, Any]] = Field(None, description="Personalization rules")
    response_intelligence: Optional[Dict[str, Any]] = Field(None, description="Response intelligence settings")
    priority: int = Field(10, ge=1, le=100, description="Priority level")
    
    # Relationships
    restaurant_id: UUID = Field(..., description="Restaurant ID")
    default_persona_id: Optional[UUID] = Field(None, description="Default persona ID")


class MessageFlowUpdate(BaseSchema):
    """Schema for updating message flow."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Flow name")
    description: Optional[str] = Field(None, description="Flow description")
    is_active: Optional[bool] = Field(None, description="Active status")
    priority: Optional[int] = Field(None, ge=1, le=100, description="Priority level")
    
    # Trigger conditions
    trigger_conditions: Optional[Dict[str, Any]] = Field(None, description="Trigger conditions")
    
    # Message sequence
    message_sequence: Optional[List[Dict[str, Any]]] = Field(None, description="Message sequence steps")
    
    # Optional configurations
    personalization_rules: Optional[Dict[str, Any]] = Field(None, description="Personalization rules")
    response_intelligence: Optional[Dict[str, Any]] = Field(None, description="Response intelligence settings")
    
    # Relationships
    default_persona_id: Optional[UUID] = Field(None, description="Default persona ID")


class MessageFlowResponse(BaseResponse):
    """Schema for message flow response."""
    
    name: str = Field(..., description="Flow name")
    description: Optional[str] = Field(None, description="Flow description")
    flow_type: str = Field(..., description="Flow type")
    is_active: bool = Field(..., description="Active status")
    priority: int = Field(..., description="Priority level")
    
    # Configuration
    trigger_conditions: Dict[str, Any] = Field(..., description="Trigger conditions")
    message_sequence: List[Dict[str, Any]] = Field(..., description="Message sequence steps")
    personalization_rules: Optional[Dict[str, Any]] = Field(None, description="Personalization rules")
    response_intelligence: Optional[Dict[str, Any]] = Field(None, description="Response intelligence settings")
    
    # Performance tracking
    execution_count: int = Field(..., description="Execution count")
    completion_rate: float = Field(..., description="Completion rate percentage")
    average_customer_satisfaction: float = Field(..., description="Average customer satisfaction")
    
    # Relationships
    restaurant_id: UUID = Field(..., description="Restaurant ID")
    default_persona_id: Optional[UUID] = Field(None, description="Default persona ID")
    created_by_user_id: UUID = Field(..., description="Created by user ID")
    
    # Computed properties
    step_count: int = Field(..., description="Number of steps")
    estimated_duration_hours: float = Field(..., description="Estimated duration in hours")


class AIInteractionCreate(BaseSchema):
    """Schema for creating AI interaction record."""
    
    interaction_type: str = Field(..., description="Interaction type")
    trigger_event: str = Field(..., description="Trigger event")
    input_data: Dict[str, Any] = Field(..., description="Input data")
    ai_response: Dict[str, Any] = Field(..., description="AI response")
    
    # AI processing details
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="Confidence score")
    processing_time_ms: int = Field(..., ge=0, description="Processing time in ms")
    ai_model_used: str = Field(..., description="AI model used")
    model_version: Optional[str] = Field(None, description="Model version")
    
    # Token usage
    prompt_tokens: int = Field(0, ge=0, description="Prompt tokens")
    completion_tokens: int = Field(0, ge=0, description="Completion tokens")
    total_tokens: int = Field(0, ge=0, description="Total tokens")
    estimated_cost_usd: float = Field(0.0, ge=0, description="Estimated cost USD")
    
    # Context
    conversation_context: Optional[Dict[str, Any]] = Field(None, description="Conversation context")
    personalization_applied: Optional[Dict[str, Any]] = Field(None, description="Personalization applied")
    
    # Relationships
    restaurant_id: UUID = Field(..., description="Restaurant ID")
    customer_id: Optional[UUID] = Field(None, description="Customer ID")
    agent_persona_id: Optional[UUID] = Field(None, description="Agent persona ID")
    message_flow_id: Optional[UUID] = Field(None, description="Message flow ID")
    related_message_id: Optional[UUID] = Field(None, description="Related message ID")


class AIInteractionResponse(BaseResponse):
    """Schema for AI interaction response."""
    
    interaction_type: str = Field(..., description="Interaction type")
    trigger_event: str = Field(..., description="Trigger event")
    input_data: Dict[str, Any] = Field(..., description="Input data")
    ai_response: Dict[str, Any] = Field(..., description="AI response")
    
    # AI processing details
    confidence_score: Optional[float] = Field(None, description="Confidence score")
    processing_time_ms: int = Field(..., description="Processing time in ms")
    ai_model_used: str = Field(..., description="AI model used")
    model_version: Optional[str] = Field(None, description="Model version")
    
    # Token usage
    prompt_tokens: int = Field(..., description="Prompt tokens")
    completion_tokens: int = Field(..., description="Completion tokens")
    total_tokens: int = Field(..., description="Total tokens")
    estimated_cost_usd: float = Field(..., description="Estimated cost USD")
    
    # Context
    conversation_context: Optional[Dict[str, Any]] = Field(None, description="Conversation context")
    personalization_applied: Optional[Dict[str, Any]] = Field(None, description="Personalization applied")
    
    # Quality and feedback
    human_feedback_score: Optional[int] = Field(None, description="Human feedback score (1-5)")
    human_feedback_notes: Optional[str] = Field(None, description="Human feedback notes")
    customer_satisfaction_inferred: Optional[bool] = Field(None, description="Customer satisfaction inferred")
    
    # Learning and improvement
    requires_review: bool = Field(..., description="Requires review")
    review_reason: Optional[str] = Field(None, description="Review reason")
    learning_tags: Optional[List[str]] = Field(None, description="Learning tags")
    
    # Results tracking
    resulted_in_response: bool = Field(..., description="Resulted in response")
    resulted_in_escalation: bool = Field(..., description="Resulted in escalation")
    resulted_in_positive_outcome: Optional[bool] = Field(None, description="Resulted in positive outcome")
    
    # Relationships
    restaurant_id: UUID = Field(..., description="Restaurant ID")
    customer_id: Optional[UUID] = Field(None, description="Customer ID")
    agent_persona_id: Optional[UUID] = Field(None, description="Agent persona ID")
    message_flow_id: Optional[UUID] = Field(None, description="Message flow ID")
    related_message_id: Optional[UUID] = Field(None, description="Related message ID")
    
    # Computed properties
    is_successful: Optional[bool] = Field(None, description="Is successful")
    response_quality_score: float = Field(..., description="Response quality score")


class AIInteractionFeedback(BaseSchema):
    """Schema for AI interaction feedback."""
    
    score: int = Field(..., ge=1, le=5, description="Feedback score (1-5)")
    notes: Optional[str] = Field(None, max_length=1000, description="Feedback notes")
    tags: Optional[List[str]] = Field(None, description="Feedback tags")


class AIModelConfig(BaseSchema):
    """Schema for AI model configuration."""
    
    primary_model_arabic: str = Field(..., description="Primary Arabic model")
    fallback_model_english: str = Field(..., description="Fallback English model")
    fallback_model_free: str = Field(..., description="Fallback free model")
    max_tokens_per_request: int = Field(4000, gt=0, description="Max tokens per request")
    temperature: float = Field(0.7, ge=0, le=2, description="Model temperature")
    presence_penalty: float = Field(0.0, ge=-2, le=2, description="Presence penalty")
    frequency_penalty: float = Field(0.0, ge=-2, le=2, description="Frequency penalty")


class ConversationTestRequest(BaseSchema):
    """Schema for conversation testing request."""
    
    persona_id: UUID = Field(..., description="Persona ID to test")
    test_scenarios: List[Dict[str, Any]] = Field(..., min_items=1, description="Test scenarios")
    customer_profile: Optional[Dict[str, Any]] = Field(None, description="Customer profile simulation")
    language: str = Field("ar", pattern="^(ar|en)$", description="Test language")


class ConversationTestResponse(BaseSchema):
    """Schema for conversation test response."""
    
    test_id: UUID = Field(..., description="Test ID")
    persona_id: UUID = Field(..., description="Persona ID")
    test_results: List[Dict[str, Any]] = Field(..., description="Test results per scenario")
    overall_score: float = Field(..., ge=0, le=100, description="Overall test score")
    performance_metrics: Dict[str, Any] = Field(..., description="Performance metrics")
    recommendations: List[str] = Field(..., description="Improvement recommendations")
    cultural_sensitivity_score: float = Field(..., description="Cultural sensitivity score")
    response_consistency_score: float = Field(..., description="Response consistency score")


class AIAnalytics(BaseSchema):
    """Schema for AI system analytics."""
    
    period: str = Field(..., description="Analytics period")
    total_interactions: int = Field(..., description="Total AI interactions")
    successful_interactions: int = Field(..., description="Successful interactions")
    failed_interactions: int = Field(..., description="Failed interactions")
    average_confidence_score: float = Field(..., description="Average confidence score")
    average_processing_time_ms: float = Field(..., description="Average processing time")
    total_tokens_used: int = Field(..., description="Total tokens used")
    total_cost_usd: float = Field(..., description="Total cost USD")
    model_usage_distribution: Dict[str, int] = Field(..., description="Model usage distribution")
    interaction_types: Dict[str, int] = Field(..., description="Interaction type distribution")
    personas_performance: List[Dict[str, Any]] = Field(..., description="Persona performance data")
    top_triggers: List[Dict[str, Any]] = Field(..., description="Top trigger events")
    quality_scores: Dict[str, float] = Field(..., description="Quality score distribution")


class PersonaListFilter(BaseSchema):
    """Schema for filtering persona lists."""
    
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(None, description="Search term")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    tone_style: Optional[str] = Field(None, description="Filter by tone style")
    created_by: Optional[UUID] = Field(None, description="Filter by creator")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")