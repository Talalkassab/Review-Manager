"""
AI Agent models for managing agent personas, interactions, and configurations.
Handles the configurable AI behavior system and learning optimization.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, LanguageChoice, SentimentChoice
from ..core.logging import get_logger

logger = get_logger(__name__)


class AgentPersona(Base):
    """
    Agent persona model for configurable AI behavior.
    Defines personality, tone, cultural awareness, and response patterns.
    """
    
    __tablename__ = "agent_personas"
    
    # Basic persona information
    name = Column(String(100), nullable=False, index=True)  # "Friendly Sarah", "Professional Ahmad"
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    
    # Personality configuration
    personality_traits = Column(JSON, nullable=False)  # ["warm", "helpful", "respectful", "culturally_aware"]
    tone_style = Column(String(20), default="friendly", nullable=False)  # formal, casual, friendly, professional
    
    # Language and communication style
    language_style = Column(JSON, nullable=False)  # Arabic dialect, English level, emoji usage
    
    # Response patterns
    response_patterns = Column(JSON, nullable=False)  # Greeting, follow-up, thank you styles
    
    # Cultural awareness settings
    cultural_awareness = Column(JSON, nullable=False)  # Religious sensitivity, holidays, etiquette
    
    # Performance tracking
    usage_count = Column(Integer, default=0, nullable=False)
    success_rate = Column(Float, default=0.0, nullable=False)  # Based on positive responses
    average_response_time_seconds = Column(Float, default=0.0, nullable=False)
    
    # A/B testing results
    conversion_metrics = Column(JSON, nullable=True)  # Performance metrics from A/B tests
    
    # Foreign keys
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id"), nullable=False, index=True)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    restaurant = relationship("Restaurant")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    ai_interactions = relationship("AIInteraction", back_populates="agent_persona")
    message_flows = relationship("MessageFlow", back_populates="default_persona")
    
    @property
    def arabic_dialect(self) -> str:
        """Get Arabic dialect preference."""
        return self.language_style.get("arabic_dialect", "gulf")
    
    @property
    def english_level(self) -> str:
        """Get English proficiency level."""
        return self.language_style.get("english_level", "business")
    
    @property
    def emoji_usage(self) -> str:
        """Get emoji usage preference."""
        return self.language_style.get("emoji_usage", "moderate")
    
    @property
    def uses_religious_sensitivity(self) -> bool:
        """Check if persona uses religious sensitivity."""
        return self.cultural_awareness.get("religious_sensitivity", True)
    
    @property
    def respects_cultural_holidays(self) -> bool:
        """Check if persona respects cultural holidays."""
        return bool(self.cultural_awareness.get("cultural_holidays", []))
    
    def get_greeting_template(self, language: str = None) -> str:
        """Get greeting template for specified language."""
        lang = language or LanguageChoice.ARABIC
        patterns = self.response_patterns.get(lang, {})
        return patterns.get("greeting_style", "مرحباً! كيف يمكنني مساعدتك؟")
    
    def get_follow_up_template(self, language: str = None) -> str:
        """Get follow-up template for specified language."""
        lang = language or LanguageChoice.ARABIC
        patterns = self.response_patterns.get(lang, {})
        return patterns.get("follow_up_style", "نود معرفة رأيك في تجربتك معنا")
    
    def get_thank_you_template(self, language: str = None) -> str:
        """Get thank you template for specified language."""
        lang = language or LanguageChoice.ARABIC
        patterns = self.response_patterns.get(lang, {})
        return patterns.get("thank_you_style", "شكراً جزيلاً لوقتك الثمين")
    
    def increment_usage(self):
        """Increment usage counter."""
        self.usage_count += 1
        logger.info(f"Agent persona usage incremented: {self.name} - {self.usage_count}")
    
    def update_performance_metrics(self, response_time_seconds: float, was_successful: bool):
        """Update performance metrics."""
        # Update average response time
        if self.usage_count > 0:
            total_time = self.average_response_time_seconds * (self.usage_count - 1)
            self.average_response_time_seconds = (total_time + response_time_seconds) / self.usage_count
        else:
            self.average_response_time_seconds = response_time_seconds
        
        # Update success rate
        if was_successful:
            successful_interactions = self.success_rate * (self.usage_count - 1) / 100
            self.success_rate = ((successful_interactions + 1) / self.usage_count) * 100
        else:
            successful_interactions = self.success_rate * (self.usage_count - 1) / 100
            self.success_rate = (successful_interactions / self.usage_count) * 100
        
        logger.info(f"Updated performance metrics for persona {self.name}: success_rate={self.success_rate:.2f}%")
    
    def get_persona_config(self) -> Dict[str, Any]:
        """Get complete persona configuration."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "personality_traits": self.personality_traits,
            "tone_style": self.tone_style,
            "language_style": self.language_style,
            "response_patterns": self.response_patterns,
            "cultural_awareness": self.cultural_awareness,
            "performance_metrics": {
                "usage_count": self.usage_count,
                "success_rate": self.success_rate,
                "average_response_time": self.average_response_time_seconds
            }
        }
    
    def __repr__(self) -> str:
        """String representation of agent persona."""
        return f"<AgentPersona(name={self.name}, tone={self.tone_style}, active={self.is_active})>"


class MessageFlow(Base):
    """
    Message flow model for defining multi-step conversation sequences.
    Handles trigger conditions, message steps, and response handling.
    """
    
    __tablename__ = "message_flows"
    
    # Basic flow information
    name = Column(String(200), nullable=False, index=True)  # "Standard Follow-up", "VIP Customer", etc.
    description = Column(Text, nullable=True)
    flow_type = Column(String(50), nullable=False)  # standard_followup, complaint_resolution, vip_customer
    
    # Status and activation
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=10, nullable=False)  # Higher number = higher priority
    
    # Trigger conditions
    trigger_conditions = Column(JSON, nullable=False)  # Customer type, timing, visit amount, etc.
    
    # Message sequence configuration
    message_sequence = Column(JSON, nullable=False)  # Array of message steps
    
    # Personalization rules
    personalization_rules = Column(JSON, nullable=True)  # Rules for personalizing messages
    
    # Response intelligence settings
    response_intelligence = Column(JSON, nullable=True)  # Sentiment handling, escalation rules
    
    # Performance tracking
    execution_count = Column(Integer, default=0, nullable=False)
    completion_rate = Column(Float, default=0.0, nullable=False)
    average_customer_satisfaction = Column(Float, default=0.0, nullable=False)
    
    # Foreign keys
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id"), nullable=False, index=True)
    default_persona_id = Column(UUID(as_uuid=True), ForeignKey("agent_personas.id"), nullable=True)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    restaurant = relationship("Restaurant")
    default_persona = relationship("AgentPersona", back_populates="message_flows")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    
    @property
    def step_count(self) -> int:
        """Get number of steps in the message flow."""
        return len(self.message_sequence) if self.message_sequence else 0
    
    @property
    def estimated_duration_hours(self) -> float:
        """Get estimated flow duration in hours."""
        if not self.message_sequence:
            return 0.0
        
        total_delay = sum(step.get("delay_hours", 0) for step in self.message_sequence)
        return total_delay
    
    def matches_trigger_conditions(self, customer_data: Dict[str, Any]) -> bool:
        """Check if customer matches trigger conditions."""
        if not self.trigger_conditions:
            return False
        
        # Check customer type
        customer_type = self.trigger_conditions.get("customer_type", "all")
        if customer_type != "all":
            if customer_data.get("type") != customer_type:
                return False
        
        # Check time after visit
        time_after_visit = self.trigger_conditions.get("time_after_visit")
        if time_after_visit:
            hours_since_visit = customer_data.get("hours_since_visit", 0)
            if hours_since_visit < time_after_visit:
                return False
        
        # Check visit amount range
        amount_range = self.trigger_conditions.get("visit_amount_range")
        if amount_range:
            order_total = customer_data.get("order_total", 0)
            if not (amount_range.get("min", 0) <= order_total <= amount_range.get("max", float('inf'))):
                return False
        
        # Check previous sentiment
        previous_sentiment = self.trigger_conditions.get("previous_sentiment")
        if previous_sentiment and previous_sentiment != "none":
            if customer_data.get("previous_sentiment") != previous_sentiment:
                return False
        
        return True
    
    def get_step(self, step_number: int) -> Optional[Dict[str, Any]]:
        """Get specific message step by number."""
        if not self.message_sequence or step_number < 1:
            return None
        
        for step in self.message_sequence:
            if step.get("step_number") == step_number:
                return step
        return None
    
    def get_next_step(self, current_step: int) -> Optional[Dict[str, Any]]:
        """Get next message step."""
        return self.get_step(current_step + 1)
    
    def increment_execution(self):
        """Increment execution counter."""
        self.execution_count += 1
        logger.info(f"Message flow execution incremented: {self.name} - {self.execution_count}")
    
    def update_completion_metrics(self, completed: bool, satisfaction_score: float = None):
        """Update flow completion metrics."""
        if completed:
            completed_flows = (self.completion_rate * (self.execution_count - 1)) / 100
            self.completion_rate = ((completed_flows + 1) / self.execution_count) * 100
        else:
            completed_flows = (self.completion_rate * (self.execution_count - 1)) / 100
            self.completion_rate = (completed_flows / self.execution_count) * 100
        
        # Update satisfaction if provided
        if satisfaction_score is not None:
            if self.execution_count > 1:
                total_satisfaction = self.average_customer_satisfaction * (self.execution_count - 1)
                self.average_customer_satisfaction = (total_satisfaction + satisfaction_score) / self.execution_count
            else:
                self.average_customer_satisfaction = satisfaction_score
        
        logger.info(f"Updated completion metrics for flow {self.name}: completion_rate={self.completion_rate:.2f}%")
    
    def get_flow_summary(self) -> Dict[str, Any]:
        """Get message flow summary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "flow_type": self.flow_type,
            "is_active": self.is_active,
            "priority": self.priority,
            "step_count": self.step_count,
            "estimated_duration_hours": self.estimated_duration_hours,
            "execution_count": self.execution_count,
            "completion_rate": self.completion_rate,
            "average_satisfaction": self.average_customer_satisfaction,
            "trigger_conditions": self.trigger_conditions
        }
    
    def __repr__(self) -> str:
        """String representation of message flow."""
        return f"<MessageFlow(name={self.name}, type={self.flow_type}, steps={self.step_count})>"


class AIInteraction(Base):
    """
    AI interaction model for tracking all AI-powered customer interactions.
    Records AI decisions, responses, and learning data.
    """
    
    __tablename__ = "ai_interactions"
    
    # Interaction metadata
    interaction_type = Column(String(50), nullable=False, index=True)  # message_response, sentiment_analysis, escalation_decision
    trigger_event = Column(String(100), nullable=False)  # customer_message, scheduled_followup, complaint_detected
    
    # AI processing details
    input_data = Column(JSON, nullable=False)  # Input that triggered the AI interaction
    ai_response = Column(JSON, nullable=False)  # AI's response/decision
    confidence_score = Column(Float, nullable=True)  # AI confidence in its response (0.0-1.0)
    processing_time_ms = Column(Integer, nullable=False)  # Time taken to process
    
    # Model information
    ai_model_used = Column(String(100), nullable=False)  # Model that generated the response
    model_version = Column(String(50), nullable=True)
    prompt_tokens = Column(Integer, default=0, nullable=False)
    completion_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    estimated_cost_usd = Column(Float, default=0.0, nullable=False)
    
    # Context and personalization
    conversation_context = Column(JSON, nullable=True)  # Conversation history and context
    personalization_applied = Column(JSON, nullable=True)  # Personalization rules applied
    
    # Quality and feedback
    human_feedback_score = Column(Integer, nullable=True)  # 1-5 rating from human review
    human_feedback_notes = Column(Text, nullable=True)
    customer_satisfaction_inferred = Column(Boolean, nullable=True)  # Inferred from customer response
    
    # Learning and improvement
    requires_review = Column(Boolean, default=False, nullable=False)
    review_reason = Column(String(200), nullable=True)
    learning_tags = Column(JSON, nullable=True)  # Tags for ML training
    
    # Results tracking
    resulted_in_response = Column(Boolean, default=False, nullable=False)
    resulted_in_escalation = Column(Boolean, default=False, nullable=False)
    resulted_in_positive_outcome = Column(Boolean, nullable=True)
    
    # Foreign keys
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True, index=True)
    agent_persona_id = Column(UUID(as_uuid=True), ForeignKey("agent_personas.id"), nullable=True)
    message_flow_id = Column(UUID(as_uuid=True), ForeignKey("message_flows.id"), nullable=True)
    related_message_id = Column(UUID(as_uuid=True), ForeignKey("whatsapp_messages.id"), nullable=True)
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="ai_interactions")
    customer = relationship("Customer", back_populates="ai_interactions")
    agent_persona = relationship("AgentPersona", back_populates="ai_interactions")
    message_flow = relationship("MessageFlow")
    related_message = relationship("WhatsAppMessage")
    
    @property
    def is_successful(self) -> Optional[bool]:
        """Determine if interaction was successful."""
        if self.resulted_in_positive_outcome is not None:
            return self.resulted_in_positive_outcome
        
        # Infer from other metrics
        if self.human_feedback_score:
            return self.human_feedback_score >= 4
        
        if self.customer_satisfaction_inferred is not None:
            return self.customer_satisfaction_inferred
        
        return None
    
    @property
    def response_quality_score(self) -> float:
        """Calculate response quality score."""
        score = 0.0
        factors = 0
        
        # Confidence score
        if self.confidence_score:
            score += self.confidence_score * 0.3
            factors += 0.3
        
        # Human feedback
        if self.human_feedback_score:
            score += (self.human_feedback_score / 5.0) * 0.4
            factors += 0.4
        
        # Customer satisfaction
        if self.customer_satisfaction_inferred:
            score += 0.3
            factors += 0.3
        
        return score / factors if factors > 0 else 0.0
    
    def record_human_feedback(self, score: int, notes: str = None):
        """Record human feedback on AI interaction."""
        if not (1 <= score <= 5):
            raise ValueError("Feedback score must be between 1 and 5")
        
        self.human_feedback_score = score
        self.human_feedback_notes = notes
        
        # Update persona performance if linked
        if self.agent_persona_id:
            # This would trigger persona performance update
            pass
        
        logger.info(f"Human feedback recorded for AI interaction {self.id}: score={score}")
    
    def mark_for_review(self, reason: str):
        """Mark interaction for human review."""
        self.requires_review = True
        self.review_reason = reason
        logger.info(f"AI interaction marked for review: {self.id}, reason: {reason}")
    
    def record_outcome(self, positive: bool, resulted_in_response: bool = False, resulted_in_escalation: bool = False):
        """Record the outcome of the AI interaction."""
        self.resulted_in_positive_outcome = positive
        self.resulted_in_response = resulted_in_response
        self.resulted_in_escalation = resulted_in_escalation
        
        # Update persona performance if linked
        if self.agent_persona and positive is not None:
            self.agent_persona.update_performance_metrics(
                self.processing_time_ms / 1000.0,
                positive
            )
    
    def get_interaction_summary(self) -> Dict[str, Any]:
        """Get interaction summary for analytics."""
        return {
            "id": str(self.id),
            "interaction_type": self.interaction_type,
            "trigger_event": self.trigger_event,
            "ai_model_used": self.ai_model_used,
            "confidence_score": self.confidence_score,
            "processing_time_ms": self.processing_time_ms,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": self.estimated_cost_usd,
            "response_quality_score": self.response_quality_score,
            "is_successful": self.is_successful,
            "requires_review": self.requires_review,
            "created_at": self.created_at.isoformat()
        }
    
    def __repr__(self) -> str:
        """String representation of AI interaction."""
        return f"<AIInteraction(type={self.interaction_type}, model={self.ai_model_used}, confidence={self.confidence_score})>"