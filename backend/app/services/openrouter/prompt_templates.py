"""
Prompt Template Engine for OpenRouter service.
Provides templating system for different restaurant AI scenarios.
"""

import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import json

from .types import ChatMessage, ConversationContext, Language, MessageRole

logger = logging.getLogger(__name__)


class TemplateCategory(str, Enum):
    """Template categories for different use cases."""
    GREETING = "greeting"
    MENU_INQUIRY = "menu_inquiry"
    RESERVATION = "reservation"
    ORDER_TAKING = "order_taking"
    COMPLAINT_HANDLING = "complaint_handling"
    FEEDBACK_REQUEST = "feedback_request"
    CONVERSATION_SUMMARY = "conversation_summary"
    CULTURAL_GUIDANCE = "cultural_guidance"
    CLOSING = "closing"
    GENERAL_ASSISTANCE = "general_assistance"


@dataclass
class PromptTemplate:
    """Prompt template definition."""
    id: str
    category: TemplateCategory
    name: str
    description: str
    system_prompt: str
    user_prompt_template: Optional[str] = None
    variables: List[str] = None
    languages: List[Language] = None
    cultural_context: Optional[str] = None
    examples: List[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = []
        if self.languages is None:
            self.languages = [Language.ENGLISH, Language.ARABIC]
        if self.examples is None:
            self.examples = []


class PromptTemplateEngine:
    """
    Prompt template engine for restaurant AI scenarios.
    
    Features:
    - Multi-language template support
    - Variable substitution
    - Cultural context adaptation
    - Dynamic template selection
    - Performance optimization
    """
    
    def __init__(self):
        """Initialize the prompt template engine."""
        self.templates: Dict[str, PromptTemplate] = {}
        self.template_usage_stats: Dict[str, int] = {}
        
        self._initialize_default_templates()
        logger.info("Prompt template engine initialized")
    
    def _initialize_default_templates(self):
        """Initialize default prompt templates."""
        default_templates = [
            # Greeting Templates
            PromptTemplate(
                id="friendly_greeting",
                category=TemplateCategory.GREETING,
                name="Friendly Restaurant Greeting",
                description="Warm, welcoming greeting for restaurant customers",
                system_prompt="""أنت مساعد ذكي ودود لمطعم راقي. تحدث بطريقة مهذبة ومرحبة.
استخدم التحيات المناسبة ثقافياً واعرض المساعدة بحماس.
إذا كان العميل يتحدث العربية، استخدم العبارات التقليدية للضيافة العربية.

You are a friendly and professional restaurant AI assistant. Speak warmly and welcomingly.
Use culturally appropriate greetings and offer assistance enthusiastically.
If the customer speaks Arabic, use traditional Arabic hospitality expressions.""",
                variables=["restaurant_name", "time_of_day", "special_offers"],
                examples=[
                    {
                        "input": "مرحبا",
                        "output": "أهلاً وسهلاً بك في مطعم {restaurant_name}! نورت المكان. كيف يمكنني مساعدتك اليوم؟"
                    },
                    {
                        "input": "Hello",
                        "output": "Welcome to {restaurant_name}! We're delighted to have you. How can I assist you today?"
                    }
                ]
            ),
            
            # Menu Inquiry Templates
            PromptTemplate(
                id="menu_assistance",
                category=TemplateCategory.MENU_INQUIRY,
                name="Menu Information Assistant",
                description="Help customers with menu inquiries and recommendations",
                system_prompt="""أنت خبير في قائمة الطعام ومساعد مطعم محترف. 
اعرض الأطباق بطريقة شهية ووصف مكوناتها بوضوح.
قدم توصيات شخصية بناءً على تفضيلات العميل.
كن حساساً للقيود الغذائية والتفضيلات الثقافية.

You are a knowledgeable menu expert and professional restaurant assistant.
Present dishes appetizingly and describe ingredients clearly.
Provide personalized recommendations based on customer preferences.
Be sensitive to dietary restrictions and cultural preferences.""",
                variables=["menu_items", "daily_specials", "dietary_options", "price_range"],
                examples=[
                    {
                        "input": "شو عندكم أكلات عربية؟",
                        "output": "عندنا تشكيلة رائعة من الأكلات العربية الأصيلة! نرشح لك {daily_specials} والكبسة اللذيذة مع اللحم الطري."
                    }
                ]
            ),
            
            # Reservation Templates
            PromptTemplate(
                id="reservation_handling",
                category=TemplateCategory.RESERVATION,
                name="Reservation Management",
                description="Handle table reservations professionally",
                system_prompt="""أنت متخصص في حجوزات المطعم ومساعد محترف.
اجمع المعلومات المطلوبة للحجز: التاريخ، الوقت، عدد الأشخاص، المناسبة الخاصة.
تأكد من الأوقات المتاحة وقدم بدائل مناسبة.
كن مرناً ومتفهماً لاحتياجات العملاء الخاصة.

You are a professional reservation specialist and assistant.
Collect required booking information: date, time, party size, special occasions.
Confirm availability and offer suitable alternatives.
Be flexible and understanding of special customer needs.""",
                variables=["available_times", "table_capacity", "special_events", "contact_info"],
                examples=[
                    {
                        "input": "أبي أحجز طاولة لـ 6 أشخاص الجمعة",
                        "output": "ممتاز! حجز لـ 6 أشخاص يوم الجمعة. في أي وقت تفضلون؟ عندنا مواعيد متاحة {available_times}."
                    }
                ]
            ),
            
            # Order Taking Templates
            PromptTemplate(
                id="order_processing",
                category=TemplateCategory.ORDER_TAKING,
                name="Order Taking Assistant",
                description="Process customer orders efficiently and accurately",
                system_prompt="""أنت متخصص في استقبال الطلبات ومساعد مطعم دقيق.
سجل الطلبات بعناية واطلب التوضيحات عند الحاجة.
تأكد من تفضيلات الطبخ والإضافات الخاصة.
احسب التكلفة الإجمالية واعرض ملخص الطلب قبل التأكيد.

You are an order specialist and precise restaurant assistant.
Record orders carefully and ask for clarifications when needed.
Confirm cooking preferences and special additions.
Calculate total cost and provide order summary before confirmation.""",
                variables=["menu_items", "prices", "cooking_options", "add_ons", "delivery_info"],
                examples=[
                    {
                        "input": "أبي برجر لحم وسط مع بطاطس",
                        "output": "برجر لحم وسط مع بطاطس، ممتاز! تبيه مع أي إضافات خاصة؟ جبنة إضافية أو صوص معين؟"
                    }
                ]
            ),
            
            # Complaint Handling Templates
            PromptTemplate(
                id="complaint_resolution",
                category=TemplateCategory.COMPLAINT_HANDLING,
                name="Professional Complaint Handler",
                description="Handle customer complaints with empathy and professionalism",
                system_prompt="""أنت متخصص في حل الشكاوى ومساعد مطعم متفهم.
استمع بتعاطف واعترف بمشاعر العميل.
اعتذر بصدق واعرض حلول عملية فورية.
تابع مع العميل للتأكد من رضاه التام.

You are a complaint resolution specialist and empathetic restaurant assistant.
Listen with empathy and acknowledge customer feelings.
Apologize sincerely and offer practical immediate solutions.
Follow up with the customer to ensure complete satisfaction.""",
                variables=["issue_type", "compensation_options", "manager_contact", "follow_up_timeline"],
                examples=[
                    {
                        "input": "الأكل وصل بارد والطعم مو حلو",
                        "output": "أعتذر بشدة على هذه التجربة السيئة. هذا ليس مستوانا المعتاد. سأطلب من الشيف تحضير طبق جديد فوراً وساخن، أو يمكنني استرداد المبلغ كاملاً."
                    }
                ]
            ),
            
            # Feedback Request Templates
            PromptTemplate(
                id="feedback_collection",
                category=TemplateCategory.FEEDBACK_REQUEST,
                name="Feedback Collection Assistant",
                description="Collect customer feedback professionally and encouragingly",
                system_prompt="""أنت متخصص في جمع التعليقات ومساعد مطعم محفز.
اطلب الملاحظات بطريقة ودودة وغير مُلحة.
اشكر العملاء على وقتهم وآرائهم القيمة.
اطرح أسئلة محددة عن جوانب مختلفة من التجربة.

You are a feedback collection specialist and encouraging restaurant assistant.
Request feedback in a friendly and non-pushy manner.
Thank customers for their time and valuable opinions.
Ask specific questions about different aspects of their experience.""",
                variables=["experience_aspects", "rating_scale", "incentives", "contact_options"],
                examples=[
                    {
                        "input": "الأكل كان حلو شكراً",
                        "output": "يسعدنا أن الطعام عجبك! ممكن تقييمك للخدمة والأجواء؟ رأيك مهم جداً لنا لنطور من أنفسنا أكثر."
                    }
                ]
            ),
            
            # Cultural Guidance Templates  
            PromptTemplate(
                id="arabic_cultural_context",
                category=TemplateCategory.CULTURAL_GUIDANCE,
                name="Arabic Cultural Context Provider",
                description="Provide cultural context for Arabic-speaking customers",
                system_prompt="""أنت مساعد مطعم خبير بالثقافة العربية والضيافة الأصيلة.
استخدم العبارات التقليدية والتعابير المناسبة ثقافياً.
كن حساساً للمناسبات الدينية والاجتماعية.
اظهر الاحترام للتقاليد والقيم العربية في التعامل.

You are a restaurant assistant expert in Arabic culture and authentic hospitality.
Use traditional expressions and culturally appropriate phrases.
Be sensitive to religious and social occasions.
Show respect for Arab traditions and values in interactions.""",
                variables=["cultural_occasion", "time_context", "religious_considerations"],
                cultural_context="arabic_hospitality"
            ),
            
            # Conversation Summary Templates
            PromptTemplate(
                id="conversation_summary",
                category=TemplateCategory.CONVERSATION_SUMMARY,
                name="Conversation Summarizer",
                description="Summarize customer conversations concisely",
                system_prompt="""لخص المحادثة التالية بإيجاز واذكر النقاط المهمة:
- طلبات العميل أو استفساراته
- المشاكل المطروحة والحلول المقدمة  
- متطلبات المتابعة
- مستوى رضا العميل

Summarize the following conversation concisely, highlighting:
- Customer requests or inquiries
- Issues raised and solutions provided
- Follow-up requirements  
- Customer satisfaction level""",
                variables=["conversation_length", "key_topics", "action_items"]
            ),
            
            # General Assistance Templates
            PromptTemplate(
                id="general_help",
                category=TemplateCategory.GENERAL_ASSISTANCE,
                name="General Restaurant Assistant",
                description="Provide general assistance and information",
                system_prompt="""أنت مساعد مطعم شامل وودود. تستطيع مساعدة العملاء في:
- معلومات عن القائمة والأسعار
- الحجوزات والمواعيد
- ساعات العمل والموقع
- العروض الخاصة والفعاليات
- أي استفسارات عامة أخرى

كن مفيداً ومتعاوناً دائماً.

You are a comprehensive and friendly restaurant assistant. You can help customers with:
- Menu information and prices
- Reservations and appointments  
- Opening hours and location
- Special offers and events
- Any other general inquiries

Always be helpful and cooperative.""",
                variables=["restaurant_info", "current_offers", "contact_details", "operating_hours"]
            )
        ]
        
        # Store templates
        for template in default_templates:
            self.templates[template.id] = template
    
    async def apply_template(
        self,
        template_id: str,
        messages: List[ChatMessage],
        context: ConversationContext,
        **variables
    ) -> List[ChatMessage]:
        """
        Apply a template to enhance messages.
        
        Args:
            template_id: ID of template to apply
            messages: List of messages to enhance
            context: Conversation context
            **variables: Template variables to substitute
            
        Returns:
            Enhanced messages with template applied
        """
        if template_id not in self.templates:
            logger.warning(f"Template {template_id} not found")
            return messages
        
        template = self.templates[template_id]
        
        # Track template usage
        self.template_usage_stats[template_id] = self.template_usage_stats.get(template_id, 0) + 1
        
        # Prepare template variables
        template_vars = await self._prepare_variables(template, context, variables)
        
        # Apply template
        enhanced_messages = await self._apply_template_to_messages(
            template, messages, context, template_vars
        )
        
        logger.debug(f"Applied template {template_id} to {len(messages)} messages")
        return enhanced_messages
    
    async def _prepare_variables(
        self,
        template: PromptTemplate,
        context: ConversationContext,
        provided_vars: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare variables for template substitution."""
        variables = provided_vars.copy()
        
        # Add default context variables
        variables.update({
            "user_id": context.user_id,
            "session_id": context.session_id,
            "language": context.language,
            "current_time": datetime.utcnow().isoformat(),
            "conversation_length": len(context.message_history)
        })
        
        # Add restaurant-specific defaults
        if "restaurant_name" not in variables:
            variables["restaurant_name"] = "مطعمنا المميز"  # "Our Special Restaurant"
        
        # Time-based variables
        hour = datetime.utcnow().hour
        if "time_of_day" not in variables:
            if 5 <= hour <= 11:
                variables["time_of_day"] = "morning" if context.language == Language.ENGLISH else "صباح"
            elif 12 <= hour <= 17:
                variables["time_of_day"] = "afternoon" if context.language == Language.ENGLISH else "بعد الظهر"
            else:
                variables["time_of_day"] = "evening" if context.language == Language.ENGLISH else "مساء"
        
        # Cultural context variables
        if context.language == Language.ARABIC:
            variables.update({
                "greeting": "أهلاً وسهلاً",
                "thanks": "شكراً لك",
                "please": "لو سمحت",
                "welcome": "مرحب فيك"
            })
        else:
            variables.update({
                "greeting": "Welcome",
                "thanks": "Thank you",
                "please": "Please",
                "welcome": "Welcome"
            })
        
        return variables
    
    async def _apply_template_to_messages(
        self,
        template: PromptTemplate,
        messages: List[ChatMessage],
        context: ConversationContext,
        variables: Dict[str, Any]
    ) -> List[ChatMessage]:
        """Apply template to messages."""
        enhanced_messages = []
        
        # Add system message from template if not already present
        has_system_message = any(msg.role == MessageRole.SYSTEM for msg in messages)
        
        if not has_system_message and template.system_prompt:
            system_content = self._substitute_variables(template.system_prompt, variables)
            system_message = ChatMessage(
                role=MessageRole.SYSTEM,
                content=system_content
            )
            enhanced_messages.append(system_message)
        
        # Process existing messages
        for message in messages:
            enhanced_message = await self._enhance_message_with_template(
                message, template, variables, context
            )
            enhanced_messages.append(enhanced_message)
        
        # Add template-specific user prompt if provided
        if template.user_prompt_template and messages:
            user_prompt = self._substitute_variables(template.user_prompt_template, variables)
            if user_prompt.strip():
                prompt_message = ChatMessage(
                    role=MessageRole.USER,
                    content=user_prompt
                )
                enhanced_messages.append(prompt_message)
        
        return enhanced_messages
    
    async def _enhance_message_with_template(
        self,
        message: ChatMessage,
        template: PromptTemplate,
        variables: Dict[str, Any],
        context: ConversationContext
    ) -> ChatMessage:
        """Enhance a single message with template context."""
        # For now, return message as-is
        # In more advanced implementations, you might:
        # - Add context-specific prefixes/suffixes
        # - Adjust tone based on template category
        # - Add template-specific metadata
        
        return message
    
    def _substitute_variables(self, text: str, variables: Dict[str, Any]) -> str:
        """Substitute template variables in text."""
        if not text:
            return text
        
        result = text
        for key, value in variables.items():
            placeholder = "{" + key + "}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))
        
        return result
    
    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """Get a template by ID."""
        return self.templates.get(template_id)
    
    def list_templates(
        self,
        category: Optional[TemplateCategory] = None,
        language: Optional[Language] = None
    ) -> List[PromptTemplate]:
        """List available templates, optionally filtered."""
        templates = list(self.templates.values())
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        if language:
            templates = [t for t in templates if language in t.languages]
        
        return templates
    
    def add_template(self, template: PromptTemplate) -> bool:
        """Add a new template."""
        try:
            self.templates[template.id] = template
            logger.info(f"Added template: {template.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add template {template.id}: {str(e)}")
            return False
    
    def update_template(self, template_id: str, template: PromptTemplate) -> bool:
        """Update an existing template."""
        if template_id not in self.templates:
            return False
        
        try:
            self.templates[template_id] = template
            logger.info(f"Updated template: {template_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update template {template_id}: {str(e)}")
            return False
    
    def remove_template(self, template_id: str) -> bool:
        """Remove a template."""
        if template_id in self.templates:
            del self.templates[template_id]
            logger.info(f"Removed template: {template_id}")
            return True
        return False
    
    async def suggest_template(
        self,
        messages: List[ChatMessage],
        context: ConversationContext
    ) -> Optional[str]:
        """Suggest appropriate template based on conversation context."""
        if not messages:
            return "friendly_greeting"
        
        latest_message = messages[-1]
        content_lower = latest_message.content.lower() if latest_message.content else ""
        
        # Simple keyword-based suggestion
        if any(word in content_lower for word in ["مرحبا", "hello", "hi", "سلام"]):
            return "friendly_greeting"
        
        elif any(word in content_lower for word in ["قائمة", "menu", "أكل", "food", "طبق", "dish"]):
            return "menu_assistance"
        
        elif any(word in content_lower for word in ["حجز", "reservation", "طاولة", "table", "موعد"]):
            return "reservation_handling"
        
        elif any(word in content_lower for word in ["طلب", "order", "أطلب", "أبي"]):
            return "order_processing"
        
        elif any(word in content_lower for word in ["شكوى", "مشكلة", "complaint", "problem", "سيء", "bad"]):
            return "complaint_resolution"
        
        elif any(word in content_lower for word in ["رأي", "تقييم", "feedback", "review"]):
            return "feedback_collection"
        
        else:
            return "general_help"
    
    def get_template_statistics(self) -> Dict[str, Any]:
        """Get template usage statistics."""
        total_usage = sum(self.template_usage_stats.values())
        
        stats = {
            "total_templates": len(self.templates),
            "total_usage": total_usage,
            "usage_by_template": self.template_usage_stats.copy(),
            "usage_by_category": {},
            "most_used_templates": []
        }
        
        # Usage by category
        for template_id, usage_count in self.template_usage_stats.items():
            if template_id in self.templates:
                category = self.templates[template_id].category
                stats["usage_by_category"][category] = stats["usage_by_category"].get(category, 0) + usage_count
        
        # Most used templates
        sorted_usage = sorted(
            self.template_usage_stats.items(),
            key=lambda x: x[1],
            reverse=True
        )
        stats["most_used_templates"] = [
            {"template_id": tid, "usage_count": count, "percentage": (count/total_usage*100) if total_usage > 0 else 0}
            for tid, count in sorted_usage[:5]
        ]
        
        return stats
    
    async def validate_template(self, template: PromptTemplate) -> List[str]:
        """Validate a template and return any issues found."""
        issues = []
        
        # Required fields
        if not template.id:
            issues.append("Template ID is required")
        if not template.name:
            issues.append("Template name is required")
        if not template.system_prompt:
            issues.append("System prompt is required")
        
        # Variable validation
        if template.variables:
            # Check if variables in system_prompt exist
            system_vars = set()
            import re
            for match in re.finditer(r'\{(\w+)\}', template.system_prompt):
                system_vars.add(match.group(1))
            
            missing_vars = system_vars - set(template.variables)
            if missing_vars:
                issues.append(f"Variables used in system prompt but not declared: {missing_vars}")
        
        # Language validation
        if not template.languages:
            issues.append("At least one language must be specified")
        
        return issues
    
    async def export_templates(self, template_ids: Optional[List[str]] = None) -> str:
        """Export templates as JSON."""
        templates_to_export = {}
        
        if template_ids:
            for tid in template_ids:
                if tid in self.templates:
                    templates_to_export[tid] = self.templates[tid]
        else:
            templates_to_export = self.templates
        
        # Convert to serializable format
        export_data = {}
        for tid, template in templates_to_export.items():
            export_data[tid] = {
                "id": template.id,
                "category": template.category,
                "name": template.name,
                "description": template.description,
                "system_prompt": template.system_prompt,
                "user_prompt_template": template.user_prompt_template,
                "variables": template.variables,
                "languages": template.languages,
                "cultural_context": template.cultural_context,
                "examples": template.examples
            }
        
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    async def import_templates(self, json_data: str) -> Tuple[int, List[str]]:
        """Import templates from JSON. Returns (success_count, error_list)."""
        try:
            data = json.loads(json_data)
            success_count = 0
            errors = []
            
            for tid, template_data in data.items():
                try:
                    template = PromptTemplate(
                        id=template_data["id"],
                        category=TemplateCategory(template_data["category"]),
                        name=template_data["name"],
                        description=template_data["description"],
                        system_prompt=template_data["system_prompt"],
                        user_prompt_template=template_data.get("user_prompt_template"),
                        variables=template_data.get("variables", []),
                        languages=[Language(lang) for lang in template_data.get("languages", ["en", "ar"])],
                        cultural_context=template_data.get("cultural_context"),
                        examples=template_data.get("examples", [])
                    )
                    
                    # Validate template
                    validation_issues = await self.validate_template(template)
                    if validation_issues:
                        errors.append(f"Template {tid}: {'; '.join(validation_issues)}")
                        continue
                    
                    # Add template
                    self.templates[tid] = template
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f"Template {tid}: {str(e)}")
            
            return success_count, errors
            
        except json.JSONDecodeError as e:
            return 0, [f"Invalid JSON: {str(e)}"]