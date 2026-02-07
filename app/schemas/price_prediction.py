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
        default=10,
        ge=5,
        le=120,
        description="Request timeout (5-120 seconds, endpoint returns instantly from DB)"
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


# ============================================
# Prediction Line (Chart Overlay) Schemas
# ============================================


class PredictionLinePoint(BaseModel):
    """A single point on the prediction line."""

    time: int = Field(
        ...,
        description="Unix timestamp in seconds (matches lightweight-charts format)"
    )
    value: float = Field(
        ...,
        description="Predicted price value at this timestamp"
    )


class PredictionLineRequest(BaseModel):
    """Request for generating a price prediction line on the chart."""

    symbol: str = Field(
        ...,
        description="Trading pair symbol (e.g., BTCUSDT, ETHUSDT)",
        examples=["BTCUSDT", "ETHUSDT"],
    )
    interval: str = Field(
        default="1h",
        description="Chart timeframe interval (1m, 5m, 15m, 1h, 4h, 1d, 1w)",
        examples=["1m", "5m", "15m", "1h", "4h", "1d", "1w"],
    )
    periods: int = Field(
        default=24,
        ge=4,
        le=100,
        description="Number of future candle periods to predict",
    )
    news_limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of recent news articles to consider",
    )


class PredictionLineResponse(BaseModel):
    """Response containing the prediction line data for chart overlay."""

    success: bool = True
    symbol: str
    interval: str
    current_price: float = Field(
        ...,
        description="Current price at time of prediction (anchor point)"
    )
    current_time: int = Field(
        ...,
        description="Current timestamp in seconds (anchor point)"
    )
    prediction_line: list[PredictionLinePoint] = Field(
        ...,
        description="Array of predicted price points for the chart line"
    )
    direction: str = Field(
        ...,
        description="Overall predicted direction: bullish, bearish, or neutral"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence level of the prediction"
    )
    reasoning: str = Field(
        ...,
        description="Brief reasoning behind the prediction"
    )
    news_analyzed: int = Field(
        ...,
        description="Number of news articles analyzed"
    )
    model_version: str
    generated_at: str = Field(
        ...,
        description="ISO 8601 timestamp of when this prediction was generated"
    )
