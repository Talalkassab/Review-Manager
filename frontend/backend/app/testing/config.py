"""
Testing Configuration
"""
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class TestEnvironment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class CulturalRegion(Enum):
    SAUDI_ARABIA = "saudi_arabia"
    UAE = "uae"
    QATAR = "qatar"
    KUWAIT = "kuwait"
    BAHRAIN = "bahrain"
    OMAN = "oman"
    EGYPT = "egypt"
    JORDAN = "jordan"
    LEBANON = "lebanon"


@dataclass
class TestConfig:
    """Base configuration for testing"""
    environment: TestEnvironment = TestEnvironment.DEVELOPMENT
    max_concurrent_tests: int = 10
    test_timeout_seconds: int = 300
    enable_logging: bool = True
    log_level: str = "INFO"
    
    # A/B Testing
    min_sample_size: int = 100
    confidence_level: float = 0.95
    statistical_power: float = 0.8
    
    # Performance thresholds
    max_response_time_ms: int = 5000
    min_cultural_sensitivity_score: float = 0.8
    min_persona_consistency_score: float = 0.85
    
    # Database settings
    test_db_isolation: bool = True
    cleanup_test_data: bool = True


@dataclass
class PersonaConfig:
    """Configuration for agent personas"""
    name: str
    description: str
    cultural_context: CulturalRegion
    language_preferences: List[str]
    personality_traits: Dict[str, Any]
    communication_style: Dict[str, Any]
    knowledge_domains: List[str]


# Default persona configurations
DEFAULT_PERSONAS = {
    "customer_service_saudi": PersonaConfig(
        name="Saudi Customer Service",
        description="Polite, respectful customer service agent for Saudi customers",
        cultural_context=CulturalRegion.SAUDI_ARABIA,
        language_preferences=["arabic", "english"],
        personality_traits={
            "politeness": 0.9,
            "patience": 0.8,
            "helpfulness": 0.9,
            "formality": 0.8
        },
        communication_style={
            "greeting_style": "formal",
            "use_honorifics": True,
            "response_length": "detailed",
            "emoji_usage": "minimal"
        },
        knowledge_domains=["customer_service", "product_information", "cultural_etiquette"]
    ),
    "technical_support_uae": PersonaConfig(
        name="UAE Technical Support",
        description="Technical support agent specialized for UAE customers",
        cultural_context=CulturalRegion.UAE,
        language_preferences=["arabic", "english"],
        personality_traits={
            "technical_expertise": 0.9,
            "problem_solving": 0.9,
            "patience": 0.8,
            "clarity": 0.9
        },
        communication_style={
            "greeting_style": "professional",
            "use_honorifics": True,
            "response_length": "concise",
            "emoji_usage": "none"
        },
        knowledge_domains=["technical_support", "troubleshooting", "product_features"]
    )
}


# Test scenario categories
TEST_SCENARIOS = {
    "customer_service": [
        "Product inquiry",
        "Order status check",
        "Return request",
        "Complaint handling",
        "General information"
    ],
    "technical_support": [
        "Installation help",
        "Troubleshooting",
        "Feature explanation",
        "Bug reporting",
        "Performance issues"
    ],
    "cultural_sensitivity": [
        "Religious considerations",
        "Cultural greetings",
        "Local customs awareness",
        "Language preferences",
        "Regional differences"
    ]
}


# Performance metrics configuration
PERFORMANCE_METRICS = {
    "response_time": {
        "excellent": {"min": 0, "max": 1000},  # milliseconds
        "good": {"min": 1000, "max": 3000},
        "acceptable": {"min": 3000, "max": 5000},
        "poor": {"min": 5000, "max": float('inf')}
    },
    "cultural_sensitivity": {
        "excellent": {"min": 0.9, "max": 1.0},
        "good": {"min": 0.8, "max": 0.9},
        "acceptable": {"min": 0.7, "max": 0.8},
        "poor": {"min": 0.0, "max": 0.7}
    },
    "persona_consistency": {
        "excellent": {"min": 0.9, "max": 1.0},
        "good": {"min": 0.8, "max": 0.9},
        "acceptable": {"min": 0.7, "max": 0.8},
        "poor": {"min": 0.0, "max": 0.7}
    }
}