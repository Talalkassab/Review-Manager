"""
Campaign management API routes with advanced features.
Handles campaign CRUD operations, execution, and performance tracking.

Features:
- Campaign creation with demographic targeting
- A/B testing configuration and statistical analysis
- Real-time campaign monitoring via WebSockets
- Customer segmentation and personalization
- Cultural-aware timing optimization
- Advanced analytics and ROI calculation
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
import asyncio

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.orm import selectinload

from ..core.logging import get_logger
from ..database import get_db_session
from ..models import Campaign, CampaignRecipient, User, Customer, WhatsAppMessage, Restaurant
from ..schemas import (
    CampaignCreate, CampaignUpdate, CampaignResponse,
    CampaignAction, CampaignStats, CampaignListFilter,
    CampaignRecipientCreate, CampaignRecipientResponse,
    CampaignAnalytics, ABTestResults, CampaignTemplate,
    BulkCampaignOperation, PaginatedResponse, ErrorResponse
)
from .auth import current_active_user
from ..services.campaigns import (
    CampaignExecutionService,
    CampaignAnalyticsService,
    CustomerSegmentationService,
    ABTestingService,
    TimingOptimizationService,
    PersonalizationEngine,
    CampaignWebSocketManager
)

logger = get_logger(__name__)
router = APIRouter()
websocket_manager = CampaignWebSocketManager()

# Service instances (will be injected via dependency injection in production)
campaign_execution_service = CampaignExecutionService()
analytics_service = CampaignAnalyticsService()
segmentation_service = CustomerSegmentationService()
ab_testing_service = ABTestingService()
timing_service = TimingOptimizationService()
personalization_engine = PersonalizationEngine()


async def get_campaign_or_404(
    campaign_id: UUID,
    session: AsyncSession,
    user: User,
    check_restaurant: bool = True
) -> Campaign:
    """Get campaign by ID or raise 404."""
    stmt = select(Campaign).where(Campaign.id == campaign_id)
    
    if check_restaurant and not user.is_superuser:
        stmt = stmt.where(Campaign.restaurant_id == user.restaurant_id)
    
    result = await session.execute(stmt)
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    return campaign


@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign_data: CampaignCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Create a new campaign."""
    try:
        # Check permissions - managers and above can create campaigns
        if not current_user.is_manager:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create campaigns"
            )
        
        # Verify restaurant access
        if not current_user.is_superuser and campaign_data.restaurant_id != current_user.restaurant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create campaign for different restaurant"
            )
        
        # Create campaign
        campaign_dict = campaign_data.model_dump()
        campaign_dict["created_by_user_id"] = current_user.id
        campaign_dict["status"] = "draft"
        
        campaign = Campaign(**campaign_dict)
        session.add(campaign)
        await session.commit()
        await session.refresh(campaign)
        
        logger.info(f"Created campaign: {campaign.id}")
        return CampaignResponse.model_validate(campaign)
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Campaign creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create campaign"
        )


@router.get("/", response_model=PaginatedResponse[CampaignResponse])
async def list_campaigns(
    filters: CampaignListFilter = Depends(),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """List campaigns with filtering and pagination."""
    try:
        # Base query
        stmt = select(Campaign).where(Campaign.is_deleted == False)
        count_stmt = select(func.count(Campaign.id)).where(Campaign.is_deleted == False)
        
        # Restaurant filtering
        if not current_user.is_superuser:
            stmt = stmt.where(Campaign.restaurant_id == current_user.restaurant_id)
            count_stmt = count_stmt.where(Campaign.restaurant_id == current_user.restaurant_id)
        
        # Apply filters
        if filters.search:
            search_filter = Campaign.name.ilike(f"%{filters.search}%")
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)
        
        if filters.campaign_type:
            stmt = stmt.where(Campaign.campaign_type == filters.campaign_type)
            count_stmt = count_stmt.where(Campaign.campaign_type == filters.campaign_type)
        
        if filters.status:
            stmt = stmt.where(Campaign.status == filters.status)
            count_stmt = count_stmt.where(Campaign.status == filters.status)
        
        if filters.created_by:
            stmt = stmt.where(Campaign.created_by_user_id == filters.created_by)
            count_stmt = count_stmt.where(Campaign.created_by_user_id == filters.created_by)
        
        if filters.is_ab_test is not None:
            stmt = stmt.where(Campaign.is_ab_test == filters.is_ab_test)
            count_stmt = count_stmt.where(Campaign.is_ab_test == filters.is_ab_test)
        
        if filters.created_from:
            stmt = stmt.where(Campaign.created_at >= filters.created_from)
            count_stmt = count_stmt.where(Campaign.created_at >= filters.created_from)
        
        if filters.created_to:
            stmt = stmt.where(Campaign.created_at <= filters.created_to)
            count_stmt = count_stmt.where(Campaign.created_at <= filters.created_to)
        
        # Sorting
        sort_field = getattr(Campaign, filters.sort_by, Campaign.created_at)
        if filters.sort_order == "asc":
            stmt = stmt.order_by(sort_field.asc())
        else:
            stmt = stmt.order_by(sort_field.desc())
        
        # Pagination
        offset = (filters.page - 1) * filters.per_page
        stmt = stmt.offset(offset).limit(filters.per_page)
        
        # Execute queries
        result = await session.execute(stmt)
        campaigns = result.scalars().all()
        
        count_result = await session.execute(count_stmt)
        total = count_result.scalar()
        
        # Calculate pagination info
        pages = (total + filters.per_page - 1) // filters.per_page
        has_prev = filters.page > 1
        has_next = filters.page < pages
        
        return PaginatedResponse(
            items=[CampaignResponse.model_validate(campaign) for campaign in campaigns],
            total=total,
            page=filters.page,
            per_page=filters.per_page,
            pages=pages,
            has_prev=has_prev,
            has_next=has_next
        )
        
    except Exception as e:
        logger.error(f"Campaign list failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve campaigns"
        )


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Get campaign by ID."""
    campaign = await get_campaign_or_404(campaign_id, session, current_user)
    return CampaignResponse.model_validate(campaign)


@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: UUID,
    campaign_update: CampaignUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Update campaign information."""
    try:
        # Check permissions
        if not current_user.is_manager:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update campaigns"
            )
        
        campaign = await get_campaign_or_404(campaign_id, session, current_user)
        
        # Check if campaign can be updated
        if campaign.status in ["running", "completed", "cancelled"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot update campaign with status: {campaign.status}"
            )
        
        # Update fields
        update_dict = campaign_update.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(campaign, field, value)
        
        campaign.updated_by = current_user.id
        await session.commit()
        await session.refresh(campaign)
        
        logger.info(f"Updated campaign: {campaign_id}")
        return CampaignResponse.model_validate(campaign)
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Campaign update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update campaign"
        )


@router.post("/{campaign_id}/actions", status_code=status.HTTP_200_OK)
async def perform_campaign_action(
    campaign_id: UUID,
    action_data: CampaignAction,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Perform campaign actions (start, pause, resume, cancel)."""
    try:
        # Check permissions
        if not current_user.is_manager:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to control campaigns"
            )
        
        campaign = await get_campaign_or_404(campaign_id, session, current_user)
        
        # Perform action
        if action_data.action == "start":
            campaign.start_campaign()
        elif action_data.action == "pause":
            campaign.pause_campaign()
        elif action_data.action == "resume":
            campaign.resume_campaign()
        elif action_data.action == "cancel":
            campaign.cancel_campaign(action_data.reason)
        elif action_data.action == "complete":
            campaign.complete_campaign()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown action: {action_data.action}"
            )
        
        await session.commit()
        
        logger.info(f"Campaign action performed: {campaign_id} - {action_data.action}")
        return {"message": f"Campaign {action_data.action} successful"}
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        await session.rollback()
        logger.error(f"Campaign action failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Campaign action failed"
        )


@router.get("/{campaign_id}/stats", response_model=CampaignStats)
async def get_campaign_stats(
    campaign_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Get campaign statistics."""
    try:
        campaign = await get_campaign_or_404(campaign_id, session, current_user)
        
        # Get performance summary
        performance_summary = campaign.get_performance_summary()
        
        # Get targeting summary
        targeting_summary = campaign.get_targeting_summary()
        
        # Mock additional data (implement as needed)
        hourly_breakdown = []  # Implement hourly performance analysis
        variant_performance = []  # Implement A/B test variant analysis
        top_performing_times = []  # Implement optimal timing analysis
        customer_segments = {}  # Implement segment performance analysis
        
        return CampaignStats(
            campaign_id=campaign_id,
            performance_summary=performance_summary,
            targeting_summary=targeting_summary,
            hourly_breakdown=hourly_breakdown,
            variant_performance=variant_performance if campaign.is_ab_test else None,
            top_performing_times=top_performing_times,
            customer_segments=customer_segments
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Campaign stats failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve campaign statistics"
        )


@router.delete("/{campaign_id}", status_code=status.HTTP_200_OK)
async def delete_campaign(
    campaign_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Soft delete campaign."""
    try:
        # Check permissions
        if not current_user.is_manager:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to delete campaigns"
            )
        
        campaign = await get_campaign_or_404(campaign_id, session, current_user)
        
        # Check if campaign can be deleted
        if campaign.status == "running":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete running campaign. Pause or cancel first."
            )
        
        # Soft delete
        campaign.soft_delete()
        campaign.updated_by = current_user.id
        await session.commit()
        
        logger.info(f"Deleted campaign: {campaign_id}")
        return {"message": "Campaign deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Campaign deletion failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete campaign"
        )


# ===== ADVANCED CAMPAIGN FEATURES =====

@router.post("/{campaign_id}/recipients", response_model=List[CampaignRecipientResponse])
async def add_campaign_recipients(
    campaign_id: UUID,
    recipients_data: CampaignRecipientCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Add recipients to campaign with smart segmentation."""
    try:
        if not current_user.is_manager:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        campaign = await get_campaign_or_404(campaign_id, session, current_user)
        
        if campaign.status != "draft":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only add recipients to draft campaigns"
            )
        
        # Get customer data for segmentation
        stmt = select(Customer).where(Customer.id.in_(recipients_data.customer_ids))
        result = await session.execute(stmt)
        customers = result.scalars().all()
        
        if len(customers) != len(recipients_data.customer_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some customer IDs are invalid"
            )
        
        # Apply segmentation logic
        segmented_customers = await segmentation_service.segment_customers(
            customers=customers,
            targeting_config=campaign.targeting_config,
            session=session
        )
        
        # Generate personalization data
        personalized_data = await personalization_engine.generate_personalization_data(
            customers=segmented_customers,
            campaign=campaign,
            session=session
        )
        
        # Optimize timing for each recipient
        optimized_timings = await timing_service.optimize_send_times(
            customers=segmented_customers,
            campaign=campaign
        )
        
        # Handle A/B testing variant assignments
        variant_assignments = {}
        if campaign.is_ab_test and campaign.ab_test_config:
            variant_assignments = ab_testing_service.assign_variants(
                customer_ids=[c.id for c in segmented_customers],
                ab_config=campaign.ab_test_config
            )
        
        # Create recipient records
        recipients = []
        for customer in segmented_customers:
            recipient_data = {
                "campaign_id": campaign_id,
                "customer_id": customer.id,
                "variant_id": variant_assignments.get(customer.id),
                "personalization_data": personalized_data.get(customer.id, {}),
                "scheduled_send_time": optimized_timings.get(customer.id)
            }
            recipient = CampaignRecipient(**recipient_data)
            recipients.append(recipient)
            session.add(recipient)
        
        # Update campaign recipients count
        campaign.recipients_count = len(recipients)
        
        await session.commit()
        
        # Schedule background personalization if needed
        background_tasks.add_task(
            personalization_engine.enhance_personalization,
            campaign_id=campaign_id,
            recipient_ids=[r.id for r in recipients]
        )
        
        logger.info(f"Added {len(recipients)} recipients to campaign {campaign_id}")
        
        # Return response data
        return [
            CampaignRecipientResponse.model_validate(recipient) 
            for recipient in recipients
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Adding recipients failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add campaign recipients"
        )


@router.post("/{campaign_id}/execute", status_code=status.HTTP_202_ACCEPTED)
async def execute_campaign(
    campaign_id: UUID,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Execute campaign with bulk messaging and real-time monitoring."""
    try:
        if not current_user.is_manager:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        campaign = await get_campaign_or_404(campaign_id, session, current_user)
        
        if not campaign.can_be_started:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Campaign cannot be started"
            )
        
        # Start the campaign
        campaign.start_campaign()
        await session.commit()
        
        # Execute campaign in background with real-time updates
        background_tasks.add_task(
            campaign_execution_service.execute_campaign,
            campaign_id=campaign_id,
            websocket_manager=websocket_manager
        )
        
        logger.info(f"Campaign execution started: {campaign_id}")
        
        return {
            "message": "Campaign execution started",
            "campaign_id": str(campaign_id),
            "status": "executing",
            "websocket_endpoint": f"/ws/campaigns/{campaign_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Campaign execution failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute campaign"
        )


@router.get("/{campaign_id}/analytics", response_model=CampaignAnalytics)
async def get_campaign_analytics(
    campaign_id: UUID,
    period: str = "24h",
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Get comprehensive campaign analytics and ROI metrics."""
    try:
        campaign = await get_campaign_or_404(campaign_id, session, current_user)
        
        analytics_data = await analytics_service.get_comprehensive_analytics(
            campaign=campaign,
            period=period,
            session=session
        )
        
        return CampaignAnalytics(**analytics_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Campaign analytics failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve campaign analytics"
        )


@router.get("/{campaign_id}/ab-test-results", response_model=ABTestResults)
async def get_ab_test_results(
    campaign_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Get A/B testing statistical analysis results."""
    try:
        campaign = await get_campaign_or_404(campaign_id, session, current_user)
        
        if not campaign.is_ab_test:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Campaign is not an A/B test"
            )
        
        # Get recipients with variant data
        stmt = select(CampaignRecipient).where(
            CampaignRecipient.campaign_id == campaign_id
        ).options(selectinload(CampaignRecipient.customer))
        result = await session.execute(stmt)
        recipients = result.scalars().all()
        
        # Perform statistical analysis
        ab_results = await ab_testing_service.analyze_ab_test(
            campaign=campaign,
            recipients=recipients
        )
        
        return ABTestResults(**ab_results)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"A/B test analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze A/B test results"
        )


@router.get("/{campaign_id}/customer-journey", response_model=Dict[str, Any])
async def get_customer_journey(
    campaign_id: UUID,
    customer_id: Optional[UUID] = None,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Get customer journey mapping for campaign."""
    try:
        campaign = await get_campaign_or_404(campaign_id, session, current_user)
        
        journey_data = await analytics_service.map_customer_journey(
            campaign=campaign,
            customer_id=customer_id,
            session=session
        )
        
        return journey_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Customer journey mapping failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to map customer journey"
        )


@router.post("/bulk-operations", status_code=status.HTTP_200_OK)
async def bulk_campaign_operations(
    operation_data: BulkCampaignOperation,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Perform bulk operations on multiple campaigns."""
    try:
        if not current_user.is_manager:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Validate campaigns exist and user has access
        stmt = select(Campaign).where(
            Campaign.id.in_(operation_data.campaign_ids),
            Campaign.is_deleted == False
        )
        
        if not current_user.is_superuser:
            stmt = stmt.where(Campaign.restaurant_id == current_user.restaurant_id)
        
        result = await session.execute(stmt)
        campaigns = result.scalars().all()
        
        if len(campaigns) != len(operation_data.campaign_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some campaigns not found or access denied"
            )
        
        # Execute bulk operation in background
        background_tasks.add_task(
            campaign_execution_service.execute_bulk_operation,
            campaigns=campaigns,
            operation=operation_data.operation,
            parameters=operation_data.parameters,
            websocket_manager=websocket_manager
        )
        
        logger.info(f"Bulk operation initiated: {operation_data.operation} on {len(campaigns)} campaigns")
        
        return {
            "message": f"Bulk {operation_data.operation} initiated",
            "campaign_count": len(campaigns),
            "operation_id": str(UUID()),  # Generate operation tracking ID
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk operation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bulk operation failed"
        )


@router.get("/templates", response_model=List[CampaignTemplate])
async def get_campaign_templates(
    campaign_type: Optional[str] = None,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Get campaign templates for quick setup."""
    try:
        templates = await campaign_execution_service.get_campaign_templates(
            restaurant_id=current_user.restaurant_id,
            campaign_type=campaign_type,
            session=session
        )
        
        return [CampaignTemplate(**template) for template in templates]
        
    except Exception as e:
        logger.error(f"Get templates failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve templates"
        )


@router.post("/{campaign_id}/optimize", status_code=status.HTTP_200_OK)
async def optimize_campaign(
    campaign_id: UUID,
    optimization_type: str,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Optimize campaign using AI and machine learning."""
    try:
        if not current_user.is_manager:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        campaign = await get_campaign_or_404(campaign_id, session, current_user)
        
        # Validate optimization type
        valid_types = ["timing", "content", "targeting", "ab_test", "full"]
        if optimization_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid optimization type. Must be one of: {valid_types}"
            )
        
        # Start optimization in background
        background_tasks.add_task(
            campaign_execution_service.optimize_campaign,
            campaign=campaign,
            optimization_type=optimization_type,
            session=session,
            websocket_manager=websocket_manager
        )
        
        logger.info(f"Campaign optimization started: {campaign_id} - {optimization_type}")
        
        return {
            "message": f"Campaign {optimization_type} optimization started",
            "campaign_id": str(campaign_id),
            "optimization_type": optimization_type,
            "status": "optimizing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Campaign optimization failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Campaign optimization failed"
        )


@router.websocket("/ws/{campaign_id}")
async def campaign_websocket(
    websocket: WebSocket,
    campaign_id: UUID,
    current_user: User = Depends(current_active_user)
):
    """WebSocket endpoint for real-time campaign monitoring."""
    await websocket_manager.connect(websocket, str(campaign_id))
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
            # Handle client commands (pause, resume, etc.)
            if data:
                command = data.strip().lower()
                if command in ["pause", "resume", "status"]:
                    await websocket_manager.handle_campaign_command(
                        campaign_id=str(campaign_id),
                        command=command,
                        user_id=str(current_user.id)
                    )
                    
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, str(campaign_id))
        logger.info(f"WebSocket disconnected for campaign: {campaign_id}")


@router.get("/{campaign_id}/export")
async def export_campaign_data(
    campaign_id: UUID,
    format: str = "csv",
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Export campaign data in various formats."""
    try:
        campaign = await get_campaign_or_404(campaign_id, session, current_user)
        
        if format not in ["csv", "excel", "json", "pdf"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid export format. Supported: csv, excel, json, pdf"
            )
        
        # Generate export data
        export_stream = await analytics_service.export_campaign_data(
            campaign=campaign,
            format=format,
            session=session
        )
        
        # Set appropriate headers
        filename = f"campaign_{campaign.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
        media_type = {
            "csv": "text/csv",
            "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "json": "application/json",
            "pdf": "application/pdf"
        }[format]
        
        return StreamingResponse(
            export_stream,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Campaign export failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export campaign data"
        )