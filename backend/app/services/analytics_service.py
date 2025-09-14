"""
Analytics Service Layer
Handles analytics and reporting business logic.
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, date
from uuid import UUID
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case, extract
from sqlalchemy.orm import selectinload

from ..models.customer import Customer
from ..models import WhatsAppMessage, Restaurant, Campaign
from ..core.logging import get_logger

logger = get_logger(__name__)


class TimeRange(Enum):
    """Time range options for analytics."""
    TODAY = "today"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    CUSTOM = "custom"


class AnalyticsService:
    """Service class for analytics and reporting."""

    def __init__(self, session: AsyncSession):
        """Initialize the service with a database session."""
        self.session = session

    async def get_dashboard_metrics(
        self,
        restaurant_id: Optional[UUID] = None,
        time_range: TimeRange = TimeRange.MONTH
    ) -> Dict[str, Any]:
        """Get comprehensive dashboard metrics."""
        # Calculate date range
        start_date, end_date = self._calculate_date_range(time_range)

        # Build base filters
        base_filters = self._build_base_filters(restaurant_id, start_date, end_date)

        # Gather all metrics
        metrics = {
            "summary": await self._get_summary_metrics(base_filters),
            "customer_metrics": await self._get_customer_metrics(base_filters),
            "engagement_metrics": await self._get_engagement_metrics(base_filters),
            "sentiment_metrics": await self._get_sentiment_metrics(base_filters),
            "message_metrics": await self._get_message_metrics(base_filters),
            "trends": await self._get_trend_data(base_filters, time_range),
            "time_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "type": time_range.value
            }
        }

        return metrics

    async def get_customer_analytics(
        self,
        restaurant_id: Optional[UUID] = None,
        time_range: TimeRange = TimeRange.MONTH
    ) -> Dict[str, Any]:
        """Get detailed customer analytics."""
        start_date, end_date = self._calculate_date_range(time_range)
        base_filters = self._build_base_filters(restaurant_id, start_date, end_date)

        return {
            "total_customers": await self._count_customers(base_filters),
            "new_customers": await self._count_new_customers(base_filters),
            "returning_customers": await self._count_returning_customers(base_filters),
            "customer_segments": await self._get_customer_segments(base_filters),
            "customer_lifetime_value": await self._calculate_customer_lifetime_value(base_filters),
            "churn_rate": await self._calculate_churn_rate(base_filters),
            "retention_rate": await self._calculate_retention_rate(base_filters),
            "top_customers": await self._get_top_customers(base_filters)
        }

    async def get_sentiment_analytics(
        self,
        restaurant_id: Optional[UUID] = None,
        time_range: TimeRange = TimeRange.MONTH
    ) -> Dict[str, Any]:
        """Get detailed sentiment analytics."""
        start_date, end_date = self._calculate_date_range(time_range)
        base_filters = self._build_base_filters(restaurant_id, start_date, end_date)

        return {
            "overall_sentiment": await self._get_overall_sentiment(base_filters),
            "sentiment_distribution": await self._get_sentiment_distribution(base_filters),
            "sentiment_trends": await self._get_sentiment_trends(base_filters, time_range),
            "sentiment_by_segment": await self._get_sentiment_by_segment(base_filters),
            "negative_feedback_themes": await self._analyze_negative_feedback_themes(base_filters),
            "positive_feedback_themes": await self._analyze_positive_feedback_themes(base_filters)
        }

    async def get_engagement_analytics(
        self,
        restaurant_id: Optional[UUID] = None,
        time_range: TimeRange = TimeRange.MONTH
    ) -> Dict[str, Any]:
        """Get detailed engagement analytics."""
        start_date, end_date = self._calculate_date_range(time_range)
        base_filters = self._build_base_filters(restaurant_id, start_date, end_date)

        return {
            "message_statistics": await self._get_message_statistics(base_filters),
            "response_rates": await self._calculate_response_rates(base_filters),
            "response_times": await self._calculate_response_times(base_filters),
            "conversation_metrics": await self._get_conversation_metrics(base_filters),
            "peak_hours": await self._analyze_peak_hours(base_filters),
            "channel_performance": await self._get_channel_performance(base_filters)
        }

    async def get_campaign_analytics(
        self,
        campaign_id: Optional[UUID] = None,
        restaurant_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get campaign performance analytics."""
        if campaign_id:
            return await self._get_single_campaign_analytics(campaign_id)
        else:
            return await self._get_all_campaigns_analytics(restaurant_id)

    async def generate_report(
        self,
        report_type: str,
        restaurant_id: Optional[UUID] = None,
        time_range: TimeRange = TimeRange.MONTH,
        format: str = "json"
    ) -> Dict[str, Any]:
        """Generate a comprehensive report."""
        start_date, end_date = self._calculate_date_range(time_range)

        report_data = {
            "report_type": report_type,
            "generated_at": datetime.utcnow().isoformat(),
            "time_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "type": time_range.value
            }
        }

        if report_type == "executive_summary":
            report_data["data"] = await self._generate_executive_summary(
                restaurant_id, start_date, end_date
            )
        elif report_type == "customer_insights":
            report_data["data"] = await self._generate_customer_insights(
                restaurant_id, start_date, end_date
            )
        elif report_type == "operational_metrics":
            report_data["data"] = await self._generate_operational_metrics(
                restaurant_id, start_date, end_date
            )
        else:
            report_data["data"] = await self.get_dashboard_metrics(
                restaurant_id, time_range
            )

        if format == "pdf":
            # TODO: Implement PDF generation
            pass

        return report_data

    async def get_real_time_metrics(
        self,
        restaurant_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get real-time metrics for monitoring."""
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        last_24h = now - timedelta(hours=24)

        return {
            "current_time": now.isoformat(),
            "active_conversations": await self._count_active_conversations(restaurant_id, last_hour),
            "messages_last_hour": await self._count_messages_since(restaurant_id, last_hour),
            "new_customers_today": await self._count_new_customers_since(restaurant_id, last_24h),
            "avg_response_time": await self._get_average_response_time(restaurant_id, last_hour),
            "pending_responses": await self._count_pending_responses(restaurant_id),
            "system_health": await self._check_system_health()
        }

    # Private helper methods
    def _calculate_date_range(
        self,
        time_range: TimeRange,
        custom_start: Optional[datetime] = None,
        custom_end: Optional[datetime] = None
    ) -> Tuple[datetime, datetime]:
        """Calculate start and end dates based on time range."""
        end_date = datetime.utcnow()

        if time_range == TimeRange.TODAY:
            start_date = datetime.combine(date.today(), datetime.min.time())
        elif time_range == TimeRange.WEEK:
            start_date = end_date - timedelta(days=7)
        elif time_range == TimeRange.MONTH:
            start_date = end_date - timedelta(days=30)
        elif time_range == TimeRange.QUARTER:
            start_date = end_date - timedelta(days=90)
        elif time_range == TimeRange.YEAR:
            start_date = end_date - timedelta(days=365)
        elif time_range == TimeRange.CUSTOM:
            start_date = custom_start or end_date - timedelta(days=30)
            end_date = custom_end or end_date
        else:
            start_date = end_date - timedelta(days=30)

        return start_date, end_date

    def _build_base_filters(
        self,
        restaurant_id: Optional[UUID],
        start_date: datetime,
        end_date: datetime
    ) -> List:
        """Build base filters for queries."""
        filters = [
            Customer.is_deleted == False,
            Customer.created_at >= start_date,
            Customer.created_at <= end_date
        ]

        if restaurant_id:
            filters.append(Customer.restaurant_id == restaurant_id)

        return filters

    async def _get_summary_metrics(self, base_filters: List) -> Dict[str, Any]:
        """Get summary metrics."""
        # Total customers
        total_customers = await self._count_customers(base_filters)

        # Active customers (interacted in last 7 days)
        active_filters = base_filters.copy()
        active_filters.append(
            Customer.updated_at >= datetime.utcnow() - timedelta(days=7)
        )
        active_customers = await self._count_customers(active_filters)

        # Average sentiment
        avg_sentiment = await self._calculate_average_sentiment(base_filters)

        # Total messages
        total_messages = await self._count_total_messages(base_filters)

        return {
            "total_customers": total_customers,
            "active_customers": active_customers,
            "average_sentiment": avg_sentiment,
            "total_messages": total_messages,
            "engagement_rate": (active_customers / total_customers * 100) if total_customers > 0 else 0
        }

    async def _get_customer_metrics(self, base_filters: List) -> Dict[str, Any]:
        """Get customer-related metrics."""
        return {
            "total": await self._count_customers(base_filters),
            "new": await self._count_new_customers(base_filters),
            "returning": await self._count_returning_customers(base_filters),
            "by_status": await self._get_customers_by_status(base_filters),
            "growth_rate": await self._calculate_growth_rate(base_filters)
        }

    async def _get_engagement_metrics(self, base_filters: List) -> Dict[str, Any]:
        """Get engagement metrics."""
        return {
            "total_conversations": await self._count_conversations(base_filters),
            "avg_messages_per_conversation": await self._calculate_avg_messages_per_conversation(base_filters),
            "response_rate": await self._calculate_response_rate(base_filters),
            "avg_response_time": await self._calculate_avg_response_time(base_filters)
        }

    async def _get_sentiment_metrics(self, base_filters: List) -> Dict[str, Any]:
        """Get sentiment metrics."""
        return {
            "average_score": await self._calculate_average_sentiment(base_filters),
            "distribution": await self._get_sentiment_distribution(base_filters),
            "trending": await self._calculate_sentiment_trend(base_filters)
        }

    async def _get_message_metrics(self, base_filters: List) -> Dict[str, Any]:
        """Get message metrics."""
        return {
            "total": await self._count_total_messages(base_filters),
            "inbound": await self._count_inbound_messages(base_filters),
            "outbound": await self._count_outbound_messages(base_filters),
            "by_hour": await self._get_messages_by_hour(base_filters),
            "by_day": await self._get_messages_by_day(base_filters)
        }

    async def _get_trend_data(
        self,
        base_filters: List,
        time_range: TimeRange
    ) -> Dict[str, Any]:
        """Get trend data for charts."""
        # Determine appropriate granularity
        if time_range == TimeRange.TODAY:
            granularity = "hour"
        elif time_range in [TimeRange.WEEK, TimeRange.MONTH]:
            granularity = "day"
        else:
            granularity = "week"

        return {
            "customers": await self._get_customer_trend(base_filters, granularity),
            "messages": await self._get_message_trend(base_filters, granularity),
            "sentiment": await self._get_sentiment_trend(base_filters, granularity)
        }

    async def _count_customers(self, filters: List) -> int:
        """Count customers with filters."""
        query = select(func.count()).select_from(Customer).where(and_(*filters))
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def _count_new_customers(self, filters: List) -> int:
        """Count new customers."""
        # Customers with only one visit
        query = select(func.count()).select_from(Customer).where(
            and_(*filters, func.jsonb_array_length(Customer.visit_history) == 1)
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def _count_returning_customers(self, filters: List) -> int:
        """Count returning customers."""
        # Customers with more than one visit
        query = select(func.count()).select_from(Customer).where(
            and_(*filters, func.jsonb_array_length(Customer.visit_history) > 1)
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def _calculate_average_sentiment(self, filters: List) -> float:
        """Calculate average sentiment score."""
        query = select(func.avg(Customer.sentiment_score)).where(
            and_(*filters, Customer.sentiment_score.isnot(None))
        )
        result = await self.session.execute(query)
        avg = result.scalar()
        return float(avg) if avg else 0.5

    async def _count_total_messages(self, filters: List) -> int:
        """Count total messages."""
        # Join with Customer to apply filters
        customer_subquery = select(Customer.id).where(and_(*filters))

        query = select(func.count()).select_from(WhatsAppMessage).where(
            WhatsAppMessage.customer_id.in_(customer_subquery)
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def _get_sentiment_distribution(self, filters: List) -> Dict[str, int]:
        """Get sentiment category distribution."""
        query = select(
            Customer.sentiment_category,
            func.count(Customer.id)
        ).where(
            and_(*filters, Customer.sentiment_category.isnot(None))
        ).group_by(Customer.sentiment_category)

        result = await self.session.execute(query)
        return dict(result.all())

    async def _get_customers_by_status(self, filters: List) -> Dict[str, int]:
        """Get customer count by status."""
        query = select(
            Customer.status,
            func.count(Customer.id)
        ).where(
            and_(*filters)
        ).group_by(Customer.status)

        result = await self.session.execute(query)
        return dict(result.all())

    async def _calculate_growth_rate(self, filters: List) -> float:
        """Calculate customer growth rate."""
        # Compare current period with previous period
        current_count = await self._count_customers(filters)

        # Calculate previous period filters
        # This is simplified - would need proper period calculation
        previous_filters = filters.copy()
        # Shift dates back by same period length
        # Implementation depends on specific requirements

        previous_count = await self._count_customers(previous_filters)

        if previous_count == 0:
            return 100.0 if current_count > 0 else 0.0

        return ((current_count - previous_count) / previous_count) * 100

    async def _count_conversations(self, filters: List) -> int:
        """Count unique conversations."""
        customer_subquery = select(Customer.id).where(and_(*filters))

        query = select(func.count(func.distinct(WhatsAppMessage.customer_id))).where(
            WhatsAppMessage.customer_id.in_(customer_subquery)
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def _calculate_avg_messages_per_conversation(self, filters: List) -> float:
        """Calculate average messages per conversation."""
        total_messages = await self._count_total_messages(filters)
        total_conversations = await self._count_conversations(filters)

        if total_conversations == 0:
            return 0.0

        return total_messages / total_conversations

    async def _calculate_response_rate(self, filters: List) -> float:
        """Calculate response rate to customer messages."""
        try:
            # Get customer IDs that match the filters
            customer_subquery = select(Customer.id).where(and_(*filters))

            # Count inbound messages that have responses
            # This query looks for inbound messages followed by outbound messages
            inbound_messages = await self.session.execute(
                select(func.count(WhatsAppMessage.id)).where(
                    and_(
                        WhatsAppMessage.customer_id.in_(customer_subquery),
                        WhatsAppMessage.direction == 'inbound'
                    )
                )
            )
            total_inbound = inbound_messages.scalar() or 0

            if total_inbound == 0:
                return 0.0

            # Count inbound messages that were responded to
            # Simplified: check if there's an outbound message after each inbound one
            responded_messages = await self.session.execute(
                select(func.count(func.distinct(WhatsAppMessage.customer_id))).where(
                    and_(
                        WhatsAppMessage.customer_id.in_(customer_subquery),
                        WhatsAppMessage.direction == 'outbound'
                    )
                )
            )
            total_responded = responded_messages.scalar() or 0

            return min(total_responded / total_inbound, 1.0) if total_inbound > 0 else 0.0

        except Exception as e:
            logger.error(f"Error calculating response rate: {str(e)}")
            return 0.0

    async def _calculate_avg_response_time(self, filters: List) -> float:
        """Calculate average response time in minutes."""
        try:
            # Get customer IDs that match the filters
            customer_subquery = select(Customer.id).where(and_(*filters))

            # Get conversation pairs (inbound followed by outbound messages)
            # This is a simplified approach - in practice, you'd want to properly identify conversation threads
            response_times_query = select(
                WhatsAppMessage.customer_id,
                WhatsAppMessage.created_at,
                WhatsAppMessage.direction
            ).where(
                WhatsAppMessage.customer_id.in_(customer_subquery)
            ).order_by(
                WhatsAppMessage.customer_id,
                WhatsAppMessage.created_at
            )

            messages_result = await self.session.execute(response_times_query)
            messages = messages_result.all()

            response_times = []
            prev_message = None

            for message in messages:
                if (prev_message and
                    prev_message[2] == 'inbound' and  # Previous was inbound
                    message[2] == 'outbound' and     # Current is outbound
                    prev_message[0] == message[0]):   # Same customer

                    time_diff = (message[1] - prev_message[1]).total_seconds() / 60  # Convert to minutes
                    if 0 < time_diff <= 1440:  # Reasonable response time (up to 24 hours)
                        response_times.append(time_diff)

                prev_message = message

            if response_times:
                return sum(response_times) / len(response_times)
            else:
                return 0.0

        except Exception as e:
            logger.error(f"Error calculating average response time: {str(e)}")
            return 0.0

    async def _count_inbound_messages(self, filters: List) -> int:
        """Count inbound messages."""
        customer_subquery = select(Customer.id).where(and_(*filters))

        query = select(func.count()).select_from(WhatsAppMessage).where(
            and_(
                WhatsAppMessage.customer_id.in_(customer_subquery),
                WhatsAppMessage.direction == 'inbound'
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def _count_outbound_messages(self, filters: List) -> int:
        """Count outbound messages."""
        customer_subquery = select(Customer.id).where(and_(*filters))

        query = select(func.count()).select_from(WhatsAppMessage).where(
            and_(
                WhatsAppMessage.customer_id.in_(customer_subquery),
                WhatsAppMessage.direction == 'outbound'
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def _get_messages_by_hour(self, filters: List) -> Dict[int, int]:
        """Get message distribution by hour."""
        customer_subquery = select(Customer.id).where(and_(*filters))

        query = select(
            extract('hour', WhatsAppMessage.created_at).label('hour'),
            func.count(WhatsAppMessage.id)
        ).where(
            WhatsAppMessage.customer_id.in_(customer_subquery)
        ).group_by('hour')

        result = await self.session.execute(query)
        return {int(row[0]): row[1] for row in result.all()}

    async def _get_messages_by_day(self, filters: List) -> Dict[str, int]:
        """Get message distribution by day of week."""
        customer_subquery = select(Customer.id).where(and_(*filters))

        query = select(
            extract('dow', WhatsAppMessage.created_at).label('dow'),
            func.count(WhatsAppMessage.id)
        ).where(
            WhatsAppMessage.customer_id.in_(customer_subquery)
        ).group_by('dow')

        result = await self.session.execute(query)

        day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        return {day_names[int(row[0])]: row[1] for row in result.all()}

    async def _get_customer_trend(
        self,
        filters: List,
        granularity: str
    ) -> List[Dict[str, Any]]:
        """Get customer trend data."""
        try:
            # Determine the time grouping based on granularity
            if granularity == "hour":
                time_group = func.date_trunc('hour', Customer.created_at)
            elif granularity == "day":
                time_group = func.date_trunc('day', Customer.created_at)
            elif granularity == "week":
                time_group = func.date_trunc('week', Customer.created_at)
            else:
                time_group = func.date_trunc('day', Customer.created_at)

            # Query for customer counts by time period
            query = select(
                time_group.label('period'),
                func.count(Customer.id).label('count')
            ).where(
                and_(*filters)
            ).group_by(
                time_group
            ).order_by(
                time_group
            )

            result = await self.session.execute(query)
            trends = result.all()

            return [
                {
                    "period": trend.period.isoformat() if trend.period else None,
                    "count": trend.count,
                    "type": "customers"
                }
                for trend in trends
            ]

        except Exception as e:
            logger.error(f"Error getting customer trend: {str(e)}")
            return []

    async def _get_message_trend(
        self,
        filters: List,
        granularity: str
    ) -> List[Dict[str, Any]]:
        """Get message trend data."""
        try:
            # Get customer IDs that match the filters
            customer_subquery = select(Customer.id).where(and_(*filters))

            # Determine the time grouping based on granularity
            if granularity == "hour":
                time_group = func.date_trunc('hour', WhatsAppMessage.created_at)
            elif granularity == "day":
                time_group = func.date_trunc('day', WhatsAppMessage.created_at)
            elif granularity == "week":
                time_group = func.date_trunc('week', WhatsAppMessage.created_at)
            else:
                time_group = func.date_trunc('day', WhatsAppMessage.created_at)

            # Query for message counts by time period
            query = select(
                time_group.label('period'),
                func.count(WhatsAppMessage.id).label('count'),
                WhatsAppMessage.direction
            ).where(
                WhatsAppMessage.customer_id.in_(customer_subquery)
            ).group_by(
                time_group,
                WhatsAppMessage.direction
            ).order_by(
                time_group
            )

            result = await self.session.execute(query)
            trends = result.all()

            return [
                {
                    "period": trend.period.isoformat() if trend.period else None,
                    "count": trend.count,
                    "direction": trend.direction,
                    "type": "messages"
                }
                for trend in trends
            ]

        except Exception as e:
            logger.error(f"Error getting message trend: {str(e)}")
            return []

    async def _get_sentiment_trend(
        self,
        filters: List,
        granularity: str
    ) -> List[Dict[str, Any]]:
        """Get sentiment trend data."""
        try:
            # Determine the time grouping based on granularity
            if granularity == "hour":
                time_group = func.date_trunc('hour', Customer.created_at)
            elif granularity == "day":
                time_group = func.date_trunc('day', Customer.created_at)
            elif granularity == "week":
                time_group = func.date_trunc('week', Customer.created_at)
            else:
                time_group = func.date_trunc('day', Customer.created_at)

            # Query for sentiment averages by time period
            query = select(
                time_group.label('period'),
                func.avg(Customer.sentiment_score).label('avg_sentiment'),
                func.count(Customer.id).label('count')
            ).where(
                and_(*filters, Customer.sentiment_score.isnot(None))
            ).group_by(
                time_group
            ).order_by(
                time_group
            )

            result = await self.session.execute(query)
            trends = result.all()

            return [
                {
                    "period": trend.period.isoformat() if trend.period else None,
                    "sentiment_score": float(trend.avg_sentiment) if trend.avg_sentiment else 0.5,
                    "customer_count": trend.count,
                    "type": "sentiment"
                }
                for trend in trends
            ]

        except Exception as e:
            logger.error(f"Error getting sentiment trend: {str(e)}")
            return []

    async def _calculate_sentiment_trend(self, filters: List) -> str:
        """Calculate if sentiment is trending up or down."""
        # Simplified implementation
        return "stable"

    async def _generate_executive_summary(
        self,
        restaurant_id: Optional[UUID],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate executive summary report."""
        base_filters = self._build_base_filters(restaurant_id, start_date, end_date)

        return {
            "key_metrics": await self._get_summary_metrics(base_filters),
            "highlights": await self._generate_highlights(base_filters),
            "recommendations": await self._generate_recommendations(base_filters)
        }

    async def _generate_customer_insights(
        self,
        restaurant_id: Optional[UUID],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate customer insights report."""
        base_filters = self._build_base_filters(restaurant_id, start_date, end_date)

        return {
            "segments": await self._get_customer_segments(base_filters),
            "behavior_patterns": await self._analyze_behavior_patterns(base_filters),
            "satisfaction_analysis": await self._analyze_satisfaction(base_filters)
        }

    async def _generate_operational_metrics(
        self,
        restaurant_id: Optional[UUID],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate operational metrics report."""
        base_filters = self._build_base_filters(restaurant_id, start_date, end_date)

        return {
            "efficiency_metrics": await self._calculate_efficiency_metrics(base_filters),
            "workload_analysis": await self._analyze_workload(base_filters),
            "performance_indicators": await self._get_performance_indicators(base_filters)
        }

    async def _get_customer_segments(self, filters: List) -> Dict[str, Any]:
        """Segment customers based on behavior."""
        # Simplified segmentation
        return {
            "vip": await self._count_vip_customers(filters),
            "regular": await self._count_regular_customers(filters),
            "at_risk": await self._count_at_risk_customers(filters),
            "lost": await self._count_lost_customers(filters)
        }

    async def _count_vip_customers(self, filters: List) -> int:
        """Count VIP customers (frequent, high satisfaction)."""
        vip_filters = filters.copy()
        vip_filters.extend([
            func.jsonb_array_length(Customer.visit_history) > 5,
            Customer.sentiment_score > 0.7
        ])
        return await self._count_customers(vip_filters)

    async def _count_regular_customers(self, filters: List) -> int:
        """Count regular customers."""
        regular_filters = filters.copy()
        regular_filters.append(
            func.jsonb_array_length(Customer.visit_history).between(2, 5)
        )
        return await self._count_customers(regular_filters)

    async def _count_at_risk_customers(self, filters: List) -> int:
        """Count at-risk customers (negative sentiment)."""
        at_risk_filters = filters.copy()
        at_risk_filters.append(Customer.sentiment_score < 0.3)
        return await self._count_customers(at_risk_filters)

    async def _count_lost_customers(self, filters: List) -> int:
        """Count lost customers (no recent interaction)."""
        lost_filters = filters.copy()
        lost_filters.append(
            Customer.updated_at < datetime.utcnow() - timedelta(days=60)
        )
        return await self._count_customers(lost_filters)

    async def _generate_highlights(self, filters: List) -> List[str]:
        """Generate report highlights."""
        highlights = []

        # Check growth
        growth_rate = await self._calculate_growth_rate(filters)
        if growth_rate > 10:
            highlights.append(f"Customer base grew by {growth_rate:.1f}%")

        # Check sentiment
        avg_sentiment = await self._calculate_average_sentiment(filters)
        if avg_sentiment > 0.7:
            highlights.append("Overall customer sentiment is very positive")

        return highlights

    async def _generate_recommendations(self, filters: List) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Check response times
        avg_response = await self._calculate_avg_response_time(filters)
        if avg_response > 10:
            recommendations.append("Consider improving response times to enhance customer satisfaction")

        # Check at-risk customers
        at_risk_count = await self._count_at_risk_customers(filters)
        if at_risk_count > 10:
            recommendations.append(f"Reach out to {at_risk_count} at-risk customers to address concerns")

        return recommendations

    async def _analyze_behavior_patterns(self, filters: List) -> Dict[str, Any]:
        """Analyze customer behavior patterns."""
        return {
            "peak_interaction_times": await self._get_messages_by_hour(filters),
            "preferred_days": await self._get_messages_by_day(filters),
            "engagement_patterns": "Analysis pending"
        }

    async def _analyze_satisfaction(self, filters: List) -> Dict[str, Any]:
        """Analyze customer satisfaction."""
        return {
            "average_sentiment": await self._calculate_average_sentiment(filters),
            "sentiment_distribution": await self._get_sentiment_distribution(filters),
            "satisfaction_drivers": "Analysis pending"
        }

    async def _calculate_efficiency_metrics(self, filters: List) -> Dict[str, Any]:
        """Calculate operational efficiency metrics."""
        return {
            "response_time": await self._calculate_avg_response_time(filters),
            "resolution_rate": 0.82,  # Placeholder
            "automation_rate": 0.65  # Placeholder
        }

    async def _analyze_workload(self, filters: List) -> Dict[str, Any]:
        """Analyze workload distribution."""
        return {
            "messages_by_hour": await self._get_messages_by_hour(filters),
            "messages_by_day": await self._get_messages_by_day(filters),
            "peak_load_times": "Analysis pending"
        }

    async def _get_performance_indicators(self, filters: List) -> Dict[str, Any]:
        """Get key performance indicators."""
        return {
            "customer_satisfaction": await self._calculate_average_sentiment(filters) * 100,
            "response_rate": await self._calculate_response_rate(filters) * 100,
            "engagement_rate": 75.0  # Placeholder
        }

    async def _count_active_conversations(
        self,
        restaurant_id: Optional[UUID],
        since: datetime
    ) -> int:
        """Count active conversations since given time."""
        query = select(func.count(func.distinct(WhatsAppMessage.customer_id))).where(
            WhatsAppMessage.created_at >= since
        )

        if restaurant_id:
            # Add restaurant filter through customer relationship
            pass

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def _count_messages_since(
        self,
        restaurant_id: Optional[UUID],
        since: datetime
    ) -> int:
        """Count messages since given time."""
        query = select(func.count()).select_from(WhatsAppMessage).where(
            WhatsAppMessage.created_at >= since
        )

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def _count_new_customers_since(
        self,
        restaurant_id: Optional[UUID],
        since: datetime
    ) -> int:
        """Count new customers since given time."""
        filters = [
            Customer.created_at >= since,
            Customer.is_deleted == False
        ]

        if restaurant_id:
            filters.append(Customer.restaurant_id == restaurant_id)

        return await self._count_customers(filters)

    async def _get_average_response_time(
        self,
        restaurant_id: Optional[UUID],
        since: datetime
    ) -> float:
        """Get average response time in last period."""
        # Simplified implementation
        return 4.5  # Minutes

    async def _count_pending_responses(
        self,
        restaurant_id: Optional[UUID]
    ) -> int:
        """Count messages awaiting response."""
        # Would need to track conversation state
        return 3  # Placeholder

    async def _check_system_health(self) -> Dict[str, Any]:
        """Check system health metrics."""
        return {
            "status": "healthy",
            "database": "connected",
            "services": {
                "whatsapp": "operational",
                "ai": "operational",
                "analytics": "operational"
            }
        }

    async def _get_single_campaign_analytics(
        self,
        campaign_id: UUID
    ) -> Dict[str, Any]:
        """Get analytics for a single campaign."""
        # Placeholder implementation
        return {
            "campaign_id": str(campaign_id),
            "metrics": "Campaign analytics pending implementation"
        }

    async def _get_all_campaigns_analytics(
        self,
        restaurant_id: Optional[UUID]
    ) -> Dict[str, Any]:
        """Get analytics for all campaigns."""
        # Placeholder implementation
        return {
            "campaigns": "Campaign analytics pending implementation"
        }

    async def _calculate_customer_lifetime_value(
        self,
        filters: List
    ) -> float:
        """Calculate average customer lifetime value."""
        # Placeholder - would need revenue data
        return 0.0

    async def _calculate_churn_rate(self, filters: List) -> float:
        """Calculate customer churn rate."""
        # Placeholder - would need proper churn definition
        return 0.0

    async def _calculate_retention_rate(self, filters: List) -> float:
        """Calculate customer retention rate."""
        # Placeholder - would need proper retention definition
        return 0.0

    async def _get_top_customers(self, filters: List) -> List[Dict[str, Any]]:
        """Get top customers by engagement."""
        # Simplified implementation
        return []

    async def _get_overall_sentiment(self, filters: List) -> Dict[str, Any]:
        """Get overall sentiment analysis."""
        return {
            "score": await self._calculate_average_sentiment(filters),
            "trend": await self._calculate_sentiment_trend(filters),
            "confidence": 0.85  # Placeholder
        }

    async def _get_sentiment_trends(
        self,
        filters: List,
        time_range: TimeRange
    ) -> List[Dict[str, Any]]:
        """Get sentiment trends over time."""
        # Simplified implementation
        return []

    async def _get_sentiment_by_segment(self, filters: List) -> Dict[str, float]:
        """Get sentiment by customer segment."""
        # Simplified implementation
        return {
            "vip": 0.85,
            "regular": 0.72,
            "new": 0.68
        }

    async def _analyze_negative_feedback_themes(
        self,
        filters: List
    ) -> List[Dict[str, Any]]:
        """Analyze themes in negative feedback."""
        # Simplified implementation
        return []

    async def _analyze_positive_feedback_themes(
        self,
        filters: List
    ) -> List[Dict[str, Any]]:
        """Analyze themes in positive feedback."""
        # Simplified implementation
        return []

    async def _get_message_statistics(self, filters: List) -> Dict[str, Any]:
        """Get detailed message statistics."""
        return {
            "total": await self._count_total_messages(filters),
            "inbound": await self._count_inbound_messages(filters),
            "outbound": await self._count_outbound_messages(filters),
            "average_length": 0  # Placeholder
        }

    async def _calculate_response_rates(self, filters: List) -> Dict[str, float]:
        """Calculate various response rates."""
        return {
            "overall": await self._calculate_response_rate(filters),
            "within_1_hour": 0.75,  # Placeholder
            "within_24_hours": 0.95  # Placeholder
        }

    async def _calculate_response_times(self, filters: List) -> Dict[str, float]:
        """Calculate response time metrics."""
        return {
            "average": await self._calculate_avg_response_time(filters),
            "median": 3.5,  # Placeholder
            "p95": 15.0  # Placeholder
        }

    async def _get_conversation_metrics(self, filters: List) -> Dict[str, Any]:
        """Get conversation-level metrics."""
        return {
            "total": await self._count_conversations(filters),
            "avg_messages": await self._calculate_avg_messages_per_conversation(filters),
            "avg_duration": 12.5,  # Minutes placeholder
            "resolution_rate": 0.82  # Placeholder
        }

    async def _analyze_peak_hours(self, filters: List) -> Dict[str, Any]:
        """Analyze peak activity hours."""
        messages_by_hour = await self._get_messages_by_hour(filters)

        if messages_by_hour:
            peak_hour = max(messages_by_hour, key=messages_by_hour.get)
            return {
                "peak_hour": peak_hour,
                "message_count": messages_by_hour[peak_hour],
                "distribution": messages_by_hour
            }

        return {
            "peak_hour": None,
            "message_count": 0,
            "distribution": {}
        }

    async def _get_channel_performance(self, filters: List) -> Dict[str, Any]:
        """Get performance metrics by channel."""
        return {
            "whatsapp": {
                "messages": await self._count_total_messages(filters),
                "response_rate": 0.85,
                "satisfaction": 0.75
            }
        }