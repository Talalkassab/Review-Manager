"""
Scenario Testing Framework
=========================

Comprehensive framework for testing agent performance across various scenarios
with predefined test cases, batch testing, and automated evaluation.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from ..database import get_db
from .models import TestScenario, TestSession, TestConversation
from .schemas import (
    TestScenarioCreate, TestScenarioResponse, ConversationStep,
    SuccessCriteria, ScenarioTestResult, BatchTestRequest, BatchTestResult,
    CustomerProfileType, TestMessage
)
from .customer_simulator import CustomerProfileSimulator
from .conversation_playground import ConversationPlaygroundAPI

router = APIRouter(prefix="/testing/scenarios", tags=["scenario-testing"])

class ScenarioEvaluator:
    """Evaluates test scenario performance against success criteria"""
    
    def __init__(self):
        self.evaluation_functions = {
            "response_time": self._evaluate_response_time,
            "sentiment_score": self._evaluate_sentiment_score,
            "cultural_sensitivity": self._evaluate_cultural_sensitivity,
            "persona_consistency": self._evaluate_persona_consistency,
            "language_appropriateness": self._evaluate_language_appropriateness,
            "contains_keywords": self._evaluate_contains_keywords,
            "avoids_keywords": self._evaluate_avoids_keywords,
            "tone_match": self._evaluate_tone_match,
            "response_length": self._evaluate_response_length,
            "escalation_appropriateness": self._evaluate_escalation_appropriateness
        }

    async def evaluate_scenario_result(
        self,
        conversation_messages: List[Dict[str, Any]],
        success_criteria: List[SuccessCriteria],
        expected_behaviors: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Evaluate scenario performance against criteria"""
        
        results = {
            "criteria_results": [],
            "overall_score": 0.0,
            "passed": False,
            "failure_reasons": [],
            "recommendations": []
        }
        
        total_weight = 0
        weighted_score = 0
        
        for criteria in success_criteria:
            evaluation = await self._evaluate_single_criteria(
                conversation_messages, criteria
            )
            
            results["criteria_results"].append({
                "criteria_name": criteria.criteria_name,
                "criteria_type": criteria.criteria_type,
                "target_value": criteria.target_value,
                "actual_value": evaluation["actual_value"],
                "passed": evaluation["passed"],
                "score": evaluation["score"],
                "details": evaluation["details"]
            })
            
            # Calculate weighted score
            total_weight += criteria.weight
            weighted_score += evaluation["score"] * criteria.weight
            
            if not evaluation["passed"]:
                results["failure_reasons"].append(
                    f"{criteria.criteria_name}: {evaluation['details']}"
                )
        
        # Calculate overall score
        if total_weight > 0:
            results["overall_score"] = weighted_score / total_weight
        
        # Determine if scenario passed (threshold: 70%)
        results["passed"] = results["overall_score"] >= 0.7
        
        # Generate recommendations
        results["recommendations"] = await self._generate_recommendations(
            results["criteria_results"], expected_behaviors
        )
        
        return results

    async def _evaluate_single_criteria(
        self,
        conversation_messages: List[Dict[str, Any]],
        criteria: SuccessCriteria
    ) -> Dict[str, Any]:
        """Evaluate a single success criteria"""
        
        evaluation_func = self.evaluation_functions.get(criteria.criteria_type)
        
        if not evaluation_func:
            return {
                "actual_value": None,
                "passed": False,
                "score": 0.0,
                "details": f"Unknown criteria type: {criteria.criteria_type}"
            }
        
        return await evaluation_func(conversation_messages, criteria)

    async def _evaluate_response_time(
        self, 
        messages: List[Dict[str, Any]], 
        criteria: SuccessCriteria
    ) -> Dict[str, Any]:
        """Evaluate agent response time"""
        
        agent_messages = [m for m in messages if m.get("sender") == "agent"]
        
        if not agent_messages:
            return {
                "actual_value": None,
                "passed": False,
                "score": 0.0,
                "details": "No agent messages found"
            }
        
        response_times = [
            m.get("response_time_seconds", 0) for m in agent_messages
        ]
        avg_response_time = sum(response_times) / len(response_times)
        target_time = float(criteria.target_value)
        
        passed = avg_response_time <= target_time
        score = min(1.0, target_time / max(avg_response_time, 0.1))
        
        return {
            "actual_value": avg_response_time,
            "passed": passed,
            "score": score,
            "details": f"Average response time: {avg_response_time:.2f}s (target: {target_time}s)"
        }

    async def _evaluate_sentiment_score(
        self, 
        messages: List[Dict[str, Any]], 
        criteria: SuccessCriteria
    ) -> Dict[str, Any]:
        """Evaluate sentiment score of agent messages"""
        
        agent_messages = [m for m in messages if m.get("sender") == "agent"]
        
        if not agent_messages:
            return {
                "actual_value": None,
                "passed": False,
                "score": 0.0,
                "details": "No agent messages found"
            }
        
        # Mock sentiment analysis - replace with actual implementation
        sentiment_scores = [
            m.get("metadata", {}).get("sentiment_score", 0.5) 
            for m in agent_messages
        ]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        target_sentiment = float(criteria.target_value)
        
        passed = avg_sentiment >= target_sentiment
        score = min(1.0, avg_sentiment / target_sentiment)
        
        return {
            "actual_value": avg_sentiment,
            "passed": passed,
            "score": score,
            "details": f"Average sentiment: {avg_sentiment:.2f} (target: {target_sentiment})"
        }

    async def _evaluate_cultural_sensitivity(
        self, 
        messages: List[Dict[str, Any]], 
        criteria: SuccessCriteria
    ) -> Dict[str, Any]:
        """Evaluate cultural sensitivity of agent responses"""
        
        agent_messages = [m for m in messages if m.get("sender") == "agent"]
        
        if not agent_messages:
            return {
                "actual_value": None,
                "passed": False,
                "score": 0.0,
                "details": "No agent messages found"
            }
        
        # Mock cultural sensitivity scoring - replace with actual implementation
        cultural_scores = [
            m.get("metadata", {}).get("cultural_sensitivity", 0.8) 
            for m in agent_messages
        ]
        avg_cultural_score = sum(cultural_scores) / len(cultural_scores)
        target_score = float(criteria.target_value)
        
        passed = avg_cultural_score >= target_score
        score = min(1.0, avg_cultural_score / target_score)
        
        return {
            "actual_value": avg_cultural_score,
            "passed": passed,
            "score": score,
            "details": f"Cultural sensitivity: {avg_cultural_score:.2f} (target: {target_score})"
        }

    async def _evaluate_persona_consistency(
        self, 
        messages: List[Dict[str, Any]], 
        criteria: SuccessCriteria
    ) -> Dict[str, Any]:
        """Evaluate persona consistency across messages"""
        
        agent_messages = [m for m in messages if m.get("sender") == "agent"]
        
        if not agent_messages:
            return {
                "actual_value": None,
                "passed": False,
                "score": 0.0,
                "details": "No agent messages found"
            }
        
        # Mock persona consistency scoring
        consistency_scores = [
            m.get("metadata", {}).get("persona_consistency", 0.9) 
            for m in agent_messages
        ]
        avg_consistency = sum(consistency_scores) / len(consistency_scores)
        target_consistency = float(criteria.target_value)
        
        passed = avg_consistency >= target_consistency
        score = min(1.0, avg_consistency / target_consistency)
        
        return {
            "actual_value": avg_consistency,
            "passed": passed,
            "score": score,
            "details": f"Persona consistency: {avg_consistency:.2f} (target: {target_consistency})"
        }

    async def _evaluate_language_appropriateness(
        self, 
        messages: List[Dict[str, Any]], 
        criteria: SuccessCriteria
    ) -> Dict[str, Any]:
        """Evaluate language appropriateness"""
        
        agent_messages = [m for m in messages if m.get("sender") == "agent"]
        target_language = str(criteria.target_value).lower()
        
        if not agent_messages:
            return {
                "actual_value": None,
                "passed": False,
                "score": 0.0,
                "details": "No agent messages found"
            }
        
        correct_language_count = sum(
            1 for m in agent_messages 
            if m.get("language", "").lower() == target_language
        )
        
        language_accuracy = correct_language_count / len(agent_messages)
        passed = language_accuracy >= 0.9  # 90% threshold
        score = language_accuracy
        
        return {
            "actual_value": language_accuracy,
            "passed": passed,
            "score": score,
            "details": f"Language accuracy: {language_accuracy:.2%} for {target_language}"
        }

    async def _evaluate_contains_keywords(
        self, 
        messages: List[Dict[str, Any]], 
        criteria: SuccessCriteria
    ) -> Dict[str, Any]:
        """Evaluate if messages contain required keywords"""
        
        agent_messages = [m for m in messages if m.get("sender") == "agent"]
        required_keywords = criteria.target_value if isinstance(criteria.target_value, list) else [criteria.target_value]
        
        if not agent_messages:
            return {
                "actual_value": None,
                "passed": False,
                "score": 0.0,
                "details": "No agent messages found"
            }
        
        all_content = " ".join([m.get("content", "").lower() for m in agent_messages])
        
        found_keywords = [
            keyword for keyword in required_keywords 
            if str(keyword).lower() in all_content
        ]
        
        keyword_coverage = len(found_keywords) / len(required_keywords)
        passed = keyword_coverage >= 0.8  # 80% of keywords must be present
        score = keyword_coverage
        
        return {
            "actual_value": found_keywords,
            "passed": passed,
            "score": score,
            "details": f"Found {len(found_keywords)}/{len(required_keywords)} required keywords"
        }

    async def _evaluate_avoids_keywords(
        self, 
        messages: List[Dict[str, Any]], 
        criteria: SuccessCriteria
    ) -> Dict[str, Any]:
        """Evaluate if messages avoid forbidden keywords"""
        
        agent_messages = [m for m in messages if m.get("sender") == "agent"]
        forbidden_keywords = criteria.target_value if isinstance(criteria.target_value, list) else [criteria.target_value]
        
        if not agent_messages:
            return {
                "actual_value": None,
                "passed": True,
                "score": 1.0,
                "details": "No agent messages found"
            }
        
        all_content = " ".join([m.get("content", "").lower() for m in agent_messages])
        
        found_forbidden = [
            keyword for keyword in forbidden_keywords 
            if str(keyword).lower() in all_content
        ]
        
        passed = len(found_forbidden) == 0
        score = 1.0 if passed else 0.0
        
        return {
            "actual_value": found_forbidden,
            "passed": passed,
            "score": score,
            "details": f"Found {len(found_forbidden)} forbidden keywords: {found_forbidden}"
        }

    async def _evaluate_tone_match(
        self, 
        messages: List[Dict[str, Any]], 
        criteria: SuccessCriteria
    ) -> Dict[str, Any]:
        """Evaluate if message tone matches expected tone"""
        
        agent_messages = [m for m in messages if m.get("sender") == "agent"]
        expected_tone = str(criteria.target_value).lower()
        
        if not agent_messages:
            return {
                "actual_value": None,
                "passed": False,
                "score": 0.0,
                "details": "No agent messages found"
            }
        
        # Mock tone analysis - replace with actual implementation
        correct_tone_count = sum(
            1 for m in agent_messages 
            if m.get("metadata", {}).get("tone", "").lower() == expected_tone
        )
        
        tone_accuracy = correct_tone_count / len(agent_messages)
        passed = tone_accuracy >= 0.8  # 80% threshold
        score = tone_accuracy
        
        return {
            "actual_value": tone_accuracy,
            "passed": passed,
            "score": score,
            "details": f"Tone accuracy: {tone_accuracy:.2%} for {expected_tone} tone"
        }

    async def _evaluate_response_length(
        self, 
        messages: List[Dict[str, Any]], 
        criteria: SuccessCriteria
    ) -> Dict[str, Any]:
        """Evaluate if response length is appropriate"""
        
        agent_messages = [m for m in messages if m.get("sender") == "agent"]
        
        if not agent_messages:
            return {
                "actual_value": None,
                "passed": False,
                "score": 0.0,
                "details": "No agent messages found"
            }
        
        avg_length = sum(len(m.get("content", "")) for m in agent_messages) / len(agent_messages)
        target_length = float(criteria.target_value)
        
        # Score based on how close to target length
        length_diff = abs(avg_length - target_length) / target_length
        score = max(0.0, 1.0 - length_diff)
        passed = length_diff <= 0.3  # Within 30% of target
        
        return {
            "actual_value": avg_length,
            "passed": passed,
            "score": score,
            "details": f"Average length: {avg_length:.0f} chars (target: {target_length:.0f})"
        }

    async def _evaluate_escalation_appropriateness(
        self, 
        messages: List[Dict[str, Any]], 
        criteria: SuccessCriteria
    ) -> Dict[str, Any]:
        """Evaluate if escalation decisions are appropriate"""
        
        # Look for escalation indicators in conversation
        escalation_needed = bool(criteria.target_value)
        
        escalation_keywords = ["manager", "supervisor", "escalate", "transfer", "مدير", "مشرف"]
        all_content = " ".join([m.get("content", "").lower() for m in messages])
        
        escalation_mentioned = any(keyword in all_content for keyword in escalation_keywords)
        
        if escalation_needed:
            passed = escalation_mentioned
            score = 1.0 if passed else 0.0
            details = "Escalation was appropriately suggested" if passed else "Escalation needed but not suggested"
        else:
            passed = not escalation_mentioned
            score = 1.0 if passed else 0.0
            details = "No unnecessary escalation" if passed else "Unnecessary escalation suggested"
        
        return {
            "actual_value": escalation_mentioned,
            "passed": passed,
            "score": score,
            "details": details
        }

    async def _generate_recommendations(
        self,
        criteria_results: List[Dict[str, Any]],
        expected_behaviors: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate improvement recommendations based on results"""
        
        recommendations = []
        
        for result in criteria_results:
            if not result["passed"]:
                criteria_type = result.get("criteria_type", "")
                
                if criteria_type == "response_time":
                    recommendations.append(
                        "Optimize agent response time by streamlining decision-making logic"
                    )
                elif criteria_type == "sentiment_score":
                    recommendations.append(
                        "Improve message sentiment by using more positive language and empathy"
                    )
                elif criteria_type == "cultural_sensitivity":
                    recommendations.append(
                        "Enhance cultural sensitivity training and context awareness"
                    )
                elif criteria_type == "persona_consistency":
                    recommendations.append(
                        "Review persona guidelines and ensure consistent application"
                    )
                elif criteria_type == "language_appropriateness":
                    recommendations.append(
                        "Improve language detection and selection mechanisms"
                    )
                elif criteria_type == "contains_keywords":
                    recommendations.append(
                        f"Ensure agent includes required keywords: {result.get('details', '')}"
                    )
                elif criteria_type == "avoids_keywords":
                    recommendations.append(
                        f"Train agent to avoid inappropriate language: {result.get('details', '')}"
                    )
        
        # Add general recommendations if overall performance is poor
        overall_passed = sum(1 for r in criteria_results if r["passed"])
        total_criteria = len(criteria_results)
        
        if total_criteria > 0 and (overall_passed / total_criteria) < 0.5:
            recommendations.append(
                "Consider comprehensive agent retraining or persona adjustment"
            )
        
        return recommendations

class ScenarioTestingFramework:
    """Main scenario testing framework"""
    
    def __init__(self):
        self.evaluator = ScenarioEvaluator()
        self.customer_simulator = CustomerProfileSimulator()
        self.playground = ConversationPlaygroundAPI()
        
        # Predefined scenarios
        self.predefined_scenarios = self._initialize_predefined_scenarios()

    def _initialize_predefined_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """Initialize predefined test scenarios"""
        
        return {
            "happy_customer_feedback": {
                "scenario_name": "Happy Customer Feedback Collection",
                "scenario_type": "customer_service",
                "difficulty_level": "easy",
                "description": "Test agent's ability to collect positive feedback",
                "customer_profile": {
                    "profile_type": CustomerProfileType.HAPPY_CUSTOMER,
                    "demographics": {
                        "language_preference": "arabic",
                        "cultural_background": "gulf"
                    }
                },
                "conversation_steps": [
                    {
                        "step_number": 1,
                        "customer_message": {
                            "text": "مرحباً، كان الطعام ممتاز!",
                            "sentiment": "positive"
                        },
                        "expected_agent_response_criteria": {
                            "should_contain": ["شكر", "سعيد", "تقييم"],
                            "tone_should_be": "friendly",
                            "language_should_be": "arabic"
                        }
                    }
                ],
                "success_criteria": [
                    {
                        "criteria_name": "Response Time",
                        "criteria_type": "response_time",
                        "target_value": 3.0,
                        "weight": 0.3
                    },
                    {
                        "criteria_name": "Cultural Sensitivity",
                        "criteria_type": "cultural_sensitivity", 
                        "target_value": 0.9,
                        "weight": 0.4
                    },
                    {
                        "criteria_name": "Contains Thank You",
                        "criteria_type": "contains_keywords",
                        "target_value": ["شكر", "أقدر"],
                        "weight": 0.3
                    }
                ]
            },
            
            "complaint_resolution": {
                "scenario_name": "Complaint Resolution",
                "scenario_type": "complaint_handling",
                "difficulty_level": "hard",
                "description": "Test agent's ability to handle customer complaints",
                "customer_profile": {
                    "profile_type": CustomerProfileType.COMPLAINT_CUSTOMER,
                    "demographics": {
                        "language_preference": "arabic",
                        "cultural_background": "gulf"
                    }
                },
                "conversation_steps": [
                    {
                        "step_number": 1,
                        "customer_message": {
                            "text": "الطعام وصل بارد والخدمة سيئة!",
                            "sentiment": "negative"
                        },
                        "expected_agent_response_criteria": {
                            "should_contain": ["آسف", "اعتذار", "حل"],
                            "should_not_contain": ["غلط", "خطأ"],
                            "tone_should_be": "apologetic",
                            "response_time_max_seconds": 2
                        }
                    },
                    {
                        "step_number": 2,
                        "customer_message": {
                            "text": "هذا غير مقبول! أريد حلاً فورياً",
                            "sentiment": "angry"
                        },
                        "expected_agent_response_criteria": {
                            "should_contain": ["مدير", "تعويض", "حل فوري"],
                            "tone_should_be": "professional",
                            "escalation_needed": True
                        }
                    }
                ],
                "success_criteria": [
                    {
                        "criteria_name": "Apology Present",
                        "criteria_type": "contains_keywords",
                        "target_value": ["آسف", "اعتذار", "أسف"],
                        "weight": 0.3
                    },
                    {
                        "criteria_name": "Escalation Offered",
                        "criteria_type": "escalation_appropriateness",
                        "target_value": True,
                        "weight": 0.4
                    },
                    {
                        "criteria_name": "Avoids Blame",
                        "criteria_type": "avoids_keywords", 
                        "target_value": ["غلط", "خطأ", "ذنب"],
                        "weight": 0.3
                    }
                ]
            },
            
            "first_time_visitor": {
                "scenario_name": "First Time Visitor Welcome",
                "scenario_type": "customer_onboarding",
                "difficulty_level": "medium",
                "description": "Test agent's ability to welcome and guide first-time visitors",
                "customer_profile": {
                    "profile_type": CustomerProfileType.FIRST_TIME_VISITOR,
                    "demographics": {
                        "language_preference": "english",
                        "cultural_background": "international"
                    }
                },
                "conversation_steps": [
                    {
                        "step_number": 1,
                        "customer_message": {
                            "text": "Hi, this is my first time here. What do you recommend?",
                            "sentiment": "neutral"
                        },
                        "expected_agent_response_criteria": {
                            "should_contain": ["welcome", "recommend", "popular"],
                            "tone_should_be": "helpful",
                            "language_should_be": "english"
                        }
                    }
                ],
                "success_criteria": [
                    {
                        "criteria_name": "Welcome Message",
                        "criteria_type": "contains_keywords",
                        "target_value": ["welcome", "glad", "happy"],
                        "weight": 0.4
                    },
                    {
                        "criteria_name": "Recommendations Provided",
                        "criteria_type": "contains_keywords",
                        "target_value": ["recommend", "popular", "suggest"],
                        "weight": 0.6
                    }
                ]
            }
        }

    async def create_scenario(
        self, 
        scenario_data: TestScenarioCreate, 
        db: Session
    ) -> TestScenarioResponse:
        """Create a new test scenario"""
        
        db_scenario = TestScenario(
            scenario_name=scenario_data.scenario_name,
            scenario_type=scenario_data.scenario_type,
            difficulty_level=scenario_data.difficulty_level,
            description=scenario_data.description,
            customer_profile=scenario_data.customer_profile.dict(),
            conversation_steps=[step.dict() for step in scenario_data.conversation_steps],
            success_criteria=[criteria.dict() for criteria in scenario_data.success_criteria],
            expected_behaviors=[behavior for behavior in scenario_data.expected_behaviors],
            tags=scenario_data.tags or [],
            created_by="system"
        )
        
        db.add(db_scenario)
        db.commit()
        db.refresh(db_scenario)
        
        return TestScenarioResponse.from_orm(db_scenario)

    async def run_scenario_test(
        self,
        scenario_id: int,
        agent_persona_id: str,
        db: Session
    ) -> ScenarioTestResult:
        """Run a single scenario test"""
        
        # Get scenario
        scenario = db.query(TestScenario).filter(TestScenario.id == scenario_id).first()
        if not scenario:
            raise HTTPException(status_code=404, detail="Test scenario not found")
        
        # Create test session
        from .schemas import TestSessionCreate, TestScenarioType
        session_data = TestSessionCreate(
            session_name=f"Scenario Test: {scenario.scenario_name}",
            session_type=TestScenarioType.SCENARIO,
            agent_persona_id=agent_persona_id,
            test_parameters={"scenario_id": scenario_id}
        )
        
        test_session = await self.playground.create_test_session(session_data, db)
        
        # Create customer profile
        profile_config = scenario.customer_profile
        customer_profile = await self.customer_simulator.create_customer_profile(
            profile_type=CustomerProfileType(profile_config["profile_type"]),
            demographics=profile_config.get("demographics"),
            context=profile_config
        )
        
        # Run conversation steps
        conversation_messages = []
        
        for step in scenario.conversation_steps:
            step_data = step if isinstance(step, dict) else step
            
            # Send customer message
            customer_message = TestMessage(
                message_id=f"step_{step_data['step_number']}_customer",
                sender="customer",
                content=step_data["customer_message"]["text"],
                timestamp=datetime.utcnow(),
                sentiment=step_data["customer_message"].get("sentiment")
            )
            
            conversation_messages.append(customer_message.dict())
            
            # Get agent response (mock implementation)
            agent_response = await self._get_agent_response(
                customer_message.content, 
                agent_persona_id, 
                conversation_messages
            )
            
            conversation_messages.append(agent_response)
            
            # Simulate delay
            await asyncio.sleep(0.1)
        
        # Evaluate results
        success_criteria = [
            SuccessCriteria(**criteria) if isinstance(criteria, dict) else criteria
            for criteria in scenario.success_criteria
        ]
        
        evaluation = await self.evaluator.evaluate_scenario_result(
            conversation_messages,
            success_criteria,
            scenario.expected_behaviors
        )
        
        # Create result
        result = ScenarioTestResult(
            scenario_id=scenario_id,
            session_id=test_session.id,
            test_start=test_session.start_time,
            test_end=datetime.utcnow(),
            passed=evaluation["passed"],
            score=evaluation["overall_score"],
            criteria_results=evaluation["criteria_results"],
            failure_reasons=evaluation["failure_reasons"] if evaluation["failure_reasons"] else None,
            recommendations=evaluation["recommendations"] if evaluation["recommendations"] else None
        )
        
        # Update scenario usage
        scenario.usage_count += 1
        db.commit()
        
        return result

    async def _get_agent_response(
        self,
        customer_message: str,
        agent_persona_id: str,
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get agent response (mock implementation - replace with actual CrewAI integration)"""
        
        # Mock agent response based on message content
        message_lower = customer_message.lower()
        
        if any(word in message_lower for word in ["ممتاز", "رائع", "excellent", "great"]):
            response_content = "شكراً لكم على تقييمكم الإيجابي! نسعد بخدمتكم دائماً."
            sentiment_score = 0.9
        elif any(word in message_lower for word in ["بارد", "سيئة", "cold", "bad"]):
            response_content = "أعتذر بشدة عن هذه التجربة. سأقوم بتحويلكم للمدير لحل هذه المشكلة فوراً."
            sentiment_score = 0.7
        elif any(word in message_lower for word in ["أول مرة", "first time", "recommend"]):
            response_content = "أهلاً وسهلاً بكم! أنصحكم بتجربة الأطباق الشعبية لدينا."
            sentiment_score = 0.85
        else:
            response_content = "شكراً لتواصلكم معنا. كيف يمكنني مساعدتكم؟"
            sentiment_score = 0.8
        
        return {
            "message_id": f"agent_{datetime.utcnow().timestamp()}",
            "sender": "agent",
            "content": response_content,
            "timestamp": datetime.utcnow().isoformat(),
            "language": "arabic",
            "response_time_seconds": 1.5,
            "metadata": {
                "sentiment_score": sentiment_score,
                "cultural_sensitivity": 0.95,
                "persona_consistency": 0.9,
                "tone": "friendly"
            }
        }

    async def run_batch_tests(
        self,
        batch_request: BatchTestRequest,
        agent_persona_id: str,
        db: Session
    ) -> BatchTestResult:
        """Run multiple scenario tests in batch"""
        
        batch_id = f"batch_{datetime.utcnow().timestamp()}"
        start_time = datetime.utcnow()
        
        results = []
        
        if batch_request.parallel_execution:
            # Run tests in parallel (limited concurrency)
            semaphore = asyncio.Semaphore(batch_request.max_parallel_tests)
            
            async def run_single_test(scenario_id: int):
                async with semaphore:
                    try:
                        return await self.run_scenario_test(scenario_id, agent_persona_id, db)
                    except Exception as e:
                        return {
                            "scenario_id": scenario_id,
                            "error": str(e),
                            "passed": False,
                            "score": 0.0
                        }
            
            tasks = [run_single_test(sid) for sid in batch_request.scenarios]
            results = await asyncio.gather(*tasks)
        else:
            # Run tests sequentially
            for scenario_id in batch_request.scenarios:
                try:
                    result = await self.run_scenario_test(scenario_id, agent_persona_id, db)
                    results.append(result)
                except Exception as e:
                    results.append({
                        "scenario_id": scenario_id,
                        "error": str(e),
                        "passed": False,
                        "score": 0.0
                    })
        
        # Calculate summary
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()
        
        passed_tests = sum(1 for r in results if getattr(r, 'passed', False))
        failed_tests = len(results) - passed_tests
        
        return BatchTestResult(
            batch_id=batch_id,
            total_tests=len(results),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            execution_time_seconds=execution_time,
            individual_results=[
                result.dict() if hasattr(result, 'dict') else result 
                for result in results
            ]
        )

    async def get_predefined_scenarios(self) -> List[Dict[str, Any]]:
        """Get list of predefined test scenarios"""
        
        scenarios = []
        for key, scenario_data in self.predefined_scenarios.items():
            scenarios.append({
                "key": key,
                **scenario_data
            })
        
        return scenarios

    async def create_predefined_scenario(
        self, 
        scenario_key: str, 
        db: Session
    ) -> TestScenarioResponse:
        """Create a predefined scenario in database"""
        
        if scenario_key not in self.predefined_scenarios:
            raise HTTPException(status_code=404, detail="Predefined scenario not found")
        
        scenario_data = self.predefined_scenarios[scenario_key]
        
        # Convert to creation schema
        from .schemas import CustomerProfileSimulatorConfig, CustomerDemographics, CustomerBehavioralTraits, VisitContext
        
        profile_data = scenario_data["customer_profile"]
        customer_profile = CustomerProfileSimulatorConfig(
            demographics=CustomerDemographics(**profile_data.get("demographics", {})),
            behavioral_traits=CustomerBehavioralTraits(
                communication_style="polite",
                response_speed="immediate",
                sentiment_baseline="neutral",
                complaint_likelihood=0.3
            ),
            visit_context=VisitContext(
                visit_type="repeat",
                order_value=100.0,
                dining_experience="average"
            )
        )
        
        scenario_create = TestScenarioCreate(
            scenario_name=scenario_data["scenario_name"],
            scenario_type=scenario_data["scenario_type"],
            difficulty_level=scenario_data["difficulty_level"],
            description=scenario_data["description"],
            customer_profile=customer_profile,
            conversation_steps=[
                ConversationStep(**step) for step in scenario_data["conversation_steps"]
            ],
            success_criteria=[
                SuccessCriteria(**criteria) for criteria in scenario_data["success_criteria"]
            ],
            expected_behaviors=scenario_data.get("expected_behaviors", []),
            tags=scenario_data.get("tags")
        )
        
        return await self.create_scenario(scenario_create, db)

# Initialize framework instance
framework = ScenarioTestingFramework()

# API Routes
@router.post("/scenarios", response_model=TestScenarioResponse)
async def create_scenario(
    scenario_data: TestScenarioCreate,
    db: Session = Depends(get_db)
):
    """Create a new test scenario"""
    return await framework.create_scenario(scenario_data, db)

@router.get("/scenarios", response_model=List[TestScenarioResponse])
async def list_scenarios(
    scenario_type: Optional[str] = None,
    difficulty_level: Optional[str] = None,
    tags: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List test scenarios with filtering"""
    
    query = db.query(TestScenario).filter(TestScenario.is_active == True)
    
    if scenario_type:
        query = query.filter(TestScenario.scenario_type == scenario_type)
    
    if difficulty_level:
        query = query.filter(TestScenario.difficulty_level == difficulty_level)
    
    if tags:
        # Simple tag filtering (can be enhanced with proper JSON querying)
        tag_list = [tag.strip() for tag in tags.split(",")]
        for tag in tag_list:
            query = query.filter(TestScenario.tags.contains([tag]))
    
    scenarios = query.order_by(desc(TestScenario.usage_count)).offset(offset).limit(limit).all()
    
    return [TestScenarioResponse.from_orm(scenario) for scenario in scenarios]

@router.get("/scenarios/{scenario_id}", response_model=TestScenarioResponse)
async def get_scenario(
    scenario_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific test scenario"""
    
    scenario = db.query(TestScenario).filter(TestScenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Test scenario not found")
    
    return TestScenarioResponse.from_orm(scenario)

@router.post("/scenarios/{scenario_id}/run")
async def run_scenario(
    scenario_id: int,
    agent_persona_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Run a single scenario test"""
    
    result = await framework.run_scenario_test(scenario_id, agent_persona_id, db)
    return result

@router.post("/batch-test")
async def run_batch_test(
    batch_request: BatchTestRequest,
    agent_persona_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Run multiple scenario tests in batch"""
    
    result = await framework.run_batch_tests(batch_request, agent_persona_id, db)
    return result

@router.get("/predefined-scenarios")
async def get_predefined_scenarios():
    """Get list of predefined test scenarios"""
    
    return await framework.get_predefined_scenarios()

@router.post("/predefined-scenarios/{scenario_key}", response_model=TestScenarioResponse)
async def create_predefined_scenario(
    scenario_key: str,
    db: Session = Depends(get_db)
):
    """Create a predefined scenario in database"""
    
    return await framework.create_predefined_scenario(scenario_key, db)

@router.delete("/scenarios/{scenario_id}")
async def deactivate_scenario(
    scenario_id: int,
    db: Session = Depends(get_db)
):
    """Deactivate a test scenario"""
    
    scenario = db.query(TestScenario).filter(TestScenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Test scenario not found")
    
    scenario.is_active = False
    db.commit()
    
    return {"message": "Scenario deactivated successfully"}