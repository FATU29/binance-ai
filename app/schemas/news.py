"""Pydantic schemas for news articles."""

from datetime import datetime

from pydantic import Field, HttpUrl

from app.schemas.base import BaseSchema, TimestampSchema


class NewsArticleBase(BaseSchema):
    """Base schema for news article."""

    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1, max_length=200)
    url: HttpUrl
    author: str | None = Field(None, max_length=200)
    published_at: datetime | None = None
    category: str | None = Field(None, max_length=100)


class NewsArticleCreate(NewsArticleBase):
    """Schema for creating a news article."""

    pass


class NewsArticleUpdate(BaseSchema):
    """Schema for updating a news article."""

    title: str | None = Field(None, min_length=1, max_length=500)
    content: str | None = Field(None, min_length=1)
    source: str | None = Field(None, min_length=1, max_length=200)
    url: HttpUrl | None = None
    author: str | None = Field(None, max_length=200)
    published_at: datetime | None = None
    category: str | None = Field(None, max_length=100)


class NewsArticleResponse(NewsArticleBase, TimestampSchema):
    """Schema for news article response."""

    id: int

    model_config = BaseSchema.model_config | {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "title": "Bitcoin reaches new all-time high",
                    "content": "Bitcoin has reached a new all-time high of $100,000...",
                    "source": "CryptoNews",
                    "url": "https://example.com/bitcoin-ath",
                    "author": "John Doe",
                    "published_at": "2024-01-01T12:00:00Z",
                    "category": "cryptocurrency",
                    "created_at": "2024-01-01T12:00:00Z",
                    "updated_at": "2024-01-01T12:00:00Z",
                }
            ]
        }
    }


class NewsArticleList(BaseSchema):
    """Schema for list of news articles."""

    items: list[NewsArticleResponse]
    total: int
    page: int
    page_size: int
