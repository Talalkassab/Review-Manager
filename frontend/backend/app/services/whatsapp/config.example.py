"""
Example WhatsApp service configuration.

Copy this file to config.py and update with your actual values.
"""

# WhatsApp Business API Configuration
WHATSAPP_ACCESS_TOKEN = "your_whatsapp_access_token_here"
WHATSAPP_PHONE_NUMBER_ID = "your_phone_number_id_here"
WHATSAPP_BUSINESS_ACCOUNT_ID = "your_business_account_id_here"
WHATSAPP_WEBHOOK_SECRET = "your_webhook_secret_here"
WHATSAPP_VERIFY_TOKEN = "your_webhook_verify_token_here"

# Media Storage Configuration
MEDIA_STORAGE_PATH = "media"
MEDIA_BASE_URL = "https://your-domain.com/media"

# Rate Limiting Configuration
RATE_LIMIT_CONFIG = {
    "max_requests": 80,      # Messages per minute (WhatsApp limit)
    "time_window": 60,       # Time window in seconds
    "burst_limit": 1000      # Daily message limit
}

# Async Messaging Configuration
ASYNC_MESSAGING_CONFIG = {
    "worker_count": 3,       # Number of background workers
    "queue_size_limit": 10000,
    "retry_config": {
        "max_retries": 3,
        "base_delay": 30,    # seconds
        "max_delay": 3600    # seconds
    }
}

# Template Configuration
TEMPLATE_CONFIG = {
    "auto_create_restaurant_templates": True,
    "default_language": "ar",
    "supported_languages": ["ar", "en"],
    "sync_interval_hours": 24  # Sync with WhatsApp every 24 hours
}

# Restaurant Information
RESTAURANT_CONFIG = {
    "name": "Your Restaurant Name",
    "phone": "+966501234567",
    "email": "contact@restaurant.com",
    "address": "Restaurant Address",
    "website": "https://restaurant.com",
    "logo_url": "https://restaurant.com/logo.png"
}

# Campaign Configuration
CAMPAIGN_CONFIG = {
    "default_rate_limits": {
        "messages_per_minute": 60,
        "messages_per_hour": 1000,
        "messages_per_day": 10000
    },
    "segment_cache_ttl": 3600,    # seconds
    "max_recipients_per_campaign": 50000
}

# Database Configuration
DATABASE_CONFIG = {
    "connection_pool_size": 10,
    "connection_pool_recycle": 3600,
    "query_timeout": 30
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file_path": "logs/whatsapp_service.log",
    "max_file_size": "10MB",
    "backup_count": 5
}

# Monitoring and Health Checks
MONITORING_CONFIG = {
    "health_check_interval": 300,  # seconds
    "metrics_collection_enabled": True,
    "performance_monitoring": True,
    "error_reporting_webhook": None  # Optional webhook for error notifications
}

# Security Configuration
SECURITY_CONFIG = {
    "webhook_signature_validation": True,
    "rate_limit_by_ip": True,
    "max_requests_per_ip": 1000,    # per hour
    "blocked_phone_patterns": [],   # Phone number patterns to block
    "allowed_media_types": [
        "image/jpeg", "image/png", "image/webp",
        "application/pdf", "text/plain",
        "audio/mpeg", "audio/ogg",
        "video/mp4", "video/mpeg"
    ]
}

# Feature Flags
FEATURE_FLAGS = {
    "async_messaging_enabled": True,
    "bulk_messaging_enabled": True,
    "media_optimization_enabled": True,
    "template_auto_sync_enabled": True,
    "webhook_processing_enabled": True,
    "campaign_analytics_enabled": True,
    "interactive_messages_enabled": True
}

# Development/Testing Configuration
DEVELOPMENT_CONFIG = {
    "test_mode": False,
    "test_phone_numbers": ["+966501234567"],  # Numbers for testing
    "webhook_ngrok_url": None,  # For local development
    "mock_whatsapp_api": False,  # Use mock API for testing
    "debug_logging": False
}