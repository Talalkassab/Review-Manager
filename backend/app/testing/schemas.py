"""
Testing System Pydantic Schemas
===============================

Data schemas for the agent testing system API endpoints.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, validator
from enum import Enum

# Enums
class TestSessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    FAILED = "failed"

class TestScenarioType(str, Enum):
    CONVERSATION = "conversation"
    AB_TEST = "ab_test"
    SCENARIO = "scenario"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"

class CustomerProfileType(str, Enum):
    HAPPY_CUSTOMER = "happy_customer"
    DISSATISFIED_CUSTOMER = "dissatisfied_customer"
    FIRST_TIME_VISITOR = "first_time_visitor"
    REPEAT_CUSTOMER = "repeat_customer"
    VIP_CUSTOMER = "vip_customer"
    COMPLAINT_CUSTOMER = "complaint_customer"

class CommunicationStyle(str, Enum):
    DIRECT = "direct"
    POLITE = "polite"
    EMOTIONAL = "emotional"
    ANALYTICAL = "analytical"

class ResponseSpeed(str, Enum):
    IMMEDIATE = "immediate"
    DELAYED = "delayed"
    IRREGULAR = "irregular"

# Base Schemas
class TestSessionBase(BaseModel):
    session_name: str
    session_type: TestScenarioType
    agent_persona_id: Optional[str] = None
    customer_profile_config: Optional[Dict[str, Any]] = None
    test_parameters: Optional[Dict[str, Any]] = None

class TestSessionCreate(TestSessionBase):
    pass

class TestSessionUpdate(BaseModel):
    session_name: Optional[str] = None
    status: Optional[TestSessionStatus] = None
    test_parameters: Optional[Dict[str, Any]] = None

class TestSessionResponse(TestSessionBase):
    id: int
    status: TestSessionStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    total_interactions: int
    success_rate: float
    test_results: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

# Customer Profile Schemas
class CustomerDemographics(BaseModel):
    age_range: str = Field(..., example="25-35")
    gender: str = Field(..., example="male")
    language_preference: str = Field(..., example="arabic")
    cultural_background: str = Field(..., example="gulf")
    location: Optional[str] = Field(None, example="Riyadh")

class CustomerBehavioralTraits(BaseModel):
    communication_style: CommunicationStyle
    response_speed: ResponseSpeed
    sentiment_baseline: str = Field(..., example="positive")
    complaint_likelihood: float = Field(..., ge=0, le=1)

class VisitContext(BaseModel):
    visit_type: str = Field(..., example="repeat")
    order_value: float = Field(..., ge=0)
    dining_experience: str = Field(..., example="excellent")
    specific_issues: Optional[List[str]] = None

class CustomerProfileSimulatorConfig(BaseModel):
    demographics: CustomerDemographics
    behavioral_traits: CustomerBehavioralTraits
    visit_context: VisitContext

class SyntheticCustomerCreate(BaseModel):
    profile_name: str
    profile_type: CustomerProfileType
    demographics: CustomerDemographics
    behavioral_traits: CustomerBehavioralTraits
    visit_context: VisitContext

class SyntheticCustomerResponse(SyntheticCustomerCreate):
    id: int
    times_used: int
    last_used: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Conversation Testing Schemas
class TestMessage(BaseModel):
    message_id: str
    sender: str = Field(..., description="'customer' or 'agent'")
    content: str
    timestamp: datetime
    language: Optional[str] = None
    sentiment: Optional[str] = None
    response_time_seconds: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class ConversationAnalysis(BaseModel):
    sentiment_scores: Dict[str, float]
    response_times: List[float]
    persona_consistency_score: float = Field(..., ge=0, le=1)
    cultural_sensitivity_score: float = Field(..., ge=0, le=1)
    language_appropriateness_score: float = Field(..., ge=0, le=1)
    overall_score: float = Field(..., ge=0, le=1)

class TestConversationCreate(BaseModel):
    session_id: int
    conversation_name: str
    customer_profile_type: CustomerProfileType
    customer_demographics: CustomerDemographics
    customer_context: Dict[str, Any]

class TestConversationResponse(TestConversationCreate):
    id: int
    conversation_messages: List[TestMessage]
    conversation_start: datetime
    conversation_end: Optional[datetime] = None
    sentiment_analysis: Optional[Dict[str, Any]] = None
    analysis: Optional[ConversationAnalysis] = None
    
    class Config:
        from_attributes = True

# A/B Testing Schemas
class MessageVariant(BaseModel):
    variant_name: str
    weight: float = Field(..., ge=0, le=1, description="Percentage of audience")
    persona_override: Optional[Dict[str, Any]] = None
    message_content: Dict[str, str] = Field(..., description="Arabic and English versions")
    call_to_action: Optional[Dict[str, Any]] = None

class ABTestMetrics(BaseModel):
    metric_name: str
    metric_type: str = Field(..., example="response_rate")
    target_value: float
    minimum_sample_size: int = Field(..., ge=1)
    significance_threshold: float = Field(default=0.05, ge=0, le=1)

class ABTestCreate(BaseModel):
    session_id: int
    test_name: str
    test_description: Optional[str] = None
    variants: List[MessageVariant]
    target_metrics: List[ABTestMetrics]
    sample_size: int = Field(..., ge=1)
    confidence_threshold: float = Field(default=0.95, ge=0, le=1)
    duration_days: int = Field(default=7, ge=1)

class VariantResult(BaseModel):
    variant_name: str
    sample_size: int
    response_rate: float
    conversion_rate: float
    sentiment_score: float
    confidence_interval: Dict[str, float]

class StatisticalAnalysis(BaseModel):
    p_value: float
    confidence_level: float
    effect_size: float
    statistical_significance: bool
    recommendation: str

class ABTestResponse(ABTestCreate):
    id: int
    start_date: datetime
    end_date: Optional[datetime] = None
    is_active: bool
    variant_results: Optional[List[VariantResult]] = None
    statistical_analysis: Optional[StatisticalAnalysis] = None
    winner_variant: Optional[str] = None
    
    class Config:
        from_attributes = True

# Scenario Testing Schemas
class ConversationStep(BaseModel):
    step_number: int
    customer_message: Dict[str, Any]
    expected_agent_response_criteria: Dict[str, Any]

class SuccessCriteria(BaseModel):
    criteria_name: str
    criteria_type: str
    target_value: Union[float, str, bool]
    weight: float = Field(default=1.0, ge=0)

class TestScenarioCreate(BaseModel):
    scenario_name: str
    scenario_type: str
    difficulty_level: str = Field(..., pattern="^(easy|medium|hard)$")
    description: str
    customer_profile: CustomerProfileSimulatorConfig
    conversation_steps: List[ConversationStep]
    success_criteria: List[SuccessCriteria]
    expected_behaviors: List[Dict[str, Any]]
    tags: Optional[List[str]] = None

class TestScenarioResponse(TestScenarioCreate):
    id: int
    is_active: bool
    created_by: Optional[str] = None
    usage_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ScenarioTestResult(BaseModel):
    scenario_id: int
    session_id: int
    test_start: datetime
    test_end: datetime
    passed: bool
    score: float = Field(..., ge=0, le=1)
    criteria_results: List[Dict[str, Any]]
    failure_reasons: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None

# Performance Monitoring Schemas
class PerformanceMetricCreate(BaseModel):
    metric_name: str
    metric_category: str
    value: float
    target_value: Optional[float] = None
    threshold_min: Optional[float] = None
    threshold_max: Optional[float] = None
    agent_persona_id: Optional[str] = None
    test_session_id: Optional[int] = None
    context_data: Optional[Dict[str, Any]] = None

class PerformanceMetricResponse(PerformanceMetricCreate):
    id: int
    measurement_time: datetime
    is_within_threshold: bool
    
    class Config:
        from_attributes = True

class RealTimeMetrics(BaseModel):
    response_accuracy: float = Field(..., ge=0, le=1)
    cultural_sensitivity_score: float = Field(..., ge=0, le=1)
    persona_consistency_score: float = Field(..., ge=0, le=1)
    language_appropriateness: float = Field(..., ge=0, le=1)
    timing_optimization_score: float = Field(..., ge=0, le=1)
    timestamp: datetime

class PerformanceAlert(BaseModel):
    alert_type: str
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    title: str
    message: str
    alert_data: Optional[Dict[str, Any]] = None
    test_session_id: Optional[int] = None
    agent_persona_id: Optional[str] = None

# Integration Testing Schemas
class IntegrationTestConfig(BaseModel):
    test_name: str
    test_type: str = Field(..., pattern="^(whatsapp|openrouter|database)$")
    test_config: Dict[str, Any]
    environment: str = Field(default="test", pattern="^(test|staging|sandbox)$")

class IntegrationTestResult(BaseModel):
    test_name: str
    test_type: str
    start_time: datetime
    end_time: datetime
    status: str = Field(..., pattern="^(passed|failed|error)$")
    test_output: Optional[Dict[str, Any]] = None
    error_details: Optional[Dict[str, Any]] = None
    performance_data: Optional[Dict[str, Any]] = None

# Batch Operations
class BatchTestRequest(BaseModel):
    test_type: TestScenarioType
    scenarios: List[int]  # List of scenario IDs
    parallel_execution: bool = Field(default=True)
    max_parallel_tests: int = Field(default=5, ge=1, le=20)

class BatchTestResult(BaseModel):
    batch_id: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    execution_time_seconds: float
    individual_results: List[Dict[str, Any]]

# WebSocket Schemas
class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class TestProgressUpdate(BaseModel):
    test_session_id: int
    progress_percentage: float = Field(..., ge=0, le=100)
    current_step: str
    metrics_update: Optional[RealTimeMetrics] = None
    alerts: Optional[List[PerformanceAlert]] = None