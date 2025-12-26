"""Business logic for sentiment analysis using OpenAI."""

import json
from typing import Any

import structlog
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from app.core.config import settings
from app.schemas.sentiment import SentimentAnalysisRequest, SentimentAnalysisResult

logger = structlog.get_logger()


class SentimentService:
    """Service for performing sentiment analysis using OpenAI GPT models."""

    def __init__(self) -> None:
        """
        Initialize sentiment service with OpenAI client.
        
        Model configuration is loaded from settings (environment variables)
        to prevent client-side cost manipulation and ensure security.
        """
        self.model_version = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE
        self.client: AsyncOpenAI | None = None
        
        # Initialize OpenAI client if API key is available
        if settings.OPENAI_API_KEY:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info(
                "OpenAI client initialized",
                model=self.model_version,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
        else:
            logger.warning(
                "OpenAI API key not found. Sentiment analysis will use fallback method."
            )

    async def analyze_text(self, request: SentimentAnalysisRequest) -> SentimentAnalysisResult:
        """
        Analyze sentiment of text using OpenAI GPT models.

        Args:
            request: SentimentAnalysisRequest containing text to analyze

        Returns:
            SentimentAnalysisResult with sentiment label, score, and confidence
        """
        # Use OpenAI if available, otherwise fall back to keyword-based analysis
        if self.client and settings.OPENAI_API_KEY:
            return await self._analyze_with_openai(request)
        else:
            logger.info("Using fallback keyword-based sentiment analysis")
            return await self._analyze_with_keywords(request)

    async def _analyze_with_openai(
        self, request: SentimentAnalysisRequest
    ) -> SentimentAnalysisResult:
        """
        Analyze sentiment using OpenAI GPT models.

        This uses a structured prompt to get consistent JSON responses with
        sentiment classification for financial/crypto news.
        """
        try:
            # Construct prompt for crypto/financial sentiment analysis
            system_prompt = """You are an expert financial sentiment analyzer specializing in cryptocurrency and trading news.

Analyze the sentiment of the given text and respond with a JSON object containing:
- sentiment_label: one of "bullish", "bearish", "neutral", "positive", or "negative"
- sentiment_score: a float between 0.0 (most negative/bearish) and 1.0 (most positive/bullish)
- confidence: a float between 0.0 and 1.0 indicating your confidence in the analysis
- key_factors: a list of 2-3 key phrases or factors that influenced your decision

Consider:
- Financial terminology (bull/bear markets, support/resistance, etc.)
- Price action indicators (surge, crash, rally, decline)
- Market sentiment indicators (fear, greed, uncertainty, confidence)
- News impact (adoption, regulation, partnerships, security issues)

Respond ONLY with valid JSON, no additional text."""

            user_prompt = f"Analyze the sentiment of this text:\n\n{request.text}"

            # Call OpenAI API with server-controlled model version
            logger.info(
                "Calling OpenAI API for sentiment analysis",
                model=self.model_version,
                text_length=len(request.text),
            )

            response: ChatCompletion = await self.client.chat.completions.create(
                model=self.model_version,  # Use server-controlled model only
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,  # From settings
                max_tokens=self.max_tokens,    # From settings
                response_format={"type": "json_object"},  # Ensure JSON response
            )

            # Parse the response
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")

            result_data = json.loads(content)

            # Extract and validate data
            sentiment_label = result_data.get("sentiment_label", "neutral").lower()
            sentiment_score = float(result_data.get("sentiment_score", 0.5))
            confidence = float(result_data.get("confidence", 0.8))
            key_factors = result_data.get("key_factors", [])

            # Normalize sentiment score to 0-1 range
            sentiment_score = max(0.0, min(1.0, sentiment_score))
            confidence = max(0.0, min(1.0, confidence))

            # Build metadata
            metadata = json.dumps({
                "key_factors": key_factors,
                "model": response.model,
                "tokens_used": response.usage.total_tokens if response.usage else 0,
                "finish_reason": response.choices[0].finish_reason,
            })

            logger.info(
                "OpenAI sentiment analysis completed",
                sentiment=sentiment_label,
                score=sentiment_score,
                confidence=confidence,
            )

            return SentimentAnalysisResult(
                sentiment_label=sentiment_label,
                sentiment_score=sentiment_score,
                confidence=confidence,
                model_version=response.model,
            )

        except json.JSONDecodeError as e:
            logger.error("Failed to parse OpenAI response as JSON", error=str(e))
            # Fall back to keyword-based analysis
            return await self._analyze_with_keywords(request)

        except Exception as e:
            logger.error(
                "OpenAI sentiment analysis failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            # Fall back to keyword-based analysis
            return await self._analyze_with_keywords(request)

    async def _analyze_with_keywords(
        self, request: SentimentAnalysisRequest
    ) -> SentimentAnalysisResult:
        """
        Fallback keyword-based sentiment analysis.

        Used when OpenAI API is not available or fails.
        """
        text = request.text.lower()

        # Crypto/financial specific keywords
        bullish_keywords = [
            "bull", "bullish", "growth", "surge", "rally", "profit", "gain",
            "positive", "up", "rise", "pump", "moon", "breakout", "support",
            "buy", "accumulate", "hodl", "adoption", "partnership"
        ]
        bearish_keywords = [
            "bear", "bearish", "decline", "crash", "drop", "loss", "negative",
            "down", "fall", "dump", "dip", "breakdown", "resistance",
            "sell", "fear", "panic", "regulation", "hack", "scam"
        ]
        neutral_keywords = [
            "stable", "sideways", "consolidation", "range", "waiting",
            "uncertain", "mixed", "flat"
        ]

        # Count keyword occurrences
        bullish_count = sum(1 for keyword in bullish_keywords if keyword in text)
        bearish_count = sum(1 for keyword in bearish_keywords if keyword in text)
        neutral_count = sum(1 for keyword in neutral_keywords if keyword in text)

        # Determine sentiment
        if bullish_count > bearish_count and bullish_count > neutral_count:
            sentiment_label = "bullish"
            sentiment_score = min(0.5 + (bullish_count * 0.08), 0.95)
        elif bearish_count > bullish_count and bearish_count > neutral_count:
            sentiment_label = "bearish"
            sentiment_score = max(0.5 - (bearish_count * 0.08), 0.05)
        elif neutral_count > 0 and neutral_count >= bullish_count and neutral_count >= bearish_count:
            sentiment_label = "neutral"
            sentiment_score = 0.5
        elif bullish_count == bearish_count:
            sentiment_label = "neutral"
            sentiment_score = 0.5
        else:
            # Default case
            sentiment_label = "neutral"
            sentiment_score = 0.5

        # Calculate confidence based on keyword density
        total_keywords = bullish_count + bearish_count + neutral_count
        word_count = len(text.split())
        keyword_density = total_keywords / max(word_count, 1)
        confidence = min(0.5 + (keyword_density * 2), 0.85)  # Cap at 0.85 for fallback

        logger.info(
            "Keyword-based sentiment analysis completed",
            sentiment=sentiment_label,
            score=sentiment_score,
            bullish=bullish_count,
            bearish=bearish_count,
            neutral=neutral_count,
        )

        return SentimentAnalysisResult(
            sentiment_label=sentiment_label,
            sentiment_score=sentiment_score,
            confidence=confidence,
            model_version=f"keyword-fallback-{request.model_version or 'v1.0.0'}",
        )


# Singleton instance
sentiment_service = SentimentService()

