"""
Customer management API routes.
Handles customer CRUD operations, feedback tracking, and interaction management.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from ..core.logging import get_logger
from ..database import get_db_session
from ..models import Customer, User, Restaurant
from ..schemas import (
    CustomerCreate, CustomerUpdate, CustomerResponse, CustomerInteractionSummary,
    CustomerFeedbackUpdate, CustomerListFilter, CustomerStats, PaginatedResponse,
    ErrorResponse
)
from .auth import current_active_user

logger = get_logger(__name__)
router = APIRouter()


async def get_customer_or_404(
    customer_id: UUID,
    session: AsyncSession,
    user: User,
    check_restaurant: bool = True
) -> Customer:
    """Get customer by ID or raise 404."""
    stmt = select(Customer).where(Customer.id == customer_id)
    
    if check_restaurant and not user.is_superuser:
        stmt = stmt.where(Customer.restaurant_id == user.restaurant_id)
    
    result = await session.execute(stmt)
    customer = result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    return customer


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Create a new customer."""
    try:
        # Check user permissions
        if not current_user.can_manage_customers:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create customers"
            )
        
        # Verify restaurant access
        if not current_user.is_superuser and customer_data.restaurant_id != current_user.restaurant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create customer for different restaurant"
            )
        
        # Check if customer already exists (by phone and restaurant)
        existing_stmt = select(Customer).where(
            and_(
                Customer.phone_number == customer_data.phone_number,
                Customer.restaurant_id == customer_data.restaurant_id,
                Customer.is_deleted == False
            )
        )
        result = await session.execute(existing_stmt)
        existing_customer = result.scalar_one_or_none()
        
        if existing_customer:
            # Update existing customer with new visit
            existing_customer.visit_date = customer_data.visit_date or datetime.utcnow()
            existing_customer.update_visit_history()
            existing_customer.status = "pending"  # Reset status for new visit
            
            # Update other fields
            for field, value in customer_data.model_dump(exclude_unset=True).items():
                if field not in ["restaurant_id"] and hasattr(existing_customer, field):
                    setattr(existing_customer, field, value)
            
            existing_customer.updated_by = current_user.id
            await session.commit()
            await session.refresh(existing_customer)
            
            logger.info(f"Updated existing customer: {existing_customer.id}")
            return CustomerResponse.model_validate(existing_customer)
        
        # Create new customer
        customer_dict = customer_data.model_dump()
        customer_dict["created_by"] = current_user.id
        customer_dict["visit_date"] = customer_dict.get("visit_date") or datetime.utcnow()
        
        customer = Customer(**customer_dict)
        session.add(customer)
        await session.commit()
        await session.refresh(customer)
        
        logger.info(f"Created new customer: {customer.id}")
        return CustomerResponse.model_validate(customer)
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Customer creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create customer"
        )


@router.get("/", response_model=PaginatedResponse[CustomerResponse])
async def list_customers(
    filters: CustomerListFilter = Depends(),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """List customers with filtering and pagination."""
    try:
        # Base query
        stmt = select(Customer).where(Customer.is_deleted == False)
        count_stmt = select(func.count(Customer.id)).where(Customer.is_deleted == False)
        
        # Restaurant filtering
        if not current_user.is_superuser:
            stmt = stmt.where(Customer.restaurant_id == current_user.restaurant_id)
            count_stmt = count_stmt.where(Customer.restaurant_id == current_user.restaurant_id)
        
        # Apply filters
        if filters.search:
            search_filter = or_(
                Customer.first_name.ilike(f"%{filters.search}%"),
                Customer.last_name.ilike(f"%{filters.search}%"),
                Customer.phone_number.ilike(f"%{filters.search}%")
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)
        
        if filters.status:
            stmt = stmt.where(Customer.status == filters.status)
            count_stmt = count_stmt.where(Customer.status == filters.status)
        
        if filters.sentiment:
            stmt = stmt.where(Customer.feedback_sentiment == filters.sentiment)
            count_stmt = count_stmt.where(Customer.feedback_sentiment == filters.sentiment)
        
        if filters.has_feedback is not None:
            if filters.has_feedback:
                stmt = stmt.where(Customer.feedback_text.isnot(None))
                count_stmt = count_stmt.where(Customer.feedback_text.isnot(None))
            else:
                stmt = stmt.where(Customer.feedback_text.is_(None))
                count_stmt = count_stmt.where(Customer.feedback_text.is_(None))
        
        if filters.requires_follow_up is not None:
            stmt = stmt.where(Customer.requires_follow_up == filters.requires_follow_up)
            count_stmt = count_stmt.where(Customer.requires_follow_up == filters.requires_follow_up)
        
        if filters.visit_date_from:
            stmt = stmt.where(Customer.visit_date >= filters.visit_date_from)
            count_stmt = count_stmt.where(Customer.visit_date >= filters.visit_date_from)
        
        if filters.visit_date_to:
            stmt = stmt.where(Customer.visit_date <= filters.visit_date_to)
            count_stmt = count_stmt.where(Customer.visit_date <= filters.visit_date_to)
        
        if filters.rating_min:
            stmt = stmt.where(Customer.rating >= filters.rating_min)
            count_stmt = count_stmt.where(Customer.rating >= filters.rating_min)
        
        if filters.rating_max:
            stmt = stmt.where(Customer.rating <= filters.rating_max)
            count_stmt = count_stmt.where(Customer.rating <= filters.rating_max)
        
        if filters.is_repeat_customer is not None:
            stmt = stmt.where(Customer.is_repeat_customer == filters.is_repeat_customer)
            count_stmt = count_stmt.where(Customer.is_repeat_customer == filters.is_repeat_customer)
        
        if filters.google_review_completed is not None:
            stmt = stmt.where(Customer.google_review_completed == filters.google_review_completed)
            count_stmt = count_stmt.where(Customer.google_review_completed == filters.google_review_completed)
        
        # Sorting
        sort_field = getattr(Customer, filters.sort_by, Customer.visit_date)
        if filters.sort_order == "asc":
            stmt = stmt.order_by(sort_field.asc())
        else:
            stmt = stmt.order_by(sort_field.desc())
        
        # Pagination
        offset = (filters.page - 1) * filters.per_page
        stmt = stmt.offset(offset).limit(filters.per_page)
        
        # Execute queries
        result = await session.execute(stmt)
        customers = result.scalars().all()
        
        count_result = await session.execute(count_stmt)
        total = count_result.scalar()
        
        # Calculate pagination info
        pages = max(1, (total + filters.per_page - 1) // filters.per_page)
        has_prev = filters.page > 1
        has_next = filters.page < pages
        
        return PaginatedResponse(
            items=[CustomerResponse.model_validate(customer) for customer in customers],
            total=total,
            page=filters.page,
            per_page=filters.per_page,
            pages=pages,
            has_prev=has_prev,
            has_next=has_next
        )
        
    except Exception as e:
        logger.error(f"Customer list failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve customers"
        )


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Get customer by ID."""
    customer = await get_customer_or_404(customer_id, session, current_user)
    return CustomerResponse.model_validate(customer)


@router.patch("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: UUID,
    customer_update: CustomerUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Update customer information."""
    try:
        # Check permissions
        if not current_user.can_manage_customers:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update customers"
            )
        
        customer = await get_customer_or_404(customer_id, session, current_user)
        
        # Update fields
        update_dict = customer_update.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(customer, field, value)
        
        customer.updated_by = current_user.id
        await session.commit()
        await session.refresh(customer)
        
        logger.info(f"Updated customer: {customer_id}")
        return CustomerResponse.model_validate(customer)
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Customer update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update customer"
        )


@router.delete("/{customer_id}", status_code=status.HTTP_200_OK)
async def delete_customer(
    customer_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Soft delete customer."""
    try:
        # Check permissions
        if not current_user.can_manage_customers:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to delete customers"
            )
        
        customer = await get_customer_or_404(customer_id, session, current_user)
        
        # Soft delete
        customer.soft_delete()
        customer.updated_by = current_user.id
        await session.commit()
        
        logger.info(f"Deleted customer: {customer_id}")
        return {"message": "Customer deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Customer deletion failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete customer"
        )


@router.patch("/{customer_id}/feedback", response_model=CustomerResponse)
async def update_customer_feedback(
    customer_id: UUID,
    feedback_update: CustomerFeedbackUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Update customer feedback."""
    try:
        # Check permissions
        if not current_user.can_manage_customers:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update customer feedback"
            )
        
        customer = await get_customer_or_404(customer_id, session, current_user)
        
        # Record feedback
        customer.record_feedback(
            feedback_text=feedback_update.feedback_text,
            sentiment=feedback_update.sentiment,
            confidence_score=feedback_update.confidence_score,
            rating=feedback_update.rating
        )
        
        # Update other fields
        if feedback_update.requires_follow_up is not None:
            customer.requires_follow_up = feedback_update.requires_follow_up
        
        if feedback_update.issue_resolved is not None:
            customer.issue_resolved = feedback_update.issue_resolved
        
        if feedback_update.resolution_notes:
            customer.resolution_notes = feedback_update.resolution_notes
        
        customer.updated_by = current_user.id
        await session.commit()
        await session.refresh(customer)
        
        logger.info(f"Updated customer feedback: {customer_id}")
        return CustomerResponse.model_validate(customer)
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Customer feedback update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update customer feedback"
        )


@router.post("/{customer_id}/google-review", status_code=status.HTTP_200_OK)
async def request_google_review(
    customer_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Request Google review from customer."""
    try:
        # Check permissions
        if not current_user.can_manage_customers:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to request reviews"
            )
        
        customer = await get_customer_or_404(customer_id, session, current_user)
        
        # Request Google review
        success = customer.request_google_review()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot request review for non-positive feedback"
            )
        
        customer.updated_by = current_user.id
        await session.commit()
        
        logger.info(f"Google review requested for customer: {customer_id}")
        return {"message": "Google review requested successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Google review request failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to request Google review"
        )


@router.get("/stats/summary", response_model=CustomerStats)
async def get_customer_stats(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Get customer statistics summary."""
    try:
        # Base filters
        base_filter = Customer.is_deleted == False
        if not current_user.is_superuser:
            base_filter = and_(base_filter, Customer.restaurant_id == current_user.restaurant_id)
        
        # Total customers
        total_stmt = select(func.count(Customer.id)).where(base_filter)
        total_result = await session.execute(total_stmt)
        total_customers = total_result.scalar()
        
        # Today's customers
        today = datetime.utcnow().date()
        today_stmt = select(func.count(Customer.id)).where(
            and_(base_filter, func.date(Customer.visit_date) == today)
        )
        today_result = await session.execute(today_stmt)
        customers_today = today_result.scalar()
        
        # Status counts
        status_counts = {}
        for status in ["pending", "contacted", "responded", "completed", "failed"]:
            stmt = select(func.count(Customer.id)).where(
                and_(base_filter, Customer.status == status)
            )
            result = await session.execute(stmt)
            status_counts[status] = result.scalar()
        
        # Calculate rates
        response_rate = 0.0
        if status_counts["contacted"] > 0:
            responded = status_counts["responded"] + status_counts["completed"]
            response_rate = (responded / status_counts["contacted"]) * 100
        
        # Positive feedback rate
        positive_stmt = select(func.count(Customer.id)).where(
            and_(base_filter, Customer.feedback_sentiment == "positive")
        )
        positive_result = await session.execute(positive_stmt)
        positive_feedback = positive_result.scalar()
        
        feedback_stmt = select(func.count(Customer.id)).where(
            and_(base_filter, Customer.feedback_text.isnot(None))
        )
        feedback_result = await session.execute(feedback_stmt)
        total_feedback = feedback_result.scalar()
        
        positive_feedback_rate = 0.0
        if total_feedback > 0:
            positive_feedback_rate = (positive_feedback / total_feedback) * 100
        
        # Average rating
        rating_stmt = select(func.avg(Customer.rating)).where(
            and_(base_filter, Customer.rating.isnot(None))
        )
        rating_result = await session.execute(rating_stmt)
        average_rating = rating_result.scalar()
        
        # Google reviews
        reviews_stmt = select(func.count(Customer.id)).where(
            and_(base_filter, Customer.google_review_completed == True)
        )
        reviews_result = await session.execute(reviews_stmt)
        google_reviews = reviews_result.scalar()
        
        return CustomerStats(
            total_customers=total_customers,
            customers_today=customers_today,
            customers_this_week=0,  # Implement if needed
            customers_this_month=0,  # Implement if needed
            pending_contact=status_counts["pending"],
            contacted=status_counts["contacted"],
            responded=status_counts["responded"],
            completed=status_counts["completed"],
            failed=status_counts["failed"],
            response_rate=round(response_rate, 2),
            positive_feedback_rate=round(positive_feedback_rate, 2),
            average_rating=float(average_rating) if average_rating else None,
            google_reviews_generated=google_reviews
        )
        
    except Exception as e:
        logger.error(f"Customer stats failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve customer statistics"
        )