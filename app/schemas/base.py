"""Base Pydantic schemas with common fields."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,  # Enable ORM mode (SQLAlchemy model conversion)
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class TimestampSchema(BaseModel):
    """Schema for models with timestamps."""

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginationParams(BaseModel):
    """Schema for pagination parameters."""

    page: int = 1
    page_size: int = 20

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "page": 1,
                    "page_size": 20,
                }
            ]
        }
    )


class PaginatedResponse(BaseModel):
    """Generic paginated response schema."""

    items: list[BaseSchema]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)
