"""
Test Session Manager
===================

Manages test sessions, their lifecycle, and data persistence.
Handles creation, updating, retrieval, and deletion of test sessions.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import desc, and_, or_, func
import uuid

from .models import TestSession, TestConversation, ABTest, TestScenario
from .schemas import (
    TestSessionCreate, TestSessionResponse, TestSessionUpdate,
    TestSessionStatus, TestScenarioType
)

class SessionManager:
    """Manages test session lifecycle and operations"""
    
    def __init__(self):
        self.active_sessions: Dict[int, Dict[str, Any]] = {}
    
    async def create_session(
        self,
        db: Session,
        user_id: str,
        session_data: TestSessionCreate
    ) -> TestSessionResponse:
        """Create a new test session"""
        
        # Validate session data
        self._validate_session_data(session_data)
        
        # Create database record
        db_session = TestSession(
            session_name=session_data.session_name,
            session_type=session_data.session_type,
            status=TestSessionStatus.ACTIVE,
            agent_persona_id=session_data.agent_persona_id,
            customer_profile_config=session_data.customer_profile_config or {},
            test_parameters=session_data.test_parameters or {},
            start_time=datetime.utcnow(),
            total_interactions=0,
            success_rate=0.0,
            user_id=user_id  # Assuming TestSession model has user_id
        )
        
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        
        # Initialize in-memory session tracking
        self.active_sessions[db_session.id] = {
            "user_id": user_id,
            "start_time": datetime.utcnow(),
            "activity_log": [],
            "real_time_metrics": {},
            "alerts": []
        }
        
        return TestSessionResponse.from_orm(db_session)
    
    async def get_session_by_id(
        self,
        db: Session,
        session_id: int,
        user_id: str
    ) -> Optional[TestSessionResponse]:
        """Get a specific test session"""
        
        session = db.query(TestSession).filter(
            and_(
                TestSession.id == session_id,
                TestSession.user_id == user_id
            )
        ).first()
        
        if not session:
            return None
        
        # Include related data
        session = db.query(TestSession).options(
            selectinload(TestSession.conversations),
            selectinload(TestSession.ab_tests)
        ).filter(TestSession.id == session_id).first()
        
        return TestSessionResponse.from_orm(session) if session else None
    
    async def get_user_sessions(
        self,
        db: Session,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
        session_type: Optional[str] = None,
        status_filter: Optional[TestSessionStatus] = None
    ) -> List[TestSessionResponse]:
        """Get all sessions for a user with filtering"""
        
        query = db.query(TestSession).filter(TestSession.user_id == user_id)
        
        # Apply filters
        if session_type:
            try:
                session_type_enum = TestScenarioType(session_type)
                query = query.filter(TestSession.session_type == session_type_enum)
            except ValueError:
                pass  # Invalid session type, ignore filter
        
        if status_filter:
            query = query.filter(TestSession.status == status_filter)
        
        # Order by most recent first
        query = query.order_by(desc(TestSession.created_at))
        
        # Apply pagination
        sessions = query.offset(skip).limit(limit).all()
        
        return [TestSessionResponse.from_orm(session) for session in sessions]
    
    async def update_session(
        self,
        db: Session,
        session_id: int,
        user_id: str,
        session_update: TestSessionUpdate
    ) -> Optional[TestSessionResponse]:
        """Update a test session"""
        
        session = db.query(TestSession).filter(
            and_(
                TestSession.id == session_id,
                TestSession.user_id == user_id
            )
        ).first()
        
        if not session:
            return None
        
        # Update fields
        update_data = session_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(session, field):
                setattr(session, field, value)
        
        # Update modified time
        session.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(session)
        
        # Update in-memory tracking
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["activity_log"].append({
                "action": "session_updated",
                "timestamp": datetime.utcnow(),
                "changes": update_data
            })
        
        return TestSessionResponse.from_orm(session)
    
    async def delete_session(
        self,
        db: Session,
        session_id: int,
        user_id: str
    ) -> bool:
        """Delete a test session and all related data"""
        
        session = db.query(TestSession).filter(
            and_(
                TestSession.id == session_id,
                TestSession.user_id == user_id
            )
        ).first()
        
        if not session:
            return False
        
        # Delete related conversations
        db.query(TestConversation).filter(
            TestConversation.session_id == session_id
        ).delete()
        
        # Delete related A/B tests
        db.query(ABTest).filter(
            ABTest.session_id == session_id
        ).delete()
        
        # Delete the session itself
        db.delete(session)
        db.commit()
        
        # Clean up in-memory tracking
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        return True
    
    async def pause_session(
        self,
        db: Session,
        session_id: int,
        user_id: str
    ) -> Optional[TestSessionResponse]:
        """Pause an active test session"""
        
        update = TestSessionUpdate(status=TestSessionStatus.PAUSED)
        return await self.update_session(db, session_id, user_id, update)
    
    async def resume_session(
        self,
        db: Session,
        session_id: int,
        user_id: str
    ) -> Optional[TestSessionResponse]:
        """Resume a paused test session"""
        
        update = TestSessionUpdate(status=TestSessionStatus.ACTIVE)
        return await self.update_session(db, session_id, user_id, update)
    
    async def complete_session(
        self,
        db: Session,
        session_id: int,
        user_id: str,
        final_results: Optional[Dict[str, Any]] = None
    ) -> Optional[TestSessionResponse]:
        """Complete a test session with final results"""
        
        session = db.query(TestSession).filter(
            and_(
                TestSession.id == session_id,
                TestSession.user_id == user_id
            )
        ).first()
        
        if not session:
            return None
        
        # Calculate final metrics
        final_metrics = await self._calculate_final_metrics(db, session)
        
        # Update session
        session.status = TestSessionStatus.COMPLETED
        session.end_time = datetime.utcnow()
        session.test_results = final_results or {}
        session.performance_metrics = final_metrics
        session.success_rate = final_metrics.get("overall_success_rate", 0.0)
        
        db.commit()
        db.refresh(session)
        
        # Clean up active session tracking
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        return TestSessionResponse.from_orm(session)
    
    async def get_session_summary(
        self,
        db: Session,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get summary of testing activity for a user"""
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Query session statistics
        total_sessions = db.query(func.count(TestSession.id)).filter(
            and_(
                TestSession.user_id == user_id,
                TestSession.created_at >= start_date
            )
        ).scalar()
        
        completed_sessions = db.query(func.count(TestSession.id)).filter(
            and_(
                TestSession.user_id == user_id,
                TestSession.status == TestSessionStatus.COMPLETED,
                TestSession.created_at >= start_date
            )
        ).scalar()
        
        active_sessions = db.query(func.count(TestSession.id)).filter(
            and_(
                TestSession.user_id == user_id,
                TestSession.status == TestSessionStatus.ACTIVE
            )
        ).scalar()
        
        # Query conversation statistics
        total_conversations = db.query(func.count(TestConversation.id)).join(
            TestSession
        ).filter(
            and_(
                TestSession.user_id == user_id,
                TestSession.created_at >= start_date
            )
        ).scalar()
        
        # Query A/B test statistics
        total_ab_tests = db.query(func.count(ABTest.id)).join(
            TestSession
        ).filter(
            and_(
                TestSession.user_id == user_id,
                TestSession.created_at >= start_date
            )
        ).scalar()
        
        # Average success rate
        avg_success_rate = db.query(func.avg(TestSession.success_rate)).filter(
            and_(
                TestSession.user_id == user_id,
                TestSession.status == TestSessionStatus.COMPLETED,
                TestSession.created_at >= start_date
            )
        ).scalar() or 0.0
        
        return {
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "active_sessions": active_sessions,
            "total_conversations": total_conversations,
            "total_ab_tests": total_ab_tests,
            "average_success_rate": float(avg_success_rate),
            "completion_rate": (completed_sessions / max(total_sessions, 1)) * 100,
            "period_days": days,
            "summary_generated": datetime.utcnow().isoformat()
        }
    
    async def get_active_session_metrics(
        self,
        session_id: int
    ) -> Dict[str, Any]:
        """Get real-time metrics for an active session"""
        
        if session_id not in self.active_sessions:
            return {}
        
        session_data = self.active_sessions[session_id]
        
        return {
            "session_id": session_id,
            "uptime_minutes": (datetime.utcnow() - session_data["start_time"]).total_seconds() / 60,
            "activity_count": len(session_data["activity_log"]),
            "real_time_metrics": session_data["real_time_metrics"],
            "alerts_count": len(session_data["alerts"]),
            "last_activity": session_data["activity_log"][-1] if session_data["activity_log"] else None
        }
    
    def _validate_session_data(self, session_data: TestSessionCreate):
        """Validate session creation data"""
        
        if not session_data.session_name or len(session_data.session_name.strip()) == 0:
            raise HTTPException(status_code=400, detail="Session name is required")
        
        if len(session_data.session_name) > 200:
            raise HTTPException(status_code=400, detail="Session name too long (max 200 characters)")
        
        # Validate session type
        try:
            TestScenarioType(session_data.session_type)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid session type")
        
        # Validate customer profile config if provided
        if session_data.customer_profile_config:
            required_keys = ["demographics", "behavioral_traits", "visit_context"]
            if not all(key in session_data.customer_profile_config for key in required_keys):
                raise HTTPException(
                    status_code=400, 
                    detail="Customer profile config missing required keys"
                )
    
    async def _calculate_final_metrics(
        self,
        db: Session,
        session: TestSession
    ) -> Dict[str, Any]:
        """Calculate final performance metrics for a completed session"""
        
        # Get all conversations for this session
        conversations = db.query(TestConversation).filter(
            TestConversation.session_id == session.id
        ).all()
        
        # Get all A/B tests for this session
        ab_tests = db.query(ABTest).filter(
            ABTest.session_id == session.id
        ).all()
        
        metrics = {
            "session_duration_minutes": 0,
            "total_conversations": len(conversations),
            "total_ab_tests": len(ab_tests),
            "total_interactions": 0,
            "average_response_time": 0.0,
            "average_sentiment_score": 0.0,
            "persona_consistency_average": 0.0,
            "cultural_sensitivity_average": 0.0,
            "overall_success_rate": 0.0
        }
        
        if session.end_time and session.start_time:
            duration = session.end_time - session.start_time
            metrics["session_duration_minutes"] = duration.total_seconds() / 60
        
        if conversations:
            # Calculate conversation metrics
            total_messages = 0
            total_response_time = 0.0
            sentiment_scores = []
            persona_scores = []
            cultural_scores = []
            
            for conv in conversations:
                if conv.conversation_messages:
                    total_messages += len(conv.conversation_messages)
                    
                    # Calculate average response times
                    for msg in conv.conversation_messages:
                        if isinstance(msg, dict) and msg.get("response_time_seconds"):
                            total_response_time += msg["response_time_seconds"]
                
                if conv.sentiment_analysis and isinstance(conv.sentiment_analysis, dict):
                    sentiment_score = conv.sentiment_analysis.get("overall_sentiment", 0)
                    if sentiment_score:
                        sentiment_scores.append(sentiment_score)
                
                if conv.persona_consistency_score:
                    persona_scores.append(conv.persona_consistency_score)
                
                if conv.cultural_sensitivity_score:
                    cultural_scores.append(conv.cultural_sensitivity_score)
            
            metrics["total_interactions"] = total_messages
            
            if total_messages > 0:
                metrics["average_response_time"] = total_response_time / total_messages
            
            if sentiment_scores:
                metrics["average_sentiment_score"] = sum(sentiment_scores) / len(sentiment_scores)
            
            if persona_scores:
                metrics["persona_consistency_average"] = sum(persona_scores) / len(persona_scores)
            
            if cultural_scores:
                metrics["cultural_sensitivity_average"] = sum(cultural_scores) / len(cultural_scores)
            
            # Overall success rate calculation
            success_factors = []
            if persona_scores:
                success_factors.append(sum(persona_scores) / len(persona_scores))
            if cultural_scores:
                success_factors.append(sum(cultural_scores) / len(cultural_scores))
            if sentiment_scores:
                success_factors.append(sum(sentiment_scores) / len(sentiment_scores))
            
            if success_factors:
                metrics["overall_success_rate"] = sum(success_factors) / len(success_factors)
        
        return metrics

# Global session manager instance
session_manager = SessionManager()