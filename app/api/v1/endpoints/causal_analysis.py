"""API endpoints for causal analysis of news with price history."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import DBSession
from app.schemas.causal_analysis import (
    CausalAnalysisDirectRequest,
    CausalAnalysisRequest,
    CausalAnalysisResponse,
    CausalAnalysisResult,
)
from app.services.causal_analysis_service import causal_analysis_service

router = APIRouter()


@router.post("/analyze/causal", response_model=CausalAnalysisResponse)
async def analyze_causal_relationship(
    request: CausalAnalysisRequest,
    db: DBSession,
) -> CausalAnalysisResponse:
    """
    Perform causal analysis between news article and price movements.
    
    This endpoint:
    1. Fetches the news article
    2. Analyzes sentiment using AI
    3. Fetches price history before and after news publication
    4. Uses AI to identify causal relationships
    5. Predicts future price trend with detailed reasoning
    
    - **news_article_id**: ID of the news article to analyze
    - **symbol**: Trading pair symbol (e.g., BTCUSDT)
    - **hours_before**: Hours of price history before news (default: 24)
    - **hours_after**: Hours of price history after news (default: 24)
    - **prediction_horizon**: Time horizon for prediction (1h, 4h, 24h, 7d)
    
    Returns comprehensive causal analysis with trend prediction.
    """
    try:
        result = await causal_analysis_service.analyze_causal_relationship(
            request=request,
            db=db,
        )
        
        return CausalAnalysisResponse(
            success=True,
            data=result,
            message="Causal analysis completed successfully",
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform causal analysis: {str(e)}",
        )


@router.get("/analyze/causal/{article_id}", response_model=CausalAnalysisResponse)
async def get_causal_analysis_for_article(
    article_id: int,
    symbol: str,
    db: DBSession,
    hours_before: int = 24,
    hours_after: int = 24,
    prediction_horizon: str = "24h",
) -> CausalAnalysisResponse:
    """
    Get causal analysis for a news article with default parameters.
    
    - **article_id**: ID of the news article
    - **symbol**: Trading pair symbol (e.g., BTCUSDT)
    - **hours_before**: Hours of price history before news (default: 24)
    - **hours_after**: Hours of price history after news (default: 24)
    - **prediction_horizon**: Time horizon for prediction (default: 24h)
    """
    request = CausalAnalysisRequest(
        news_article_id=article_id,
        symbol=symbol,
        hours_before=hours_before,
        hours_after=hours_after,
        prediction_horizon=prediction_horizon,  # type: ignore
    )
    
    return await analyze_causal_relationship(request, db)


@router.post("/analyze/direct", response_model=CausalAnalysisResponse)
async def analyze_causal_relationship_direct(
    request: CausalAnalysisDirectRequest,
) -> CausalAnalysisResponse:
    """
    Perform causal analysis with direct news content (no database required).
    
    This endpoint accepts news content directly and performs:
    1. Sentiment analysis using AI
    2. Fetches price history before and after news publication
    3. Uses AI to identify causal relationships
    4. Predicts future price trend with detailed reasoning
    
    - **title**: News article title
    - **content**: News article content
    - **published_at**: Publication timestamp
    - **symbol**: Trading pair symbol (e.g., BTCUSDT)
    - **hours_before**: Hours of price history before news (default: 24)
    - **hours_after**: Hours of price history after news (default: 24)
    - **prediction_horizon**: Time horizon for prediction (1h, 4h, 24h, 7d)
    
    Returns comprehensive causal analysis with trend prediction.
    """
    try:
        result = await causal_analysis_service.analyze_causal_relationship_direct(
            title=request.title,
            content=request.content,
            published_at=request.published_at,
            symbol=request.symbol,
            hours_before=request.hours_before,
            hours_after=request.hours_after,
            prediction_horizon=request.prediction_horizon,
        )
        
        return CausalAnalysisResponse(
            success=True,
            data=result,
            message="Causal analysis completed successfully",
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform causal analysis: {str(e)}",
        )

