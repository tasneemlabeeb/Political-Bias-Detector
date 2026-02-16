"""
Articles Endpoints

Endpoints for fetching and managing news articles.
"""

import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel

from src.backend.source_manager import SourceManager
from src.backend.news_crawler import NewsCrawler

logger = logging.getLogger(__name__)
router = APIRouter()


class ArticleResponse(BaseModel):
    """Response model for article."""
    id: str
    title: str
    link: str  # Changed from 'url' to 'link' to match frontend
    source_name: str
    political_bias: str
    published: str
    summary: Optional[str] = None
    content: Optional[str] = None


class FetchNewsResponse(BaseModel):
    """Response model for news fetching."""
    success: bool
    message: str
    articles_count: int
    sources_count: int
    articles: List[ArticleResponse]


@router.get("", response_model=List[ArticleResponse])
async def get_articles(
    source: Optional[str] = Query(None, description="Filter by source name"),
    bias: Optional[str] = Query(None, description="Filter by political bias"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of articles"),
):
    """
    Get articles from the database.
    
    Args:
        source: Optional filter by source name
        bias: Optional filter by political bias
        limit: Maximum number of articles to return
    """
    try:
        # TODO: Implement database storage and retrieval
        # For now, return empty list
        return []
    except Exception as e:
        logger.error(f"Error fetching articles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching articles: {str(e)}"
        )


@router.post("/fetch", response_model=FetchNewsResponse)
async def fetch_news(
    max_sources: int = Query(10, ge=1, le=50, description="Max sources to crawl"),
    articles_per_source: int = Query(20, ge=1, le=100, description="Max articles per source"),
):
    """
    Fetch latest news from all active sources.
    
    This endpoint will:
    1. Get all active news sources from database
    2. Crawl RSS feeds and websites
    3. Extract articles with metadata
    4. Return articles with bias labels
    
    Args:
        max_sources: Maximum number of sources to crawl
        articles_per_source: Maximum articles to fetch per source
    """
    try:
        logger.info(f"Starting news fetch: max_sources={max_sources}, articles_per_source={articles_per_source}")
        
        # Initialize managers
        source_manager = SourceManager()
        crawler = NewsCrawler(
            source_manager=source_manager,
            max_articles_per_source=articles_per_source
        )
        
        # Get active sources
        sources = source_manager.get_active_sources()
        
        if not sources:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active news sources found. Please add sources first."
            )
        
        # Limit sources if needed
        sources = sources[:max_sources]
        logger.info(f"Crawling {len(sources)} sources")
        
        # Crawl articles
        articles_df = crawler.crawl_all_sources()
        
        if articles_df.empty:
            return FetchNewsResponse(
                success=True,
                message="No articles found",
                articles_count=0,
                sources_count=len(sources),
                articles=[]
            )
        
        # Convert DataFrame to response models
        articles = []
        for _, row in articles_df.iterrows():
            article = ArticleResponse(
                id=f"{row['source_name']}_{hash(row['link'])}",
                title=row['title'],
                link=row['link'],
                source_name=row['source_name'],
                political_bias=row['political_bias'],
                published=row['published'] if row['published'] else datetime.now().isoformat(),
                summary=row.get('summary'),
                content=row.get('content')
            )
            articles.append(article)
        
        logger.info(f"Successfully fetched {len(articles)} articles from {len(sources)} sources")
        
        return FetchNewsResponse(
            success=True,
            message=f"Successfully fetched {len(articles)} articles from {len(sources)} sources",
            articles_count=len(articles),
            sources_count=len(sources),
            articles=articles
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching news: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching news: {str(e)}"
        )


@router.delete("/{article_id}")
async def delete_article(article_id: str):
    """Delete an article by ID."""
    # TODO: Implement article deletion from database
    return {"success": True, "message": f"Article {article_id} deleted"}
