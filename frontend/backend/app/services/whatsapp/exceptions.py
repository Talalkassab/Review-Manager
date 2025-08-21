"""
WhatsApp service exception classes.

This module defines custom exceptions for WhatsApp Business API integration,
providing detailed error information and proper error handling for different
failure scenarios.
"""

from typing import Optional, Dict, Any


class WhatsAppError(Exception):
    """Base exception for all WhatsApp-related errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class WhatsAppAPIError(WhatsAppError):
    """Exception raised for WhatsApp API errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        http_status: Optional[int] = None,
        api_response: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code)
        self.http_status = http_status
        self.api_response = api_response or {}


class RateLimitExceededError(WhatsAppError):
    """Exception raised when rate limits are exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        limit_type: str = "general"
    ):
        super().__init__(message)
        self.retry_after = retry_after
        self.limit_type = limit_type


class InvalidPhoneNumberError(WhatsAppError):
    """Exception raised for invalid phone number formats."""
    
    def __init__(self, message: str, phone_number: Optional[str] = None):
        super().__init__(message)
        self.phone_number = phone_number


class TemplateNotFoundError(WhatsAppError):
    """Exception raised when a message template is not found or not approved."""
    
    def __init__(self, message: str, template_name: Optional[str] = None, language: Optional[str] = None):
        super().__init__(message)
        self.template_name = template_name
        self.language = language


class MediaUploadError(WhatsAppError):
    """Exception raised for media upload failures."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, media_type: Optional[str] = None):
        super().__init__(message)
        self.file_path = file_path
        self.media_type = media_type


class MediaDownloadError(WhatsAppError):
    """Exception raised for media download failures."""
    
    def __init__(self, message: str, media_id: Optional[str] = None, url: Optional[str] = None):
        super().__init__(message)
        self.media_id = media_id
        self.url = url


class MediaValidationError(WhatsAppError):
    """Exception raised for media validation failures."""
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        validation_type: str = "general"
    ):
        super().__init__(message)
        self.file_path = file_path
        self.validation_type = validation_type


class WebhookValidationError(WhatsAppError):
    """Exception raised for webhook validation failures."""
    
    def __init__(self, message: str, webhook_data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.webhook_data = webhook_data


class MessageDeliveryError(WhatsAppError):
    """Exception raised for message delivery failures."""
    
    def __init__(
        self,
        message: str,
        message_id: Optional[str] = None,
        recipient: Optional[str] = None,
        delivery_status: Optional[str] = None
    ):
        super().__init__(message)
        self.message_id = message_id
        self.recipient = recipient
        self.delivery_status = delivery_status


class BulkMessagingError(WhatsAppError):
    """Exception raised for bulk messaging failures."""
    
    def __init__(
        self,
        message: str,
        failed_count: int = 0,
        successful_count: int = 0,
        failures: Optional[List[Dict[str, Any]]] = None
    ):
        super().__init__(message)
        self.failed_count = failed_count
        self.successful_count = successful_count
        self.failures = failures or []


class TemplateValidationError(WhatsAppError):
    """Exception raised for template validation failures."""
    
    def __init__(
        self,
        message: str,
        template_name: Optional[str] = None,
        validation_errors: Optional[List[str]] = None
    ):
        super().__init__(message)
        self.template_name = template_name
        self.validation_errors = validation_errors or []


class QueueError(WhatsAppError):
    """Exception raised for message queue operations."""
    
    def __init__(self, message: str, queue_name: Optional[str] = None, operation: Optional[str] = None):
        super().__init__(message)
        self.queue_name = queue_name
        self.operation = operation


class ConfigurationError(WhatsAppError):
    """Exception raised for configuration-related errors."""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(message)
        self.config_key = config_key


class AuthenticationError(WhatsAppError):
    """Exception raised for authentication failures."""
    
    def __init__(self, message: str = "Authentication failed", token_type: str = "access_token"):
        super().__init__(message)
        self.token_type = token_type


class InteractiveMessageError(WhatsAppError):
    """Exception raised for interactive message handling errors."""
    
    def __init__(
        self,
        message: str,
        interaction_type: Optional[str] = None,
        component_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.interaction_type = interaction_type
        self.component_data = component_data


class CampaignError(WhatsAppError):
    """Exception raised for campaign management errors."""
    
    def __init__(
        self,
        message: str,
        campaign_id: Optional[str] = None,
        campaign_status: Optional[str] = None
    ):
        super().__init__(message)
        self.campaign_id = campaign_id
        self.campaign_status = campaign_status