"""SQLAlchemy models - Import all models here for Alembic."""

from app.db.base import Base, TimestampMixin
from app.db.models.news import NewsArticle
from app.db.models.price_prediction import PricePrediction
from app.db.models.sentiment import SentimentAnalysis

# Export all models for Alembic to discover
__all__ = ["Base", "TimestampMixin", "NewsArticle", "SentimentAnalysis", "PricePrediction"]
