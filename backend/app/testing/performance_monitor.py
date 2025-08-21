"""
Agent Performance Monitor
========================

Real-time performance monitoring system for AI agents with metrics tracking,
alert generation, and performance analytics.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, deque
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
import statistics

from ..database import get_db
from .models import PerformanceMetric, TestAlert, TestSession
from .schemas import (
    PerformanceMetricCreate, PerformanceMetricResponse, RealTimeMetrics,
    PerformanceAlert, TestProgressUpdate
)

router = APIRouter(prefix="/testing/performance", tags=["performance-monitor"])

class MetricsCollector:
    """Collects and aggregates performance metrics"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.metrics_windows: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self.current_metrics: Dict[str, float] = {}
        self.metric_thresholds = {
            "response_accuracy": {"min": 0.8, "max": 1.0},
            "cultural_sensitivity_score": {"min": 0.85, "max": 1.0}, 
            "persona_consistency_score": {"min": 0.8, "max": 1.0},
            "language_appropriateness": {"min": 0.9, "max": 1.0},
            "timing_optimization_score": {"min": 0.7, "max": 1.0},
            "response_time": {"min": 0.5, "max": 5.0},
            "sentiment_score": {"min": 0.6, "max": 1.0},
            "customer_satisfaction": {"min": 0.7, "max": 1.0}
        }

    def add_metric(self, metric_name: str, value: float, timestamp: datetime = None):
        """Add a metric value to the collection"""
        
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        metric_data = {
            "value": value,
            "timestamp": timestamp,
            "metadata": {}
        }
        
        self.metrics_windows[metric_name].append(metric_data)
        self.current_metrics[metric_name] = value

    def get_current_metrics(self) -> Dict[str, float]:
        """Get current metric values"""
        return self.current_metrics.copy()

    def get_metric_statistics(self, metric_name: str, minutes: int = 60) -> Dict[str, float]:
        """Get statistics for a specific metric over time window"""
        
        if metric_name not in self.metrics_windows:
            return {}
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        recent_values = [
            m["value"] for m in self.metrics_windows[metric_name]
            if m["timestamp"] >= cutoff_time
        ]
        
        if not recent_values:
            return {}
        
        return {
            "mean": statistics.mean(recent_values),
            "median": statistics.median(recent_values),
            "min": min(recent_values),
            "max": max(recent_values),
            "std_dev": statistics.stdev(recent_values) if len(recent_values) > 1 else 0.0,
            "count": len(recent_values)
        }

    def get_trend_analysis(self, metric_name: str, minutes: int = 60) -> Dict[str, Any]:
        """Analyze trends for a specific metric"""
        
        if metric_name not in self.metrics_windows:
            return {"trend": "unknown", "confidence": 0.0}
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        recent_data = [
            m for m in self.metrics_windows[metric_name]
            if m["timestamp"] >= cutoff_time
        ]
        
        if len(recent_data) < 3:
            return {"trend": "insufficient_data", "confidence": 0.0}
        
        # Simple linear trend analysis
        values = [d["value"] for d in recent_data]
        x_values = list(range(len(values)))
        
        # Calculate linear regression slope
        n = len(values)
        sum_x = sum(x_values)
        sum_y = sum(values)
        sum_xy = sum(x * y for x, y in zip(x_values, values))
        sum_x2 = sum(x * x for x in x_values)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        # Determine trend direction and confidence
        if abs(slope) < 0.001:
            trend = "stable"
            confidence = 0.8
        elif slope > 0:
            trend = "improving"
            confidence = min(0.9, abs(slope) * 100)
        else:
            trend = "declining"
            confidence = min(0.9, abs(slope) * 100)
        
        return {
            "trend": trend,
            "confidence": confidence,
            "slope": slope,
            "recent_change": values[-1] - values[0] if values else 0.0
        }

    def check_thresholds(self, metric_name: str, value: float) -> Optional[Dict[str, Any]]:
        """Check if metric value violates thresholds"""
        
        if metric_name not in self.metric_thresholds:
            return None
        
        thresholds = self.metric_thresholds[metric_name]
        
        if value < thresholds["min"]:
            return {
                "type": "threshold_violation",
                "severity": "high" if value < thresholds["min"] * 0.8 else "medium",
                "message": f"{metric_name} below minimum threshold: {value:.3f} < {thresholds['min']}",
                "threshold_type": "minimum",
                "threshold_value": thresholds["min"],
                "actual_value": value
            }
        
        if value > thresholds["max"]:
            return {
                "type": "threshold_violation", 
                "severity": "medium",
                "message": f"{metric_name} above maximum threshold: {value:.3f} > {thresholds['max']}",
                "threshold_type": "maximum",
                "threshold_value": thresholds["max"],
                "actual_value": value
            }
        
        return None

class AlertManager:
    """Manages performance alerts and notifications"""
    
    def __init__(self):
        self.active_alerts: Dict[str, Dict[str, Any]] = {}
        self.alert_history: List[Dict[str, Any]] = []
        self.alert_rules = {
            "performance_degradation": {
                "condition": "metric_trend_declining",
                "threshold": 0.7,
                "duration_minutes": 10
            },
            "cultural_insensitivity": {
                "condition": "metric_below_threshold",
                "metric": "cultural_sensitivity_score",
                "threshold": 0.8
            },
            "response_time_high": {
                "condition": "metric_above_threshold",
                "metric": "response_time",
                "threshold": 8.0
            },
            "persona_inconsistency": {
                "condition": "metric_below_threshold",
                "metric": "persona_consistency_score",
                "threshold": 0.75
            }
        }

    async def evaluate_alerts(
        self,
        metrics: Dict[str, float],
        metrics_collector: MetricsCollector,
        session_id: Optional[int] = None
    ) -> List[PerformanceAlert]:
        """Evaluate metrics against alert rules"""
        
        alerts = []
        
        for alert_type, rule in self.alert_rules.items():
            alert = await self._check_alert_rule(
                alert_type, rule, metrics, metrics_collector, session_id
            )
            if alert:
                alerts.append(alert)
        
        # Update active alerts
        for alert in alerts:
            alert_key = f"{alert.alert_type}_{session_id}"
            self.active_alerts[alert_key] = {
                "alert": alert,
                "first_triggered": datetime.utcnow(),
                "last_updated": datetime.utcnow()
            }
        
        return alerts

    async def _check_alert_rule(
        self,
        alert_type: str,
        rule: Dict[str, Any],
        metrics: Dict[str, float],
        metrics_collector: MetricsCollector,
        session_id: Optional[int]
    ) -> Optional[PerformanceAlert]:
        """Check a specific alert rule"""
        
        condition = rule["condition"]
        
        if condition == "metric_below_threshold":
            metric_name = rule["metric"]
            threshold = rule["threshold"]
            
            if metric_name in metrics and metrics[metric_name] < threshold:
                return PerformanceAlert(
                    alert_type=alert_type,
                    severity="high" if metrics[metric_name] < threshold * 0.8 else "medium",
                    title=f"{metric_name.replace('_', ' ').title()} Below Threshold",
                    message=f"{metric_name} is {metrics[metric_name]:.3f}, below threshold of {threshold}",
                    alert_data={
                        "metric_name": metric_name,
                        "current_value": metrics[metric_name],
                        "threshold": threshold,
                        "deviation": threshold - metrics[metric_name]
                    },
                    test_session_id=session_id
                )
        
        elif condition == "metric_above_threshold":
            metric_name = rule["metric"]
            threshold = rule["threshold"]
            
            if metric_name in metrics and metrics[metric_name] > threshold:
                return PerformanceAlert(
                    alert_type=alert_type,
                    severity="medium",
                    title=f"{metric_name.replace('_', ' ').title()} Above Threshold",
                    message=f"{metric_name} is {metrics[metric_name]:.3f}, above threshold of {threshold}",
                    alert_data={
                        "metric_name": metric_name,
                        "current_value": metrics[metric_name],
                        "threshold": threshold,
                        "deviation": metrics[metric_name] - threshold
                    },
                    test_session_id=session_id
                )
        
        elif condition == "metric_trend_declining":
            threshold_confidence = rule["threshold"]
            duration_minutes = rule.get("duration_minutes", 10)
            
            # Check trends for key metrics
            declining_metrics = []
            for metric_name in ["response_accuracy", "cultural_sensitivity_score", "persona_consistency_score"]:
                if metric_name in metrics:
                    trend = metrics_collector.get_trend_analysis(metric_name, duration_minutes)
                    if (trend.get("trend") == "declining" and 
                        trend.get("confidence", 0) > threshold_confidence):
                        declining_metrics.append(metric_name)
            
            if declining_metrics:
                return PerformanceAlert(
                    alert_type=alert_type,
                    severity="high" if len(declining_metrics) > 2 else "medium",
                    title="Performance Degradation Detected",
                    message=f"Declining trends detected in: {', '.join(declining_metrics)}",
                    alert_data={
                        "declining_metrics": declining_metrics,
                        "duration_minutes": duration_minutes,
                        "confidence_threshold": threshold_confidence
                    },
                    test_session_id=session_id
                )
        
        return None

    def get_active_alerts(self, session_id: Optional[int] = None) -> List[PerformanceAlert]:
        """Get currently active alerts"""
        
        alerts = []
        for key, alert_data in self.active_alerts.items():
            alert = alert_data["alert"]
            if session_id is None or alert.test_session_id == session_id:
                alerts.append(alert)
        
        return alerts

    def acknowledge_alert(self, alert_type: str, session_id: Optional[int], acknowledged_by: str):
        """Acknowledge an active alert"""
        
        alert_key = f"{alert_type}_{session_id}"
        if alert_key in self.active_alerts:
            self.active_alerts[alert_key]["acknowledged"] = True
            self.active_alerts[alert_key]["acknowledged_by"] = acknowledged_by
            self.active_alerts[alert_key]["acknowledged_at"] = datetime.utcnow()

class AgentPerformanceMonitor:
    """Main performance monitoring system"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.websocket_connections: Dict[int, List[WebSocket]] = defaultdict(list)
        self.monitoring_tasks: Dict[int, asyncio.Task] = {}

    async def start_monitoring(self, session_id: int) -> Dict[str, str]:
        """Start monitoring for a test session"""
        
        if session_id in self.monitoring_tasks:
            return {"status": "already_monitoring", "session_id": session_id}
        
        # Start monitoring task
        task = asyncio.create_task(self._monitor_session(session_id))
        self.monitoring_tasks[session_id] = task
        
        return {"status": "monitoring_started", "session_id": session_id}

    async def stop_monitoring(self, session_id: int) -> Dict[str, str]:
        """Stop monitoring for a test session"""
        
        if session_id in self.monitoring_tasks:
            self.monitoring_tasks[session_id].cancel()
            del self.monitoring_tasks[session_id]
        
        # Clean up websocket connections
        if session_id in self.websocket_connections:
            for ws in self.websocket_connections[session_id]:
                try:
                    await ws.close()
                except:
                    pass
            del self.websocket_connections[session_id]
        
        return {"status": "monitoring_stopped", "session_id": session_id}

    async def _monitor_session(self, session_id: int):
        """Monitor a specific test session"""
        
        try:
            while True:
                # Collect current metrics
                current_metrics = self.metrics_collector.get_current_metrics()
                
                # Evaluate alerts
                alerts = await self.alert_manager.evaluate_alerts(
                    current_metrics, self.metrics_collector, session_id
                )
                
                # Create real-time metrics update
                metrics_update = RealTimeMetrics(
                    response_accuracy=current_metrics.get("response_accuracy", 0.0),
                    cultural_sensitivity_score=current_metrics.get("cultural_sensitivity_score", 0.0),
                    persona_consistency_score=current_metrics.get("persona_consistency_score", 0.0),
                    language_appropriateness=current_metrics.get("language_appropriateness", 0.0),
                    timing_optimization_score=current_metrics.get("timing_optimization_score", 0.0),
                    timestamp=datetime.utcnow()
                )
                
                # Send updates to WebSocket connections
                await self._broadcast_updates(session_id, metrics_update, alerts)
                
                # Wait before next update
                await asyncio.sleep(5)  # Update every 5 seconds
                
        except asyncio.CancelledError:
            pass

    async def _broadcast_updates(
        self,
        session_id: int,
        metrics: RealTimeMetrics,
        alerts: List[PerformanceAlert]
    ):
        """Broadcast updates to WebSocket connections"""
        
        if session_id not in self.websocket_connections:
            return
        
        update_data = TestProgressUpdate(
            test_session_id=session_id,
            progress_percentage=75.0,  # Mock progress
            current_step="monitoring_performance",
            metrics_update=metrics,
            alerts=alerts
        )
        
        message = {
            "type": "performance_update",
            "data": update_data.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to all connected clients
        disconnected = []
        for ws in self.websocket_connections[session_id]:
            try:
                await ws.send_text(json.dumps(message))
            except:
                disconnected.append(ws)
        
        # Remove disconnected clients
        for ws in disconnected:
            self.websocket_connections[session_id].remove(ws)

    async def record_metrics(
        self,
        session_id: int,
        metrics: Dict[str, float],
        db: Optional[Session] = None
    ) -> List[PerformanceMetricResponse]:
        """Record performance metrics"""
        
        recorded_metrics = []
        
        for metric_name, value in metrics.items():
            # Add to collector
            self.metrics_collector.add_metric(metric_name, value)
            
            # Check thresholds
            threshold_violation = self.metrics_collector.check_thresholds(metric_name, value)
            
            # Store in database if provided
            if db:
                db_metric = PerformanceMetric(
                    metric_name=metric_name,
                    metric_category=self._categorize_metric(metric_name),
                    value=value,
                    test_session_id=session_id,
                    context_data={"threshold_violation": threshold_violation}
                )
                
                db.add(db_metric)
                recorded_metrics.append(PerformanceMetricResponse.from_orm(db_metric))
        
        if db:
            db.commit()
        
        return recorded_metrics

    def _categorize_metric(self, metric_name: str) -> str:
        """Categorize metric by name"""
        
        if "response" in metric_name or "time" in metric_name:
            return "response_time"
        elif "accuracy" in metric_name or "consistency" in metric_name:
            return "accuracy"
        elif "cultural" in metric_name or "sensitivity" in metric_name:
            return "cultural"
        elif "sentiment" in metric_name:
            return "sentiment"
        elif "language" in metric_name:
            return "language"
        else:
            return "general"

    async def get_performance_summary(
        self,
        session_id: int,
        hours: int = 24,
        db: Session = None
    ) -> Dict[str, Any]:
        """Get performance summary for a session"""
        
        summary = {
            "session_id": session_id,
            "time_window_hours": hours,
            "current_metrics": self.metrics_collector.get_current_metrics(),
            "metric_statistics": {},
            "trends": {},
            "active_alerts": self.alert_manager.get_active_alerts(session_id),
            "recommendations": []
        }
        
        # Get statistics for each metric
        for metric_name in summary["current_metrics"].keys():
            stats = self.metrics_collector.get_metric_statistics(metric_name, hours * 60)
            if stats:
                summary["metric_statistics"][metric_name] = stats
                
                # Get trend analysis
                trend = self.metrics_collector.get_trend_analysis(metric_name, hours * 60)
                summary["trends"][metric_name] = trend
        
        # Generate recommendations
        summary["recommendations"] = await self._generate_performance_recommendations(summary)
        
        return summary

    async def _generate_performance_recommendations(
        self, 
        performance_summary: Dict[str, Any]
    ) -> List[str]:
        """Generate performance improvement recommendations"""
        
        recommendations = []
        current_metrics = performance_summary.get("current_metrics", {})
        trends = performance_summary.get("trends", {})
        
        # Check individual metrics
        if current_metrics.get("response_accuracy", 1.0) < 0.8:
            recommendations.append(
                "Response accuracy is low. Consider refining agent training data and decision logic."
            )
        
        if current_metrics.get("cultural_sensitivity_score", 1.0) < 0.85:
            recommendations.append(
                "Cultural sensitivity needs improvement. Review cultural context training and guidelines."
            )
        
        if current_metrics.get("persona_consistency_score", 1.0) < 0.8:
            recommendations.append(
                "Persona consistency is inconsistent. Ensure agent maintains character throughout conversations."
            )
        
        # Check trends
        declining_metrics = [
            name for name, trend in trends.items()
            if trend.get("trend") == "declining" and trend.get("confidence", 0) > 0.6
        ]
        
        if len(declining_metrics) > 2:
            recommendations.append(
                f"Multiple metrics showing decline: {', '.join(declining_metrics)}. "
                "Consider comprehensive agent review."
            )
        
        # Check active alerts
        if len(performance_summary.get("active_alerts", [])) > 3:
            recommendations.append(
                "Multiple active alerts detected. Consider immediate agent intervention."
            )
        
        return recommendations

    async def add_websocket_connection(self, session_id: int, websocket: WebSocket):
        """Add WebSocket connection for real-time updates"""
        
        self.websocket_connections[session_id].append(websocket)

    async def remove_websocket_connection(self, session_id: int, websocket: WebSocket):
        """Remove WebSocket connection"""
        
        if session_id in self.websocket_connections:
            if websocket in self.websocket_connections[session_id]:
                self.websocket_connections[session_id].remove(websocket)

# Initialize monitor instance
performance_monitor = AgentPerformanceMonitor()

# API Routes
@router.post("/sessions/{session_id}/start")
async def start_monitoring(session_id: int):
    """Start performance monitoring for a test session"""
    return await performance_monitor.start_monitoring(session_id)

@router.post("/sessions/{session_id}/stop")
async def stop_monitoring(session_id: int):
    """Stop performance monitoring for a test session"""
    return await performance_monitor.stop_monitoring(session_id)

@router.post("/sessions/{session_id}/metrics")
async def record_metrics(
    session_id: int,
    metrics: Dict[str, float],
    db: Session = Depends(get_db)
):
    """Record performance metrics for a session"""
    
    return await performance_monitor.record_metrics(session_id, metrics, db)

@router.get("/sessions/{session_id}/summary")
async def get_performance_summary(
    session_id: int,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get performance summary for a test session"""
    
    return await performance_monitor.get_performance_summary(session_id, hours, db)

@router.get("/metrics", response_model=List[PerformanceMetricResponse])
async def get_metrics(
    session_id: Optional[int] = None,
    metric_category: Optional[str] = None,
    hours: int = 24,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get performance metrics with filtering"""
    
    query = db.query(PerformanceMetric)
    
    # Apply filters
    if session_id:
        query = query.filter(PerformanceMetric.test_session_id == session_id)
    
    if metric_category:
        query = query.filter(PerformanceMetric.metric_category == metric_category)
    
    # Time filter
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    query = query.filter(PerformanceMetric.measurement_time >= cutoff_time)
    
    metrics = query.order_by(desc(PerformanceMetric.measurement_time)).offset(offset).limit(limit).all()
    
    return [PerformanceMetricResponse.from_orm(metric) for metric in metrics]

@router.get("/alerts")
async def get_alerts(
    session_id: Optional[int] = None,
    active_only: bool = True
):
    """Get performance alerts"""
    
    if active_only:
        return performance_monitor.alert_manager.get_active_alerts(session_id)
    else:
        # Return all alerts from history
        return performance_monitor.alert_manager.alert_history

@router.post("/alerts/{alert_type}/acknowledge")
async def acknowledge_alert(
    alert_type: str,
    session_id: Optional[int] = None,
    acknowledged_by: str = "system"
):
    """Acknowledge a performance alert"""
    
    performance_monitor.alert_manager.acknowledge_alert(alert_type, session_id, acknowledged_by)
    return {"message": "Alert acknowledged", "alert_type": alert_type}

@router.get("/metrics/statistics")
async def get_metrics_statistics(
    metric_name: str,
    session_id: Optional[int] = None,
    minutes: int = 60
):
    """Get statistics for a specific metric"""
    
    stats = performance_monitor.metrics_collector.get_metric_statistics(metric_name, minutes)
    trend = performance_monitor.metrics_collector.get_trend_analysis(metric_name, minutes)
    
    return {
        "metric_name": metric_name,
        "time_window_minutes": minutes,
        "statistics": stats,
        "trend_analysis": trend
    }

# WebSocket endpoint
@router.websocket("/sessions/{session_id}/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: int):
    """WebSocket connection for real-time performance updates"""
    
    await websocket.accept()
    await performance_monitor.add_websocket_connection(session_id, websocket)
    
    try:
        # Start monitoring if not already started
        await performance_monitor.start_monitoring(session_id)
        
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }))
            
    except WebSocketDisconnect:
        await performance_monitor.remove_websocket_connection(session_id, websocket)