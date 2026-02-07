"""Service for generating AI prediction line data for chart overlay."""

import json
from datetime import datetime, timezone

import httpx
import structlog
from openai import AsyncOpenAI

from app.core.config import settings
from app.schemas.price_prediction import (
    PredictionLinePoint,
    PredictionLineRequest,
    PredictionLineResponse,
)

logger = structlog.get_logger()

# Interval -> seconds per candle
INTERVAL_SECONDS: dict[str, int] = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1h": 3600,
    "4h": 14400,
    "1d": 86400,
    "1w": 604800,
}


class PredictionLineService:
    """Generates a predicted price line based on news sentiment + recent price action."""

    def __init__(self) -> None:
        self.model_version = settings.OPENAI_MODEL
        self.client: AsyncOpenAI | None = None
        self.crawler_base_url = settings.CRAWLER_SERVICE_URL

        if settings.OPENAI_API_KEY:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info("PredictionLineService initialized", model=self.model_version)
        else:
            logger.warning("OpenAI API key not found. Prediction line will not be available.")

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    async def generate_prediction_line(
        self, request: PredictionLineRequest
    ) -> PredictionLineResponse:
        """Generate a prediction line for chart overlay.

        1. Fetch recent klines from Binance for context
        2. Fetch latest news from crawler service
        3. Ask OpenAI to predict future prices
        4. Return structured line data
        """
        if not self.client or not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key not configured")

        interval_sec = INTERVAL_SECONDS.get(request.interval)
        if interval_sec is None:
            raise ValueError(
                f"Unsupported interval '{request.interval}'. "
                f"Supported: {', '.join(INTERVAL_SECONDS.keys())}"
            )

        # Parallel data fetching
        recent_klines = await self._fetch_recent_klines(
            request.symbol, request.interval, limit=50
        )
        news_items = await self._fetch_latest_news(request.symbol, request.news_limit)

        if not recent_klines:
            raise ValueError(f"Could not fetch recent price data for {request.symbol}")

        current_price = recent_klines[-1]["close"]
        current_time = recent_klines[-1]["time"]

        # Build context for AI
        price_context = self._format_price_context(recent_klines[-20:])
        news_context = self._format_news_context(news_items) if news_items else "No recent news available."

        # Call OpenAI
        ai_result = await self._predict_with_openai(
            symbol=request.symbol,
            interval=request.interval,
            periods=request.periods,
            current_price=current_price,
            price_context=price_context,
            news_context=news_context,
        )

        # Build prediction line points
        points: list[PredictionLinePoint] = []
        for i, predicted_price in enumerate(ai_result["predicted_prices"], start=1):
            points.append(
                PredictionLinePoint(
                    time=current_time + i * interval_sec,
                    value=round(predicted_price, 2),
                )
            )

        return PredictionLineResponse(
            success=True,
            symbol=request.symbol,
            interval=request.interval,
            current_price=current_price,
            current_time=current_time,
            prediction_line=points,
            direction=ai_result["direction"],
            confidence=ai_result["confidence"],
            reasoning=ai_result["reasoning"],
            news_analyzed=len(news_items) if news_items else 0,
            model_version=self.model_version,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    # ------------------------------------------------------------------
    # Data fetching helpers
    # ------------------------------------------------------------------

    async def _fetch_recent_klines(
        self, symbol: str, interval: str, limit: int = 50
    ) -> list[dict]:
        """Fetch recent klines from Binance public API."""
        try:
            url = "https://api.binance.com/api/v3/klines"
            params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}

            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()

            return [
                {
                    "time": int(k[0]) // 1000,
                    "open": float(k[1]),
                    "high": float(k[2]),
                    "low": float(k[3]),
                    "close": float(k[4]),
                    "volume": float(k[5]),
                }
                for k in data
            ]
        except Exception as e:
            logger.error("Failed to fetch klines", symbol=symbol, error=str(e))
            return []

    async def _fetch_latest_news(self, symbol: str, limit: int) -> list[dict]:
        """Fetch latest news from crawler service."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"{self.crawler_base_url}/api/v1/news/latest/{symbol}"
                resp = await client.get(url, params={"limit": limit})
                resp.raise_for_status()
                data = resp.json()

                if data.get("success") and "data" in data:
                    return data["data"].get("items", [])
                return []
        except Exception as e:
            logger.warning("Could not fetch news, continuing without", error=str(e))
            return []

    # ------------------------------------------------------------------
    # Formatting helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_price_context(klines: list[dict]) -> str:
        lines = []
        for k in klines:
            dt = datetime.fromtimestamp(k["time"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
            lines.append(
                f"{dt} | O:{k['open']:.2f} H:{k['high']:.2f} L:{k['low']:.2f} C:{k['close']:.2f} V:{k['volume']:.0f}"
            )
        return "\n".join(lines)

    @staticmethod
    def _format_news_context(news_items: list[dict]) -> str:
        parts = []
        for i, item in enumerate(news_items[:15], 1):
            sentiment = item.get("sentiment", {})
            parts.append(
                f"[{i}] {item.get('title', 'N/A')} "
                f"(sentiment: {sentiment.get('label', 'unknown')}, "
                f"score: {sentiment.get('score', 0):.2f})"
            )
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # OpenAI prediction
    # ------------------------------------------------------------------

    async def _predict_with_openai(
        self,
        *,
        symbol: str,
        interval: str,
        periods: int,
        current_price: float,
        price_context: str,
        news_context: str,
    ) -> dict:
        """Ask OpenAI to predict future price points."""

        system_prompt = f"""You are an expert quantitative crypto analyst.
Given recent price history and current news sentiment for {symbol}, predict the next {periods} candle close prices on the {interval} timeframe.

RULES:
1. Predictions must be realistic — avoid extreme moves unless news justifies it.
2. Use the price history trend, support/resistance levels, and news sentiment together.
3. Each predicted price should be a float. The first predicted price should be close to the current price.
4. Return ONLY valid JSON matching this exact schema:

{{
  "direction": "bullish" | "bearish" | "neutral",
  "confidence": 0.0 to 1.0,
  "reasoning": "1-2 sentence explanation",
  "predicted_prices": [<float>, <float>, ...]
}}

The "predicted_prices" array must have exactly {periods} elements — one predicted close price per future candle period.
Current price is {current_price:.2f}."""

        user_prompt = f"""Recent {interval} candles for {symbol}:
{price_context}

Latest news:
{news_context}

Predict the next {periods} candle close prices."""

        logger.info(
            "Calling OpenAI for prediction line",
            symbol=symbol,
            interval=interval,
            periods=periods,
        )

        response = await self.client.chat.completions.create(
            model=self.model_version,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=settings.OPENAI_MAX_TOKENS * 4,  # need room for the array
            temperature=settings.OPENAI_TEMPERATURE,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from OpenAI")

        result = json.loads(content)

        # Validate
        prices = result.get("predicted_prices", [])
        if not prices or len(prices) < 2:
            raise ValueError("OpenAI returned insufficient predicted prices")

        # Ensure correct length — pad or trim
        if len(prices) < periods:
            last = prices[-1]
            prices.extend([last] * (periods - len(prices)))
        elif len(prices) > periods:
            prices = prices[:periods]

        result["predicted_prices"] = [float(p) for p in prices]
        result.setdefault("direction", "neutral")
        result.setdefault("confidence", 0.5)
        result.setdefault("reasoning", "AI prediction based on price action and news sentiment.")

        logger.info(
            "Prediction line generated",
            symbol=symbol,
            direction=result["direction"],
            points=len(result["predicted_prices"]),
        )

        return result


# Global instance
prediction_line_service = PredictionLineService()
