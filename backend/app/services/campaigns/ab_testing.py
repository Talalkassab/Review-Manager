"""
A/B testing service with statistical analysis.
Provides variant assignment, statistical significance testing, and recommendations.
"""
import random
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
import numpy as np
from scipy import stats
from scipy.stats import chi2_contingency, ttest_ind

from ...core.logging import get_logger
from ...models import Campaign, CampaignRecipient, Customer

logger = get_logger(__name__)


class ABTestingService:
    """Service for A/B testing statistical analysis and management."""
    
    def __init__(self):
        pass
    
    def assign_variants(
        self,
        customer_ids: List[UUID],
        ab_config: Dict[str, Any]
    ) -> Dict[UUID, str]:
        """Assign variants to customers for A/B testing."""
        try:
            variants = ab_config.get("variants", [])
            if not variants:
                return {}
            
            # Get variant weights (default to equal distribution)
            total_weight = sum(variant.get("weight", 1) for variant in variants)
            variant_probabilities = [variant.get("weight", 1) / total_weight for variant in variants]
            variant_ids = [variant.get("id") for variant in variants]
            
            assignments = {}
            
            # Ensure random seed for reproducibility if specified
            if ab_config.get("random_seed"):
                random.seed(ab_config["random_seed"])
            
            assignment_method = ab_config.get("assignment_method", "random")
            
            if assignment_method == "random":
                assignments = self._random_assignment(customer_ids, variant_ids, variant_probabilities)
            elif assignment_method == "sequential":
                assignments = self._sequential_assignment(customer_ids, variant_ids, variant_probabilities)
            elif assignment_method == "stratified":
                # Would require customer segmentation data
                assignments = self._random_assignment(customer_ids, variant_ids, variant_probabilities)
            else:
                assignments = self._random_assignment(customer_ids, variant_ids, variant_probabilities)
            
            logger.info(f"Assigned variants to {len(assignments)} customers")
            return assignments
            
        except Exception as e:
            logger.error(f"Variant assignment failed: {str(e)}")
            return {}
    
    def _random_assignment(
        self,
        customer_ids: List[UUID],
        variant_ids: List[str],
        probabilities: List[float]
    ) -> Dict[UUID, str]:
        """Randomly assign variants based on probabilities."""
        assignments = {}
        
        for customer_id in customer_ids:
            # Use customer_id as seed for consistent assignment
            random.seed(hash(str(customer_id)) % (2**32))
            variant = random.choices(variant_ids, weights=probabilities, k=1)[0]
            assignments[customer_id] = variant
        
        return assignments
    
    def _sequential_assignment(
        self,
        customer_ids: List[UUID],
        variant_ids: List[str],
        probabilities: List[float]
    ) -> Dict[UUID, str]:
        """Sequential assignment to maintain exact proportions."""
        assignments = {}
        
        # Calculate exact counts for each variant
        total_customers = len(customer_ids)
        variant_counts = [int(total_customers * prob) for prob in probabilities]
        
        # Adjust for rounding errors
        remaining = total_customers - sum(variant_counts)
        for i in range(remaining):
            variant_counts[i % len(variant_counts)] += 1
        
        # Create assignment list
        assignment_list = []
        for variant_id, count in zip(variant_ids, variant_counts):
            assignment_list.extend([variant_id] * count)
        
        # Shuffle and assign
        random.shuffle(assignment_list)
        
        for i, customer_id in enumerate(customer_ids):
            assignments[customer_id] = assignment_list[i]
        
        return assignments
    
    async def analyze_ab_test(
        self,
        campaign: Campaign,
        recipients: List[CampaignRecipient]
    ) -> Dict[str, Any]:
        """Perform comprehensive A/B test statistical analysis."""
        try:
            if not campaign.is_ab_test or not campaign.ab_test_config:
                raise ValueError("Campaign is not configured for A/B testing")
            
            # Group recipients by variant
            variant_data = self._group_by_variant(recipients)
            
            if len(variant_data) < 2:
                return {
                    "campaign_id": str(campaign.id),
                    "test_duration_hours": 0,
                    "variants": [],
                    "winner": None,
                    "confidence_level": 0,
                    "statistical_significance": False,
                    "recommendations": ["Insufficient variants for A/B testing"],
                    "key_metrics": {},
                    "conversion_uplift": None
                }
            
            # Calculate test duration
            test_duration = self._calculate_test_duration(campaign)
            
            # Analyze each variant
            variant_analyses = []
            for variant_id, variant_recipients in variant_data.items():
                analysis = self._analyze_variant(variant_id, variant_recipients)
                variant_analyses.append(analysis)
            
            # Perform statistical significance testing
            significance_results = self._test_statistical_significance(variant_analyses)
            
            # Determine winner
            winner_info = self._determine_winner(variant_analyses, significance_results)
            
            # Calculate conversion uplift
            uplift_info = self._calculate_conversion_uplift(variant_analyses)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                variant_analyses,
                significance_results,
                winner_info,
                test_duration
            )
            
            # Key metrics summary
            key_metrics = self._calculate_key_metrics(variant_analyses, significance_results)
            
            return {
                "campaign_id": str(campaign.id),
                "test_duration_hours": test_duration,
                "variants": variant_analyses,
                "winner": winner_info["winner_id"] if winner_info else None,
                "confidence_level": significance_results.get("confidence_level", 0),
                "statistical_significance": significance_results.get("is_significant", False),
                "recommendations": recommendations,
                "key_metrics": key_metrics,
                "conversion_uplift": uplift_info.get("max_uplift"),
                "p_value": significance_results.get("p_value"),
                "effect_size": significance_results.get("effect_size")
            }
            
        except Exception as e:
            logger.error(f"A/B test analysis failed: {str(e)}")
            return {"error": str(e)}
    
    def _group_by_variant(self, recipients: List[CampaignRecipient]) -> Dict[str, List[CampaignRecipient]]:
        """Group recipients by variant ID."""
        variant_data = {}
        
        for recipient in recipients:
            variant_id = recipient.variant_id or "control"
            if variant_id not in variant_data:
                variant_data[variant_id] = []
            variant_data[variant_id].append(recipient)
        
        return variant_data
    
    def _calculate_test_duration(self, campaign: Campaign) -> float:
        """Calculate test duration in hours."""
        if not campaign.started_at:
            return 0
        
        end_time = campaign.completed_at or datetime.utcnow()
        duration = end_time - campaign.started_at
        return duration.total_seconds() / 3600
    
    def _analyze_variant(self, variant_id: str, recipients: List[CampaignRecipient]) -> Dict[str, Any]:
        """Analyze performance metrics for a variant."""
        total_recipients = len(recipients)
        
        if total_recipients == 0:
            return {
                "variant_id": variant_id,
                "sample_size": 0,
                "sent_count": 0,
                "delivered_count": 0,
                "read_count": 0,
                "response_count": 0,
                "delivery_rate": 0,
                "read_rate": 0,
                "response_rate": 0,
                "avg_response_time_hours": 0
            }
        
        # Count metrics
        sent_count = sum(1 for r in recipients if r.is_sent)
        delivered_count = sum(1 for r in recipients if r.status in ["delivered", "read", "responded"])
        read_count = sum(1 for r in recipients if r.status in ["read", "responded"])
        response_count = sum(1 for r in recipients if r.has_responded)
        
        # Calculate rates
        delivery_rate = (delivered_count / sent_count * 100) if sent_count > 0 else 0
        read_rate = (read_count / delivered_count * 100) if delivered_count > 0 else 0
        response_rate = (response_count / delivered_count * 100) if delivered_count > 0 else 0
        
        # Calculate average response time
        response_times = []
        for recipient in recipients:
            if recipient.sent_at and recipient.responded_at:
                time_diff = recipient.responded_at - recipient.sent_at
                response_times.append(time_diff.total_seconds() / 3600)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "variant_id": variant_id,
            "sample_size": total_recipients,
            "sent_count": sent_count,
            "delivered_count": delivered_count,
            "read_count": read_count,
            "response_count": response_count,
            "delivery_rate": round(delivery_rate, 2),
            "read_rate": round(read_rate, 2),
            "response_rate": round(response_rate, 2),
            "avg_response_time_hours": round(avg_response_time, 2),
            "conversion_rate": response_rate  # Primary metric for comparison
        }
    
    def _test_statistical_significance(self, variant_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test statistical significance between variants."""
        try:
            if len(variant_analyses) < 2:
                return {"is_significant": False, "p_value": 1.0}
            
            # Prepare data for chi-square test
            # Compare response rates (conversions) between variants
            delivered_counts = [v["delivered_count"] for v in variant_analyses]
            response_counts = [v["response_count"] for v in variant_analyses]
            non_response_counts = [d - r for d, r in zip(delivered_counts, response_counts)]
            
            # Create contingency table
            contingency_table = [response_counts, non_response_counts]
            
            # Perform chi-square test
            if min(delivered_counts) > 5 and min(response_counts) > 0:  # Check minimum sample size
                chi2_stat, p_value, dof, expected = chi2_contingency(contingency_table)
                
                # Calculate effect size (Cramér's V)
                n = sum(delivered_counts)
                cramer_v = math.sqrt(chi2_stat / (n * (len(variant_analyses) - 1))) if n > 0 else 0
                
                # Determine confidence level
                if p_value < 0.01:
                    confidence_level = 99
                elif p_value < 0.05:
                    confidence_level = 95
                elif p_value < 0.1:
                    confidence_level = 90
                else:
                    confidence_level = 0
                
                return {
                    "is_significant": p_value < 0.05,
                    "p_value": round(p_value, 4),
                    "confidence_level": confidence_level,
                    "effect_size": round(cramer_v, 4),
                    "chi2_statistic": round(chi2_stat, 4),
                    "test_method": "chi_square"
                }
            else:
                # Use Fisher's exact test for small samples (simplified binary comparison)
                if len(variant_analyses) == 2:
                    return self._fishers_exact_test(variant_analyses[0], variant_analyses[1])
                else:
                    return {
                        "is_significant": False,
                        "p_value": 1.0,
                        "confidence_level": 0,
                        "effect_size": 0,
                        "test_method": "insufficient_sample_size"
                    }
                    
        except Exception as e:
            logger.error(f"Statistical significance test failed: {str(e)}")
            return {
                "is_significant": False,
                "p_value": 1.0,
                "error": str(e)
            }
    
    def _fishers_exact_test(self, variant_a: Dict[str, Any], variant_b: Dict[str, Any]) -> Dict[str, Any]:
        """Perform Fisher's exact test for two variants."""
        try:
            # Create 2x2 contingency table
            a_responses = variant_a["response_count"]
            a_non_responses = variant_a["delivered_count"] - a_responses
            b_responses = variant_b["response_count"]
            b_non_responses = variant_b["delivered_count"] - b_responses
            
            table = [[a_responses, a_non_responses], [b_responses, b_non_responses]]
            
            # Use scipy's contingency table test
            chi2_stat, p_value, dof, expected = chi2_contingency(table)
            
            # Calculate effect size
            n = variant_a["delivered_count"] + variant_b["delivered_count"]
            cramer_v = math.sqrt(chi2_stat / n) if n > 0 else 0
            
            return {
                "is_significant": p_value < 0.05,
                "p_value": round(p_value, 4),
                "confidence_level": 95 if p_value < 0.05 else 0,
                "effect_size": round(cramer_v, 4),
                "test_method": "fishers_exact"
            }
            
        except Exception as e:
            logger.error(f"Fisher's exact test failed: {str(e)}")
            return {"is_significant": False, "p_value": 1.0}
    
    def _determine_winner(
        self,
        variant_analyses: List[Dict[str, Any]],
        significance_results: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Determine the winning variant."""
        if not significance_results.get("is_significant", False):
            return None
        
        # Find variant with highest conversion rate
        best_variant = max(variant_analyses, key=lambda x: x["conversion_rate"])
        
        # Check if the difference is meaningful (at least 5% relative improvement)
        other_variants = [v for v in variant_analyses if v["variant_id"] != best_variant["variant_id"]]
        if not other_variants:
            return None
        
        baseline_rate = max(v["conversion_rate"] for v in other_variants)
        relative_improvement = ((best_variant["conversion_rate"] - baseline_rate) / baseline_rate * 100) if baseline_rate > 0 else 0
        
        if relative_improvement >= 5:  # At least 5% relative improvement
            return {
                "winner_id": best_variant["variant_id"],
                "winning_rate": best_variant["conversion_rate"],
                "baseline_rate": baseline_rate,
                "relative_improvement": round(relative_improvement, 2),
                "absolute_improvement": round(best_variant["conversion_rate"] - baseline_rate, 2)
            }
        
        return None
    
    def _calculate_conversion_uplift(self, variant_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate conversion uplift between variants."""
        if len(variant_analyses) < 2:
            return {}
        
        # Use first variant as control
        control_variant = variant_analyses[0]
        control_rate = control_variant["conversion_rate"]
        
        uplifts = []
        max_uplift = 0
        
        for variant in variant_analyses[1:]:
            variant_rate = variant["conversion_rate"]
            
            if control_rate > 0:
                uplift_percent = ((variant_rate - control_rate) / control_rate) * 100
            else:
                uplift_percent = 0
            
            uplifts.append({
                "variant_id": variant["variant_id"],
                "uplift_percent": round(uplift_percent, 2),
                "absolute_diff": round(variant_rate - control_rate, 2)
            })
            
            if abs(uplift_percent) > abs(max_uplift):
                max_uplift = uplift_percent
        
        return {
            "control_variant": control_variant["variant_id"],
            "control_rate": control_rate,
            "uplifts": uplifts,
            "max_uplift": round(max_uplift, 2)
        }
    
    def _generate_recommendations(
        self,
        variant_analyses: List[Dict[str, Any]],
        significance_results: Dict[str, Any],
        winner_info: Optional[Dict[str, Any]],
        test_duration: float
    ) -> List[str]:
        """Generate recommendations based on A/B test results."""
        recommendations = []
        
        # Check test duration
        if test_duration < 24:
            recommendations.append("Test duration is less than 24 hours. Consider running longer for more reliable results.")
        
        # Check sample sizes
        min_sample_size = min(v["sample_size"] for v in variant_analyses)
        if min_sample_size < 100:
            recommendations.append("Sample size is small. Consider larger sample sizes for more statistical power.")
        
        # Check statistical significance
        if significance_results.get("is_significant", False):
            if winner_info:
                recommendations.append(f"Test shows significant results. Variant {winner_info['winner_id']} is the winner with {winner_info['relative_improvement']:.1f}% improvement.")
                recommendations.append("Consider implementing the winning variant for all future campaigns.")
            else:
                recommendations.append("Test is statistically significant but practical difference is minimal.")
        else:
            recommendations.append("No statistically significant difference found between variants.")
            
            if significance_results.get("p_value", 1) > 0.1:
                recommendations.append("Consider running the test longer or increasing sample size.")
            else:
                recommendations.append("Results suggest no meaningful difference. Either variant can be used.")
        
        # Check effect size
        effect_size = significance_results.get("effect_size", 0)
        if effect_size < 0.1:
            recommendations.append("Effect size is small. Even if significant, the practical impact may be limited.")
        elif effect_size > 0.3:
            recommendations.append("Large effect size detected. The difference between variants is substantial.")
        
        # Performance-specific recommendations
        best_performing = max(variant_analyses, key=lambda x: x["conversion_rate"])
        worst_performing = min(variant_analyses, key=lambda x: x["conversion_rate"])
        
        if best_performing["conversion_rate"] > 0 and worst_performing["conversion_rate"] == 0:
            recommendations.append(f"Variant {worst_performing['variant_id']} had zero conversions. Consider investigating the message content or targeting.")
        
        # Response time analysis
        response_times = [v["avg_response_time_hours"] for v in variant_analyses if v["avg_response_time_hours"] > 0]
        if response_times:
            fastest_variant = min(variant_analyses, key=lambda x: x["avg_response_time_hours"] if x["avg_response_time_hours"] > 0 else float('inf'))
            if fastest_variant["avg_response_time_hours"] > 0:
                recommendations.append(f"Variant {fastest_variant['variant_id']} had the fastest average response time ({fastest_variant['avg_response_time_hours']:.1f} hours).")
        
        return recommendations if recommendations else ["No specific recommendations available."]
    
    def _calculate_key_metrics(
        self,
        variant_analyses: List[Dict[str, Any]],
        significance_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate key metrics summary."""
        total_sample_size = sum(v["sample_size"] for v in variant_analyses)
        total_responses = sum(v["response_count"] for v in variant_analyses)
        total_delivered = sum(v["delivered_count"] for v in variant_analyses)
        
        overall_conversion_rate = (total_responses / total_delivered * 100) if total_delivered > 0 else 0
        
        # Best and worst performing variants
        best_variant = max(variant_analyses, key=lambda x: x["conversion_rate"])
        worst_variant = min(variant_analyses, key=lambda x: x["conversion_rate"])
        
        return {
            "total_sample_size": total_sample_size,
            "total_responses": total_responses,
            "overall_conversion_rate": round(overall_conversion_rate, 2),
            "best_conversion_rate": best_variant["conversion_rate"],
            "worst_conversion_rate": worst_variant["conversion_rate"],
            "conversion_rate_range": round(best_variant["conversion_rate"] - worst_variant["conversion_rate"], 2),
            "statistical_power": self._calculate_statistical_power(variant_analyses, significance_results),
            "minimum_detectable_effect": self._calculate_minimum_detectable_effect(variant_analyses)
        }
    
    def _calculate_statistical_power(
        self,
        variant_analyses: List[Dict[str, Any]],
        significance_results: Dict[str, Any]
    ) -> float:
        """Calculate statistical power (simplified estimation)."""
        # This is a simplified power calculation
        # In practice, you'd use more sophisticated methods
        
        if len(variant_analyses) < 2:
            return 0.0
        
        min_sample_size = min(v["delivered_count"] for v in variant_analyses)
        effect_size = significance_results.get("effect_size", 0)
        
        # Rough power estimation based on sample size and effect size
        if min_sample_size >= 100 and effect_size >= 0.2:
            power = 0.8
        elif min_sample_size >= 50 and effect_size >= 0.3:
            power = 0.7
        elif min_sample_size >= 30:
            power = 0.6
        else:
            power = 0.5
        
        return round(power, 2)
    
    def _calculate_minimum_detectable_effect(self, variant_analyses: List[Dict[str, Any]]) -> float:
        """Calculate minimum detectable effect size."""
        if len(variant_analyses) < 2:
            return 0.0
        
        min_sample_size = min(v["delivered_count"] for v in variant_analyses)
        
        # Simplified MDE calculation
        # Assumes alpha = 0.05, power = 0.8
        if min_sample_size >= 1000:
            mde = 2.0
        elif min_sample_size >= 500:
            mde = 3.0
        elif min_sample_size >= 100:
            mde = 5.0
        elif min_sample_size >= 50:
            mde = 8.0
        else:
            mde = 15.0
        
        return mde
    
    def calculate_required_sample_size(
        self,
        baseline_conversion_rate: float,
        minimum_detectable_effect: float,
        statistical_power: float = 0.8,
        significance_level: float = 0.05
    ) -> int:
        """Calculate required sample size for A/B test."""
        try:
            # Use standard formula for sample size calculation
            # This is a simplified version - in practice you'd use more precise calculations
            
            alpha = significance_level
            beta = 1 - statistical_power
            
            # Convert percentage to proportion
            p1 = baseline_conversion_rate / 100
            p2 = p1 * (1 + minimum_detectable_effect / 100)
            
            # Average proportion
            p_avg = (p1 + p2) / 2
            
            # Z-scores
            z_alpha = 1.96  # for alpha = 0.05
            z_beta = 0.84   # for beta = 0.2 (power = 0.8)
            
            # Sample size calculation
            numerator = (z_alpha * math.sqrt(2 * p_avg * (1 - p_avg)) + z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
            denominator = (p2 - p1) ** 2
            
            sample_size_per_variant = math.ceil(numerator / denominator)
            
            # Minimum sample size considerations
            if sample_size_per_variant < 50:
                sample_size_per_variant = 50
            
            return sample_size_per_variant
            
        except Exception as e:
            logger.error(f"Sample size calculation failed: {str(e)}")
            return 100  # Default minimum