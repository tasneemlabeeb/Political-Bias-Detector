"""
Articles Endpoints

Fetch latest news articles with ML bias classification.
"""

import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from backend.news_search_service import get_news_search_service
from backend.ml_service import get_ml_classifier

logger = logging.getLogger(__name__)
router = APIRouter()


class ArticleResponse(BaseModel):
    id: str
    title: str
    link: str
    source_name: str
    published: str
    summary: Optional[str] = None
    image_url: Optional[str] = None
    political_bias: str = "Centrist"
    ml_bias: Optional[str] = None
    ml_confidence: Optional[float] = None
    ml_reasoning: Optional[str] = None


class FetchNewsResponse(BaseModel):
    success: bool
    articles: List[ArticleResponse]
    message: Optional[str] = None


@router.post("/fetch", response_model=FetchNewsResponse)
async def fetch_news():
    """Fetch latest political news articles and classify them."""
    try:
        search_service = get_news_search_service()

        if not search_service.enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="News search service not configured. Please set NEWS_API_KEY.",
            )

        raw_articles = search_service.search_articles(
            query="politics OR government OR congress OR election",
            max_results=30,
            days_back=7,
        )

        if not raw_articles:
            return FetchNewsResponse(
                success=True, articles=[], message="No articles found"
            )

        # Classify with ML
        texts = []
        titles = []
        for a in raw_articles:
            title = a.get("title", "")
            desc = a.get("description", "") or ""
            titles.append(title)
            texts.append(f"{title}. {desc}")

        classifier = get_ml_classifier()
        if classifier.is_available:
            classifications = classifier.classify_batch(texts, titles)
        else:
            classifications = [{}] * len(raw_articles)

        articles = []
        for i, a in enumerate(raw_articles):
            cls = classifications[i] if i < len(classifications) else {}
            bias = cls.get("ml_bias", "Centrist")

            articles.append(ArticleResponse(
                id=str(i + 1),
                title=a.get("title", ""),
                link=a.get("url", ""),
                source_name=a.get("source", {}).get("name", "Unknown"),
                published=a.get("publishedAt", datetime.now().isoformat()),
                summary=a.get("description"),
                image_url=a.get("urlToImage"),
                political_bias=bias,
                ml_bias=bias,
                ml_confidence=cls.get("ml_confidence"),
                ml_reasoning=cls.get("ml_reasoning"),
            ))

        return FetchNewsResponse(success=True, articles=articles)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch news: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch news: {str(e)}",
        )
