"""Service for long-polling price predictions."""

import asyncio
from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.price_prediction import (
    LongPollingPredictionRequest,
    LongPollingPredictionResponse,
    PricePredictionRequest,
)
from app.services.price_prediction_crud import price_prediction_crud
from app.services.price_prediction_service import price_prediction_service

logger = structlog.get_logger()

# Cache refresh interval - minimum time between new predictions (to save OpenAI tokens)
CACHE_REFRESH_INTERVAL_SECONDS = 300  # 5 minutes


class LongPollingPredictionService:
    """Service for handling price predictions — database-first, no long-polling."""

    async def poll_for_prediction(
        self,
        db: AsyncSession,
        request: LongPollingPredictionRequest,
    ) -> LongPollingPredictionResponse:
        """
        Return the latest prediction from the database immediately.
        
        This is a fast, database-only lookup:
        1. Query the latest prediction for the symbol from DB
        2. If one exists and is recent enough → return it (cache hit)
        3. If none exists or cache expired → return what we have and signal next_poll_after
        
        No OpenAI calls are made inline — predictions are generated
        by a background task or a separate trigger endpoint.
        """
        symbol = request.symbol.upper()
        last_prediction_time = request.last_prediction_time

        logger.info(
            "Prediction request (DB-only)",
            symbol=symbol,
            last_prediction_time=last_prediction_time,
        )

        # Fast DB lookup
        latest_prediction = await price_prediction_crud.get_latest_by_symbol(db, symbol)

        # No prediction exists at all
        if latest_prediction is None:
            logger.info("No prediction found in DB", symbol=symbol)
            return LongPollingPredictionResponse(
                success=True,
                has_new_data=False,
                prediction=None,
                cache_hit=False,
                next_poll_after=10,
            )

        prediction_result = price_prediction_crud.to_prediction_result(latest_prediction)
        time_since_last = (
            datetime.now(timezone.utc) - latest_prediction.created_at
        ).total_seconds()
        next_poll = max(5, int(CACHE_REFRESH_INTERVAL_SECONDS - time_since_last))

        # Client already has this prediction
        if last_prediction_time and latest_prediction.created_at <= last_prediction_time:
            logger.info(
                "Client already has latest prediction",
                symbol=symbol,
                age_seconds=int(time_since_last),
            )
            return LongPollingPredictionResponse(
                success=True,
                has_new_data=False,
                prediction=prediction_result,
                cache_hit=True,
                next_poll_after=next_poll,
            )

        # Return the prediction (new data for client)
        logger.info(
            "Returning prediction from DB",
            symbol=symbol,
            prediction=latest_prediction.prediction,
            age_seconds=int(time_since_last),
        )
        return LongPollingPredictionResponse(
            success=True,
            has_new_data=True,
            prediction=prediction_result,
            cache_hit=True,
            next_poll_after=next_poll,
        )


# Global instance
long_polling_service = LongPollingPredictionService()
