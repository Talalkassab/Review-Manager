"""
AI Models for tracking usage, performance, and interactions.
"""

from datetime import datetime, date
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


class AIInteraction(Base):
    """Track all AI interactions for analysis and debugging"""
    
    __tablename__ = "ai_interactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Request details
    model_used = Column(String(100), nullable=False)
    use_case = Column(String(50), nullable=False)  # sentiment, message_gen, chat, etc.
    language = Column(String(10), nullable=False)  # ar, en
    
    # Input/Output
    input_messages = Column(JSON, nullable=False)
    output_content = Column(Text)
    
    # Performance metrics
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    response_time_seconds = Column(Float, default=0.0)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    # Cost tracking
    cost_usd = Column(Float, default=0.0)
    
    # Metadata
    user_id = Column(String(100))  # Customer or admin user
    session_id = Column(String(100))
    request_id = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Quality metrics (can be updated later)
    human_rating = Column(Integer)  # 1-5 rating if provided
    feedback = Column(Text)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "model_used": self.model_used,
            "use_case": self.use_case,
            "language": self.language,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "response_time_seconds": self.response_time_seconds,
            "success": self.success,
            "error_message": self.error_message,
            "cost_usd": self.cost_usd,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "human_rating": self.human_rating,
            "feedback": self.feedback
        }


class ModelUsage(Base):
    """Daily usage tracking for each model"""
    
    __tablename__ = "model_usage"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Model and date
    model_name = Column(String(100), nullable=False)
    usage_date = Column(Date, nullable=False, default=date.today)
    
    # Usage metrics
    total_requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    
    # Token usage
    total_input_tokens = Column(Integer, default=0)
    total_output_tokens = Column(Integer, default=0)
    
    # Cost tracking
    total_cost_usd = Column(Float, default=0.0)
    
    # Performance metrics
    average_response_time = Column(Float, default=0.0)
    success_rate = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "model_name": self.model_name,
            "usage_date": self.usage_date.isoformat() if self.usage_date else None,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": self.total_cost_usd,
            "average_response_time": self.average_response_time,
            "success_rate": self.success_rate,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class PromptTemplate(Base):
    """Store and version prompt templates"""
    
    __tablename__ = "prompt_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Template identification
    name = Column(String(100), nullable=False)
    use_case = Column(String(50), nullable=False)
    language = Column(String(10), nullable=False)
    version = Column(String(20), nullable=False)
    
    # Template content
    system_prompt = Column(Text, nullable=False)
    user_prompt_template = Column(Text)
    few_shot_examples = Column(JSON)  # List of example interactions
    
    # Metadata
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Performance tracking
    usage_count = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "name": self.name,
            "use_case": self.use_case,
            "language": self.language,
            "version": self.version,
            "system_prompt": self.system_prompt,
            "user_prompt_template": self.user_prompt_template,
            "few_shot_examples": self.few_shot_examples,
            "description": self.description,
            "is_active": self.is_active,
            "usage_count": self.usage_count,
            "average_rating": self.average_rating,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by
        }


class AIMetrics(Base):
    """Overall AI system performance metrics"""
    
    __tablename__ = "ai_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Date and period
    metric_date = Column(Date, nullable=False, default=date.today)
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly
    
    # Overall metrics
    total_requests = Column(Integer, default=0)
    total_successful = Column(Integer, default=0)
    total_failed = Column(Integer, default=0)
    overall_success_rate = Column(Float, default=0.0)
    
    # Cost metrics
    total_cost_usd = Column(Float, default=0.0)
    cost_per_request = Column(Float, default=0.0)
    budget_utilization_percent = Column(Float, default=0.0)
    
    # Performance metrics
    average_response_time = Column(Float, default=0.0)
    p95_response_time = Column(Float, default=0.0)
    p99_response_time = Column(Float, default=0.0)
    
    # Language breakdown
    arabic_requests = Column(Integer, default=0)
    english_requests = Column(Integer, default=0)
    
    # Use case breakdown
    sentiment_analysis_requests = Column(Integer, default=0)
    message_generation_requests = Column(Integer, default=0)
    chat_requests = Column(Integer, default=0)
    cultural_check_requests = Column(Integer, default=0)
    
    # Quality metrics
    average_user_rating = Column(Float, default=0.0)
    user_feedback_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "metric_date": self.metric_date.isoformat() if self.metric_date else None,
            "period_type": self.period_type,
            "total_requests": self.total_requests,
            "total_successful": self.total_successful,
            "total_failed": self.total_failed,
            "overall_success_rate": self.overall_success_rate,
            "total_cost_usd": self.total_cost_usd,
            "cost_per_request": self.cost_per_request,
            "budget_utilization_percent": self.budget_utilization_percent,
            "average_response_time": self.average_response_time,
            "p95_response_time": self.p95_response_time,
            "p99_response_time": self.p99_response_time,
            "arabic_requests": self.arabic_requests,
            "english_requests": self.english_requests,
            "sentiment_analysis_requests": self.sentiment_analysis_requests,
            "message_generation_requests": self.message_generation_requests,
            "chat_requests": self.chat_requests,
            "cultural_check_requests": self.cultural_check_requests,
            "average_user_rating": self.average_user_rating,
            "user_feedback_count": self.user_feedback_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class CustomerFeedback(Base):
    """Store customer feedback for training and analysis"""
    
    __tablename__ = "customer_feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Customer information
    customer_id = Column(String(100))
    customer_phone = Column(String(20))
    customer_name = Column(String(100))
    
    # Feedback content
    original_message = Column(Text, nullable=False)
    language = Column(String(10), nullable=False)
    
    # AI Analysis results
    sentiment_score = Column(Float)  # -1 to 1
    sentiment_label = Column(String(20))  # positive, negative, neutral
    emotion_detected = Column(String(50))
    topics_extracted = Column(JSON)  # List of topics/keywords
    
    # Restaurant context
    restaurant_location = Column(String(100))
    order_id = Column(String(100))
    visit_date = Column(DateTime)
    
    # AI Processing
    ai_response_generated = Column(Text)
    ai_model_used = Column(String(100))
    processing_time = Column(Float)
    
    # Quality assurance
    human_reviewed = Column(Boolean, default=False)
    human_sentiment_override = Column(String(20))
    staff_notes = Column(Text)
    
    # Follow-up tracking
    response_sent = Column(Boolean, default=False)
    response_method = Column(String(20))  # whatsapp, email, sms
    customer_replied = Column(Boolean, default=False)
    issue_resolved = Column(Boolean, default=False)
    
    # Timestamps
    received_at = Column(DateTime, nullable=False)
    processed_at = Column(DateTime)
    responded_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "customer_id": self.customer_id,
            "customer_phone": self.customer_phone,
            "customer_name": self.customer_name,
            "original_message": self.original_message,
            "language": self.language,
            "sentiment_score": self.sentiment_score,
            "sentiment_label": self.sentiment_label,
            "emotion_detected": self.emotion_detected,
            "topics_extracted": self.topics_extracted,
            "restaurant_location": self.restaurant_location,
            "order_id": self.order_id,
            "visit_date": self.visit_date.isoformat() if self.visit_date else None,
            "ai_response_generated": self.ai_response_generated,
            "ai_model_used": self.ai_model_used,
            "processing_time": self.processing_time,
            "human_reviewed": self.human_reviewed,
            "human_sentiment_override": self.human_sentiment_override,
            "staff_notes": self.staff_notes,
            "response_sent": self.response_sent,
            "response_method": self.response_method,
            "customer_replied": self.customer_replied,
            "issue_resolved": self.issue_resolved,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "responded_at": self.responded_at.isoformat() if self.responded_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }