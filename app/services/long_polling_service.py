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
    """Service for handling price predictions — database-first with auto-generate."""

    async def poll_for_prediction(
        self,
        db: AsyncSession,
        request: LongPollingPredictionRequest,
    ) -> LongPollingPredictionResponse:
        """
        Return the latest prediction from the database.
        If no prediction exists or cache is stale, generate a new one via OpenAI,
        save it to the DB, then return it.
        """
        symbol = request.symbol.upper()
        last_prediction_time = request.last_prediction_time

        logger.info(
            "Prediction poll request",
            symbol=symbol,
            last_prediction_time=last_prediction_time,
        )

        # Fast DB lookup
        latest_prediction = await price_prediction_crud.get_latest_by_symbol(db, symbol)

        # Check if we need to generate a new prediction
        need_new_prediction = False
        if latest_prediction is None:
            need_new_prediction = True
            logger.info("No prediction in DB, will generate", symbol=symbol)
        else:
            time_since_last = (
                datetime.now(timezone.utc) - latest_prediction.created_at
            ).total_seconds()
            if time_since_last > CACHE_REFRESH_INTERVAL_SECONDS:
                need_new_prediction = True
                logger.info(
                    "Prediction cache expired, will regenerate",
                    symbol=symbol,
                    age_seconds=int(time_since_last),
                )

        # Generate new prediction if needed
        if need_new_prediction:
            try:
                predict_request = PricePredictionRequest(
                    symbol=symbol,
                    limit=request.news_limit if hasattr(request, "news_limit") else 10,
                )
                prediction_result, _news = await price_prediction_service.predict_price(
                    predict_request
                )
                # Save to DB
                latest_prediction = (
                    await price_prediction_crud.create_from_prediction_result(
                        db, prediction_result
                    )
                )
                await db.commit()
                logger.info(
                    "New prediction generated and saved",
                    symbol=symbol,
                    prediction=prediction_result.prediction,
                )
            except Exception as e:
                logger.error(
                    "Failed to generate prediction, returning cached if available",
                    symbol=symbol,
                    error=str(e),
                )
                # If we have a stale prediction, still return it
                if latest_prediction is None:
                    return LongPollingPredictionResponse(
                        success=False,
                        has_new_data=False,
                        prediction=None,
                        cache_hit=False,
                        next_poll_after=10,
                    )

        # At this point latest_prediction should exist
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
            "Returning prediction",
            symbol=symbol,
            prediction=latest_prediction.prediction,
            age_seconds=int(time_since_last),
            was_generated=need_new_prediction,
        )
        return LongPollingPredictionResponse(
            success=True,
            has_new_data=True,
            prediction=prediction_result,
            cache_hit=not need_new_prediction,
            next_poll_after=next_poll,
        )


# Global instance
long_polling_service = LongPollingPredictionService()
