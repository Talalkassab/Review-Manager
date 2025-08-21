"""
Restaurant management API routes.
Handles restaurant CRUD operations, settings, and analytics.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..core.logging import get_logger
from ..database import get_db_session
from ..models import Restaurant, User
from ..schemas import (
    RestaurantCreate, RestaurantUpdate, RestaurantResponse,
    RestaurantSettings, RestaurantStats, RestaurantListFilter,
    PaginatedResponse, ErrorResponse
)
from .auth import current_active_user, current_superuser

logger = get_logger(__name__)
router = APIRouter()


async def get_restaurant_or_404(
    restaurant_id: UUID,
    session: AsyncSession,
    user: User,
    check_access: bool = True
) -> Restaurant:
    """Get restaurant by ID or raise 404."""
    stmt = select(Restaurant).where(Restaurant.id == restaurant_id)
    result = await session.execute(stmt)
    restaurant = result.scalar_one_or_none()
    
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )
    
    # Check access permissions
    if check_access and not user.is_superuser and user.restaurant_id != restaurant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this restaurant"
        )
    
    return restaurant


@router.post("/", response_model=RestaurantResponse, status_code=status.HTTP_201_CREATED)
async def create_restaurant(
    restaurant_data: RestaurantCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_superuser)
):
    """Create a new restaurant (admin only)."""
    try:
        restaurant_dict = restaurant_data.model_dump()
        restaurant_dict["created_by"] = current_user.id
        
        restaurant = Restaurant(**restaurant_dict)
        session.add(restaurant)
        await session.commit()
        await session.refresh(restaurant)
        
        logger.info(f"Created restaurant: {restaurant.id}")
        return RestaurantResponse.model_validate(restaurant)
        
    except Exception as e:
        await session.rollback()
        logger.error(f"Restaurant creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create restaurant"
        )


@router.get("/", response_model=PaginatedResponse[RestaurantResponse])
async def list_restaurants(
    filters: RestaurantListFilter = Depends(),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """List restaurants with filtering and pagination."""
    try:
        # Base query
        stmt = select(Restaurant).where(Restaurant.is_deleted == False)
        count_stmt = select(func.count(Restaurant.id)).where(Restaurant.is_deleted == False)
        
        # Non-superusers can only see their own restaurant
        if not current_user.is_superuser:
            if current_user.restaurant_id:
                stmt = stmt.where(Restaurant.id == current_user.restaurant_id)
                count_stmt = count_stmt.where(Restaurant.id == current_user.restaurant_id)
            else:
                # User has no restaurant assigned
                return PaginatedResponse(
                    items=[],
                    total=0,
                    page=filters.page,
                    per_page=filters.per_page,
                    pages=0,
                    has_prev=False,
                    has_next=False
                )
        
        # Apply filters
        if filters.search:
            search_filter = Restaurant.name.ilike(f"%{filters.search}%")
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)
        
        if filters.city:
            stmt = stmt.where(Restaurant.city.ilike(f"%{filters.city}%"))
            count_stmt = count_stmt.where(Restaurant.city.ilike(f"%{filters.city}%"))
        
        if filters.is_active is not None:
            stmt = stmt.where(Restaurant.is_active == filters.is_active)
            count_stmt = count_stmt.where(Restaurant.is_active == filters.is_active)
        
        # Sorting
        sort_field = getattr(Restaurant, filters.sort_by, Restaurant.created_at)
        if filters.sort_order == "asc":
            stmt = stmt.order_by(sort_field.asc())
        else:
            stmt = stmt.order_by(sort_field.desc())
        
        # Pagination
        offset = (filters.page - 1) * filters.per_page
        stmt = stmt.offset(offset).limit(filters.per_page)
        
        # Execute queries
        result = await session.execute(stmt)
        restaurants = result.scalars().all()
        
        count_result = await session.execute(count_stmt)
        total = count_result.scalar()
        
        # Calculate pagination info
        pages = (total + filters.per_page - 1) // filters.per_page
        has_prev = filters.page > 1
        has_next = filters.page < pages
        
        return PaginatedResponse(
            items=[RestaurantResponse.model_validate(restaurant) for restaurant in restaurants],
            total=total,
            page=filters.page,
            per_page=filters.per_page,
            pages=pages,
            has_prev=has_prev,
            has_next=has_next
        )
        
    except Exception as e:
        logger.error(f"Restaurant list failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve restaurants"
        )


@router.get("/{restaurant_id}", response_model=RestaurantResponse)
async def get_restaurant(
    restaurant_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Get restaurant by ID."""
    restaurant = await get_restaurant_or_404(restaurant_id, session, current_user)
    return RestaurantResponse.model_validate(restaurant)


@router.patch("/{restaurant_id}", response_model=RestaurantResponse)
async def update_restaurant(
    restaurant_id: UUID,
    restaurant_update: RestaurantUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Update restaurant information."""
    try:
        # Check permissions - only restaurant owners and admins can update
        if not current_user.is_superuser and not current_user.is_restaurant_owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update restaurant"
            )
        
        restaurant = await get_restaurant_or_404(restaurant_id, session, current_user)
        
        # Update fields
        update_dict = restaurant_update.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(restaurant, field, value)
        
        restaurant.updated_by = current_user.id
        await session.commit()
        await session.refresh(restaurant)
        
        logger.info(f"Updated restaurant: {restaurant_id}")
        return RestaurantResponse.model_validate(restaurant)
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Restaurant update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update restaurant"
        )


@router.patch("/{restaurant_id}/settings", response_model=RestaurantResponse)
async def update_restaurant_settings(
    restaurant_id: UUID,
    settings_update: RestaurantSettings,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Update restaurant settings."""
    try:
        # Check permissions
        if not current_user.is_superuser and not current_user.is_restaurant_owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update settings"
            )
        
        restaurant = await get_restaurant_or_404(restaurant_id, session, current_user)
        
        # Update settings
        update_dict = settings_update.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(restaurant, field, value)
        
        restaurant.updated_by = current_user.id
        await session.commit()
        await session.refresh(restaurant)
        
        logger.info(f"Updated restaurant settings: {restaurant_id}")
        return RestaurantResponse.model_validate(restaurant)
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Restaurant settings update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update restaurant settings"
        )


@router.get("/{restaurant_id}/stats", response_model=RestaurantStats)
async def get_restaurant_stats(
    restaurant_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Get restaurant statistics."""
    try:
        restaurant = await get_restaurant_or_404(restaurant_id, session, current_user)
        
        # Import here to avoid circular imports
        from ..models import Customer, WhatsAppMessage, Campaign
        
        # Basic customer stats
        customer_count_stmt = select(func.count(Customer.id)).where(
            Customer.restaurant_id == restaurant_id,
            Customer.is_deleted == False
        )
        customer_result = await session.execute(customer_count_stmt)
        total_customers = customer_result.scalar()
        
        # Message stats
        message_count_stmt = select(func.count(WhatsAppMessage.id)).where(
            WhatsAppMessage.restaurant_id == restaurant_id
        )
        message_result = await session.execute(message_count_stmt)
        total_messages = message_result.scalar()
        
        # Response rate calculation
        contacted_stmt = select(func.count(Customer.id)).where(
            Customer.restaurant_id == restaurant_id,
            Customer.status.in_(["contacted", "responded", "completed"]),
            Customer.is_deleted == False
        )
        contacted_result = await session.execute(contacted_stmt)
        contacted_customers = contacted_result.scalar()
        
        responded_stmt = select(func.count(Customer.id)).where(
            Customer.restaurant_id == restaurant_id,
            Customer.status.in_(["responded", "completed"]),
            Customer.is_deleted == False
        )
        responded_result = await session.execute(responded_stmt)
        responded_customers = responded_result.scalar()
        
        response_rate = 0.0
        if contacted_customers > 0:
            response_rate = (responded_customers / contacted_customers) * 100
        
        # Positive feedback rate
        positive_stmt = select(func.count(Customer.id)).where(
            Customer.restaurant_id == restaurant_id,
            Customer.feedback_sentiment == "positive",
            Customer.is_deleted == False
        )
        positive_result = await session.execute(positive_stmt)
        positive_feedback = positive_result.scalar()
        
        feedback_stmt = select(func.count(Customer.id)).where(
            Customer.restaurant_id == restaurant_id,
            Customer.feedback_text.isnot(None),
            Customer.is_deleted == False
        )
        feedback_result = await session.execute(feedback_stmt)
        total_feedback = feedback_result.scalar()
        
        positive_feedback_rate = 0.0
        if total_feedback > 0:
            positive_feedback_rate = (positive_feedback / total_feedback) * 100
        
        # Average rating
        rating_stmt = select(func.avg(Customer.rating)).where(
            Customer.restaurant_id == restaurant_id,
            Customer.rating.isnot(None),
            Customer.is_deleted == False
        )
        rating_result = await session.execute(rating_stmt)
        average_rating = rating_result.scalar()
        
        # Google reviews
        reviews_stmt = select(func.count(Customer.id)).where(
            Customer.restaurant_id == restaurant_id,
            Customer.google_review_completed == True,
            Customer.is_deleted == False
        )
        reviews_result = await session.execute(reviews_stmt)
        google_reviews = reviews_result.scalar()
        
        # Active campaigns
        campaigns_stmt = select(func.count(Campaign.id)).where(
            Campaign.restaurant_id == restaurant_id,
            Campaign.status.in_(["running", "scheduled"]),
            Campaign.is_deleted == False
        )
        campaigns_result = await session.execute(campaigns_stmt)
        active_campaigns = campaigns_result.scalar()
        
        return RestaurantStats(
            restaurant_id=restaurant_id,
            total_customers=total_customers,
            customers_this_month=restaurant.current_month_customers,
            total_messages=total_messages,
            messages_this_month=0,  # Implement if needed
            average_rating=float(average_rating) if average_rating else None,
            response_rate=round(response_rate, 2),
            positive_feedback_rate=round(positive_feedback_rate, 2),
            google_reviews_generated=google_reviews,
            active_campaigns=active_campaigns
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Restaurant stats failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve restaurant statistics"
        )