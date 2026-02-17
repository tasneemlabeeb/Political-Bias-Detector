"""
Search Endpoints

News search with NewsAPI integration and ML-based bias classification.
"""

import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field

from backend.news_search_service import get_news_search_service
from backend.ml_service import get_ml_classifier

logger = logging.getLogger(__name__)
router = APIRouter()


class SearchResult(BaseModel):
    """Individual search result."""
    title: str
    link: str
    source_name: str
    published: str
    summary: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None

    # ML Classification Results
    ml_bias: str
    ml_confidence: float
    ml_explanation: Optional[str] = None

    # Detailed ML Scores
    spectrum_left: Optional[float] = None
    spectrum_center: Optional[float] = None
    spectrum_right: Optional[float] = None
    bias_intensity: Optional[float] = None


class TopicSearchResponse(BaseModel):
    """Response model for topic search."""
    success: bool
    query: str
    total_found: int
    articles: List[SearchResult]


@router.post("/topic", response_model=TopicSearchResponse)
async def search_by_topic(
    topic: str = Query(..., min_length=3, max_length=200, description="Search query"),
    max_articles: int = Query(20, ge=1, le=100, description="Maximum articles to return"),
):
    """
    Search for news articles using NewsAPI and classify with ML model.

    1. Search NewsAPI for articles matching the query
    2. Fetch full article content from sources
    3. Apply ML bias classification to each article
    4. Return results with detailed bias analysis
    """
    try:
        logger.info(f"Search initiated: {topic}")

        search_service = get_news_search_service()

        if not search_service.enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="News search service not configured. Please set NEWS_API_KEY."
            )

        articles = search_service.search_with_content(
            query=topic,
            max_results=max_articles,
            fetch_full_content=True
        )

        if not articles:
            return TopicSearchResponse(
                success=True, query=topic, total_found=0, articles=[]
            )

        # Prepare texts for batch classification
        texts = []
        titles = []
        for article in articles:
            title = article.get("title", "")
            content = article.get("full_content", "") or article.get("description", "")
            titles.append(title)
            texts.append(content)

        # Classify with ML model (batch)
        classifier = get_ml_classifier()
        if classifier.is_available:
            classifications = classifier.classify_batch(texts, titles)
        else:
            # Fallback: use Gemini for each article
            from backend.llm_service import get_gemini_service
            gemini = get_gemini_service()
            classifications = []
            for title, text in zip(titles, texts):
                result = gemini.classify_bias(text, title)
                classifications.append(result)

        # Build response
        results = []
        for i, article in enumerate(articles):
            cls = classifications[i] if i < len(classifications) else {}

            summary = article.get("description")
            image_url = article.get("urlToImage")
            content = article.get("full_content", "")

            results.append(SearchResult(
                title=article.get("title", ""),
                link=article.get("url", ""),
                source_name=article.get("source", {}).get("name", "Unknown"),
                published=article.get("publishedAt", datetime.now().isoformat()),
                summary=summary if summary else None,
                content=str(content)[:500] if content else None,
                image_url=image_url if image_url else None,
                ml_bias=cls.get("ml_bias", "Centrist"),
                ml_confidence=float(cls.get("ml_confidence", 0.5)),
                ml_explanation=cls.get("ml_reasoning"),
                spectrum_left=cls.get("spectrum_left"),
                spectrum_center=cls.get("spectrum_center"),
                spectrum_right=cls.get("spectrum_right"),
                bias_intensity=cls.get("bias_intensity"),
            ))

        logger.info(f"Successfully classified {len(results)} articles")

        return TopicSearchResponse(
            success=True, query=topic, total_found=len(results), articles=results
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )
