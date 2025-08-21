"""
Agent Testing Framework API Router
==================================

Main router for the comprehensive agent testing system.
Provides endpoints for all testing interfaces including:
- Test Playground API
- A/B Testing API  
- Scenario Testing API
- Performance Monitoring API
- Test Data Generator
- WebSocket API
- Test Session Management

Based on AI_AGENT_SYSTEM_PLAN.md Section 7.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid

from fastapi import (
    APIRouter, 
    Depends, 
    HTTPException, 
    status, 
    Query, 
    WebSocket,
    WebSocketDisconnect,
    BackgroundTasks
)
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
import json

from ..core.logging import get_logger
from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..testing.schemas import (
    # Session Management
    TestSessionCreate,
    TestSessionUpdate,
    TestSessionResponse,
    TestSessionStatus,
    
    # Conversation Testing
    TestConversationCreate,
    TestConversationResponse,
    TestMessage,
    ConversationAnalysis,
    
    # A/B Testing
    ABTestCreate,
    ABTestResponse,
    MessageVariant,
    VariantResult,
    StatisticalAnalysis,
    
    # Scenario Testing
    TestScenarioCreate,
    TestScenarioResponse,
    ScenarioTestResult,
    BatchTestRequest,
    BatchTestResult,
    
    # Performance Monitoring
    PerformanceMetricCreate,
    PerformanceMetricResponse,
    RealTimeMetrics,
    PerformanceAlert,
    
    # Customer Simulation
    SyntheticCustomerCreate,
    SyntheticCustomerResponse,
    CustomerProfileSimulatorConfig,
    CustomerProfileType,
    
    # Integration Testing
    IntegrationTestConfig,
    IntegrationTestResult,
    
    # WebSocket
    WebSocketMessage,
    TestProgressUpdate
)

# Import API modules for different testing components
from ..testing import (
    conversation_playground,
    ab_testing, 
    scenario_testing,
    performance_monitor as performance_monitoring,
    test_data_generator,
    websocket_handler,
    session_manager,
    statistical_analysis,
    integration_testing,
    test_reporting
)

logger = get_logger(__name__)
router = APIRouter()

# WebSocket connection manager for real-time testing feedback
class TestingWebSocketManager:
    """Manages WebSocket connections for real-time testing updates."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.test_subscriptions: Dict[str, List[str]] = {}  # user_id -> test_session_ids
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a user to WebSocket updates."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.test_subscriptions[user_id] = []
        logger.info(f"WebSocket connected for user {user_id}")
    
    def disconnect(self, user_id: str):
        """Disconnect a user from WebSocket updates."""
        self.active_connections.pop(user_id, None)
        self.test_subscriptions.pop(user_id, None)
        logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def subscribe_to_test(self, user_id: str, test_session_id: str):
        """Subscribe user to updates from a specific test session."""
        if user_id in self.test_subscriptions:
            if test_session_id not in self.test_subscriptions[user_id]:
                self.test_subscriptions[user_id].append(test_session_id)
    
    async def broadcast_test_update(self, test_session_id: str, update: TestProgressUpdate):
        """Broadcast test progress update to subscribed users."""
        message = WebSocketMessage(
            type="test_progress_update",
            data=update.dict()
        )
        
        for user_id, subscriptions in self.test_subscriptions.items():
            if test_session_id in subscriptions and user_id in self.active_connections:
                try:
                    await self.active_connections[user_id].send_text(message.json())
                except Exception as e:
                    logger.error(f"Failed to send WebSocket update to user {user_id}: {e}")
                    # Clean up dead connection
                    self.disconnect(user_id)

# Global WebSocket manager instance
websocket_manager = TestingWebSocketManager()


# ==============================================================================
# SESSION MANAGEMENT ENDPOINTS
# ==============================================================================

@router.post("/sessions", response_model=TestSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_test_session(
    session_data: TestSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TestSessionResponse:
    """
    Create a new test session for agent testing.
    
    Supports different types of testing:
    - Conversation playground testing
    - A/B testing campaigns  
    - Scenario-based testing
    - Integration testing
    - Performance benchmarking
    """
    try:
        logger.info(f"Creating test session: {session_data.session_name} for user {current_user.id}")
        
        # Create test session using session manager
        test_session = await session_manager.create_session(
            db=db,
            user_id=current_user.id,
            session_data=session_data
        )
        
        logger.info(f"Test session created with ID: {test_session.id}")
        return test_session
        
    except Exception as e:
        logger.error(f"Failed to create test session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create test session: {str(e)}"
        )


@router.get("/sessions", response_model=List[TestSessionResponse])
async def get_test_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session_type: Optional[str] = Query(None),
    status_filter: Optional[TestSessionStatus] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[TestSessionResponse]:
    """Get test sessions for the current user with filtering and pagination."""
    try:
        sessions = await session_manager.get_user_sessions(
            db=db,
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            session_type=session_type,
            status_filter=status_filter
        )
        return sessions
        
    except Exception as e:
        logger.error(f"Failed to retrieve test sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve test sessions"
        )


@router.get("/sessions/{session_id}", response_model=TestSessionResponse)
async def get_test_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TestSessionResponse:
    """Get detailed information about a specific test session."""
    try:
        session = await session_manager.get_session_by_id(
            db=db,
            session_id=session_id,
            user_id=current_user.id
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test session not found"
            )
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get test session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve test session"
        )


@router.patch("/sessions/{session_id}", response_model=TestSessionResponse)
async def update_test_session(
    session_id: int,
    session_update: TestSessionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TestSessionResponse:
    """Update a test session's configuration or status."""
    try:
        updated_session = await session_manager.update_session(
            db=db,
            session_id=session_id,
            user_id=current_user.id,
            session_update=session_update
        )
        
        if not updated_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test session not found"
            )
        
        return updated_session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update test session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update test session"
        )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a test session and all associated data."""
    try:
        deleted = await session_manager.delete_session(
            db=db,
            session_id=session_id,
            user_id=current_user.id
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test session not found"
            )
        
        logger.info(f"Test session {session_id} deleted by user {current_user.id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete test session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete test session"
        )


# ==============================================================================
# CONVERSATION PLAYGROUND ENDPOINTS  
# ==============================================================================

@router.post("/sessions/{session_id}/conversations", response_model=TestConversationResponse)
async def start_test_conversation(
    session_id: int,
    conversation_data: TestConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TestConversationResponse:
    """Start a new test conversation in the playground."""
    try:
        # Validate session exists and belongs to user
        session = await session_manager.get_session_by_id(db, session_id, current_user.id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test session not found"
            )
        
        # Create test conversation
        conversation = await conversation_playground.create_test_conversation(
            db=db,
            session_id=session_id,
            conversation_data=conversation_data
        )
        
        # Subscribe user to WebSocket updates for this conversation
        await websocket_manager.subscribe_to_test(str(current_user.id), str(session_id))
        
        logger.info(f"Test conversation started: {conversation.id} in session {session_id}")
        return conversation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start test conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start test conversation"
        )


@router.post("/conversations/{conversation_id}/messages", response_model=TestMessage)
async def send_test_message(
    conversation_id: int,
    message_content: str,
    sender: str = Query(..., pattern="^(customer|agent)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TestMessage:
    """Send a message in a test conversation and get AI agent response."""
    try:
        # Send message and get agent response
        test_message = await conversation_playground.send_message(
            db=db,
            conversation_id=conversation_id,
            message_content=message_content,
            sender=sender,
            user_id=current_user.id
        )
        
        # Broadcast real-time update via WebSocket
        await websocket_manager.broadcast_test_update(
            test_session_id=str(conversation_id),  # Assuming conversation maps to session
            update=TestProgressUpdate(
                test_session_id=conversation_id,
                progress_percentage=50.0,  # Calculate based on conversation progress
                current_step=f"Processing {sender} message",
                metrics_update=None  # Add real-time metrics if needed
            )
        )
        
        return test_message
        
    except Exception as e:
        logger.error(f"Failed to send test message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test message"
        )


@router.get("/conversations/{conversation_id}/analysis", response_model=ConversationAnalysis)
async def get_conversation_analysis(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ConversationAnalysis:
    """Get comprehensive analysis of a test conversation."""
    try:
        analysis = await conversation_playground.analyze_conversation(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id
        )
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found or analysis not available"
            )
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze conversation"
        )


# ==============================================================================
# A/B TESTING ENDPOINTS
# ==============================================================================

@router.post("/sessions/{session_id}/ab-tests", response_model=ABTestResponse)
async def create_ab_test(
    session_id: int,
    ab_test_data: ABTestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ABTestResponse:
    """Create and start a new A/B test campaign."""
    try:
        # Validate session
        session = await session_manager.get_session_by_id(db, session_id, current_user.id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test session not found"
            )
        
        # Create A/B test
        ab_test = await ab_testing.create_ab_test(
            db=db,
            session_id=session_id,
            ab_test_data=ab_test_data,
            user_id=current_user.id
        )
        
        logger.info(f"A/B test created: {ab_test.id} with {len(ab_test_data.variants)} variants")
        return ab_test
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create A/B test: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create A/B test"
        )


@router.get("/ab-tests/{test_id}/results", response_model=List[VariantResult])
async def get_ab_test_results(
    test_id: int,
    include_confidence_intervals: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[VariantResult]:
    """Get real-time results from an A/B test."""
    try:
        results = await ab_testing.get_test_results(
            db=db,
            test_id=test_id,
            user_id=current_user.id,
            include_confidence_intervals=include_confidence_intervals
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to get A/B test results: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve A/B test results"
        )


@router.get("/ab-tests/{test_id}/statistical-analysis", response_model=StatisticalAnalysis)
async def get_ab_test_statistical_analysis(
    test_id: int,
    confidence_level: float = Query(0.95, ge=0.8, le=0.99),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> StatisticalAnalysis:
    """Get statistical significance analysis for A/B test."""
    try:
        analysis = await statistical_analysis.analyze_ab_test(
            db=db,
            test_id=test_id,
            confidence_level=confidence_level,
            user_id=current_user.id
        )
        
        return analysis
        
    except Exception as e:
        logger.error(f"Failed to get statistical analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform statistical analysis"
        )


@router.post("/ab-tests/{test_id}/stop")
async def stop_ab_test(
    test_id: int,
    declare_winner: Optional[str] = Query(None, description="Variant name to declare as winner"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Stop an active A/B test and optionally declare a winner."""
    try:
        stopped_test = await ab_testing.stop_test(
            db=db,
            test_id=test_id,
            user_id=current_user.id,
            winner_variant=declare_winner
        )
        
        if not stopped_test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="A/B test not found"
            )
        
        logger.info(f"A/B test {test_id} stopped by user {current_user.id}")
        return {"message": "A/B test stopped successfully", "winner": declare_winner}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop A/B test: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop A/B test"
        )


# ==============================================================================
# SCENARIO TESTING ENDPOINTS
# ==============================================================================

@router.post("/scenarios", response_model=TestScenarioResponse)
async def create_test_scenario(
    scenario_data: TestScenarioCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TestScenarioResponse:
    """Create a new test scenario for reusable testing."""
    try:
        scenario = await scenario_testing.create_scenario(
            db=db,
            scenario_data=scenario_data,
            user_id=current_user.id
        )
        
        logger.info(f"Test scenario created: {scenario.id} - {scenario.scenario_name}")
        return scenario
        
    except Exception as e:
        logger.error(f"Failed to create test scenario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create test scenario"
        )


@router.get("/scenarios", response_model=List[TestScenarioResponse])
async def get_test_scenarios(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    scenario_type: Optional[str] = Query(None),
    difficulty_level: Optional[str] = Query(None),
    tags: Optional[List[str]] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[TestScenarioResponse]:
    """Get available test scenarios with filtering."""
    try:
        scenarios = await scenario_testing.get_scenarios(
            db=db,
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            scenario_type=scenario_type,
            difficulty_level=difficulty_level,
            tags=tags
        )
        
        return scenarios
        
    except Exception as e:
        logger.error(f"Failed to retrieve test scenarios: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve test scenarios"
        )


@router.post("/sessions/{session_id}/scenarios/{scenario_id}/run", response_model=ScenarioTestResult)
async def run_test_scenario(
    session_id: int,
    scenario_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ScenarioTestResult:
    """Run a specific test scenario and return results."""
    try:
        # Validate session
        session = await session_manager.get_session_by_id(db, session_id, current_user.id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test session not found"
            )
        
        # Start scenario test
        result = await scenario_testing.run_scenario(
            db=db,
            session_id=session_id,
            scenario_id=scenario_id,
            user_id=current_user.id
        )
        
        # Send WebSocket updates in background
        background_tasks.add_task(
            websocket_manager.broadcast_test_update,
            str(session_id),
            TestProgressUpdate(
                test_session_id=session_id,
                progress_percentage=100.0,
                current_step=f"Scenario test completed: {'PASSED' if result.passed else 'FAILED'}",
                metrics_update=None
            )
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to run test scenario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run test scenario"
        )


@router.post("/sessions/{session_id}/batch-test", response_model=BatchTestResult)
async def run_batch_scenario_tests(
    session_id: int,
    batch_request: BatchTestRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> BatchTestResult:
    """Run multiple test scenarios in batch mode."""
    try:
        # Validate session
        session = await session_manager.get_session_by_id(db, session_id, current_user.id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test session not found"
            )
        
        # Start batch testing
        batch_id = str(uuid.uuid4())
        
        # Run batch tests in background
        background_tasks.add_task(
            scenario_testing.run_batch_tests,
            db,
            session_id,
            batch_request,
            current_user.id,
            batch_id,
            websocket_manager
        )
        
        # Return immediate response with batch ID for tracking
        return BatchTestResult(
            batch_id=batch_id,
            total_tests=len(batch_request.scenarios),
            passed_tests=0,
            failed_tests=0,
            execution_time_seconds=0.0,
            individual_results=[]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start batch tests: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start batch tests"
        )


# ==============================================================================
# PERFORMANCE MONITORING ENDPOINTS
# ==============================================================================

@router.get("/sessions/{session_id}/performance/metrics", response_model=List[PerformanceMetricResponse])
async def get_performance_metrics(
    session_id: int,
    metric_category: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[PerformanceMetricResponse]:
    """Get performance metrics for a test session."""
    try:
        metrics = await performance_monitoring.get_session_metrics(
            db=db,
            session_id=session_id,
            user_id=current_user.id,
            metric_category=metric_category,
            start_time=start_time,
            end_time=end_time
        )
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance metrics"
        )


@router.get("/sessions/{session_id}/performance/real-time", response_model=RealTimeMetrics)
async def get_real_time_metrics(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> RealTimeMetrics:
    """Get current real-time performance metrics for a session."""
    try:
        metrics = await performance_monitoring.get_real_time_metrics(
            db=db,
            session_id=session_id,
            user_id=current_user.id
        )
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get real-time metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get real-time metrics"
        )


@router.get("/sessions/{session_id}/performance/alerts", response_model=List[PerformanceAlert])
async def get_performance_alerts(
    session_id: int,
    severity: Optional[str] = Query(None, pattern="^(low|medium|high|critical)$"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[PerformanceAlert]:
    """Get performance alerts for a test session."""
    try:
        alerts = await performance_monitoring.get_session_alerts(
            db=db,
            session_id=session_id,
            user_id=current_user.id,
            severity=severity,
            limit=limit
        )
        
        return alerts
        
    except Exception as e:
        logger.error(f"Failed to get performance alerts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get performance alerts"
        )


# ==============================================================================
# TEST DATA GENERATOR ENDPOINTS
# ==============================================================================

@router.post("/synthetic-customers", response_model=List[SyntheticCustomerResponse])
async def generate_synthetic_customers(
    count: int = Query(..., ge=1, le=100),
    profile_types: List[CustomerProfileType] = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[SyntheticCustomerResponse]:
    """Generate synthetic customer profiles for testing."""
    try:
        customers = await test_data_generator.generate_customers(
            db=db,
            count=count,
            profile_types=profile_types,
            user_id=current_user.id
        )
        
        logger.info(f"Generated {len(customers)} synthetic customers for user {current_user.id}")
        return customers
        
    except Exception as e:
        logger.error(f"Failed to generate synthetic customers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate synthetic customers"
        )


@router.get("/synthetic-customers", response_model=List[SyntheticCustomerResponse])
async def get_synthetic_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    profile_type: Optional[CustomerProfileType] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[SyntheticCustomerResponse]:
    """Get existing synthetic customer profiles."""
    try:
        customers = await test_data_generator.get_customers(
            db=db,
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            profile_type=profile_type
        )
        
        return customers
        
    except Exception as e:
        logger.error(f"Failed to retrieve synthetic customers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve synthetic customers"
        )


# ==============================================================================
# INTEGRATION TESTING ENDPOINTS
# ==============================================================================

@router.post("/integration-tests/whatsapp", response_model=IntegrationTestResult)
async def test_whatsapp_integration(
    test_config: IntegrationTestConfig,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> IntegrationTestResult:
    """Test WhatsApp API integration."""
    try:
        # Run WhatsApp integration tests
        result = await integration_testing.test_whatsapp_integration(
            config=test_config,
            user_id=current_user.id
        )
        
        # Store results in database
        background_tasks.add_task(
            integration_testing.store_test_result,
            db,
            result,
            current_user.id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"WhatsApp integration test failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="WhatsApp integration test failed"
        )


@router.post("/integration-tests/openrouter", response_model=IntegrationTestResult)
async def test_openrouter_integration(
    test_config: IntegrationTestConfig,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> IntegrationTestResult:
    """Test OpenRouter AI API integration."""
    try:
        result = await integration_testing.test_openrouter_integration(
            config=test_config,
            user_id=current_user.id
        )
        
        background_tasks.add_task(
            integration_testing.store_test_result,
            db,
            result,
            current_user.id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"OpenRouter integration test failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OpenRouter integration test failed"
        )


@router.post("/integration-tests/database", response_model=IntegrationTestResult)
async def test_database_integration(
    test_config: IntegrationTestConfig,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> IntegrationTestResult:
    """Test database operations and performance."""
    try:
        result = await integration_testing.test_database_integration(
            db=db,
            config=test_config,
            user_id=current_user.id
        )
        
        background_tasks.add_task(
            integration_testing.store_test_result,
            db,
            result,
            current_user.id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Database integration test failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database integration test failed"
        )


# ==============================================================================
# REPORTING AND EXPORT ENDPOINTS
# ==============================================================================

@router.get("/sessions/{session_id}/report")
async def export_test_report(
    session_id: int,
    format: str = Query("json", pattern="^(json|csv|pdf)$"),
    include_details: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export comprehensive test report for a session."""
    try:
        # Generate report
        report_data = await test_reporting.generate_session_report(
            db=db,
            session_id=session_id,
            user_id=current_user.id,
            include_details=include_details
        )
        
        if format == "json":
            return report_data
        
        elif format == "csv":
            csv_data = await test_reporting.export_to_csv(report_data)
            return StreamingResponse(
                iter([csv_data]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=test_report_{session_id}.csv"}
            )
        
        elif format == "pdf":
            pdf_path = await test_reporting.export_to_pdf(report_data, session_id)
            return FileResponse(
                path=pdf_path,
                media_type="application/pdf",
                filename=f"test_report_{session_id}.pdf"
            )
        
    except Exception as e:
        logger.error(f"Failed to export test report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export test report"
        )


@router.get("/reports/summary")
async def get_testing_summary(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get testing activity summary for dashboard."""
    try:
        summary = await test_reporting.get_testing_summary(
            db=db,
            user_id=current_user.id,
            days=days
        )
        
        return summary
        
    except Exception as e:
        logger.error(f"Failed to get testing summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get testing summary"
        )


# ==============================================================================
# WEBSOCKET ENDPOINT
# ==============================================================================

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    current_user: User = Depends(get_current_user)  # This might need adjustment for WebSocket
):
    """WebSocket endpoint for real-time testing updates."""
    try:
        # Connect user to WebSocket
        await websocket_manager.connect(websocket, user_id)
        
        try:
            while True:
                # Listen for client messages
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "subscribe_test":
                    test_session_id = message.get("test_session_id")
                    if test_session_id:
                        await websocket_manager.subscribe_to_test(user_id, test_session_id)
                
                elif message.get("type") == "ping":
                    # Respond to ping
                    response = WebSocketMessage(
                        type="pong",
                        data={"timestamp": datetime.utcnow().isoformat()}
                    )
                    await websocket.send_text(response.json())
                
        except WebSocketDisconnect:
            websocket_manager.disconnect(user_id)
        
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {str(e)}")
        websocket_manager.disconnect(user_id)