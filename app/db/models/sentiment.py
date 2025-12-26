"""Sentiment analysis model."""

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class SentimentAnalysis(Base, TimestampMixin):
    """Model for storing sentiment analysis results."""

    __tablename__ = "sentiment_analyses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    news_article_id: Mapped[int] = mapped_column(
        ForeignKey("news_articles.id", ondelete="CASCADE"),
        nullable=False,
    )
    sentiment_label: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # e.g., "positive", "negative", "neutral"
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False)  # e.g., 0.0 to 1.0
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    analysis_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string

    # Relationships
    # Uncomment if you want bidirectional relationship
    # news_article = relationship("NewsArticle", back_populates="sentiment_analyses")

    def __repr__(self) -> str:
        return f"<SentimentAnalysis(id={self.id}, label='{self.sentiment_label}', score={self.sentiment_score})>"
