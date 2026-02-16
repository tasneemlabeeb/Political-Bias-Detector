"""
Enhanced Search API Endpoint

Combines NewsAPI and Serper for comprehensive news search with ML bias classification.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel
import logging
import pandas as pd

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
    source: str = "combined"  # "newsapi", "serper", or "combined"


def get_news_search_service():
    """Import and return NewsAPI service."""
    from backend.news_search_service import get_news_search_service as get_newsapi
    return get_newsapi()


def get_serper_service():
    """Import and return Serper service."""
    from backend.serper_search_service import get_serper_service as get_serper
    return get_serper()


def get_bias_classifier():
    """Import and return bias classifier."""
    from src.backend.bias_classifier import PoliticalBiasClassifier
    return PoliticalBiasClassifier()


@router.post("/topic")
async def search_topic(
    topic: str = Query(..., min_length=2, max_length=200),
    max_articles: int = Query(30, ge=1, le=100),
    use_serper: bool = Query(False)
) -> SearchResponse:
    """
    Search for articles on a topic and classify with ML bias analysis.
    
    Args:
        topic: Search topic/query
        max_articles: Maximum articles to return
        use_serper: If True, use Serper; if False, use NewsAPI; if None, try both
    
    Returns:
        SearchResponse with articles and ML classifications
    """
    try:
        articles = []
        
        # Try NewsAPI by default
        if not use_serper:
            try:
                logger.info(f"Searching NewsAPI for: {topic}")
                news_service = get_news_search_service()
                articles = news_service.search_with_content(
                    query=topic,
                    max_results=max_articles
                )
                source = "newsapi"
            except Exception as e:
                logger.warning(f"NewsAPI search failed: {e}")
                articles = []
        
        # Fall back to or use Serper
        if use_serper or (not articles and not use_serper):
            try:
                logger.info(f"Searching Serper for: {topic}")
                serper_service = get_serper_service()
                serper_results = serper_service.search_with_content(
                    query=topic,
                    max_results=max_articles,
                    fetch_content=True,
                    search_type="news"
                )
                
                # Convert Serper format to NewsAPI format
                articles = []
                for result in serper_results:
                    articles.append({
                        "title": result.get("title", ""),
                        "link": result.get("link", ""),
                        "source_name": result.get("source", "Unknown"),
                        "published": result.get("date", ""),
                        "summary": result.get("snippet", ""),
                        "content": result.get("content", ""),
                        "image_url": result.get("image", None)
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
                success=True,
                query=topic,
                total_found=0,
                articles=[],
                source=source
            )
        
        # Prepare data for ML classification
        df_data = []
        for article in articles:
            df_data.append({
                "title": article.get("title", ""),
                "summary": article.get("summary", ""),
                "content": article.get("content", ""),
                "source": article.get("source_name", "Unknown"),
                "published": article.get("published", ""),
                "image_url": article.get("image_url", None),
                "link": article.get("link", "")
            })
        
        df = pd.DataFrame(df_data)
        
        # Classify with ML
        try:
            classifier = get_bias_classifier()
            results = classifier.classify_dataframe(df)
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            # Return without classification if it fails
            results = []
            for idx, row in df.iterrows():
                results.append({
                    "ml_bias": "Centrist",
                    "ml_confidence": 0.5,
                    "ml_explanation": "Classification unavailable",
                    "spectrum_left": 0.33,
                    "spectrum_center": 0.34,
                    "spectrum_right": 0.33,
                    "bias_intensity": 0.0
                })
        
        # Combine results
        search_results = []
        for idx, row in df.iterrows():
            if idx < len(results):
                classification = results[idx]
                
                # Handle NaN values
                summary = row.get("summary")
                if pd.isna(summary):
                    summary = None
                
                image_url = row.get("image_url")
                if pd.isna(image_url):
                    image_url = None
                
                content = row.get("content", "")
                if pd.isna(content):
                    content = ""
                else:
                    content = str(content)[:500]
                
                ml_explanation = classification.get("ml_explanation")
                if ml_explanation and pd.isna(ml_explanation):
                    ml_explanation = None
                
                result = SearchResult(
                    title=row.get("title", ""),
                    link=row.get("link", ""),
                    source_name=row.get("source", "Unknown"),
                    published=row.get("published"),
                    summary=summary,
                    content=content,
                    image_url=image_url,
                    ml_bias=classification.get("ml_bias", "Centrist"),
                    ml_confidence=float(classification.get("ml_confidence", 0.5)),
                    ml_explanation=ml_explanation,
                    spectrum_left=float(classification.get("spectrum_left", 0.33)),
                    spectrum_center=float(classification.get("spectrum_center", 0.34)),
                    spectrum_right=float(classification.get("spectrum_right", 0.33)),
                    bias_intensity=float(classification.get("bias_intensity", 0.0))
                )
                search_results.append(result)
        
        return SearchResponse(
            success=True,
            query=topic,
            total_found=len(search_results),
            articles=search_results,
            source=source
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search endpoint error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/serper-only")
async def search_serper_only(
    topic: str = Query(..., min_length=2, max_length=200),
    max_articles: int = Query(30, ge=1, le=100)
) -> SearchResponse:
    """
    Search using Serper API only.
    
    Args:
        topic: Search topic/query
        max_articles: Maximum articles to return
    
    Returns:
        SearchResponse with Serper results and ML classifications
    """
    return await search_topic(topic=topic, max_articles=max_articles, use_serper=True)
