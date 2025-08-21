"""
Base testing utilities and classes
"""
import asyncio
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from .config import TestConfig, CulturalRegion, PersonaConfig


class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TestResult(Enum):
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    ERROR = "error"


@dataclass
class TestMessage:
    """Represents a message in a test conversation"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    role: str = ""  # "user" or "assistant"
    content: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestMetrics:
    """Performance metrics for a test"""
    response_time_ms: float = 0.0
    cultural_sensitivity_score: float = 0.0
    persona_consistency_score: float = 0.0
    language_accuracy_score: float = 0.0
    completion_rate: float = 0.0
    error_count: int = 0
    custom_metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "response_time_ms": self.response_time_ms,
            "cultural_sensitivity_score": self.cultural_sensitivity_score,
            "persona_consistency_score": self.persona_consistency_score,
            "language_accuracy_score": self.language_accuracy_score,
            "completion_rate": self.completion_rate,
            "error_count": self.error_count,
            "custom_metrics": self.custom_metrics
        }


@dataclass
class TestContext:
    """Context for running tests"""
    test_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    persona: Optional[PersonaConfig] = None
    cultural_region: Optional[CulturalRegion] = None
    language: str = "en"
    environment: str = "test"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class BaseTest(ABC):
    """Base class for all tests"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.status = TestStatus.PENDING
        self.result = None
        self.start_time = None
        self.end_time = None
        self.metrics = TestMetrics()
        self.errors: List[str] = []
        
    @abstractmethod
    async def setup(self) -> None:
        """Setup test environment"""
        pass
    
    @abstractmethod
    async def execute(self, context: TestContext) -> TestResult:
        """Execute the test"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup after test"""
        pass
    
    async def run(self, context: TestContext) -> TestResult:
        """Run the complete test lifecycle"""
        try:
            self.status = TestStatus.RUNNING
            self.start_time = time.time()
            
            await self.setup()
            self.result = await self.execute(context)
            
            self.status = TestStatus.COMPLETED
            return self.result
            
        except Exception as e:
            self.logger.error(f"Test failed: {str(e)}")
            self.errors.append(str(e))
            self.status = TestStatus.FAILED
            self.result = TestResult.ERROR
            return TestResult.ERROR
            
        finally:
            self.end_time = time.time()
            if self.start_time:
                self.metrics.response_time_ms = (self.end_time - self.start_time) * 1000
            await self.cleanup()
    
    def get_duration(self) -> float:
        """Get test duration in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0


class TestRunner:
    """Runs and manages tests"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.running_tests: Dict[str, BaseTest] = {}
        self.completed_tests: Dict[str, BaseTest] = {}
        self.semaphore = asyncio.Semaphore(config.max_concurrent_tests)
    
    async def run_test(self, test: BaseTest, context: TestContext) -> TestResult:
        """Run a single test with concurrency control"""
        async with self.semaphore:
            test_id = context.test_id
            self.running_tests[test_id] = test
            
            try:
                # Add timeout
                result = await asyncio.wait_for(
                    test.run(context),
                    timeout=self.config.test_timeout_seconds
                )
                return result
                
            except asyncio.TimeoutError:
                self.logger.error(f"Test {test_id} timed out")
                test.status = TestStatus.FAILED
                test.result = TestResult.ERROR
                test.errors.append("Test timed out")
                return TestResult.ERROR
                
            finally:
                if test_id in self.running_tests:
                    self.completed_tests[test_id] = self.running_tests.pop(test_id)
    
    async def run_tests(self, tests: List[BaseTest], contexts: List[TestContext]) -> List[TestResult]:
        """Run multiple tests concurrently"""
        if len(tests) != len(contexts):
            raise ValueError("Number of tests must match number of contexts")
        
        tasks = [
            self.run_test(test, context)
            for test, context in zip(tests, contexts)
        ]
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_test_status(self, test_id: str) -> Optional[TestStatus]:
        """Get status of a specific test"""
        if test_id in self.running_tests:
            return self.running_tests[test_id].status
        elif test_id in self.completed_tests:
            return self.completed_tests[test_id].status
        return None
    
    def get_test_metrics(self, test_id: str) -> Optional[TestMetrics]:
        """Get metrics for a specific test"""
        if test_id in self.running_tests:
            return self.running_tests[test_id].metrics
        elif test_id in self.completed_tests:
            return self.completed_tests[test_id].metrics
        return None


class MetricsCalculator:
    """Calculates various test metrics"""
    
    @staticmethod
    def calculate_cultural_sensitivity_score(
        messages: List[TestMessage],
        cultural_region: CulturalRegion,
        language: str
    ) -> float:
        """
        Calculate cultural sensitivity score based on:
        - Appropriate greetings and formalities
        - Cultural context awareness
        - Language usage
        - Religious/cultural considerations
        """
        if not messages:
            return 0.0
        
        score = 0.0
        total_checks = 0
        
        for message in messages:
            if message.role == "assistant":
                content = message.content.lower()
                
                # Check for appropriate greetings
                if any(greeting in content for greeting in ["peace", "salam", "hello", "good"]):
                    score += 1
                total_checks += 1
                
                # Check for respectful language
                if any(respect in content for respect in ["please", "kindly", "respectfully"]):
                    score += 1
                total_checks += 1
                
                # Check for cultural awareness
                if cultural_region in [CulturalRegion.SAUDI_ARABIA, CulturalRegion.UAE]:
                    if any(cultural in content for cultural in ["inshallah", "mashallah", "respected"]):
                        score += 1
                    total_checks += 1
        
        return score / total_checks if total_checks > 0 else 0.0
    
    @staticmethod
    def calculate_persona_consistency_score(
        messages: List[TestMessage],
        persona: PersonaConfig
    ) -> float:
        """
        Calculate how consistently the agent maintains its persona
        """
        if not messages or not persona:
            return 0.0
        
        score = 0.0
        total_checks = 0
        
        for message in messages:
            if message.role == "assistant":
                content = message.content.lower()
                
                # Check communication style consistency
                if persona.communication_style.get("formality", 0) > 0.7:
                    if any(formal in content for formal in ["sir", "madam", "respectfully", "kindly"]):
                        score += 1
                    total_checks += 1
                
                # Check personality traits
                if persona.personality_traits.get("helpfulness", 0) > 0.8:
                    if any(helpful in content for helpful in ["help", "assist", "support", "glad"]):
                        score += 1
                    total_checks += 1
        
        return score / total_checks if total_checks > 0 else 0.0
    
    @staticmethod
    def calculate_language_accuracy_score(
        messages: List[TestMessage],
        expected_language: str
    ) -> float:
        """
        Calculate language accuracy and appropriateness
        """
        if not messages:
            return 0.0
        
        # Simple heuristic - in a real implementation, you'd use NLP libraries
        # to detect language and grammar accuracy
        assistant_messages = [m for m in messages if m.role == "assistant"]
        if not assistant_messages:
            return 0.0
        
        # Basic checks for now
        score = 1.0  # Start with perfect score
        
        for message in assistant_messages:
            content = message.content
            
            # Check for obvious issues
            if not content.strip():
                score -= 0.1
            elif len(content.split()) < 3:  # Too short responses
                score -= 0.05
            elif content.isupper():  # All caps
                score -= 0.1
        
        return max(0.0, min(1.0, score))


# Utility functions
async def wait_for_condition(
    condition_func,
    timeout: float = 30.0,
    interval: float = 0.1
) -> bool:
    """Wait for a condition to become true"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if await condition_func():
            return True
        await asyncio.sleep(interval)
    return False


def generate_test_id() -> str:
    """Generate a unique test ID"""
    return f"test_{uuid.uuid4().hex[:8]}_{int(time.time())}"


def generate_session_id() -> str:
    """Generate a unique session ID"""
    return f"session_{uuid.uuid4().hex[:8]}"