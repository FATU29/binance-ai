"""Service for causal analysis of news with price history using AI models."""

import json
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
import structlog
from openai import AsyncOpenAI

from app.core.config import settings
from app.schemas.causal_analysis import (
    CausalAnalysisRequest,
    CausalAnalysisResult,
    CausalRelationship,
    PriceDataPoint,
    TrendPrediction,
)
from app.schemas.sentiment import SentimentAnalysisResult
from app.services.news import news_article
from app.services.sentiment_service import sentiment_service

logger = structlog.get_logger()


class CausalAnalysisService:
    """Service for performing causal analysis between news and price movements."""

    def __init__(self) -> None:
        """Initialize causal analysis service."""
        self.model_version = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS * 3  # More tokens for complex analysis
        self.temperature = settings.OPENAI_TEMPERATURE
        self.client: AsyncOpenAI | None = None
        
        # Binance API base URL
        self.binance_api_base = "https://api.binance.com/api/v3"
        
        if settings.OPENAI_API_KEY:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info(
                "Causal analysis service initialized",
                model=self.model_version,
            )
        else:
            logger.warning(
                "OpenAI API key not found. Causal analysis will use fallback method."
            )

    async def fetch_price_history(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        interval: str = "1h"
    ) -> list[PriceDataPoint]:
        """
        Fetch price history from Binance API.
        
        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT)
            start_time: Start timestamp
            end_time: End timestamp
            interval: Kline interval (1m, 5m, 15m, 1h, 4h, 1d, etc.)
        
        Returns:
            List of price data points
        """
        try:
            # Normalize datetimes to UTC timezone-aware
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            else:
                start_time = start_time.astimezone(timezone.utc)
            
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=timezone.utc)
            else:
                end_time = end_time.astimezone(timezone.utc)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {
                    "symbol": symbol.upper(),
                    "interval": interval,
                    "startTime": int(start_time.timestamp() * 1000),
                    "endTime": int(end_time.timestamp() * 1000),
                    "limit": 1000,
                }
                
                response = await client.get(
                    f"{self.binance_api_base}/klines",
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                
                price_points = []
                for kline in data:
                    price_points.append(PriceDataPoint(
                        timestamp=datetime.fromtimestamp(kline[0] / 1000, tz=timezone.utc),
                        open=float(kline[1]),
                        high=float(kline[2]),
                        low=float(kline[3]),
                        close=float(kline[4]),
                        volume=float(kline[5]),
                    ))
                
                logger.info(
                    "Fetched price history",
                    symbol=symbol,
                    points=len(price_points),
                    interval=interval,
                )
                
                return price_points
                
        except Exception as e:
            logger.error(
                "Failed to fetch price history",
                symbol=symbol,
                error=str(e),
                error_type=type(e).__name__,
            )
            return []

    async def analyze_causal_relationship_direct(
        self,
        title: str,
        content: str,
        published_at: datetime,
        symbol: str,
        hours_before: int = 24,
        hours_after: int = 24,
        prediction_horizon: str = "24h",
    ) -> CausalAnalysisResult:
        """
        Perform causal analysis with direct news content (no DB required).
        
        This method:
        1. Analyzes sentiment from news content
        2. Fetches price history before and after news
        3. Uses AI to identify causal relationships
        4. Predicts future trend with reasoning
        """
        # Analyze sentiment
        from app.schemas.sentiment import SentimentAnalysisRequest
        sentiment_request = SentimentAnalysisRequest(
            text=f"{title}\n\n{content}"
        )
        sentiment_result: SentimentAnalysisResult = await sentiment_service.analyze_text(
            sentiment_request
        )
        
        # Normalize published_at to UTC timezone-aware datetime
        if published_at.tzinfo is None:
            # If naive, assume it's UTC
            published_at = published_at.replace(tzinfo=timezone.utc)
        else:
            # If aware, convert to UTC
            published_at = published_at.astimezone(timezone.utc)
        
        # Calculate time windows
        time_before = published_at - timedelta(hours=hours_before)
        time_after = published_at + timedelta(hours=hours_after)
        now = datetime.now(timezone.utc)
        
        # Fetch price history before news
        price_history_before = await self.fetch_price_history(
            symbol,
            time_before,
            published_at,
            interval="1h"
        )
        
        # Fetch price history after news (if available)
        price_history_after = []
        if now > published_at:
            end_time = min(time_after, now)
            price_history_after = await self.fetch_price_history(
                symbol,
                published_at,
                end_time,
                interval="1h"
            )
        
        # Get price before and after
        price_before = price_history_before[-1].close if price_history_before else 0.0
        price_after = price_history_after[-1].close if price_history_after else None
        price_change_percent = None
        if price_after and price_before > 0:
            price_change_percent = ((price_after - price_before) / price_before) * 100
        
        # Create a simple article-like object for AI analysis
        class SimpleArticle:
            def __init__(self, title: str, content: str, published_at: datetime):
                self.title = title
                self.content = content
                self.published_at = published_at
                self.id = 0
        
        article = SimpleArticle(title, content, published_at)
        
        # Perform AI causal analysis
        if self.client and settings.OPENAI_API_KEY:
            causal_relationship, trend_prediction = await self._analyze_with_ai(
                article=article,
                sentiment_result=sentiment_result,
                price_history_before=price_history_before,
                price_history_after=price_history_after,
                price_before=price_before,
                price_after=price_after,
                prediction_horizon=prediction_horizon,
            )
        else:
            # Fallback analysis
            causal_relationship, trend_prediction = await self._analyze_fallback(
                sentiment_result=sentiment_result,
                price_history_before=price_history_before,
                price_history_after=price_history_after,
                price_before=price_before,
                price_after=price_after,
            )
        
        return CausalAnalysisResult(
            news_article_id=None,
            symbol=symbol,
            news_published_at=published_at,
            analysis_timestamp=datetime.now(timezone.utc),
            price_before_news=price_before,
            price_after_news=price_after,
            price_change_percent=price_change_percent,
            sentiment_label=sentiment_result.sentiment_label,
            sentiment_score=sentiment_result.sentiment_score,
            causal_relationship=causal_relationship,
            trend_prediction=trend_prediction,
            price_history_before=price_history_before,
            price_history_after=price_history_after,
            model_version=sentiment_result.model_version,
        )

    async def analyze_causal_relationship(
        self,
        request: CausalAnalysisRequest,
        db: Any,
    ) -> CausalAnalysisResult:
        """
        Perform causal analysis between news and price movements.
        
        This method:
        1. Fetches the news article
        2. Analyzes sentiment
        3. Fetches price history before and after news
        4. Uses AI to identify causal relationships
        5. Predicts future trend with reasoning
        """
        # Fetch news article
        article = await news_article.get(db, request.news_article_id)
        if not article:
            raise ValueError(f"News article {request.news_article_id} not found")
        
        news_time = article.published_at or article.created_at
        
        # Normalize news_time to UTC timezone-aware datetime
        if news_time.tzinfo is None:
            # If naive, assume it's UTC
            news_time = news_time.replace(tzinfo=timezone.utc)
        else:
            # If aware, convert to UTC
            news_time = news_time.astimezone(timezone.utc)
        
        # Analyze sentiment
        from app.schemas.sentiment import SentimentAnalysisRequest
        sentiment_request = SentimentAnalysisRequest(
            text=f"{article.title}\n\n{article.content}"
        )
        sentiment_result: SentimentAnalysisResult = await sentiment_service.analyze_text(
            sentiment_request
        )
        
        # Calculate time windows
        time_before = news_time - timedelta(hours=request.hours_before)
        time_after = news_time + timedelta(hours=request.hours_after)
        now = datetime.now(timezone.utc)
        
        # Fetch price history before news
        price_history_before = await self.fetch_price_history(
            request.symbol,
            time_before,
            news_time,
            interval="1h"
        )
        
        # Fetch price history after news (if available)
        price_history_after = []
        if now > news_time:
            end_time = min(time_after, now)
            price_history_after = await self.fetch_price_history(
                request.symbol,
                news_time,
                end_time,
                interval="1h"
            )
        
        # Get price before and after
        price_before = price_history_before[-1].close if price_history_before else 0.0
        price_after = price_history_after[-1].close if price_history_after else None
        price_change_percent = None
        if price_after and price_before > 0:
            price_change_percent = ((price_after - price_before) / price_before) * 100
        
        # Perform AI causal analysis
        if self.client and settings.OPENAI_API_KEY:
            causal_relationship, trend_prediction = await self._analyze_with_ai(
                article=article,
                sentiment_result=sentiment_result,
                price_history_before=price_history_before,
                price_history_after=price_history_after,
                price_before=price_before,
                price_after=price_after,
                prediction_horizon=request.prediction_horizon,
            )
        else:
            # Fallback analysis
            causal_relationship, trend_prediction = await self._analyze_fallback(
                sentiment_result=sentiment_result,
                price_history_before=price_history_before,
                price_history_after=price_history_after,
                price_before=price_before,
                price_after=price_after,
            )
        
        return CausalAnalysisResult(
            news_article_id=request.news_article_id,
            symbol=request.symbol,
            news_published_at=news_time,
            analysis_timestamp=datetime.now(timezone.utc),
            price_before_news=price_before,
            price_after_news=price_after,
            price_change_percent=price_change_percent,
            sentiment_label=sentiment_result.sentiment_label,
            sentiment_score=sentiment_result.sentiment_score,
            causal_relationship=causal_relationship,
            trend_prediction=trend_prediction,
            price_history_before=price_history_before,
            price_history_after=price_history_after,
            model_version=sentiment_result.model_version,
        )

    async def _analyze_with_ai(
        self,
        article: Any,
        sentiment_result: SentimentAnalysisResult,
        price_history_before: list[PriceDataPoint],
        price_history_after: list[PriceDataPoint],
        price_before: float,
        price_after: float | None,
        prediction_horizon: str,
    ) -> tuple[CausalRelationship, TrendPrediction]:
        """Perform AI-powered causal analysis using OpenAI."""
        try:
            # Prepare price data summary
            price_summary_before = self._summarize_price_data(price_history_before)
            price_summary_after = self._summarize_price_data(price_history_after) if price_history_after else None
            
            # Construct comprehensive prompt
            system_prompt = """You are an expert financial analyst specializing in cryptocurrency market analysis and causal inference.

Your task is to:
1. Analyze the causal relationship between news events and price movements
2. Predict future price trends with detailed reasoning
3. Identify key factors influencing the market

Consider:
- News sentiment and its alignment with price movements
- Historical price patterns before and after news
- Market context and volatility
- Correlation strength between news and price action
- Potential confounding factors

Respond with valid JSON containing:
- causal_relationship: {
    relationship_type: "STRONG" | "MODERATE" | "WEAK" | "NONE",
    correlation_score: float (-1.0 to 1.0),
    explanation: string (detailed explanation),
    evidence_points: array of strings (specific evidence)
  }
- trend_prediction: {
    direction: "UP" | "DOWN" | "NEUTRAL",
    confidence: float (0.0 to 1.0),
    expected_change_percent: float (can be negative),
    reasoning: string (detailed reasoning, 200+ words),
    key_factors: array of 3-5 strings
  }

Respond ONLY with valid JSON, no additional text."""

            user_prompt = f"""Analyze the causal relationship and predict future trend:

NEWS ARTICLE:
Title: {article.title}
Content: {article.content[:2000]}...
Published: {article.published_at}

SENTIMENT ANALYSIS:
Label: {sentiment_result.sentiment_label}
Score: {sentiment_result.sentiment_score:.2f}
Confidence: {sentiment_result.confidence:.2f}

PRICE HISTORY BEFORE NEWS ({len(price_history_before)} data points):
{price_summary_before}
Price at news time: ${price_before:.2f}

PRICE HISTORY AFTER NEWS ({len(price_history_after) if price_history_after else 0} data points):
{price_summary_after if price_summary_after else "Not enough data yet"}
{'' if not price_after else f'Current price: ${price_after:.2f} (Change: {((price_after - price_before) / price_before * 100):.2f}%)'}

PREDICTION HORIZON: {prediction_horizon}

Provide detailed causal analysis and trend prediction."""

            logger.info(
                "Calling OpenAI for causal analysis",
                model=self.model_version,
                article_id=article.id,
            )

            response = await self.client.chat.completions.create(
                model=self.model_version,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")

            result_data = json.loads(content)

            # Parse causal relationship
            causal_data = result_data.get("causal_relationship", {})
            causal_relationship = CausalRelationship(
                relationship_type=causal_data.get("relationship_type", "NONE"),
                correlation_score=float(causal_data.get("correlation_score", 0.0)),
                explanation=causal_data.get("explanation", "No explanation provided"),
                evidence_points=causal_data.get("evidence_points", []),
            )

            # Parse trend prediction
            prediction_data = result_data.get("trend_prediction", {})
            trend_prediction = TrendPrediction(
                direction=prediction_data.get("direction", "NEUTRAL"),
                confidence=float(prediction_data.get("confidence", 0.5)),
                expected_change_percent=float(prediction_data.get("expected_change_percent", 0.0)),
                reasoning=prediction_data.get("reasoning", "No reasoning provided"),
                key_factors=prediction_data.get("key_factors", []),
            )

            logger.info(
                "AI causal analysis completed",
                relationship_type=causal_relationship.relationship_type,
                trend_direction=trend_prediction.direction,
                confidence=trend_prediction.confidence,
            )

            return causal_relationship, trend_prediction

        except Exception as e:
            logger.error(
                "AI causal analysis failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            # Fallback to simple analysis
            return await self._analyze_fallback(
                sentiment_result,
                price_history_before,
                price_history_after,
                price_before,
                price_after,
            )

    def _summarize_price_data(self, price_data: list[PriceDataPoint]) -> str:
        """Summarize price data for AI prompt."""
        if not price_data:
            return "No price data available"
        
        prices = [p.close for p in price_data]
        volumes = [p.volume for p in price_data]
        
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        price_change = ((prices[-1] - prices[0]) / prices[0] * 100) if prices[0] > 0 else 0
        avg_volume = sum(volumes) / len(volumes) if volumes else 0
        
        return f"""Period: {price_data[0].timestamp} to {price_data[-1].timestamp}
Price range: ${min_price:.2f} - ${max_price:.2f}
Average price: ${avg_price:.2f}
Price change: {price_change:.2f}%
Average volume: {avg_volume:.2f}
Data points: {len(price_data)}"""

    async def _analyze_fallback(
        self,
        sentiment_result: SentimentAnalysisResult,
        price_history_before: list[PriceDataPoint],
        price_history_after: list[PriceDataPoint],
        price_before: float,
        price_after: float | None,
    ) -> tuple[CausalRelationship, TrendPrediction]:
        """Fallback analysis when AI is not available."""
        # Simple correlation based on sentiment and price movement
        price_change = 0.0
        if price_after and price_before > 0:
            price_change = ((price_after - price_before) / price_before) * 100
        
        # Determine relationship strength
        sentiment_numeric = sentiment_result.sentiment_score - 0.5  # -0.5 to 0.5
        price_change_normalized = price_change / 10.0  # Normalize to similar scale
        
        correlation = sentiment_numeric * (price_change_normalized / 0.5) if price_change_normalized != 0 else 0.0
        correlation = max(-1.0, min(1.0, correlation))
        
        if abs(correlation) > 0.7:
            relationship_type = "STRONG"
        elif abs(correlation) > 0.4:
            relationship_type = "MODERATE"
        elif abs(correlation) > 0.1:
            relationship_type = "WEAK"
        else:
            relationship_type = "NONE"
        
        causal_relationship = CausalRelationship(
            relationship_type=relationship_type,
            correlation_score=correlation,
            explanation=f"Fallback analysis: Sentiment score {sentiment_result.sentiment_score:.2f} shows {'positive' if sentiment_result.sentiment_score > 0.5 else 'negative'} sentiment. "
                       f"Price changed by {price_change:.2f}%. Correlation: {correlation:.2f}.",
            evidence_points=[
                f"Sentiment: {sentiment_result.sentiment_label}",
                f"Price change: {price_change:.2f}%",
                f"Correlation: {correlation:.2f}",
            ],
        )
        
        # Simple trend prediction
        if sentiment_result.sentiment_score > 0.6:
            direction = "UP"
            expected_change = 2.0
        elif sentiment_result.sentiment_score < 0.4:
            direction = "DOWN"
            expected_change = -2.0
        else:
            direction = "NEUTRAL"
            expected_change = 0.0
        
        trend_prediction = TrendPrediction(
            direction=direction,
            confidence=0.6,
            expected_change_percent=expected_change,
            reasoning=f"Based on sentiment analysis ({sentiment_result.sentiment_label}), the market is expected to move {direction.lower()}. "
                     f"This is a simplified prediction using sentiment score of {sentiment_result.sentiment_score:.2f}.",
            key_factors=[
                f"News sentiment: {sentiment_result.sentiment_label}",
                f"Sentiment score: {sentiment_result.sentiment_score:.2f}",
            ],
        )
        
        return causal_relationship, trend_prediction


# Singleton instance
causal_analysis_service = CausalAnalysisService()

