"""
Citation Network API Endpoints

Endpoints for building, querying, and analyzing the citation network.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db, CitationRecord, Article, NewsSource
from backend.citation_network import (
    CitationNetwork,
    Citation,
    create_demo_network,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory network instance (rebuilt from DB on demand)
_network: Optional[CitationNetwork] = None


def _get_network() -> CitationNetwork:
    """Get or create the in-memory citation network."""
    global _network
    if _network is None:
        _network = CitationNetwork()
    return _network


# --- Pydantic Models ---

class CitationCreate(BaseModel):
    from_source: str
    to_source: str
    from_article_id: Optional[int] = None
    to_url: Optional[str] = None
    context: Optional[str] = None
    citation_type: str = "hyperlink"
    from_bias: Optional[str] = None
    to_bias: Optional[str] = None


class BuildRequest(BaseModel):
    rebuild: bool = False


# --- Endpoints ---

@router.post("/build")
async def build_network(
    request: BuildRequest,
    db: AsyncSession = Depends(get_db),
):
    """Build citation network from articles in the database."""
    global _network
    network = CitationNetwork()

    # Load sources from DB
    result = await db.execute(select(NewsSource).where(NewsSource.active == True))
    db_sources = result.scalars().all()

    for source in db_sources:
        network.add_source(source.name, source.url, source.political_bias or "unknown")

    # Load existing citations from DB
    result = await db.execute(select(CitationRecord))
    db_citations = result.scalars().all()

    for rec in db_citations:
        network.add_citation(Citation(
            from_source=rec.from_source,
            to_source=rec.to_source,
            from_article_id=rec.from_article_id,
            to_url=rec.to_url,
            context=rec.context,
            citation_type=rec.citation_type,
            from_bias=rec.from_bias,
            to_bias=rec.to_bias,
        ))

    # If rebuild requested, also scan articles for new citations
    if request.rebuild:
        result = await db.execute(
            select(Article).where(Article.content.isnot(None)).limit(500)
        )
        articles = result.scalars().all()

        new_citations = 0
        for article in articles:
            # Find the source name for this article
            src_result = await db.execute(
                select(NewsSource).where(NewsSource.id == article.source_id)
            )
            source = src_result.scalar_one_or_none()
            if not source:
                continue

            extracted = network.extract_citations_from_article(
                from_source=source.name,
                article_id=article.id,
                content=article.content,
                is_html="<" in (article.content or "")[:100],
            )

            # Persist new citations to DB
            for citation in extracted:
                db_record = CitationRecord(
                    from_source=citation.from_source,
                    to_source=citation.to_source,
                    from_article_id=citation.from_article_id,
                    to_url=citation.to_url,
                    context=citation.context,
                    citation_type=citation.citation_type,
                    from_bias=network.sources.get(citation.from_source, None) and network.sources[citation.from_source].political_bias,
                    to_bias=network.sources.get(citation.to_source, None) and network.sources[citation.to_source].political_bias,
                )
                db.add(db_record)
                new_citations += 1

        if new_citations > 0:
            await db.commit()

    _network = network

    summary = network.get_network_summary()
    return {
        "status": "success",
        "message": f"Network built with {summary['total_sources']} sources and {summary['total_citations']} citations",
        **summary,
    }


@router.post("/citations/add")
async def add_citation(
    citation_data: CitationCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add a single citation to the network."""
    network = _get_network()

    citation = Citation(
        from_source=citation_data.from_source,
        to_source=citation_data.to_source,
        from_article_id=citation_data.from_article_id,
        to_url=citation_data.to_url,
        context=citation_data.context,
        citation_type=citation_data.citation_type,
        from_bias=citation_data.from_bias,
        to_bias=citation_data.to_bias,
    )
    network.add_citation(citation)

    # Persist to DB
    db_record = CitationRecord(
        from_source=citation_data.from_source,
        to_source=citation_data.to_source,
        from_article_id=citation_data.from_article_id,
        to_url=citation_data.to_url,
        context=citation_data.context,
        citation_type=citation_data.citation_type,
        from_bias=citation_data.from_bias,
        to_bias=citation_data.to_bias,
    )
    db.add(db_record)
    await db.commit()

    return {"status": "success", "message": "Citation added"}


@router.get("/sources")
async def get_sources(
    sort_by: str = Query("authority", enum=["authority", "citations_received", "citations_made", "echo_chamber_score", "name"]),
):
    """Get all sources with their network statistics."""
    network = _get_network()
    return network.get_sources_list(sort_by=sort_by)


@router.get("/echo-chambers")
async def get_echo_chambers():
    """Detect and return echo chambers in the citation network."""
    network = _get_network()
    chambers = network.detect_echo_chambers()
    return [
        {
            "chamber_id": c.chamber_id,
            "sources": c.sources,
            "dominant_bias": c.dominant_bias,
            "internal_citations": c.internal_citations,
            "external_citations": c.external_citations,
            "insularity_score": c.insularity_score,
            "avg_authority": c.avg_authority,
        }
        for c in chambers
    ]


@router.get("/summary")
async def get_summary():
    """Get network summary statistics."""
    network = _get_network()
    return network.get_network_summary()


@router.get("/visualization")
async def get_visualization():
    """Export network for D3.js / graph visualization."""
    network = _get_network()
    return network.export_for_visualization()


@router.get("/cross-bias")
async def get_cross_bias():
    """Get cross-bias citation analysis."""
    network = _get_network()
    return network.get_cross_bias_citations()


@router.post("/demo")
async def create_demo(db: AsyncSession = Depends(get_db)):
    """Create a demo network with sample data."""
    global _network
    network = create_demo_network()
    _network = network

    # Persist demo citations to DB
    for citation in network.citations:
        db_record = CitationRecord(
            from_source=citation.from_source,
            to_source=citation.to_source,
            context=citation.context,
            citation_type=citation.citation_type,
            from_bias=network.sources.get(citation.from_source, None) and network.sources[citation.from_source].political_bias,
            to_bias=network.sources.get(citation.to_source, None) and network.sources[citation.to_source].political_bias,
        )
        db.add(db_record)

    await db.commit()

    summary = network.get_network_summary()
    return {
        "status": "success",
        "message": "Demo network created",
        "sources": summary["total_sources"],
        "citations": summary["total_citations"],
        "summary": summary,
    }


@router.delete("/reset")
async def reset_network(db: AsyncSession = Depends(get_db)):
    """Clear the entire citation network."""
    global _network
    _network = CitationNetwork()

    # Clear DB citations
    result = await db.execute(select(CitationRecord))
    records = result.scalars().all()
    for record in records:
        await db.delete(record)
    await db.commit()

    return {"status": "success", "message": "Network reset"}
