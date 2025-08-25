"""
OpenRouter API Service - Handles AI model interactions through OpenRouter API
with support for multiple models, fallback mechanisms, and cost tracking.
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import httpx
from dataclasses import dataclass
from enum import Enum

from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)


class ModelType(Enum):
    """Available AI model types through OpenRouter"""
    CLAUDE_3_5_HAIKU = "anthropic/claude-3.5-haiku"
    CLAUDE_3_5_SONNET = "anthropic/claude-3.5-sonnet"
    GPT_4O_MINI = "openai/gpt-4o-mini"
    GPT_4O = "openai/gpt-4o"
    LLAMA_3_1_8B = "meta-llama/llama-3.1-8b-instruct:free"
    LLAMA_3_1_70B = "meta-llama/llama-3.1-70b-instruct"
    GEMINI_PRO = "google/gemini-pro"
    MISTRAL_LARGE = "mistralai/mistral-large"


@dataclass
class ModelConfig:
    """Configuration for AI model usage"""
    name: str
    max_tokens: int
    temperature: float
    top_p: float
    cost_per_1k_tokens_input: float
    cost_per_1k_tokens_output: float
    language_strength: str  # "arabic", "english", "both"
    use_case: str  # "general", "cultural", "sentiment", "creative"


class OpenRouterService:
    """
    Service for interacting with AI models through OpenRouter API.
    Handles model selection, fallbacks, rate limiting, and cost tracking.
    """
    
    def __init__(self):
        self.base_url = "https://openrouter.ai/api/v1"
        self.api_key = settings.openrouter.OPENROUTER_API_KEY
        self.app_name = getattr(settings.openrouter, 'OPENROUTER_APP_NAME', 'Restaurant AI Agent')
        self.app_url = getattr(settings.openrouter, 'OPENROUTER_APP_URL', 'https://restaurant-ai.com')
        
        # Model configurations
        self.models = {
            ModelType.CLAUDE_3_5_HAIKU: ModelConfig(
                name="Claude 3.5 Haiku",
                max_tokens=4096,
                temperature=0.7,
                top_p=0.9,
                cost_per_1k_tokens_input=0.25,
                cost_per_1k_tokens_output=1.25,
                language_strength="both",
                use_case="cultural"
            ),
            ModelType.GPT_4O_MINI: ModelConfig(
                name="GPT-4O Mini",
                max_tokens=4096,
                temperature=0.7,
                top_p=0.9,
                cost_per_1k_tokens_input=0.15,
                cost_per_1k_tokens_output=0.60,
                language_strength="english",
                use_case="general"
            ),
            ModelType.LLAMA_3_1_8B: ModelConfig(
                name="Llama 3.1 8B (Free)",
                max_tokens=2048,
                temperature=0.7,
                top_p=0.9,
                cost_per_1k_tokens_input=0.0,
                cost_per_1k_tokens_output=0.0,
                language_strength="english",
                use_case="general"
            )
        }
        
        # Usage tracking
        self.usage_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_cost_usd": 0.0,
            "tokens_consumed": {"input": 0, "output": 0}
        }
        
        # Rate limiting
        self.rate_limits = {
            "requests_per_minute": 60,
            "requests_per_hour": 1000,
            "current_minute_requests": 0,
            "current_hour_requests": 0,
            "last_minute_reset": time.time(),
            "last_hour_reset": time.time()
        }
        
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": self.app_url,
                "X-Title": self.app_name,
                "Content-Type": "application/json"
            }
        )
    
    async def generate_response(
        self,
        prompt: str,
        model_type: ModelType = ModelType.CLAUDE_3_5_HAIKU,
        language: str = "arabic",
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate AI response with automatic model selection and fallback.
        """
        try:
            # Check rate limits
            await self._check_rate_limits()
            
            # Select optimal model based on language and context
            selected_model = self._select_optimal_model(model_type, language, context)
            
            # Prepare request
            request_data = await self._prepare_request(
                prompt, selected_model, language, context, **kwargs
            )
            
            # Make API call with retries
            response_data = await self._make_api_call_with_retries(request_data, selected_model)
            
            # Process and track response
            processed_response = await self._process_response(
                response_data, selected_model, prompt
            )
            
            # Update usage statistics
            await self._update_usage_stats(processed_response, selected_model)
            
            logger.info(f"Successfully generated response using {selected_model.value}")
            return processed_response
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            self.usage_stats["failed_requests"] += 1
            
            # Try fallback model
            return await self._try_fallback_model(prompt, language, context, str(e))
    
    async def generate_batch_responses(
        self,
        prompts: List[str],
        model_type: ModelType = ModelType.CLAUDE_3_5_HAIKU,
        language: str = "arabic",
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple AI responses concurrently with rate limiting.
        """
        try:
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def process_single_prompt(prompt: str, index: int) -> Dict[str, Any]:
                async with semaphore:
                    try:
                        response = await self.generate_response(
                            prompt=prompt,
                            model_type=model_type,
                            language=language,
                            context={"batch_index": index, "batch_total": len(prompts)}
                        )
                        return {"index": index, "success": True, **response}
                    except Exception as e:
                        logger.error(f"Batch request {index} failed: {str(e)}")
                        return {
                            "index": index, 
                            "success": False, 
                            "error": str(e),
                            "fallback_response": "عذراً، حدث خطأ في المعالجة"
                        }
            
            # Execute batch processing
            tasks = [
                process_single_prompt(prompt, i) 
                for i, prompt in enumerate(prompts)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Sort results by index to maintain order
            sorted_results = sorted(
                [r for r in results if isinstance(r, dict)], 
                key=lambda x: x.get("index", 0)
            )
            
            logger.info(f"Batch processing completed: {len(prompts)} prompts")
            return sorted_results
            
        except Exception as e:
            logger.error(f"Batch processing failed: {str(e)}")
            return [{"success": False, "error": str(e)} for _ in prompts]
    
    async def analyze_text_sentiment(
        self,
        text: str,
        language: str = "arabic",
        detailed_analysis: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze text sentiment with cultural context awareness.
        """
        try:
            sentiment_prompt = await self._create_sentiment_analysis_prompt(
                text, language, detailed_analysis
            )
            
            # Use appropriate model for sentiment analysis
            model = ModelType.CLAUDE_3_5_HAIKU if language == "arabic" else ModelType.GPT_4O_MINI
            
            response = await self.generate_response(
                prompt=sentiment_prompt,
                model_type=model,
                language=language,
                context={"task": "sentiment_analysis", "detailed": detailed_analysis}
            )
            
            # Parse sentiment analysis result
            sentiment_data = await self._parse_sentiment_response(response, language)
            
            return {
                "original_text": text,
                "language": language,
                "sentiment": sentiment_data,
                "model_used": model.value,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {str(e)}")
            return {
                "original_text": text,
                "error": str(e),
                "fallback_sentiment": "neutral"
            }
    
    async def generate_personalized_message(
        self,
        customer_data: Dict[str, Any],
        message_type: str,
        language: str = "arabic",
        cultural_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate personalized messages for customers with cultural awareness.
        """
        try:
            message_prompt = await self._create_personalization_prompt(
                customer_data, message_type, language, cultural_context
            )
            
            # Select model based on language and personalization needs
            model = ModelType.CLAUDE_3_5_HAIKU  # Best for cultural nuances
            
            response = await self.generate_response(
                prompt=message_prompt,
                model_type=model,
                language=language,
                context={
                    "task": "message_personalization",
                    "message_type": message_type,
                    "customer_segment": customer_data.get("segment")
                }
            )
            
            # Extract and format the personalized message
            personalized_message = await self._extract_personalized_message(
                response, language, message_type
            )
            
            return {
                "customer_id": customer_data.get("id"),
                "message_type": message_type,
                "language": language,
                "personalized_message": personalized_message,
                "cultural_elements": cultural_context,
                "model_used": model.value,
                "generation_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Message personalization failed: {str(e)}")
            return {
                "error": str(e),
                "fallback_message": await self._get_fallback_message(message_type, language)
            }
    
    async def optimize_campaign_content(
        self,
        campaign_data: Dict[str, Any],
        performance_metrics: Dict[str, Any],
        target_audience: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Optimize campaign content based on performance data and audience insights.
        """
        try:
            optimization_prompt = await self._create_optimization_prompt(
                campaign_data, performance_metrics, target_audience
            )
            
            model = ModelType.CLAUDE_3_5_HAIKU  # Best for creative optimization
            
            response = await self.generate_response(
                prompt=optimization_prompt,
                model_type=model,
                language=target_audience.get("primary_language", "arabic"),
                context={
                    "task": "campaign_optimization",
                    "current_performance": performance_metrics.get("overall_score", 0)
                }
            )
            
            # Parse optimization suggestions
            optimization_suggestions = await self._parse_optimization_response(
                response, campaign_data, performance_metrics
            )
            
            return {
                "campaign_id": campaign_data.get("id"),
                "optimization_suggestions": optimization_suggestions,
                "expected_improvement": optimization_suggestions.get("expected_improvement", 0),
                "model_used": model.value,
                "optimization_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Campaign optimization failed: {str(e)}")
            return {"error": str(e)}
    
    async def _select_optimal_model(
        self, 
        requested_model: ModelType, 
        language: str, 
        context: Optional[Dict]
    ) -> ModelType:
        """Select the most appropriate model based on requirements"""
        
        # If specific model requested and available, use it
        if requested_model in self.models:
            return requested_model
        
        # Select based on language and use case
        if language == "arabic" or "cultural" in str(context):
            return ModelType.CLAUDE_3_5_HAIKU  # Best for Arabic and cultural context
        elif context and context.get("task") == "sentiment_analysis":
            return ModelType.CLAUDE_3_5_HAIKU  # Good for sentiment
        elif context and "cost_sensitive" in str(context):
            return ModelType.LLAMA_3_1_8B  # Free option
        else:
            return ModelType.GPT_4O_MINI  # Good general purpose
    
    async def _prepare_request(
        self,
        prompt: str,
        model: ModelType,
        language: str,
        context: Optional[Dict],
        **kwargs
    ) -> Dict[str, Any]:
        """Prepare the API request data"""
        
        model_config = self.models[model]
        
        # Build system message based on language and context
        system_message = await self._build_system_message(language, context)
        
        request_data = {
            "model": model.value,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": kwargs.get("max_tokens", model_config.max_tokens),
            "temperature": kwargs.get("temperature", model_config.temperature),
            "top_p": kwargs.get("top_p", model_config.top_p),
            "stream": False
        }
        
        return request_data
    
    async def _build_system_message(self, language: str, context: Optional[Dict]) -> str:
        """Build appropriate system message based on language and context"""
        
        base_messages = {
            "arabic": """أنت مساعد ذكي متخصص في خدمة المطاعم والتواصل مع العملاء. 
            تتحدث العربية بطلاقة وتفهم الثقافة العربية والخليجية بعمق.
            تراعي الاعتبارات الدينية والثقافية في جميع ردودك.""",
            
            "english": """You are an intelligent assistant specialized in restaurant customer service. 
            You understand cultural nuances and provide contextually appropriate responses."""
        }
        
        system_msg = base_messages.get(language, base_messages["english"])
        
        # Add context-specific instructions
        if context:
            task = context.get("task", "")
            
            if task == "sentiment_analysis":
                system_msg += "\n\nمهمتك تحليل المشاعر والعواطف في النصوص مع مراعاة السياق الثقافي." if language == "arabic" else "\n\nYour task is to analyze sentiment and emotions with cultural context awareness."
            
            elif task == "message_personalization":
                system_msg += "\n\nمهمتك إنشاء رسائل شخصية ومناسبة ثقافياً للعملاء." if language == "arabic" else "\n\nYour task is to create personalized, culturally appropriate messages for customers."
            
            elif task == "campaign_optimization":
                system_msg += "\n\nمهمتك تحسين المحتوى والاستراتيجيات لزيادة فعالية الحملات." if language == "arabic" else "\n\nYour task is to optimize content and strategies for better campaign performance."
        
        return system_msg
    
    async def _make_api_call_with_retries(
        self, 
        request_data: Dict, 
        model: ModelType,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Make API call with retry logic"""
        
        for attempt in range(max_retries):
            try:
                response = await self.client.post(
                    f"{self.base_url}/chat/completions",
                    json=request_data
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limited
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    response.raise_for_status()
                    
            except Exception as e:
                logger.warning(f"API call attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(1)  # Brief pause between retries
        
        raise Exception(f"All {max_retries} API call attempts failed")
    
    async def _process_response(
        self, 
        response_data: Dict, 
        model: ModelType, 
        original_prompt: str
    ) -> Dict[str, Any]:
        """Process and structure the API response"""
        
        try:
            content = response_data["choices"][0]["message"]["content"]
            usage = response_data.get("usage", {})
            
            return {
                "content": content.strip(),
                "model_used": model.value,
                "tokens_used": {
                    "input": usage.get("prompt_tokens", 0),
                    "output": usage.get("completion_tokens", 0),
                    "total": usage.get("total_tokens", 0)
                },
                "request_timestamp": datetime.now().isoformat(),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error processing response: {str(e)}")
            return {
                "content": "عذراً، حدث خطأ في معالجة الرد",
                "error": str(e),
                "success": False
            }
    
    async def _update_usage_stats(self, response: Dict, model: ModelType):
        """Update usage statistics and cost tracking"""
        
        self.usage_stats["total_requests"] += 1
        
        if response.get("success", False):
            self.usage_stats["successful_requests"] += 1
            
            # Track token usage
            tokens = response.get("tokens_used", {})
            self.usage_stats["tokens_consumed"]["input"] += tokens.get("input", 0)
            self.usage_stats["tokens_consumed"]["output"] += tokens.get("output", 0)
            
            # Calculate cost
            model_config = self.models[model]
            input_cost = (tokens.get("input", 0) / 1000) * model_config.cost_per_1k_tokens_input
            output_cost = (tokens.get("output", 0) / 1000) * model_config.cost_per_1k_tokens_output
            total_cost = input_cost + output_cost
            
            self.usage_stats["total_cost_usd"] += total_cost
            
            # Log cost if significant
            if total_cost > 0.01:  # Log if cost > 1 cent
                logger.info(f"API call cost: ${total_cost:.4f} using {model.value}")
        else:
            self.usage_stats["failed_requests"] += 1
    
    async def _try_fallback_model(
        self, 
        prompt: str, 
        language: str, 
        context: Optional[Dict], 
        original_error: str
    ) -> Dict[str, Any]:
        """Try fallback model when primary model fails"""
        
        try:
            logger.info("Attempting fallback model due to primary model failure")
            
            # Try free model as fallback
            fallback_model = ModelType.LLAMA_3_1_8B
            
            return await self.generate_response(
                prompt=prompt,
                model_type=fallback_model,
                language=language,
                context={**(context or {}), "fallback_attempt": True}
            )
            
        except Exception as fallback_error:
            logger.error(f"Fallback model also failed: {str(fallback_error)}")
            return {
                "content": "عذراً، الخدمة غير متوفرة حالياً" if language == "arabic" else "Sorry, service temporarily unavailable",
                "error": f"Primary: {original_error}, Fallback: {str(fallback_error)}",
                "success": False,
                "fallback_used": True
            }
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        return {
            **self.usage_stats,
            "cost_breakdown": {
                model.value: {
                    "cost_per_1k_input": config.cost_per_1k_tokens_input,
                    "cost_per_1k_output": config.cost_per_1k_tokens_output
                }
                for model, config in self.models.items()
            },
            "available_models": [model.value for model in self.models.keys()],
            "rate_limits": self.rate_limits
        }
    
    async def _check_rate_limits(self):
        """Check and enforce rate limits"""
        current_time = time.time()
        
        # Reset counters if time windows have passed
        if current_time - self.rate_limits["last_minute_reset"] >= 60:
            self.rate_limits["current_minute_requests"] = 0
            self.rate_limits["last_minute_reset"] = current_time
        
        if current_time - self.rate_limits["last_hour_reset"] >= 3600:
            self.rate_limits["current_hour_requests"] = 0
            self.rate_limits["last_hour_reset"] = current_time
        
        # Check limits
        if self.rate_limits["current_minute_requests"] >= self.rate_limits["requests_per_minute"]:
            raise Exception("Rate limit exceeded: requests per minute")
        
        if self.rate_limits["current_hour_requests"] >= self.rate_limits["requests_per_hour"]:
            raise Exception("Rate limit exceeded: requests per hour")
        
        # Increment counters
        self.rate_limits["current_minute_requests"] += 1
        self.rate_limits["current_hour_requests"] += 1
    
    async def shutdown(self):
        """Cleanup and close connections"""
        await self.client.aclose()
        logger.info("OpenRouter service shut down")