"""CRUD operations for price predictions."""

import json
from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.price_prediction import PricePrediction
from app.schemas.price_prediction import PricePredictionResult


class PricePredictionCRUD:
    """CRUD operations for price predictions."""

    async def get_latest_by_symbol(
        self, db: AsyncSession, symbol: str
    ) -> PricePrediction | None:
        """
        Get the latest prediction for a symbol.
        
        Args:
            db: Database session
            symbol: Trading pair symbol
            
        Returns:
            Latest prediction or None
        """
        result = await db.execute(
            select(PricePrediction)
            .where(PricePrediction.symbol == symbol.upper())
            .order_by(desc(PricePrediction.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_latest_after_time(
        self, db: AsyncSession, symbol: str, after_time: datetime
    ) -> PricePrediction | None:
        """
        Get the latest prediction for a symbol after a specific time.
        
        Args:
            db: Database session
            symbol: Trading pair symbol
            after_time: Get predictions created after this time
            
        Returns:
            Latest prediction after the time or None
        """
        result = await db.execute(
            select(PricePrediction)
            .where(
                PricePrediction.symbol == symbol.upper(),
                PricePrediction.created_at > after_time,
            )
            .order_by(desc(PricePrediction.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create_from_prediction_result(
        self, db: AsyncSession, result: PricePredictionResult
    ) -> PricePrediction:
        """
        Create a new price prediction from PricePredictionResult.
        
        Args:
            db: Database session
            result: Prediction result from AI analysis
            
        Returns:
            Created PricePrediction model
        """
        prediction = PricePrediction(
            symbol=result.symbol.upper(),
            prediction=result.prediction,
            confidence=result.confidence,
            sentiment_summary=json.dumps(result.sentiment_summary),
            reasoning=result.reasoning,
            key_factors=json.dumps(result.key_factors),
            news_analyzed=result.news_analyzed,
            model_version=result.model_version,
        )
        db.add(prediction)
        await db.flush()
        await db.refresh(prediction)
        return prediction

    def to_prediction_result(self, prediction: PricePrediction) -> PricePredictionResult:
        """
        Convert database model to PricePredictionResult schema.
        
        Args:
            prediction: Database model
            
        Returns:
            PricePredictionResult schema
        """
        return PricePredictionResult(
            symbol=prediction.symbol,
            prediction=prediction.prediction,
            confidence=prediction.confidence,
            sentiment_summary=json.loads(prediction.sentiment_summary),
            reasoning=prediction.reasoning,
            key_factors=json.loads(prediction.key_factors),
            news_analyzed=prediction.news_analyzed,
            analyzed_at=prediction.created_at,
            model_version=prediction.model_version,
        )


# Global instance
price_prediction_crud = PricePredictionCRUD()
