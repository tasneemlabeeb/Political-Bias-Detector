"""
Sources Endpoints

Endpoints for managing news sources.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, HttpUrl

from src.backend.source_manager import SourceManager

logger = logging.getLogger(__name__)
router = APIRouter()


class NewsSourceResponse(BaseModel):
    """Response model for a news source."""
    id: int
    name: str
    url: str
    rss_feed: Optional[str] = None
    political_bias: str
    last_scraped: Optional[str] = None
    active: int


class AddSourceRequest(BaseModel):
    """Request model for adding a news source."""
    name: str
    url: str
    rss_feed: Optional[str] = None
    political_bias: str = "Unclassified"


class SourceOperationResponse(BaseModel):
    """Response for source operations."""
    success: bool
    message: str
    source_id: Optional[int] = None


@router.get("", response_model=List[NewsSourceResponse])
async def get_sources(
    active_only: bool = Query(True, description="Return only active sources"),
):
    """
    Get all news sources.
    
    Args:
        active_only: If True, return only active sources
    """
    try:
        source_manager = SourceManager()
        
        if active_only:
            sources = source_manager.get_active_sources()
        else:
            sources = source_manager.get_all_sources()
        
        return [NewsSourceResponse(**source) for source in sources]
        
    except Exception as e:
        logger.error(f"Error fetching sources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching sources: {str(e)}"
        )


@router.post("", response_model=SourceOperationResponse)
async def add_source(request: AddSourceRequest):
    """
    Add a new news source.
    
    Args:
        request: Source details
    """
    try:
        source_manager = SourceManager()
        
        result = source_manager.add_source(
            name=request.name,
            url=request.url,
            rss_feed=request.rss_feed,
            political_bias=request.political_bias
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['message']
            )
        
        return SourceOperationResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding source: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding source: {str(e)}"
        )


@router.delete("/{source_id}", response_model=SourceOperationResponse)
async def delete_source(source_id: int):
    """
    Delete a news source.
    
    Args:
        source_id: ID of the source to delete
    """
    try:
        source_manager = SourceManager()
        result = source_manager.remove_source(source_id)
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result['message']
            )
        
        return SourceOperationResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting source: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting source: {str(e)}"
        )


@router.put("/{source_id}/toggle", response_model=SourceOperationResponse)
async def toggle_source(source_id: int, active: bool = Query(..., description="Set active status")):
    """
    Toggle a source's active status.
    
    Args:
        source_id: ID of the source to toggle
        active: New active status
    """
    try:
        source_manager = SourceManager()
        result = source_manager.update_source_status(source_id, active)
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result['message']
            )
        
        return SourceOperationResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling source: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error toggling source: {str(e)}"
        )
