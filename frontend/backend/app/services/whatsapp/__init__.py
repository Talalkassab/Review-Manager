"""
WhatsApp Business Cloud API integration package.

This package provides comprehensive WhatsApp Business API integration with features for:
- Message sending (text, template, media, interactive)
- Webhook processing and event handling
- Template management and synchronization
- Media handling with optimization
- Bulk messaging and campaigns
- Rate limiting and queue management
- Delivery tracking and analytics
- Restaurant-specific message templates
- Multi-language support with RTL formatting
"""

from .service import WhatsAppService, create_whatsapp_service
from .client import WhatsAppClient
from .formatter import MessageFormatter
from .media import WhatsAppMediaHandler
from .webhook import WebhookHandler
from .template_manager import TemplateManager
from .async_messaging import AsyncMessagingService
from .bulk_messaging import BulkMessagingService
from .rate_limiter import RateLimiter
from .exceptions import (
    WhatsAppError,
    WhatsAppAPIError,
    RateLimitExceededError,
    InvalidPhoneNumberError,
    TemplateNotFoundError,
    MediaUploadError,
    MediaDownloadError,
    MediaValidationError,
    WebhookValidationError,
    MessageDeliveryError,
    BulkMessagingError
)
from .utils import (
    validate_phone_number,
    format_phone_number,
    extract_country_code,
    is_saudi_number,
    mask_phone_number
)

__all__ = [
    # Main service
    'WhatsAppService',
    'create_whatsapp_service',
    
    # Core components
    'WhatsAppClient',
    'MessageFormatter',
    'WhatsAppMediaHandler',
    'WebhookHandler',
    'TemplateManager',
    
    # Advanced services
    'AsyncMessagingService',
    'BulkMessagingService',
    'RateLimiter',
    
    # Exceptions
    'WhatsAppError',
    'WhatsAppAPIError',
    'RateLimitExceededError',
    'InvalidPhoneNumberError',
    'TemplateNotFoundError',
    'MediaUploadError',
    'MediaDownloadError',
    'MediaValidationError',
    'WebhookValidationError',
    'MessageDeliveryError',
    'BulkMessagingError',
    
    # Utilities
    'validate_phone_number',
    'format_phone_number',
    'extract_country_code',
    'is_saudi_number',
    'mask_phone_number'
]

__version__ = "1.0.0"