"""Service for price prediction based on news sentiment analysis."""

import json
from datetime import datetime, timezone
from typing import Any

import httpx
import structlog
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from app.core.config import settings
from app.schemas.price_prediction import (
    NewsSummary,
    PricePredictionRequest,
    PricePredictionResult,
)

logger = structlog.get_logger()


class PricePredictionService:
    """Service for predicting price movements based on news sentiment."""

    def __init__(self) -> None:
        """Initialize price prediction service."""
        self.model_version = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE
        self.client: AsyncOpenAI | None = None
        self.crawler_base_url = settings.CRAWLER_SERVICE_URL
        
        # Initialize OpenAI client if API key is available
        if settings.OPENAI_API_KEY:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info(
                "Price prediction service initialized",
                model=self.model_version,
                crawler_url=self.crawler_base_url,
            )
        else:
            logger.warning(
                "OpenAI API key not found. Price prediction will not be available."
            )

    async def fetch_latest_news(self, symbol: str, limit: int) -> list[dict]:
        """
        Fetch latest news from crawler service.
        
        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT)
            limit: Number of articles to fetch
            
        Returns:
            List of news articles
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"{self.crawler_base_url}/api/v1/news/latest/{symbol}"
                params = {"limit": limit}
                
                logger.info(
                    "Fetching latest news from crawler",
                    symbol=symbol,
                    limit=limit,
                    url=url,
                )
                
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                if data.get("success") and "data" in data:
                    items = data["data"].get("items", [])
                    logger.info(
                        "Successfully fetched news from crawler",
                        symbol=symbol,
                        count=len(items),
                    )
                    return items
                else:
                    logger.error("Invalid response format from crawler", data=data)
                    return []
                    
        except httpx.HTTPError as e:
            logger.error(
                "Failed to fetch news from crawler",
                symbol=symbol,
                error=str(e),
            )
            raise
        except Exception as e:
            logger.error(
                "Unexpected error fetching news",
                symbol=symbol,
                error=str(e),
            )
            raise

    async def predict_price(
        self, request: PricePredictionRequest
    ) -> tuple[PricePredictionResult, list[NewsSummary]]:
        """
        Predict price movement based on news sentiment.
        
        Args:
            request: Price prediction request
            
        Returns:
            Tuple of (prediction result, news articles analyzed)
        """
        if not self.client or not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key not configured")
        
        # Fetch latest news
        news_items = await self.fetch_latest_news(request.symbol, request.limit)
        
        if not news_items:
            raise ValueError(f"No news articles found for symbol {request.symbol}")
        
        # Convert to NewsSummary objects
        news_summaries = [
            NewsSummary(
                id=item["id"],
                title=item["title"],
                summary=item.get("summary", ""),
                source=item["source"],
                published_at=datetime.fromisoformat(
                    item["published_at"].replace("Z", "+00:00")
                ),
                sentiment=item.get("sentiment", {}),
                related_pairs=item.get("related_pairs", []),
            )
            for item in news_items
        ]
        
        # Prepare news text for analysis
        news_text = self._format_news_for_analysis(news_summaries)
        
        # Call OpenAI for prediction
        prediction = await self._analyze_with_openai(request.symbol, news_text, len(news_summaries))
        
        return prediction, news_summaries

    def _format_news_for_analysis(self, news: list[NewsSummary]) -> str:
        """Format news articles for OpenAI analysis."""
        formatted = []
        for i, article in enumerate(news, 1):
            sentiment = article.sentiment
            formatted.append(
                f"[Article {i}]\n"
                f"Title: {article.title}\n"
                f"Summary: {article.summary}\n"
                f"Source: {article.source}\n"
                f"Published: {article.published_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
                f"Current Sentiment: {sentiment.get('label', 'unknown')} "
                f"(score: {sentiment.get('score', 0):.2f}, "
                f"confidence: {sentiment.get('confidence', 0):.2f})\n"
            )
        return "\n\n".join(formatted)

    async def _analyze_with_openai(
        self, symbol: str, news_text: str, news_count: int
    ) -> PricePredictionResult:
        """
        Analyze news and predict price movement using OpenAI.
        
        Args:
            symbol: Trading pair symbol
            news_text: Formatted news text
            news_count: Number of news articles
            
        Returns:
            Price prediction result
        """
        try:
            system_prompt = """You are an expert cryptocurrency market analyst specializing in news-based price prediction.

Analyze the provided news articles about a cryptocurrency trading pair and predict the likely price movement.

Your analysis should consider:
1. Overall sentiment trend across all articles
2. Impact level of each news item (market-moving vs routine news)
3. Recency and timing of news (more recent = higher weight)
4. Credibility of sources
5. Correlation between news sentiment and typical market reactions
6. Any conflicting signals or mixed sentiment

Respond with ONLY valid JSON in this exact format:
{
    "prediction": "bullish" | "bearish" | "neutral",
    "confidence": 0.0 to 1.0,
    "sentiment_summary": {
        "overall_sentiment": "positive" | "negative" | "mixed" | "neutral",
        "bullish_signals": number,
        "bearish_signals": number,
        "neutral_signals": number,
        "sentiment_score": -1.0 to 1.0
    },
    "reasoning": "Detailed explanation of your prediction based on the news analysis",
    "key_factors": ["factor 1", "factor 2", "factor 3"]
}

Guidelines:
- "bullish" prediction suggests price increase likely
- "bearish" prediction suggests price decrease likely  
- "neutral" suggests no clear direction or balanced signals
- Confidence should reflect certainty based on signal strength and consistency
- Key factors should be specific, actionable insights from the news"""

            user_prompt = f"""Analyze these {news_count} recent news articles for {symbol} and predict the price movement:

{news_text}

Provide your prediction in JSON format."""

            logger.info(
                "Calling OpenAI for price prediction",
                symbol=symbol,
                news_count=news_count,
                model=self.model_version,
            )

            response: ChatCompletion = await self.client.chat.completions.create(
                model=self.model_version,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"},
            )

            # Parse response
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")

            result = json.loads(content)
            
            logger.info(
                "Price prediction completed",
                symbol=symbol,
                prediction=result.get("prediction"),
                confidence=result.get("confidence"),
            )

            return PricePredictionResult(
                symbol=symbol,
                prediction=result["prediction"],
                confidence=result["confidence"],
                sentiment_summary=result["sentiment_summary"],
                reasoning=result["reasoning"],
                key_factors=result["key_factors"],
                news_analyzed=news_count,
                analyzed_at=datetime.now(timezone.utc),
                model_version=self.model_version,
            )

        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse OpenAI response as JSON",
                error=str(e),
                content=content if 'content' in locals() else None,
            )
            raise ValueError(f"Invalid JSON response from OpenAI: {e}")
        except Exception as e:
            logger.error(
                "Error during OpenAI analysis",
                symbol=symbol,
                error=str(e),
            )
            raise


# Global instance
price_prediction_service = PricePredictionService()
