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
POLL_CHECK_INTERVAL_SECONDS = 5  # Check every 5 seconds


class LongPollingPredictionService:
    """Service for handling long-polling price predictions."""

    async def poll_for_prediction(
        self,
        db: AsyncSession,
        request: LongPollingPredictionRequest,
    ) -> LongPollingPredictionResponse:
        """
        Long-poll for price prediction.
        
        This method:
        1. Checks for existing predictions in database
        2. If no recent prediction exists, generates a new one
        3. Waits for new predictions if client already has latest
        4. Returns after timeout or when new data is available
        
        Args:
            db: Database session
            request: Long-polling request with symbol and optional last prediction time
            
        Returns:
            Response with prediction data or indication to retry
        """
        symbol = request.symbol.upper()
        start_time = datetime.now(timezone.utc)
        timeout = request.timeout
        last_prediction_time = request.last_prediction_time

        logger.info(
            "Long-polling request started",
            symbol=symbol,
            last_prediction_time=last_prediction_time,
            timeout=timeout,
        )

        # Check for existing prediction first
        latest_prediction = await price_prediction_crud.get_latest_by_symbol(db, symbol)

        # If no prediction exists, generate one
        if latest_prediction is None:
            logger.info("No existing prediction found, generating new one", symbol=symbol)
            try:
                prediction_result = await self._generate_new_prediction(symbol)
                latest_prediction = await price_prediction_crud.create_from_prediction_result(
                    db, prediction_result
                )
                await db.commit()
                
                logger.info(
                    "New prediction generated and saved",
                    symbol=symbol,
                    prediction=latest_prediction.prediction,
                )
                
                return LongPollingPredictionResponse(
                    success=True,
                    has_new_data=True,
                    prediction=price_prediction_crud.to_prediction_result(latest_prediction),
                    cache_hit=False,
                    next_poll_after=CACHE_REFRESH_INTERVAL_SECONDS,
                )
            except Exception as e:
                logger.error("Failed to generate prediction", symbol=symbol, error=str(e))
                return LongPollingPredictionResponse(
                    success=False,
                    has_new_data=False,
                    prediction=None,
                    cache_hit=False,
                    next_poll_after=30,
                )

        # Check if client already has this prediction
        if last_prediction_time:
            # If client's prediction is up to date, wait for new data
            if latest_prediction.created_at <= last_prediction_time:
                logger.info(
                    "Client has latest prediction, polling for updates",
                    symbol=symbol,
                    client_time=last_prediction_time,
                    latest_time=latest_prediction.created_at,
                )
                
                # Poll for new predictions
                new_prediction = await self._wait_for_new_prediction(
                    db, symbol, last_prediction_time, timeout
                )
                
                if new_prediction:
                    logger.info(
                        "New prediction found during polling",
                        symbol=symbol,
                        prediction=new_prediction.prediction,
                    )
                    return LongPollingPredictionResponse(
                        success=True,
                        has_new_data=True,
                        prediction=price_prediction_crud.to_prediction_result(new_prediction),
                        cache_hit=True,
                        next_poll_after=CACHE_REFRESH_INTERVAL_SECONDS,
                    )
                else:
                    # Timeout reached, check if we should generate new prediction
                    time_since_last = (
                        datetime.now(timezone.utc) - latest_prediction.created_at
                    ).total_seconds()
                    
                    if time_since_last >= CACHE_REFRESH_INTERVAL_SECONDS:
                        # Generate new prediction
                        logger.info(
                            "Cache expired, generating new prediction",
                            symbol=symbol,
                            time_since_last=time_since_last,
                        )
                        try:
                            prediction_result = await self._generate_new_prediction(symbol)
                            new_prediction = await price_prediction_crud.create_from_prediction_result(
                                db, prediction_result
                            )
                            await db.commit()
                            
                            return LongPollingPredictionResponse(
                                success=True,
                                has_new_data=True,
                                prediction=price_prediction_crud.to_prediction_result(new_prediction),
                                cache_hit=False,
                                next_poll_after=CACHE_REFRESH_INTERVAL_SECONDS,
                            )
                        except Exception as e:
                            logger.error(
                                "Failed to generate new prediction after timeout",
                                symbol=symbol,
                                error=str(e),
                            )
                            # Return existing prediction as fallback
                            return LongPollingPredictionResponse(
                                success=True,
                                has_new_data=False,
                                prediction=price_prediction_crud.to_prediction_result(
                                    latest_prediction
                                ),
                                cache_hit=True,
                                next_poll_after=30,
                            )
                    else:
                        # Still fresh, return existing
                        logger.info(
                            "No new prediction, returning existing",
                            symbol=symbol,
                            time_since_last=time_since_last,
                        )
                        return LongPollingPredictionResponse(
                            success=True,
                            has_new_data=False,
                            prediction=price_prediction_crud.to_prediction_result(
                                latest_prediction
                            ),
                            cache_hit=True,
                            next_poll_after=max(
                                5, int(CACHE_REFRESH_INTERVAL_SECONDS - time_since_last)
                            ),
                        )

        # Client doesn't have this prediction yet, return it
        logger.info(
            "Returning existing prediction to client",
            symbol=symbol,
            prediction=latest_prediction.prediction,
        )
        
        time_since_last = (
            datetime.now(timezone.utc) - latest_prediction.created_at
        ).total_seconds()
        
        return LongPollingPredictionResponse(
            success=True,
            has_new_data=True,
            prediction=price_prediction_crud.to_prediction_result(latest_prediction),
            cache_hit=True,
            next_poll_after=max(
                5, int(CACHE_REFRESH_INTERVAL_SECONDS - time_since_last)
            ),
        )

    async def _wait_for_new_prediction(
        self,
        db: AsyncSession,
        symbol: str,
        after_time: datetime,
        timeout: int,
    ) -> None:
        """
        Wait for a new prediction to appear in database.
        
        Args:
            db: Database session
            symbol: Trading pair symbol
            after_time: Wait for predictions created after this time
            timeout: Maximum time to wait in seconds
            
        Returns:
            New prediction if found, None if timeout
        """
        start = datetime.now(timezone.utc)
        
        while (datetime.now(timezone.utc) - start).total_seconds() < timeout:
            # Check for new prediction
            new_prediction = await price_prediction_crud.get_latest_after_time(
                db, symbol, after_time
            )
            
            if new_prediction:
                return new_prediction
            
            # Wait before checking again
            await asyncio.sleep(POLL_CHECK_INTERVAL_SECONDS)
        
        return None

    async def _generate_new_prediction(self, symbol: str):
        """
        Generate a new price prediction.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            PricePredictionResult
        """
        request = PricePredictionRequest(
            symbol=symbol,
            limit=10,
            include_historical_price=False,
        )
        
        prediction, _ = await price_prediction_service.predict_price(request)
        return prediction


# Global instance
long_polling_service = LongPollingPredictionService()
