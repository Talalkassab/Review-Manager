"""
Database Query Optimization Module
Provides utilities for optimizing database queries, preventing N+1 problems,
and monitoring query performance.
"""
import time
import asyncio
from typing import Any, Dict, List, Optional, Type, Union
from uuid import UUID
from contextlib import asynccontextmanager
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, event, inspect
from sqlalchemy.orm import selectinload, joinedload, contains_eager, Load
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool

from ...core.logging import get_logger
from ...core.config import settings
from ...models.customer import Customer
from ...models.whatsapp import WhatsAppMessage
from ...models.ai_agent import AIInteraction

logger = get_logger(__name__)


@dataclass
class QueryPerformanceMetrics:
    """Query performance metrics data class."""
    query_hash: str
    query_text: str
    execution_count: int
    total_duration_ms: float
    avg_duration_ms: float
    max_duration_ms: float
    min_duration_ms: float
    is_slow: bool
    n_plus_one_detected: bool


class QueryOptimizer:
    """Database query optimization utilities."""

    def __init__(self):
        self.query_metrics: Dict[str, QueryPerformanceMetrics] = {}
        self.slow_query_threshold_ms = getattr(settings.logging, 'SLOW_QUERY_THRESHOLD_MS', 500)
        self.n_plus_one_detection_enabled = True

    @asynccontextmanager
    async def track_query_performance(self, query_description: str):
        """Context manager to track query performance."""
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000

            if duration_ms > self.slow_query_threshold_ms:
                logger.warning(
                    f"Slow query detected: {query_description}",
                    duration_ms=duration_ms,
                    threshold_ms=self.slow_query_threshold_ms
                )

    # Customer Query Optimizations

    async def get_customers_with_messages_optimized(
        self,
        session: AsyncSession,
        restaurant_id: UUID,
        limit: int = 100,
        include_message_count: bool = True
    ) -> List[Customer]:
        """
        Optimized query to get customers with their message counts.
        Prevents N+1 queries by using joins and subqueries.
        """
        async with self.track_query_performance("customers_with_messages"):
            if include_message_count:
                # Use subquery to get message counts efficiently
                message_count_subquery = (
                    select(
                        WhatsAppMessage.customer_id,
                        func.count(WhatsAppMessage.id).label('message_count')
                    )
                    .where(WhatsAppMessage.customer_id.isnot(None))
                    .group_by(WhatsAppMessage.customer_id)
                    .subquery()
                )

                stmt = (
                    select(Customer, message_count_subquery.c.message_count)
                    .outerjoin(
                        message_count_subquery,
                        Customer.id == message_count_subquery.c.customer_id
                    )
                    .where(
                        Customer.restaurant_id == restaurant_id,
                        Customer.is_deleted == False
                    )
                    .order_by(Customer.created_at.desc())
                    .limit(limit)
                )

                result = await session.execute(stmt)
                customers_with_counts = result.all()

                # Attach message counts to customer objects
                customers = []
                for customer, message_count in customers_with_counts:
                    customer._message_count = message_count or 0
                    customers.append(customer)

                return customers
            else:
                stmt = (
                    select(Customer)
                    .where(
                        Customer.restaurant_id == restaurant_id,
                        Customer.is_deleted == False
                    )
                    .order_by(Customer.created_at.desc())
                    .limit(limit)
                )

                result = await session.execute(stmt)
                return result.scalars().all()

    async def get_customer_with_full_conversation_history(
        self,
        session: AsyncSession,
        customer_id: UUID,
        message_limit: int = 50
    ) -> Optional[Customer]:
        """
        Optimized query to get customer with full conversation history.
        Uses eager loading to prevent N+1 queries.
        """
        async with self.track_query_performance("customer_with_conversation"):
            # Use selectinload for efficient eager loading
            stmt = (
                select(Customer)
                .options(
                    selectinload(Customer.whatsapp_messages)
                    .options(
                        selectinload(WhatsAppMessage.sent_by_user)
                    ),
                    selectinload(Customer.ai_interactions),
                    selectinload(Customer.restaurant),
                    selectinload(Customer.created_by_user)
                )
                .where(
                    Customer.id == customer_id,
                    Customer.is_deleted == False
                )
            )

            result = await session.execute(stmt)
            customer = result.scalar_one_or_none()

            if customer:
                # Sort messages by date and limit if necessary
                customer.whatsapp_messages.sort(key=lambda m: m.created_at, reverse=True)
                if len(customer.whatsapp_messages) > message_limit:
                    customer.whatsapp_messages = customer.whatsapp_messages[:message_limit]

            return customer

    async def get_customers_with_recent_activity(
        self,
        session: AsyncSession,
        restaurant_id: UUID,
        days_back: int = 7,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Optimized query to get customers with their recent activity summary.
        Uses efficient joins to prevent N+1 queries.
        """
        async with self.track_query_performance("customers_recent_activity"):
            # Calculate cutoff date
            from datetime import datetime, timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)

            # Subquery for recent messages
            recent_messages_subquery = (
                select(
                    WhatsAppMessage.customer_id,
                    func.count(WhatsAppMessage.id).label('recent_message_count'),
                    func.max(WhatsAppMessage.created_at).label('last_message_at')
                )
                .where(
                    WhatsAppMessage.created_at >= cutoff_date,
                    WhatsAppMessage.customer_id.isnot(None)
                )
                .group_by(WhatsAppMessage.customer_id)
                .subquery()
            )

            # Main query with joins
            stmt = (
                select(
                    Customer,
                    recent_messages_subquery.c.recent_message_count,
                    recent_messages_subquery.c.last_message_at
                )
                .outerjoin(
                    recent_messages_subquery,
                    Customer.id == recent_messages_subquery.c.customer_id
                )
                .where(
                    Customer.restaurant_id == restaurant_id,
                    Customer.is_deleted == False,
                    # Only customers with recent activity
                    recent_messages_subquery.c.recent_message_count > 0
                )
                .order_by(recent_messages_subquery.c.last_message_at.desc())
                .limit(limit)
            )

            result = await session.execute(stmt)

            customers_data = []
            for customer, message_count, last_message_at in result.all():
                customers_data.append({
                    'customer': customer,
                    'recent_message_count': message_count or 0,
                    'last_message_at': last_message_at,
                    'days_since_last_message': (datetime.utcnow() - (last_message_at or datetime.utcnow())).days
                })

            return customers_data

    # Analytics Query Optimizations

    async def get_customer_analytics_optimized(
        self,
        session: AsyncSession,
        restaurant_id: Optional[UUID] = None,
        date_range_days: int = 30
    ) -> Dict[str, Any]:
        """
        Optimized analytics query that calculates multiple metrics efficiently.
        Uses single queries with aggregations instead of multiple round trips.
        """
        async with self.track_query_performance("customer_analytics"):
            from datetime import datetime, timedelta

            cutoff_date = datetime.utcnow() - timedelta(days=date_range_days)

            # Build base filter conditions
            customer_filters = [Customer.is_deleted == False]
            message_filters = [WhatsAppMessage.created_at >= cutoff_date]

            if restaurant_id:
                customer_filters.append(Customer.restaurant_id == restaurant_id)
                message_filters.append(WhatsAppMessage.restaurant_id == restaurant_id)

            # Single query for customer metrics
            customer_metrics_query = (
                select(
                    func.count(Customer.id).label('total_customers'),
                    func.count(
                        case((Customer.created_at >= cutoff_date, Customer.id))
                    ).label('new_customers'),
                    func.count(
                        case((Customer.visit_count > 1, Customer.id))
                    ).label('returning_customers'),
                    func.avg(Customer.rating).label('avg_rating'),
                    func.count(
                        case((Customer.feedback_sentiment == 'positive', Customer.id))
                    ).label('positive_feedback'),
                    func.count(
                        case((Customer.feedback_sentiment == 'negative', Customer.id))
                    ).label('negative_feedback'),
                    func.count(
                        case((Customer.feedback_text.isnot(None), Customer.id))
                    ).label('customers_with_feedback')
                )
                .where(and_(*customer_filters))
            )

            # Single query for message metrics
            message_metrics_query = (
                select(
                    func.count(WhatsAppMessage.id).label('total_messages'),
                    func.count(
                        case((WhatsAppMessage.direction == 'inbound', WhatsAppMessage.id))
                    ).label('inbound_messages'),
                    func.count(
                        case((WhatsAppMessage.direction == 'outbound', WhatsAppMessage.id))
                    ).label('outbound_messages'),
                    func.count(
                        func.distinct(WhatsAppMessage.customer_id)
                    ).label('active_customers')
                )
                .where(and_(*message_filters))
            )

            # Execute queries concurrently
            customer_result, message_result = await asyncio.gather(
                session.execute(customer_metrics_query),
                session.execute(message_metrics_query)
            )

            customer_metrics = customer_result.one()
            message_metrics = message_result.one()

            # Calculate derived metrics
            total_customers = customer_metrics.total_customers or 0
            customers_with_feedback = customer_metrics.customers_with_feedback or 0
            positive_feedback = customer_metrics.positive_feedback or 0
            negative_feedback = customer_metrics.negative_feedback or 0

            response_rate = (customers_with_feedback / total_customers * 100) if total_customers > 0 else 0
            positive_rate = (positive_feedback / customers_with_feedback * 100) if customers_with_feedback > 0 else 0

            return {
                'total_customers': total_customers,
                'new_customers': customer_metrics.new_customers or 0,
                'returning_customers': customer_metrics.returning_customers or 0,
                'active_customers': message_metrics.active_customers or 0,
                'avg_rating': float(customer_metrics.avg_rating or 0),
                'total_messages': message_metrics.total_messages or 0,
                'inbound_messages': message_metrics.inbound_messages or 0,
                'outbound_messages': message_metrics.outbound_messages or 0,
                'response_rate': round(response_rate, 2),
                'positive_feedback_rate': round(positive_rate, 2),
                'feedback_summary': {
                    'positive': positive_feedback,
                    'negative': negative_feedback,
                    'total': customers_with_feedback
                }
            }

    # Connection Pool Optimization

    def configure_connection_pool(self, engine) -> None:
        """Configure SQLAlchemy connection pool for optimal performance."""
        if hasattr(engine.pool, 'size'):
            # Configure pool parameters based on environment
            if settings.app.ENVIRONMENT == "production":
                # Production settings - larger pool
                pool_size = 20
                max_overflow = 30
                pool_timeout = 30
                pool_recycle = 3600  # 1 hour
            else:
                # Development settings - smaller pool
                pool_size = 5
                max_overflow = 10
                pool_timeout = 10
                pool_recycle = 1800  # 30 minutes

            # Apply pool configuration
            if isinstance(engine.pool, QueuePool):
                engine.pool._size = pool_size
                engine.pool._max_overflow = max_overflow
                engine.pool._timeout = pool_timeout
                engine.pool._recycle = pool_recycle

                logger.info(
                    "Connection pool configured",
                    pool_size=pool_size,
                    max_overflow=max_overflow,
                    pool_timeout=pool_timeout,
                    pool_recycle=pool_recycle
                )

    # Query Performance Monitoring

    def setup_query_monitoring(self, engine) -> None:
        """Set up query performance monitoring."""

        @event.listens_for(engine.sync_engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
            context._query_statement = statement

        @event.listens_for(engine.sync_engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            if hasattr(context, '_query_start_time'):
                duration_ms = (time.time() - context._query_start_time) * 1000

                # Log slow queries
                if duration_ms > self.slow_query_threshold_ms:
                    logger.warning(
                        "Slow query detected",
                        duration_ms=duration_ms,
                        statement=statement[:200] + "..." if len(statement) > 200 else statement,
                        threshold_ms=self.slow_query_threshold_ms
                    )

                # Track query metrics
                query_hash = str(hash(statement))
                if query_hash in self.query_metrics:
                    metrics = self.query_metrics[query_hash]
                    metrics.execution_count += 1
                    metrics.total_duration_ms += duration_ms
                    metrics.avg_duration_ms = metrics.total_duration_ms / metrics.execution_count
                    metrics.max_duration_ms = max(metrics.max_duration_ms, duration_ms)
                    metrics.min_duration_ms = min(metrics.min_duration_ms, duration_ms)
                    metrics.is_slow = duration_ms > self.slow_query_threshold_ms
                else:
                    self.query_metrics[query_hash] = QueryPerformanceMetrics(
                        query_hash=query_hash,
                        query_text=statement[:500],
                        execution_count=1,
                        total_duration_ms=duration_ms,
                        avg_duration_ms=duration_ms,
                        max_duration_ms=duration_ms,
                        min_duration_ms=duration_ms,
                        is_slow=duration_ms > self.slow_query_threshold_ms,
                        n_plus_one_detected=False
                    )

    def get_query_performance_report(self) -> Dict[str, Any]:
        """Generate a query performance report."""
        slow_queries = [m for m in self.query_metrics.values() if m.is_slow]
        frequent_queries = sorted(
            self.query_metrics.values(),
            key=lambda m: m.execution_count,
            reverse=True
        )[:10]

        return {
            "total_queries_monitored": len(self.query_metrics),
            "slow_queries_count": len(slow_queries),
            "slow_query_threshold_ms": self.slow_query_threshold_ms,
            "top_slow_queries": [
                {
                    "query_preview": q.query_text,
                    "execution_count": q.execution_count,
                    "avg_duration_ms": round(q.avg_duration_ms, 2),
                    "max_duration_ms": round(q.max_duration_ms, 2)
                }
                for q in sorted(slow_queries, key=lambda m: m.avg_duration_ms, reverse=True)[:5]
            ],
            "most_frequent_queries": [
                {
                    "query_preview": q.query_text,
                    "execution_count": q.execution_count,
                    "avg_duration_ms": round(q.avg_duration_ms, 2)
                }
                for q in frequent_queries
            ]
        }

    # Index Recommendations

    async def analyze_query_patterns(self, session: AsyncSession) -> Dict[str, List[str]]:
        """Analyze query patterns and recommend indexes."""
        recommendations = {
            "missing_indexes": [],
            "composite_indexes": [],
            "performance_improvements": []
        }

        try:
            # Check for common query patterns that need indexes

            # 1. Customer lookups by phone and restaurant
            recommendations["missing_indexes"].extend([
                "CREATE INDEX CONCURRENTLY idx_customers_phone_restaurant ON customers(phone_number, restaurant_id) WHERE is_deleted = FALSE;",
                "CREATE INDEX CONCURRENTLY idx_customers_status_restaurant ON customers(status, restaurant_id) WHERE is_deleted = FALSE;",
                "CREATE INDEX CONCURRENTLY idx_customers_created_at_restaurant ON customers(created_at DESC, restaurant_id) WHERE is_deleted = FALSE;"
            ])

            # 2. Message queries by customer and date
            recommendations["missing_indexes"].extend([
                "CREATE INDEX CONCURRENTLY idx_whatsapp_messages_customer_date ON whatsapp_messages(customer_id, created_at DESC);",
                "CREATE INDEX CONCURRENTLY idx_whatsapp_messages_restaurant_date ON whatsapp_messages(restaurant_id, created_at DESC);",
                "CREATE INDEX CONCURRENTLY idx_whatsapp_messages_direction_status ON whatsapp_messages(direction, status);"
            ])

            # 3. Composite indexes for analytics
            recommendations["composite_indexes"].extend([
                "CREATE INDEX CONCURRENTLY idx_customers_restaurant_feedback ON customers(restaurant_id, feedback_sentiment, created_at) WHERE is_deleted = FALSE;",
                "CREATE INDEX CONCURRENTLY idx_messages_analytics ON whatsapp_messages(restaurant_id, direction, created_at, customer_id);"
            ])

            # 4. Performance improvement suggestions
            recommendations["performance_improvements"].extend([
                "Consider partitioning whatsapp_messages table by date if volume is high",
                "Add partial indexes on frequently filtered boolean columns",
                "Consider materialized views for complex analytics queries",
                "Implement query result caching for expensive analytics operations"
            ])

        except Exception as e:
            logger.error("Error analyzing query patterns", error=str(e))

        return recommendations


# Global query optimizer instance
query_optimizer = QueryOptimizer()


# Optimization decorators and utilities

def optimize_query(description: str):
    """Decorator to track query performance."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            async with query_optimizer.track_query_performance(description):
                return await func(*args, **kwargs)
        return wrapper
    return decorator


async def bulk_create_optimized(
    session: AsyncSession,
    model_class: Type,
    objects_data: List[Dict[str, Any]],
    batch_size: int = 1000
) -> List[Any]:
    """
    Optimized bulk create operation.
    Creates objects in batches to avoid memory issues.
    """
    objects = []

    for i in range(0, len(objects_data), batch_size):
        batch = objects_data[i:i + batch_size]
        batch_objects = [model_class(**data) for data in batch]

        session.add_all(batch_objects)
        await session.flush()  # Get IDs without committing

        objects.extend(batch_objects)

        logger.info(f"Created batch of {len(batch_objects)} {model_class.__name__} objects")

    return objects


# Export commonly used functions
__all__ = [
    'QueryOptimizer',
    'QueryPerformanceMetrics',
    'query_optimizer',
    'optimize_query',
    'bulk_create_optimized'
]