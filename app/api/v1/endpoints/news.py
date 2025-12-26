"""News article endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import DBSession
from app.schemas.common import MessageResponse
from app.schemas.news import (
    NewsArticleCreate,
    NewsArticleList,
    NewsArticleResponse,
    NewsArticleUpdate,
)
from app.services.news import news_article

router = APIRouter()


@router.get("", response_model=NewsArticleList)
async def get_news_articles(
    db: DBSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> NewsArticleList:
    """
    Get paginated list of news articles.

    - **page**: Page number (starting from 1)
    - **page_size**: Number of items per page (max 100)
    """
    skip = (page - 1) * page_size
    items = await news_article.get_multi(db, skip=skip, limit=page_size)
    total = await news_article.count(db)

    return NewsArticleList(
        items=[NewsArticleResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{article_id}", response_model=NewsArticleResponse)
async def get_news_article(
    article_id: int,
    db: DBSession,
) -> NewsArticleResponse:
    """
    Get a specific news article by ID.

    - **article_id**: The ID of the news article
    """
    article = await news_article.get(db, article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"News article with ID {article_id} not found",
        )
    return NewsArticleResponse.model_validate(article)


@router.post("", response_model=NewsArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_news_article(
    article_in: NewsArticleCreate,
    db: DBSession,
) -> NewsArticleResponse:
    """
    Create a new news article.

    - **article_in**: News article data
    """
    # Check if article with same URL already exists
    existing_article = await news_article.get_by_url(db, url=str(article_in.url))
    if existing_article:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="News article with this URL already exists",
        )

    created_article = await news_article.create(db, obj_in=article_in)
    await db.commit()
    return NewsArticleResponse.model_validate(created_article)


@router.patch("/{article_id}", response_model=NewsArticleResponse)
async def update_news_article(
    article_id: int,
    article_in: NewsArticleUpdate,
    db: DBSession,
) -> NewsArticleResponse:
    """
    Update a news article.

    - **article_id**: The ID of the news article to update
    - **article_in**: Updated news article data
    """
    existing_article = await news_article.get(db, article_id)
    if not existing_article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"News article with ID {article_id} not found",
        )

    updated_article = await news_article.update(db, db_obj=existing_article, obj_in=article_in)
    await db.commit()
    return NewsArticleResponse.model_validate(updated_article)


@router.delete("/{article_id}", response_model=MessageResponse)
async def delete_news_article(
    article_id: int,
    db: DBSession,
) -> MessageResponse:
    """
    Delete a news article.

    - **article_id**: The ID of the news article to delete
    """
    deleted_article = await news_article.delete(db, id=article_id)
    if not deleted_article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"News article with ID {article_id} not found",
        )

    await db.commit()
    return MessageResponse(message=f"News article with ID {article_id} deleted successfully")


@router.get("/search/", response_model=NewsArticleList)
async def search_news_articles(
    db: DBSession,
    q: Annotated[str, Query(min_length=1)] = "",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> NewsArticleList:
    """
    Search news articles by title or content.

    - **q**: Search query
    - **page**: Page number (starting from 1)
    - **page_size**: Number of items per page (max 100)
    """
    skip = (page - 1) * page_size
    items = await news_article.search(db, query=q, skip=skip, limit=page_size)
    total = len(items)  # In production, you'd want a separate count query

    return NewsArticleList(
        items=[NewsArticleResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )
