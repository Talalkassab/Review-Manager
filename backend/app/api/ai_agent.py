"""
AI Agent management API routes.
Handles agent personas, message flows, and AI interactions.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from ..core.logging import get_logger
from ..database import get_db_session
from ..models import AgentPersona, MessageFlow, AIInteraction, User
from ..schemas import (
    AgentPersonaCreate, AgentPersonaUpdate, AgentPersonaResponse,
    MessageFlowCreate, MessageFlowUpdate, MessageFlowResponse,
    AIInteractionResponse, AIInteractionFeedback, ConversationTestRequest,
    ConversationTestResponse, PersonaListFilter, PaginatedResponse,
    ErrorResponse
)
from .auth import current_active_user

logger = get_logger(__name__)
router = APIRouter()


async def get_persona_or_404(
    persona_id: UUID,
    session: AsyncSession,
    user: User,
    check_restaurant: bool = True
) -> AgentPersona:
    """Get agent persona by ID or raise 404."""
    stmt = select(AgentPersona).where(AgentPersona.id == persona_id)
    
    if check_restaurant and not user.is_superuser:
        stmt = stmt.where(AgentPersona.restaurant_id == user.restaurant_id)
    
    result = await session.execute(stmt)
    persona = result.scalar_one_or_none()
    
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent persona not found"
        )
    
    return persona


async def get_message_flow_or_404(
    flow_id: UUID,
    session: AsyncSession,
    user: User,
    check_restaurant: bool = True
) -> MessageFlow:
    """Get message flow by ID or raise 404."""
    stmt = select(MessageFlow).where(MessageFlow.id == flow_id)
    
    if check_restaurant and not user.is_superuser:
        stmt = stmt.where(MessageFlow.restaurant_id == user.restaurant_id)
    
    result = await session.execute(stmt)
    flow = result.scalar_one_or_none()
    
    if not flow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message flow not found"
        )
    
    return flow


# Agent Persona Routes
@router.post("/personas", response_model=AgentPersonaResponse, status_code=status.HTTP_201_CREATED)
async def create_persona(
    persona_data: AgentPersonaCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Create a new agent persona."""
    try:
        # Check permissions
        if not current_user.is_manager:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create agent personas"
            )
        
        # Verify restaurant access
        if not current_user.is_superuser and persona_data.restaurant_id != current_user.restaurant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create persona for different restaurant"
            )
        
        # Create persona
        persona_dict = persona_data.model_dump()
        persona_dict["created_by_user_id"] = current_user.id
        
        persona = AgentPersona(**persona_dict)
        session.add(persona)
        await session.commit()
        await session.refresh(persona)
        
        logger.info(f"Created agent persona: {persona.id}")
        return AgentPersonaResponse.model_validate(persona)
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Agent persona creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create agent persona"
        )


@router.get("/personas", response_model=PaginatedResponse[AgentPersonaResponse])
async def list_personas(
    filters: PersonaListFilter = Depends(),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """List agent personas with filtering and pagination."""
    try:
        # Base query
        stmt = select(AgentPersona).where(AgentPersona.is_deleted == False)
        count_stmt = select(func.count(AgentPersona.id)).where(AgentPersona.is_deleted == False)
        
        # Restaurant filtering
        if not current_user.is_superuser:
            stmt = stmt.where(AgentPersona.restaurant_id == current_user.restaurant_id)
            count_stmt = count_stmt.where(AgentPersona.restaurant_id == current_user.restaurant_id)
        
        # Apply filters
        if filters.search:
            search_filter = AgentPersona.name.ilike(f"%{filters.search}%")
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)
        
        if filters.is_active is not None:
            stmt = stmt.where(AgentPersona.is_active == filters.is_active)
            count_stmt = count_stmt.where(AgentPersona.is_active == filters.is_active)
        
        if filters.tone_style:
            stmt = stmt.where(AgentPersona.tone_style == filters.tone_style)
            count_stmt = count_stmt.where(AgentPersona.tone_style == filters.tone_style)
        
        if filters.created_by:
            stmt = stmt.where(AgentPersona.created_by_user_id == filters.created_by)
            count_stmt = count_stmt.where(AgentPersona.created_by_user_id == filters.created_by)
        
        # Sorting
        sort_field = getattr(AgentPersona, filters.sort_by, AgentPersona.created_at)
        if filters.sort_order == "asc":
            stmt = stmt.order_by(sort_field.asc())
        else:
            stmt = stmt.order_by(sort_field.desc())
        
        # Pagination
        offset = (filters.page - 1) * filters.per_page
        stmt = stmt.offset(offset).limit(filters.per_page)
        
        # Execute queries
        result = await session.execute(stmt)
        personas = result.scalars().all()
        
        count_result = await session.execute(count_stmt)
        total = count_result.scalar()
        
        # Calculate pagination info
        pages = (total + filters.per_page - 1) // filters.per_page
        has_prev = filters.page > 1
        has_next = filters.page < pages
        
        return PaginatedResponse(
            items=[AgentPersonaResponse.model_validate(persona) for persona in personas],
            total=total,
            page=filters.page,
            per_page=filters.per_page,
            pages=pages,
            has_prev=has_prev,
            has_next=has_next
        )
        
    except Exception as e:
        logger.error(f"Persona list failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agent personas"
        )


@router.get("/personas/{persona_id}", response_model=AgentPersonaResponse)
async def get_persona(
    persona_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Get agent persona by ID."""
    persona = await get_persona_or_404(persona_id, session, current_user)
    return AgentPersonaResponse.model_validate(persona)


@router.patch("/personas/{persona_id}", response_model=AgentPersonaResponse)
async def update_persona(
    persona_id: UUID,
    persona_update: AgentPersonaUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Update agent persona."""
    try:
        # Check permissions
        if not current_user.is_manager:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update agent personas"
            )
        
        persona = await get_persona_or_404(persona_id, session, current_user)
        
        # Update fields
        update_dict = persona_update.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(persona, field, value)
        
        persona.updated_by = current_user.id
        await session.commit()
        await session.refresh(persona)
        
        logger.info(f"Updated agent persona: {persona_id}")
        return AgentPersonaResponse.model_validate(persona)
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Agent persona update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update agent persona"
        )


@router.post("/personas/{persona_id}/test", response_model=ConversationTestResponse)
async def test_persona_conversation(
    persona_id: UUID,
    test_request: ConversationTestRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Test agent persona in conversation scenarios."""
    try:
        # Check permissions
        if not current_user.is_manager:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to test agent personas"
            )
        
        persona = await get_persona_or_404(persona_id, session, current_user)
        
        # Mock conversation testing (implement actual testing logic)
        import uuid
        test_id = uuid.uuid4()
        
        # Placeholder results - implement actual conversation testing
        test_results = []
        for i, scenario in enumerate(test_request.test_scenarios):
            test_results.append({
                "scenario_id": i,
                "scenario_name": scenario.get("name", f"Test {i+1}"),
                "passed": True,
                "score": 85.0,
                "issues": [],
                "recommendations": []
            })
        
        return ConversationTestResponse(
            test_id=test_id,
            persona_id=persona_id,
            test_results=test_results,
            overall_score=85.0,
            performance_metrics={
                "response_time_avg": 1.2,
                "accuracy_score": 90.0,
                "consistency_score": 88.0
            },
            recommendations=["Consider more cultural context", "Improve response timing"],
            cultural_sensitivity_score=92.0,
            response_consistency_score=88.0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Persona testing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test agent persona"
        )


# Message Flow Routes
@router.post("/flows", response_model=MessageFlowResponse, status_code=status.HTTP_201_CREATED)
async def create_message_flow(
    flow_data: MessageFlowCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Create a new message flow."""
    try:
        # Check permissions
        if not current_user.is_manager:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create message flows"
            )
        
        # Verify restaurant access
        if not current_user.is_superuser and flow_data.restaurant_id != current_user.restaurant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create flow for different restaurant"
            )
        
        # Create flow
        flow_dict = flow_data.model_dump()
        flow_dict["created_by_user_id"] = current_user.id
        
        flow = MessageFlow(**flow_dict)
        session.add(flow)
        await session.commit()
        await session.refresh(flow)
        
        logger.info(f"Created message flow: {flow.id}")
        return MessageFlowResponse.model_validate(flow)
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Message flow creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create message flow"
        )


@router.get("/flows", response_model=List[MessageFlowResponse])
async def list_message_flows(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    flow_type: Optional[str] = None,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """List message flows."""
    try:
        stmt = select(MessageFlow).where(MessageFlow.is_deleted == False)
        
        # Restaurant filtering
        if not current_user.is_superuser:
            stmt = stmt.where(MessageFlow.restaurant_id == current_user.restaurant_id)
        
        # Apply filters
        if is_active is not None:
            stmt = stmt.where(MessageFlow.is_active == is_active)
        
        if flow_type:
            stmt = stmt.where(MessageFlow.flow_type == flow_type)
        
        # Order by priority and creation date
        stmt = stmt.order_by(MessageFlow.priority.desc(), MessageFlow.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)
        
        result = await session.execute(stmt)
        flows = result.scalars().all()
        
        return [MessageFlowResponse.model_validate(flow) for flow in flows]
        
    except Exception as e:
        logger.error(f"Message flow list failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve message flows"
        )


@router.get("/flows/{flow_id}", response_model=MessageFlowResponse)
async def get_message_flow(
    flow_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Get message flow by ID."""
    flow = await get_message_flow_or_404(flow_id, session, current_user)
    return MessageFlowResponse.model_validate(flow)


@router.patch("/flows/{flow_id}", response_model=MessageFlowResponse)
async def update_message_flow(
    flow_id: UUID,
    flow_update: MessageFlowUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Update message flow."""
    try:
        # Check permissions
        if not current_user.is_manager:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update message flows"
            )
        
        flow = await get_message_flow_or_404(flow_id, session, current_user)
        
        # Update fields
        update_dict = flow_update.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(flow, field, value)
        
        flow.updated_by = current_user.id
        await session.commit()
        await session.refresh(flow)
        
        logger.info(f"Updated message flow: {flow_id}")
        return MessageFlowResponse.model_validate(flow)
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Message flow update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update message flow"
        )


# AI Interaction Routes
@router.get("/interactions", response_model=List[AIInteractionResponse])
async def list_ai_interactions(
    skip: int = 0,
    limit: int = 100,
    interaction_type: Optional[str] = None,
    requires_review: Optional[bool] = None,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """List AI interactions."""
    try:
        stmt = select(AIInteraction).where(AIInteraction.is_deleted == False)
        
        # Restaurant filtering
        if not current_user.is_superuser:
            stmt = stmt.where(AIInteraction.restaurant_id == current_user.restaurant_id)
        
        # Apply filters
        if interaction_type:
            stmt = stmt.where(AIInteraction.interaction_type == interaction_type)
        
        if requires_review is not None:
            stmt = stmt.where(AIInteraction.requires_review == requires_review)
        
        # Order by creation date (newest first)
        stmt = stmt.order_by(AIInteraction.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)
        
        result = await session.execute(stmt)
        interactions = result.scalars().all()
        
        return [AIInteractionResponse.model_validate(interaction) for interaction in interactions]
        
    except Exception as e:
        logger.error(f"AI interactions list failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve AI interactions"
        )


@router.post("/interactions/{interaction_id}/feedback", status_code=status.HTTP_200_OK)
async def provide_ai_feedback(
    interaction_id: UUID,
    feedback: AIInteractionFeedback,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(current_active_user)
):
    """Provide feedback on AI interaction."""
    try:
        # Check permissions
        if not current_user.is_manager:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to provide AI feedback"
            )
        
        # Get interaction
        stmt = select(AIInteraction).where(AIInteraction.id == interaction_id)
        if not current_user.is_superuser:
            stmt = stmt.where(AIInteraction.restaurant_id == current_user.restaurant_id)
        
        result = await session.execute(stmt)
        interaction = result.scalar_one_or_none()
        
        if not interaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AI interaction not found"
            )
        
        # Record feedback
        interaction.record_human_feedback(feedback.score, feedback.notes)
        
        # Add tags if provided
        if feedback.tags:
            if not interaction.learning_tags:
                interaction.learning_tags = []
            interaction.learning_tags.extend(feedback.tags)
        
        await session.commit()
        
        logger.info(f"AI feedback recorded: {interaction_id}")
        return {"message": "Feedback recorded successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"AI feedback failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record AI feedback"
        )