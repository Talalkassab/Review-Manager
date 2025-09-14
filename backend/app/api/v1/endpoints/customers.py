"""
Customer management API routes.
Refactored to use service layer for business logic.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.logging import get_logger
from ....database import get_db_session
from ....models import User
from ....schemas import (
    CustomerCreate, CustomerUpdate, CustomerResponse,
    CustomerFeedbackUpdate, CustomerListFilter, CustomerStats,
    PaginatedResponse
)
from ....api.auth import current_active_user
from ..dependencies.services import get_customer_service
from ....services import CustomerService

logger = get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    current_user: User = Depends(current_active_user),
    service: CustomerService = Depends(get_customer_service)
):
    """Create a new customer."""
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

    try:
        customer = await service.create_customer(customer_data, current_user)
        return CustomerResponse.model_validate(customer)
    except Exception as e:
        logger.error(f"Customer creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create customer"
        )


@router.get("/", response_model=PaginatedResponse[CustomerResponse])
async def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    filters: CustomerListFilter = Depends(),
    current_user: User = Depends(current_active_user),
    service: CustomerService = Depends(get_customer_service)
):
    """List customers with filtering and pagination."""
    try:
        customers, total = await service.list_customers(
            user=current_user,
            filters=filters,
            skip=skip,
            limit=limit
        )

        return PaginatedResponse(
            data=[CustomerResponse.model_validate(c) for c in customers],
            total=total,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Failed to list customers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve customers"
        )


@router.get("/stats", response_model=CustomerStats)
async def get_customer_stats(
    restaurant_id: Optional[UUID] = Query(None),
    current_user: User = Depends(current_active_user),
    service: CustomerService = Depends(get_customer_service)
):
    """Get customer statistics."""
    # Verify restaurant access
    if restaurant_id and not current_user.is_superuser:
        if restaurant_id != current_user.restaurant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access statistics for different restaurant"
            )

    try:
        stats = await service.get_customer_stats(current_user, restaurant_id)
        return CustomerStats(**stats)
    except Exception as e:
        logger.error(f"Failed to get customer stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID,
    current_user: User = Depends(current_active_user),
    service: CustomerService = Depends(get_customer_service)
):
    """Get a specific customer by ID."""
    customer = await service.get_customer_by_id(customer_id, current_user)

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    return CustomerResponse.model_validate(customer)


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: UUID,
    update_data: CustomerUpdate,
    current_user: User = Depends(current_active_user),
    service: CustomerService = Depends(get_customer_service)
):
    """Update customer information."""
    # Check permissions
    if not current_user.can_manage_customers:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update customers"
        )

    # Get customer
    customer = await service.get_customer_by_id(customer_id, current_user)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    try:
        updated_customer = await service.update_customer(customer, update_data, current_user)
        return CustomerResponse.model_validate(updated_customer)
    except Exception as e:
        logger.error(f"Failed to update customer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update customer"
        )


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: UUID,
    current_user: User = Depends(current_active_user),
    service: CustomerService = Depends(get_customer_service)
):
    """Delete a customer (soft delete)."""
    # Check permissions
    if not current_user.can_manage_customers:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete customers"
        )

    # Get customer
    customer = await service.get_customer_by_id(customer_id, current_user)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    try:
        await service.delete_customer(customer, current_user)
    except Exception as e:
        logger.error(f"Failed to delete customer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete customer"
        )


@router.post("/{customer_id}/feedback", response_model=CustomerResponse)
async def update_customer_feedback(
    customer_id: UUID,
    feedback_data: CustomerFeedbackUpdate,
    current_user: User = Depends(current_active_user),
    service: CustomerService = Depends(get_customer_service)
):
    """Update customer feedback and sentiment."""
    # Get customer
    customer = await service.get_customer_by_id(customer_id, current_user)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    try:
        updated_customer = await service.update_customer_feedback(
            customer, feedback_data, current_user
        )
        return CustomerResponse.model_validate(updated_customer)
    except Exception as e:
        logger.error(f"Failed to update feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update customer feedback"
        )