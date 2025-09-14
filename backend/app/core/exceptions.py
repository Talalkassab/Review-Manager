"""
Custom Exception System and Global Error Handler
Provides domain-specific exceptions and centralized error handling.
"""
from typing import Any, Dict, Optional, Union
from datetime import datetime
from uuid import uuid4
import traceback
import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError, OperationalError

logger = logging.getLogger(__name__)


# Base Exception Classes
class BaseServiceException(Exception):
    """Base exception for all service-layer exceptions."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.status_code = status_code
        self.correlation_id = str(uuid4())
        self.timestamp = datetime.utcnow()


# Customer Service Exceptions
class CustomerServiceException(BaseServiceException):
    """Base exception for customer service errors."""
    pass


class CustomerNotFound(CustomerServiceException):
    """Raised when a customer is not found."""

    def __init__(self, customer_id: Optional[str] = None):
        message = f"Customer not found: {customer_id}" if customer_id else "Customer not found"
        super().__init__(
            message=message,
            error_code="CUSTOMER_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"customer_id": customer_id} if customer_id else {}
        )


class CustomerAlreadyExists(CustomerServiceException):
    """Raised when attempting to create a duplicate customer."""

    def __init__(self, phone_number: str, restaurant_id: Optional[str] = None):
        super().__init__(
            message=f"Customer with phone number {phone_number} already exists",
            error_code="CUSTOMER_ALREADY_EXISTS",
            status_code=status.HTTP_409_CONFLICT,
            details={"phone_number": phone_number, "restaurant_id": restaurant_id}
        )


class InvalidPhoneNumber(CustomerServiceException):
    """Raised when an invalid phone number is provided."""

    def __init__(self, phone_number: str):
        super().__init__(
            message=f"Invalid phone number format: {phone_number}",
            error_code="INVALID_PHONE_NUMBER",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"phone_number": phone_number}
        )


class InsufficientPermissions(CustomerServiceException):
    """Raised when user lacks required permissions."""

    def __init__(self, action: str, resource: Optional[str] = None):
        message = f"Insufficient permissions to {action}"
        if resource:
            message += f" on {resource}"
        super().__init__(
            message=message,
            error_code="INSUFFICIENT_PERMISSIONS",
            status_code=status.HTTP_403_FORBIDDEN,
            details={"action": action, "resource": resource}
        )


# WhatsApp Service Exceptions
class WhatsAppServiceException(BaseServiceException):
    """Base exception for WhatsApp service errors."""
    pass


class MessageSendFailure(WhatsAppServiceException):
    """Raised when a WhatsApp message fails to send."""

    def __init__(self, to_number: str, reason: Optional[str] = None):
        super().__init__(
            message=f"Failed to send message to {to_number}",
            error_code="MESSAGE_SEND_FAILURE",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details={"to_number": to_number, "reason": reason}
        )


class WebhookProcessingError(WhatsAppServiceException):
    """Raised when webhook processing fails."""

    def __init__(self, webhook_type: str, error: str):
        super().__init__(
            message=f"Failed to process {webhook_type} webhook",
            error_code="WEBHOOK_PROCESSING_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"webhook_type": webhook_type, "error": error}
        )


class TwilioServiceUnavailable(WhatsAppServiceException):
    """Raised when Twilio service is unavailable."""

    def __init__(self):
        super().__init__(
            message="Twilio service is currently unavailable",
            error_code="TWILIO_SERVICE_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


# AI Service Exceptions
class AIServiceException(BaseServiceException):
    """Base exception for AI service errors."""
    pass


class SentimentAnalysisFailure(AIServiceException):
    """Raised when sentiment analysis fails."""

    def __init__(self, reason: str):
        super().__init__(
            message="Failed to analyze sentiment",
            error_code="SENTIMENT_ANALYSIS_FAILURE",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"reason": reason}
        )


class AIModelUnavailable(AIServiceException):
    """Raised when AI model is unavailable."""

    def __init__(self, model_name: Optional[str] = None):
        message = f"AI model {model_name} is unavailable" if model_name else "AI model is unavailable"
        super().__init__(
            message=message,
            error_code="AI_MODEL_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"model": model_name} if model_name else {}
        )


class ResponseGenerationFailure(AIServiceException):
    """Raised when AI response generation fails."""

    def __init__(self, context: Optional[Dict] = None):
        super().__init__(
            message="Failed to generate AI response",
            error_code="RESPONSE_GENERATION_FAILURE",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"context": context} if context else {}
        )


# Analytics Service Exceptions
class AnalyticsServiceException(BaseServiceException):
    """Base exception for analytics service errors."""
    pass


class MetricsCalculationError(AnalyticsServiceException):
    """Raised when metrics calculation fails."""

    def __init__(self, metric_type: str, reason: str):
        super().__init__(
            message=f"Failed to calculate {metric_type} metrics",
            error_code="METRICS_CALCULATION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"metric_type": metric_type, "reason": reason}
        )


class ReportGenerationFailure(AnalyticsServiceException):
    """Raised when report generation fails."""

    def __init__(self, report_type: str, reason: str):
        super().__init__(
            message=f"Failed to generate {report_type} report",
            error_code="REPORT_GENERATION_FAILURE",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"report_type": report_type, "reason": reason}
        )


class InvalidTimeRange(AnalyticsServiceException):
    """Raised when an invalid time range is specified."""

    def __init__(self, start_date: str, end_date: str):
        super().__init__(
            message="Invalid time range specified",
            error_code="INVALID_TIME_RANGE",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"start_date": start_date, "end_date": end_date}
        )


# Database Exceptions
class DatabaseException(BaseServiceException):
    """Base exception for database errors."""
    pass


class DatabaseConnectionError(DatabaseException):
    """Raised when database connection fails."""

    def __init__(self, details: Optional[str] = None):
        super().__init__(
            message="Failed to connect to database",
            error_code="DATABASE_CONNECTION_ERROR",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"error": details} if details else {}
        )


class DataIntegrityError(DatabaseException):
    """Raised when data integrity constraints are violated."""

    def __init__(self, constraint: str, details: Optional[str] = None):
        super().__init__(
            message=f"Data integrity constraint violated: {constraint}",
            error_code="DATA_INTEGRITY_ERROR",
            status_code=status.HTTP_409_CONFLICT,
            details={"constraint": constraint, "error": details}
        )


# Configuration Exceptions
class ConfigurationException(BaseServiceException):
    """Base exception for configuration errors."""
    pass


class MissingConfiguration(ConfigurationException):
    """Raised when required configuration is missing."""

    def __init__(self, config_key: str):
        super().__init__(
            message=f"Required configuration missing: {config_key}",
            error_code="MISSING_CONFIGURATION",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"config_key": config_key}
        )


class InvalidConfiguration(ConfigurationException):
    """Raised when configuration is invalid."""

    def __init__(self, config_key: str, reason: str):
        super().__init__(
            message=f"Invalid configuration for {config_key}: {reason}",
            error_code="INVALID_CONFIGURATION",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"config_key": config_key, "reason": reason}
        )


# Authentication & Authorization Exceptions
class AuthenticationException(BaseServiceException):
    """Base exception for authentication errors."""
    pass


class InvalidCredentials(AuthenticationException):
    """Raised when invalid credentials are provided."""

    def __init__(self):
        super().__init__(
            message="Invalid authentication credentials",
            error_code="INVALID_CREDENTIALS",
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class TokenExpired(AuthenticationException):
    """Raised when authentication token has expired."""

    def __init__(self):
        super().__init__(
            message="Authentication token has expired",
            error_code="TOKEN_EXPIRED",
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class UnauthorizedAccess(AuthenticationException):
    """Raised when user attempts unauthorized access."""

    def __init__(self, resource: str):
        super().__init__(
            message=f"Unauthorized access to {resource}",
            error_code="UNAUTHORIZED_ACCESS",
            status_code=status.HTTP_403_FORBIDDEN,
            details={"resource": resource}
        )


# Validation Exceptions
class ValidationException(BaseServiceException):
    """Base exception for validation errors."""
    pass


class InvalidInput(ValidationException):
    """Raised when input validation fails."""

    def __init__(self, field: str, reason: str):
        super().__init__(
            message=f"Invalid input for {field}: {reason}",
            error_code="INVALID_INPUT",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"field": field, "reason": reason}
        )


class MissingRequiredField(ValidationException):
    """Raised when a required field is missing."""

    def __init__(self, field: str):
        super().__init__(
            message=f"Required field missing: {field}",
            error_code="MISSING_REQUIRED_FIELD",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"field": field}
        )


# Global Error Handler Middleware
class ErrorHandlerMiddleware:
    """
    Global error handler middleware for FastAPI.
    Catches all exceptions and returns standardized error responses.
    """

    @staticmethod
    def create_error_response(
        error_type: str,
        message: str,
        correlation_id: str,
        status_code: int = 500,
        details: Optional[Dict] = None
    ) -> JSONResponse:
        """Create standardized error response."""
        error_response = {
            "error": {
                "type": error_type,
                "message": message,
                "correlation_id": correlation_id,
                "timestamp": datetime.utcnow().isoformat(),
                "details": details or {}
            }
        }
        return JSONResponse(
            status_code=status_code,
            content=error_response
        )

    @classmethod
    async def handle_service_exception(cls, request: Request, exc: BaseServiceException) -> JSONResponse:
        """Handle service layer exceptions."""
        # Log the error with correlation ID
        logger.error(
            f"Service exception: {exc.error_code} | "
            f"Correlation ID: {exc.correlation_id} | "
            f"Message: {exc.message} | "
            f"Details: {exc.details}"
        )

        return cls.create_error_response(
            error_type=exc.error_code,
            message=exc.message,
            correlation_id=exc.correlation_id,
            status_code=exc.status_code,
            details=exc.details
        )

    @classmethod
    async def handle_http_exception(cls, request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Handle HTTP exceptions."""
        correlation_id = str(uuid4())

        logger.warning(
            f"HTTP exception: {exc.status_code} | "
            f"Correlation ID: {correlation_id} | "
            f"Detail: {exc.detail}"
        )

        return cls.create_error_response(
            error_type="HTTP_ERROR",
            message=str(exc.detail),
            correlation_id=correlation_id,
            status_code=exc.status_code
        )

    @classmethod
    async def handle_validation_error(cls, request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle request validation errors."""
        correlation_id = str(uuid4())

        # Extract validation error details
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })

        logger.warning(
            f"Validation error | "
            f"Correlation ID: {correlation_id} | "
            f"Errors: {errors}"
        )

        return cls.create_error_response(
            error_type="VALIDATION_ERROR",
            message="Request validation failed",
            correlation_id=correlation_id,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"validation_errors": errors}
        )

    @classmethod
    async def handle_database_error(cls, request: Request, exc: Union[IntegrityError, OperationalError]) -> JSONResponse:
        """Handle database exceptions."""
        correlation_id = str(uuid4())

        if isinstance(exc, IntegrityError):
            error_type = "DATABASE_INTEGRITY_ERROR"
            message = "Database integrity constraint violated"
            status_code = status.HTTP_409_CONFLICT
        else:
            error_type = "DATABASE_OPERATIONAL_ERROR"
            message = "Database operation failed"
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        logger.error(
            f"Database error: {error_type} | "
            f"Correlation ID: {correlation_id} | "
            f"Error: {str(exc)}"
        )

        return cls.create_error_response(
            error_type=error_type,
            message=message,
            correlation_id=correlation_id,
            status_code=status_code
        )

    @classmethod
    async def handle_generic_exception(cls, request: Request, exc: Exception) -> JSONResponse:
        """Handle all other exceptions."""
        correlation_id = str(uuid4())

        # Log full traceback for debugging
        logger.error(
            f"Unhandled exception | "
            f"Correlation ID: {correlation_id} | "
            f"Error: {str(exc)} | "
            f"Traceback: {traceback.format_exc()}"
        )

        # Don't expose internal errors in production
        return cls.create_error_response(
            error_type="INTERNAL_SERVER_ERROR",
            message="An internal server error occurred",
            correlation_id=correlation_id,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def register_exception_handlers(app):
    """Register all exception handlers with the FastAPI app."""
    from fastapi import FastAPI

    # Service exceptions
    app.add_exception_handler(BaseServiceException, ErrorHandlerMiddleware.handle_service_exception)

    # HTTP exceptions
    app.add_exception_handler(StarletteHTTPException, ErrorHandlerMiddleware.handle_http_exception)

    # Validation errors
    app.add_exception_handler(RequestValidationError, ErrorHandlerMiddleware.handle_validation_error)

    # Database errors
    app.add_exception_handler(IntegrityError, ErrorHandlerMiddleware.handle_database_error)
    app.add_exception_handler(OperationalError, ErrorHandlerMiddleware.handle_database_error)

    # Generic exceptions (catch-all)
    app.add_exception_handler(Exception, ErrorHandlerMiddleware.handle_generic_exception)

    logger.info("Exception handlers registered successfully")