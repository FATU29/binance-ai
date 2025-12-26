"""CRUD operations for news articles."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.news import NewsArticle
from app.schemas.news import NewsArticleCreate, NewsArticleUpdate
from app.services.base import CRUDBase


class CRUDNewsArticle(CRUDBase[NewsArticle, NewsArticleCreate, NewsArticleUpdate]):
    """CRUD operations for news articles."""

    async def get_by_url(self, db: AsyncSession, *, url: str) -> NewsArticle | None:
        """Get a news article by URL."""
        result = await db.execute(select(NewsArticle).where(NewsArticle.url == url))
        return result.scalar_one_or_none()

    async def get_by_category(
        self, db: AsyncSession, *, category: str, skip: int = 0, limit: int = 100
    ) -> list[NewsArticle]:
        """Get news articles by category."""
        result = await db.execute(
            select(NewsArticle)
            .where(NewsArticle.category == category)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search(
        self, db: AsyncSession, *, query: str, skip: int = 0, limit: int = 100
    ) -> list[NewsArticle]:
        """Search news articles by title or content."""
        search_pattern = f"%{query}%"
        result = await db.execute(
            select(NewsArticle)
            .where(
                (NewsArticle.title.ilike(search_pattern))
                | (NewsArticle.content.ilike(search_pattern))
            )
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())


# Singleton instance
news_article = CRUDNewsArticle(NewsArticle)
