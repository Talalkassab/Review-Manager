"""
Utility functions for WhatsApp service operations.

This module provides common utility functions for phone number validation,
formatting, text processing, and other helper operations used throughout
the WhatsApp integration system.
"""

import re
import hashlib
import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta


def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number format using international standards.
    
    Args:
        phone: Phone number string to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Parse phone number
        parsed = phonenumbers.parse(phone, None)
        
        # Check if the number is valid
        return phonenumbers.is_valid_number(parsed)
        
    except NumberParseException:
        return False


def format_phone_number(phone: str, country_code: str = "SA") -> str:
    """
    Format phone number to international format for WhatsApp.
    
    Args:
        phone: Phone number string
        country_code: Default country code if not provided
        
    Returns:
        Formatted phone number in international format (without +)
    """
    try:
        # Clean input
        cleaned = re.sub(r'[^\d+]', '', phone)
        
        # Handle different input formats
        if cleaned.startswith('+'):
            # Already has country code
            parsed = phonenumbers.parse(cleaned, None)
        elif cleaned.startswith('00'):
            # International format with 00 prefix
            parsed = phonenumbers.parse(f'+{cleaned[2:]}', None)
        elif cleaned.startswith('966'):
            # Saudi number with country code
            parsed = phonenumbers.parse(f'+{cleaned}', None)
        elif cleaned.startswith('0') and len(cleaned) == 10:
            # Local Saudi number
            parsed = phonenumbers.parse(cleaned, country_code)
        else:
            # Assume local number
            parsed = phonenumbers.parse(cleaned, country_code)
        
        # Format to international without +
        formatted = phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
        return formatted[1:]  # Remove the + prefix
        
    except NumberParseException:
        # Return original if parsing fails
        return phone


def extract_country_code(phone: str) -> Optional[str]:
    """
    Extract country code from phone number.
    
    Args:
        phone: Phone number string
        
    Returns:
        Country code or None if not found
    """
    try:
        parsed = phonenumbers.parse(phone, None)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.region_code_for_number(parsed)
    except NumberParseException:
        pass
    
    return None


def is_saudi_number(phone: str) -> bool:
    """
    Check if phone number is a Saudi number.
    
    Args:
        phone: Phone number string
        
    Returns:
        True if Saudi number, False otherwise
    """
    formatted = format_phone_number(phone)
    return formatted.startswith('966')


def mask_phone_number(phone: str, show_last: int = 4) -> str:
    """
    Mask phone number for privacy.
    
    Args:
        phone: Phone number to mask
        show_last: Number of digits to show at the end
        
    Returns:
        Masked phone number
    """
    if len(phone) <= show_last:
        return phone
    
    masked_length = len(phone) - show_last
    return '*' * masked_length + phone[-show_last:]


def generate_conversation_id(customer_id: int, timestamp: Optional[datetime] = None) -> str:
    """
    Generate unique conversation ID for message threading.
    
    Args:
        customer_id: Customer database ID
        timestamp: Optional timestamp (uses current time if not provided)
        
    Returns:
        Unique conversation ID
    """
    if timestamp is None:
        timestamp = datetime.utcnow()
    
    # Create hash from customer ID and date
    date_str = timestamp.strftime('%Y-%m-%d')
    hash_input = f"{customer_id}_{date_str}"
    
    return hashlib.md5(hash_input.encode()).hexdigest()[:16]


def extract_mentions(text: str) -> List[str]:
    """
    Extract @mentions from message text.
    
    Args:
        text: Message text
        
    Returns:
        List of mentioned usernames
    """
    mention_pattern = r'@(\w+)'
    return re.findall(mention_pattern, text)


def extract_hashtags(text: str) -> List[str]:
    """
    Extract #hashtags from message text.
    
    Args:
        text: Message text
        
    Returns:
        List of hashtags
    """
    hashtag_pattern = r'#(\w+)'
    return re.findall(hashtag_pattern, text)


def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from message text.
    
    Args:
        text: Message text
        
    Returns:
        List of URLs found in text
    """
    url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'
    return re.findall(url_pattern, text)


def clean_whatsapp_formatting(text: str) -> str:
    """
    Clean WhatsApp formatting characters from text.
    
    Args:
        text: Text with WhatsApp formatting
        
    Returns:
        Clean text without formatting
    """
    # Remove WhatsApp formatting: *bold*, _italic_, ~strikethrough~, ```monospace```
    patterns = [
        r'\*([^*]+)\*',  # Bold
        r'_([^_]+)_',    # Italic
        r'~([^~]+)~',    # Strikethrough
        r'```([^`]+)```' # Monospace
    ]
    
    cleaned = text
    for pattern in patterns:
        cleaned = re.sub(pattern, r'\1', cleaned)
    
    return cleaned


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """
    Truncate text to specified length with optional suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length allowed
        suffix: Suffix to add if text is truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def estimate_message_cost(text: str, message_type: str = "text") -> float:
    """
    Estimate cost of sending a WhatsApp message.
    
    Args:
        text: Message text
        message_type: Type of message (text, template, media)
        
    Returns:
        Estimated cost in USD
    """
    # WhatsApp Business API pricing (approximate)
    pricing = {
        "text": 0.005,      # $0.005 per message
        "template": 0.015,  # $0.015 per template message
        "media": 0.005,     # $0.005 per media message
        "interactive": 0.005 # $0.005 per interactive message
    }
    
    base_cost = pricing.get(message_type, 0.005)
    
    # Additional cost for long messages (if over 1000 characters)
    if len(text) > 1000:
        additional_segments = (len(text) - 1000) // 1000 + 1
        base_cost += additional_segments * 0.005
    
    return base_cost


def parse_webhook_timestamp(timestamp: str) -> datetime:
    """
    Parse WhatsApp webhook timestamp.
    
    Args:
        timestamp: Timestamp string from webhook
        
    Returns:
        Parsed datetime object
    """
    try:
        # WhatsApp sends Unix timestamps
        return datetime.fromtimestamp(int(timestamp))
    except (ValueError, TypeError):
        return datetime.utcnow()


def format_duration(seconds: int) -> str:
    """
    Format duration in seconds to human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"


def generate_message_signature(
    phone_number: str,
    content: str,
    timestamp: str,
    secret_key: str
) -> str:
    """
    Generate message signature for verification.
    
    Args:
        phone_number: Recipient phone number
        content: Message content
        timestamp: Message timestamp
        secret_key: Secret key for signing
        
    Returns:
        Generated signature
    """
    message = f"{phone_number}|{content}|{timestamp}"
    signature = hashlib.hmac.new(
        secret_key.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return signature


def validate_message_signature(
    phone_number: str,
    content: str,
    timestamp: str,
    signature: str,
    secret_key: str,
    tolerance_seconds: int = 300
) -> bool:
    """
    Validate message signature.
    
    Args:
        phone_number: Recipient phone number
        content: Message content
        timestamp: Message timestamp
        signature: Provided signature
        secret_key: Secret key for verification
        tolerance_seconds: Time tolerance for timestamp validation
        
    Returns:
        True if signature is valid, False otherwise
    """
    # Check timestamp tolerance
    try:
        message_time = datetime.fromisoformat(timestamp)
        current_time = datetime.utcnow()
        time_diff = abs((current_time - message_time).total_seconds())
        
        if time_diff > tolerance_seconds:
            return False
    except ValueError:
        return False
    
    # Verify signature
    expected_signature = generate_message_signature(
        phone_number, content, timestamp, secret_key
    )
    
    return signature == expected_signature


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace unsafe characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Limit length
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        max_name_length = 255 - len(ext)
        sanitized = name[:max_name_length] + ext
    
    return sanitized


def get_media_type_category(mime_type: str) -> str:
    """
    Get media category from MIME type.
    
    Args:
        mime_type: MIME type string
        
    Returns:
        Media category (image, document, audio, video, other)
    """
    if mime_type.startswith('image/'):
        return 'image'
    elif mime_type.startswith('video/'):
        return 'video'
    elif mime_type.startswith('audio/'):
        return 'audio'
    elif mime_type in ['application/pdf', 'text/plain', 'application/msword',
                       'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                       'application/vnd.ms-excel',
                       'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
        return 'document'
    else:
        return 'other'


def create_delivery_receipt_url(message_id: str, base_url: str) -> str:
    """
    Create delivery receipt tracking URL.
    
    Args:
        message_id: WhatsApp message ID
        base_url: Base URL for tracking
        
    Returns:
        Tracking URL
    """
    return f"{base_url}/delivery/{message_id}"


def parse_interactive_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse interactive message response from customer.
    
    Args:
        response_data: Interactive response data from webhook
        
    Returns:
        Parsed response information
    """
    interactive = response_data.get('interactive', {})
    response_type = interactive.get('type')
    
    result = {
        'type': response_type,
        'timestamp': response_data.get('timestamp'),
        'from': response_data.get('from')
    }
    
    if response_type == 'button_reply':
        button_reply = interactive.get('button_reply', {})
        result.update({
            'button_id': button_reply.get('id'),
            'button_title': button_reply.get('title')
        })
    elif response_type == 'list_reply':
        list_reply = interactive.get('list_reply', {})
        result.update({
            'list_id': list_reply.get('id'),
            'list_title': list_reply.get('title'),
            'list_description': list_reply.get('description')
        })
    
    return result