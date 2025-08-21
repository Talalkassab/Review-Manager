"""
A/B Testing Dashboard Backend
============================

Comprehensive A/B testing system for agent messaging with statistical analysis,
real-time monitoring, and automated winner detection.
"""

import numpy as np
import scipy.stats as stats
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_

from ..database import get_db
from .models import ABTest, TestSession
from .schemas import (
    ABTestCreate, ABTestResponse, MessageVariant, ABTestMetrics,
    VariantResult, StatisticalAnalysis, TestSessionStatus
)

router = APIRouter(prefix="/testing/ab-testing", tags=["ab-testing"])

class StatisticalAnalyzer:
    """Statistical analysis engine for A/B testing"""
    
    @staticmethod
    def calculate_z_test(
        control_conversions: int, 
        control_visitors: int,
        treatment_conversions: int, 
        treatment_visitors: int
    ) -> Dict[str, float]:
        """Calculate Z-test for two proportions"""
        
        if control_visitors == 0 or treatment_visitors == 0:
            return {
                "z_score": 0.0,
                "p_value": 1.0,
                "confidence_level": 0.0,
                "significant": False
            }
        
        # Conversion rates
        p1 = control_conversions / control_visitors
        p2 = treatment_conversions / treatment_visitors
        
        # Pooled proportion
        p_pooled = (control_conversions + treatment_conversions) / (control_visitors + treatment_visitors)
        
        # Standard error
        se = np.sqrt(p_pooled * (1 - p_pooled) * (1/control_visitors + 1/treatment_visitors))
        
        if se == 0:
            return {
                "z_score": 0.0,
                "p_value": 1.0,
                "confidence_level": 0.0,
                "significant": False
            }
        
        # Z-score
        z_score = (p2 - p1) / se
        
        # Two-tailed p-value
        p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
        
        # Confidence level
        confidence_level = 1 - p_value
        
        return {
            "z_score": float(z_score),
            "p_value": float(p_value),
            "confidence_level": float(confidence_level),
            "significant": p_value < 0.05
        }
    
    @staticmethod
    def calculate_confidence_interval(
        conversions: int, 
        visitors: int, 
        confidence_level: float = 0.95
    ) -> Tuple[float, float]:
        """Calculate confidence interval for conversion rate"""
        
        if visitors == 0:
            return (0.0, 0.0)
        
        p = conversions / visitors
        z = stats.norm.ppf(1 - (1 - confidence_level) / 2)
        
        se = np.sqrt(p * (1 - p) / visitors)
        margin_error = z * se
        
        lower = max(0, p - margin_error)
        upper = min(1, p + margin_error)
        
        return (float(lower), float(upper))
    
    @staticmethod
    def calculate_effect_size(
        control_conversions: int,
        control_visitors: int,
        treatment_conversions: int,
        treatment_visitors: int
    ) -> float:
        """Calculate Cohen's h effect size for proportions"""
        
        if control_visitors == 0 or treatment_visitors == 0:
            return 0.0
        
        p1 = control_conversions / control_visitors
        p2 = treatment_conversions / treatment_visitors
        
        # Cohen's h
        h = 2 * (np.arcsin(np.sqrt(p2)) - np.arcsin(np.sqrt(p1)))
        
        return float(h)
    
    @staticmethod
    def calculate_sample_size(
        baseline_rate: float,
        minimum_detectable_effect: float,
        power: float = 0.8,
        significance_level: float = 0.05
    ) -> int:
        """Calculate required sample size for A/B test"""
        
        # Effect size
        p1 = baseline_rate
        p2 = baseline_rate * (1 + minimum_detectable_effect)
        
        # Z-scores for power and significance
        z_alpha = stats.norm.ppf(1 - significance_level / 2)
        z_beta = stats.norm.ppf(power)
        
        # Pooled proportion
        p_pooled = (p1 + p2) / 2
        
        # Sample size calculation
        numerator = (z_alpha * np.sqrt(2 * p_pooled * (1 - p_pooled)) + 
                    z_beta * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
        denominator = (p2 - p1) ** 2
        
        n = numerator / denominator
        
        return int(np.ceil(n))

class ABTestingDashboard:
    """Main A/B testing dashboard backend"""
    
    def __init__(self):
        self.statistical_analyzer = StatisticalAnalyzer()
        self.active_tests: Dict[int, Dict[str, Any]] = {}

    async def create_ab_test(
        self, 
        test_data: ABTestCreate, 
        db: Session
    ) -> ABTestResponse:
        """Create a new A/B test"""
        
        # Validate variants weights sum to 1.0
        total_weight = sum(variant.weight for variant in test_data.variants)
        if abs(total_weight - 1.0) > 0.01:
            raise HTTPException(
                status_code=400, 
                detail=f"Variant weights must sum to 1.0, got {total_weight}"
            )
        
        # Verify session exists
        session = db.query(TestSession).filter(TestSession.id == test_data.session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Test session not found")
        
        # Create A/B test
        db_test = ABTest(
            session_id=test_data.session_id,
            test_name=test_data.test_name,
            test_description=test_data.test_description,
            variants=[variant.dict() for variant in test_data.variants],
            target_metrics=[metric.dict() for metric in test_data.target_metrics],
            sample_size=test_data.sample_size,
            confidence_threshold=test_data.confidence_threshold,
            duration_days=test_data.duration_days,
            end_date=datetime.utcnow() + timedelta(days=test_data.duration_days)
        )
        
        db.add(db_test)
        db.commit()
        db.refresh(db_test)
        
        # Initialize test tracking
        self.active_tests[db_test.id] = {
            "start_time": datetime.utcnow(),
            "variant_stats": {
                variant.variant_name: {
                    "impressions": 0,
                    "responses": 0,
                    "conversions": 0,
                    "sentiment_scores": []
                }
                for variant in test_data.variants
            }
        }
        
        return ABTestResponse.from_orm(db_test)

    async def get_ab_test(self, test_id: int, db: Session) -> ABTestResponse:
        """Get A/B test details with current results"""
        
        test = db.query(ABTest).filter(ABTest.id == test_id).first()
        if not test:
            raise HTTPException(status_code=404, detail="A/B test not found")
        
        # Update with real-time statistics if test is active
        if test.is_active and test_id in self.active_tests:
            await self._update_test_statistics(test_id, test, db)
        
        return ABTestResponse.from_orm(test)

    async def record_variant_interaction(
        self,
        test_id: int,
        variant_name: str,
        interaction_type: str,  # impression, response, conversion
        interaction_data: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """Record interaction with a test variant"""
        
        if test_id not in self.active_tests:
            test = db.query(ABTest).filter(ABTest.id == test_id).first()
            if not test or not test.is_active:
                raise HTTPException(status_code=404, detail="Active A/B test not found")
        
        test_stats = self.active_tests[test_id]
        variant_stats = test_stats["variant_stats"]
        
        if variant_name not in variant_stats:
            raise HTTPException(status_code=400, detail=f"Variant {variant_name} not found")
        
        # Record interaction
        variant_stat = variant_stats[variant_name]
        
        if interaction_type == "impression":
            variant_stat["impressions"] += 1
        elif interaction_type == "response":
            variant_stat["responses"] += 1
            if "sentiment_score" in interaction_data:
                variant_stat["sentiment_scores"].append(interaction_data["sentiment_score"])
        elif interaction_type == "conversion":
            variant_stat["conversions"] += 1
        
        # Check if test should be analyzed for early stopping
        total_interactions = sum(
            stats["impressions"] for stats in variant_stats.values()
        )
        
        if total_interactions % 100 == 0:  # Analyze every 100 interactions
            await self._analyze_test_progress(test_id, db)
        
        return {"recorded": True, "variant": variant_name, "type": interaction_type}

    async def _analyze_test_progress(self, test_id: int, db: Session):
        """Analyze test progress and check for statistical significance"""
        
        test = db.query(ABTest).filter(ABTest.id == test_id).first()
        if not test:
            return
        
        test_stats = self.active_tests.get(test_id, {})
        variant_stats = test_stats.get("variant_stats", {})
        
        if len(variant_stats) < 2:
            return
        
        # Get control and treatment variants
        variants = list(variant_stats.items())
        control_name, control_stats = variants[0]
        
        results = []
        statistical_analyses = []
        
        for variant_name, variant_stat in variants:
            # Calculate metrics
            response_rate = (
                variant_stat["responses"] / max(variant_stat["impressions"], 1)
            )
            conversion_rate = (
                variant_stat["conversions"] / max(variant_stat["impressions"], 1)
            )
            avg_sentiment = (
                np.mean(variant_stat["sentiment_scores"]) 
                if variant_stat["sentiment_scores"] else 0.0
            )
            
            # Calculate confidence intervals
            response_ci = self.statistical_analyzer.calculate_confidence_interval(
                variant_stat["responses"], variant_stat["impressions"]
            )
            conversion_ci = self.statistical_analyzer.calculate_confidence_interval(
                variant_stat["conversions"], variant_stat["impressions"]
            )
            
            variant_result = VariantResult(
                variant_name=variant_name,
                sample_size=variant_stat["impressions"],
                response_rate=response_rate,
                conversion_rate=conversion_rate,
                sentiment_score=avg_sentiment,
                confidence_interval={
                    "response_rate_lower": response_ci[0],
                    "response_rate_upper": response_ci[1],
                    "conversion_rate_lower": conversion_ci[0],
                    "conversion_rate_upper": conversion_ci[1]
                }
            )
            
            results.append(variant_result)
            
            # Statistical comparison with control (if not control)
            if variant_name != control_name:
                z_test_response = self.statistical_analyzer.calculate_z_test(
                    control_stats["responses"],
                    control_stats["impressions"],
                    variant_stat["responses"],
                    variant_stat["impressions"]
                )
                
                z_test_conversion = self.statistical_analyzer.calculate_z_test(
                    control_stats["conversions"],
                    control_stats["impressions"],
                    variant_stat["conversions"],
                    variant_stat["impressions"]
                )
                
                effect_size = self.statistical_analyzer.calculate_effect_size(
                    control_stats["conversions"],
                    control_stats["impressions"],
                    variant_stat["conversions"],
                    variant_stat["impressions"]
                )
                
                analysis = StatisticalAnalysis(
                    p_value=min(z_test_response["p_value"], z_test_conversion["p_value"]),
                    confidence_level=max(z_test_response["confidence_level"], z_test_conversion["confidence_level"]),
                    effect_size=effect_size,
                    statistical_significance=(
                        z_test_response["significant"] or z_test_conversion["significant"]
                    ),
                    recommendation=self._generate_recommendation(
                        variant_result, results[0], z_test_response, z_test_conversion
                    )
                )
                
                statistical_analyses.append(analysis)
        
        # Update test results
        test.variant_results = [result.dict() for result in results]
        test.statistical_analysis = [analysis.dict() for analysis in statistical_analyses]
        
        # Determine winner if statistically significant
        if statistical_analyses and any(a.statistical_significance for a in statistical_analyses):
            winner = self._determine_winner(results, statistical_analyses)
            if winner:
                test.winner_variant = winner.variant_name
                test.confidence_level = max(a.confidence_level for a in statistical_analyses)
        
        db.commit()

    def _generate_recommendation(
        self,
        treatment_result: VariantResult,
        control_result: VariantResult,
        response_test: Dict[str, float],
        conversion_test: Dict[str, float]
    ) -> str:
        """Generate recommendation based on test results"""
        
        if response_test["significant"] and conversion_test["significant"]:
            if treatment_result.conversion_rate > control_result.conversion_rate:
                return f"Recommend {treatment_result.variant_name}: significantly higher conversion rate"
            else:
                return f"Recommend {control_result.variant_name}: control performs better"
        
        elif response_test["significant"]:
            if treatment_result.response_rate > control_result.response_rate:
                return f"Consider {treatment_result.variant_name}: higher response rate"
            else:
                return f"Keep {control_result.variant_name}: better response rate"
        
        elif conversion_test["significant"]:
            if treatment_result.conversion_rate > control_result.conversion_rate:
                return f"Recommend {treatment_result.variant_name}: higher conversion rate"
            else:
                return f"Keep {control_result.variant_name}: better conversion rate"
        
        else:
            return "Continue test: no statistically significant difference yet"

    def _determine_winner(
        self, 
        results: List[VariantResult], 
        analyses: List[StatisticalAnalysis]
    ) -> Optional[VariantResult]:
        """Determine the winning variant based on statistical analysis"""
        
        # Find the variant with the highest conversion rate and statistical significance
        significant_variants = []
        
        for i, (result, analysis) in enumerate(zip(results[1:], analyses), 1):
            if analysis.statistical_significance and result.conversion_rate > results[0].conversion_rate:
                significant_variants.append((result, analysis.confidence_level))
        
        if significant_variants:
            # Return variant with highest confidence level
            return max(significant_variants, key=lambda x: x[1])[0]
        
        return None

    async def _update_test_statistics(self, test_id: int, test: ABTest, db: Session):
        """Update test with latest statistics"""
        
        if test_id not in self.active_tests:
            return
        
        # This method would be called periodically to update statistics
        # Implementation would depend on your specific metrics collection
        pass

    async def pause_ab_test(self, test_id: int, db: Session) -> ABTestResponse:
        """Pause an active A/B test"""
        
        test = db.query(ABTest).filter(ABTest.id == test_id).first()
        if not test:
            raise HTTPException(status_code=404, detail="A/B test not found")
        
        test.is_active = False
        db.commit()
        
        return ABTestResponse.from_orm(test)

    async def resume_ab_test(self, test_id: int, db: Session) -> ABTestResponse:
        """Resume a paused A/B test"""
        
        test = db.query(ABTest).filter(ABTest.id == test_id).first()
        if not test:
            raise HTTPException(status_code=404, detail="A/B test not found")
        
        # Check if test hasn't expired
        if test.end_date and datetime.utcnow() > test.end_date:
            raise HTTPException(status_code=400, detail="Test has expired and cannot be resumed")
        
        test.is_active = True
        db.commit()
        
        return ABTestResponse.from_orm(test)

    async def end_ab_test(self, test_id: int, db: Session) -> ABTestResponse:
        """End an A/B test and finalize results"""
        
        test = db.query(ABTest).filter(ABTest.id == test_id).first()
        if not test:
            raise HTTPException(status_code=404, detail="A/B test not found")
        
        # Final analysis
        if test_id in self.active_tests:
            await self._analyze_test_progress(test_id, db)
        
        # End test
        test.is_active = False
        test.end_date = datetime.utcnow()
        
        # Update session status
        session = db.query(TestSession).filter(TestSession.id == test.session_id).first()
        if session:
            session.status = TestSessionStatus.COMPLETED
        
        db.commit()
        
        # Clean up active test tracking
        if test_id in self.active_tests:
            del self.active_tests[test_id]
        
        return ABTestResponse.from_orm(test)

    async def get_test_recommendations(self, test_id: int, db: Session) -> Dict[str, Any]:
        """Get AI-powered recommendations for test optimization"""
        
        test = db.query(ABTest).filter(ABTest.id == test_id).first()
        if not test:
            raise HTTPException(status_code=404, detail="A/B test not found")
        
        recommendations = {
            "test_optimization": [],
            "variant_suggestions": [],
            "audience_insights": [],
            "next_steps": []
        }
        
        # Analyze current performance
        if test.variant_results:
            results = [VariantResult(**result) for result in test.variant_results]
            
            # Performance-based recommendations
            best_variant = max(results, key=lambda x: x.conversion_rate)
            worst_variant = min(results, key=lambda x: x.conversion_rate)
            
            if best_variant.conversion_rate > worst_variant.conversion_rate * 1.5:
                recommendations["test_optimization"].append(
                    f"Consider allocating more traffic to {best_variant.variant_name} "
                    f"(conversion rate: {best_variant.conversion_rate:.2%})"
                )
            
            # Sample size recommendations
            if max(result.sample_size for result in results) < 1000:
                recommendations["test_optimization"].append(
                    "Consider increasing sample size for more reliable results (current max: "
                    f"{max(result.sample_size for result in results)})"
                )
            
            # Variant performance insights
            for result in results:
                if result.conversion_rate < 0.05:
                    recommendations["variant_suggestions"].append(
                        f"Variant '{result.variant_name}' has low conversion rate ({result.conversion_rate:.2%}). "
                        "Consider revising message content or call-to-action."
                    )
        
        # Test duration recommendations
        test_duration = (datetime.utcnow() - test.start_date).days
        if test_duration < 7:
            recommendations["next_steps"].append(
                f"Test has been running for {test_duration} days. "
                "Consider running for at least 7 days to account for weekly patterns."
            )
        
        return recommendations

# Initialize API instance
ab_testing_dashboard = ABTestingDashboard()

# API functions for main testing router integration
async def create_ab_test(db, session_id: int, ab_test_data, user_id: str):
    """Create A/B test for main testing API"""
    return await ab_testing_dashboard.create_ab_test(ab_test_data, db)

async def get_test_results(db, test_id: int, user_id: str, include_confidence_intervals: bool = True):
    """Get A/B test results for main testing API"""
    test = await ab_testing_dashboard.get_ab_test(test_id, db)
    if test.variant_results:
        return [VariantResult(**result) for result in test.variant_results]
    return []

async def stop_test(db, test_id: int, user_id: str, winner_variant: str = None):
    """Stop A/B test for main testing API"""
    test = await ab_testing_dashboard.end_ab_test(test_id, db)
    if winner_variant:
        test_obj = db.query(ABTest).filter(ABTest.id == test_id).first()
        if test_obj:
            test_obj.winner_variant = winner_variant
            db.commit()
    return test

# Export the dashboard instance as 'ab_testing' for compatibility
ab_testing = ab_testing_dashboard

# API Routes
@router.post("/tests", response_model=ABTestResponse)
async def create_ab_test(
    test_data: ABTestCreate,
    db: Session = Depends(get_db)
):
    """Create a new A/B test"""
    return await ab_testing.create_ab_test(test_data, db)

@router.get("/tests/{test_id}", response_model=ABTestResponse)
async def get_ab_test(
    test_id: int,
    db: Session = Depends(get_db)
):
    """Get A/B test details and results"""
    return await ab_testing.get_ab_test(test_id, db)

@router.get("/tests", response_model=List[ABTestResponse])
async def list_ab_tests(
    session_id: Optional[int] = None,
    active_only: bool = False,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List A/B tests with optional filtering"""
    
    query = db.query(ABTest)
    
    if session_id:
        query = query.filter(ABTest.session_id == session_id)
    
    if active_only:
        query = query.filter(ABTest.is_active == True)
    
    tests = query.order_by(desc(ABTest.created_at)).offset(offset).limit(limit).all()
    
    return [ABTestResponse.from_orm(test) for test in tests]

@router.post("/tests/{test_id}/interactions")
async def record_interaction(
    test_id: int,
    variant_name: str,
    interaction_type: str,
    interaction_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Record interaction with a test variant"""
    
    return await ab_testing.record_variant_interaction(
        test_id, variant_name, interaction_type, interaction_data, db
    )

@router.post("/tests/{test_id}/pause", response_model=ABTestResponse)
async def pause_test(
    test_id: int,
    db: Session = Depends(get_db)
):
    """Pause an active A/B test"""
    return await ab_testing.pause_ab_test(test_id, db)

@router.post("/tests/{test_id}/resume", response_model=ABTestResponse)
async def resume_test(
    test_id: int,
    db: Session = Depends(get_db)
):
    """Resume a paused A/B test"""
    return await ab_testing.resume_ab_test(test_id, db)

@router.post("/tests/{test_id}/end", response_model=ABTestResponse)
async def end_test(
    test_id: int,
    db: Session = Depends(get_db)
):
    """End an A/B test and finalize results"""
    return await ab_testing.end_ab_test(test_id, db)

@router.get("/tests/{test_id}/recommendations")
async def get_test_recommendations(
    test_id: int,
    db: Session = Depends(get_db)
):
    """Get AI-powered recommendations for test optimization"""
    return await ab_testing.get_test_recommendations(test_id, db)

@router.post("/calculate-sample-size")
async def calculate_required_sample_size(
    baseline_rate: float,
    minimum_detectable_effect: float,
    power: float = 0.8,
    significance_level: float = 0.05
):
    """Calculate required sample size for A/B test"""
    
    if not (0 < baseline_rate < 1):
        raise HTTPException(status_code=400, detail="Baseline rate must be between 0 and 1")
    
    if minimum_detectable_effect <= 0:
        raise HTTPException(status_code=400, detail="Minimum detectable effect must be positive")
    
    sample_size = StatisticalAnalyzer.calculate_sample_size(
        baseline_rate, minimum_detectable_effect, power, significance_level
    )
    
    return {
        "required_sample_size_per_variant": sample_size,
        "total_sample_size": sample_size * 2,
        "parameters": {
            "baseline_rate": baseline_rate,
            "minimum_detectable_effect": minimum_detectable_effect,
            "power": power,
            "significance_level": significance_level
        }
    }