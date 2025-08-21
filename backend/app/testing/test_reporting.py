"""
Test Reporting and Analytics
===========================

Comprehensive reporting system for agent testing results with export capabilities,
analytics, and insights generation.
"""

import json
import csv
import io
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

from ..core.logging import get_logger
from .models import TestSession, TestConversation, ABTest, PerformanceMetric, TestAlert
from .schemas import TestSessionResponse

logger = get_logger(__name__)

@dataclass
class TestingMetrics:
    """Container for testing analytics metrics"""
    total_sessions: int
    active_sessions: int
    completed_sessions: int
    average_success_rate: float
    total_conversations: int
    total_interactions: int
    average_response_time: float
    top_performing_personas: List[Dict[str, Any]]
    common_issues: List[Dict[str, Any]]
    performance_trends: List[Dict[str, Any]]

@dataclass
class SessionReport:
    """Comprehensive session report data"""
    session_info: Dict[str, Any]
    performance_summary: Dict[str, Any]
    conversation_analysis: Dict[str, Any]
    ab_test_results: List[Dict[str, Any]]
    alerts_summary: Dict[str, Any]
    recommendations: List[str]
    raw_data: Dict[str, Any]

class TestReportGenerator:
    """
    Advanced reporting system for agent testing with:
    - Session-level detailed reports
    - Cross-session analytics
    - Performance trending
    - Export to multiple formats (JSON, CSV, PDF)
    - Automated insights and recommendations
    """
    
    def __init__(self):
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
    
    async def generate_session_report(
        self,
        db: Session,
        session_id: int,
        user_id: str,
        include_details: bool = True
    ) -> SessionReport:
        """Generate comprehensive report for a single test session"""
        
        try:
            # Get session data
            session = db.query(TestSession).filter(
                and_(
                    TestSession.id == session_id,
                    TestSession.user_id == user_id
                )
            ).first()
            
            if not session:
                raise ValueError(f"Test session {session_id} not found for user {user_id}")
            
            # Get related data
            conversations = db.query(TestConversation).filter(
                TestConversation.session_id == session_id
            ).all()
            
            ab_tests = db.query(ABTest).filter(
                ABTest.session_id == session_id
            ).all()
            
            performance_metrics = db.query(PerformanceMetric).filter(
                PerformanceMetric.test_session_id == session_id
            ).all()
            
            alerts = db.query(TestAlert).filter(
                TestAlert.test_session_id == session_id
            ).all()
            
            # Generate session info
            session_info = {
                "session_id": session.id,
                "session_name": session.session_name,
                "session_type": session.session_type.value if session.session_type else None,
                "status": session.status.value if session.status else None,
                "start_time": session.start_time.isoformat() if session.start_time else None,
                "end_time": session.end_time.isoformat() if session.end_time else None,
                "duration_minutes": self._calculate_session_duration(session),
                "agent_persona_id": session.agent_persona_id,
                "customer_profile_config": session.customer_profile_config
            }
            
            # Generate performance summary
            performance_summary = await self._analyze_session_performance(
                session, conversations, performance_metrics
            )
            
            # Generate conversation analysis
            conversation_analysis = await self._analyze_conversations(conversations, include_details)
            
            # Generate A/B test results
            ab_test_results = await self._analyze_ab_tests(ab_tests)
            
            # Generate alerts summary
            alerts_summary = await self._analyze_alerts(alerts)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(
                session, conversations, ab_tests, alerts, performance_metrics
            )
            
            # Compile raw data if requested
            raw_data = {}
            if include_details:
                raw_data = {
                    "conversations": [self._conversation_to_dict(c) for c in conversations],
                    "ab_tests": [self._ab_test_to_dict(t) for t in ab_tests],
                    "performance_metrics": [self._metric_to_dict(m) for m in performance_metrics],
                    "alerts": [self._alert_to_dict(a) for a in alerts]
                }
            
            return SessionReport(
                session_info=session_info,
                performance_summary=performance_summary,
                conversation_analysis=conversation_analysis,
                ab_test_results=ab_test_results,
                alerts_summary=alerts_summary,
                recommendations=recommendations,
                raw_data=raw_data
            )
            
        except Exception as e:
            logger.error(f"Error generating session report: {str(e)}")
            raise
    
    async def get_testing_summary(
        self,
        db: Session,
        user_id: str,
        days: int = 30
    ) -> TestingMetrics:
        """Generate testing activity summary for dashboard"""
        
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Basic session statistics
            total_sessions = db.query(func.count(TestSession.id)).filter(
                and_(
                    TestSession.user_id == user_id,
                    TestSession.created_at >= start_date
                )
            ).scalar() or 0
            
            active_sessions = db.query(func.count(TestSession.id)).filter(
                and_(
                    TestSession.user_id == user_id,
                    TestSession.status == 'active'
                )
            ).scalar() or 0
            
            completed_sessions = db.query(func.count(TestSession.id)).filter(
                and_(
                    TestSession.user_id == user_id,
                    TestSession.status == 'completed',
                    TestSession.created_at >= start_date
                )
            ).scalar() or 0
            
            # Average success rate
            avg_success_rate = db.query(func.avg(TestSession.success_rate)).filter(
                and_(
                    TestSession.user_id == user_id,
                    TestSession.status == 'completed',
                    TestSession.created_at >= start_date
                )
            ).scalar() or 0.0
            
            # Conversation statistics
            total_conversations = db.query(func.count(TestConversation.id)).join(
                TestSession
            ).filter(
                and_(
                    TestSession.user_id == user_id,
                    TestSession.created_at >= start_date
                )
            ).scalar() or 0
            
            # Total interactions (sum of all messages across conversations)
            conversations_with_messages = db.query(TestConversation).join(
                TestSession
            ).filter(
                and_(
                    TestSession.user_id == user_id,
                    TestSession.created_at >= start_date
                )
            ).all()
            
            total_interactions = sum(
                len(conv.conversation_messages or []) for conv in conversations_with_messages
            )
            
            # Average response time
            response_times = []
            for conv in conversations_with_messages:
                if conv.response_times:
                    response_times.extend(conv.response_times)
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
            
            # Top performing personas
            top_personas = await self._get_top_performing_personas(db, user_id, start_date)
            
            # Common issues
            common_issues = await self._get_common_issues(db, user_id, start_date)
            
            # Performance trends
            performance_trends = await self._get_performance_trends(db, user_id, days)
            
            return TestingMetrics(
                total_sessions=total_sessions,
                active_sessions=active_sessions,
                completed_sessions=completed_sessions,
                average_success_rate=float(avg_success_rate),
                total_conversations=total_conversations,
                total_interactions=total_interactions,
                average_response_time=avg_response_time,
                top_performing_personas=top_personas,
                common_issues=common_issues,
                performance_trends=performance_trends
            )
            
        except Exception as e:
            logger.error(f"Error generating testing summary: {str(e)}")
            raise
    
    async def export_to_csv(self, report_data: Dict[str, Any]) -> str:
        """Export report data to CSV format"""
        
        try:
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Session information
            writer.writerow(["Session Report"])
            writer.writerow(["Generated:", datetime.utcnow().isoformat()])
            writer.writerow([])
            
            # Session info
            if "session_info" in report_data:
                writer.writerow(["Session Information"])
                for key, value in report_data["session_info"].items():
                    writer.writerow([key.replace("_", " ").title(), value])
                writer.writerow([])
            
            # Performance summary
            if "performance_summary" in report_data:
                writer.writerow(["Performance Summary"])
                for key, value in report_data["performance_summary"].items():
                    writer.writerow([key.replace("_", " ").title(), value])
                writer.writerow([])
            
            # Conversation analysis
            if "conversation_analysis" in report_data:
                writer.writerow(["Conversation Analysis"])
                for key, value in report_data["conversation_analysis"].items():
                    if isinstance(value, (list, dict)):
                        writer.writerow([key.replace("_", " ").title(), json.dumps(value)])
                    else:
                        writer.writerow([key.replace("_", " ").title(), value])
                writer.writerow([])
            
            # A/B test results
            if "ab_test_results" in report_data and report_data["ab_test_results"]:
                writer.writerow(["A/B Test Results"])
                writer.writerow(["Test Name", "Status", "Winner", "Statistical Significance"])
                for test in report_data["ab_test_results"]:
                    writer.writerow([
                        test.get("test_name", ""),
                        test.get("status", ""),
                        test.get("winner_variant", ""),
                        test.get("statistical_significance", "")
                    ])
                writer.writerow([])
            
            # Recommendations
            if "recommendations" in report_data and report_data["recommendations"]:
                writer.writerow(["Recommendations"])
                for i, rec in enumerate(report_data["recommendations"], 1):
                    writer.writerow([f"Recommendation {i}", rec])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            raise
    
    async def export_to_pdf(self, report_data: Dict[str, Any], session_id: int) -> str:
        """Export report data to PDF format"""
        
        try:
            filename = f"test_report_session_{session_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = self.reports_dir / filename
            
            # Create PDF document
            doc = SimpleDocTemplate(str(filepath), pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                textColor=colors.darkblue
            )
            story.append(Paragraph("Agent Testing Session Report", title_style))
            story.append(Spacer(1, 12))
            
            # Session info
            if "session_info" in report_data:
                story.append(Paragraph("Session Information", styles['Heading2']))
                
                session_data = []
                for key, value in report_data["session_info"].items():
                    session_data.append([key.replace("_", " ").title(), str(value)])
                
                session_table = Table(session_data, colWidths=[2*inch, 3*inch])
                session_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(session_table)
                story.append(Spacer(1, 20))
            
            # Performance summary
            if "performance_summary" in report_data:
                story.append(Paragraph("Performance Summary", styles['Heading2']))
                
                perf_data = []
                for key, value in report_data["performance_summary"].items():
                    if isinstance(value, float):
                        value = f"{value:.2f}"
                    perf_data.append([key.replace("_", " ").title(), str(value)])
                
                perf_table = Table(perf_data, colWidths=[2*inch, 3*inch])
                perf_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(perf_table)
                story.append(Spacer(1, 20))
            
            # A/B test results
            if "ab_test_results" in report_data and report_data["ab_test_results"]:
                story.append(Paragraph("A/B Test Results", styles['Heading2']))
                
                ab_headers = ["Test Name", "Status", "Winner", "Significance"]
                ab_data = [ab_headers]
                
                for test in report_data["ab_test_results"]:
                    ab_data.append([
                        test.get("test_name", "")[:20],  # Truncate long names
                        test.get("status", ""),
                        test.get("winner_variant", ""),
                        "Yes" if test.get("statistical_significance") else "No"
                    ])
                
                ab_table = Table(ab_data, colWidths=[1.5*inch, 1*inch, 1.5*inch, 1*inch])
                ab_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(ab_table)
                story.append(Spacer(1, 20))
            
            # Recommendations
            if "recommendations" in report_data and report_data["recommendations"]:
                story.append(Paragraph("Recommendations", styles['Heading2']))
                
                for i, rec in enumerate(report_data["recommendations"], 1):
                    story.append(Paragraph(f"{i}. {rec}", styles['Normal']))
                    story.append(Spacer(1, 6))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"PDF report generated: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error exporting to PDF: {str(e)}")
            raise
    
    def _calculate_session_duration(self, session: TestSession) -> Optional[float]:
        """Calculate session duration in minutes"""
        
        if session.start_time and session.end_time:
            duration = session.end_time - session.start_time
            return duration.total_seconds() / 60
        return None
    
    async def _analyze_session_performance(
        self,
        session: TestSession,
        conversations: List[TestConversation],
        performance_metrics: List[PerformanceMetric]
    ) -> Dict[str, Any]:
        """Analyze overall session performance"""
        
        metrics = {
            "total_conversations": len(conversations),
            "total_interactions": session.total_interactions or 0,
            "overall_success_rate": session.success_rate or 0.0,
            "session_status": session.status.value if session.status else "unknown"
        }
        
        if conversations:
            # Calculate conversation-level metrics
            sentiment_scores = []
            persona_scores = []
            cultural_scores = []
            response_times = []
            
            for conv in conversations:
                if conv.overall_score:
                    sentiment_scores.append(conv.overall_score)
                if conv.persona_consistency_score:
                    persona_scores.append(conv.persona_consistency_score)
                if conv.cultural_sensitivity_score:
                    cultural_scores.append(conv.cultural_sensitivity_score)
                if conv.response_times:
                    response_times.extend(conv.response_times)
            
            metrics.update({
                "average_sentiment_score": sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0,
                "average_persona_consistency": sum(persona_scores) / len(persona_scores) if persona_scores else 0,
                "average_cultural_sensitivity": sum(cultural_scores) / len(cultural_scores) if cultural_scores else 0,
                "average_response_time": sum(response_times) / len(response_times) if response_times else 0
            })
        
        # Add performance metrics analysis
        if performance_metrics:
            metrics_by_category = {}
            for metric in performance_metrics:
                category = metric.metric_category
                if category not in metrics_by_category:
                    metrics_by_category[category] = []
                metrics_by_category[category].append(metric.value)
            
            for category, values in metrics_by_category.items():
                metrics[f"avg_{category}"] = sum(values) / len(values)
        
        return metrics
    
    async def _analyze_conversations(
        self,
        conversations: List[TestConversation],
        include_details: bool = False
    ) -> Dict[str, Any]:
        """Analyze conversation patterns and quality"""
        
        if not conversations:
            return {"total_conversations": 0}
        
        analysis = {
            "total_conversations": len(conversations),
            "conversation_types": {},
            "average_message_count": 0,
            "language_distribution": {},
            "sentiment_distribution": {}
        }
        
        total_messages = 0
        language_counts = {}
        sentiment_counts = {}
        
        for conv in conversations:
            # Count messages
            if conv.conversation_messages:
                message_count = len(conv.conversation_messages)
                total_messages += message_count
                
                # Analyze messages if details requested
                if include_details:
                    for msg in conv.conversation_messages:
                        if isinstance(msg, dict):
                            # Language analysis
                            lang = msg.get("language", "unknown")
                            language_counts[lang] = language_counts.get(lang, 0) + 1
                            
                            # Sentiment analysis
                            sentiment = msg.get("sentiment", "unknown")
                            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
            
            # Conversation type analysis
            conv_type = conv.customer_profile_type
            if conv_type:
                type_name = conv_type.value if hasattr(conv_type, 'value') else str(conv_type)
                analysis["conversation_types"][type_name] = analysis["conversation_types"].get(type_name, 0) + 1
        
        analysis["average_message_count"] = total_messages / len(conversations)
        analysis["language_distribution"] = language_counts
        analysis["sentiment_distribution"] = sentiment_counts
        
        return analysis
    
    async def _analyze_ab_tests(self, ab_tests: List[ABTest]) -> List[Dict[str, Any]]:
        """Analyze A/B test results"""
        
        results = []
        
        for test in ab_tests:
            test_result = {
                "test_name": test.test_name,
                "test_description": test.test_description,
                "status": "completed" if test.end_date else "active",
                "start_date": test.start_date.isoformat() if test.start_date else None,
                "end_date": test.end_date.isoformat() if test.end_date else None,
                "is_active": test.is_active,
                "winner_variant": test.winner_variant,
                "confidence_level": test.confidence_level,
                "statistical_significance": test.statistical_analysis is not None
            }
            
            # Add variant results if available
            if test.variant_results:
                test_result["variant_results"] = test.variant_results
            
            # Add statistical analysis if available
            if test.statistical_analysis:
                test_result["statistical_analysis"] = test.statistical_analysis
            
            results.append(test_result)
        
        return results
    
    async def _analyze_alerts(self, alerts: List[TestAlert]) -> Dict[str, Any]:
        """Analyze performance alerts"""
        
        if not alerts:
            return {"total_alerts": 0}
        
        alert_summary = {
            "total_alerts": len(alerts),
            "alerts_by_severity": {},
            "alerts_by_type": {},
            "unacknowledged_alerts": 0
        }
        
        for alert in alerts:
            # Severity analysis
            severity = alert.severity
            alert_summary["alerts_by_severity"][severity] = alert_summary["alerts_by_severity"].get(severity, 0) + 1
            
            # Type analysis
            alert_type = alert.alert_type
            alert_summary["alerts_by_type"][alert_type] = alert_summary["alerts_by_type"].get(alert_type, 0) + 1
            
            # Acknowledgment status
            if not alert.is_acknowledged:
                alert_summary["unacknowledged_alerts"] += 1
        
        return alert_summary
    
    async def _generate_recommendations(
        self,
        session: TestSession,
        conversations: List[TestConversation],
        ab_tests: List[ABTest],
        alerts: List[TestAlert],
        performance_metrics: List[PerformanceMetric]
    ) -> List[str]:
        """Generate actionable recommendations based on test results"""
        
        recommendations = []
        
        # Success rate recommendations
        if session.success_rate is not None:
            if session.success_rate < 0.7:
                recommendations.append(
                    f"Session success rate ({session.success_rate:.1%}) is below optimal. "
                    "Consider reviewing agent persona configuration and conversation flows."
                )
            elif session.success_rate > 0.9:
                recommendations.append(
                    "Excellent performance! Consider using this configuration as a baseline for future tests."
                )
        
        # Conversation analysis recommendations
        if conversations:
            avg_messages = sum(len(c.conversation_messages or []) for c in conversations) / len(conversations)
            
            if avg_messages < 3:
                recommendations.append(
                    "Conversations are quite short. Consider enhancing engagement strategies to encourage longer interactions."
                )
            elif avg_messages > 15:
                recommendations.append(
                    "Conversations are lengthy. Review if the agent can resolve issues more efficiently."
                )
            
            # Response time recommendations
            response_times = []
            for conv in conversations:
                if conv.response_times:
                    response_times.extend(conv.response_times)
            
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                if avg_response_time > 10:  # seconds
                    recommendations.append(
                        f"Average response time ({avg_response_time:.1f}s) is high. "
                        "Consider optimizing AI model selection or prompt engineering."
                    )
        
        # A/B test recommendations
        for test in ab_tests:
            if test.winner_variant and test.statistical_analysis:
                recommendations.append(
                    f"A/B test '{test.test_name}' shows {test.winner_variant} performing better. "
                    "Consider implementing the winning variant in production."
                )
        
        # Alert-based recommendations
        critical_alerts = [a for a in alerts if a.severity == "critical"]
        if critical_alerts:
            recommendations.append(
                f"Found {len(critical_alerts)} critical alerts. "
                "Immediate attention required to address performance issues."
            )
        
        # Performance metric recommendations
        if performance_metrics:
            accuracy_metrics = [m for m in performance_metrics if "accuracy" in m.metric_name.lower()]
            if accuracy_metrics:
                avg_accuracy = sum(m.value for m in accuracy_metrics) / len(accuracy_metrics)
                if avg_accuracy < 0.8:
                    recommendations.append(
                        f"Agent accuracy ({avg_accuracy:.1%}) needs improvement. "
                        "Consider additional training data or prompt refinement."
                    )
        
        # General recommendations if no specific issues found
        if not recommendations:
            recommendations.append(
                "Test session completed successfully with good performance metrics. "
                "Continue monitoring and consider scaling to production environment."
            )
        
        return recommendations
    
    async def _get_top_performing_personas(
        self,
        db: Session,
        user_id: str,
        start_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get top performing agent personas"""
        
        try:
            # Query sessions grouped by persona
            persona_performance = db.query(
                TestSession.agent_persona_id,
                func.avg(TestSession.success_rate).label('avg_success_rate'),
                func.count(TestSession.id).label('test_count')
            ).filter(
                and_(
                    TestSession.user_id == user_id,
                    TestSession.created_at >= start_date,
                    TestSession.agent_persona_id.isnot(None),
                    TestSession.success_rate.isnot(None)
                )
            ).group_by(TestSession.agent_persona_id).order_by(
                desc('avg_success_rate')
            ).limit(5).all()
            
            return [
                {
                    "persona_id": persona_id,
                    "average_success_rate": float(avg_rate),
                    "test_count": test_count
                }
                for persona_id, avg_rate, test_count in persona_performance
            ]
            
        except Exception as e:
            logger.error(f"Error getting top performing personas: {str(e)}")
            return []
    
    async def _get_common_issues(
        self,
        db: Session,
        user_id: str,
        start_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get most common issues from alerts"""
        
        try:
            # Query alerts grouped by type
            issue_counts = db.query(
                TestAlert.alert_type,
                func.count(TestAlert.id).label('count')
            ).join(TestSession).filter(
                and_(
                    TestSession.user_id == user_id,
                    TestSession.created_at >= start_date
                )
            ).group_by(TestAlert.alert_type).order_by(
                desc('count')
            ).limit(5).all()
            
            return [
                {
                    "issue_type": issue_type,
                    "occurrence_count": count
                }
                for issue_type, count in issue_counts
            ]
            
        except Exception as e:
            logger.error(f"Error getting common issues: {str(e)}")
            return []
    
    async def _get_performance_trends(
        self,
        db: Session,
        user_id: str,
        days: int
    ) -> List[Dict[str, Any]]:
        """Get performance trends over time"""
        
        try:
            # Get daily performance averages
            daily_performance = db.query(
                func.date(TestSession.created_at).label('test_date'),
                func.avg(TestSession.success_rate).label('avg_success_rate'),
                func.count(TestSession.id).label('session_count')
            ).filter(
                and_(
                    TestSession.user_id == user_id,
                    TestSession.created_at >= datetime.utcnow() - timedelta(days=days),
                    TestSession.success_rate.isnot(None)
                )
            ).group_by(func.date(TestSession.created_at)).order_by('test_date').all()
            
            return [
                {
                    "date": test_date.isoformat(),
                    "average_success_rate": float(avg_rate),
                    "session_count": session_count
                }
                for test_date, avg_rate, session_count in daily_performance
            ]
            
        except Exception as e:
            logger.error(f"Error getting performance trends: {str(e)}")
            return []
    
    def _conversation_to_dict(self, conv: TestConversation) -> Dict[str, Any]:
        """Convert conversation to dictionary"""
        
        return {
            "id": conv.id,
            "conversation_name": conv.conversation_name,
            "customer_profile_type": conv.customer_profile_type.value if conv.customer_profile_type else None,
            "conversation_messages": conv.conversation_messages,
            "sentiment_analysis": conv.sentiment_analysis,
            "persona_consistency_score": conv.persona_consistency_score,
            "cultural_sensitivity_score": conv.cultural_sensitivity_score,
            "overall_score": conv.overall_score
        }
    
    def _ab_test_to_dict(self, test: ABTest) -> Dict[str, Any]:
        """Convert A/B test to dictionary"""
        
        return {
            "id": test.id,
            "test_name": test.test_name,
            "test_description": test.test_description,
            "variants": test.variants,
            "variant_results": test.variant_results,
            "statistical_analysis": test.statistical_analysis,
            "winner_variant": test.winner_variant,
            "is_active": test.is_active
        }
    
    def _metric_to_dict(self, metric: PerformanceMetric) -> Dict[str, Any]:
        """Convert performance metric to dictionary"""
        
        return {
            "id": metric.id,
            "metric_name": metric.metric_name,
            "metric_category": metric.metric_category,
            "value": metric.value,
            "measurement_time": metric.measurement_time.isoformat() if metric.measurement_time else None
        }
    
    def _alert_to_dict(self, alert: TestAlert) -> Dict[str, Any]:
        """Convert alert to dictionary"""
        
        return {
            "id": alert.id,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "title": alert.title,
            "message": alert.message,
            "is_acknowledged": alert.is_acknowledged
        }

# Global test reporting instance
test_reporting = TestReportGenerator()