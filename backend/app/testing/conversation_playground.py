"""
Test Conversation Playground API
===============================

Interactive testing environment for agent conversations with real-time analysis.
Supports WebSocket connections for live testing feedback.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..database import get_db
from .models import TestSession, TestConversation
from .schemas import (
    TestSessionCreate, TestSessionResponse, TestSessionUpdate,
    TestConversationCreate, TestConversationResponse,
    TestMessage, ConversationAnalysis, WebSocketMessage,
    TestProgressUpdate, CustomerProfileSimulatorConfig
)
from .customer_simulator import CustomerProfileSimulator
from .performance_monitor import AgentPerformanceMonitor

router = APIRouter(prefix="/testing/playground", tags=["conversation-playground"])

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_connections: Dict[int, List[str]] = {}

    async def connect(self, websocket: WebSocket, session_id: int) -> str:
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = websocket
        
        if session_id not in self.session_connections:
            self.session_connections[session_id] = []
        self.session_connections[session_id].append(connection_id)
        
        return connection_id

    def disconnect(self, connection_id: str, session_id: int):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        if session_id in self.session_connections:
            if connection_id in self.session_connections[session_id]:
                self.session_connections[session_id].remove(connection_id)
            
            if not self.session_connections[session_id]:
                del self.session_connections[session_id]

    async def send_to_session(self, session_id: int, message: dict):
        if session_id in self.session_connections:
            for connection_id in self.session_connections[session_id]:
                if connection_id in self.active_connections:
                    try:
                        await self.active_connections[connection_id].send_text(json.dumps(message))
                    except Exception:
                        # Connection closed, will be cleaned up
                        pass

manager = ConnectionManager()

class ConversationPlaygroundAPI:
    def __init__(self):
        self.customer_simulator = CustomerProfileSimulator()
        self.performance_monitor = AgentPerformanceMonitor()
        self.active_conversations: Dict[int, Dict[str, Any]] = {}

    async def create_test_session(
        self, 
        session_data: TestSessionCreate, 
        db: Session
    ) -> TestSessionResponse:
        """Create a new test conversation session"""
        
        db_session = TestSession(
            session_name=session_data.session_name,
            session_type=session_data.session_type,
            agent_persona_id=session_data.agent_persona_id,
            customer_profile_config=session_data.customer_profile_config,
            test_parameters=session_data.test_parameters or {}
        )
        
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        
        # Initialize conversation state
        self.active_conversations[db_session.id] = {
            "messages": [],
            "start_time": datetime.utcnow(),
            "customer_simulator": None,
            "performance_metrics": {}
        }
        
        return TestSessionResponse.from_orm(db_session)

    async def start_conversation(
        self,
        session_id: int,
        conversation_data: TestConversationCreate,
        db: Session
    ) -> TestConversationResponse:
        """Start a new conversation within a test session"""
        
        # Verify session exists
        session = db.query(TestSession).filter(TestSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Test session not found")
        
        # Create customer simulator
        customer_simulator = await self.customer_simulator.create_customer_profile(
            profile_type=conversation_data.customer_profile_type,
            demographics=conversation_data.customer_demographics,
            context=conversation_data.customer_context
        )
        
        # Create conversation record
        db_conversation = TestConversation(
            session_id=session_id,
            conversation_name=conversation_data.conversation_name,
            customer_profile_type=conversation_data.customer_profile_type,
            customer_demographics=conversation_data.customer_demographics.dict(),
            customer_context=conversation_data.customer_context,
            conversation_messages=[]
        )
        
        db.add(db_conversation)
        db.commit()
        db.refresh(db_conversation)
        
        # Update active conversation
        if session_id in self.active_conversations:
            self.active_conversations[session_id]["customer_simulator"] = customer_simulator
            self.active_conversations[session_id]["conversation_id"] = db_conversation.id
        
        # Send WebSocket update
        await manager.send_to_session(session_id, {
            "type": "conversation_started",
            "data": {
                "conversation_id": db_conversation.id,
                "customer_profile": customer_simulator.profile_summary(),
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        return TestConversationResponse.from_orm(db_conversation)

    async def send_message(
        self,
        session_id: int,
        message: TestMessage,
        db: Session
    ) -> Dict[str, Any]:
        """Process a message in the conversation"""
        
        if session_id not in self.active_conversations:
            raise HTTPException(status_code=404, detail="Active conversation not found")
        
        conversation_state = self.active_conversations[session_id]
        conversation_id = conversation_state.get("conversation_id")
        
        if not conversation_id:
            raise HTTPException(status_code=400, detail="No active conversation in session")
        
        # Add message to conversation
        message_data = message.dict()
        message_data["timestamp"] = datetime.utcnow().isoformat()
        message_data["message_id"] = str(uuid.uuid4())
        
        conversation_state["messages"].append(message_data)
        
        # Process based on sender
        response_data = {}
        
        if message.sender == "customer":
            # Generate agent response
            agent_response = await self._generate_agent_response(
                session_id, message, conversation_state
            )
            response_data["agent_response"] = agent_response
            
        elif message.sender == "agent":
            # Analyze agent response
            analysis = await self._analyze_agent_response(
                session_id, message, conversation_state
            )
            response_data["analysis"] = analysis
            
            # Generate customer response if in simulation mode
            if conversation_state["customer_simulator"]:
                customer_response = await self._generate_customer_response(
                    session_id, message, conversation_state
                )
                response_data["customer_response"] = customer_response
        
        # Update database
        await self._update_conversation_in_db(conversation_id, conversation_state, db)
        
        # Send real-time updates
        await manager.send_to_session(session_id, {
            "type": "message_processed",
            "data": {
                "message": message_data,
                "response_data": response_data,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        return response_data

    async def _generate_agent_response(
        self,
        session_id: int,
        customer_message: TestMessage,
        conversation_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate agent response using AI"""
        
        # This would integrate with your CrewAI agents
        # For now, returning mock response
        
        start_time = datetime.utcnow()
        
        # Mock agent response generation
        await asyncio.sleep(1)  # Simulate processing time
        
        response_time = (datetime.utcnow() - start_time).total_seconds()
        
        agent_response = {
            "content": f"شكراً لك على رسالتك. كيف يمكنني مساعدتك اليوم؟",
            "language": "arabic",
            "response_time_seconds": response_time,
            "confidence_score": 0.95,
            "persona_consistency": 0.92,
            "cultural_sensitivity": 0.98
        }
        
        # Add to conversation
        agent_message = TestMessage(
            message_id=str(uuid.uuid4()),
            sender="agent",
            content=agent_response["content"],
            timestamp=datetime.utcnow(),
            language=agent_response["language"],
            response_time_seconds=agent_response["response_time_seconds"],
            metadata=agent_response
        )
        
        conversation_state["messages"].append(agent_message.dict())
        
        return agent_response

    async def _analyze_agent_response(
        self,
        session_id: int,
        agent_message: TestMessage,
        conversation_state: Dict[str, Any]
    ) -> ConversationAnalysis:
        """Analyze agent response for quality metrics"""
        
        # Mock analysis - replace with actual AI analysis
        analysis = ConversationAnalysis(
            sentiment_scores={
                "positive": 0.8,
                "neutral": 0.15,
                "negative": 0.05
            },
            response_times=[2.3, 1.8, 2.1],  # Mock response times
            persona_consistency_score=0.92,
            cultural_sensitivity_score=0.96,
            language_appropriateness_score=0.94,
            overall_score=0.91
        )
        
        # Store performance metrics
        await self.performance_monitor.record_metrics(
            session_id=session_id,
            metrics={
                "response_time": agent_message.response_time_seconds or 0,
                "persona_consistency": analysis.persona_consistency_score,
                "cultural_sensitivity": analysis.cultural_sensitivity_score,
                "overall_score": analysis.overall_score
            }
        )
        
        return analysis

    async def _generate_customer_response(
        self,
        session_id: int,
        agent_message: TestMessage,
        conversation_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate customer response using customer simulator"""
        
        customer_simulator = conversation_state["customer_simulator"]
        if not customer_simulator:
            return {}
        
        # Generate customer response
        customer_response = await customer_simulator.generate_response(
            agent_message.content,
            conversation_context=conversation_state["messages"]
        )
        
        # Add to conversation
        customer_message = TestMessage(
            message_id=str(uuid.uuid4()),
            sender="customer",
            content=customer_response["content"],
            timestamp=datetime.utcnow(),
            language=customer_response.get("language", "arabic"),
            sentiment=customer_response.get("sentiment", "neutral"),
            metadata=customer_response
        )
        
        conversation_state["messages"].append(customer_message.dict())
        
        return customer_response

    async def _update_conversation_in_db(
        self,
        conversation_id: int,
        conversation_state: Dict[str, Any],
        db: Session
    ):
        """Update conversation in database"""
        
        conversation = db.query(TestConversation).filter(
            TestConversation.id == conversation_id
        ).first()
        
        if conversation:
            conversation.conversation_messages = conversation_state["messages"]
            
            # Calculate metrics
            agent_messages = [m for m in conversation_state["messages"] if m.get("sender") == "agent"]
            if agent_messages:
                response_times = [m.get("response_time_seconds", 0) for m in agent_messages]
                conversation.response_times = response_times
                
                # Mock overall scores
                conversation.persona_consistency_score = 0.92
                conversation.cultural_sensitivity_score = 0.96
                conversation.overall_score = 0.91
            
            db.commit()

    async def get_session(self, session_id: int, db: Session) -> TestSessionResponse:
        """Get test session details"""
        
        session = db.query(TestSession).filter(TestSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Test session not found")
        
        return TestSessionResponse.from_orm(session)

    async def get_conversations(
        self, 
        session_id: int, 
        db: Session
    ) -> List[TestConversationResponse]:
        """Get all conversations for a session"""
        
        conversations = db.query(TestConversation).filter(
            TestConversation.session_id == session_id
        ).order_by(desc(TestConversation.created_at)).all()
        
        return [TestConversationResponse.from_orm(conv) for conv in conversations]

    async def end_session(
        self,
        session_id: int,
        db: Session
    ) -> TestSessionResponse:
        """End a test session and generate final report"""
        
        session = db.query(TestSession).filter(TestSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Test session not found")
        
        # Update session
        session.status = "completed"
        session.end_time = datetime.utcnow()
        
        # Calculate final metrics
        conversations = db.query(TestConversation).filter(
            TestConversation.session_id == session_id
        ).all()
        
        total_interactions = sum(len(conv.conversation_messages or []) for conv in conversations)
        avg_score = sum(conv.overall_score or 0 for conv in conversations) / max(len(conversations), 1)
        
        session.total_interactions = total_interactions
        session.success_rate = avg_score
        
        # Generate final report
        session.test_results = {
            "total_conversations": len(conversations),
            "total_interactions": total_interactions,
            "average_score": avg_score,
            "completion_time": (session.end_time - session.start_time).total_seconds()
        }
        
        db.commit()
        
        # Clean up active conversation
        if session_id in self.active_conversations:
            del self.active_conversations[session_id]
        
        # Send final update
        await manager.send_to_session(session_id, {
            "type": "session_ended",
            "data": {
                "session_id": session_id,
                "final_report": session.test_results,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        return TestSessionResponse.from_orm(session)

# Initialize API instance
playground_api = ConversationPlaygroundAPI()

# API Routes
@router.post("/sessions", response_model=TestSessionResponse)
async def create_test_session(
    session_data: TestSessionCreate,
    db: Session = Depends(get_db)
):
    """Create a new test conversation session"""
    return await playground_api.create_test_session(session_data, db)

@router.get("/sessions/{session_id}", response_model=TestSessionResponse)
async def get_test_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Get test session details"""
    return await playground_api.get_session(session_id, db)

@router.patch("/sessions/{session_id}", response_model=TestSessionResponse)
async def update_test_session(
    session_id: int,
    update_data: TestSessionUpdate,
    db: Session = Depends(get_db)
):
    """Update test session"""
    session = db.query(TestSession).filter(TestSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Test session not found")
    
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(session, field, value)
    
    db.commit()
    db.refresh(session)
    
    return TestSessionResponse.from_orm(session)

@router.post("/sessions/{session_id}/conversations", response_model=TestConversationResponse)
async def start_conversation(
    session_id: int,
    conversation_data: TestConversationCreate,
    db: Session = Depends(get_db)
):
    """Start a new conversation within a test session"""
    return await playground_api.start_conversation(session_id, conversation_data, db)

@router.get("/sessions/{session_id}/conversations", response_model=List[TestConversationResponse])
async def get_conversations(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Get all conversations for a session"""
    return await playground_api.get_conversations(session_id, db)

@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: int,
    message: TestMessage,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Send a message in the conversation"""
    return await playground_api.send_message(session_id, message, db)

@router.post("/sessions/{session_id}/end", response_model=TestSessionResponse)
async def end_test_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    """End a test session"""
    return await playground_api.end_session(session_id, db)

# WebSocket endpoint
@router.websocket("/sessions/{session_id}/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: int):
    """WebSocket connection for real-time testing updates"""
    
    connection_id = await manager.connect(websocket, session_id)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle different message types
            if message_data["type"] == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong", 
                    "timestamp": datetime.utcnow().isoformat()
                }))
            
            elif message_data["type"] == "get_status":
                # Send current session status
                await websocket.send_text(json.dumps({
                    "type": "status_update",
                    "data": {
                        "session_id": session_id,
                        "connection_id": connection_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }))
                
    except WebSocketDisconnect:
        manager.disconnect(connection_id, session_id)