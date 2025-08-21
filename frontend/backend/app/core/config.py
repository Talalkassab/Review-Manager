"""
Core configuration settings for the Restaurant AI Customer Feedback Agent.
"""
import os
from typing import Optional
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # API Keys and External Services
    OPENROUTER_API_KEY: Optional[str] = None
    WHATSAPP_ACCESS_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    WHATSAPP_BUSINESS_ACCOUNT_ID: Optional[str] = None
    
    # Database Configuration
    DATABASE_URL: str = "sqlite:///./restaurant_ai.db"
    
    # Redis Configuration (for caching and job queues)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Application Settings
    APP_NAME: str = "Restaurant AI Customer Feedback Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Agent Configuration
    DEFAULT_LLM_MODEL: str = "anthropic/claude-3-haiku"
    BACKUP_LLM_MODEL: str = "openai/gpt-4o-mini"
    MAX_TOKENS: int = 4000
    TEMPERATURE: float = 0.7
    
    # Restaurant Configuration
    RESTAURANT_NAME: str = "Default Restaurant"
    RESTAURANT_PHONE: Optional[str] = None
    RESTAURANT_EMAIL: Optional[str] = None
    RESTAURANT_ADDRESS: Optional[str] = None
    
    # Language Support
    DEFAULT_LANGUAGE: str = "ar"  # Arabic
    SUPPORTED_LANGUAGES: list = ["ar", "en"]
    
    # Campaign Settings
    MAX_DAILY_MESSAGES: int = 100
    MIN_MESSAGE_INTERVAL: int = 60  # minutes
    CAMPAIGN_RETRY_ATTEMPTS: int = 3
    
    # Sentiment Analysis
    NEGATIVE_SENTIMENT_THRESHOLD: float = -0.3
    POSITIVE_SENTIMENT_THRESHOLD: float = 0.3
    
    # Performance Thresholds
    MIN_RESPONSE_RATE: float = 0.15  # 15%
    TARGET_SATISFACTION_SCORE: float = 0.8  # 80%
    
    # Escalation Settings
    ESCALATION_KEYWORDS: list = ["مدير", "شكوى", "منظف", "manager", "complaint", "refund"]
    ESCALATION_PHONE: Optional[str] = None
    ESCALATION_EMAIL: Optional[str] = None
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/restaurant_ai.log"
    
    @validator('OPENROUTER_API_KEY')
    def validate_openrouter_key(cls, v):
        if not v:
            raise ValueError("OPENROUTER_API_KEY is required")
        return v
    
    @validator('SUPPORTED_LANGUAGES')
    def validate_languages(cls, v):
        if not isinstance(v, list) or len(v) == 0:
            return ["ar", "en"]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()