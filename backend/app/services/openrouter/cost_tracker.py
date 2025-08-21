"""
Cost Tracking Service for OpenRouter integration.
Monitors API usage, tracks costs, and enforces budget limits.
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from .types import Usage, CostTracking
from .exceptions import BudgetExceededError
from ...core.config import settings

logger = logging.getLogger(__name__)


class BudgetPeriod(str, Enum):
    """Budget tracking periods."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class UsageRecord:
    """Individual usage record."""
    timestamp: datetime
    model: str
    user_id: str
    session_id: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    request_duration: float
    success: bool
    error_type: Optional[str] = None


@dataclass
class BudgetLimit:
    """Budget limit configuration."""
    period: BudgetPeriod
    limit_usd: float
    alert_threshold: float = 0.8  # Alert at 80%
    enabled: bool = True


class CostTracker:
    """
    Cost tracking service for OpenRouter API usage.
    
    Features:
    - Real-time cost tracking per request
    - Budget limits and alerts
    - Usage analytics and reporting
    - Cost forecasting
    - Multi-user cost allocation
    """
    
    def __init__(self):
        """Initialize the cost tracker."""
        self.usage_history: List[UsageRecord] = []
        self.current_costs: Dict[str, float] = {
            "daily": 0.0,
            "weekly": 0.0,
            "monthly": 0.0
        }
        self.budget_limits: Dict[str, BudgetLimit] = {}
        self.last_reset: Dict[str, datetime] = {
            "daily": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
            "weekly": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
            "monthly": datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        }
        
        # Model cost information (cost per 1K tokens)
        self.model_costs: Dict[str, Dict[str, float]] = {}
        
        self._initialize_budget_limits()
        logger.info("Cost tracker initialized")
    
    def _initialize_budget_limits(self):
        """Initialize default budget limits from configuration."""
        # Monthly budget from settings
        if hasattr(settings.openrouter, 'MONTHLY_BUDGET_LIMIT_USD'):
            monthly_limit = settings.openrouter.MONTHLY_BUDGET_LIMIT_USD
            self.budget_limits["monthly"] = BudgetLimit(
                period=BudgetPeriod.MONTHLY,
                limit_usd=monthly_limit,
                alert_threshold=0.8
            )
            
            # Set daily limit as 1/30th of monthly (with some buffer)
            daily_limit = monthly_limit / 25  # Slightly higher than 1/30th
            self.budget_limits["daily"] = BudgetLimit(
                period=BudgetPeriod.DAILY,
                limit_usd=daily_limit,
                alert_threshold=0.8
            )
            
            # Set weekly limit as 1/4th of monthly
            weekly_limit = monthly_limit / 4
            self.budget_limits["weekly"] = BudgetLimit(
                period=BudgetPeriod.WEEKLY,
                limit_usd=weekly_limit,
                alert_threshold=0.8
            )
    
    async def track_usage(
        self,
        usage: Usage,
        model: str,
        estimated_cost: float,
        user_id: str = "system",
        session_id: str = "default",
        request_duration: float = 0.0,
        success: bool = True,
        error_type: Optional[str] = None
    ):
        """
        Track API usage and costs.
        
        Args:
            usage: Token usage information
            model: Model used for the request
            estimated_cost: Calculated cost for the request
            user_id: User who made the request
            session_id: Session identifier
            request_duration: How long the request took
            success: Whether the request was successful
            error_type: Type of error if request failed
        """
        # Create usage record
        record = UsageRecord(
            timestamp=datetime.utcnow(),
            model=model,
            user_id=user_id,
            session_id=session_id,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            cost=estimated_cost,
            request_duration=request_duration,
            success=success,
            error_type=error_type
        )
        
        # Store record
        self.usage_history.append(record)
        
        # Update current costs (only for successful requests)
        if success:
            await self._update_current_costs(estimated_cost)
        
        # Clean up old records periodically
        if len(self.usage_history) > 10000:
            await self._cleanup_old_records()
        
        logger.debug(
            f"Tracked usage: {usage.total_tokens} tokens, "
            f"${estimated_cost:.6f}, model: {model}"
        )
    
    async def _update_current_costs(self, cost: float):
        """Update current period costs and check for resets."""
        now = datetime.utcnow()
        
        # Check if we need to reset daily costs
        if now.date() > self.last_reset["daily"].date():
            self.current_costs["daily"] = 0.0
            self.last_reset["daily"] = now.replace(hour=0, minute=0, second=0, microsecond=0)
            logger.info("Daily costs reset")
        
        # Check if we need to reset weekly costs (Monday)
        days_since_monday = now.weekday()
        week_start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_since_monday)
        if week_start > self.last_reset["weekly"]:
            self.current_costs["weekly"] = 0.0
            self.last_reset["weekly"] = week_start
            logger.info("Weekly costs reset")
        
        # Check if we need to reset monthly costs
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if month_start > self.last_reset["monthly"]:
            self.current_costs["monthly"] = 0.0
            self.last_reset["monthly"] = month_start
            logger.info("Monthly costs reset")
        
        # Update costs
        self.current_costs["daily"] += cost
        self.current_costs["weekly"] += cost
        self.current_costs["monthly"] += cost
    
    async def check_budget(self, estimated_cost: float, period: Optional[str] = None):
        """
        Check if a request would exceed budget limits.
        
        Args:
            estimated_cost: Cost of the upcoming request
            period: Specific period to check, or None for all periods
            
        Raises:
            BudgetExceededError: If budget would be exceeded
        """
        periods_to_check = [period] if period else ["daily", "weekly", "monthly"]
        
        for period_name in periods_to_check:
            if period_name not in self.budget_limits:
                continue
            
            budget = self.budget_limits[period_name]
            if not budget.enabled:
                continue
            
            current_cost = self.current_costs.get(period_name, 0.0)
            projected_cost = current_cost + estimated_cost
            
            # Check if budget would be exceeded
            if projected_cost > budget.limit_usd:
                raise BudgetExceededError(
                    current_cost=current_cost,
                    budget_limit=budget.limit_usd,
                    period=period_name
                )
            
            # Log warning if approaching limit
            if projected_cost > (budget.limit_usd * budget.alert_threshold):
                usage_percent = (projected_cost / budget.limit_usd) * 100
                logger.warning(
                    f"{period_name.title()} budget at {usage_percent:.1f}% "
                    f"(${projected_cost:.4f} / ${budget.limit_usd:.2f})"
                )
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current cost tracking status and statistics."""
        # Calculate recent usage statistics
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        last_24h = now - timedelta(days=1)
        
        recent_records = [r for r in self.usage_history if r.timestamp > last_24h]
        hourly_records = [r for r in recent_records if r.timestamp > last_hour]
        
        # Budget status
        budget_status = {}
        for period, budget in self.budget_limits.items():
            current = self.current_costs.get(period, 0.0)
            budget_status[period] = {
                "current_cost": current,
                "budget_limit": budget.limit_usd,
                "remaining": max(0, budget.limit_usd - current),
                "usage_percent": (current / budget.limit_usd * 100) if budget.limit_usd > 0 else 0,
                "alert_threshold": budget.alert_threshold,
                "enabled": budget.enabled
            }
        
        # Usage statistics
        total_requests = len(self.usage_history)
        successful_requests = sum(1 for r in self.usage_history if r.success)
        total_tokens = sum(r.total_tokens for r in self.usage_history)
        total_cost = sum(r.cost for r in self.usage_history if r.success)
        
        return {
            "budget_status": budget_status,
            "usage_stats": {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "success_rate": successful_requests / max(1, total_requests),
                "total_tokens_used": total_tokens,
                "total_cost_usd": total_cost,
                "last_hour_requests": len(hourly_records),
                "last_24h_requests": len(recent_records),
                "avg_cost_per_request": total_cost / max(1, successful_requests),
                "avg_tokens_per_request": total_tokens / max(1, total_requests)
            },
            "tracking_info": {
                "records_stored": len(self.usage_history),
                "last_reset_times": {
                    period: reset_time.isoformat() 
                    for period, reset_time in self.last_reset.items()
                }
            }
        }
    
    async def get_usage_by_model(self, days: int = 7) -> Dict[str, Dict[str, Any]]:
        """Get usage statistics broken down by model."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent_records = [r for r in self.usage_history if r.timestamp > cutoff]
        
        model_stats = {}
        for record in recent_records:
            if record.model not in model_stats:
                model_stats[record.model] = {
                    "requests": 0,
                    "successful_requests": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "avg_response_time": 0.0,
                    "errors": {}
                }
            
            stats = model_stats[record.model]
            stats["requests"] += 1
            stats["total_tokens"] += record.total_tokens
            stats["avg_response_time"] = (
                (stats["avg_response_time"] * (stats["requests"] - 1) + record.request_duration) 
                / stats["requests"]
            )
            
            if record.success:
                stats["successful_requests"] += 1
                stats["total_cost"] += record.cost
            elif record.error_type:
                stats["errors"][record.error_type] = stats["errors"].get(record.error_type, 0) + 1
        
        # Calculate derived metrics
        for model, stats in model_stats.items():
            if stats["requests"] > 0:
                stats["success_rate"] = stats["successful_requests"] / stats["requests"]
                stats["avg_cost_per_request"] = stats["total_cost"] / max(1, stats["successful_requests"])
                stats["avg_tokens_per_request"] = stats["total_tokens"] / stats["requests"]
        
        return model_stats
    
    async def get_usage_by_user(self, days: int = 7) -> Dict[str, Dict[str, Any]]:
        """Get usage statistics broken down by user."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent_records = [r for r in self.usage_history if r.timestamp > cutoff]
        
        user_stats = {}
        for record in recent_records:
            if record.user_id not in user_stats:
                user_stats[record.user_id] = {
                    "requests": 0,
                    "successful_requests": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "models_used": set(),
                    "sessions": set()
                }
            
            stats = user_stats[record.user_id]
            stats["requests"] += 1
            stats["total_tokens"] += record.total_tokens
            stats["models_used"].add(record.model)
            stats["sessions"].add(record.session_id)
            
            if record.success:
                stats["successful_requests"] += 1
                stats["total_cost"] += record.cost
        
        # Convert sets to counts and calculate derived metrics
        for user, stats in user_stats.items():
            stats["unique_models"] = len(stats["models_used"])
            stats["unique_sessions"] = len(stats["sessions"])
            stats["success_rate"] = stats["successful_requests"] / max(1, stats["requests"])
            stats["avg_cost_per_request"] = stats["total_cost"] / max(1, stats["successful_requests"])
            
            # Remove sets (not JSON serializable)
            del stats["models_used"]
            del stats["sessions"]
        
        return user_stats
    
    async def forecast_costs(self, days_ahead: int = 30) -> Dict[str, float]:
        """Forecast costs based on recent usage patterns."""
        if not self.usage_history:
            return {"daily": 0.0, "weekly": 0.0, "monthly": 0.0}
        
        # Calculate average daily cost from last 7 days
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_records = [
            r for r in self.usage_history 
            if r.timestamp > week_ago and r.success
        ]
        
        if not recent_records:
            return {"daily": 0.0, "weekly": 0.0, "monthly": 0.0}
        
        total_recent_cost = sum(r.cost for r in recent_records)
        daily_avg = total_recent_cost / 7
        
        return {
            "daily": daily_avg,
            "weekly": daily_avg * 7,
            "monthly": daily_avg * 30,
            "forecast_period": f"{days_ahead} days",
            "projected_cost": daily_avg * days_ahead
        }
    
    async def set_budget_limit(
        self, 
        period: str, 
        limit_usd: float, 
        alert_threshold: float = 0.8,
        enabled: bool = True
    ):
        """Set or update a budget limit."""
        try:
            period_enum = BudgetPeriod(period)
            self.budget_limits[period] = BudgetLimit(
                period=period_enum,
                limit_usd=limit_usd,
                alert_threshold=alert_threshold,
                enabled=enabled
            )
            logger.info(f"Updated {period} budget limit to ${limit_usd:.2f}")
        except ValueError:
            raise ValueError(f"Invalid period: {period}. Must be one of: {[p.value for p in BudgetPeriod]}")
    
    async def export_usage_data(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        format: str = "json"
    ) -> str:
        """Export usage data for analysis."""
        # Filter records by date range
        records = self.usage_history
        if start_date:
            records = [r for r in records if r.timestamp >= start_date]
        if end_date:
            records = [r for r in records if r.timestamp <= end_date]
        
        # Convert to serializable format
        export_data = []
        for record in records:
            data = asdict(record)
            data["timestamp"] = record.timestamp.isoformat()
            export_data.append(data)
        
        if format.lower() == "json":
            return json.dumps(export_data, indent=2, ensure_ascii=False)
        elif format.lower() == "csv":
            # Simple CSV export
            if not export_data:
                return ""
            
            headers = list(export_data[0].keys())
            csv_lines = [",".join(headers)]
            
            for record in export_data:
                row = [str(record.get(h, "")) for h in headers]
                csv_lines.append(",".join(row))
            
            return "\n".join(csv_lines)
        else:
            raise ValueError("Format must be 'json' or 'csv'")
    
    async def _cleanup_old_records(self):
        """Remove old usage records to prevent memory bloat."""
        # Keep last 30 days of records
        cutoff = datetime.utcnow() - timedelta(days=30)
        old_count = len(self.usage_history)
        
        self.usage_history = [
            record for record in self.usage_history 
            if record.timestamp > cutoff
        ]
        
        new_count = len(self.usage_history)
        if old_count > new_count:
            logger.info(f"Cleaned up {old_count - new_count} old usage records")
    
    async def get_cost_alerts(self) -> List[Dict[str, Any]]:
        """Get active cost alerts based on current usage."""
        alerts = []
        
        for period, budget in self.budget_limits.items():
            if not budget.enabled:
                continue
            
            current_cost = self.current_costs.get(period, 0.0)
            usage_percent = (current_cost / budget.limit_usd) * 100 if budget.limit_usd > 0 else 0
            
            if usage_percent >= budget.alert_threshold * 100:
                alert_level = "warning" if usage_percent < 100 else "critical"
                alerts.append({
                    "level": alert_level,
                    "period": period,
                    "message": f"{period.title()} budget at {usage_percent:.1f}%",
                    "current_cost": current_cost,
                    "budget_limit": budget.limit_usd,
                    "usage_percent": usage_percent
                })
        
        return alerts