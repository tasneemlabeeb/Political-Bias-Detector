"""
Classification API Endpoints

Endpoints for classifying articles and text.
Uses fine-tuned ML model as primary, Gemini LLM as fallback.
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.llm_service import get_gemini_service
from backend.ml_service import get_ml_classifier

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
    spectrum_left: Optional[float] = None
    spectrum_center: Optional[float] = None
    spectrum_right: Optional[float] = None
    bias_intensity: Optional[float] = None
    model_used: str = "ml"


@router.post("", response_model=ClassifyTextResponse)
async def classify_text(request: ClassifyTextRequest):
    """
    Classify text for political bias.

    Uses fine-tuned ML model as primary classifier.
    Falls back to Gemini LLM if the ML model is unavailable.
    """
    # Try ML model first (faster, no API cost)
    ml_classifier = get_ml_classifier()
    if ml_classifier.is_available:
        try:
            result = ml_classifier.classify(request.text, request.title or "")
            return ClassifyTextResponse(
                bias=result["ml_bias"],
                confidence=result["ml_confidence"],
                reasoning=result["ml_reasoning"],
                spectrum_left=result.get("spectrum_left"),
                spectrum_center=result.get("spectrum_center"),
                spectrum_right=result.get("spectrum_right"),
                bias_intensity=result.get("bias_intensity"),
                model_used="ml",
            )
        except Exception as e:
            # Log but fall through to Gemini
            import logging
            logging.getLogger(__name__).warning(f"ML classification failed, falling back to Gemini: {e}")

    # Fallback to Gemini
    try:
        gemini = get_gemini_service()
        result = gemini.classify_bias(request.text, request.title or "")
        return ClassifyTextResponse(
            bias=result["ml_bias"],
            confidence=result["ml_confidence"],
            reasoning=result["ml_reasoning"],
            model_used="gemini",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification failed: {str(e)}",
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
