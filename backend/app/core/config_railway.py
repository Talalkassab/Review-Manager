"""
Railway-optimized configuration settings.
Enhanced for Railway deployment with Vercel frontend integration.
"""
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import validator, Field
import secrets
import os


class RailwayDatabaseSettings(BaseSettings):
    """Railway PostgreSQL database configuration."""
    
    # Railway provides DATABASE_URL automatically
    DATABASE_URL: str = Field(
        default="postgresql://postgres:password@localhost:5432/whatsapp_agent",
        description="Railway PostgreSQL connection URL"
    )
    
    # Alternative individual connection parameters (Railway style)
    PGHOST: Optional[str] = None
    PGPORT: Optional[int] = 5432  
    PGUSER: Optional[str] = None
    PGPASSWORD: Optional[str] = None
    PGDATABASE: Optional[str] = None
    
    # Connection pool settings optimized for Railway
    DB_POOL_SIZE: int = 10  # Railway has connection limits
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600  # Recycle connections every hour
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v):
        """Assemble DATABASE_URL from individual components if not provided."""
        if v and v != "postgresql://postgres:password@localhost:5432/whatsapp_agent":
            return v
        
        # Try to build from Railway environment variables
        host = os.getenv("PGHOST")
        port = os.getenv("PGPORT", "5432")
        user = os.getenv("PGUSER")
        password = os.getenv("PGPASSWORD")  
        database = os.getenv("PGDATABASE")
        
        if all([host, user, password, database]):
            return f"postgresql://{user}:{password}@{host}:{port}/{database}"
        
        return v
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class RailwaySecuritySettings(BaseSettings):
    """Enhanced security settings for Railway deployment."""
    
    SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="JWT secret key"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 * 24 * 8  # 8 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 30 * 24 * 30  # 30 days
    
    # Password requirements
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = False  # Relaxed for user experience
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class RailwayCORSSettings(BaseSettings):
    """CORS configuration optimized for Railway-Vercel integration."""
    
    # Allowed origins with Railway-Vercel specific handling
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,https://localhost:3000",
        description="Comma-separated list of allowed CORS origins"
    )
    
    # Additional CORS settings
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_MAX_AGE: int = 86400  # 24 hours
    
    @validator("ALLOWED_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            origins = [origin.strip() for origin in v.split(",") if origin.strip()]
            
            # Add automatic Vercel preview URLs if VERCEL_URL is set
            vercel_url = os.getenv("VERCEL_URL")
            if vercel_url and f"https://{vercel_url}" not in origins:
                origins.append(f"https://{vercel_url}")
            
            return origins
        
        return v if isinstance(v, list) else [v]
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class RailwayApplicationSettings(BaseSettings):
    """Railway-specific application settings."""
    
    # App metadata
    APP_NAME: str = "WhatsApp Customer Agent"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Environment detection
    ENVIRONMENT: str = Field(
        default="production",
        description="Application environment"
    )
    DEBUG: bool = Field(
        default=False,
        description="Debug mode"
    )
    
    # Server settings (Railway optimized)
    HOST: str = "0.0.0.0"
    PORT: int = Field(
        default=8000,
        description="Application port (Railway sets this automatically)"
    )
    WORKERS: int = Field(
        default=1,
        description="Number of worker processes (Railway manages scaling)"
    )
    
    # Railway-specific settings
    RAILWAY_ENVIRONMENT: Optional[str] = None
    RAILWAY_SERVICE_NAME: Optional[str] = None
    RAILWAY_PROJECT_ID: Optional[str] = None
    
    # File upload settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_EXTENSIONS: List[str] = [
        ".jpg", ".jpeg", ".png", ".gif", ".pdf", 
        ".doc", ".docx", ".csv", ".xlsx", ".json"
    ]
    
    # Performance settings
    REQUEST_TIMEOUT: int = 30
    KEEPALIVE_TIMEOUT: int = 5
    
    @validator("PORT", pre=True)
    def get_railway_port(cls, v):
        """Get port from Railway environment or use default."""
        return int(os.getenv("PORT", v))
    
    @validator("ENVIRONMENT", pre=True) 
    def detect_railway_environment(cls, v):
        """Detect Railway environment automatically."""
        # Railway sets RAILWAY_ENVIRONMENT
        railway_env = os.getenv("RAILWAY_ENVIRONMENT")
        if railway_env:
            return railway_env
        
        # Fallback to checking for Railway-specific variables
        if os.getenv("RAILWAY_PROJECT_ID"):
            return "production"
        
        return v
    
    @validator("DEBUG", pre=True)
    def set_debug_from_environment(cls, v):
        """Set debug mode based on environment."""
        env = os.getenv("ENVIRONMENT", "production")
        return env == "development"
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class RailwayTwilioSettings(BaseSettings):
    """Twilio configuration for Railway deployment."""
    
    TWILIO_ACCOUNT_SID: Optional[str] = Field(None, description="Twilio Account SID")
    TWILIO_AUTH_TOKEN: Optional[str] = Field(None, description="Twilio Auth Token")
    TWILIO_WHATSAPP_NUMBER: str = Field(
        default="whatsapp:+14155238886", 
        description="Twilio WhatsApp number"
    )
    TWILIO_WEBHOOK_URL: Optional[str] = Field(None, description="Webhook URL for Twilio")
    
    @validator("TWILIO_WEBHOOK_URL", pre=True)
    def build_webhook_url(cls, v):
        """Build webhook URL from Railway environment."""
        if v:
            return v
            
        # Try to build from Railway URL
        railway_url = os.getenv("RAILWAY_PUBLIC_DOMAIN")
        if railway_url:
            return f"https://{railway_url}/api/v1/whatsapp/webhook"
        
        return v
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class RailwayOpenRouterSettings(BaseSettings):
    """OpenRouter AI configuration for Railway."""
    
    OPENROUTER_API_KEY: Optional[str] = Field(None, description="OpenRouter API key")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = Field(
        default="openai/gpt-3.5-turbo",
        description="Default model for OpenRouter"
    )
    
    # Cost management
    MONTHLY_BUDGET_LIMIT_USD: float = 100.0
    MAX_TOKENS_PER_REQUEST: int = 4000
    MAX_REQUESTS_PER_MINUTE: int = 30  # Conservative for Railway
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class RailwayLoggingSettings(BaseSettings):
    """Logging configuration optimized for Railway."""
    
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level"
    )
    LOG_FORMAT: str = "json"  # Railway works well with structured logs
    
    # Railway logging settings
    ENABLE_REQUEST_LOGGING: bool = True
    ENABLE_SQL_LOGGING: bool = False  # Disable in production for performance
    ENABLE_PERFORMANCE_LOGGING: bool = True
    ENABLE_ERROR_TRACKING: bool = True
    
    # Sentry integration (optional)
    SENTRY_DSN: Optional[str] = Field(None, description="Sentry DSN for error tracking")
    
    @validator("LOG_LEVEL", pre=True)
    def set_log_level_from_env(cls, v):
        """Set log level based on environment."""
        env = os.getenv("ENVIRONMENT", "production")
        if env == "development":
            return "DEBUG"
        elif env == "production":
            return "INFO"
        return v
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class RailwayRedisSettings(BaseSettings):
    """Redis configuration for Railway."""
    
    REDIS_URL: Optional[str] = Field(
        None, 
        description="Redis URL (Railway provides this for Redis service)"
    )
    REDIS_CACHE_TTL: int = 3600  # 1 hour
    REDIS_SESSION_TTL: int = 86400  # 24 hours
    
    # Fallback to in-memory cache if Redis not available
    USE_REDIS: bool = Field(
        default=True,
        description="Whether to use Redis (falls back to memory cache)"
    )
    
    @validator("USE_REDIS", pre=True)
    def check_redis_availability(cls, v):
        """Check if Redis is available in Railway environment."""
        redis_url = os.getenv("REDIS_URL")
        return bool(redis_url) if v else False
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class RailwaySettings(BaseSettings):
    """Combined Railway-optimized settings."""
    
    # Sub-settings
    database: RailwayDatabaseSettings = RailwayDatabaseSettings()
    security: RailwaySecuritySettings = RailwaySecuritySettings() 
    cors: RailwayCORSSettings = RailwayCORSSettings()
    app: RailwayApplicationSettings = RailwayApplicationSettings()
    twilio: RailwayTwilioSettings = RailwayTwilioSettings()
    openrouter: RailwayOpenRouterSettings = RailwayOpenRouterSettings()
    logging: RailwayLoggingSettings = RailwayLoggingSettings()
    redis: RailwayRedisSettings = RailwayRedisSettings()
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app.ENVIRONMENT == "production"
    
    @property
    def is_railway_deployment(self) -> bool:
        """Check if running on Railway."""
        return bool(os.getenv("RAILWAY_PROJECT_ID"))
    
    @property
    def cors_origins(self) -> List[str]:
        """Get processed CORS origins."""
        return self.cors.ALLOWED_ORIGINS
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# Global Railway-optimized settings instance
railway_settings = RailwaySettings()

# Backward compatibility
settings = railway_settings