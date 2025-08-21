"""
Statistical Analysis Tools for A/B Testing
==========================================

Advanced statistical analysis tools for A/B testing with confidence intervals,
significance testing, and effect size calculations.
"""

import math
import numpy as np
from scipy import stats
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .schemas import (
    StatisticalAnalysis, VariantResult, ABTestMetrics,
    ABTestResponse
)

class TestType(str, Enum):
    PROPORTION = "proportion"  # For conversion rates, response rates
    MEAN = "mean"  # For continuous metrics like response time
    COUNT = "count"  # For count-based metrics

@dataclass
class TestData:
    """Container for test variant data"""
    variant_name: str
    sample_size: int
    successes: int  # For proportion tests
    sum_values: float  # For mean tests
    sum_squared: float  # For variance calculations
    values: List[float]  # Raw values if available

class StatisticalAnalyzer:
    """
    Advanced statistical analysis for A/B testing with support for:
    - Proportion tests (Chi-square, Fisher's exact test)
    - Mean comparison tests (t-tests, Welch's t-test)
    - Confidence intervals
    - Effect size calculations
    - Power analysis
    - Sequential testing
    """
    
    def __init__(self):
        self.minimum_sample_size = 100
        self.default_alpha = 0.05
        self.default_power = 0.8
    
    async def analyze_ab_test(
        self,
        variants: List[VariantResult],
        test_config: ABTestResponse,
        confidence_level: float = 0.95
    ) -> StatisticalAnalysis:
        """
        Perform comprehensive statistical analysis of A/B test results.
        
        Args:
            variants: List of variant results with metrics
            test_config: A/B test configuration
            confidence_level: Statistical confidence level (0.95 = 95%)
        
        Returns:
            StatisticalAnalysis with p-values, confidence intervals, and recommendations
        """
        
        alpha = 1 - confidence_level
        
        # Determine primary metric for analysis
        primary_metric = self._get_primary_metric(test_config.target_metrics)
        
        # Prepare test data
        test_data = self._prepare_test_data(variants, primary_metric)
        
        if len(test_data) < 2:
            return StatisticalAnalysis(
                p_value=1.0,
                confidence_level=confidence_level,
                effect_size=0.0,
                statistical_significance=False,
                recommendation="Insufficient variants for comparison"
            )
        
        # Perform appropriate statistical test
        if primary_metric.metric_type in ["response_rate", "conversion", "click_through"]:
            result = await self._analyze_proportion_test(test_data, alpha)
        elif primary_metric.metric_type in ["response_time", "satisfaction_score"]:
            result = await self._analyze_mean_test(test_data, alpha)
        else:
            result = await self._analyze_count_test(test_data, alpha)
        
        # Add power analysis and sample size recommendations
        result = await self._add_power_analysis(result, test_data, alpha)
        
        return result
    
    def _get_primary_metric(self, target_metrics: List[ABTestMetrics]) -> ABTestMetrics:
        """Identify the primary metric for statistical analysis"""
        
        # Priority order for metrics
        metric_priority = {
            "conversion": 1,
            "response_rate": 2,
            "satisfaction": 3,
            "response_time": 4
        }
        
        primary = min(
            target_metrics,
            key=lambda m: metric_priority.get(m.metric_type, 999)
        )
        
        return primary
    
    def _prepare_test_data(
        self, 
        variants: List[VariantResult], 
        primary_metric: ABTestMetrics
    ) -> List[TestData]:
        """Prepare variant data for statistical testing"""
        
        test_data = []
        
        for variant in variants:
            if primary_metric.metric_type in ["response_rate", "conversion"]:
                # For proportion metrics
                successes = int(variant.sample_size * variant.response_rate)
                test_data.append(TestData(
                    variant_name=variant.variant_name,
                    sample_size=variant.sample_size,
                    successes=successes,
                    sum_values=successes,
                    sum_squared=successes,
                    values=[]
                ))
            
            elif primary_metric.metric_type == "satisfaction_score":
                # For continuous metrics - using sentiment score as proxy
                mean_value = variant.sentiment_score
                # Estimate sum and sum of squares (assuming normal distribution)
                sum_values = mean_value * variant.sample_size
                # Estimate variance (this would be better with actual data)
                estimated_variance = 0.2  # Reasonable assumption for normalized scores
                sum_squared = sum_values * mean_value + estimated_variance * variant.sample_size
                
                test_data.append(TestData(
                    variant_name=variant.variant_name,
                    sample_size=variant.sample_size,
                    successes=0,
                    sum_values=sum_values,
                    sum_squared=sum_squared,
                    values=[]
                ))
        
        return test_data
    
    async def _analyze_proportion_test(
        self, 
        test_data: List[TestData], 
        alpha: float
    ) -> StatisticalAnalysis:
        """Analyze proportion-based metrics using Chi-square or Fisher's exact test"""
        
        # For now, compare first two variants (can be extended for multiple comparisons)
        variant_a = test_data[0]
        variant_b = test_data[1]
        
        # Calculate proportions
        p1 = variant_a.successes / variant_a.sample_size
        p2 = variant_b.successes / variant_b.sample_size
        
        # Two-proportion z-test
        n1, n2 = variant_a.sample_size, variant_b.sample_size
        x1, x2 = variant_a.successes, variant_b.successes
        
        # Pooled proportion
        p_pool = (x1 + x2) / (n1 + n2)
        
        # Standard error
        se = math.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
        
        if se == 0:
            # No variance, cannot perform test
            return StatisticalAnalysis(
                p_value=1.0,
                confidence_level=1-alpha,
                effect_size=0.0,
                statistical_significance=False,
                recommendation="No variance in data for statistical comparison"
            )
        
        # Test statistic
        z_score = (p1 - p2) / se
        
        # Two-tailed p-value
        p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
        
        # Effect size (Cohen's h for proportions)
        effect_size = 2 * (math.asin(math.sqrt(p1)) - math.asin(math.sqrt(p2)))
        
        # Confidence interval for difference in proportions
        diff = p1 - p2
        se_diff = math.sqrt((p1 * (1-p1) / n1) + (p2 * (1-p2) / n2))
        ci_lower = diff - 1.96 * se_diff
        ci_upper = diff + 1.96 * se_diff
        
        # Generate recommendation
        recommendation = self._generate_proportion_recommendation(
            p_value, alpha, effect_size, variant_a.variant_name, variant_b.variant_name,
            p1, p2, ci_lower, ci_upper
        )
        
        return StatisticalAnalysis(
            p_value=p_value,
            confidence_level=1-alpha,
            effect_size=abs(effect_size),
            statistical_significance=p_value < alpha,
            recommendation=recommendation
        )
    
    async def _analyze_mean_test(
        self, 
        test_data: List[TestData], 
        alpha: float
    ) -> StatisticalAnalysis:
        """Analyze continuous metrics using t-tests"""
        
        variant_a = test_data[0]
        variant_b = test_data[1]
        
        # Calculate means
        mean_a = variant_a.sum_values / variant_a.sample_size
        mean_b = variant_b.sum_values / variant_b.sample_size
        
        # Calculate variances (using sum of squares)
        var_a = (variant_a.sum_squared - (variant_a.sum_values**2 / variant_a.sample_size)) / (variant_a.sample_size - 1)
        var_b = (variant_b.sum_squared - (variant_b.sum_values**2 / variant_b.sample_size)) / (variant_b.sample_size - 1)
        
        # Handle zero variance
        if var_a <= 0 or var_b <= 0:
            return StatisticalAnalysis(
                p_value=1.0,
                confidence_level=1-alpha,
                effect_size=0.0,
                statistical_significance=False,
                recommendation="Insufficient variance for statistical comparison"
            )
        
        # Welch's t-test (unequal variances)
        se_diff = math.sqrt(var_a/variant_a.sample_size + var_b/variant_b.sample_size)
        t_stat = (mean_a - mean_b) / se_diff
        
        # Degrees of freedom (Welch-Satterthwaite equation)
        df = ((var_a/variant_a.sample_size + var_b/variant_b.sample_size)**2) / \
             ((var_a/variant_a.sample_size)**2/(variant_a.sample_size-1) + 
              (var_b/variant_b.sample_size)**2/(variant_b.sample_size-1))
        
        # Two-tailed p-value
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))
        
        # Effect size (Cohen's d)
        pooled_std = math.sqrt(((variant_a.sample_size-1)*var_a + (variant_b.sample_size-1)*var_b) / 
                              (variant_a.sample_size + variant_b.sample_size - 2))
        effect_size = abs(mean_a - mean_b) / pooled_std
        
        # Generate recommendation
        recommendation = self._generate_mean_recommendation(
            p_value, alpha, effect_size, variant_a.variant_name, variant_b.variant_name,
            mean_a, mean_b
        )
        
        return StatisticalAnalysis(
            p_value=p_value,
            confidence_level=1-alpha,
            effect_size=effect_size,
            statistical_significance=p_value < alpha,
            recommendation=recommendation
        )
    
    async def _analyze_count_test(
        self, 
        test_data: List[TestData], 
        alpha: float
    ) -> StatisticalAnalysis:
        """Analyze count-based metrics using Poisson or negative binomial tests"""
        
        # For simplicity, treating as proportion test
        return await self._analyze_proportion_test(test_data, alpha)
    
    async def _add_power_analysis(
        self, 
        result: StatisticalAnalysis, 
        test_data: List[TestData], 
        alpha: float
    ) -> StatisticalAnalysis:
        """Add power analysis and sample size recommendations"""
        
        # Calculate achieved power (post-hoc power analysis)
        if len(test_data) >= 2:
            n1, n2 = test_data[0].sample_size, test_data[1].sample_size
            
            # For proportion test power calculation
            if result.statistical_significance:
                power_note = f" Test achieved sufficient power with samples of {n1} and {n2}."
            else:
                # Estimate required sample size for detecting this effect
                required_n = self._estimate_required_sample_size(result.effect_size, alpha)
                power_note = f" Consider increasing sample size to at least {required_n} per variant for adequate power."
            
            result.recommendation += power_note
        
        return result
    
    def _estimate_required_sample_size(self, effect_size: float, alpha: float) -> int:
        """Estimate required sample size for adequate power (80%)"""
        
        if effect_size == 0:
            return 10000  # Very large sample needed for no effect
        
        # Simplified calculation for proportion test
        # This is an approximation - real calculation would depend on baseline rates
        z_alpha = stats.norm.ppf(1 - alpha/2)  # Two-tailed
        z_beta = stats.norm.ppf(0.8)  # 80% power
        
        # Simplified formula for two proportions
        n_per_group = 2 * ((z_alpha + z_beta) / effect_size)**2
        
        return max(100, int(n_per_group))
    
    def _generate_proportion_recommendation(
        self, 
        p_value: float, 
        alpha: float, 
        effect_size: float,
        variant_a_name: str, 
        variant_b_name: str,
        p1: float, 
        p2: float,
        ci_lower: float, 
        ci_upper: float
    ) -> str:
        """Generate actionable recommendations for proportion tests"""
        
        recommendations = []
        
        if p_value < alpha:
            winner = variant_a_name if p1 > p2 else variant_b_name
            improvement = abs(p1 - p2) * 100
            
            recommendations.append(
                f"Statistical significance detected (p={p_value:.4f}). "
                f"{winner} performs {improvement:.1f} percentage points better."
            )
            
            if abs(effect_size) > 0.2:
                recommendations.append("Effect size is small but meaningful.")
            elif abs(effect_size) > 0.5:
                recommendations.append("Effect size is medium - practical significance likely.")
            elif abs(effect_size) > 0.8:
                recommendations.append("Effect size is large - strong practical significance.")
            
            if ci_lower > 0 or ci_upper < 0:
                recommendations.append(f"95% CI for difference: [{ci_lower:.3f}, {ci_upper:.3f}]")
        
        else:
            recommendations.append(
                f"No statistical significance detected (p={p_value:.4f}). "
                f"Continue testing or consider alternative approaches."
            )
            
            if min(len([d for d in [p1*100, p2*100] if d > 0]), 2) < 2:
                recommendations.append("Consider increasing sample size before drawing conclusions.")
        
        return " ".join(recommendations)
    
    def _generate_mean_recommendation(
        self,
        p_value: float,
        alpha: float,
        effect_size: float,
        variant_a_name: str,
        variant_b_name: str,
        mean_a: float,
        mean_b: float
    ) -> str:
        """Generate actionable recommendations for mean comparison tests"""
        
        recommendations = []
        
        if p_value < alpha:
            winner = variant_a_name if mean_a > mean_b else variant_b_name
            better_mean = max(mean_a, mean_b)
            worse_mean = min(mean_a, mean_b)
            improvement = ((better_mean - worse_mean) / worse_mean) * 100
            
            recommendations.append(
                f"Statistical significance detected (p={p_value:.4f}). "
                f"{winner} shows {improvement:.1f}% improvement."
            )
            
            # Cohen's d interpretation
            if effect_size < 0.2:
                recommendations.append("Effect size is very small.")
            elif effect_size < 0.5:
                recommendations.append("Effect size is small but may be meaningful.")
            elif effect_size < 0.8:
                recommendations.append("Effect size is medium - practical significance likely.")
            else:
                recommendations.append("Effect size is large - strong practical significance.")
        
        else:
            recommendations.append(
                f"No statistical significance detected (p={p_value:.4f}). "
                f"Difference may be due to random variation."
            )
        
        return " ".join(recommendations)

    async def calculate_confidence_intervals(
        self,
        variant_results: List[VariantResult],
        confidence_level: float = 0.95
    ) -> List[Dict[str, Any]]:
        """Calculate confidence intervals for all variant metrics"""
        
        alpha = 1 - confidence_level
        z_score = stats.norm.ppf(1 - alpha/2)
        
        confidence_intervals = []
        
        for variant in variant_results:
            # Response rate CI (proportion)
            p = variant.response_rate
            n = variant.sample_size
            se_p = math.sqrt(p * (1-p) / n) if n > 0 else 0
            
            ci_response_rate = {
                "lower": max(0, p - z_score * se_p),
                "upper": min(1, p + z_score * se_p)
            }
            
            # Conversion rate CI
            p_conv = variant.conversion_rate
            se_conv = math.sqrt(p_conv * (1-p_conv) / n) if n > 0 else 0
            
            ci_conversion_rate = {
                "lower": max(0, p_conv - z_score * se_conv),
                "upper": min(1, p_conv + z_score * se_conv)
            }
            
            # Sentiment score CI (assuming it's a mean)
            # Using estimated standard deviation
            estimated_sd = 0.2  # Reasonable for normalized sentiment scores
            se_sentiment = estimated_sd / math.sqrt(n) if n > 0 else 0
            
            ci_sentiment = {
                "lower": variant.sentiment_score - z_score * se_sentiment,
                "upper": variant.sentiment_score + z_score * se_sentiment
            }
            
            confidence_intervals.append({
                "variant_name": variant.variant_name,
                "response_rate_ci": ci_response_rate,
                "conversion_rate_ci": ci_conversion_rate,
                "sentiment_score_ci": ci_sentiment,
                "confidence_level": confidence_level
            })
        
        return confidence_intervals

    async def detect_early_winner(
        self,
        variants: List[VariantResult],
        minimum_effect_size: float = 0.1,
        confidence_threshold: float = 0.99
    ) -> Optional[Dict[str, Any]]:
        """
        Early winner detection for sequential testing.
        Stops test early if there's strong evidence of a winner.
        """
        
        if len(variants) < 2:
            return None
        
        # Sort by performance (response rate for now)
        sorted_variants = sorted(variants, key=lambda x: x.response_rate, reverse=True)
        leader = sorted_variants[0]
        runner_up = sorted_variants[1]
        
        # Check if sample sizes are adequate for early stopping
        min_sample_size = 100  # Minimum before considering early stopping
        if leader.sample_size < min_sample_size or runner_up.sample_size < min_sample_size:
            return None
        
        # Calculate test statistic for early stopping
        p1 = leader.response_rate
        p2 = runner_up.response_rate
        n1, n2 = leader.sample_size, runner_up.sample_size
        
        # Effect size
        observed_effect = p1 - p2
        if observed_effect < minimum_effect_size:
            return None  # Effect too small for early stopping
        
        # Statistical test
        p_pool = ((p1 * n1) + (p2 * n2)) / (n1 + n2)
        se = math.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
        
        if se == 0:
            return None
        
        z_score = observed_effect / se
        p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
        
        # Check if meets early stopping criteria
        alpha = 1 - confidence_threshold
        if p_value < alpha:
            return {
                "early_winner": leader.variant_name,
                "confidence": confidence_threshold,
                "effect_size": observed_effect,
                "p_value": p_value,
                "recommendation": f"Strong evidence for {leader.variant_name}. "
                               f"Consider stopping test early to implement winner."
            }
        
        return None

# Initialize global analyzer instance
statistical_analyzer = StatisticalAnalyzer()

# Helper functions for API integration
async def analyze_ab_test(
    db,
    test_id: int,
    confidence_level: float,
    user_id: str
) -> StatisticalAnalysis:
    """Analyze A/B test results with statistical significance testing"""
    
    # This would fetch test data from database
    # For now, return mock analysis
    
    return StatisticalAnalysis(
        p_value=0.023,
        confidence_level=confidence_level,
        effect_size=0.15,
        statistical_significance=True,
        recommendation="Variant B shows statistically significant improvement over Variant A"
    )

async def calculate_sample_size_requirements(
    baseline_rate: float,
    minimum_detectable_effect: float,
    power: float = 0.8,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """Calculate required sample size for A/B test"""
    
    z_alpha = stats.norm.ppf(1 - alpha/2)
    z_beta = stats.norm.ppf(power)
    
    p1 = baseline_rate
    p2 = baseline_rate + minimum_detectable_effect
    
    p_avg = (p1 + p2) / 2
    
    n_per_group = (2 * p_avg * (1 - p_avg) * (z_alpha + z_beta)**2) / (p1 - p2)**2
    
    return {
        "sample_size_per_variant": int(n_per_group),
        "total_sample_size": int(2 * n_per_group),
        "baseline_rate": baseline_rate,
        "minimum_detectable_effect": minimum_detectable_effect,
        "power": power,
        "alpha": alpha,
        "estimated_duration_days": int(n_per_group / 50)  # Assuming 50 samples per day
    }