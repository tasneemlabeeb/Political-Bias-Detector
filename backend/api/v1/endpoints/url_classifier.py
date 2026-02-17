"""
URL Classification Endpoint

Fetch and classify articles directly from URLs.
"""

import logging
from typing import List, Optional

import requests
from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, HttpUrl

from backend.ml_service import get_ml_classifier

logger = logging.getLogger(__name__)
router = APIRouter()


class URLClassifyResponse(BaseModel):
    """Response for URL classification."""
    success: bool
    url: str
    title: str
    content: str
    ml_bias: str
    ml_confidence: float
    ml_explanation: Optional[str] = None
    spectrum_left: float = 0.0
    spectrum_center: float = 0.0
    spectrum_right: float = 0.0
    bias_intensity: float = 0.0


def fetch_url_content(url: str) -> tuple[str, str]:
    """Fetch title and content from URL."""
    try:
        response = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.title.string if soup.title else "Unknown"

        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text(separator=" ", strip=True)
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = " ".join(chunk for chunk in chunks if chunk)

        return title, text

    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not fetch URL: {str(e)}"
        )


@router.post("/url", response_model=URLClassifyResponse)
async def classify_url(
    url: str = Query(..., description="Article URL to classify"),
) -> URLClassifyResponse:
    """Fetch and classify an article directly from URL."""
    try:
        title, content = fetch_url_content(url)

        if not content or len(content) < 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract sufficient content from URL"
            )

        # Classify with ML model, fallback to Gemini
        classifier = get_ml_classifier()
        if classifier.is_available:
            result = classifier.classify(content, title)
        else:
            from backend.llm_service import get_gemini_service
            result = get_gemini_service().classify_bias(content, title)

        return URLClassifyResponse(
            success=True,
            url=str(url),
            title=title,
            content=content[:1000],
            ml_bias=result.get("ml_bias", "Centrist"),
            ml_confidence=float(result.get("ml_confidence", 0.5)),
            ml_explanation=result.get("ml_reasoning"),
            spectrum_left=float(result.get("spectrum_left", 0.33)),
            spectrum_center=float(result.get("spectrum_center", 0.34)),
            spectrum_right=float(result.get("spectrum_right", 0.33)),
            bias_intensity=float(result.get("bias_intensity", 0.0)),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"URL classification error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification failed: {str(e)}"
        )


@router.post("/batch-urls")
async def classify_multiple_urls(urls: List[str] = Query(...)) -> dict:
    """Classify multiple URLs (max 20)."""
    if not urls:
        raise HTTPException(status_code=400, detail="At least one URL required")
    if len(urls) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 URLs allowed")

    results = []
    failed = []

    for url in urls:
        try:
            result = await classify_url(url=url)
            results.append(result.model_dump())
        except Exception as e:
            failed.append({"url": url, "error": str(e)})

    if results:
        avg_confidence = sum(r["ml_confidence"] for r in results) / len(results)
        bias_counts = {}
        for r in results:
            bias_counts[r["ml_bias"]] = bias_counts.get(r["ml_bias"], 0) + 1
    else:
        avg_confidence = 0
        bias_counts = {}

    return {
        "success": True,
        "total_urls": len(urls),
        "classified": len(results),
        "failed": len(failed),
        "results": results,
        "failed_urls": failed,
        "statistics": {
            "average_confidence": avg_confidence,
            "bias_distribution": bias_counts,
        },
    }
