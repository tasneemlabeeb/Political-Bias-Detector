"""
Bias Report Endpoints

Crowdsourced bias reports for future model training.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db, BiasReport

logger = logging.getLogger(__name__)
router = APIRouter()

VALID_BIAS_LABELS = [
    "Left-Leaning", "Center-Left", "Centrist", "Center-Right", "Right-Leaning"
]


class BiasReportCreate(BaseModel):
    url: Optional[str] = None
    title: Optional[str] = None
    article_text: Optional[str] = None
    bias_label: str

    @field_validator("bias_label")
    @classmethod
    def validate_bias_label(cls, v: str) -> str:
        if v not in VALID_BIAS_LABELS:
            raise ValueError(f"bias_label must be one of: {VALID_BIAS_LABELS}")
        return v


class BiasReportResponse(BaseModel):
    success: bool
    message: str
    report_id: Optional[int] = None


@router.post("", response_model=BiasReportResponse)
async def submit_bias_report(
    report: BiasReportCreate,
    db: AsyncSession = Depends(get_db),
):
    """Submit a crowdsourced bias report for an article."""
    if not report.url and not report.title:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one of 'url' or 'title' must be provided.",
        )

    try:
        db_report = BiasReport(
            url=report.url.strip() if report.url else None,
            title=report.title.strip() if report.title else None,
            article_text=report.article_text.strip() if report.article_text else None,
            bias_label=report.bias_label,
        )
        db.add(db_report)
        await db.commit()
        await db.refresh(db_report)

        return BiasReportResponse(
            success=True,
            message="Bias report submitted. Thank you for contributing!",
            report_id=db_report.id,
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to save bias report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save bias report.",
        )
