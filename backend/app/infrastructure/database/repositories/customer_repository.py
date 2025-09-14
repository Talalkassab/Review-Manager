"""
Customer Repository Implementation
Handles data access operations for customers.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from .base_repository import BaseRepository
from ....models.customer import Customer


class CustomerRepository(BaseRepository[Customer]):
    """Repository for customer data operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Customer)

    def get_model(self) -> type[Customer]:
        return Customer

    async def find_by_phone_and_restaurant(
        self,
        phone_number: str,
        restaurant_id: UUID
    ) -> Optional[Customer]:
        """Find customer by phone number and restaurant."""
        # Input validation
        if not phone_number or not phone_number.strip():
            raise ValueError("Phone number cannot be empty")

        if not restaurant_id:
            raise ValueError("Restaurant ID cannot be empty")

        # Normalize phone number
        normalized_phone = phone_number.strip().replace(" ", "")
        if len(normalized_phone) < 8:  # Basic phone number length validation
            raise ValueError("Phone number is too short")

        stmt = select(Customer).where(
            and_(
                Customer.phone_number == normalized_phone,
                Customer.restaurant_id == restaurant_id,
                Customer.is_deleted == False
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_restaurant(
        self,
        restaurant_id: UUID,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[Customer], int]:
        """Get customers by restaurant with pagination."""
        # Input validation
        if not restaurant_id:
            raise ValueError("Restaurant ID cannot be empty")

        if skip < 0:
            raise ValueError("Skip must be non-negative")

        if limit <= 0 or limit > 1000:  # Prevent excessive data retrieval
            raise ValueError("Limit must be between 1 and 1000")

        # Validate filters if provided
        if filters:
            self._validate_filters(filters)

        base_filters = {
            'restaurant_id': restaurant_id,
            'is_deleted': False
        }

        if filters:
            base_filters.update(filters)

        customers = await self.get_all(
            skip=skip,
            limit=limit,
            filters=base_filters,
            order_by='created_at'
        )

        total = await self.count(base_filters)

        return customers, total

    async def search_customers(
        self,
        search_term: str,
        restaurant_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Customer]:
        """Search customers by name, phone, or email."""
        # Input validation
        if not search_term or len(search_term.strip()) < 2:
            raise ValueError("Search term must be at least 2 characters long")

        if len(search_term.strip()) > 100:  # Prevent excessively long search terms
            raise ValueError("Search term cannot exceed 100 characters")

        if skip < 0:
            raise ValueError("Skip must be non-negative")

        if limit <= 0 or limit > 1000:
            raise ValueError("Limit must be between 1 and 1000")

        # Sanitize search term to prevent injection attacks
        sanitized_term = search_term.strip().replace('%', '\\%').replace('_', '\\_')

        stmt = select(Customer).where(
            and_(
                Customer.is_deleted == False,
                or_(
                    Customer.name.ilike(f"%{sanitized_term}%"),
                    Customer.phone_number.ilike(f"%{sanitized_term}%"),
                    Customer.email.ilike(f"%{sanitized_term}%") if hasattr(Customer, 'email') else False
                )
            )
        )

        if restaurant_id:
            stmt = stmt.where(Customer.restaurant_id == restaurant_id)

        stmt = stmt.offset(skip).limit(limit).order_by(Customer.created_at.desc())

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_customers_by_status(
        self,
        status: str,
        restaurant_id: Optional[UUID] = None
    ) -> List[Customer]:
        """Get customers by status."""
        filters = {'status': status, 'is_deleted': False}
        if restaurant_id:
            filters['restaurant_id'] = restaurant_id

        return await self.get_all(filters=filters)

    async def get_customers_by_sentiment(
        self,
        sentiment_category: str,
        restaurant_id: Optional[UUID] = None
    ) -> List[Customer]:
        """Get customers by sentiment category."""
        filters = {'sentiment_category': sentiment_category, 'is_deleted': False}
        if restaurant_id:
            filters['restaurant_id'] = restaurant_id

        return await self.get_all(filters=filters)

    async def get_recent_customers(
        self,
        days: int = 7,
        restaurant_id: Optional[UUID] = None
    ) -> List[Customer]:
        """Get customers from the last N days."""
        cutoff_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)

        filters = {
            'created_at': {'gte': cutoff_date},
            'is_deleted': False
        }
        if restaurant_id:
            filters['restaurant_id'] = restaurant_id

        return await self.get_all(
            filters=filters,
            order_by='created_at'
        )

    async def get_returning_customers(
        self,
        restaurant_id: Optional[UUID] = None
    ) -> List[Customer]:
        """Get customers with multiple visits."""
        stmt = select(Customer).where(
            and_(
                Customer.is_deleted == False,
                func.jsonb_array_length(Customer.visit_history) > 1
            )
        )

        if restaurant_id:
            stmt = stmt.where(Customer.restaurant_id == restaurant_id)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_vip_customers(
        self,
        min_visits: int = 5,
        min_sentiment: float = 0.7,
        restaurant_id: Optional[UUID] = None
    ) -> List[Customer]:
        """Get VIP customers based on visit count and sentiment."""
        stmt = select(Customer).where(
            and_(
                Customer.is_deleted == False,
                func.jsonb_array_length(Customer.visit_history) >= min_visits,
                Customer.sentiment_score >= min_sentiment
            )
        )

        if restaurant_id:
            stmt = stmt.where(Customer.restaurant_id == restaurant_id)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_at_risk_customers(
        self,
        max_sentiment: float = 0.3,
        restaurant_id: Optional[UUID] = None
    ) -> List[Customer]:
        """Get customers at risk (low sentiment)."""
        filters = {
            'sentiment_score': {'lte': max_sentiment},
            'is_deleted': False
        }
        if restaurant_id:
            filters['restaurant_id'] = restaurant_id

        return await self.get_all(filters=filters)

    async def update_customer_visit(
        self,
        customer_id: UUID,
        visit_date: Optional[datetime] = None
    ) -> Optional[Customer]:
        """Update customer with new visit information."""
        customer = await self.get_by_id(customer_id)
        if not customer:
            return None

        # Update visit date and history
        customer.visit_date = visit_date or datetime.utcnow()
        customer.update_visit_history()
        customer.status = "pending"  # Reset status for new visit

        await self.session.commit()
        await self.session.refresh(customer)

        return customer

    async def update_sentiment(
        self,
        customer_id: UUID,
        sentiment_score: float,
        sentiment_category: str
    ) -> Optional[Customer]:
        """Update customer sentiment information."""
        return await self.update(
            customer_id,
            sentiment_score=sentiment_score,
            sentiment_category=sentiment_category,
            updated_at=datetime.utcnow()
        )

    async def get_customer_stats(
        self,
        restaurant_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get customer statistics."""
        base_filter = {'is_deleted': False}
        if restaurant_id:
            base_filter['restaurant_id'] = restaurant_id

        total_customers = await self.count(base_filter)

        # Status breakdown
        status_stats = {}
        for status in ['pending', 'completed', 'follow_up']:
            filters = base_filter.copy()
            filters['status'] = status
            count = await self.count(filters)
            status_stats[status] = count

        # Sentiment breakdown
        sentiment_stats = {}
        for sentiment in ['positive', 'neutral', 'negative']:
            filters = base_filter.copy()
            filters['sentiment_category'] = sentiment
            count = await self.count(filters)
            sentiment_stats[sentiment] = count

        # Average sentiment
        stmt = select(func.avg(Customer.sentiment_score)).where(
            and_(
                Customer.is_deleted == False,
                Customer.sentiment_score.isnot(None)
            )
        )
        if restaurant_id:
            stmt = stmt.where(Customer.restaurant_id == restaurant_id)

        result = await self.session.execute(stmt)
        avg_sentiment = result.scalar() or 0.5

        return {
            'total_customers': total_customers,
            'status_breakdown': status_stats,
            'sentiment_breakdown': sentiment_stats,
            'average_sentiment': float(avg_sentiment)
        }

    def _validate_filters(self, filters: Dict[str, Any]) -> None:
        """Validate filter parameters to prevent malicious input."""
        if not isinstance(filters, dict):
            raise ValueError("Filters must be a dictionary")

        allowed_filter_keys = {
            'status', 'sentiment_category', 'sentiment_score', 'restaurant_id',
            'created_at', 'updated_at', 'visit_date', 'is_deleted'
        }

        for key, value in filters.items():
            if key not in allowed_filter_keys:
                raise ValueError(f"Invalid filter key: {key}")

            # Validate specific filter values
            if key == 'status' and isinstance(value, str):
                allowed_statuses = {'pending', 'completed', 'follow_up', 'cancelled'}
                if value not in allowed_statuses:
                    raise ValueError(f"Invalid status value: {value}")

            elif key == 'sentiment_category' and isinstance(value, str):
                allowed_categories = {'positive', 'negative', 'neutral'}
                if value not in allowed_categories:
                    raise ValueError(f"Invalid sentiment category: {value}")

            elif key == 'sentiment_score' and isinstance(value, (int, float)):
                if not (0.0 <= value <= 1.0):
                    raise ValueError("Sentiment score must be between 0.0 and 1.0")

            elif key in ['created_at', 'updated_at', 'visit_date']:
                if isinstance(value, dict):
                    # Range filters like {'gte': date, 'lte': date}
                    allowed_operators = {'gte', 'gt', 'lte', 'lt', 'eq'}
                    for op in value.keys():
                        if op not in allowed_operators:
                            raise ValueError(f"Invalid date operator: {op}")

            elif key == 'is_deleted' and not isinstance(value, bool):
                raise ValueError("is_deleted must be a boolean value")