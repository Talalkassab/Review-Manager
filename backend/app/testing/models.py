"""
Testing System Database Models
=============================

Database models for the comprehensive agent testing system.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, JSON, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum

from ..models.base import BaseModel

Base = declarative_base()

class TestSessionStatus(enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    FAILED = "failed"

class TestScenarioType(enum.Enum):
    CONVERSATION = "conversation"
    AB_TEST = "ab_test"
    SCENARIO = "scenario"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"

class CustomerProfileType(enum.Enum):
    HAPPY_CUSTOMER = "happy_customer"
    DISSATISFIED_CUSTOMER = "dissatisfied_customer"
    FIRST_TIME_VISITOR = "first_time_visitor"
    REPEAT_CUSTOMER = "repeat_customer"
    VIP_CUSTOMER = "vip_customer"
    COMPLAINT_CUSTOMER = "complaint_customer"

class TestSession(BaseModel):
    """Test session for tracking testing activities"""
    __tablename__ = "test_sessions"
    
    session_name = Column(String(200), nullable=False)
    session_type = Column(Enum(TestScenarioType), nullable=False)
    status = Column(Enum(TestSessionStatus), default=TestSessionStatus.ACTIVE)
    
    # Configuration
    agent_persona_id = Column(String(100))
    customer_profile_config = Column(JSON)
    test_parameters = Column(JSON)
    
    # Metrics
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    total_interactions = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    
    # Results
    test_results = Column(JSON)
    performance_metrics = Column(JSON)
    recommendations = Column(JSON)
    
    # Relationships
    conversations = relationship("TestConversation", back_populates="session")
    ab_tests = relationship("ABTest", back_populates="session")

class TestConversation(BaseModel):
    """Individual test conversation within a session"""
    __tablename__ = "test_conversations"
    
    session_id = Column(Integer, ForeignKey("test_sessions.id"))
    conversation_name = Column(String(200))
    
    # Customer simulation
    customer_profile_type = Column(Enum(CustomerProfileType))
    customer_demographics = Column(JSON)
    customer_context = Column(JSON)
    
    # Conversation flow
    conversation_messages = Column(JSON)  # List of messages with metadata
    conversation_start = Column(DateTime, default=datetime.utcnow)
    conversation_end = Column(DateTime)
    
    # Analysis results
    sentiment_analysis = Column(JSON)
    response_times = Column(JSON)
    persona_consistency_score = Column(Float)
    cultural_sensitivity_score = Column(Float)
    overall_score = Column(Float)
    
    # Relationships
    session = relationship("TestSession", back_populates="conversations")

class ABTest(BaseModel):
    """A/B test configuration and results"""
    __tablename__ = "ab_tests"
    
    session_id = Column(Integer, ForeignKey("test_sessions.id"))
    test_name = Column(String(200), nullable=False)
    test_description = Column(Text)
    
    # Test configuration
    variants = Column(JSON)  # List of message variants
    target_metrics = Column(JSON)  # Success metrics to track
    sample_size = Column(Integer)
    confidence_threshold = Column(Float, default=0.95)
    duration_days = Column(Integer, default=7)
    
    # Test execution
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Results
    variant_results = Column(JSON)
    statistical_analysis = Column(JSON)
    winner_variant = Column(String(100))
    confidence_level = Column(Float)
    
    # Relationships
    session = relationship("TestSession", back_populates="ab_tests")

class TestScenario(BaseModel):
    """Predefined test scenarios"""
    __tablename__ = "test_scenarios"
    
    scenario_name = Column(String(200), nullable=False)
    scenario_type = Column(String(100))  # complaint_handling, cultural_sensitivity, etc.
    difficulty_level = Column(String(50))  # easy, medium, hard
    
    # Scenario definition
    description = Column(Text)
    customer_profile = Column(JSON)
    conversation_steps = Column(JSON)
    success_criteria = Column(JSON)
    expected_behaviors = Column(JSON)
    
    # Metadata
    tags = Column(JSON)  # For categorization and search
    is_active = Column(Boolean, default=True)
    created_by = Column(String(100))
    usage_count = Column(Integer, default=0)

class SyntheticCustomer(BaseModel):
    """Generated synthetic customer profiles for testing"""
    __tablename__ = "synthetic_customers"
    
    profile_name = Column(String(200))
    profile_type = Column(Enum(CustomerProfileType))
    
    # Demographics
    age_range = Column(String(50))
    gender = Column(String(50))
    language_preference = Column(String(50))
    cultural_background = Column(String(100))
    location = Column(String(100))
    
    # Behavioral traits
    communication_style = Column(String(50))  # direct, polite, emotional, analytical
    response_speed = Column(String(50))  # immediate, delayed, irregular
    sentiment_baseline = Column(String(50))  # positive, neutral, negative, mixed
    complaint_likelihood = Column(Float)  # 0-1
    
    # Visit context
    visit_history = Column(JSON)
    order_preferences = Column(JSON)
    special_requirements = Column(JSON)
    
    # Usage tracking
    times_used = Column(Integer, default=0)
    last_used = Column(DateTime)

class PerformanceMetric(BaseModel):
    """Performance metrics for agent monitoring"""
    __tablename__ = "performance_metrics"
    
    metric_name = Column(String(100), nullable=False)
    metric_category = Column(String(50))  # response_time, accuracy, sentiment, etc.
    
    # Metric data
    value = Column(Float, nullable=False)
    target_value = Column(Float)
    threshold_min = Column(Float)
    threshold_max = Column(Float)
    
    # Context
    agent_persona_id = Column(String(100))
    test_session_id = Column(Integer, ForeignKey("test_sessions.id"))
    measurement_time = Column(DateTime, default=datetime.utcnow)
    context_data = Column(JSON)  # Additional context for the metric

class IntegrationTestResult(BaseModel):
    """Integration test results"""
    __tablename__ = "integration_test_results"
    
    test_name = Column(String(200), nullable=False)
    test_type = Column(String(50))  # whatsapp, openrouter, database
    
    # Test execution
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    status = Column(String(50))  # passed, failed, error
    
    # Results
    test_output = Column(JSON)
    error_details = Column(JSON)
    performance_data = Column(JSON)
    
    # Configuration
    test_config = Column(JSON)
    environment = Column(String(50))  # test, staging, sandbox

class TestAlert(BaseModel):
    """Alerts generated during testing"""
    __tablename__ = "test_alerts"
    
    alert_type = Column(String(50))  # performance_degradation, cultural_insensitivity, etc.
    severity = Column(String(20))  # low, medium, high, critical
    
    # Alert details
    title = Column(String(200))
    message = Column(Text)
    alert_data = Column(JSON)
    
    # Context
    test_session_id = Column(Integer, ForeignKey("test_sessions.id"))
    agent_persona_id = Column(String(100))
    
    # Status
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(100))
    acknowledged_at = Column(DateTime)
    resolution_notes = Column(Text)