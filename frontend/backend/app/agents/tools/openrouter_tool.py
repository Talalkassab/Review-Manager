"""
OpenRouter LLM integration tool for CrewAI agents.
"""
import httpx
import json
from typing import Any, Dict, List, Optional
from pydantic import Field

from .base_tool import BaseAgentTool, ToolResult
from ...core.config import settings


class OpenRouterTool(BaseAgentTool):
    """Tool for making LLM calls through OpenRouter API with fallback support."""
    
    name: str = "openrouter_llm"
    description: str = (
        "Make LLM calls through OpenRouter API with support for multiple models "
        "and automatic fallback. Supports Arabic and English text processing."
    )
    
    api_key: str = Field(default=settings.OPENROUTER_API_KEY, description="OpenRouter API key")
    base_url: str = Field(default="https://openrouter.ai/api/v1", description="OpenRouter API base URL")
    default_model: str = Field(default=settings.DEFAULT_LLM_MODEL, description="Default model to use")
    backup_model: str = Field(default=settings.BACKUP_LLM_MODEL, description="Backup model if default fails")
    max_tokens: int = Field(default=settings.MAX_TOKENS, description="Maximum tokens in response")
    temperature: float = Field(default=settings.TEMPERATURE, description="Response randomness")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": settings.APP_NAME,
                "X-Title": settings.APP_NAME
            },
            timeout=60.0
        )
    
    def _validate_input(self, **kwargs) -> bool:
        """Validate input parameters for LLM call."""
        messages = kwargs.get('messages')
        prompt = kwargs.get('prompt')
        
        if not messages and not prompt:
            self.logger.error("Either 'messages' or 'prompt' parameter is required")
            return False
        
        if messages and not isinstance(messages, list):
            self.logger.error("'messages' parameter must be a list")
            return False
        
        return True
    
    def _format_messages(self, prompt: str = None, messages: List[Dict] = None, 
                        system_prompt: str = None) -> List[Dict]:
        """Format messages for OpenRouter API."""
        if messages:
            return messages
        
        formatted_messages = []
        
        if system_prompt:
            formatted_messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        if prompt:
            formatted_messages.append({
                "role": "user", 
                "content": prompt
            })
        
        return formatted_messages
    
    async def _make_llm_call(self, model: str, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """Make the actual LLM API call."""
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": kwargs.get('max_tokens', self.max_tokens),
            "temperature": kwargs.get('temperature', self.temperature),
            "stream": False
        }
        
        # Add optional parameters
        if kwargs.get('top_p'):
            payload["top_p"] = kwargs['top_p']
        if kwargs.get('frequency_penalty'):
            payload["frequency_penalty"] = kwargs['frequency_penalty']
        if kwargs.get('presence_penalty'):
            payload["presence_penalty"] = kwargs['presence_penalty']
        
        self.logger.log_llm_call(model, len(str(messages)))
        
        response = await self.client.post("/chat/completions", json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        if 'choices' not in result or not result['choices']:
            raise ValueError("Invalid response from OpenRouter API")
        
        content = result['choices'][0]['message']['content']
        usage = result.get('usage', {})
        
        self.logger.log_llm_call(model, usage.get('prompt_tokens', 0), len(content))
        
        return {
            "content": content,
            "model": model,
            "usage": usage,
            "finish_reason": result['choices'][0].get('finish_reason')
        }
    
    def _execute(self, **kwargs) -> Dict[str, Any]:
        """Execute LLM call with fallback support."""
        try:
            messages = self._format_messages(
                prompt=kwargs.get('prompt'),
                messages=kwargs.get('messages'),
                system_prompt=kwargs.get('system_prompt')
            )
            
            model = kwargs.get('model', self.default_model)
            
            # First attempt with primary model
            try:
                import asyncio
                result = asyncio.run(self._make_llm_call(model, messages, **kwargs))
                
                return ToolResult(
                    success=True,
                    data=result,
                    metadata={
                        "model_used": model,
                        "attempt": 1,
                        "fallback_used": False
                    }
                ).dict()
                
            except Exception as e:
                self.logger.warning(f"Primary model {model} failed: {str(e)}")
                
                # Fallback to backup model
                if model != self.backup_model:
                    self.logger.info(f"Trying fallback model: {self.backup_model}")
                    result = asyncio.run(self._make_llm_call(self.backup_model, messages, **kwargs))
                    
                    return ToolResult(
                        success=True,
                        data=result,
                        metadata={
                            "model_used": self.backup_model,
                            "attempt": 2,
                            "fallback_used": True,
                            "primary_error": str(e)
                        }
                    ).dict()
                else:
                    raise e
                    
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"LLM call failed: {str(e)}",
                metadata={"models_tried": [model, self.backup_model]}
            ).dict()
    
    def generate_response(self, prompt: str, system_prompt: str = None, **kwargs) -> str:
        """Simple interface to generate a response."""
        result = self.run(
            prompt=prompt,
            system_prompt=system_prompt,
            **kwargs
        )
        
        if result['success']:
            return result['data']['content']
        else:
            raise Exception(result['error'])
    
    def analyze_sentiment(self, text: str, language: str = "auto") -> Dict[str, Any]:
        """Analyze sentiment of text in Arabic or English."""
        system_prompt = """You are an expert sentiment analyzer for restaurant feedback. 
        Analyze the sentiment of the given text and respond with a JSON object containing:
        - sentiment: "positive", "negative", or "neutral"
        - confidence: float between 0 and 1
        - emotions: list of detected emotions
        - key_phrases: important phrases that influenced the sentiment
        - language: detected language (ar for Arabic, en for English)
        
        Be culturally sensitive to Arabic expressions and context."""
        
        prompt = f"Analyze the sentiment of this restaurant feedback:\n\n{text}"
        
        try:
            result = self.run(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3  # Lower temperature for more consistent analysis
            )
            
            if result['success']:
                response_text = result['data']['content']
                # Try to parse JSON response
                try:
                    return json.loads(response_text)
                except json.JSONDecodeError:
                    # Fallback if response is not valid JSON
                    return {
                        "sentiment": "neutral",
                        "confidence": 0.5,
                        "raw_response": response_text,
                        "language": language
                    }
            else:
                raise Exception(result['error'])
                
        except Exception as e:
            self.logger.error(f"Sentiment analysis failed: {str(e)}")
            return {
                "sentiment": "neutral",
                "confidence": 0.0,
                "error": str(e),
                "language": language
            }
    
    def __del__(self):
        """Clean up the HTTP client."""
        try:
            import asyncio
            asyncio.run(self.client.aclose())
        except:
            pass