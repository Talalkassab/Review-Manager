"""
Customer Service Layer
Handles all business logic for customer operations.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from ..models import User
from ..models.customer import Customer
from ..schemas import (
    CustomerCreate, CustomerUpdate, CustomerResponse,
    CustomerFeedbackUpdate, CustomerListFilter
)
from ..infrastructure.database.repositories import CustomerRepository
from ..core.logging import get_logger
from ..core.exceptions import CustomerNotFound, InvalidInput

logger = get_logger(__name__)


class CustomerService:
    """Service class for customer-related business logic."""

    def __init__(self, session: AsyncSession):
        """Initialize the service with a database session."""
        self.session = session
        self.customer_repository = CustomerRepository(session)

    async def get_customer_by_id(
        self,
        customer_id: UUID,
        user: User,
        check_restaurant: bool = True
    ) -> Optional[Customer]:
        """Get customer by ID with restaurant filtering."""
        customer = await self.customer_repository.get_by_id(customer_id)

        if not customer:
            return None

        # Check restaurant access
        if check_restaurant and not user.is_superuser:
            if customer.restaurant_id != user.restaurant_id:
                return None

        return customer

    async def create_customer(
        self,
        customer_data: CustomerCreate,
        user: User
    ) -> Customer:
        """Create a new customer or update existing one."""
        # Validate user can create customers for this restaurant
        if not user.is_superuser and customer_data.restaurant_id != user.restaurant_id:
            raise InvalidInput(
                field="restaurant_id",
                reason="Cannot create customer for different restaurant"
            )

        # Check for existing customer
        existing_customer = await self.customer_repository.find_by_phone_and_restaurant(
            phone_number=customer_data.phone_number,
            restaurant_id=customer_data.restaurant_id
        )

        if existing_customer:
            # Update existing customer with new visit
            return await self._update_customer_visit(existing_customer, customer_data, user)

        # Create customer data
        customer_dict = customer_data.model_dump(exclude_unset=True)
        customer_dict.update({
            'created_by': user.id,
            'updated_by': user.id
        })

        # Create new customer through repository
        customer = await self.customer_repository.create(customer_dict)

        # Set initial visit history
        customer.update_visit_history()
        await self.session.commit()

        logger.info(f"Created new customer: {customer.id}")
        return customer

    async def update_customer(
        self,
        customer: Customer,
        update_data: CustomerUpdate,
        user: User
    ) -> Customer:
        """Update customer information."""
        # Prepare update data
        update_dict = update_data.model_dump(exclude_unset=True)
        update_dict.update({
            'updated_by': user.id,
            'updated_at': datetime.utcnow()
        })

        # Update through repository
        updated_customer = await self.customer_repository.update(
            customer.id,
            **update_dict
        )

        if not updated_customer:
            raise CustomerNotFound(str(customer.id))

        logger.info(f"Updated customer: {customer.id}")
        return updated_customer

    async def delete_customer(
        self,
        customer: Customer,
        user: User
    ) -> bool:
        """Soft delete a customer."""
        # Perform soft delete through repository
        result = await self.customer_repository.delete(
            customer.id,
            soft_delete=True
        )

        if result:
            # Update audit fields
            await self.customer_repository.update(
                customer.id,
                updated_by=user.id,
                deleted_at=datetime.utcnow()
            )

        logger.info(f"Soft deleted customer: {customer.id}")
        return result

    async def list_customers(
        self,
        user: User,
        filters: Optional[CustomerListFilter] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Customer], int]:
        """List customers with filtering and pagination."""
        # Build repository filters
        repo_filters = {'is_deleted': False}

        # Apply restaurant filter for non-superusers
        if not user.is_superuser:
            repo_filters['restaurant_id'] = user.restaurant_id

        # Convert CustomerListFilter to repository filters
        if filters:
            if filters.status:
                repo_filters['status'] = filters.status
            if filters.sentiment_category:
                repo_filters['sentiment_category'] = filters.sentiment_category
            if filters.restaurant_id:
                repo_filters['restaurant_id'] = filters.restaurant_id
            # Note: Search functionality would need to be handled by repository

        # Get customers through repository
        if user.is_superuser:
            customers, total = await self.customer_repository.get_by_restaurant(
                restaurant_id=filters.restaurant_id if filters else None,
                skip=skip,
                limit=limit,
                filters=repo_filters
            )
        else:
            customers, total = await self.customer_repository.get_by_restaurant(
                restaurant_id=user.restaurant_id,
                skip=skip,
                limit=limit,
                filters=repo_filters
            )

        return customers, total

    async def update_customer_feedback(
        self,
        customer: Customer,
        feedback_data: CustomerFeedbackUpdate,
        user: User
    ) -> Customer:
        """Update customer feedback and sentiment."""
        customer.feedback = feedback_data.feedback
        customer.sentiment_score = feedback_data.sentiment_score
        customer.sentiment_category = feedback_data.sentiment_category
        customer.status = "completed"
        customer.updated_by = user.id
        customer.updated_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(customer)

        logger.info(f"Updated feedback for customer: {customer.id}")
        return customer

    async def get_customer_stats(
        self,
        user: User,
        restaurant_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get customer statistics."""
        # Determine which restaurant to get stats for
        target_restaurant_id = restaurant_id
        if not user.is_superuser:
            target_restaurant_id = user.restaurant_id

        # Get stats through repository
        return await self.customer_repository.get_customer_stats(target_restaurant_id)

    # Private helper methods

    async def _update_customer_visit(
        self,
        customer: Customer,
        customer_data: CustomerCreate,
        user: User
    ) -> Customer:
        """Update existing customer with new visit."""
        # Prepare update data
        update_data = {
            'visit_date': customer_data.visit_date or datetime.utcnow(),
            'status': 'pending',  # Reset status for new visit
            'updated_by': user.id,
            'updated_at': datetime.utcnow()
        }

        # Add other fields from customer data (except restaurant_id)
        for field, value in customer_data.model_dump(exclude_unset=True).items():
            if field not in ["restaurant_id", "visit_date"]:
                update_data[field] = value

        # Update through repository
        updated_customer = await self.customer_repository.update(
            customer.id,
            **update_data
        )

        # Update visit history
        updated_customer.update_visit_history()
        await self.session.commit()

        logger.info(f"Updated existing customer with new visit: {customer.id}")
        return updated_customer