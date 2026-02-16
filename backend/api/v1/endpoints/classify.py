"""
Classification API Endpoints

Endpoints for classifying articles and text using Gemini LLM.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.llm_service import get_gemini_service

router = APIRouter()


class ClassifyTextRequest(BaseModel):
    """Request model for text classification."""
    
    text: str = Field(..., min_length=10, max_length=10000)
    title: Optional[str] = Field(None, max_length=500)


class ClassifyTextResponse(BaseModel):
    """Response model for text classification."""
    
    bias: str
    confidence: float
    reasoning: Optional[str] = None


@router.post("", response_model=ClassifyTextResponse)
async def classify_text(request: ClassifyTextRequest):
    """
    Classify text for political bias using Gemini LLM.
    
    Args:
        request: Text to classify
    
    Returns:
        Classification result with bias label and confidence
    """
    try:
        gemini = get_gemini_service()
        result = gemini.classify_bias(request.text, request.title or "")
        
        return ClassifyTextResponse(
            bias=result['ml_bias'],
            confidence=result['ml_confidence'],
            reasoning=result['ml_reasoning']
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification failed: {str(e)}"
        )


@router.post("/url")
async def classify_url(url: str):
    """
    Classify an article from URL.
    
    Args:
        url: Article URL to fetch and classify
    
    Returns:
        Classification result
    """
    # TODO: Implement URL fetching and classification
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="URL classification not yet implemented",
    )
