"""Sentiment analysis endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import DBSession
from app.schemas.common import MessageResponse
from app.schemas.sentiment import (
    SentimentAnalysisCreate,
    SentimentAnalysisRequest,
    SentimentAnalysisResponse,
    SentimentAnalysisResult,
    SentimentAnalysisUpdate,
)
from app.services.sentiment import sentiment_analysis
from app.services.sentiment_service import sentiment_service

router = APIRouter()


@router.post("/analyze", response_model=SentimentAnalysisResult)
async def analyze_sentiment(
    request: SentimentAnalysisRequest,
) -> SentimentAnalysisResult:
    """
    Analyze sentiment of text without saving to database.

    This endpoint performs real-time sentiment analysis on the provided text.

    - **request**: Text to analyze and optional model version
    """
    result = await sentiment_service.analyze_text(request)
    return result


@router.get("", response_model=list[SentimentAnalysisResponse])
async def get_sentiment_analyses(
    db: DBSession,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[SentimentAnalysisResponse]:
    """
    Get paginated list of sentiment analyses.

    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return (max 100)
    """
    analyses = await sentiment_analysis.get_multi(db, skip=skip, limit=limit)
    return [SentimentAnalysisResponse.model_validate(analysis) for analysis in analyses]


@router.get("/{analysis_id}", response_model=SentimentAnalysisResponse)
async def get_sentiment_analysis(
    analysis_id: int,
    db: DBSession,
) -> SentimentAnalysisResponse:
    """
    Get a specific sentiment analysis by ID.

    - **analysis_id**: The ID of the sentiment analysis
    """
    analysis = await sentiment_analysis.get(db, analysis_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sentiment analysis with ID {analysis_id} not found",
        )
    return SentimentAnalysisResponse.model_validate(analysis)


@router.post("", response_model=SentimentAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def create_sentiment_analysis(
    analysis_in: SentimentAnalysisCreate,
    db: DBSession,
) -> SentimentAnalysisResponse:
    """
    Create a new sentiment analysis record.

    - **analysis_in**: Sentiment analysis data
    """
    created_analysis = await sentiment_analysis.create(db, obj_in=analysis_in)
    await db.commit()
    return SentimentAnalysisResponse.model_validate(created_analysis)


@router.patch("/{analysis_id}", response_model=SentimentAnalysisResponse)
async def update_sentiment_analysis(
    analysis_id: int,
    analysis_in: SentimentAnalysisUpdate,
    db: DBSession,
) -> SentimentAnalysisResponse:
    """
    Update a sentiment analysis record.

    - **analysis_id**: The ID of the sentiment analysis to update
    - **analysis_in**: Updated sentiment analysis data
    """
    existing_analysis = await sentiment_analysis.get(db, analysis_id)
    if not existing_analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sentiment analysis with ID {analysis_id} not found",
        )

    updated_analysis = await sentiment_analysis.update(
        db, db_obj=existing_analysis, obj_in=analysis_in
    )
    await db.commit()
    return SentimentAnalysisResponse.model_validate(updated_analysis)


@router.delete("/{analysis_id}", response_model=MessageResponse)
async def delete_sentiment_analysis(
    analysis_id: int,
    db: DBSession,
) -> MessageResponse:
    """
    Delete a sentiment analysis record.

    - **analysis_id**: The ID of the sentiment analysis to delete
    """
    deleted_analysis = await sentiment_analysis.delete(db, id=analysis_id)
    if not deleted_analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sentiment analysis with ID {analysis_id} not found",
        )

    await db.commit()
    return MessageResponse(
        message=f"Sentiment analysis with ID {analysis_id} deleted successfully"
    )


@router.get("/news/{article_id}", response_model=list[SentimentAnalysisResponse])
async def get_sentiment_by_article(
    article_id: int,
    db: DBSession,
) -> list[SentimentAnalysisResponse]:
    """
    Get all sentiment analyses for a specific news article.

    - **article_id**: The ID of the news article
    """
    analyses = await sentiment_analysis.get_by_news_article(db, news_article_id=article_id)
    return [SentimentAnalysisResponse.model_validate(analysis) for analysis in analyses]
