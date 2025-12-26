"""CRUD operations for sentiment analysis."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.sentiment import SentimentAnalysis
from app.schemas.sentiment import SentimentAnalysisCreate, SentimentAnalysisUpdate
from app.services.base import CRUDBase


class CRUDSentimentAnalysis(
    CRUDBase[SentimentAnalysis, SentimentAnalysisCreate, SentimentAnalysisUpdate]
):
    """CRUD operations for sentiment analysis."""

    async def get_by_news_article(
        self, db: AsyncSession, *, news_article_id: int
    ) -> list[SentimentAnalysis]:
        """Get sentiment analyses for a specific news article."""
        result = await db.execute(
            select(SentimentAnalysis).where(
                SentimentAnalysis.news_article_id == news_article_id
            )
        )
        return list(result.scalars().all())

    async def get_latest_by_news_article(
        self, db: AsyncSession, *, news_article_id: int
    ) -> SentimentAnalysis | None:
        """Get the latest sentiment analysis for a specific news article."""
        result = await db.execute(
            select(SentimentAnalysis)
            .where(SentimentAnalysis.news_article_id == news_article_id)
            .order_by(SentimentAnalysis.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_sentiment_label(
        self, db: AsyncSession, *, sentiment_label: str, skip: int = 0, limit: int = 100
    ) -> list[SentimentAnalysis]:
        """Get sentiment analyses by label."""
        result = await db.execute(
            select(SentimentAnalysis)
            .where(SentimentAnalysis.sentiment_label == sentiment_label)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())


# Singleton instance
sentiment_analysis = CRUDSentimentAnalysis(SentimentAnalysis)
