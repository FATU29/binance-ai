"""Advanced sentiment analysis endpoints with OpenAI integration."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import DBSession
from app.schemas.news import NewsArticleResponse
from app.schemas.sentiment import (
    SentimentAnalysisCreate,
    SentimentAnalysisRequest,
    SentimentAnalysisResponse,
    SentimentAnalysisResult,
)
from app.services.news import news_article
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
