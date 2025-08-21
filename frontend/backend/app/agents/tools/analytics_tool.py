"""
Analytics and data processing tool for agents
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import statistics
from .base_tool import BaseAgentTool, ToolResult


class AnalyticsTool(BaseAgentTool):
    """Tool for performing analytics and data analysis operations"""
    
    name: str = "analytics_processor"
    description: str = (
        "Perform statistical analysis, trend detection, and data insights "
        "for customer behavior and restaurant performance metrics."
    )
    
    def _validate_input(self, **kwargs) -> bool:
        """Validate analytics operation parameters"""
        operation = kwargs.get('operation')
        if not operation:
            self.logger.error("Operation parameter is required")
            return False
        
        valid_operations = [
            'calculate_statistics', 'detect_trends', 'segment_analysis',
            'performance_metrics', 'correlation_analysis', 'forecast'
        ]
        
        if operation not in valid_operations:
            self.logger.error(f"Invalid operation: {operation}")
            return False
            
        return True
    
    def _execute(self, **kwargs) -> Dict[str, Any]:
        """Execute analytics operation"""
        operation = kwargs.get('operation')
        data = kwargs.get('data', [])
        
        try:
            if operation == 'calculate_statistics':
                return self._calculate_statistics(data, kwargs.get('metric'))
            elif operation == 'detect_trends':
                return self._detect_trends(data, kwargs.get('time_field'))
            elif operation == 'segment_analysis':
                return self._segment_analysis(data, kwargs.get('segment_field'))
            elif operation == 'performance_metrics':
                return self._calculate_performance_metrics(data)
            elif operation == 'correlation_analysis':
                return self._correlation_analysis(
                    data, 
                    kwargs.get('field1'), 
                    kwargs.get('field2')
                )
            elif operation == 'forecast':
                return self._forecast_metrics(data, kwargs.get('periods', 7))
            else:
                raise ValueError(f"Unsupported operation: {operation}")
                
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Analytics operation failed: {str(e)}"
            ).dict()
    
    def _calculate_statistics(self, data: List[Dict[str, Any]], metric: str) -> Dict[str, Any]:
        """Calculate basic statistics for a metric"""
        if not data or not metric:
            return ToolResult(success=False, error="Data and metric required").dict()
        
        values = []
        for item in data:
            value = item.get(metric)
            if value is not None and isinstance(value, (int, float)):
                values.append(value)
        
        if not values:
            return ToolResult(success=False, error=f"No valid values found for metric: {metric}").dict()
        
        stats = {
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
            "sum": sum(values),
            "standard_deviation": statistics.stdev(values) if len(values) > 1 else 0
        }
        
        # Add percentiles
        sorted_values = sorted(values)
        stats["percentiles"] = {
            "25th": self._percentile(sorted_values, 25),
            "75th": self._percentile(sorted_values, 75),
            "90th": self._percentile(sorted_values, 90)
        }
        
        return ToolResult(
            success=True,
            data=stats,
            metadata={"metric": metric, "data_points": len(values)}
        ).dict()
    
    def _detect_trends(self, data: List[Dict[str, Any]], time_field: str) -> Dict[str, Any]:
        """Detect trends in time-series data"""
        if not data or not time_field:
            return ToolResult(success=False, error="Data and time_field required").dict()
        
        # Sort by time
        time_sorted = sorted(data, key=lambda x: x.get(time_field, ""))
        
        if len(time_sorted) < 3:
            return ToolResult(success=False, error="Insufficient data for trend analysis").dict()
        
        # Calculate trend metrics
        recent_period = time_sorted[-7:]  # Last 7 items
        previous_period = time_sorted[-14:-7] if len(time_sorted) >= 14 else time_sorted[:-7]
        
        trends = {}
        
        # Analyze numeric fields
        numeric_fields = self._identify_numeric_fields(time_sorted)
        
        for field in numeric_fields:
            recent_avg = self._calculate_average(recent_period, field)
            previous_avg = self._calculate_average(previous_period, field)
            
            if previous_avg != 0:
                change_percent = ((recent_avg - previous_avg) / previous_avg) * 100
            else:
                change_percent = 0
            
            trend_direction = "increasing" if change_percent > 5 else "decreasing" if change_percent < -5 else "stable"
            
            trends[field] = {
                "recent_average": recent_avg,
                "previous_average": previous_avg,
                "change_percent": change_percent,
                "trend_direction": trend_direction
            }
        
        return ToolResult(
            success=True,
            data={"trends": trends, "analysis_period": "last_7_vs_previous_7"},
            metadata={"total_data_points": len(time_sorted)}
        ).dict()
    
    def _segment_analysis(self, data: List[Dict[str, Any]], segment_field: str) -> Dict[str, Any]:
        """Perform segmentation analysis"""
        if not data or not segment_field:
            return ToolResult(success=False, error="Data and segment_field required").dict()
        
        segments = {}
        
        # Group by segment
        for item in data:
            segment_value = item.get(segment_field, "unknown")
            if segment_value not in segments:
                segments[segment_value] = []
            segments[segment_value].append(item)
        
        # Calculate metrics for each segment
        segment_analysis = {}
        
        for segment_name, segment_data in segments.items():
            # Basic metrics
            segment_analysis[segment_name] = {
                "count": len(segment_data),
                "percentage": (len(segment_data) / len(data)) * 100
            }
            
            # Calculate averages for numeric fields
            numeric_fields = self._identify_numeric_fields(segment_data)
            averages = {}
            
            for field in numeric_fields:
                avg = self._calculate_average(segment_data, field)
                if avg is not None:
                    averages[field] = avg
            
            segment_analysis[segment_name]["averages"] = averages
        
        # Identify best and worst performing segments
        if "total_spent" in numeric_fields or "rating" in numeric_fields:
            performance_field = "total_spent" if "total_spent" in numeric_fields else "rating"
            sorted_segments = sorted(
                segment_analysis.items(),
                key=lambda x: x[1]["averages"].get(performance_field, 0),
                reverse=True
            )
            
            best_segment = sorted_segments[0][0] if sorted_segments else None
            worst_segment = sorted_segments[-1][0] if sorted_segments else None
        else:
            best_segment = None
            worst_segment = None
        
        return ToolResult(
            success=True,
            data={
                "segments": segment_analysis,
                "total_segments": len(segments),
                "best_performing": best_segment,
                "worst_performing": worst_segment
            },
            metadata={"segment_field": segment_field}
        ).dict()
    
    def _calculate_performance_metrics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate key performance metrics"""
        if not data:
            return ToolResult(success=False, error="No data provided").dict()
        
        metrics = {}
        
        # Customer satisfaction metrics
        if any("rating" in item for item in data):
            ratings = [item.get("rating") for item in data if item.get("rating")]
            if ratings:
                metrics["satisfaction"] = {
                    "average_rating": statistics.mean(ratings),
                    "rating_distribution": self._calculate_distribution(ratings),
                    "nps_score": self._calculate_nps(ratings)
                }
        
        # Response rate metrics
        if any("response_received" in item for item in data):
            responses = [item.get("response_received", False) for item in data]
            response_rate = sum(responses) / len(responses) * 100
            metrics["engagement"] = {
                "response_rate": response_rate,
                "total_messages": len(responses),
                "responses_received": sum(responses)
            }
        
        # Visit frequency metrics
        if any("visit_count" in item for item in data):
            visit_counts = [item.get("visit_count", 0) for item in data]
            metrics["loyalty"] = {
                "average_visits": statistics.mean(visit_counts),
                "high_frequency_customers": sum(1 for v in visit_counts if v >= 10),
                "new_customers": sum(1 for v in visit_counts if v == 1)
            }
        
        # Revenue metrics
        if any("total_spent" in item for item in data):
            spending = [item.get("total_spent", 0) for item in data]
            metrics["revenue"] = {
                "total_revenue": sum(spending),
                "average_order_value": statistics.mean(spending),
                "high_value_customers": sum(1 for s in spending if s >= 500)
            }
        
        return ToolResult(
            success=True,
            data=metrics,
            metadata={"calculation_date": datetime.now().isoformat()}
        ).dict()
    
    def _correlation_analysis(self, data: List[Dict[str, Any]], field1: str, field2: str) -> Dict[str, Any]:
        """Analyze correlation between two fields"""
        if not data or not field1 or not field2:
            return ToolResult(success=False, error="Data and both fields required").dict()
        
        # Extract values for both fields
        pairs = []
        for item in data:
            val1 = item.get(field1)
            val2 = item.get(field2)
            
            if val1 is not None and val2 is not None and \
               isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                pairs.append((val1, val2))
        
        if len(pairs) < 2:
            return ToolResult(success=False, error="Insufficient data pairs for correlation").dict()
        
        # Calculate correlation coefficient (simplified Pearson)
        x_values = [pair[0] for pair in pairs]
        y_values = [pair[1] for pair in pairs]
        
        correlation = self._calculate_correlation(x_values, y_values)
        
        # Interpret correlation strength
        abs_corr = abs(correlation)
        if abs_corr >= 0.8:
            strength = "very strong"
        elif abs_corr >= 0.6:
            strength = "strong"
        elif abs_corr >= 0.4:
            strength = "moderate"
        elif abs_corr >= 0.2:
            strength = "weak"
        else:
            strength = "very weak"
        
        direction = "positive" if correlation > 0 else "negative"
        
        return ToolResult(
            success=True,
            data={
                "correlation_coefficient": correlation,
                "strength": strength,
                "direction": direction,
                "data_points": len(pairs),
                "interpretation": f"{strength.capitalize()} {direction} correlation"
            },
            metadata={"field1": field1, "field2": field2}
        ).dict()
    
    def _forecast_metrics(self, data: List[Dict[str, Any]], periods: int) -> Dict[str, Any]:
        """Simple forecasting based on historical trends"""
        if not data:
            return ToolResult(success=False, error="No data provided").dict()
        
        # Identify numeric fields for forecasting
        numeric_fields = self._identify_numeric_fields(data)
        
        if not numeric_fields:
            return ToolResult(success=False, error="No numeric fields found for forecasting").dict()
        
        forecasts = {}
        
        for field in numeric_fields:
            # Get recent trend
            recent_values = []
            for item in data[-10:]:  # Last 10 data points
                value = item.get(field)
                if value is not None and isinstance(value, (int, float)):
                    recent_values.append(value)
            
            if len(recent_values) >= 3:
                # Simple linear trend forecast
                trend = self._calculate_linear_trend(recent_values)
                current_avg = statistics.mean(recent_values)
                
                forecast_values = []
                for i in range(1, periods + 1):
                    forecast_value = current_avg + (trend * i)
                    forecast_values.append(max(0, forecast_value))  # Ensure non-negative
                
                forecasts[field] = {
                    "forecast_values": forecast_values,
                    "trend_per_period": trend,
                    "confidence": self._calculate_forecast_confidence(recent_values)
                }
        
        return ToolResult(
            success=True,
            data={
                "forecasts": forecasts,
                "forecast_periods": periods,
                "base_period": "recent_10_data_points"
            },
            metadata={"forecast_date": datetime.now().isoformat()}
        ).dict()
    
    # Helper methods
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        index = int((percentile / 100) * len(values))
        index = max(0, min(index, len(values) - 1))
        return values[index]
    
    def _identify_numeric_fields(self, data: List[Dict[str, Any]]) -> List[str]:
        """Identify numeric fields in data"""
        if not data:
            return []
        
        numeric_fields = []
        sample = data[0]
        
        for key, value in sample.items():
            if isinstance(value, (int, float)):
                numeric_fields.append(key)
        
        return numeric_fields
    
    def _calculate_average(self, data: List[Dict[str, Any]], field: str) -> Optional[float]:
        """Calculate average for a field"""
        values = []
        for item in data:
            value = item.get(field)
            if value is not None and isinstance(value, (int, float)):
                values.append(value)
        
        return statistics.mean(values) if values else None
    
    def _calculate_distribution(self, values: List[float]) -> Dict[str, int]:
        """Calculate distribution of values"""
        distribution = {}
        for value in values:
            value_key = str(int(value))
            distribution[value_key] = distribution.get(value_key, 0) + 1
        return distribution
    
    def _calculate_nps(self, ratings: List[float]) -> float:
        """Calculate Net Promoter Score from ratings"""
        # Assuming ratings are 1-5, convert to NPS scale
        promoters = sum(1 for r in ratings if r >= 4.5)
        detractors = sum(1 for r in ratings if r <= 2.5)
        
        nps = ((promoters - detractors) / len(ratings)) * 100
        return nps
    
    def _calculate_correlation(self, x_values: List[float], y_values: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return 0
        
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)
        sum_y2 = sum(y * y for y in y_values)
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y)) ** 0.5
        
        if denominator == 0:
            return 0
        
        return numerator / denominator
    
    def _calculate_linear_trend(self, values: List[float]) -> float:
        """Calculate linear trend from values"""
        if len(values) < 2:
            return 0
        
        n = len(values)
        x_values = list(range(n))
        
        # Calculate slope of linear regression
        sum_x = sum(x_values)
        sum_y = sum(values)
        sum_xy = sum(x * y for x, y in zip(x_values, values))
        sum_x2 = sum(x * x for x in x_values)
        
        if n * sum_x2 - sum_x * sum_x == 0:
            return 0
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        return slope
    
    def _calculate_forecast_confidence(self, values: List[float]) -> float:
        """Calculate confidence level for forecast"""
        if len(values) < 3:
            return 0.5
        
        # Based on data consistency and sample size
        variance = statistics.variance(values)
        mean_val = statistics.mean(values)
        
        # Coefficient of variation
        cv = (variance ** 0.5) / abs(mean_val) if mean_val != 0 else 1
        
        # Sample size factor
        size_factor = min(len(values) / 10, 1.0)
        
        # Confidence decreases with higher variation
        confidence = max(0.3, min(0.9, 1.0 - cv * 0.5)) * size_factor
        
        return confidence