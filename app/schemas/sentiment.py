"""Pydantic schemas for sentiment analysis."""

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema


class SentimentAnalysisBase(BaseSchema):
    """Base schema for sentiment analysis."""

    news_article_id: int
    sentiment_label: str = Field(..., min_length=1, max_length=50)
    sentiment_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    model_version: str = Field(..., min_length=1, max_length=50)
    analysis_metadata: str | None = None

    @field_validator("sentiment_label")
    @classmethod
    def validate_sentiment_label(cls, v: str) -> str:
        """Validate sentiment label."""
        allowed_labels = {"positive", "negative", "neutral", "bullish", "bearish"}
        if v.lower() not in allowed_labels:
            raise ValueError(
                f"Invalid sentiment label. Must be one of: {', '.join(allowed_labels)}"
            )
        return v.lower()


class SentimentAnalysisCreate(SentimentAnalysisBase):
    """Schema for creating sentiment analysis."""

    pass


class SentimentAnalysisUpdate(BaseSchema):
    """Schema for updating sentiment analysis."""

    sentiment_label: str | None = Field(None, min_length=1, max_length=50)
    sentiment_score: float | None = Field(None, ge=0.0, le=1.0)
    confidence: float | None = Field(None, ge=0.0, le=1.0)
    model_version: str | None = Field(None, min_length=1, max_length=50)
    analysis_metadata: str | None = None


class SentimentAnalysisResponse(SentimentAnalysisBase, TimestampSchema):
    """Schema for sentiment analysis response."""

    id: int

    model_config = BaseSchema.model_config | {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "news_article_id": 1,
                    "sentiment_label": "positive",
                    "sentiment_score": 0.85,
                    "confidence": 0.92,
                    "model_version": "v1.0.0",
                    "analysis_metadata": '{"keywords": ["bullish", "growth"]}',
                    "created_at": "2024-01-01T12:00:00Z",
                    "updated_at": "2024-01-01T12:00:00Z",
                }
            ]
        }
    }


class SentimentAnalysisRequest(BaseSchema):
    """Schema for sentiment analysis request (text input).
    
    Note: Model version is controlled server-side via config, not client input.
    This prevents cost manipulation and ensures consistent AI behavior.
    """

    text: str = Field(..., min_length=1, max_length=10000)


class SentimentAnalysisResult(BaseSchema):
    """Schema for sentiment analysis result (without DB record)."""

    sentiment_label: str
    sentiment_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    model_version: str
