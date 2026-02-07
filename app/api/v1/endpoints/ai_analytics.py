"""Advanced sentiment analysis endpoints with OpenAI integration."""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import DBSession
from app.schemas.news import NewsArticleResponse
from app.schemas.price_prediction import (
    LongPollingPredictionRequest,
    LongPollingPredictionResponse,
    PredictionLineRequest,
    PredictionLineResponse,
    PricePredictionRequest,
    PricePredictionResponse,
)
from app.schemas.sentiment import (
    SentimentAnalysisCreate,
    SentimentAnalysisRequest,
    SentimentAnalysisResponse,
    SentimentAnalysisResult,
)
from app.services.long_polling_service import long_polling_service
from app.services.news import news_article
from app.services.prediction_line_service import prediction_line_service
from app.services.price_prediction_crud import price_prediction_crud
from app.services.price_prediction_service import price_prediction_service
from app.services.sentiment import sentiment_analysis
from app.services.sentiment_service import sentiment_service

router = APIRouter()


@router.post("/analyze/news/{article_id}", response_model=SentimentAnalysisResponse)
async def analyze_news_article(
    article_id: int,
    db: DBSession,
) -> SentimentAnalysisResponse:
    """
    Analyze sentiment of a news article and save the result.

    This endpoint:
    1. Fetches the news article from the database
    2. Analyzes its sentiment using OpenAI
    3. Saves the analysis result to the database
    4. Returns the complete analysis

    - **article_id**: The ID of the news article to analyze
    
    Note: Model version is controlled server-side for security and cost management.
    """
    # Fetch the news article
    article = await news_article.get(db, article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"News article with ID {article_id} not found",
        )

    # Create analysis request with article content
    # Model version controlled by server config, not client
    request = SentimentAnalysisRequest(
        text=f"{article.title}\n\n{article.content}",
    )

    # Analyze sentiment
    result = await sentiment_service.analyze_text(request)

    # Save analysis to database
    analysis_create = SentimentAnalysisCreate(
        news_article_id=article_id,
        sentiment_label=result.sentiment_label,
        sentiment_score=result.sentiment_score,
        confidence=result.confidence,
        model_version=result.model_version,
        analysis_metadata=None,  # Could add metadata here
    )

    created_analysis = await sentiment_analysis.create(db, obj_in=analysis_create)
    await db.commit()

    return SentimentAnalysisResponse.model_validate(created_analysis)


@router.post("/analyze/batch", response_model=list[SentimentAnalysisResult])
async def analyze_batch_texts(
    texts: list[str],
) -> list[SentimentAnalysisResult]:
    """
    Analyze sentiment of multiple texts in batch.

    This endpoint analyzes multiple texts without saving to database.
    Useful for real-time analysis or testing.

    - **texts**: List of text strings to analyze
    
    Note: Model version is controlled server-side for security and cost management.
    """
    if len(texts) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 texts allowed per batch request",
        )

    results = []
    for text in texts:
        request = SentimentAnalysisRequest(text=text)
        result = await sentiment_service.analyze_text(request)
        results.append(result)

    return results


@router.get("/news/{article_id}/latest", response_model=SentimentAnalysisResponse)
async def get_latest_sentiment_for_article(
    article_id: int,
    db: DBSession,
) -> SentimentAnalysisResponse:
    """
    Get the latest sentiment analysis for a news article.

    - **article_id**: The ID of the news article
    """
    # Check if article exists
    article = await news_article.get(db, article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"News article with ID {article_id} not found",
        )

    # Get latest analysis
    latest_analysis = await sentiment_analysis.get_latest_by_news_article(
        db, news_article_id=article_id
    )

    if not latest_analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No sentiment analysis found for article {article_id}",
        )

    return SentimentAnalysisResponse.model_validate(latest_analysis)


@router.post("/analyze/quick", response_model=SentimentAnalysisResult)
async def quick_sentiment_analysis(
    text: str,
    use_openai: bool = True,
) -> SentimentAnalysisResult:
    """
    Quick sentiment analysis without database storage.

    - **text**: Text to analyze
    - **use_openai**: Whether to use OpenAI (true) or fallback to keywords (false)
    
    Note: Model version is controlled server-side for security and cost management.
    """
    if not text or len(text.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text cannot be empty",
        )

    if len(text) > 10000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text too long. Maximum 10,000 characters allowed",
        )

    request = SentimentAnalysisRequest(text=text)

    # Force fallback if requested
    if not use_openai:
        return await sentiment_service._analyze_with_keywords(request)

    return await sentiment_service.analyze_text(request)


@router.post("/predict-price", response_model=PricePredictionResponse)
async def predict_price_from_news(
    request: PricePredictionRequest,
    db: DBSession,
) -> PricePredictionResponse:
    """
    Predict cryptocurrency price movement based on latest news sentiment.
    
    This endpoint:
    1. Fetches the latest news articles for the specified symbol from crawler service
    2. Analyzes the overall sentiment using OpenAI
    3. Predicts likely price movement (bullish/bearish/neutral)
    4. Saves the result to the database for caching
    5. Returns detailed reasoning and key factors
    
    - **symbol**: Trading pair symbol (e.g., BTCUSDT, ETHUSDT)
    - **limit**: Number of recent articles to analyze (default: 10, max: 50)
    - **include_historical_price**: Whether to include historical price data (not yet implemented)
    
    Example request:
    ```json
    {
        "symbol": "BTCUSDT",
        "limit": 10
    }
    ```
    
    Note: This uses OpenAI's advanced analysis to provide comprehensive price predictions.
    Model version and settings are controlled server-side for security and cost management.
    """
    try:
        # Get prediction from service
        prediction, news_articles = await price_prediction_service.predict_price(request)
        
        # Save prediction to DB for caching (used by predict-price-poll)
        try:
            await price_prediction_crud.create_from_prediction_result(db, prediction)
            await db.commit()
        except Exception as save_err:
            import structlog
            structlog.get_logger().warning(
                "Failed to save prediction to DB (non-fatal)",
                error=str(save_err),
            )
        
        return PricePredictionResponse(
            success=True,
            prediction=prediction,
            news_articles=news_articles,
            historical_price=None,  # TODO: Implement if chart service integration needed
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to predict price: {str(e)}",
        )


@router.post("/predict-price-poll", response_model=LongPollingPredictionResponse)
async def predict_price_long_polling(
    request: LongPollingPredictionRequest,
    db: DBSession,
) -> LongPollingPredictionResponse:
    """
    Long-polling endpoint for AI price predictions (VIP only).
    
    This endpoint implements long-polling to efficiently retrieve price predictions:
    1. Checks database for existing predictions (cache)
    2. Returns cached prediction if available and recent (< 5 minutes old)
    3. Generates new prediction using OpenAI if cache is stale or missing
    4. Waits for new predictions if client already has latest data
    5. Returns after timeout or when new data is available
    
    **Benefits:**
    - Reduces OpenAI API calls by caching predictions (5 minute cache)
    - Efficient polling mechanism (checks every 5 seconds)
    - Saves costs by reusing recent predictions
    
    **Parameters:**
    - **symbol**: Trading pair symbol (e.g., BTCUSDT, ETHUSDT)
    - **last_prediction_time**: Timestamp of last prediction received by client (optional)
    - **timeout**: Max wait time for new data (30-120 seconds, default: 90)
    
    **Response:**
    - **has_new_data**: True if new prediction is available
    - **prediction**: Prediction data (if available)
    - **cache_hit**: True if prediction was from cache
    - **next_poll_after**: Recommended seconds to wait before next poll
    
    **Example request:**
    ```json
    {
        "symbol": "BTCUSDT",
        "last_prediction_time": "2024-01-15T10:30:00Z",
        "timeout": 90
    }
    ```
    
    **Usage notes:**
    - First request: Omit `last_prediction_time` to get latest prediction
    - Subsequent requests: Include `last_prediction_time` from previous response
    - Respect `next_poll_after` to avoid unnecessary requests
    - This endpoint requires VIP account (enforced by Gateway)
    
    **Token optimization:**
    Predictions are cached for 5 minutes, meaning maximum 12 OpenAI API calls per hour per symbol.
    """
    try:
        result = await long_polling_service.poll_for_prediction(db, request)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to poll for prediction: {str(e)}",
        )


@router.post("/prediction-line", response_model=PredictionLineResponse)
async def generate_prediction_line(
    request: PredictionLineRequest,
) -> PredictionLineResponse:
    """
    Generate an AI price prediction line for chart overlay (VIP only).
    
    This endpoint:
    1. Fetches recent price data from Binance
    2. Fetches the latest news articles for the symbol
    3. Uses OpenAI to predict future candle close prices
    4. Returns an array of (time, value) points to draw on the chart
    
    The prediction line starts from the current candle and extends
    into the future by the specified number of periods.
    
    **Parameters:**
    - **symbol**: Trading pair (e.g., BTCUSDT)
    - **interval**: Chart timeframe (1m, 5m, 15m, 1h, 4h, 1d, 1w)
    - **periods**: Number of future candles to predict (4–100, default 24)
    - **news_limit**: Number of news articles to analyze (1–50, default 10)
    
    **Example request:**
    ```json
    {
        "symbol": "BTCUSDT",
        "interval": "1h",
        "periods": 24,
        "news_limit": 10
    }
    ```
    
    **Note:** This endpoint requires a VIP account (enforced by Gateway).
    """
    try:
        result = await prediction_line_service.generate_prediction_line(request)
        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate prediction line: {str(e)}",
        )
