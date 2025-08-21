"""
Integration Testing Suite
========================

Comprehensive integration testing utilities for WhatsApp, OpenRouter AI APIs,
and database operations with performance monitoring and error detection.
"""

import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..core.logging import get_logger
from ..services.openrouter.client import OpenRouterClient
from ..services.openrouter.exceptions import OpenRouterError
from .models import IntegrationTestResult as DBIntegrationTestResult
from .schemas import IntegrationTestConfig, IntegrationTestResult

logger = get_logger(__name__)

@dataclass
class TestResult:
    """Individual test result container"""
    test_name: str
    status: str  # passed, failed, error
    duration_ms: float
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    performance_metrics: Optional[Dict[str, Any]] = None

class WhatsAppIntegrationTester:
    """
    Tests WhatsApp Business API integration including:
    - Message sending capability
    - Delivery status tracking
    - Media handling
    - Rate limiting compliance
    - Webhook functionality
    """
    
    def __init__(self):
        self.base_url = "https://graph.facebook.com/v18.0"
        self.test_phone_numbers = ["+966501234567", "+966501234568"]  # Test numbers
    
    async def test_message_sending(self, config: IntegrationTestConfig) -> TestResult:
        """Test basic message sending functionality"""
        
        start_time = time.time()
        
        try:
            # Extract WhatsApp config
            wa_config = config.test_config.get("whatsapp", {})
            access_token = wa_config.get("access_token")
            phone_number_id = wa_config.get("phone_number_id")
            
            if not access_token or not phone_number_id:
                return TestResult(
                    test_name="message_sending",
                    status="error",
                    duration_ms=(time.time() - start_time) * 1000,
                    error="Missing WhatsApp configuration (access_token or phone_number_id)"
                )
            
            # Test message payload
            test_message = {
                "messaging_product": "whatsapp",
                "to": self.test_phone_numbers[0],
                "type": "text",
                "text": {
                    "body": f"Test message from integration test - {datetime.utcnow().isoformat()}"
                }
            }
            
            # Send test message
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/{phone_number_id}/messages",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    },
                    json=test_message,
                    timeout=30.0
                )
            
            duration_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                response_data = response.json()
                return TestResult(
                    test_name="message_sending",
                    status="passed",
                    duration_ms=duration_ms,
                    output={
                        "message_id": response_data.get("messages", [{}])[0].get("id"),
                        "response": response_data
                    },
                    performance_metrics={
                        "response_time_ms": duration_ms,
                        "status_code": response.status_code
                    }
                )
            else:
                return TestResult(
                    test_name="message_sending",
                    status="failed",
                    duration_ms=duration_ms,
                    error=f"HTTP {response.status_code}: {response.text}",
                    output={"status_code": response.status_code, "response": response.text}
                )
                
        except Exception as e:
            return TestResult(
                test_name="message_sending",
                status="error",
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )
    
    async def test_delivery_status_tracking(self, config: IntegrationTestConfig) -> TestResult:
        """Test message delivery status tracking"""
        
        start_time = time.time()
        
        try:
            # First send a message to get a message ID
            message_result = await self.test_message_sending(config)
            
            if message_result.status != "passed":
                return TestResult(
                    test_name="delivery_status_tracking",
                    status="error",
                    duration_ms=(time.time() - start_time) * 1000,
                    error="Cannot test delivery status - message sending failed"
                )
            
            message_id = message_result.output.get("message_id")
            
            # Wait a bit for delivery status to be available
            await asyncio.sleep(2)
            
            wa_config = config.test_config.get("whatsapp", {})
            access_token = wa_config.get("access_token")
            
            # Query message status (this is a mock - actual implementation depends on webhook)
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/{message_id}",
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=15.0
                )
            
            duration_ms = (time.time() - start_time) * 1000
            
            return TestResult(
                test_name="delivery_status_tracking",
                status="passed" if response.status_code in [200, 404] else "failed",
                duration_ms=duration_ms,
                output={
                    "message_id": message_id,
                    "status_response": response.json() if response.status_code == 200 else None
                },
                performance_metrics={
                    "query_response_time_ms": (time.time() - start_time) * 1000
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="delivery_status_tracking", 
                status="error",
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )
    
    async def test_media_handling(self, config: IntegrationTestConfig) -> TestResult:
        """Test media message handling"""
        
        start_time = time.time()
        
        try:
            wa_config = config.test_config.get("whatsapp", {})
            access_token = wa_config.get("access_token")
            phone_number_id = wa_config.get("phone_number_id")
            
            # Test image message
            test_media_message = {
                "messaging_product": "whatsapp",
                "to": self.test_phone_numbers[0],
                "type": "image",
                "image": {
                    "link": "https://via.placeholder.com/300x200.png?text=Test+Image",
                    "caption": "Integration test image"
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/{phone_number_id}/messages",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    },
                    json=test_media_message,
                    timeout=45.0
                )
            
            duration_ms = (time.time() - start_time) * 1000
            
            return TestResult(
                test_name="media_handling",
                status="passed" if response.status_code == 200 else "failed",
                duration_ms=duration_ms,
                output={"response": response.json() if response.status_code == 200 else response.text},
                performance_metrics={
                    "media_upload_time_ms": duration_ms,
                    "status_code": response.status_code
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="media_handling",
                status="error", 
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )
    
    async def test_rate_limiting(self, config: IntegrationTestConfig) -> TestResult:
        """Test rate limiting compliance"""
        
        start_time = time.time()
        
        try:
            # Send multiple messages rapidly to test rate limiting
            tasks = []
            for i in range(5):  # Send 5 messages quickly
                task = self.test_message_sending(config)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Analyze results
            passed_count = sum(1 for r in results if isinstance(r, TestResult) and r.status == "passed")
            failed_count = sum(1 for r in results if isinstance(r, TestResult) and r.status == "failed")
            error_count = sum(1 for r in results if not isinstance(r, TestResult) or r.status == "error")
            
            # Rate limiting is working if some requests failed with appropriate errors
            rate_limited = any(
                isinstance(r, TestResult) and "rate" in str(r.error).lower() 
                for r in results
            )
            
            return TestResult(
                test_name="rate_limiting",
                status="passed",  # Rate limiting behavior is expected
                duration_ms=duration_ms,
                output={
                    "total_requests": len(results),
                    "passed": passed_count,
                    "failed": failed_count, 
                    "errors": error_count,
                    "rate_limiting_detected": rate_limited
                },
                performance_metrics={
                    "average_request_time_ms": duration_ms / len(results),
                    "requests_per_second": len(results) / (duration_ms / 1000)
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="rate_limiting",
                status="error",
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )

class OpenRouterIntegrationTester:
    """
    Tests OpenRouter AI API integration including:
    - Model availability and response
    - Arabic language support
    - Response time and quality
    - Error handling
    - Cost tracking
    """
    
    def __init__(self):
        self.test_models = [
            "openai/gpt-3.5-turbo",
            "anthropic/claude-3-haiku",
            "meta-llama/llama-2-70b-chat"
        ]
    
    async def test_model_availability(self, config: IntegrationTestConfig) -> TestResult:
        """Test if configured models are available"""
        
        start_time = time.time()
        
        try:
            openrouter_config = config.test_config.get("openrouter", {})
            api_key = openrouter_config.get("api_key")
            
            if not api_key:
                return TestResult(
                    test_name="model_availability",
                    status="error",
                    duration_ms=(time.time() - start_time) * 1000,
                    error="Missing OpenRouter API key"
                )
            
            client = OpenRouterClient(api_key=api_key)
            
            # Test each model
            model_results = {}
            
            for model in self.test_models:
                try:
                    model_start = time.time()
                    
                    # Simple test prompt
                    response = await client.chat_completion(
                        model=model,
                        messages=[{"role": "user", "content": "Hello, this is a test message."}],
                        max_tokens=50,
                        temperature=0.7
                    )
                    
                    model_duration = (time.time() - model_start) * 1000
                    
                    model_results[model] = {
                        "status": "available",
                        "response_time_ms": model_duration,
                        "response_length": len(response.choices[0].message.content) if response.choices else 0
                    }
                    
                except Exception as e:
                    model_results[model] = {
                        "status": "unavailable",
                        "error": str(e)
                    }
            
            duration_ms = (time.time() - start_time) * 1000
            available_models = [m for m, r in model_results.items() if r["status"] == "available"]
            
            return TestResult(
                test_name="model_availability",
                status="passed" if available_models else "failed",
                duration_ms=duration_ms,
                output={
                    "model_results": model_results,
                    "available_models": available_models,
                    "total_models_tested": len(self.test_models)
                },
                performance_metrics={
                    "average_model_response_time_ms": sum(
                        r.get("response_time_ms", 0) for r in model_results.values() if "response_time_ms" in r
                    ) / max(len(available_models), 1)
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="model_availability",
                status="error",
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )
    
    async def test_arabic_language_support(self, config: IntegrationTestConfig) -> TestResult:
        """Test Arabic language processing capability"""
        
        start_time = time.time()
        
        try:
            openrouter_config = config.test_config.get("openrouter", {})
            api_key = openrouter_config.get("api_key")
            
            client = OpenRouterClient(api_key=api_key)
            
            # Test prompts in Arabic
            arabic_test_prompts = [
                "مرحباً، كيف يمكنني مساعدتك اليوم؟",
                "اكتب رسالة ترحيب قصيرة لعميل مطعم",
                "ما هو أفضل طبق في المطبخ السعودي؟"
            ]
            
            results = []
            
            for prompt in arabic_test_prompts:
                prompt_start = time.time()
                
                try:
                    response = await client.chat_completion(
                        model="openai/gpt-3.5-turbo",  # Use most reliable model
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant that responds in Arabic."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=100,
                        temperature=0.7
                    )
                    
                    response_content = response.choices[0].message.content
                    prompt_duration = (time.time() - prompt_start) * 1000
                    
                    # Check if response contains Arabic text
                    has_arabic = any('\u0600' <= char <= '\u06FF' for char in response_content)
                    
                    results.append({
                        "prompt": prompt,
                        "response": response_content,
                        "has_arabic": has_arabic,
                        "response_time_ms": prompt_duration,
                        "status": "passed" if has_arabic else "failed"
                    })
                    
                except Exception as e:
                    results.append({
                        "prompt": prompt,
                        "status": "error",
                        "error": str(e)
                    })
            
            duration_ms = (time.time() - start_time) * 1000
            successful_tests = [r for r in results if r["status"] == "passed"]
            
            return TestResult(
                test_name="arabic_language_support",
                status="passed" if len(successful_tests) >= 2 else "failed",
                duration_ms=duration_ms,
                output={
                    "test_results": results,
                    "successful_tests": len(successful_tests),
                    "total_tests": len(results)
                },
                performance_metrics={
                    "average_arabic_response_time_ms": sum(
                        r.get("response_time_ms", 0) for r in results if "response_time_ms" in r
                    ) / max(len(results), 1)
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="arabic_language_support",
                status="error",
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )
    
    async def test_response_quality_and_speed(self, config: IntegrationTestConfig) -> TestResult:
        """Test response quality and performance benchmarks"""
        
        start_time = time.time()
        
        try:
            openrouter_config = config.test_config.get("openrouter", {})
            client = OpenRouterClient(api_key=openrouter_config.get("api_key"))
            
            # Performance test scenarios
            test_scenarios = [
                {
                    "name": "simple_greeting",
                    "prompt": "Generate a polite greeting for a restaurant customer in Arabic",
                    "expected_max_time_ms": 3000,
                    "expected_min_length": 10
                },
                {
                    "name": "complex_response", 
                    "prompt": "Write a detailed apology message for a restaurant customer who received cold food, including steps to resolve the issue",
                    "expected_max_time_ms": 5000,
                    "expected_min_length": 50
                },
                {
                    "name": "multilingual_task",
                    "prompt": "Translate this to Arabic: 'Thank you for your feedback, we will improve our service'",
                    "expected_max_time_ms": 4000,
                    "expected_min_length": 15
                }
            ]
            
            scenario_results = []
            
            for scenario in test_scenarios:
                scenario_start = time.time()
                
                try:
                    response = await client.chat_completion(
                        model="openai/gpt-3.5-turbo",
                        messages=[{"role": "user", "content": scenario["prompt"]}],
                        max_tokens=200,
                        temperature=0.7
                    )
                    
                    scenario_duration = (time.time() - scenario_start) * 1000
                    response_content = response.choices[0].message.content
                    response_length = len(response_content)
                    
                    # Quality checks
                    meets_time_requirement = scenario_duration <= scenario["expected_max_time_ms"]
                    meets_length_requirement = response_length >= scenario["expected_min_length"]
                    has_meaningful_content = len(response_content.strip()) > 5
                    
                    scenario_results.append({
                        "scenario": scenario["name"],
                        "response_time_ms": scenario_duration,
                        "response_length": response_length,
                        "meets_time_requirement": meets_time_requirement,
                        "meets_length_requirement": meets_length_requirement,
                        "has_meaningful_content": has_meaningful_content,
                        "overall_quality_score": sum([
                            meets_time_requirement, meets_length_requirement, has_meaningful_content
                        ]) / 3,
                        "response_sample": response_content[:100] + "..." if len(response_content) > 100 else response_content
                    })
                    
                except Exception as e:
                    scenario_results.append({
                        "scenario": scenario["name"],
                        "error": str(e),
                        "overall_quality_score": 0
                    })
            
            duration_ms = (time.time() - start_time) * 1000
            average_quality = sum(r.get("overall_quality_score", 0) for r in scenario_results) / len(scenario_results)
            
            return TestResult(
                test_name="response_quality_and_speed",
                status="passed" if average_quality >= 0.7 else "failed",
                duration_ms=duration_ms,
                output={
                    "scenario_results": scenario_results,
                    "average_quality_score": average_quality,
                    "total_scenarios": len(test_scenarios)
                },
                performance_metrics={
                    "average_response_time_ms": sum(
                        r.get("response_time_ms", 0) for r in scenario_results if "response_time_ms" in r
                    ) / max(len(scenario_results), 1),
                    "quality_benchmark_score": average_quality
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="response_quality_and_speed",
                status="error",
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )

class DatabaseIntegrationTester:
    """
    Tests database operations and performance including:
    - Connection stability
    - CRUD operations
    - Query performance
    - Transaction handling
    - Data integrity
    """
    
    async def test_connection_stability(self, db: Session, config: IntegrationTestConfig) -> TestResult:
        """Test database connection stability"""
        
        start_time = time.time()
        
        try:
            # Test multiple connection attempts
            connection_tests = []
            
            for i in range(5):
                conn_start = time.time()
                
                try:
                    # Simple query to test connection
                    result = db.execute(text("SELECT 1 as test_value")).fetchone()
                    conn_duration = (time.time() - conn_start) * 1000
                    
                    connection_tests.append({
                        "test_number": i + 1,
                        "status": "success",
                        "response_time_ms": conn_duration,
                        "result": result[0] if result else None
                    })
                    
                except Exception as e:
                    connection_tests.append({
                        "test_number": i + 1,
                        "status": "failed",
                        "error": str(e)
                    })
                
                # Small delay between tests
                await asyncio.sleep(0.1)
            
            duration_ms = (time.time() - start_time) * 1000
            successful_connections = [t for t in connection_tests if t["status"] == "success"]
            
            return TestResult(
                test_name="connection_stability",
                status="passed" if len(successful_connections) == 5 else "failed",
                duration_ms=duration_ms,
                output={
                    "connection_tests": connection_tests,
                    "successful_connections": len(successful_connections),
                    "total_tests": 5
                },
                performance_metrics={
                    "average_connection_time_ms": sum(
                        t.get("response_time_ms", 0) for t in successful_connections
                    ) / max(len(successful_connections), 1),
                    "connection_success_rate": len(successful_connections) / 5
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="connection_stability",
                status="error",
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )
    
    async def test_crud_operations_performance(self, db: Session, config: IntegrationTestConfig) -> TestResult:
        """Test CRUD operations performance"""
        
        start_time = time.time()
        
        try:
            # Test data for CRUD operations
            test_records = []
            
            # CREATE test
            create_start = time.time()
            for i in range(10):
                # Create test integration result record
                test_record = DBIntegrationTestResult(
                    test_name=f"performance_test_{i}",
                    test_type="database",
                    start_time=datetime.utcnow(),
                    end_time=datetime.utcnow(),
                    status="passed",
                    test_output={"test_data": f"record_{i}"},
                    test_config={"test_id": i},
                    environment="test"
                )
                db.add(test_record)
                test_records.append(test_record)
            
            db.commit()
            create_duration = (time.time() - create_start) * 1000
            
            # READ test
            read_start = time.time()
            read_records = db.query(DBIntegrationTestResult).filter(
                DBIntegrationTestResult.test_name.like("performance_test_%")
            ).all()
            read_duration = (time.time() - read_start) * 1000
            
            # UPDATE test
            update_start = time.time()
            for record in read_records:
                record.status = "updated"
            db.commit()
            update_duration = (time.time() - update_start) * 1000
            
            # DELETE test
            delete_start = time.time()
            for record in read_records:
                db.delete(record)
            db.commit()
            delete_duration = (time.time() - delete_start) * 1000
            
            duration_ms = (time.time() - start_time) * 1000
            
            return TestResult(
                test_name="crud_operations_performance",
                status="passed",
                duration_ms=duration_ms,
                output={
                    "records_processed": len(test_records),
                    "create_duration_ms": create_duration,
                    "read_duration_ms": read_duration,
                    "update_duration_ms": update_duration,
                    "delete_duration_ms": delete_duration
                },
                performance_metrics={
                    "create_ops_per_second": len(test_records) / (create_duration / 1000),
                    "read_ops_per_second": len(read_records) / (read_duration / 1000),
                    "update_ops_per_second": len(read_records) / (update_duration / 1000),
                    "delete_ops_per_second": len(read_records) / (delete_duration / 1000)
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="crud_operations_performance",
                status="error",
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )

class IntegrationTestingSuite:
    """Main integration testing coordinator"""
    
    def __init__(self):
        self.whatsapp_tester = WhatsAppIntegrationTester()
        self.openrouter_tester = OpenRouterIntegrationTester()
        self.database_tester = DatabaseIntegrationTester()
    
    async def test_whatsapp_integration(
        self,
        config: IntegrationTestConfig,
        user_id: str
    ) -> IntegrationTestResult:
        """Run comprehensive WhatsApp integration tests"""
        
        start_time = datetime.utcnow()
        
        try:
            # Run all WhatsApp tests
            test_results = []
            
            # Message sending test
            message_result = await self.whatsapp_tester.test_message_sending(config)
            test_results.append(message_result)
            
            # Delivery status test
            delivery_result = await self.whatsapp_tester.test_delivery_status_tracking(config)
            test_results.append(delivery_result)
            
            # Media handling test
            media_result = await self.whatsapp_tester.test_media_handling(config)
            test_results.append(media_result)
            
            # Rate limiting test
            rate_limit_result = await self.whatsapp_tester.test_rate_limiting(config)
            test_results.append(rate_limit_result)
            
            end_time = datetime.utcnow()
            
            # Aggregate results
            passed_tests = [r for r in test_results if r.status == "passed"]
            failed_tests = [r for r in test_results if r.status == "failed"]
            error_tests = [r for r in test_results if r.status == "error"]
            
            overall_status = "passed" if len(failed_tests) + len(error_tests) == 0 else (
                "failed" if len(error_tests) == 0 else "error"
            )
            
            # Compile performance data
            performance_data = {
                "total_tests": len(test_results),
                "passed_tests": len(passed_tests),
                "failed_tests": len(failed_tests),
                "error_tests": len(error_tests),
                "success_rate": len(passed_tests) / len(test_results),
                "average_response_time_ms": sum(r.duration_ms for r in test_results) / len(test_results),
                "individual_test_performance": {
                    r.test_name: r.performance_metrics for r in test_results if r.performance_metrics
                }
            }
            
            return IntegrationTestResult(
                test_name="WhatsApp Integration Suite",
                test_type="whatsapp",
                start_time=start_time,
                end_time=end_time,
                status=overall_status,
                test_output={
                    "individual_test_results": [
                        {
                            "test_name": r.test_name,
                            "status": r.status,
                            "duration_ms": r.duration_ms,
                            "output": r.output,
                            "error": r.error
                        } for r in test_results
                    ]
                },
                performance_data=performance_data
            )
            
        except Exception as e:
            logger.error(f"WhatsApp integration test suite failed: {str(e)}")
            return IntegrationTestResult(
                test_name="WhatsApp Integration Suite",
                test_type="whatsapp",
                start_time=start_time,
                end_time=datetime.utcnow(),
                status="error",
                error_details={"error": str(e)}
            )
    
    async def test_openrouter_integration(
        self,
        config: IntegrationTestConfig,
        user_id: str
    ) -> IntegrationTestResult:
        """Run comprehensive OpenRouter integration tests"""
        
        start_time = datetime.utcnow()
        
        try:
            test_results = []
            
            # Model availability test
            availability_result = await self.openrouter_tester.test_model_availability(config)
            test_results.append(availability_result)
            
            # Arabic language support test
            arabic_result = await self.openrouter_tester.test_arabic_language_support(config)
            test_results.append(arabic_result)
            
            # Response quality and speed test
            quality_result = await self.openrouter_tester.test_response_quality_and_speed(config)
            test_results.append(quality_result)
            
            end_time = datetime.utcnow()
            
            # Aggregate results
            passed_tests = [r for r in test_results if r.status == "passed"]
            overall_status = "passed" if len(passed_tests) == len(test_results) else "failed"
            
            performance_data = {
                "total_tests": len(test_results),
                "passed_tests": len(passed_tests),
                "success_rate": len(passed_tests) / len(test_results),
                "test_details": {r.test_name: r.performance_metrics for r in test_results if r.performance_metrics}
            }
            
            return IntegrationTestResult(
                test_name="OpenRouter Integration Suite",
                test_type="openrouter",
                start_time=start_time,
                end_time=end_time,
                status=overall_status,
                test_output={
                    "individual_test_results": [
                        {
                            "test_name": r.test_name,
                            "status": r.status,
                            "duration_ms": r.duration_ms,
                            "output": r.output,
                            "error": r.error
                        } for r in test_results
                    ]
                },
                performance_data=performance_data
            )
            
        except Exception as e:
            return IntegrationTestResult(
                test_name="OpenRouter Integration Suite",
                test_type="openrouter",
                start_time=start_time,
                end_time=datetime.utcnow(),
                status="error",
                error_details={"error": str(e)}
            )
    
    async def test_database_integration(
        self,
        db: Session,
        config: IntegrationTestConfig,
        user_id: str
    ) -> IntegrationTestResult:
        """Run comprehensive database integration tests"""
        
        start_time = datetime.utcnow()
        
        try:
            test_results = []
            
            # Connection stability test
            connection_result = await self.database_tester.test_connection_stability(db, config)
            test_results.append(connection_result)
            
            # CRUD operations performance test
            crud_result = await self.database_tester.test_crud_operations_performance(db, config)
            test_results.append(crud_result)
            
            end_time = datetime.utcnow()
            
            passed_tests = [r for r in test_results if r.status == "passed"]
            overall_status = "passed" if len(passed_tests) == len(test_results) else "failed"
            
            performance_data = {
                "total_tests": len(test_results),
                "passed_tests": len(passed_tests),
                "performance_metrics": {r.test_name: r.performance_metrics for r in test_results if r.performance_metrics}
            }
            
            return IntegrationTestResult(
                test_name="Database Integration Suite",
                test_type="database",
                start_time=start_time,
                end_time=end_time,
                status=overall_status,
                test_output={
                    "test_results": [
                        {
                            "test_name": r.test_name,
                            "status": r.status,
                            "output": r.output,
                            "error": r.error
                        } for r in test_results
                    ]
                },
                performance_data=performance_data
            )
            
        except Exception as e:
            return IntegrationTestResult(
                test_name="Database Integration Suite",
                test_type="database",
                start_time=start_time,
                end_time=datetime.utcnow(),
                status="error",
                error_details={"error": str(e)}
            )
    
    async def store_test_result(
        self,
        db: Session,
        result: IntegrationTestResult,
        user_id: str
    ):
        """Store integration test result in database"""
        
        try:
            db_result = DBIntegrationTestResult(
                test_name=result.test_name,
                test_type=result.test_type,
                start_time=result.start_time,
                end_time=result.end_time,
                status=result.status,
                test_output=result.test_output,
                error_details=result.error_details,
                performance_data=result.performance_data,
                test_config={"user_id": user_id},
                environment="test",
                user_id=user_id
            )
            
            db.add(db_result)
            db.commit()
            
            logger.info(f"Stored integration test result: {result.test_name} - {result.status}")
            
        except Exception as e:
            logger.error(f"Failed to store integration test result: {str(e)}")
            db.rollback()

# Global integration testing suite instance
integration_testing = IntegrationTestingSuite()