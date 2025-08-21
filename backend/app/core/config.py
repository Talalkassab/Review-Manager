"""
Core application configuration settings.
Manages environment variables and application settings.
"""
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import validator
import secrets


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./restaurant_ai.db"
    DATABASE_TEST_URL: str = "sqlite+aiosqlite:///./test_restaurant_ai.db"
    
    # Connection pool settings
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_TIMEOUT: int = 30
    
    class Config:
        extra = "ignore"  # Ignore extra fields from environment
    

class SecuritySettings(BaseSettings):
    """Security and authentication settings."""
    
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 * 24 * 8  # 8 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 30 * 24 * 30  # 30 days
    
    # Password settings
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    
    class Config:
        extra = "ignore"
    

class WhatsAppSettings(BaseSettings):
    """WhatsApp Business API configuration."""
    
    WHATSAPP_ACCESS_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None  
    WHATSAPP_BUSINESS_ACCOUNT_ID: Optional[str] = None
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: Optional[str] = None
    WHATSAPP_WEBHOOK_URL: Optional[str] = None
    
    # Rate limiting
    WHATSAPP_MAX_MESSAGES_PER_HOUR: int = 1000
    WHATSAPP_MAX_MESSAGES_PER_DAY: int = 10000
    
    class Config:
        extra = "ignore"
    

class TwilioSettings(BaseSettings):
    """Twilio WhatsApp configuration."""
    
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_WHATSAPP_NUMBER: str = "whatsapp:+14155238886"  # Default sandbox number
    TWILIO_SANDBOX_CODE: Optional[str] = None
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class OpenRouterSettings(BaseSettings):
    """OpenRouter AI API configuration."""
    
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    
    # Model settings
    PRIMARY_MODEL_ARABIC: str = "anthropic/claude-3.5-haiku"
    FALLBACK_MODEL_ENGLISH: str = "openai/gpt-4o-mini"
    FALLBACK_MODEL_FREE: str = "meta-llama/llama-3.1-8b-instruct:free"
    
    # Rate limiting and costs
    MAX_TOKENS_PER_REQUEST: int = 4000
    MAX_REQUESTS_PER_MINUTE: int = 60
    MONTHLY_BUDGET_LIMIT_USD: float = 200.0
    
    class Config:
        extra = "ignore"
    

class RedisSettings(BaseSettings):
    """Redis cache and queue configuration."""
    
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600  # 1 hour
    REDIS_SESSION_TTL: int = 86400  # 24 hours
    
    class Config:
        extra = "ignore"
    

class LoggingSettings(BaseSettings):
    """Logging configuration settings."""
    
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or console
    LOG_FILE: Optional[str] = "logs/restaurant_ai.log"
    
    # Structured logging
    ENABLE_REQUEST_LOGGING: bool = True
    ENABLE_SQL_LOGGING: bool = False  # Set to True for development
    ENABLE_PERFORMANCE_LOGGING: bool = True
    
    class Config:
        extra = "ignore"
    

class ApplicationSettings(BaseSettings):
    """Main application settings."""
    
    # App Info
    APP_NAME: str = "Restaurant AI Assistant"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = False
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002", 
        "http://localhost:8000",
        "https://localhost:3000",
        "https://localhost:3001",
        "https://localhost:3002",
    ]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # File upload settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_EXTENSIONS: List[str] = [".csv", ".xlsx", ".json"]
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"
        

class Settings(BaseSettings):
    """Combined application settings."""
    
    # Sub-settings
    database: DatabaseSettings = DatabaseSettings()
    security: SecuritySettings = SecuritySettings()
    whatsapp: WhatsAppSettings = WhatsAppSettings()
    twilio: TwilioSettings = TwilioSettings()
    openrouter: OpenRouterSettings = OpenRouterSettings()
    redis: RedisSettings = RedisSettings()
    logging: LoggingSettings = LoggingSettings()
    app: ApplicationSettings = ApplicationSettings()
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app.ENVIRONMENT == "production"
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.app.ENVIRONMENT == "testing"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# Global settings instance
settings = Settings()