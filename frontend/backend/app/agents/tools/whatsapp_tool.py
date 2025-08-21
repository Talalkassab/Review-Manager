"""
WhatsApp Business API integration tool for sending messages and managing conversations.
"""
import httpx
import json
from typing import Any, Dict, List, Optional
from pydantic import Field

from .base_tool import BaseAgentTool, ToolResult
from ...core.config import settings


class WhatsAppTool(BaseAgentTool):
    """Tool for interacting with WhatsApp Business API."""
    
    name: str = "whatsapp_messenger"
    description: str = (
        "Send WhatsApp messages, templates, and manage conversations through "
        "WhatsApp Business API. Supports Arabic and English messaging."
    )
    
    access_token: str = Field(default=settings.WHATSAPP_ACCESS_TOKEN, description="WhatsApp access token")
    phone_number_id: str = Field(default=settings.WHATSAPP_PHONE_NUMBER_ID, description="WhatsApp phone number ID")
    base_url: str = Field(default="https://graph.facebook.com/v18.0", description="WhatsApp API base URL")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
    
    def _validate_input(self, **kwargs) -> bool:
        """Validate input parameters for WhatsApp operations."""
        phone_number = kwargs.get('phone_number') or kwargs.get('to')
        message = kwargs.get('message')
        action = kwargs.get('action', 'send_message')
        
        if action in ['send_message', 'send_template'] and not phone_number:
            self.logger.error("Phone number is required for messaging operations")
            return False
        
        if action == 'send_message' and not message:
            self.logger.error("Message content is required")
            return False
        
        # Validate phone number format
        if phone_number and not phone_number.startswith('+'):
            self.logger.error("Phone number must include country code with + prefix")
            return False
        
        return True
    
    def _format_phone_number(self, phone: str) -> str:
        """Format phone number for WhatsApp API."""
        # Remove + and any spaces or special characters
        clean_phone = ''.join(c for c in phone if c.isdigit())
        return clean_phone
    
    async def _send_text_message(self, to: str, message: str, preview_url: bool = False) -> Dict[str, Any]:
        """Send a text message via WhatsApp."""
        payload = {
            "messaging_product": "whatsapp",
            "to": self._format_phone_number(to),
            "type": "text",
            "text": {
                "body": message,
                "preview_url": preview_url
            }
        }
        
        response = await self.client.post(f"/{self.phone_number_id}/messages", json=payload)
        response.raise_for_status()
        
        result = response.json()
        self.logger.log_whatsapp_message(to, "text_message", True)
        
        return result
    
    async def _send_template_message(self, to: str, template_name: str, language: str = "ar", 
                                   parameters: List[str] = None) -> Dict[str, Any]:
        """Send a template message via WhatsApp."""
        template_payload = {
            "name": template_name,
            "language": {"code": language}
        }
        
        if parameters:
            template_payload["components"] = [{
                "type": "body",
                "parameters": [{"type": "text", "text": param} for param in parameters]
            }]
        
        payload = {
            "messaging_product": "whatsapp",
            "to": self._format_phone_number(to),
            "type": "template",
            "template": template_payload
        }
        
        response = await self.client.post(f"/{self.phone_number_id}/messages", json=payload)
        response.raise_for_status()
        
        result = response.json()
        self.logger.log_whatsapp_message(to, f"template:{template_name}", True)
        
        return result
    
    async def _send_interactive_message(self, to: str, header: str, body: str, 
                                      buttons: List[Dict]) -> Dict[str, Any]:
        """Send an interactive message with buttons."""
        interactive_payload = {
            "type": "button",
            "header": {"type": "text", "text": header},
            "body": {"text": body},
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": btn.get("id", f"btn_{i}"),
                            "title": btn["title"]
                        }
                    } for i, btn in enumerate(buttons)
                ]
            }
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": self._format_phone_number(to),
            "type": "interactive",
            "interactive": interactive_payload
        }
        
        response = await self.client.post(f"/{self.phone_number_id}/messages", json=payload)
        response.raise_for_status()
        
        result = response.json()
        self.logger.log_whatsapp_message(to, "interactive_message", True)
        
        return result
    
    async def _mark_message_read(self, message_id: str) -> Dict[str, Any]:
        """Mark a message as read."""
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        response = await self.client.post(f"/{self.phone_number_id}/messages", json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def _execute(self, **kwargs) -> Dict[str, Any]:
        """Execute WhatsApp operation."""
        import asyncio
        
        try:
            action = kwargs.get('action', 'send_message')
            
            if action == 'send_message':
                result = asyncio.run(self._send_text_message(
                    to=kwargs['phone_number'],
                    message=kwargs['message'],
                    preview_url=kwargs.get('preview_url', False)
                ))
                
            elif action == 'send_template':
                result = asyncio.run(self._send_template_message(
                    to=kwargs['phone_number'],
                    template_name=kwargs['template_name'],
                    language=kwargs.get('language', 'ar'),
                    parameters=kwargs.get('parameters', [])
                ))
                
            elif action == 'send_interactive':
                result = asyncio.run(self._send_interactive_message(
                    to=kwargs['phone_number'],
                    header=kwargs['header'],
                    body=kwargs['body'],
                    buttons=kwargs['buttons']
                ))
                
            elif action == 'mark_read':
                result = asyncio.run(self._mark_message_read(kwargs['message_id']))
                
            else:
                raise ValueError(f"Unknown action: {action}")
            
            return ToolResult(
                success=True,
                data=result,
                metadata={
                    "action": action,
                    "phone_number": kwargs.get('phone_number'),
                    "message_id": result.get('messages', [{}])[0].get('id')
                }
            ).dict()
            
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else str(e)
            self.logger.log_whatsapp_message(
                kwargs.get('phone_number', 'unknown'), 
                action, 
                False
            )
            
            return ToolResult(
                success=False,
                error=f"WhatsApp API error: {error_detail}",
                metadata={"status_code": e.response.status_code if e.response else None}
            ).dict()
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"WhatsApp operation failed: {str(e)}",
                metadata={"action": action}
            ).dict()
    
    def send_message(self, phone_number: str, message: str, preview_url: bool = False) -> Dict[str, Any]:
        """Simple interface to send a text message."""
        return self.run(
            action='send_message',
            phone_number=phone_number,
            message=message,
            preview_url=preview_url
        )
    
    def send_template(self, phone_number: str, template_name: str, 
                     language: str = "ar", parameters: List[str] = None) -> Dict[str, Any]:
        """Simple interface to send a template message."""
        return self.run(
            action='send_template',
            phone_number=phone_number,
            template_name=template_name,
            language=language,
            parameters=parameters or []
        )
    
    def send_feedback_request(self, phone_number: str, customer_name: str, 
                            restaurant_name: str, language: str = "ar") -> Dict[str, Any]:
        """Send a feedback request message with interactive buttons."""
        if language == "ar":
            header = f"مرحباً {customer_name}"
            body = f"نشكرك لزيارة {restaurant_name}. نرجو تقييم تجربتك معنا"
            buttons = [
                {"id": "excellent", "title": "ممتاز 😊"},
                {"id": "good", "title": "جيد 👍"},
                {"id": "poor", "title": "ضعيف 😞"}
            ]
        else:
            header = f"Hello {customer_name}"
            body = f"Thank you for visiting {restaurant_name}. Please rate your experience"
            buttons = [
                {"id": "excellent", "title": "Excellent 😊"},
                {"id": "good", "title": "Good 👍"},
                {"id": "poor", "title": "Poor 😞"}
            ]
        
        return self.run(
            action='send_interactive',
            phone_number=phone_number,
            header=header,
            body=body,
            buttons=buttons
        )
    
    def __del__(self):
        """Clean up the HTTP client."""
        try:
            import asyncio
            asyncio.run(self.client.aclose())
        except:
            pass