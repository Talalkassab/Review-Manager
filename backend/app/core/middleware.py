"""
Middleware for request processing, logging, and monitoring.
"""
import time
import uuid
from typing import Callable, Dict, Any
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
import structlog

from .logging import app_logger, get_logger
from .config import settings
from .exceptions import BaseServiceException, ErrorHandlerMiddleware

logger = get_logger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add correlation IDs to requests for tracking across services.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

        # Add to request state
        request.state.correlation_id = correlation_id

        # Bind to logger context
        logger_with_context = logger.bind(correlation_id=correlation_id)
        request.state.logger = logger_with_context

        # Process request
        response = await call_next(request)

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive request/response logging with performance tracking.
    """

    def __init__(self, app: FastAPI, log_body: bool = False):
        super().__init__(app)
        self.log_body = log_body

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Extract request information
        correlation_id = getattr(request.state, 'correlation_id', 'unknown')
        user_id = self._extract_user_id(request)
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")

        # Log request start
        request_logger = logger.bind(
            correlation_id=correlation_id,
            user_id=user_id,
            client_ip=client_ip,
            user_agent=user_agent
        )

        # Log request body if enabled (for debugging)
        request_body = None
        if self.log_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    request_body = body.decode('utf-8')[:1000]  # Limit body size in logs
            except Exception:
                request_body = "Unable to read request body"

        request_logger.info(
            "Request started",
            method=request.method,
            url=str(request.url),
            path=request.url.path,
            query_params=dict(request.query_params),
            request_body=request_body if self.log_body else None
        )

        # Process request
        response = None
        error = None

        try:
            response = await call_next(request)
        except Exception as e:
            error = e
            # Create error response
            if isinstance(e, BaseServiceException):
                response = JSONResponse(
                    status_code=e.status_code,
                    content=ErrorHandlerMiddleware.create_error_response(e, correlation_id)
                )
            else:
                response = JSONResponse(
                    status_code=500,
                    content=ErrorHandlerMiddleware.create_error_response(
                        Exception("Internal server error"),
                        correlation_id,
                        error_type="INTERNAL_SERVER_ERROR"
                    )
                )

        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000

        # Log response
        log_level = "error" if response.status_code >= 400 else "info"
        log_method = getattr(request_logger, log_level)

        log_data = {
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "processing_time_ms": round(processing_time_ms, 2),
            "response_size": len(response.body) if hasattr(response, 'body') else None
        }

        if error:
            log_data["error"] = str(error)
            log_data["error_type"] = type(error).__name__

        log_method("Request completed", **log_data)

        # Add performance headers
        response.headers["X-Processing-Time-MS"] = str(round(processing_time_ms, 2))

        # Log slow requests
        if processing_time_ms > settings.logging.SLOW_REQUEST_THRESHOLD_MS:
            request_logger.warning(
                "Slow request detected",
                processing_time_ms=processing_time_ms,
                threshold_ms=settings.logging.SLOW_REQUEST_THRESHOLD_MS,
                **log_data
            )

        return response

    def _extract_user_id(self, request: Request) -> str:
        """Extract user ID from request if available."""
        # Try to get user from request state (set by auth middleware)
        user = getattr(request.state, 'user', None)
        if user and hasattr(user, 'id'):
            return str(user.id)

        # Try to get from headers
        user_id = request.headers.get("X-User-ID")
        if user_id:
            return user_id

        return "anonymous"

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address, handling proxies."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to responses.
    """

    def __init__(self, app: FastAPI, headers: Dict[str, str] = None):
        super().__init__(app)
        self.security_headers = headers or {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()"
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Add security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value

        return response


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware (in-memory store).
    For production, use Redis-based rate limiting.
    """

    def __init__(self, app: FastAPI, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts: Dict[str, Dict[str, Any]] = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = self._get_client_ip(request)
        current_time = time.time()

        # Clean old entries
        self._cleanup_old_entries(current_time)

        # Check rate limit
        if self._is_rate_limited(client_ip, current_time):
            # Log rate limit violation
            logger.bind(
                correlation_id=getattr(request.state, 'correlation_id', 'unknown'),
                client_ip=client_ip
            ).warning(
                "Rate limit exceeded",
                requests_per_minute=self.requests_per_minute,
                path=request.url.path
            )

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "type": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please try again later.",
                        "details": {
                            "limit": self.requests_per_minute,
                            "window": "1 minute"
                        }
                    }
                },
                headers={"Retry-After": "60"}
            )

        # Update request count
        self._update_request_count(client_ip, current_time)

        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _is_rate_limited(self, client_ip: str, current_time: float) -> bool:
        """Check if client is rate limited."""
        if client_ip not in self.request_counts:
            return False

        client_data = self.request_counts[client_ip]
        window_start = current_time - 60  # 1 minute window

        # Count requests in current window
        recent_requests = [
            req_time for req_time in client_data.get('requests', [])
            if req_time > window_start
        ]

        return len(recent_requests) >= self.requests_per_minute

    def _update_request_count(self, client_ip: str, current_time: float):
        """Update request count for client."""
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = {'requests': []}

        self.request_counts[client_ip]['requests'].append(current_time)

        # Keep only recent requests
        window_start = current_time - 60
        self.request_counts[client_ip]['requests'] = [
            req_time for req_time in self.request_counts[client_ip]['requests']
            if req_time > window_start
        ]

    def _cleanup_old_entries(self, current_time: float):
        """Clean up old entries to prevent memory leaks."""
        window_start = current_time - 60
        clients_to_remove = []

        for client_ip, data in self.request_counts.items():
            recent_requests = [
                req_time for req_time in data.get('requests', [])
                if req_time > window_start
            ]

            if not recent_requests:
                clients_to_remove.append(client_ip)
            else:
                self.request_counts[client_ip]['requests'] = recent_requests

        for client_ip in clients_to_remove:
            del self.request_counts[client_ip]


class DatabaseQueryLoggingMiddleware:
    """
    Middleware for logging database queries (SQLAlchemy integration).
    """

    def __init__(self, enable_query_logging: bool = True):
        self.enable_query_logging = enable_query_logging

        if enable_query_logging:
            self._setup_query_logging()

    def _setup_query_logging(self):
        """Set up SQLAlchemy query logging."""
        import logging
        from sqlalchemy import event
        from sqlalchemy.engine import Engine

        @event.listens_for(Engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()

        @event.listens_for(Engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - context._query_start_time
            duration_ms = total * 1000

            # Log query
            app_logger.log_database_query(
                query=statement,
                params=parameters,
                duration_ms=duration_ms
            )

            # Log slow queries
            if duration_ms > settings.logging.SLOW_QUERY_THRESHOLD_MS:
                logger.warning(
                    "Slow database query detected",
                    query=statement[:200] + "..." if len(statement) > 200 else statement,
                    duration_ms=duration_ms,
                    threshold_ms=settings.logging.SLOW_QUERY_THRESHOLD_MS
                )


def setup_middleware(app: FastAPI):
    """
    Set up all middleware for the FastAPI application.
    """
    # Add middleware in reverse order of execution

    # Security headers (executed last)
    app.add_middleware(SecurityHeadersMiddleware)

    # Rate limiting
    if settings.security.ENABLE_RATE_LIMITING:
        app.add_middleware(
            RateLimitingMiddleware,
            requests_per_minute=settings.security.RATE_LIMIT_PER_MINUTE
        )

    # Request logging (executed early to catch all requests)
    app.add_middleware(
        RequestLoggingMiddleware,
        log_body=settings.logging.LOG_REQUEST_BODIES
    )

    # Correlation ID (executed first to ensure all logs have correlation ID)
    app.add_middleware(CorrelationIdMiddleware)

    # Database query logging
    if settings.logging.ENABLE_SQL_LOGGING:
        DatabaseQueryLoggingMiddleware(enable_query_logging=True)

    logger.info("Middleware setup completed", middlewares=[
        "CorrelationIdMiddleware",
        "RequestLoggingMiddleware",
        "RateLimitingMiddleware" if settings.security.ENABLE_RATE_LIMITING else None,
        "SecurityHeadersMiddleware",
        "DatabaseQueryLoggingMiddleware" if settings.logging.ENABLE_SQL_LOGGING else None
    ])