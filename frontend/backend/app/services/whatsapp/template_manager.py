"""
WhatsApp message template management system.

This module provides comprehensive template management for WhatsApp Business API,
including template creation, validation, synchronization with WhatsApp servers,
and restaurant-specific template scenarios.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass

import httpx
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.config import settings
from app.models.whatsapp import MessageTemplate, TemplateStatus
from .exceptions import (
    TemplateNotFoundError, TemplateValidationError, WhatsAppAPIError
)
from .formatter import MessageFormatter


class TemplateCategory(str, Enum):
    """WhatsApp template categories."""
    AUTHENTICATION = "AUTHENTICATION"
    MARKETING = "MARKETING"
    UTILITY = "UTILITY"


class TemplateComponentType(str, Enum):
    """Template component types."""
    HEADER = "HEADER"
    BODY = "BODY"
    FOOTER = "FOOTER"
    BUTTONS = "BUTTONS"


class ButtonType(str, Enum):
    """Button types for interactive templates."""
    QUICK_REPLY = "QUICK_REPLY"
    PHONE_NUMBER = "PHONE_NUMBER"
    URL = "URL"


@dataclass
class TemplateParameter:
    """Template parameter definition."""
    name: str
    type: str  # TEXT, CURRENCY, DATE_TIME, etc.
    example: str
    component: str  # HEADER, BODY, FOOTER
    index: int  # Parameter index in component


@dataclass
class TemplateButton:
    """Template button definition."""
    type: ButtonType
    text: str
    phone_number: Optional[str] = None
    url: Optional[str] = None


class RestaurantTemplateScenarios:
    """Pre-defined restaurant template scenarios."""
    
    @staticmethod
    def get_welcome_template(language: str = "ar") -> Dict[str, Any]:
        """Welcome message template."""
        if language == "ar":
            return {
                "name": "welcome_customer_ar",
                "language": "ar",
                "category": TemplateCategory.UTILITY,
                "header_text": "مرحباً بك في {{1}}! 👋",
                "body_text": "أهلاً وسهلاً بك {{1}}!\n\nنحن سعداء لخدمتك في {{2}}. يمكنك الآن:\n\n• تصفح قائمة الطعام\n• تقديم طلب جديد\n• تتبع طلبك الحالي\n• تقييم تجربتك\n\nكيف يمكنني مساعدتك اليوم؟",
                "footer_text": "نشكرك لاختيارك لنا 🙏",
                "parameters": [
                    TemplateParameter("restaurant_name", "TEXT", "مطعم الأصالة", "HEADER", 1),
                    TemplateParameter("customer_name", "TEXT", "أحمد", "BODY", 1),
                    TemplateParameter("restaurant_name", "TEXT", "مطعم الأصالة", "BODY", 2)
                ],
                "buttons": [
                    TemplateButton(ButtonType.QUICK_REPLY, "قائمة الطعام 🍽️"),
                    TemplateButton(ButtonType.QUICK_REPLY, "طلب جديد 🛒"),
                    TemplateButton(ButtonType.PHONE_NUMBER, "اتصل بنا 📞", "+966501234567")
                ]
            }
        else:
            return {
                "name": "welcome_customer_en",
                "language": "en",
                "category": TemplateCategory.UTILITY,
                "header_text": "Welcome to {{1}}! 👋",
                "body_text": "Hello {{1}}!\n\nWe're happy to serve you at {{2}}. You can now:\n\n• Browse our menu\n• Place a new order\n• Track your current order\n• Rate your experience\n\nHow can I help you today?",
                "footer_text": "Thank you for choosing us 🙏",
                "parameters": [
                    TemplateParameter("restaurant_name", "TEXT", "Authenticity Restaurant", "HEADER", 1),
                    TemplateParameter("customer_name", "TEXT", "Ahmed", "BODY", 1),
                    TemplateParameter("restaurant_name", "TEXT", "Authenticity Restaurant", "BODY", 2)
                ],
                "buttons": [
                    TemplateButton(ButtonType.QUICK_REPLY, "Menu 🍽️"),
                    TemplateButton(ButtonType.QUICK_REPLY, "New Order 🛒"),
                    TemplateButton(ButtonType.PHONE_NUMBER, "Call Us 📞", "+966501234567")
                ]
            }
    
    @staticmethod
    def get_order_confirmation_template(language: str = "ar") -> Dict[str, Any]:
        """Order confirmation template."""
        if language == "ar":
            return {
                "name": "order_confirmation_ar",
                "language": "ar",
                "category": TemplateCategory.UTILITY,
                "header_text": "تأكيد طلبك 📋",
                "body_text": "عزيزي {{1}},\n\nتم استلام طلبكم بنجاح!\n\nرقم الطلب: {{2}}\nإجمالي المبلغ: {{3}}\nطريقة الدفع: {{4}}\nوقت التوصيل المتوقع: {{5}}\n\nسنقوم بإرسال تحديثات حول حالة طلبكم قريباً.",
                "footer_text": "شكراً لثقتكم بنا 🙏",
                "parameters": [
                    TemplateParameter("customer_name", "TEXT", "أحمد", "BODY", 1),
                    TemplateParameter("order_number", "TEXT", "ORD-2024-001", "BODY", 2),
                    TemplateParameter("total_amount", "TEXT", "85.50 ر.س", "BODY", 3),
                    TemplateParameter("payment_method", "TEXT", "الدفع عند الاستلام", "BODY", 4),
                    TemplateParameter("delivery_time", "TEXT", "30-45 دقيقة", "BODY", 5)
                ]
            }
        else:
            return {
                "name": "order_confirmation_en",
                "language": "en",
                "category": TemplateCategory.UTILITY,
                "header_text": "Order Confirmation 📋",
                "body_text": "Dear {{1}},\n\nYour order has been received successfully!\n\nOrder Number: {{2}}\nTotal Amount: {{3}}\nPayment Method: {{4}}\nEstimated Delivery: {{5}}\n\nWe'll send you updates about your order status soon.",
                "footer_text": "Thank you for your trust 🙏",
                "parameters": [
                    TemplateParameter("customer_name", "TEXT", "Ahmed", "BODY", 1),
                    TemplateParameter("order_number", "TEXT", "ORD-2024-001", "BODY", 2),
                    TemplateParameter("total_amount", "TEXT", "85.50 SAR", "BODY", 3),
                    TemplateParameter("payment_method", "TEXT", "Cash on Delivery", "BODY", 4),
                    TemplateParameter("delivery_time", "TEXT", "30-45 minutes", "BODY", 5)
                ]
            }
    
    @staticmethod
    def get_delivery_status_template(language: str = "ar") -> Dict[str, Any]:
        """Delivery status update template."""
        if language == "ar":
            return {
                "name": "delivery_status_ar",
                "language": "ar",
                "category": TemplateCategory.UTILITY,
                "header_text": "تحديث حالة التوصيل 🚚",
                "body_text": "عزيزي {{1}},\n\nطلبكم رقم {{2}} الآن {{3}}.\n\nالوقت المتوقع للوصول: {{4}}\n\nسائق التوصيل: {{5}}\nرقم الهاتف: {{6}}",
                "footer_text": "نشكركم لصبركم 🙏",
                "parameters": [
                    TemplateParameter("customer_name", "TEXT", "أحمد", "BODY", 1),
                    TemplateParameter("order_number", "TEXT", "ORD-2024-001", "BODY", 2),
                    TemplateParameter("status", "TEXT", "في الطريق إليكم", "BODY", 3),
                    TemplateParameter("eta", "TEXT", "15 دقيقة", "BODY", 4),
                    TemplateParameter("driver_name", "TEXT", "محمد أحمد", "BODY", 5),
                    TemplateParameter("driver_phone", "TEXT", "+966501234567", "BODY", 6)
                ]
            }
        else:
            return {
                "name": "delivery_status_en",
                "language": "en",
                "category": TemplateCategory.UTILITY,
                "header_text": "Delivery Status Update 🚚",
                "body_text": "Dear {{1}},\n\nYour order #{{2}} is now {{3}}.\n\nEstimated arrival time: {{4}}\n\nDelivery driver: {{5}}\nPhone number: {{6}}",
                "footer_text": "Thank you for your patience 🙏",
                "parameters": [
                    TemplateParameter("customer_name", "TEXT", "Ahmed", "BODY", 1),
                    TemplateParameter("order_number", "TEXT", "ORD-2024-001", "BODY", 2),
                    TemplateParameter("status", "TEXT", "on the way", "BODY", 3),
                    TemplateParameter("eta", "TEXT", "15 minutes", "BODY", 4),
                    TemplateParameter("driver_name", "TEXT", "Mohammed Ahmed", "BODY", 5),
                    TemplateParameter("driver_phone", "TEXT", "+966501234567", "BODY", 6)
                ]
            }
    
    @staticmethod
    def get_feedback_request_template(language: str = "ar") -> Dict[str, Any]:
        """Feedback request template."""
        if language == "ar":
            return {
                "name": "feedback_request_ar",
                "language": "ar",
                "category": TemplateCategory.UTILITY,
                "header_text": "تقييم تجربتك معنا ⭐",
                "body_text": "عزيزي {{1}},\n\nنأمل أن تكون راضياً عن طلبكم رقم {{2}}.\n\nرأيكم مهم جداً لنا! كيف كانت تجربتك معنا اليوم؟\n\nيمكنك تقييم الخدمة والطعام والتوصيل.",
                "footer_text": "نقدر وقتكم 🙏",
                "buttons": [
                    TemplateButton(ButtonType.QUICK_REPLY, "ممتاز ⭐⭐⭐⭐⭐"),
                    TemplateButton(ButtonType.QUICK_REPLY, "جيد ⭐⭐⭐⭐"),
                    TemplateButton(ButtonType.QUICK_REPLY, "مقبول ⭐⭐⭐")
                ],
                "parameters": [
                    TemplateParameter("customer_name", "TEXT", "أحمد", "BODY", 1),
                    TemplateParameter("order_number", "TEXT", "ORD-2024-001", "BODY", 2)
                ]
            }
        else:
            return {
                "name": "feedback_request_en",
                "language": "en",
                "category": TemplateCategory.UTILITY,
                "header_text": "Rate Your Experience ⭐",
                "body_text": "Dear {{1}},\n\nWe hope you enjoyed your order #{{2}}.\n\nYour feedback is very important to us! How was your experience with us today?\n\nYou can rate our service, food, and delivery.",
                "footer_text": "We appreciate your time 🙏",
                "buttons": [
                    TemplateButton(ButtonType.QUICK_REPLY, "Excellent ⭐⭐⭐⭐⭐"),
                    TemplateButton(ButtonType.QUICK_REPLY, "Good ⭐⭐⭐⭐"),
                    TemplateButton(ButtonType.QUICK_REPLY, "Average ⭐⭐⭐")
                ],
                "parameters": [
                    TemplateParameter("customer_name", "TEXT", "Ahmed", "BODY", 1),
                    TemplateParameter("order_number", "TEXT", "ORD-2024-001", "BODY", 2)
                ]
            }
    
    @staticmethod
    def get_promotion_template(language: str = "ar") -> Dict[str, Any]:
        """Promotion/marketing template."""
        if language == "ar":
            return {
                "name": "promotion_offer_ar",
                "language": "ar",
                "category": TemplateCategory.MARKETING,
                "header_text": "عرض خاص لك! 🎉",
                "body_text": "عزيزي {{1}},\n\n{{2}}\n\nاستخدم كود الخصم: {{3}}\nسارى حتى: {{4}}\n\nلا تفوت هذه الفرصة الذهبية!",
                "footer_text": "شروط وأحكام العرض تطبق",
                "buttons": [
                    TemplateButton(ButtonType.QUICK_REPLY, "اطلب الآن 🛒"),
                    TemplateButton(ButtonType.URL, "تصفح القائمة 🍽️", "https://menu.restaurant.com")
                ],
                "parameters": [
                    TemplateParameter("customer_name", "TEXT", "أحمد", "BODY", 1),
                    TemplateParameter("offer_details", "TEXT", "خصم 25% على جميع الوجبات الرئيسية", "BODY", 2),
                    TemplateParameter("promo_code", "TEXT", "SAVE25", "BODY", 3),
                    TemplateParameter("expiry_date", "TEXT", "31 ديسمبر 2024", "BODY", 4)
                ]
            }
        else:
            return {
                "name": "promotion_offer_en",
                "language": "en",
                "category": TemplateCategory.MARKETING,
                "header_text": "Special Offer for You! 🎉",
                "body_text": "Dear {{1}},\n\n{{2}}\n\nUse discount code: {{3}}\nValid until: {{4}}\n\nDon't miss this golden opportunity!",
                "footer_text": "Terms and conditions apply",
                "buttons": [
                    TemplateButton(ButtonType.QUICK_REPLY, "Order Now 🛒"),
                    TemplateButton(ButtonType.URL, "Browse Menu 🍽️", "https://menu.restaurant.com")
                ],
                "parameters": [
                    TemplateParameter("customer_name", "TEXT", "Ahmed", "BODY", 1),
                    TemplateParameter("offer_details", "TEXT", "25% off all main courses", "BODY", 2),
                    TemplateParameter("promo_code", "TEXT", "SAVE25", "BODY", 3),
                    TemplateParameter("expiry_date", "TEXT", "December 31, 2024", "BODY", 4)
                ]
            }


class TemplateValidator:
    """Template validation utilities."""
    
    @staticmethod
    def validate_template_data(template_data: Dict[str, Any]) -> List[str]:
        """
        Validate template data before creation.
        
        Args:
            template_data: Template data dictionary
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields
        required_fields = ['name', 'language', 'category', 'body_text']
        for field in required_fields:
            if field not in template_data or not template_data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate category
        if 'category' in template_data:
            try:
                TemplateCategory(template_data['category'])
            except ValueError:
                errors.append(f"Invalid category: {template_data['category']}")
        
        # Validate language code
        if 'language' in template_data:
            language = template_data['language']
            if language not in settings.SUPPORTED_LANGUAGES:
                errors.append(f"Unsupported language: {language}")
        
        # Validate template name
        if 'name' in template_data:
            name = template_data['name']
            if not name.replace('_', '').replace('-', '').isalnum():
                errors.append("Template name must contain only letters, numbers, underscores, and hyphens")
            if len(name) > 512:
                errors.append("Template name must be 512 characters or less")
        
        # Validate text lengths
        text_limits = {
            'header_text': 60,
            'body_text': 1024,
            'footer_text': 60
        }
        
        for field, limit in text_limits.items():
            if field in template_data and template_data[field]:
                if len(template_data[field]) > limit:
                    errors.append(f"{field} must be {limit} characters or less")
        
        # Validate parameters
        if 'parameters' in template_data:
            parameters = template_data['parameters']
            if not isinstance(parameters, list):
                errors.append("Parameters must be a list")
            else:
                for i, param in enumerate(parameters):
                    if not isinstance(param, dict):
                        errors.append(f"Parameter {i} must be a dictionary")
                        continue
                    
                    if 'name' not in param or 'type' not in param:
                        errors.append(f"Parameter {i} missing required fields (name, type)")
        
        # Validate buttons
        if 'buttons' in template_data:
            buttons = template_data['buttons']
            if not isinstance(buttons, list):
                errors.append("Buttons must be a list")
            elif len(buttons) > 3:
                errors.append("Maximum 3 buttons allowed")
            else:
                for i, button in enumerate(buttons):
                    if not isinstance(button, dict):
                        errors.append(f"Button {i} must be a dictionary")
                        continue
                    
                    if 'type' not in button or 'text' not in button:
                        errors.append(f"Button {i} missing required fields (type, text)")
                        continue
                    
                    try:
                        ButtonType(button['type'])
                    except ValueError:
                        errors.append(f"Button {i} has invalid type: {button['type']}")
        
        return errors
    
    @staticmethod
    def validate_parameter_values(
        template: MessageTemplate,
        parameters: Dict[str, Any]
    ) -> List[str]:
        """
        Validate parameter values against template requirements.
        
        Args:
            template: Message template
            parameters: Parameter values to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if not template.parameters:
            if parameters:
                errors.append("Template does not accept parameters")
            return errors
        
        # Get required parameters
        template_params = {p['name']: p for p in template.parameters}
        required_params = {
            name for name, param in template_params.items()
            if param.get('required', True)
        }
        
        # Check for missing required parameters
        provided_params = set(parameters.keys())
        missing_params = required_params - provided_params
        
        if missing_params:
            errors.append(f"Missing required parameters: {', '.join(missing_params)}")
        
        # Check for extra parameters
        extra_params = provided_params - set(template_params.keys())
        if extra_params:
            errors.append(f"Unknown parameters: {', '.join(extra_params)}")
        
        # Validate parameter types and values
        for param_name, value in parameters.items():
            if param_name not in template_params:
                continue
            
            param_def = template_params[param_name]
            param_type = param_def.get('type', 'TEXT')
            
            # Basic type validation
            if param_type == 'TEXT' and not isinstance(value, str):
                errors.append(f"Parameter '{param_name}' must be a string")
            elif param_type == 'CURRENCY' and not isinstance(value, (int, float, str)):
                errors.append(f"Parameter '{param_name}' must be a currency value")
            elif param_type == 'DATE_TIME' and not isinstance(value, str):
                errors.append(f"Parameter '{param_name}' must be a datetime string")
        
        return errors


class TemplateManager:
    """
    Comprehensive template management for WhatsApp Business API.
    
    Features:
    - Template CRUD operations
    - Template validation and approval tracking
    - Synchronization with WhatsApp servers
    - Restaurant-specific template scenarios
    - Multi-language template support
    - Template usage analytics
    """
    
    def __init__(self, db: Session):
        """Initialize template manager."""
        self.db = db
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.business_account_id = settings.WHATSAPP_BUSINESS_ACCOUNT_ID
        self.logger = logging.getLogger(__name__)
        
        # HTTP client for WhatsApp API
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_connections=5)
        )
        
        # Message formatter for template rendering
        self.formatter = MessageFormatter()
    
    async def create_template(
        self,
        template_data: Dict[str, Any],
        submit_to_whatsapp: bool = True
    ) -> MessageTemplate:
        """
        Create a new message template.
        
        Args:
            template_data: Template definition
            submit_to_whatsapp: Whether to submit to WhatsApp for approval
            
        Returns:
            Created template record
            
        Raises:
            TemplateValidationError: If template data is invalid
        """
        # Validate template data
        validation_errors = TemplateValidator.validate_template_data(template_data)
        if validation_errors:
            raise TemplateValidationError(
                "Template validation failed",
                template_data.get('name'),
                validation_errors
            )
        
        # Check if template already exists
        existing = self.db.query(MessageTemplate).filter(
            and_(
                MessageTemplate.name == template_data['name'],
                MessageTemplate.language == template_data['language']
            )
        ).first()
        
        if existing:
            raise TemplateValidationError(
                f"Template '{template_data['name']}' already exists for language '{template_data['language']}'"
            )
        
        # Create template record
        template = MessageTemplate(
            name=template_data['name'],
            language=template_data['language'],
            category=template_data['category'],
            status=TemplateStatus.PENDING,
            header_text=template_data.get('header_text'),
            body_text=template_data['body_text'],
            footer_text=template_data.get('footer_text'),
            parameters=self._process_parameters(template_data.get('parameters', [])),
            buttons=self._process_buttons(template_data.get('buttons', [])),
            description=template_data.get('description'),
            tags=template_data.get('tags', []),
            is_active=True
        )
        
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        
        # Submit to WhatsApp for approval
        if submit_to_whatsapp:
            try:
                whatsapp_id = await self._submit_to_whatsapp(template)
                template.whatsapp_template_id = whatsapp_id
                template.submitted_at = datetime.utcnow().isoformat()
                self.db.commit()
                
                self.logger.info(f"Template '{template.name}' submitted to WhatsApp: {whatsapp_id}")
            except Exception as e:
                self.logger.error(f"Failed to submit template to WhatsApp: {str(e)}")
                # Template is still created locally, but not submitted
        
        return template
    
    async def update_template(
        self,
        template_id: int,
        template_data: Dict[str, Any],
        resubmit_to_whatsapp: bool = False
    ) -> MessageTemplate:
        """
        Update an existing template.
        
        Args:
            template_id: Template database ID
            template_data: Updated template data
            resubmit_to_whatsapp: Whether to resubmit to WhatsApp
            
        Returns:
            Updated template record
        """
        template = self.db.query(MessageTemplate).filter(
            MessageTemplate.id == template_id
        ).first()
        
        if not template:
            raise TemplateNotFoundError(f"Template with ID {template_id} not found")
        
        # Validate updated data
        validation_errors = TemplateValidator.validate_template_data(template_data)
        if validation_errors:
            raise TemplateValidationError(
                "Template validation failed",
                template.name,
                validation_errors
            )
        
        # Update template fields
        for field in ['category', 'header_text', 'body_text', 'footer_text', 'description']:
            if field in template_data:
                setattr(template, field, template_data[field])
        
        if 'parameters' in template_data:
            template.parameters = self._process_parameters(template_data['parameters'])
        
        if 'buttons' in template_data:
            template.buttons = self._process_buttons(template_data['buttons'])
        
        if 'tags' in template_data:
            template.tags = template_data['tags']
        
        if 'is_active' in template_data:
            template.is_active = template_data['is_active']
        
        # Reset status if content changed
        if any(field in template_data for field in ['header_text', 'body_text', 'footer_text', 'parameters', 'buttons']):
            template.status = TemplateStatus.PENDING
            template.approved_at = None
            template.rejected_at = None
            template.rejection_reason = None
        
        self.db.commit()
        
        # Resubmit to WhatsApp if requested
        if resubmit_to_whatsapp:
            try:
                whatsapp_id = await self._submit_to_whatsapp(template)
                template.whatsapp_template_id = whatsapp_id
                template.submitted_at = datetime.utcnow().isoformat()
                self.db.commit()
            except Exception as e:
                self.logger.error(f"Failed to resubmit template to WhatsApp: {str(e)}")
        
        return template
    
    async def delete_template(self, template_id: int, delete_from_whatsapp: bool = True) -> bool:
        """
        Delete a template.
        
        Args:
            template_id: Template database ID
            delete_from_whatsapp: Whether to delete from WhatsApp as well
            
        Returns:
            True if deleted successfully
        """
        template = self.db.query(MessageTemplate).filter(
            MessageTemplate.id == template_id
        ).first()
        
        if not template:
            raise TemplateNotFoundError(f"Template with ID {template_id} not found")
        
        # Delete from WhatsApp first
        if delete_from_whatsapp and template.whatsapp_template_id:
            try:
                await self._delete_from_whatsapp(template.whatsapp_template_id)
            except Exception as e:
                self.logger.error(f"Failed to delete template from WhatsApp: {str(e)}")
        
        # Delete from database
        self.db.delete(template)
        self.db.commit()
        
        self.logger.info(f"Template '{template.name}' deleted")
        return True
    
    def get_template(
        self,
        name: str,
        language: str = None
    ) -> Optional[MessageTemplate]:
        """
        Get template by name and language.
        
        Args:
            name: Template name
            language: Template language (uses default if not provided)
            
        Returns:
            Template record or None
        """
        language = language or settings.DEFAULT_LANGUAGE
        
        return self.db.query(MessageTemplate).filter(
            and_(
                MessageTemplate.name == name,
                MessageTemplate.language == language,
                MessageTemplate.is_active == True
            )
        ).first()
    
    def list_templates(
        self,
        language: Optional[str] = None,
        category: Optional[TemplateCategory] = None,
        status: Optional[TemplateStatus] = None,
        active_only: bool = True
    ) -> List[MessageTemplate]:
        """
        List templates with filtering options.
        
        Args:
            language: Filter by language
            category: Filter by category
            status: Filter by approval status
            active_only: Whether to include only active templates
            
        Returns:
            List of templates
        """
        query = self.db.query(MessageTemplate)
        
        if language:
            query = query.filter(MessageTemplate.language == language)
        
        if category:
            query = query.filter(MessageTemplate.category == category)
        
        if status:
            query = query.filter(MessageTemplate.status == status)
        
        if active_only:
            query = query.filter(MessageTemplate.is_active == True)
        
        return query.order_by(MessageTemplate.created_at.desc()).all()
    
    async def sync_templates_from_whatsapp(self) -> Dict[str, int]:
        """
        Synchronize templates from WhatsApp servers.
        
        Returns:
            Sync statistics
        """
        try:
            url = f"https://graph.facebook.com/v18.0/{self.business_account_id}/message_templates"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            response = await self.client.get(url, headers=headers)
            
            if response.status_code != 200:
                raise WhatsAppAPIError(f"Failed to fetch templates: {response.text}")
            
            data = response.json()
            whatsapp_templates = data.get('data', [])
            
            stats = {
                'fetched': len(whatsapp_templates),
                'updated': 0,
                'created': 0,
                'errors': 0
            }
            
            for wt_template in whatsapp_templates:
                try:
                    await self._sync_single_template(wt_template)
                    stats['updated'] += 1
                except Exception as e:
                    self.logger.error(f"Error syncing template {wt_template.get('name')}: {str(e)}")
                    stats['errors'] += 1
            
            self.logger.info(f"Template sync completed: {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"Template sync failed: {str(e)}")
            raise
    
    async def create_restaurant_templates(
        self,
        languages: Optional[List[str]] = None
    ) -> Dict[str, List[MessageTemplate]]:
        """
        Create standard restaurant templates for specified languages.
        
        Args:
            languages: List of language codes (uses supported languages if not provided)
            
        Returns:
            Dictionary of created templates by language
        """
        languages = languages or settings.SUPPORTED_LANGUAGES
        created_templates = {}
        
        # Template scenarios to create
        scenarios = [
            RestaurantTemplateScenarios.get_welcome_template,
            RestaurantTemplateScenarios.get_order_confirmation_template,
            RestaurantTemplateScenarios.get_delivery_status_template,
            RestaurantTemplateScenarios.get_feedback_request_template,
            RestaurantTemplateScenarios.get_promotion_template
        ]
        
        for language in languages:
            created_templates[language] = []
            
            for scenario_func in scenarios:
                try:
                    template_data = scenario_func(language)
                    
                    # Check if template already exists
                    existing = self.get_template(template_data['name'], language)
                    if existing:
                        self.logger.info(f"Template '{template_data['name']}' already exists for {language}")
                        continue
                    
                    # Create template
                    template = await self.create_template(template_data, submit_to_whatsapp=True)
                    created_templates[language].append(template)
                    
                    self.logger.info(f"Created template '{template.name}' for {language}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to create template for {language}: {str(e)}")
        
        return created_templates
    
    def render_template(
        self,
        template_name: str,
        parameters: Dict[str, Any],
        language: str = None
    ) -> str:
        """
        Render template with parameters.
        
        Args:
            template_name: Template name
            parameters: Parameter values
            language: Template language
            
        Returns:
            Rendered template text
            
        Raises:
            TemplateNotFoundError: If template not found
            TemplateValidationError: If parameters are invalid
        """
        template = self.get_template(template_name, language)
        if not template:
            raise TemplateNotFoundError(
                f"Template '{template_name}' not found",
                template_name,
                language
            )
        
        # Validate parameters
        validation_errors = TemplateValidator.validate_parameter_values(template, parameters)
        if validation_errors:
            raise TemplateValidationError(
                "Parameter validation failed",
                template_name,
                validation_errors
            )
        
        return template.render_body(parameters)
    
    def _process_parameters(self, parameters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and validate template parameters."""
        processed = []
        
        for param in parameters:
            if isinstance(param, TemplateParameter):
                processed.append({
                    'name': param.name,
                    'type': param.type,
                    'example': param.example,
                    'component': param.component,
                    'index': param.index,
                    'required': True
                })
            elif isinstance(param, dict):
                processed.append({
                    'name': param.get('name'),
                    'type': param.get('type', 'TEXT'),
                    'example': param.get('example', ''),
                    'component': param.get('component', 'BODY'),
                    'index': param.get('index', 1),
                    'required': param.get('required', True)
                })
        
        return processed
    
    def _process_buttons(self, buttons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and validate template buttons."""
        processed = []
        
        for button in buttons:
            if isinstance(button, TemplateButton):
                button_data = {
                    'type': button.type.value,
                    'text': button.text
                }
                if button.phone_number:
                    button_data['phone_number'] = button.phone_number
                if button.url:
                    button_data['url'] = button.url
                
                processed.append(button_data)
            elif isinstance(button, dict):
                processed.append(button)
        
        return processed
    
    async def _submit_to_whatsapp(self, template: MessageTemplate) -> str:
        """Submit template to WhatsApp for approval."""
        url = f"https://graph.facebook.com/v18.0/{self.business_account_id}/message_templates"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Build template payload
        payload = {
            "name": template.name,
            "language": template.language,
            "category": template.category,
            "components": self._build_whatsapp_components(template)
        }
        
        response = await self.client.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            return result.get('id')
        else:
            error_data = response.json() if response.content else {}
            error_message = error_data.get('error', {}).get('message', 'Unknown error')
            raise WhatsAppAPIError(f"Template submission failed: {error_message}")
    
    async def _delete_from_whatsapp(self, whatsapp_template_id: str) -> bool:
        """Delete template from WhatsApp."""
        url = f"https://graph.facebook.com/v18.0/{whatsapp_template_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        response = await self.client.delete(url, headers=headers)
        return response.status_code == 200
    
    def _build_whatsapp_components(self, template: MessageTemplate) -> List[Dict[str, Any]]:
        """Build WhatsApp template components."""
        components = []
        
        # Header component
        if template.header_text:
            components.append({
                "type": "HEADER",
                "format": "TEXT",
                "text": template.header_text
            })
        
        # Body component (required)
        body_component = {
            "type": "BODY",
            "text": template.body_text
        }
        
        # Add parameters if any
        if template.parameters:
            body_params = [p for p in template.parameters if p.get('component') == 'BODY']
            if body_params:
                body_component["example"] = {
                    "body_text": [[p.get('example', '') for p in body_params]]
                }
        
        components.append(body_component)
        
        # Footer component
        if template.footer_text:
            components.append({
                "type": "FOOTER",
                "text": template.footer_text
            })
        
        # Buttons component
        if template.buttons:
            button_components = []
            for button in template.buttons:
                if button['type'] == 'QUICK_REPLY':
                    button_components.append({
                        "type": "QUICK_REPLY",
                        "text": button['text']
                    })
                elif button['type'] == 'PHONE_NUMBER':
                    button_components.append({
                        "type": "PHONE_NUMBER",
                        "text": button['text'],
                        "phone_number": button['phone_number']
                    })
                elif button['type'] == 'URL':
                    button_components.append({
                        "type": "URL",
                        "text": button['text'],
                        "url": button['url']
                    })
            
            if button_components:
                components.append({
                    "type": "BUTTONS",
                    "buttons": button_components
                })
        
        return components
    
    async def _sync_single_template(self, whatsapp_template: Dict[str, Any]):
        """Sync a single template from WhatsApp."""
        name = whatsapp_template.get('name')
        language = whatsapp_template.get('language')
        
        # Find existing template
        template = self.db.query(MessageTemplate).filter(
            and_(
                MessageTemplate.name == name,
                MessageTemplate.language == language
            )
        ).first()
        
        if template:
            # Update existing template
            template.whatsapp_template_id = whatsapp_template.get('id')
            template.status = whatsapp_template.get('status', 'PENDING')
            
            # Update approval timestamps
            if template.status == 'APPROVED' and not template.approved_at:
                template.approved_at = datetime.utcnow().isoformat()
            elif template.status == 'REJECTED' and not template.rejected_at:
                template.rejected_at = datetime.utcnow().isoformat()
        
        self.db.commit()
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()