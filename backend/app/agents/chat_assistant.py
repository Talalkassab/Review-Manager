"""
Chat Assistant Agent - Handles dashboard interactions, natural language queries,
and provides intelligent assistance to restaurant staff through conversational interface.
"""

from crewai import Agent
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime, timedelta
import json
import re

from ..tools.database_tool import DatabaseTool
from ..tools.analytics_tool import AnalyticsTool
from ..tools.text_processing_tool import TextProcessingTool
from .base_agent import BaseRestaurantAgent


class ChatAssistantAgent(BaseRestaurantAgent):
    """
    Intelligent chat assistant that helps restaurant staff interact with the system
    through natural language, provides insights, and executes actions on their behalf.
    """
    
    def __init__(self):
        # Initialize tools
        self.db_tool = DatabaseTool()
        self.analytics_tool = AnalyticsTool()
        self.text_tool = TextProcessingTool()
        
        # Conversation context memory
        self.conversation_context = {}
        self.user_preferences = {}
        
        super().__init__(
            role="Intelligent Chat Assistant",
            goal="Help restaurant staff through natural language interaction and intelligent assistance",
            backstory="""You are an intelligent chat assistant specialized in helping 
            restaurant owners and managers interact with their customer engagement system. 
            You understand both Arabic and English, and can process natural language 
            queries about customer data, campaign performance, and business insights.
            
            Your expertise includes understanding restaurant operations, customer service 
            workflows, Arabic business terminology, and cultural nuances in customer 
            interactions. You can help users find information, create campaigns, 
            analyze performance, and make data-driven decisions through simple conversation.
            
            You are friendly, helpful, and culturally aware, adapting your communication 
            style to match the user's language preference and cultural context.""",
            tools=[self.db_tool, self.analytics_tool, self.text_tool],
            allow_delegation=False,
            verbose=True
        )
    
    async def process_user_query(
        self, 
        user_id: str,
        query: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process natural language query from restaurant staff"""
        try:
            # Detect language
            language = await self._detect_query_language(query)
            
            # Get conversation context
            context = await self._get_conversation_context(user_id, conversation_id)
            
            # Parse and understand the query
            query_intent = await self._parse_query_intent(query, language, context)
            
            # Execute the appropriate action
            response = await self._execute_query_action(query_intent, user_id, context)
            
            # Update conversation context
            await self._update_conversation_context(
                user_id, conversation_id, query, response, query_intent
            )
            
            # Format response for user
            formatted_response = await self._format_response(response, language, query_intent)
            
            chat_response = {
                "conversation_id": conversation_id or f"conv_{datetime.now().timestamp()}",
                "user_id": user_id,
                "query": query,
                "language": language,
                "intent": query_intent,
                "response": formatted_response,
                "timestamp": datetime.now().isoformat(),
                "actions_taken": response.get("actions", []),
                "suggested_follow_ups": await self._generate_follow_up_suggestions(query_intent, response, language)
            }
            
            # Store conversation
            await self.db_tool.store_chat_interaction(user_id, chat_response)
            
            await self._log_metric("chat_query_processed", {
                "user_id": user_id,
                "language": language,
                "intent": query_intent.get("type", "unknown")
            })
            
            return chat_response
            
        except Exception as e:
            await self._log_error("chat_query_processing", str(e))
            return {
                "error": True,
                "message": "عذراً، حدث خطأ في معالجة طلبك - Sorry, there was an error processing your request",
                "timestamp": datetime.now().isoformat()
            }
    
    async def provide_business_insights(
        self, 
        user_id: str, 
        insight_type: str = "daily_summary"
    ) -> Dict[str, Any]:
        """Provide intelligent business insights and recommendations"""
        try:
            # Get user's restaurant data
            restaurant_data = await self.db_tool.get_user_restaurant_data(user_id)
            
            if not restaurant_data:
                return {"error": "Restaurant data not found"}
            
            restaurant_id = restaurant_data["restaurant_id"]
            
            # Generate insights based on type
            if insight_type == "daily_summary":
                insights = await self._generate_daily_summary(restaurant_id)
            elif insight_type == "customer_insights":
                insights = await self._generate_customer_insights(restaurant_id)
            elif insight_type == "campaign_performance":
                insights = await self._generate_campaign_insights(restaurant_id)
            elif insight_type == "optimization_suggestions":
                insights = await self._generate_optimization_suggestions(restaurant_id)
            else:
                insights = await self._generate_comprehensive_insights(restaurant_id)
            
            # Add conversational context
            insights_response = {
                "user_id": user_id,
                "restaurant_id": restaurant_id,
                "insight_type": insight_type,
                "insights": insights,
                "generated_at": datetime.now().isoformat(),
                "language_preference": await self._get_user_language_preference(user_id)
            }
            
            await self._log_metric("business_insights_provided", {
                "user_id": user_id,
                "insight_type": insight_type
            })
            
            return insights_response
            
        except Exception as e:
            await self._log_error("business_insights", str(e))
            return {"error": f"Insights generation failed: {str(e)}"}
    
    async def execute_quick_action(
        self, 
        user_id: str,
        action_type: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute quick actions requested through chat"""
        try:
            result = {}
            
            if action_type == "send_campaign":
                result = await self._execute_send_campaign(user_id, parameters)
            elif action_type == "add_customer":
                result = await self._execute_add_customer(user_id, parameters)
            elif action_type == "generate_report":
                result = await self._execute_generate_report(user_id, parameters)
            elif action_type == "update_settings":
                result = await self._execute_update_settings(user_id, parameters)
            elif action_type == "schedule_campaign":
                result = await self._execute_schedule_campaign(user_id, parameters)
            else:
                return {"error": f"Unknown action type: {action_type}"}
            
            action_response = {
                "user_id": user_id,
                "action_type": action_type,
                "parameters": parameters,
                "result": result,
                "executed_at": datetime.now().isoformat(),
                "success": result.get("success", False)
            }
            
            # Store action execution
            await self.db_tool.store_quick_action(user_id, action_response)
            
            await self._log_metric("quick_action_executed", {
                "user_id": user_id,
                "action_type": action_type,
                "success": result.get("success", False)
            })
            
            return action_response
            
        except Exception as e:
            await self._log_error("quick_action_execution", str(e))
            return {"error": f"Action execution failed: {str(e)}"}
    
    async def _detect_query_language(self, query: str) -> str:
        """Detect the language of user query"""
        try:
            # Check for Arabic characters
            arabic_chars = re.findall(r'[\u0600-\u06FF]', query)
            english_chars = re.findall(r'[a-zA-Z]', query)
            
            if len(arabic_chars) > len(english_chars):
                return "arabic"
            elif len(english_chars) > 0:
                return "english"
            else:
                return "mixed"
                
        except Exception:
            return "english"  # Default fallback
    
    async def _parse_query_intent(
        self, 
        query: str, 
        language: str, 
        context: Dict
    ) -> Dict[str, Any]:
        """Parse user query to understand intent and extract parameters"""
        try:
            query_lower = query.lower()
            
            # Define intent patterns for Arabic
            arabic_patterns = {
                "show_customers": ["أظهر العملاء", "اعرض العملاء", "قائمة العملاء", "العملاء اللي"],
                "campaign_performance": ["أداء الحملة", "نتائج الحملة", "إحصائيات الحملة"],
                "daily_summary": ["ملخص اليوم", "تقرير يومي", "إحصائيات اليوم"],
                "send_message": ["أرسل رسالة", "إرسال", "راسل"],
                "customer_feedback": ["آراء العملاء", "تقييمات", "ردود الأفعال"],
                "add_customer": ["أضف عميل", "عميل جديد", "إضافة عميل"]
            }
            
            # Define intent patterns for English  
            english_patterns = {
                "show_customers": ["show customers", "list customers", "customer list", "customers who"],
                "campaign_performance": ["campaign performance", "campaign results", "campaign stats"],
                "daily_summary": ["daily summary", "daily report", "today's stats"],
                "send_message": ["send message", "send", "message"],
                "customer_feedback": ["customer feedback", "reviews", "ratings"],
                "add_customer": ["add customer", "new customer", "create customer"]
            }
            
            # Detect intent based on language
            patterns = arabic_patterns if language == "arabic" else english_patterns
            
            detected_intent = "general_query"
            confidence = 0.5
            parameters = {}
            
            for intent, pattern_list in patterns.items():
                for pattern in pattern_list:
                    if pattern in query_lower:
                        detected_intent = intent
                        confidence = 0.9
                        break
                if confidence > 0.8:
                    break
            
            # Extract parameters based on intent
            if detected_intent == "show_customers":
                parameters = await self._extract_customer_filter_params(query, language)
            elif detected_intent == "campaign_performance":
                parameters = await self._extract_campaign_params(query, language)
            elif detected_intent == "send_message":
                parameters = await self._extract_message_params(query, language)
            
            return {
                "type": detected_intent,
                "confidence": confidence,
                "parameters": parameters,
                "original_query": query,
                "language": language
            }
            
        except Exception as e:
            await self._log_error("query_intent_parsing", str(e))
            return {"type": "general_query", "confidence": 0.3, "parameters": {}}
    
    async def _execute_query_action(
        self, 
        query_intent: Dict, 
        user_id: str, 
        context: Dict
    ) -> Dict[str, Any]:
        """Execute the action based on parsed query intent"""
        try:
            intent_type = query_intent["type"]
            parameters = query_intent["parameters"]
            
            if intent_type == "show_customers":
                return await self._handle_show_customers(user_id, parameters)
            elif intent_type == "campaign_performance":
                return await self._handle_campaign_performance(user_id, parameters)
            elif intent_type == "daily_summary":
                return await self._handle_daily_summary(user_id)
            elif intent_type == "send_message":
                return await self._handle_send_message(user_id, parameters)
            elif intent_type == "customer_feedback":
                return await self._handle_customer_feedback(user_id, parameters)
            elif intent_type == "add_customer":
                return await self._handle_add_customer(user_id, parameters)
            else:
                return await self._handle_general_query(user_id, query_intent)
                
        except Exception as e:
            await self._log_error("query_action_execution", str(e))
            return {"error": f"Action execution failed: {str(e)}"}
    
    async def _handle_show_customers(self, user_id: str, parameters: Dict) -> Dict[str, Any]:
        """Handle showing customers based on filters"""
        try:
            # Get restaurant ID
            restaurant_data = await self.db_tool.get_user_restaurant_data(user_id)
            restaurant_id = restaurant_data["restaurant_id"]
            
            # Apply filters from parameters
            filters = {
                "restaurant_id": restaurant_id,
                "language_preference": parameters.get("language"),
                "feedback_status": parameters.get("feedback_status"),
                "last_interaction_days": parameters.get("days_filter", 30)
            }
            
            # Get filtered customers
            customers = await self.db_tool.get_customers_with_filters(filters)
            
            # Format customer data for display
            customer_summaries = []
            for customer in customers[:20]:  # Limit to 20 for chat display
                summary = {
                    "name": customer.get("name"),
                    "phone": customer.get("phone", "").replace(customer.get("phone", "")[4:8], "****"),  # Mask phone
                    "language": customer.get("language_preference", "Arabic"),
                    "last_interaction": customer.get("last_interaction_date"),
                    "feedback_status": customer.get("latest_feedback_sentiment", "neutral"),
                    "visit_count": customer.get("visit_count", 0)
                }
                customer_summaries.append(summary)
            
            return {
                "success": True,
                "data_type": "customers",
                "customers": customer_summaries,
                "total_count": len(customers),
                "showing_count": len(customer_summaries),
                "filters_applied": parameters,
                "actions": ["show_customers"]
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to retrieve customers: {str(e)}"}
    
    async def _handle_campaign_performance(self, user_id: str, parameters: Dict) -> Dict[str, Any]:
        """Handle campaign performance queries"""
        try:
            restaurant_data = await self.db_tool.get_user_restaurant_data(user_id)
            restaurant_id = restaurant_data["restaurant_id"]
            
            # Get recent campaigns if no specific campaign mentioned
            campaign_id = parameters.get("campaign_id")
            
            if campaign_id:
                campaign_metrics = await self.db_tool.get_campaign_metrics(campaign_id)
            else:
                # Get most recent campaign
                recent_campaigns = await self.db_tool.get_recent_campaigns(restaurant_id, limit=1)
                if recent_campaigns:
                    campaign_metrics = await self.db_tool.get_campaign_metrics(recent_campaigns[0]["id"])
                else:
                    return {"success": False, "error": "No campaigns found"}
            
            # Format performance data
            performance_summary = {
                "campaign_name": campaign_metrics.get("name"),
                "messages_sent": campaign_metrics.get("messages_sent", 0),
                "delivery_rate": f"{campaign_metrics.get('delivery_rate', 0):.1f}%",
                "response_rate": f"{campaign_metrics.get('response_rate', 0):.1f}%",
                "positive_responses": campaign_metrics.get("positive_responses", 0),
                "total_responses": campaign_metrics.get("total_responses", 0),
                "roi": campaign_metrics.get("roi_percentage")
            }
            
            return {
                "success": True,
                "data_type": "campaign_performance",
                "performance": performance_summary,
                "actions": ["show_campaign_performance"]
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to get campaign performance: {str(e)}"}
    
    async def _format_response(
        self, 
        response_data: Dict, 
        language: str, 
        query_intent: Dict
    ) -> Dict[str, Any]:
        """Format response in appropriate language and style"""
        try:
            if not response_data.get("success", False):
                error_msg = response_data.get("error", "Unknown error")
                return {
                    "text": f"عذراً، {error_msg}" if language == "arabic" else f"Sorry, {error_msg}",
                    "type": "error"
                }
            
            data_type = response_data.get("data_type")
            
            if data_type == "customers":
                return await self._format_customer_response(response_data, language)
            elif data_type == "campaign_performance":
                return await self._format_campaign_response(response_data, language)
            elif data_type == "daily_summary":
                return await self._format_summary_response(response_data, language)
            else:
                return await self._format_general_response(response_data, language)
                
        except Exception as e:
            await self._log_error("response_formatting", str(e))
            return {
                "text": "خطأ في تنسيق الإجابة" if language == "arabic" else "Error formatting response",
                "type": "error"
            }
    
    async def _format_customer_response(self, data: Dict, language: str) -> Dict[str, Any]:
        """Format customer list response"""
        customers = data.get("customers", [])
        total = data.get("total_count", 0)
        
        if language == "arabic":
            text = f"تم العثور على {total} عميل. إليك أحدث {len(customers)} عملاء:\n\n"
            for customer in customers:
                text += f"👤 {customer['name']}\n"
                text += f"📱 {customer['phone']}\n"
                text += f"🌐 {customer['language']}\n"
                text += f"📅 آخر تفاعل: {customer['last_interaction']}\n"
                text += f"💭 الحالة: {customer['feedback_status']}\n\n"
        else:
            text = f"Found {total} customers. Here are the latest {len(customers)} customers:\n\n"
            for customer in customers:
                text += f"👤 {customer['name']}\n"
                text += f"📱 {customer['phone']}\n"
                text += f"🌐 {customer['language']}\n"
                text += f"📅 Last interaction: {customer['last_interaction']}\n"
                text += f"💭 Status: {customer['feedback_status']}\n\n"
        
        return {
            "text": text,
            "type": "customer_list",
            "data": customers,
            "metadata": {"total_count": total, "showing_count": len(customers)}
        }
    
    async def _generate_follow_up_suggestions(
        self, 
        query_intent: Dict, 
        response: Dict, 
        language: str
    ) -> List[str]:
        """Generate intelligent follow-up suggestions"""
        try:
            suggestions = []
            intent_type = query_intent["type"]
            
            if intent_type == "show_customers" and language == "arabic":
                suggestions = [
                    "أرسل رسالة لهؤلاء العملاء",
                    "أظهر العملاء الذين لم يردوا",
                    "أنشئ حملة جديدة لهم"
                ]
            elif intent_type == "show_customers":
                suggestions = [
                    "Send message to these customers",
                    "Show customers who haven't responded", 
                    "Create new campaign for them"
                ]
            elif intent_type == "campaign_performance" and language == "arabic":
                suggestions = [
                    "قارن مع الحملة السابقة",
                    "أظهر التفاصيل الكاملة",
                    "أنشئ تقرير مفصل"
                ]
            elif intent_type == "campaign_performance":
                suggestions = [
                    "Compare with previous campaign",
                    "Show detailed breakdown",
                    "Generate detailed report"
                ]
            
            return suggestions
            
        except Exception:
            return []

    def get_assistant_summary(self) -> Dict[str, Any]:
        """Get chat assistant performance summary"""
        return {
            "agent_type": "Chat Assistant",
            "version": "1.0.0",
            "capabilities": [
                "Natural language query processing",
                "Business insights generation",
                "Quick action execution",
                "Conversational customer data access",
                "Campaign management assistance",
                "Multi-language support"
            ],
            "supported_languages": ["Arabic", "English", "Mixed"],
            "query_types": [
                "Customer queries",
                "Campaign performance",
                "Daily summaries", 
                "Message sending",
                "Customer feedback",
                "Quick actions"
            ],
            "conversation_features": [
                "Context awareness",
                "Follow-up suggestions",
                "User preference learning",
                "Cultural adaptation"
            ]
        }