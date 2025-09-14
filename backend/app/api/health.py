"""
Health check and system monitoring endpoints.
"""
import asyncio
import platform
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import psutil
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel

from app.core.database import get_session
from app.core.config import settings
from app.core.logging import get_logger
from app.services import WhatsAppService, AIService

logger = get_logger(__name__)

router = APIRouter(tags=["Health"])


class HealthStatus(BaseModel):
    """Basic health status."""
    status: str
    timestamp: datetime
    version: str = "1.0.0"


class DatabaseHealth(BaseModel):
    """Database health information."""
    status: str
    response_time_ms: float
    connection_pool_size: int
    active_connections: int


class ExternalServiceHealth(BaseModel):
    """External service health information."""
    service_name: str
    status: str
    response_time_ms: Optional[float] = None
    last_check: datetime
    error_message: Optional[str] = None


class SystemMetrics(BaseModel):
    """System performance metrics."""
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    uptime_seconds: float
    load_average: List[float]


class DetailedHealthResponse(BaseModel):
    """Comprehensive health check response."""
    status: str
    timestamp: datetime
    version: str
    environment: str
    database: DatabaseHealth
    external_services: List[ExternalServiceHealth]
    system_metrics: SystemMetrics
    checks_passed: int
    checks_total: int
    details: Dict[str, Any]


class HealthChecker:
    """Comprehensive health checking service."""

    def __init__(self):
        self.start_time = time.time()

    async def check_basic_health(self) -> HealthStatus:
        """Basic health check - just confirms the service is running."""
        return HealthStatus(
            status="healthy",
            timestamp=datetime.utcnow(),
            version="1.0.0"
        )

    async def check_database_health(self, db: AsyncSession) -> DatabaseHealth:
        """Check database connectivity and performance."""
        start_time = time.time()

        try:
            # Test database connection with a simple query
            result = await db.execute(text("SELECT 1"))
            await result.fetchone()

            response_time = (time.time() - start_time) * 1000

            # Get connection pool information
            pool = db.get_bind().pool
            pool_size = pool.size()
            active_connections = pool.checkedout()

            return DatabaseHealth(
                status="healthy",
                response_time_ms=round(response_time, 2),
                connection_pool_size=pool_size,
                active_connections=active_connections
            )

        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return DatabaseHealth(
                status="unhealthy",
                response_time_ms=-1,
                connection_pool_size=0,
                active_connections=0
            )

    async def check_whatsapp_health(self, db: AsyncSession) -> ExternalServiceHealth:
        """Check WhatsApp/Twilio service health."""
        start_time = time.time()

        try:
            whatsapp_service = WhatsAppService(db)
            health_status = await whatsapp_service.check_service_health()

            response_time = (time.time() - start_time) * 1000

            return ExternalServiceHealth(
                service_name="whatsapp",
                status="healthy" if health_status.get("healthy", False) else "unhealthy",
                response_time_ms=round(response_time, 2),
                last_check=datetime.utcnow(),
                error_message=health_status.get("error")
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error("WhatsApp health check failed", error=str(e))

            return ExternalServiceHealth(
                service_name="whatsapp",
                status="unhealthy",
                response_time_ms=round(response_time, 2),
                last_check=datetime.utcnow(),
                error_message=str(e)
            )

    async def check_ai_health(self, db: AsyncSession) -> ExternalServiceHealth:
        """Check AI service (OpenRouter) health."""
        start_time = time.time()

        try:
            ai_service = AIService(db)
            # Test with a simple sentiment analysis
            test_result = await ai_service.analyze_sentiment(
                "This is a test message for health check",
                test_mode=True
            )

            response_time = (time.time() - start_time) * 1000

            return ExternalServiceHealth(
                service_name="ai_service",
                status="healthy" if test_result else "unhealthy",
                response_time_ms=round(response_time, 2),
                last_check=datetime.utcnow()
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error("AI service health check failed", error=str(e))

            return ExternalServiceHealth(
                service_name="ai_service",
                status="unhealthy",
                response_time_ms=round(response_time, 2),
                last_check=datetime.utcnow(),
                error_message=str(e)
            )

    def get_system_metrics(self) -> SystemMetrics:
        """Get current system performance metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100

            # Uptime
            uptime = time.time() - self.start_time

            # Load average (Unix-like systems)
            try:
                load_avg = list(psutil.getloadavg())
            except (AttributeError, OSError):
                # Windows doesn't support getloadavg
                load_avg = [0.0, 0.0, 0.0]

            return SystemMetrics(
                cpu_usage_percent=round(cpu_percent, 2),
                memory_usage_percent=round(memory_percent, 2),
                disk_usage_percent=round(disk_percent, 2),
                uptime_seconds=round(uptime, 2),
                load_average=load_avg
            )

        except Exception as e:
            logger.error("Failed to get system metrics", error=str(e))
            return SystemMetrics(
                cpu_usage_percent=0.0,
                memory_usage_percent=0.0,
                disk_usage_percent=0.0,
                uptime_seconds=0.0,
                load_average=[0.0, 0.0, 0.0]
            )

    async def perform_comprehensive_health_check(self, db: AsyncSession) -> DetailedHealthResponse:
        """Perform comprehensive health check of all system components."""
        start_time = time.time()

        # Run all health checks concurrently
        db_health, whatsapp_health, ai_health = await asyncio.gather(
            self.check_database_health(db),
            self.check_whatsapp_health(db),
            self.check_ai_health(db),
            return_exceptions=True
        )

        # Handle exceptions from concurrent execution
        if isinstance(db_health, Exception):
            logger.error("Database health check exception", error=str(db_health))
            db_health = DatabaseHealth(
                status="unhealthy",
                response_time_ms=-1,
                connection_pool_size=0,
                active_connections=0
            )

        if isinstance(whatsapp_health, Exception):
            logger.error("WhatsApp health check exception", error=str(whatsapp_health))
            whatsapp_health = ExternalServiceHealth(
                service_name="whatsapp",
                status="unhealthy",
                last_check=datetime.utcnow(),
                error_message=str(whatsapp_health)
            )

        if isinstance(ai_health, Exception):
            logger.error("AI health check exception", error=str(ai_health))
            ai_health = ExternalServiceHealth(
                service_name="ai_service",
                status="unhealthy",
                last_check=datetime.utcnow(),
                error_message=str(ai_health)
            )

        external_services = [whatsapp_health, ai_health]
        system_metrics = self.get_system_metrics()

        # Count healthy services
        checks_passed = 0
        checks_total = 1 + len(external_services)  # database + external services

        if db_health.status == "healthy":
            checks_passed += 1

        for service in external_services:
            if service.status == "healthy":
                checks_passed += 1

        # Overall status
        overall_status = "healthy" if checks_passed == checks_total else "degraded"
        if checks_passed == 0:
            overall_status = "unhealthy"

        total_check_time = (time.time() - start_time) * 1000

        return DetailedHealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version="1.0.0",
            environment=settings.app.ENVIRONMENT,
            database=db_health,
            external_services=external_services,
            system_metrics=system_metrics,
            checks_passed=checks_passed,
            checks_total=checks_total,
            details={
                "platform": platform.system(),
                "python_version": sys.version.split()[0],
                "total_check_time_ms": round(total_check_time, 2),
                "healthy_services": [
                    service.service_name for service in external_services
                    if service.status == "healthy"
                ],
                "unhealthy_services": [
                    service.service_name for service in external_services
                    if service.status == "unhealthy"
                ]
            }
        )


# Global health checker instance
health_checker = HealthChecker()


@router.get("/health", response_model=HealthStatus)
async def basic_health_check():
    """
    Basic health check endpoint.
    Returns simple status to confirm the service is running.
    """
    return await health_checker.check_basic_health()


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check(db: AsyncSession = Depends(get_session)):
    """
    Comprehensive health check endpoint.
    Checks database, external services, and system metrics.
    """
    try:
        health_result = await health_checker.perform_comprehensive_health_check(db)

        # Return appropriate HTTP status based on health
        if health_result.status == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=health_result.dict()
            )
        elif health_result.status == "degraded":
            # Return 200 but log warning
            logger.warning(
                "Service health is degraded",
                checks_passed=health_result.checks_passed,
                checks_total=health_result.checks_total,
                unhealthy_services=health_result.details.get("unhealthy_services", [])
            )

        return health_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )


@router.get("/health/database")
async def database_health_check(db: AsyncSession = Depends(get_session)):
    """
    Database-specific health check endpoint.
    """
    db_health = await health_checker.check_database_health(db)

    if db_health.status != "healthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=db_health.dict()
        )

    return db_health


@router.get("/health/external")
async def external_services_health_check(db: AsyncSession = Depends(get_session)):
    """
    External services health check endpoint.
    """
    whatsapp_health, ai_health = await asyncio.gather(
        health_checker.check_whatsapp_health(db),
        health_checker.check_ai_health(db),
        return_exceptions=True
    )

    # Handle exceptions
    if isinstance(whatsapp_health, Exception):
        whatsapp_health = ExternalServiceHealth(
            service_name="whatsapp",
            status="unhealthy",
            last_check=datetime.utcnow(),
            error_message=str(whatsapp_health)
        )

    if isinstance(ai_health, Exception):
        ai_health = ExternalServiceHealth(
            service_name="ai_service",
            status="unhealthy",
            last_check=datetime.utcnow(),
            error_message=str(ai_health)
        )

    services = [whatsapp_health, ai_health]
    unhealthy_services = [s for s in services if s.status != "healthy"]

    if unhealthy_services:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "services": [s.dict() for s in services],
                "unhealthy_count": len(unhealthy_services)
            }
        )

    return {
        "status": "healthy",
        "services": [s.dict() for s in services],
        "timestamp": datetime.utcnow()
    }


@router.get("/health/system")
async def system_metrics_check():
    """
    System metrics endpoint.
    """
    metrics = health_checker.get_system_metrics()

    # Check if system is under high load
    high_load_threshold = 80.0
    warnings = []

    if metrics.cpu_usage_percent > high_load_threshold:
        warnings.append(f"High CPU usage: {metrics.cpu_usage_percent}%")

    if metrics.memory_usage_percent > high_load_threshold:
        warnings.append(f"High memory usage: {metrics.memory_usage_percent}%")

    if metrics.disk_usage_percent > 90.0:
        warnings.append(f"High disk usage: {metrics.disk_usage_percent}%")

    response = {
        "status": "healthy" if not warnings else "warning",
        "metrics": metrics.dict(),
        "timestamp": datetime.utcnow(),
        "warnings": warnings
    }

    if warnings:
        logger.warning("System metrics show high resource usage", warnings=warnings)

    return response


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_session)):
    """
    Kubernetes-style readiness probe.
    Checks if the service is ready to handle requests.
    """
    try:
        # Quick database check
        await db.execute(text("SELECT 1"))

        return {
            "status": "ready",
            "timestamp": datetime.utcnow()
        }

    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )


@router.get("/live")
async def liveness_check():
    """
    Kubernetes-style liveness probe.
    Simple check to confirm the service is alive.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow(),
        "uptime_seconds": round(time.time() - health_checker.start_time, 2)
    }