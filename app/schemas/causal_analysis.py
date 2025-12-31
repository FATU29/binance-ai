"""Pydantic schemas for causal analysis of news with price history."""

from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.base import BaseSchema


class PriceDataPoint(BaseSchema):
    """Single price data point."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class CausalAnalysisRequest(BaseSchema):
    """Request schema for causal analysis."""

    news_article_id: int
    symbol: str = Field(..., min_length=1, max_length=20, description="Trading pair symbol (e.g., BTCUSDT)")
    hours_before: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Hours of price history before news to analyze (1-168 hours)"
    )
    hours_after: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Hours of price history after news to analyze (1-168 hours)"
    )
    prediction_horizon: Literal["1h", "4h", "24h", "7d"] = Field(
        default="24h",
        description="Time horizon for trend prediction"
    )


class CausalAnalysisDirectRequest(BaseSchema):
    """Request schema for causal analysis with direct news content (no DB required)."""

    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    published_at: datetime
    symbol: str = Field(..., min_length=1, max_length=20, description="Trading pair symbol (e.g., BTCUSDT)")
    hours_before: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Hours of price history before news to analyze (1-168 hours)"
    )
    hours_after: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Hours of price history after news to analyze (1-168 hours)"
    )
    prediction_horizon: Literal["1h", "4h", "24h", "7d"] = Field(
        default="24h",
        description="Time horizon for trend prediction"
    )


class TrendPrediction(BaseSchema):
    """Predicted trend with reasoning."""

    direction: Literal["UP", "DOWN", "NEUTRAL"] = Field(
        ...,
        description="Predicted price direction"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in prediction (0.0-1.0)"
    )
    expected_change_percent: float = Field(
        ...,
        description="Expected percentage change (can be negative)"
    )
    reasoning: str = Field(
        ...,
        min_length=50,
        description="Detailed reasoning for the prediction"
    )
    key_factors: list[str] = Field(
        ...,
        min_items=1,
        max_items=5,
        description="Key factors influencing the prediction"
    )


class CausalRelationship(BaseSchema):
    """Identified causal relationship between news and price."""

    relationship_type: Literal["STRONG", "MODERATE", "WEAK", "NONE"] = Field(
        ...,
        description="Strength of causal relationship"
    )
    correlation_score: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Correlation between news sentiment and price movement"
    )
    explanation: str = Field(
        ...,
        min_length=50,
        description="Explanation of the causal relationship"
    )
    evidence_points: list[str] = Field(
        ...,
        min_items=1,
        max_items=5,
        description="Specific evidence supporting the relationship"
    )


class CausalAnalysisResult(BaseSchema):
    """Result of causal analysis."""

    news_article_id: int | None = None
    symbol: str
    news_published_at: datetime
    analysis_timestamp: datetime
    
    # Price context
    price_before_news: float = Field(..., description="Price before news publication")
    price_after_news: float | None = Field(None, description="Price after news (if available)")
    price_change_percent: float | None = Field(None, description="Actual price change percentage")
    
    # Sentiment analysis
    sentiment_label: str
    sentiment_score: float
    
    # Causal analysis
    causal_relationship: CausalRelationship
    
    # Trend prediction
    trend_prediction: TrendPrediction
    
    # Historical context
    price_history_before: list[PriceDataPoint] = Field(
        ...,
        description="Price history before news"
    )
    price_history_after: list[PriceDataPoint] = Field(
        default_factory=list,
        description="Price history after news (if available)"
    )
    
    # Metadata
    model_version: str
    analysis_metadata: dict | None = None


class CausalAnalysisResponse(BaseSchema):
    """API response for causal analysis."""

    success: bool = True
    data: CausalAnalysisResult
    message: str | None = None
