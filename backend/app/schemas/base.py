"""
Base Pydantic schemas for common response patterns.
Provides reusable schema components and utilities.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

T = TypeVar('T')


class BaseSchema(BaseModel):
    """Base schema class with common configuration."""
    
    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )


class BaseResponse(BaseSchema):
    """Base response schema with common fields."""
    
    id: UUID = Field(..., description="Unique identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class ErrorResponse(BaseSchema):
    """Standard error response schema."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request identifier for tracking")


class SuccessResponse(BaseSchema):
    """Standard success response schema."""
    
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")


class PaginatedResponse(BaseSchema, Generic[T]):
    """Paginated response schema."""
    
    items: List[T] = Field(..., description="List of items")
    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, le=100, description="Items per page")
    pages: int = Field(..., ge=1, description="Total number of pages")
    has_prev: bool = Field(..., description="Has previous page")
    has_next: bool = Field(..., description="Has next page")


class FilterSchema(BaseSchema):
    """Base schema for filtering parameters."""
    
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(None, description="Sort by field")
    sort_order: Optional[str] = Field("asc", pattern="^(asc|desc)$", description="Sort order")
    search: Optional[str] = Field(None, min_length=1, max_length=100, description="Search term")


class DateRangeFilter(BaseSchema):
    """Date range filter schema."""
    
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")


class LanguageChoice(BaseSchema):
    """Language choice validation."""
    
    language: str = Field(..., pattern="^(ar|en)$", description="Language code (ar/en)")


class SentimentChoice(BaseSchema):
    """Sentiment choice validation."""
    
    sentiment: str = Field(..., pattern="^(positive|negative|neutral)$", description="Sentiment classification")


class BulkOperationRequest(BaseSchema):
    """Schema for bulk operations."""
    
    ids: List[UUID] = Field(..., min_items=1, max_items=100, description="List of IDs to operate on")
    operation: str = Field(..., description="Operation to perform")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Operation parameters")


class BulkOperationResponse(BaseSchema):
    """Response schema for bulk operations."""
    
    success_count: int = Field(..., ge=0, description="Number of successful operations")
    error_count: int = Field(..., ge=0, description="Number of failed operations")
    total_count: int = Field(..., ge=0, description="Total operations attempted")
    errors: Optional[List[Dict[str, Any]]] = Field(None, description="List of errors encountered")


class HealthCheckResponse(BaseSchema):
    """Health check response schema."""
    
    status: str = Field(..., description="Health status")
    timestamp: float = Field(..., description="Check timestamp")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Environment name")
    services: Optional[Dict[str, Any]] = Field(None, description="Service statuses")


class AnalyticsResponse(BaseSchema):
    """Base analytics response schema."""
    
    period: str = Field(..., description="Analytics period")
    data: Dict[str, Any] = Field(..., description="Analytics data")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")


class FileUploadResponse(BaseSchema):
    """File upload response schema."""
    
    filename: str = Field(..., description="Uploaded filename")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    file_type: str = Field(..., description="File MIME type")
    upload_id: UUID = Field(..., description="Upload identifier")
    url: Optional[str] = Field(None, description="File access URL")


class ValidationErrorDetail(BaseSchema):
    """Validation error detail schema."""
    
    field: str = Field(..., description="Field name with error")
    message: str = Field(..., description="Validation error message")
    value: Any = Field(..., description="Invalid value")


class ValidationErrorResponse(BaseSchema):
    """Validation error response schema."""
    
    error: str = Field("validation_error", description="Error type")
    message: str = Field("Validation failed", description="Error message")
    details: List[ValidationErrorDetail] = Field(..., description="Validation error details")