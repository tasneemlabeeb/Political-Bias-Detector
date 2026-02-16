"""
URL Classification Endpoint

Fetch and classify articles directly from URLs without needing search.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, HttpUrl
import logging
import requests
from bs4 import BeautifulSoup
import pandas as pd

logger = logging.getLogger(__name__)

router = APIRouter()


class URLClassifyRequest(BaseModel):
    """Request for URL classification."""
    url: HttpUrl
    title: Optional[str] = None


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
    """
    Fetch title and content from URL.
    
    Returns:
        Tuple of (title, content)
    """
    try:
        response = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get title
        title = soup.title.string if soup.title else "Unknown"
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text(separator=" ", strip=True)
        
        # Clean up whitespace
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


def get_bias_classifier():
    """Import and return bias classifier."""
    from src.backend.bias_classifier import PoliticalBiasClassifier
    return PoliticalBiasClassifier()


@router.post("/url", response_model=URLClassifyResponse)
async def classify_url(
    url: str = Query(..., description="Article URL to classify")
) -> URLClassifyResponse:
    """
    Fetch and classify an article directly from URL.
    
    Args:
        url: Article URL
    
    Returns:
        Classification result with ML bias analysis
    """
    try:
        # Fetch content
        title, content = fetch_url_content(url)
        
        if not content or len(content) < 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract sufficient content from URL"
            )
        
        # Prepare for classification
        df = pd.DataFrame([{
            "title": title,
            "summary": content[:500],
            "content": content,
            "url": url,
            "source": "Direct URL",
            "published": "",
            "image_url": None,
            "political_bias": "Unclassified"
        }])
        
        # Classify
        try:
            classifier = get_bias_classifier()
            classified_df = classifier.classify_dataframe(df)
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Classification failed: {str(e)}"
            )
        
        # Extract results from DataFrame
        if len(classified_df) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Classification produced no results"
            )
        
        row = classified_df.iloc[0]
        
        return URLClassifyResponse(
            success=True,
            url=str(url),
            title=title,
            content=content[:1000],  # Return first 1000 chars
            ml_bias=row["ml_bias"],
            ml_confidence=float(row["ml_confidence"]),
            ml_explanation=row.get("ml_explanation") if not pd.isna(row.get("ml_explanation")) else None,
            spectrum_left=float(row.get("spectrum_left", 0.33)),
            spectrum_center=float(row.get("spectrum_center", 0.34)),
            spectrum_right=float(row.get("spectrum_right", 0.33)),
            bias_intensity=float(row.get("bias_intensity", 0.0))
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"URL classification error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification failed: {str(e)}"
        )


@router.post("/batch-urls", response_model=dict)
async def classify_multiple_urls(
    urls: List[str] = Query(...)
) -> dict:
    """
    Classify multiple URLs and return results.
    
    Args:
        urls: List of article URLs
    
    Returns:
        Dictionary with results and summary
    """
    if not urls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one URL required"
        )
    
    if len(urls) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 20 URLs allowed per request"
        )
    
    results = []
    failed = []
    
    for url in urls:
        try:
            result = await classify_url(url=url)
            results.append(result.dict())
        except Exception as e:
            failed.append({"url": url, "error": str(e)})
    
    # Calculate aggregate stats
    if results:
        bias_counts = {}
        avg_confidence = sum(r["ml_confidence"] for r in results) / len(results)
        
        for r in results:
            bias = r["ml_bias"]
            bias_counts[bias] = bias_counts.get(bias, 0) + 1
        
        avg_spectrum_left = sum(r["spectrum_left"] for r in results) / len(results)
        avg_spectrum_center = sum(r["spectrum_center"] for r in results) / len(results)
        avg_spectrum_right = sum(r["spectrum_right"] for r in results) / len(results)
    else:
        bias_counts = {}
        avg_confidence = 0
        avg_spectrum_left = avg_spectrum_center = avg_spectrum_right = 0
    
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
            "spectrum_average": {
                "left": avg_spectrum_left,
                "center": avg_spectrum_center,
                "right": avg_spectrum_right
            }
        }
    }
