#!/usr/bin/env python3
"""
Simple FastAPI server for testing basic functionality.
"""
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.core.config import settings
from app.core.logging import get_logger
from app.database import init_database, close_database

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    logger.info(f"Starting {settings.app.APP_NAME} v{settings.app.APP_VERSION}")
    logger.info(f"Environment: {settings.app.ENVIRONMENT}")
    
    try:
        # Initialize database
        await init_database()
        logger.info("Database initialized successfully")
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    try:
        await close_database()
        logger.info("Database connections closed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")
    
    logger.info("Application shutdown completed")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app.APP_NAME,
        description="AI-powered customer feedback agent for restaurants with Arabic/English support",
        version=settings.app.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
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
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with basic service information."""
        return {
            "service": settings.app.APP_NAME,
            "version": settings.app.APP_VERSION,
            "status": "active",
            "environment": settings.app.ENVIRONMENT,
            "docs_url": "/docs",
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
            return {
                "status": "healthy",
                "timestamp": asyncio.get_event_loop().time(),
                "version": settings.app.APP_VERSION,
                "environment": settings.app.ENVIRONMENT
            }
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    """Run the application directly for development."""
    uvicorn.run(
        "main_simple:app",
        host=settings.app.HOST,
        port=settings.app.PORT,
        reload=settings.is_development,
        workers=1,
        log_level=settings.logging.LOG_LEVEL.lower(),
        access_log=settings.logging.ENABLE_REQUEST_LOGGING,
        loop="asyncio"
    )