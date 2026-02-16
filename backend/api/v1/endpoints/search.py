"""
Search Endpoints

News search with NewsAPI integration and ML-based bias classification.
"""

import logging
from typing import List, Optional
from datetime import datetime
import pandas as pd

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field

from backend.news_search_service import get_news_search_service
from src.backend.bias_classifier import PoliticalBiasClassifier

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
    
    This endpoint will:
    1. Search NewsAPI for articles matching the query
    2. Fetch full article content from sources
    3. Apply ML bias classification to each article
    4. Return results with detailed bias analysis
    
    Args:
        topic: The search query (e.g., "bangladesh", "climate change")
        max_articles: Maximum number of articles to return
    """
    try:
        logger.info(f"Search initiated: {topic}")
        
        # Get news search service
        search_service = get_news_search_service()
        
        if not search_service.enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="News search service not configured. Please set NEWS_API_KEY."
            )
        
        # Search for articles and fetch content
        articles = search_service.search_with_content(
            query=topic,
            max_results=max_articles,
            fetch_full_content=True
        )
        
        if not articles:
            return TopicSearchResponse(
                success=True,
                query=topic,
                total_found=0,
                articles=[]
            )
        
        # Convert to DataFrame for ML classification
        df_data = []
        for article in articles:
            df_data.append({
                "title": article.get("title", ""),
                "summary": article.get("description", ""),
                "content": article.get("full_content", ""),
                "url": article.get("url", ""),
                "source": article.get("source", {}).get("name", "Unknown"),
                "published": article.get("publishedAt", datetime.now().isoformat()),
                "image_url": article.get("urlToImage"),
                "political_bias": "Unclassified"  # Will be updated by ML
            })
        
        df = pd.DataFrame(df_data)
        
        # Apply ML classification
        logger.info(f"Classifying {len(df)} articles with ML model...")
        classifier = PoliticalBiasClassifier()
        classified_df = classifier.classify_dataframe(df)
        
        # Convert back to response format
        results = []
        for _, row in classified_df.iterrows():
            # Handle NaN values from pandas
            summary = row.get("summary")
            if pd.isna(summary):
                summary = None
            
            image_url = row.get("image_url")
            if pd.isna(image_url):
                image_url = None
            
            content = row.get("content", "")
            if pd.isna(content):
                content = ""
            
            ml_explanation = row.get("ml_explanation")
            if pd.isna(ml_explanation):
                ml_explanation = None
            
            results.append(SearchResult(
                title=row["title"],
                link=row["url"],
                source_name=row["source"],
                published=row["published"],
                summary=summary,
                content=str(content)[:500] if content else None,  # Truncate for response
                image_url=image_url,
                ml_bias=row["ml_bias"],
                ml_confidence=float(row["ml_confidence"]),
                ml_explanation=ml_explanation,
                spectrum_left=float(row.get("spectrum_left", 0)),
                spectrum_center=float(row.get("spectrum_center", 0)),
                spectrum_right=float(row.get("spectrum_right", 0)),
                bias_intensity=float(row.get("bias_intensity", 0)),
            ))
        
        logger.info(f"Successfully classified {len(results)} articles")
        
        return TopicSearchResponse(
            success=True,
            query=topic,
            total_found=len(results),
            articles=results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )
