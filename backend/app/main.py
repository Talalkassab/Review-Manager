"""
Main FastAPI application for Restaurant AI Customer Feedback Agent.
Handles Arabic/English bilingual customer interactions via WhatsApp.
"""
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .core.config import settings
from .core.logging import get_logger, app_logger
from .database import init_database, close_database
from .api import (
    auth_router,
    customers_router, 
    restaurants_router,
    ai_agent_router,
    campaigns_router,
    whatsapp_router
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler for startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.app.APP_NAME} v{settings.app.APP_VERSION}")
    logger.info(f"Environment: {settings.app.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.app.DEBUG}")
    
    try:
        # Initialize database
        await init_database()
        logger.info("Database initialized successfully")
        
        # Log configuration
        logger.info("Application configuration loaded:")
        logger.info(f"- API Prefix: {settings.app.API_V1_PREFIX}")
        logger.info(f"- CORS Origins: {settings.app.BACKEND_CORS_ORIGINS}")
        logger.info(f"- Max File Size: {settings.app.MAX_FILE_SIZE / 1024 / 1024:.1f}MB")
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        app_logger.log_error_with_context(e, {"event": "startup_failed"})
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    try:
        await close_database()
        logger.info("Database connections closed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")
        app_logger.log_error_with_context(e, {"event": "shutdown_error"})
    
    logger.info("Application shutdown completed")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """
    app = FastAPI(
        title=settings.app.APP_NAME,
        description="AI-powered customer feedback agent for restaurants with Arabic/English support",
        version=settings.app.APP_VERSION,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url=f"{settings.app.API_V1_PREFIX}/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )
    
    # Add security middleware
    if not settings.is_development:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]  # Configure based on your deployment
        )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.app.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["Content-Range", "X-Content-Range"]
    )
    
    # Add request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all HTTP requests with timing and context."""
        import time
        import uuid
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Extract user info if available
        user_id = "anonymous"
        if hasattr(request.state, "user") and request.state.user:
            user_id = str(getattr(request.state.user, "id", "anonymous"))
        
        # Log request start
        start_time = time.time()
        app_logger.log_request_start(
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            user_id=user_id
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log request completion
            app_logger.log_request_end(
                request_id=request_id,
                status_code=response.status_code,
                duration_ms=duration_ms
            )
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            logger.error(
                f"Request failed: {request.method} {request.url}",
                error=str(e),
                duration_ms=duration_ms,
                request_id=request_id
            )
            
            app_logger.log_error_with_context(e, {
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "duration_ms": duration_ms
            })
            
            # Return generic error response
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "request_id": request_id,
                    "error": str(e) if settings.is_development else "An unexpected error occurred"
                }
            )
    
    # Include API routers
    app.include_router(
        auth_router,
        prefix=f"{settings.app.API_V1_PREFIX}/auth",
        tags=["Authentication"]
    )
    
    app.include_router(
        customers_router,
        prefix=f"{settings.app.API_V1_PREFIX}/customers",
        tags=["Customers"]
    )
    
    app.include_router(
        restaurants_router,
        prefix=f"{settings.app.API_V1_PREFIX}/restaurants", 
        tags=["Restaurants"]
    )
    
    app.include_router(
        ai_agent_router,
        prefix=f"{settings.app.API_V1_PREFIX}/ai-agent",
        tags=["AI Agent"]
    )
    
    app.include_router(
        campaigns_router,
        prefix=f"{settings.app.API_V1_PREFIX}/campaigns",
        tags=["Campaigns"]
    )
    
    app.include_router(
        whatsapp_router,
        prefix=f"{settings.app.API_V1_PREFIX}/whatsapp",
        tags=["WhatsApp"]
    )
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with basic service information."""
        return {
            "service": settings.app.APP_NAME,
            "version": settings.app.APP_VERSION,
            "status": "active",
            "environment": settings.app.ENVIRONMENT,
            "docs_url": "/docs" if settings.is_development else None,
            "supported_languages": ["ar", "en"],
            "features": [
                "whatsapp_integration",
                "ai_powered_responses", 
                "sentiment_analysis",
                "multilingual_support",
                "customer_feedback_analysis"
            ]
        }
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint for monitoring."""
        try:
            # Add database health check here when database.py is ready
            return {
                "status": "healthy",
                "timestamp": asyncio.get_event_loop().time(),
                "version": settings.app.APP_VERSION,
                "environment": settings.app.ENVIRONMENT
            }
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "error": str(e) if settings.is_development else "Service unavailable"
                }
            )
    
    # Metrics endpoint (for monitoring)
    @app.get("/metrics")
    async def metrics():
        """Basic metrics endpoint."""
        if not settings.is_development:
            return JSONResponse(
                status_code=404,
                content={"detail": "Not found"}
            )
        
        return {
            "requests_total": "implemented_with_prometheus",  # Placeholder
            "response_time_seconds": "implemented_with_prometheus",
            "active_connections": "implemented_with_prometheus",
            "database_connections": "implemented_with_prometheus"
        }
    
    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    """Run the application directly for development."""
    uvicorn.run(
        "app.main:app",
        host=settings.app.HOST,
        port=settings.app.PORT,
        reload=settings.is_development,
        workers=1 if settings.is_development else settings.app.WORKERS,
        log_level=settings.logging.LOG_LEVEL.lower(),
        access_log=settings.logging.ENABLE_REQUEST_LOGGING,
        loop="asyncio"
    )