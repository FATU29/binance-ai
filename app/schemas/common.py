"""Common response schemas."""

from typing import Any

from pydantic import Field

from app.schemas.base import BaseSchema


class HealthResponse(BaseSchema):
    """Health check response schema."""

    status: str = Field(default="healthy", examples=["healthy"])
    version: str = Field(..., examples=["0.1.0"])
    environment: str = Field(..., examples=["development"])


class MessageResponse(BaseSchema):
    """Generic message response schema."""

    message: str = Field(..., examples=["Operation successful"])


class ErrorResponse(BaseSchema):
    """Error response schema."""

    detail: str = Field(..., examples=["An error occurred"])
    error_code: str | None = Field(None, examples=["VALIDATION_ERROR"])
    errors: dict[str, Any] | None = Field(None, examples=[{"field": "error message"}])


class SuccessResponse(BaseSchema):
    """Generic success response schema."""

    success: bool = Field(default=True)
    message: str = Field(..., examples=["Operation completed successfully"])
    data: dict[str, Any] | None = None
