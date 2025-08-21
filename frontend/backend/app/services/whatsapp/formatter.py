"""
Message formatting service with Arabic/English RTL support and restaurant-specific templates.

This module provides comprehensive message formatting capabilities for WhatsApp messages,
with special attention to Arabic language support, RTL text handling, and restaurant
industry use cases.
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from enum import Enum

from app.core.config import settings


class TextDirection(str, Enum):
    """Text direction enumeration."""
    LTR = "ltr"  # Left-to-right (English, numbers)
    RTL = "rtl"  # Right-to-left (Arabic, Hebrew)
    AUTO = "auto"  # Auto-detect based on content


class MessageFormatter:
    """
    Advanced message formatter with multi-language support and restaurant context.
    
    Features:
    - Arabic/English mixed text formatting
    - RTL/LTR text direction handling
    - Restaurant-specific message templates
    - Customer personalization
    - Emoji and Unicode support
    - Number and date formatting
    - URL and contact formatting
    """
    
    # Arabic Unicode range
    ARABIC_RANGE = r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]'
    
    # Restaurant-specific emoji mappings
    RESTAURANT_EMOJIS = {
        'food': '🍽️',
        'delivery': '🚚',
        'star': '⭐',
        'chef': '👨‍🍳',
        'thank_you': '🙏',
        'welcome': '👋',
        'location': '📍',
        'time': '⏰',
        'phone': '📞',
        'order': '📋',
        'payment': '💳',
        'discount': '🎉',
        'feedback': '💬',
        'rating': '⭐'
    }
    
    def __init__(self, default_language: str = "ar"):
        """Initialize formatter with default language."""
        self.default_language = default_language
        self.supported_languages = settings.SUPPORTED_LANGUAGES
    
    def format_message(
        self,
        template: str,
        variables: Dict[str, Any],
        language: str = None,
        add_direction_markers: bool = True,
        preserve_formatting: bool = True
    ) -> str:
        """
        Format a message template with variables and proper text direction.
        
        Args:
            template: Message template with placeholders
            variables: Dictionary of variables to substitute
            language: Target language code
            add_direction_markers: Whether to add Unicode direction markers
            preserve_formatting: Whether to preserve original formatting
            
        Returns:
            Formatted message string
        """
        language = language or self.default_language
        
        # Substitute variables
        formatted_text = self._substitute_variables(template, variables)
        
        # Handle mixed language content
        if self._has_mixed_languages(formatted_text):
            formatted_text = self._format_mixed_content(formatted_text)
        
        # Add direction markers if requested
        if add_direction_markers:
            direction = self.detect_text_direction(formatted_text)
            formatted_text = self._add_direction_markers(formatted_text, direction)
        
        # Apply language-specific formatting
        formatted_text = self._apply_language_formatting(formatted_text, language)
        
        # Clean up extra whitespace while preserving intentional formatting
        if preserve_formatting:
            formatted_text = self._clean_whitespace(formatted_text)
        
        return formatted_text
    
    def create_welcome_message(
        self,
        customer_name: str,
        restaurant_name: str,
        language: str = None
    ) -> str:
        """
        Create a personalized welcome message.
        
        Args:
            customer_name: Customer's name
            restaurant_name: Restaurant name
            language: Message language
            
        Returns:
            Formatted welcome message
        """
        language = language or self.default_language
        
        if language == "ar":
            template = f"مرحباً {{customer_name}} {self.RESTAURANT_EMOJIS['welcome']}\n\nأهلاً وسهلاً بك في {{restaurant_name}} {self.RESTAURANT_EMOJIS['food']}\n\nنحن سعداء لخدمتك! كيف يمكنني مساعدتك اليوم؟"
        else:
            template = f"Welcome {{customer_name}}! {self.RESTAURANT_EMOJIS['welcome']}\n\nThank you for choosing {{restaurant_name}} {self.RESTAURANT_EMOJIS['food']}\n\nWe're happy to serve you! How can I help you today?"
        
        return self.format_message(template, {
            'customer_name': customer_name,
            'restaurant_name': restaurant_name
        }, language)
    
    def create_order_confirmation(
        self,
        customer_name: str,
        order_number: str,
        items: List[Dict[str, Any]],
        total_amount: float,
        currency: str = "SAR",
        language: str = None
    ) -> str:
        """
        Create an order confirmation message.
        
        Args:
            customer_name: Customer's name
            order_number: Order reference number
            items: List of ordered items
            total_amount: Total order amount
            currency: Currency code
            language: Message language
            
        Returns:
            Formatted order confirmation message
        """
        language = language or self.default_language
        
        # Format items list
        items_text = self._format_order_items(items, language)
        
        # Format currency
        amount_text = self._format_currency(total_amount, currency, language)
        
        if language == "ar":
            template = f"تأكيد الطلب {self.RESTAURANT_EMOJIS['order']}\n\nعزيزي {{customer_name}},\n\nتم استلام طلبكم بنجاح!\n\nرقم الطلب: {{order_number}}\n\n{{items_list}}\n\nإجمالي المبلغ: {{total_amount}}\n\nشكراً لثقتكم بنا {self.RESTAURANT_EMOJIS['thank_you']}"
        else:
            template = f"Order Confirmation {self.RESTAURANT_EMOJIS['order']}\n\nDear {{customer_name}},\n\nYour order has been received successfully!\n\nOrder Number: {{order_number}}\n\n{{items_list}}\n\nTotal Amount: {{total_amount}}\n\nThank you for your trust {self.RESTAURANT_EMOJIS['thank_you']}"
        
        return self.format_message(template, {
            'customer_name': customer_name,
            'order_number': order_number,
            'items_list': items_text,
            'total_amount': amount_text
        }, language)
    
    def create_delivery_update(
        self,
        customer_name: str,
        order_number: str,
        status: str,
        estimated_time: Optional[str] = None,
        tracking_url: Optional[str] = None,
        language: str = None
    ) -> str:
        """
        Create a delivery status update message.
        
        Args:
            customer_name: Customer's name
            order_number: Order reference number
            status: Delivery status
            estimated_time: Estimated delivery time
            tracking_url: Optional tracking URL
            language: Message language
            
        Returns:
            Formatted delivery update message
        """
        language = language or self.default_language
        
        # Map status to localized text
        status_text = self._get_delivery_status_text(status, language)
        
        if language == "ar":
            template = f"تحديث التوصيل {self.RESTAURANT_EMOJIS['delivery']}\n\nعزيزي {{customer_name}},\n\nطلبكم رقم: {{order_number}}\nالحالة: {{status}}"
            
            if estimated_time:
                template += f"\nالوقت المتوقع: {{estimated_time}} {self.RESTAURANT_EMOJIS['time']}"
            
            if tracking_url:
                template += f"\n\nتتبع الطلب: {{tracking_url}}"
                
        else:
            template = f"Delivery Update {self.RESTAURANT_EMOJIS['delivery']}\n\nDear {{customer_name}},\n\nYour order #{{order_number}}\nStatus: {{status}}"
            
            if estimated_time:
                template += f"\nEstimated time: {{estimated_time}} {self.RESTAURANT_EMOJIS['time']}"
            
            if tracking_url:
                template += f"\n\nTrack your order: {{tracking_url}}"
        
        variables = {
            'customer_name': customer_name,
            'order_number': order_number,
            'status': status_text
        }
        
        if estimated_time:
            variables['estimated_time'] = estimated_time
        if tracking_url:
            variables['tracking_url'] = tracking_url
        
        return self.format_message(template, variables, language)
    
    def create_feedback_request(
        self,
        customer_name: str,
        order_number: str,
        rating_url: Optional[str] = None,
        language: str = None
    ) -> str:
        """
        Create a feedback request message.
        
        Args:
            customer_name: Customer's name
            order_number: Order reference number
            rating_url: Optional rating/review URL
            language: Message language
            
        Returns:
            Formatted feedback request message
        """
        language = language or self.default_language
        
        if language == "ar":
            template = f"تقييم تجربتك {self.RESTAURANT_EMOJIS['feedback']}\n\nعزيزي {{customer_name}},\n\nنأمل أن تكون راضياً عن طلبكم رقم {{order_number}}\n\nنحن نقدر رأيكم! كيف كانت تجربتكم معنا؟ {self.RESTAURANT_EMOJIS['rating']}"
            
            if rating_url:
                template += f"\n\nيمكنكم تقييم الخدمة هنا: {{rating_url}}"
                
        else:
            template = f"Rate Your Experience {self.RESTAURANT_EMOJIS['feedback']}\n\nDear {{customer_name}},\n\nWe hope you enjoyed your order #{{order_number}}\n\nWe value your feedback! How was your experience with us? {self.RESTAURANT_EMOJIS['rating']}"
            
            if rating_url:
                template += f"\n\nRate our service here: {{rating_url}}"
        
        variables = {
            'customer_name': customer_name,
            'order_number': order_number
        }
        
        if rating_url:
            variables['rating_url'] = rating_url
        
        return self.format_message(template, variables, language)
    
    def create_promotion_message(
        self,
        customer_name: str,
        promotion_title: str,
        promotion_details: str,
        discount_code: Optional[str] = None,
        expiry_date: Optional[datetime] = None,
        language: str = None
    ) -> str:
        """
        Create a promotional message.
        
        Args:
            customer_name: Customer's name
            promotion_title: Promotion title
            promotion_details: Promotion description
            discount_code: Optional discount code
            expiry_date: Optional expiry date
            language: Message language
            
        Returns:
            Formatted promotion message
        """
        language = language or self.default_language
        
        if language == "ar":
            template = f"عرض خاص {self.RESTAURANT_EMOJIS['discount']}\n\nعزيزي {{customer_name}},\n\n{{promotion_title}}\n\n{{promotion_details}}"
            
            if discount_code:
                template += f"\n\nكود الخصم: {{discount_code}}"
            
            if expiry_date:
                template += f"\nسارى حتى: {{expiry_date}}"
                
        else:
            template = f"Special Offer {self.RESTAURANT_EMOJIS['discount']}\n\nDear {{customer_name}},\n\n{{promotion_title}}\n\n{{promotion_details}}"
            
            if discount_code:
                template += f"\n\nDiscount Code: {{discount_code}}"
            
            if expiry_date:
                template += f"\nValid until: {{expiry_date}}"
        
        variables = {
            'customer_name': customer_name,
            'promotion_title': promotion_title,
            'promotion_details': promotion_details
        }
        
        if discount_code:
            variables['discount_code'] = discount_code
        if expiry_date:
            variables['expiry_date'] = self._format_date(expiry_date, language)
        
        return self.format_message(template, variables, language)
    
    def detect_text_direction(self, text: str) -> TextDirection:
        """
        Detect text direction based on content analysis.
        
        Args:
            text: Text to analyze
            
        Returns:
            Detected text direction
        """
        if not text:
            return TextDirection.LTR
        
        # Count Arabic characters
        arabic_chars = len(re.findall(self.ARABIC_RANGE, text))
        total_chars = len(re.sub(r'[^\w]', '', text))
        
        if total_chars == 0:
            return TextDirection.LTR
        
        # If more than 30% of characters are Arabic, consider RTL
        arabic_ratio = arabic_chars / total_chars
        
        if arabic_ratio > 0.3:
            return TextDirection.RTL
        elif arabic_ratio > 0:
            return TextDirection.AUTO  # Mixed content
        else:
            return TextDirection.LTR
    
    def _substitute_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """Substitute template variables with proper escaping."""
        result = template
        for key, value in variables.items():
            placeholder = f"{{{key}}}"  # Using single braces for simplicity
            result = result.replace(placeholder, str(value))
        return result
    
    def _has_mixed_languages(self, text: str) -> bool:
        """Check if text contains mixed languages."""
        has_arabic = bool(re.search(self.ARABIC_RANGE, text))
        has_latin = bool(re.search(r'[a-zA-Z]', text))
        return has_arabic and has_latin
    
    def _format_mixed_content(self, text: str) -> str:
        """Format mixed language content with proper direction handling."""
        # Split text into segments and handle each segment
        segments = re.split(r'(\n+)', text)
        formatted_segments = []
        
        for segment in segments:
            if segment.strip():
                direction = self.detect_text_direction(segment)
                if direction == TextDirection.RTL:
                    # Add RTL mark for Arabic content
                    formatted_segments.append(f"\u202B{segment}\u202C")
                else:
                    # Keep LTR content as is
                    formatted_segments.append(segment)
            else:
                formatted_segments.append(segment)
        
        return ''.join(formatted_segments)
    
    def _add_direction_markers(self, text: str, direction: TextDirection) -> str:
        """Add Unicode bidirectional markers."""
        if direction == TextDirection.RTL:
            # Right-to-left mark
            return f"\u202B{text}\u202C"
        elif direction == TextDirection.LTR:
            # Left-to-right mark
            return f"\u202A{text}\u202C"
        else:
            # Auto direction - let the client decide
            return text
    
    def _apply_language_formatting(self, text: str, language: str) -> str:
        """Apply language-specific formatting rules."""
        if language == "ar":
            # Arabic-specific formatting
            # Fix Arabic punctuation
            text = text.replace("?", "؟").replace(",", "،")
            
            # Ensure proper spacing around Arabic text
            text = re.sub(r'([' + self.ARABIC_RANGE + r'])(\w)', r'\1 \2', text)
            text = re.sub(r'(\w)([' + self.ARABIC_RANGE + r'])', r'\1 \2', text)
        
        return text
    
    def _clean_whitespace(self, text: str) -> str:
        """Clean up whitespace while preserving formatting."""
        # Remove trailing whitespace from lines
        lines = text.split('\n')
        cleaned_lines = [line.rstrip() for line in lines]
        
        # Remove excessive empty lines (more than 2)
        result = []
        empty_count = 0
        
        for line in cleaned_lines:
            if line.strip():
                result.append(line)
                empty_count = 0
            else:
                empty_count += 1
                if empty_count <= 2:  # Allow up to 2 empty lines
                    result.append(line)
        
        return '\n'.join(result)
    
    def _format_order_items(self, items: List[Dict[str, Any]], language: str) -> str:
        """Format order items list."""
        if not items:
            return ""
        
        formatted_items = []
        for i, item in enumerate(items, 1):
            name = item.get('name', 'Unknown Item')
            quantity = item.get('quantity', 1)
            price = item.get('price', 0.0)
            
            if language == "ar":
                formatted_items.append(f"{i}. {name} (الكمية: {quantity}) - {price:.2f} ر.س")
            else:
                formatted_items.append(f"{i}. {name} (Qty: {quantity}) - {price:.2f} SAR")
        
        return '\n'.join(formatted_items)
    
    def _format_currency(self, amount: float, currency: str, language: str) -> str:
        """Format currency amount based on language."""
        if language == "ar":
            if currency.upper() == "SAR":
                return f"{amount:.2f} ر.س"
            else:
                return f"{amount:.2f} {currency}"
        else:
            return f"{amount:.2f} {currency}"
    
    def _get_delivery_status_text(self, status: str, language: str) -> str:
        """Get localized delivery status text."""
        status_map = {
            "ar": {
                "preparing": "جاري التحضير",
                "ready": "جاهز للاستلام",
                "picked_up": "تم الاستلام",
                "on_way": "في الطريق إليك",
                "delivered": "تم التوصيل",
                "cancelled": "تم الإلغاء"
            },
            "en": {
                "preparing": "Being prepared",
                "ready": "Ready for pickup",
                "picked_up": "Picked up",
                "on_way": "On the way",
                "delivered": "Delivered",
                "cancelled": "Cancelled"
            }
        }
        
        return status_map.get(language, status_map["en"]).get(status, status)
    
    def _format_date(self, date: datetime, language: str) -> str:
        """Format date based on language preferences."""
        if language == "ar":
            # Arabic date format
            return date.strftime("%d/%m/%Y")
        else:
            # English date format
            return date.strftime("%B %d, %Y")
    
    def format_phone_number_display(self, phone: str, language: str = None) -> str:
        """Format phone number for display in messages."""
        language = language or self.default_language
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Format Saudi numbers
        if digits.startswith('966'):
            # +966 50 123 4567
            formatted = f"+966 {digits[3:5]} {digits[5:8]} {digits[8:]}"
        elif digits.startswith('0') and len(digits) == 10:
            # 050 123 4567
            formatted = f"{digits[:3]} {digits[3:6]} {digits[6:]}"
        else:
            # Default formatting
            formatted = phone
        
        return formatted
    
    def create_interactive_buttons(
        self,
        buttons: List[Dict[str, str]],
        language: str = None
    ) -> List[Dict[str, Any]]:
        """
        Create interactive button structure for WhatsApp.
        
        Args:
            buttons: List of button definitions
            language: Target language
            
        Returns:
            Formatted button structure
        """
        language = language or self.default_language
        formatted_buttons = []
        
        for i, button in enumerate(buttons):
            formatted_buttons.append({
                "type": "reply",
                "reply": {
                    "id": button.get("id", f"btn_{i}"),
                    "title": button.get("title", "Button")
                }
            })
        
        return formatted_buttons
    
    def create_quick_replies(
        self,
        options: List[str],
        language: str = None
    ) -> List[Dict[str, Any]]:
        """
        Create quick reply options.
        
        Args:
            options: List of quick reply options
            language: Target language
            
        Returns:
            Formatted quick reply structure
        """
        language = language or self.default_language
        quick_replies = []
        
        for i, option in enumerate(options):
            quick_replies.append({
                "type": "reply",
                "reply": {
                    "id": f"quick_{i}",
                    "title": option[:24]  # WhatsApp limit is 24 characters
                }
            })
        
        return quick_replies