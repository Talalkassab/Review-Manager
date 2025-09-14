"""
Analytics API endpoints.
Refactored to use service layer for business logic.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from uuid import UUID
from datetime import datetime

from ....core.logging import get_logger
from ....models import User
from ....api.auth import current_active_user
from ..dependencies.services import get_analytics_service
from ....services import AnalyticsService
from ....services.analytics_service import TimeRange

logger = get_logger(__name__)
router = APIRouter(tags=["Analytics"])


@router.get("/dashboard")
async def get_dashboard_metrics(
    restaurant_id: Optional[UUID] = Query(None),
    time_range: str = Query("month", enum=["today", "week", "month", "quarter", "year"]),
    current_user: User = Depends(current_active_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get comprehensive dashboard metrics."""
    # Verify restaurant access
    if restaurant_id and not current_user.is_superuser:
        if restaurant_id != current_user.restaurant_id:
            raise HTTPException(
                status_code=403,
                detail="Cannot access analytics for different restaurant"
            )

    # Use user's restaurant if not specified
    if not restaurant_id and not current_user.is_superuser:
        restaurant_id = current_user.restaurant_id

    try:
        # Convert string to TimeRange enum
        time_range_enum = TimeRange(time_range)

        metrics = await service.get_dashboard_metrics(
            restaurant_id=restaurant_id,
            time_range=time_range_enum
        )

        return metrics

    except Exception as e:
        logger.error(f"Failed to get dashboard metrics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve dashboard metrics"
        )


@router.get("/customers")
async def get_customer_analytics(
    restaurant_id: Optional[UUID] = Query(None),
    time_range: str = Query("month", enum=["today", "week", "month", "quarter", "year"]),
    current_user: User = Depends(current_active_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get detailed customer analytics."""
    # Verify restaurant access
    if restaurant_id and not current_user.is_superuser:
        if restaurant_id != current_user.restaurant_id:
            raise HTTPException(
                status_code=403,
                detail="Cannot access analytics for different restaurant"
            )

    # Use user's restaurant if not specified
    if not restaurant_id and not current_user.is_superuser:
        restaurant_id = current_user.restaurant_id

    try:
        time_range_enum = TimeRange(time_range)

        analytics = await service.get_customer_analytics(
            restaurant_id=restaurant_id,
            time_range=time_range_enum
        )

        return analytics

    except Exception as e:
        logger.error(f"Failed to get customer analytics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve customer analytics"
        )


@router.get("/sentiment")
async def get_sentiment_analytics(
    restaurant_id: Optional[UUID] = Query(None),
    time_range: str = Query("month", enum=["today", "week", "month", "quarter", "year"]),
    current_user: User = Depends(current_active_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get detailed sentiment analytics."""
    # Verify restaurant access
    if restaurant_id and not current_user.is_superuser:
        if restaurant_id != current_user.restaurant_id:
            raise HTTPException(
                status_code=403,
                detail="Cannot access analytics for different restaurant"
            )

    # Use user's restaurant if not specified
    if not restaurant_id and not current_user.is_superuser:
        restaurant_id = current_user.restaurant_id

    try:
        time_range_enum = TimeRange(time_range)

        analytics = await service.get_sentiment_analytics(
            restaurant_id=restaurant_id,
            time_range=time_range_enum
        )

        return analytics

    except Exception as e:
        logger.error(f"Failed to get sentiment analytics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve sentiment analytics"
        )


@router.get("/engagement")
async def get_engagement_analytics(
    restaurant_id: Optional[UUID] = Query(None),
    time_range: str = Query("month", enum=["today", "week", "month", "quarter", "year"]),
    current_user: User = Depends(current_active_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get detailed engagement analytics."""
    # Verify restaurant access
    if restaurant_id and not current_user.is_superuser:
        if restaurant_id != current_user.restaurant_id:
            raise HTTPException(
                status_code=403,
                detail="Cannot access analytics for different restaurant"
            )

    # Use user's restaurant if not specified
    if not restaurant_id and not current_user.is_superuser:
        restaurant_id = current_user.restaurant_id

    try:
        time_range_enum = TimeRange(time_range)

        analytics = await service.get_engagement_analytics(
            restaurant_id=restaurant_id,
            time_range=time_range_enum
        )

        return analytics

    except Exception as e:
        logger.error(f"Failed to get engagement analytics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve engagement analytics"
        )


@router.get("/campaigns")
async def get_campaign_analytics(
    campaign_id: Optional[UUID] = Query(None),
    restaurant_id: Optional[UUID] = Query(None),
    current_user: User = Depends(current_active_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get campaign performance analytics."""
    # Verify restaurant access
    if restaurant_id and not current_user.is_superuser:
        if restaurant_id != current_user.restaurant_id:
            raise HTTPException(
                status_code=403,
                detail="Cannot access analytics for different restaurant"
            )

    # Use user's restaurant if not specified
    if not restaurant_id and not current_user.is_superuser:
        restaurant_id = current_user.restaurant_id

    try:
        analytics = await service.get_campaign_analytics(
            campaign_id=campaign_id,
            restaurant_id=restaurant_id
        )

        return analytics

    except Exception as e:
        logger.error(f"Failed to get campaign analytics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve campaign analytics"
        )


@router.get("/real-time")
async def get_real_time_metrics(
    restaurant_id: Optional[UUID] = Query(None),
    current_user: User = Depends(current_active_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get real-time metrics for monitoring."""
    # Verify restaurant access
    if restaurant_id and not current_user.is_superuser:
        if restaurant_id != current_user.restaurant_id:
            raise HTTPException(
                status_code=403,
                detail="Cannot access metrics for different restaurant"
            )

    # Use user's restaurant if not specified
    if not restaurant_id and not current_user.is_superuser:
        restaurant_id = current_user.restaurant_id

    try:
        metrics = await service.get_real_time_metrics(restaurant_id)
        return metrics

    except Exception as e:
        logger.error(f"Failed to get real-time metrics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve real-time metrics"
        )


@router.post("/report")
async def generate_report(
    report_type: str = Query(..., enum=["executive_summary", "customer_insights", "operational_metrics"]),
    restaurant_id: Optional[UUID] = Query(None),
    time_range: str = Query("month", enum=["today", "week", "month", "quarter", "year"]),
    format: str = Query("json", enum=["json", "pdf"]),
    current_user: User = Depends(current_active_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Generate a comprehensive report."""
    # Verify restaurant access
    if restaurant_id and not current_user.is_superuser:
        if restaurant_id != current_user.restaurant_id:
            raise HTTPException(
                status_code=403,
                detail="Cannot generate report for different restaurant"
            )

    # Use user's restaurant if not specified
    if not restaurant_id and not current_user.is_superuser:
        restaurant_id = current_user.restaurant_id

    try:
        time_range_enum = TimeRange(time_range)

        report = await service.generate_report(
            report_type=report_type,
            restaurant_id=restaurant_id,
            time_range=time_range_enum,
            format=format
        )

        return report

    except Exception as e:
        logger.error(f"Failed to generate report: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate report"
        )