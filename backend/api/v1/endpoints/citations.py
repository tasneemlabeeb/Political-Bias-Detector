"""
Citation Network Analysis API Endpoints

Endpoints for analyzing citation networks and detecting echo chambers.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field

router = APIRouter()


class NewsSourceResponse(BaseModel):
    """Response model for a news source."""
    name: str
    domain: str
    political_bias: Optional[str] = None
    citations_made: int
    citations_received: int
    authority_score: float
    echo_chamber_score: float
    same_bias_citations: int
    different_bias_citations: int


class CitationResponse(BaseModel):
    """Response model for a citation."""
    from_source: str
    to_source: str
    from_article_id: str
    to_url: str
    context: str
    citation_type: str
    from_bias: Optional[str] = None
    to_bias: Optional[str] = None


class EchoChamberResponse(BaseModel):
    """Response model for an echo chamber."""
    chamber_id: int
    sources: List[str]
    dominant_bias: str
    internal_citations: int
    external_citations: int
    insularity_score: float
    avg_authority: float


class NetworkSummaryResponse(BaseModel):
    """Response model for network summary."""
    total_sources: int
    total_citations: int
    avg_citations_per_source: float
    most_cited: List[tuple]
    most_citing: List[tuple]
    cross_bias_matrix: Dict[str, int]
    avg_echo_chamber_score: float
    network_density: float


class NetworkVisualizationResponse(BaseModel):
    """Response model for network visualization data."""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


class BuildNetworkRequest(BaseModel):
    """Request model for building citation network."""
    article_ids: List[str] = Field(..., min_items=1, max_items=1000)
    extract_from_html: bool = Field(True, description="Extract citations from HTML content")
    extract_from_text: bool = Field(True, description="Extract mentions from article text")


class AddCitationRequest(BaseModel):
    """Request model for adding a citation."""
    from_source: str
    to_source: str
    from_article_id: str
    to_url: str
    context: str = ""
    citation_type: str = Field("hyperlink", pattern="^(hyperlink|mention|quote)$")
    from_bias: Optional[str] = None
    to_bias: Optional[str] = None


# Global citation network instance (in production, use database or cache)
_citation_network = None


def get_citation_network():
    """Get or create citation network instance."""
    global _citation_network
    if _citation_network is None:
        from src.backend.citation_network import CitationNetwork
        _citation_network = CitationNetwork()
    return _citation_network


@router.post("/build")
async def build_network(request: BuildNetworkRequest):
    """
    Build citation network from a set of articles.
    
    Extracts citations and builds network graph.
    """
    from src.backend.citation_network import CitationExtractor, Citation
    
    try:
        network = get_citation_network()
        extractor = CitationExtractor()
        
        # In a real implementation, fetch articles from database
        # For now, return a demo response
        
        return {
            "status": "success",
            "message": f"Network built from {len(request.article_ids)} articles",
            "citations_extracted": 0,
            "sources_identified": 0
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error building network: {str(e)}"
        )


@router.post("/citations/add", response_model=dict)
async def add_citation(request: AddCitationRequest):
    """Add a citation to the network."""
    from src.backend.citation_network import Citation
    
    try:
        network = get_citation_network()
        
        citation = Citation(
            from_source=request.from_source,
            to_source=request.to_source,
            from_article_id=request.from_article_id,
            to_url=request.to_url,
            context=request.context,
            citation_type=request.citation_type,
            from_bias=request.from_bias,
            to_bias=request.to_bias
        )
        
        network.add_citation(citation)
        
        return {
            "status": "success",
            "message": "Citation added to network",
            "total_citations": len(network.citations)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding citation: {str(e)}"
        )


@router.get("/sources", response_model=List[NewsSourceResponse])
async def get_sources(
    min_citations: int = Query(0, ge=0),
    bias: Optional[str] = Query(None),
    sort_by: str = Query('authority', pattern='^(authority|citations_received|citations_made|echo_score)$')
):
    """Get all sources in the network with optional filtering."""
    try:
        network = get_citation_network()
        network.calculate_authority_scores()
        network.calculate_echo_chamber_scores()
        
        sources = []
        for name, source in network.sources.items():
            # Apply filters
            if source.citations_made + source.citations_received < min_citations:
                continue
            if bias and source.political_bias != bias:
                continue
            
            sources.append(NewsSourceResponse(
                name=source.name,
                domain=source.domain,
                political_bias=source.political_bias,
                citations_made=source.citations_made,
                citations_received=source.citations_received,
                authority_score=source.authority_score,
                echo_chamber_score=source.echo_chamber_score,
                same_bias_citations=source.same_bias_citations,
                different_bias_citations=source.different_bias_citations
            ))
        
        # Sort sources
        sort_keys = {
            'authority': lambda s: s.authority_score,
            'citations_received': lambda s: s.citations_received,
            'citations_made': lambda s: s.citations_made,
            'echo_score': lambda s: s.echo_chamber_score
        }
        
        sources.sort(key=sort_keys[sort_by], reverse=True)
        
        return sources
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving sources: {str(e)}"
        )


@router.get("/echo-chambers", response_model=List[EchoChamberResponse])
async def detect_echo_chambers(min_size: int = Query(3, ge=2, le=20)):
    """
    Detect echo chambers in the citation network.
    
    Returns groups of sources that primarily cite each other.
    """
    try:
        network = get_citation_network()
        network.calculate_authority_scores()
        
        chambers = network.detect_echo_chambers(min_size=min_size)
        
        return [
            EchoChamberResponse(
                chamber_id=chamber.chamber_id,
                sources=chamber.sources,
                dominant_bias=chamber.dominant_bias,
                internal_citations=chamber.internal_citations,
                external_citations=chamber.external_citations,
                insularity_score=chamber.insularity_score,
                avg_authority=chamber.avg_authority
            )
            for chamber in chambers
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error detecting echo chambers: {str(e)}"
        )


@router.get("/summary", response_model=NetworkSummaryResponse)
async def get_network_summary():
    """Get summary statistics of the citation network."""
    try:
        network = get_citation_network()
        summary = network.get_network_summary()
        
        return NetworkSummaryResponse(**summary)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting network summary: {str(e)}"
        )


@router.get("/visualization", response_model=NetworkVisualizationResponse)
async def get_visualization_data():
    """
    Get network data formatted for visualization.
    
    Returns nodes and edges in a format suitable for D3.js, Cytoscape, etc.
    """
    try:
        network = get_citation_network()
        network.calculate_authority_scores()
        network.calculate_echo_chamber_scores()
        
        data = network.export_for_visualization()
        
        return NetworkVisualizationResponse(
            nodes=data['nodes'],
            edges=data['edges']
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating visualization data: {str(e)}"
        )


@router.get("/cross-bias")
async def get_cross_bias_citations():
    """
    Analyze citation patterns between different political biases.
    
    Shows which bias categories cite which others.
    """
    try:
        network = get_citation_network()
        cross_bias = network.get_cross_bias_citations()
        
        # Format as matrix for easier visualization
        biases = ['left_leaning', 'left', 'center', 'right', 'right_leaning']
        matrix = {}
        
        for from_bias in biases:
            matrix[from_bias] = {}
            for to_bias in biases:
                key = (from_bias, to_bias)
                matrix[from_bias][to_bias] = cross_bias.get(key, 0)
        
        return {
            "cross_bias_matrix": matrix,
            "total_cross_bias_citations": sum(
                count for (fb, tb), count in cross_bias.items() if fb != tb
            ),
            "total_same_bias_citations": sum(
                count for (fb, tb), count in cross_bias.items() if fb == tb
            )
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing cross-bias citations: {str(e)}"
        )


@router.delete("/reset")
async def reset_network():
    """Reset the citation network (clear all data)."""
    global _citation_network
    _citation_network = None
    return {"status": "success", "message": "Citation network reset"}


@router.post("/demo")
async def create_demo_network():
    """Create a demo citation network with sample data."""
    from src.backend.citation_network import Citation
    
    try:
        network = get_citation_network()
        
        # Add sample sources
        sources = [
            ("CNN", "cnn.com", "left"),
            ("Fox News", "foxnews.com", "right"),
            ("New York Times", "nytimes.com", "left_leaning"),
            ("Wall Street Journal", "wsj.com", "right_leaning"),
            ("Reuters", "reuters.com", "center"),
            ("MSNBC", "msnbc.com", "left"),
            ("Breitbart", "breitbart.com", "right"),
            ("NPR", "npr.org", "center"),
        ]
        
        for name, domain, bias in sources:
            network.add_source(name, domain, bias)
        
        # Add sample citations (creating echo chambers)
        demo_citations = [
            # Left-leaning sources citing each other
            ("CNN", "New York Times", "left", "left_leaning"),
            ("CNN", "MSNBC", "left", "left"),
            ("MSNBC", "CNN", "left", "left"),
            ("New York Times", "CNN", "left_leaning", "left"),
            ("New York Times", "NPR", "left_leaning", "center"),
            
            # Right-leaning sources citing each other
            ("Fox News", "Breitbart", "right", "right"),
            ("Fox News", "Wall Street Journal", "right", "right_leaning"),
            ("Breitbart", "Fox News", "right", "right"),
            ("Wall Street Journal", "Fox News", "right_leaning", "right"),
            
            # Center citing both sides
            ("Reuters", "CNN", "center", "left"),
            ("Reuters", "Fox News", "center", "right"),
            ("NPR", "New York Times", "center", "left_leaning"),
            ("NPR", "Wall Street Journal", "center", "right_leaning"),
        ]
        
        for from_src, to_src, from_bias, to_bias in demo_citations:
            citation = Citation(
                from_source=from_src,
                to_source=to_src,
                from_article_id=f"demo_{from_src}_{to_src}",
                to_url=f"https://{network.sources[to_src].domain}/article",
                context=f"{from_src} cited {to_src}",
                citation_type="hyperlink",
                from_bias=from_bias,
                to_bias=to_bias
            )
            network.add_citation(citation)
        
        summary = network.get_network_summary()
        
        return {
            "status": "success",
            "message": "Demo network created",
            "sources": len(sources),
            "citations": len(demo_citations),
            "summary": summary
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating demo network: {str(e)}"
        )
