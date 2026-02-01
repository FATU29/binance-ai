"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.endpoints import ai_analytics, causal_analysis, chat, health, html_parser, news, sentiment

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(news.router, prefix="/news", tags=["News Articles"])
api_router.include_router(sentiment.router, prefix="/sentiment", tags=["Sentiment Analysis"])
api_router.include_router(
    ai_analytics.router, prefix="/ai", tags=["AI Analytics (OpenAI)"]
)
api_router.include_router(
    causal_analysis.router, prefix="/causal", tags=["Causal Analysis"]
)
api_router.include_router(
    html_parser.router, prefix="/ai", tags=["AI HTML Parser"]
)
api_router.include_router(
    chat.router, prefix="/ai", tags=["AI Chatbox (VIP Only)"]
)