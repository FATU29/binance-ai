"""Schemas for price prediction using news sentiment analysis."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class NewsSummary(BaseModel):
    """Summary of a news article for prediction."""
    
    id: str
    title: str
    summary: str
    source: str
    published_at: datetime
    sentiment: dict
    related_pairs: list[str]


class PricePredictionRequest(BaseModel):
    """Request for price prediction based on news sentiment."""
    
    symbol: str = Field(
        ...,
        description="Trading pair symbol (e.g., BTCUSDT, ETHUSDT)",
        examples=["BTCUSDT", "ETHUSDT"]
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of recent news articles to analyze"
    )
    include_historical_price: bool = Field(
        default=False,
        description="Whether to include historical price data in analysis"
    )


class PricePredictionResult(BaseModel):
    """Result of price prediction analysis."""
    
    symbol: str
    prediction: str = Field(
        ...,
        description="Predicted price direction: 'bullish', 'bearish', or 'neutral'"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence level of the prediction (0.0 to 1.0)"
    )
    sentiment_summary: dict = Field(
        ...,
        description="Summary of sentiment analysis from news articles"
    )
    reasoning: str = Field(
        ...,
        description="Detailed reasoning for the prediction based on news analysis"
    )
    key_factors: list[str] = Field(
        ...,
        description="Key factors influencing the prediction"
    )
    news_analyzed: int = Field(
        ...,
        description="Number of news articles analyzed"
    )
    analyzed_at: datetime
    model_version: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model version used for analysis"
    )


class PricePredictionResponse(BaseModel):
    """Response containing price prediction result and news data."""
    
    success: bool = True
    prediction: PricePredictionResult
    news_articles: list[NewsSummary]
    historical_price: Optional[dict] = Field(
        default=None,
        description="Historical price data if requested"
    )


class LongPollingPredictionRequest(BaseModel):
    """Request for long-polling price prediction."""
    
    symbol: str = Field(
        ...,
        description="Trading pair symbol (e.g., BTCUSDT, ETHUSDT)",
        examples=["BTCUSDT", "ETHUSDT"]
    )
    last_prediction_time: Optional[datetime] = Field(
        default=None,
        description="Timestamp of the last prediction received by client"
    )
    timeout: int = Field(
        default=90,
        ge=30,
        le=120,
        description="Maximum time to wait for new data (30-120 seconds)"
    )


class LongPollingPredictionResponse(BaseModel):
    """Response for long-polling price prediction."""
    
    success: bool = True
    has_new_data: bool = Field(
        ...,
        description="Whether new prediction data is available"
    )
    prediction: Optional[PricePredictionResult] = Field(
        default=None,
        description="Price prediction result if available"
    )
    cache_hit: bool = Field(
        default=False,
        description="Whether this prediction was retrieved from cache"
    )
    next_poll_after: int = Field(
        default=5,
        description="Recommended seconds to wait before next poll"
    )
