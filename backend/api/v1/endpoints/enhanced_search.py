"""
Enhanced Search API Endpoint

Combines NewsAPI and Serper for comprehensive news search with ML bias classification.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel

from backend.ml_service import get_ml_classifier

logger = logging.getLogger(__name__)
router = APIRouter()


class SearchResult(BaseModel):
    """Result item for search responses."""
    title: str
    link: str
    source_name: str
    published: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
    ml_bias: str
    ml_confidence: float
    ml_explanation: Optional[str] = None
    spectrum_left: float = 0.0
    spectrum_center: float = 0.0
    spectrum_right: float = 0.0
    bias_intensity: float = 0.0


class SearchResponse(BaseModel):
    """Response for search endpoint."""
    success: bool
    query: str
    total_found: int
    articles: List[SearchResult]
    source: str = "combined"


@router.post("/topic")
async def search_topic(
    topic: str = Query(..., min_length=2, max_length=200),
    max_articles: int = Query(30, ge=1, le=100),
    use_serper: bool = Query(False),
) -> SearchResponse:
    """
    Search for articles on a topic and classify with ML bias analysis.

    Uses NewsAPI by default, falls back to Serper if unavailable.
    """
    try:
        articles = []
        source = "newsapi"

        # Try NewsAPI
        if not use_serper:
            try:
                from backend.news_search_service import get_news_search_service
                news_service = get_news_search_service()
                raw_articles = news_service.search_with_content(
                    query=topic, max_results=max_articles
                )
                for a in raw_articles:
                    articles.append({
                        "title": a.get("title", ""),
                        "link": a.get("url", ""),
                        "source_name": a.get("source", {}).get("name", "Unknown"),
                        "published": a.get("publishedAt", ""),
                        "summary": a.get("description", ""),
                        "content": a.get("full_content", ""),
                        "image_url": a.get("urlToImage"),
                    })
                source = "newsapi"
            except Exception as e:
                logger.warning(f"NewsAPI search failed: {e}")

        # Fall back to Serper
        if use_serper or not articles:
            try:
                from backend.serper_search_service import get_serper_service
                serper_service = get_serper_service()
                serper_results = serper_service.search_with_content(
                    query=topic, max_results=max_articles,
                    fetch_content=True, search_type="news"
                )
                articles = []
                for r in serper_results:
                    articles.append({
                        "title": r.get("title", ""),
                        "link": r.get("link", ""),
                        "source_name": r.get("source", "Unknown"),
                        "published": r.get("date", ""),
                        "summary": r.get("snippet", ""),
                        "content": r.get("content", ""),
                        "image_url": r.get("image"),
                    })
                source = "serper"
            except Exception as e:
                logger.warning(f"Serper search failed: {e}")
                if not articles:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=f"Search service unavailable: {str(e)}"
                    )

        if not articles:
            return SearchResponse(
                success=True, query=topic, total_found=0, articles=[], source=source
            )

        # ML classification (batch)
        texts = [a.get("content", "") or a.get("summary", "") for a in articles]
        titles = [a.get("title", "") for a in articles]

        classifier = get_ml_classifier()
        if classifier.is_available:
            classifications = classifier.classify_batch(texts, titles)
        else:
            from backend.llm_service import get_gemini_service
            gemini = get_gemini_service()
            classifications = [gemini.classify_bias(t, ti) for t, ti in zip(texts, titles)]

        # Build response
        search_results = []
        for i, article in enumerate(articles):
            cls = classifications[i] if i < len(classifications) else {}
            search_results.append(SearchResult(
                title=article.get("title", ""),
                link=article.get("link", ""),
                source_name=article.get("source_name", "Unknown"),
                published=article.get("published"),
                summary=article.get("summary") or None,
                content=str(article.get("content", ""))[:500] or None,
                image_url=article.get("image_url"),
                ml_bias=cls.get("ml_bias", "Centrist"),
                ml_confidence=float(cls.get("ml_confidence", 0.5)),
                ml_explanation=cls.get("ml_reasoning"),
                spectrum_left=float(cls.get("spectrum_left", 0.33)),
                spectrum_center=float(cls.get("spectrum_center", 0.34)),
                spectrum_right=float(cls.get("spectrum_right", 0.33)),
                bias_intensity=float(cls.get("bias_intensity", 0.0)),
            ))

        return SearchResponse(
            success=True, query=topic, total_found=len(search_results),
            articles=search_results, source=source
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )
