"""
Citation Network - Map which sources cite each other and identify echo chambers.

This module provides functionality to:
- Extract citations and links from articles
- Build citation networks between news sources
- Identify echo chambers and information silos
- Analyze cross-ideological citation patterns
- Detect circular reporting and source reliability
"""

from __future__ import annotations

import re
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import List, Set, Dict, Any, Optional, Tuple
from urllib.parse import urlparse
import networkx as nx

try:
    import community as community_louvain
    COMMUNITY_AVAILABLE = True
except ImportError:
    COMMUNITY_AVAILABLE = False


@dataclass
class Citation:
    """Represents a citation from one source to another."""
    from_source: str
    to_source: str
    from_article_id: str
    to_url: str
    context: str  # Text around the citation
    citation_type: str  # 'hyperlink', 'mention', 'quote'
    
    # Bias context
    from_bias: Optional[str] = None
    to_bias: Optional[str] = None


@dataclass
class NewsSource:
    """Represents a news source in the citation network."""
    name: str
    domain: str
    political_bias: Optional[str] = None
    
    # Network metrics
    citations_made: int = 0  # Outgoing citations
    citations_received: int = 0  # Incoming citations
    authority_score: float = 0.0  # Like PageRank
    echo_chamber_score: float = 0.0  # How much it stays in its bubble
    
    # Citation patterns
    cited_sources: Set[str] = field(default_factory=set)
    citing_sources: Set[str] = field(default_factory=set)
    
    # Cross-bias metrics
    same_bias_citations: int = 0
    different_bias_citations: int = 0


@dataclass
class EchoChamber:
    """Represents an identified echo chamber."""
    chamber_id: int
    sources: List[str]
    dominant_bias: str
    internal_citations: int  # Citations within chamber
    external_citations: int  # Citations outside chamber
    insularity_score: float  # internal / (internal + external)
    avg_authority: float


class CitationExtractor:
    """Extract citations from article text and HTML."""
    
    # Common news domains
    NEWS_DOMAINS = {
        'cnn.com', 'foxnews.com', 'nytimes.com', 'washingtonpost.com',
        'wsj.com', 'bbc.com', 'reuters.com', 'apnews.com', 'nbcnews.com',
        'abcnews.com', 'cbsnews.com', 'msnbc.com', 'npr.org', 'politico.com',
        'thehill.com', 'breitbart.com', 'huffpost.com', 'theguardian.com',
        'usatoday.com', 'latimes.com', 'nypost.com', 'newsweek.com',
        'time.com', 'bloomberg.com', 'forbes.com', 'axios.com', 'vox.com',
        'salon.com', 'slate.com', 'dailywire.com', 'theatlantic.com',
        'newyorker.com', 'vice.com', 'buzzfeednews.com', 'propublica.org'
    }
    
    def __init__(self):
        """Initialize citation extractor."""
        self.domain_to_source = {}  # Map domains to standardized source names
    
    def extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www.
            domain = re.sub(r'^www\.', '', domain)
            return domain
        except:
            return ''
    
    def is_news_domain(self, domain: str) -> bool:
        """Check if domain is a known news source."""
        return domain in self.NEWS_DOMAINS
    
    def extract_hyperlinks(self, html: str, article_id: str, source_name: str) -> List[Citation]:
        """
        Extract hyperlinks from HTML content.
        
        Args:
            html: HTML content
            article_id: ID of the source article
            source_name: Name of the source publication
        """
        citations = []
        
        # Find all <a> tags with href
        link_pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>'
        matches = re.finditer(link_pattern, html, re.IGNORECASE)
        
        for match in matches:
            url = match.group(1)
            anchor_text = match.group(2)
            
            domain = self.extract_domain(url)
            if self.is_news_domain(domain):
                # Get context (50 chars before and after)
                start = max(0, match.start() - 50)
                end = min(len(html), match.end() + 50)
                context = html[start:end]
                
                citation = Citation(
                    from_source=source_name,
                    to_source=domain,
                    from_article_id=article_id,
                    to_url=url,
                    context=context,
                    citation_type='hyperlink'
                )
                citations.append(citation)
        
        return citations
    
    def extract_mentions(self, text: str, article_id: str, source_name: str) -> List[Citation]:
        """
        Extract mentions of other news sources in text.
        
        Args:
            text: Article text
            article_id: ID of the source article
            source_name: Name of the source publication
        """
        citations = []
        
        # Common mention patterns
        patterns = [
            r'according to ([A-Z][a-zA-Z\s]+(?:News|Post|Times|Journal|Network))',
            r'([A-Z][a-zA-Z\s]+(?:News|Post|Times|Journal|Network)) reported',
            r'as reported by ([A-Z][a-zA-Z\s]+(?:News|Post|Times|Journal|Network))',
            r'([A-Z][a-zA-Z\s]+(?:News|Post|Times|Journal|Network)) first reported',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                mentioned_source = match.group(1).strip()
                
                # Get context
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]
                
                citation = Citation(
                    from_source=source_name,
                    to_source=mentioned_source,
                    from_article_id=article_id,
                    to_url='',
                    context=context,
                    citation_type='mention'
                )
                citations.append(citation)
        
        return citations


class CitationNetwork:
    """Build and analyze citation networks."""
    
    def __init__(self):
        """Initialize citation network."""
        self.graph = nx.DiGraph()
        self.sources: Dict[str, NewsSource] = {}
        self.citations: List[Citation] = []
        self.source_bias_map: Dict[str, str] = {}
    
    def add_source(self, name: str, domain: str, political_bias: str = None):
        """Add a news source to the network."""
        if name not in self.sources:
            self.sources[name] = NewsSource(
                name=name,
                domain=domain,
                political_bias=political_bias
            )
            self.graph.add_node(name)
            if political_bias:
                self.source_bias_map[name] = political_bias
    
    def add_citation(self, citation: Citation):
        """Add a citation to the network."""
        # Ensure sources exist
        if citation.from_source not in self.sources:
            self.add_source(citation.from_source, '', citation.from_bias)
        if citation.to_source not in self.sources:
            self.add_source(citation.to_source, '', citation.to_bias)
        
        # Add citation
        self.citations.append(citation)
        
        # Update graph
        if self.graph.has_edge(citation.from_source, citation.to_source):
            self.graph[citation.from_source][citation.to_source]['weight'] += 1
        else:
            self.graph.add_edge(citation.from_source, citation.to_source, weight=1)
        
        # Update source metrics
        from_source = self.sources[citation.from_source]
        to_source = self.sources[citation.to_source]
        
        from_source.citations_made += 1
        from_source.cited_sources.add(citation.to_source)
        
        to_source.citations_received += 1
        to_source.citing_sources.add(citation.from_source)
        
        # Update cross-bias metrics
        if citation.from_bias and citation.to_bias:
            if citation.from_bias == citation.to_bias:
                from_source.same_bias_citations += 1
            else:
                from_source.different_bias_citations += 1
    
    def calculate_authority_scores(self):
        """Calculate authority scores (PageRank) for all sources."""
        if len(self.graph.nodes) == 0:
            return
        
        pagerank = nx.pagerank(self.graph, weight='weight')
        
        for source_name, score in pagerank.items():
            if source_name in self.sources:
                self.sources[source_name].authority_score = score
    
    def calculate_echo_chamber_scores(self):
        """Calculate echo chamber scores for each source."""
        for source_name, source in self.sources.items():
            if source.citations_made == 0:
                source.echo_chamber_score = 0.0
                continue
            
            # Echo chamber score = % of citations to same-bias sources
            if source.same_bias_citations + source.different_bias_citations > 0:
                source.echo_chamber_score = (
                    source.same_bias_citations / 
                    (source.same_bias_citations + source.different_bias_citations)
                )
    
    def detect_echo_chambers(self, min_size: int = 3) -> List[EchoChamber]:
        """
        Detect echo chambers using community detection.
        
        Args:
            min_size: Minimum number of sources to form an echo chamber
        """
        if not COMMUNITY_AVAILABLE:
            return self._detect_echo_chambers_simple(min_size)
        
        # Convert to undirected for community detection
        undirected = self.graph.to_undirected()
        
        # Detect communities
        communities = community_louvain.best_partition(undirected, weight='weight')
        
        # Group sources by community
        community_groups = defaultdict(list)
        for source, community_id in communities.items():
            community_groups[community_id].append(source)
        
        # Analyze each community
        echo_chambers = []
        for chamber_id, sources in community_groups.items():
            if len(sources) < min_size:
                continue
            
            # Determine dominant bias
            biases = [self.sources[s].political_bias for s in sources 
                     if s in self.sources and self.sources[s].political_bias]
            dominant_bias = Counter(biases).most_common(1)[0][0] if biases else 'Unknown'
            
            # Count internal vs external citations
            internal = 0
            external = 0
            
            for source in sources:
                if source not in self.sources:
                    continue
                for cited in self.sources[source].cited_sources:
                    if cited in sources:
                        internal += 1
                    else:
                        external += 1
            
            insularity = internal / (internal + external) if (internal + external) > 0 else 0
            
            # Calculate average authority
            authorities = [self.sources[s].authority_score for s in sources if s in self.sources]
            avg_authority = sum(authorities) / len(authorities) if authorities else 0
            
            echo_chambers.append(EchoChamber(
                chamber_id=chamber_id,
                sources=sources,
                dominant_bias=dominant_bias,
                internal_citations=internal,
                external_citations=external,
                insularity_score=insularity,
                avg_authority=avg_authority
            ))
        
        # Sort by insularity (most insular first)
        echo_chambers.sort(key=lambda x: x.insularity_score, reverse=True)
        
        return echo_chambers
    
    def _detect_echo_chambers_simple(self, min_size: int = 3) -> List[EchoChamber]:
        """Simple echo chamber detection based on bias labels."""
        bias_groups = defaultdict(list)
        
        for source_name, source in self.sources.items():
            if source.political_bias:
                bias_groups[source.political_bias].append(source_name)
        
        echo_chambers = []
        for chamber_id, (bias, sources) in enumerate(bias_groups.items()):
            if len(sources) < min_size:
                continue
            
            # Count citations
            internal = 0
            external = 0
            
            for source in sources:
                for cited in self.sources[source].cited_sources:
                    if cited in sources:
                        internal += 1
                    else:
                        external += 1
            
            insularity = internal / (internal + external) if (internal + external) > 0 else 0
            
            authorities = [self.sources[s].authority_score for s in sources]
            avg_authority = sum(authorities) / len(authorities) if authorities else 0
            
            echo_chambers.append(EchoChamber(
                chamber_id=chamber_id,
                sources=sources,
                dominant_bias=bias,
                internal_citations=internal,
                external_citations=external,
                insularity_score=insularity,
                avg_authority=avg_authority
            ))
        
        return echo_chambers
    
    def get_cross_bias_citations(self) -> Dict[Tuple[str, str], int]:
        """Get citation counts between different bias categories."""
        cross_bias = defaultdict(int)
        
        for citation in self.citations:
            if citation.from_bias and citation.to_bias:
                key = (citation.from_bias, citation.to_bias)
                cross_bias[key] += 1
        
        return dict(cross_bias)
    
    def get_most_cited_sources(self, n: int = 10) -> List[Tuple[str, int]]:
        """Get the most cited sources."""
        cited = [(name, source.citations_received) 
                for name, source in self.sources.items()]
        cited.sort(key=lambda x: x[1], reverse=True)
        return cited[:n]
    
    def get_most_citing_sources(self, n: int = 10) -> List[Tuple[str, int]]:
        """Get sources that cite others the most."""
        citing = [(name, source.citations_made) 
                 for name, source in self.sources.items()]
        citing.sort(key=lambda x: x[1], reverse=True)
        return citing[:n]
    
    def get_network_summary(self) -> Dict[str, Any]:
        """Get summary statistics of the citation network."""
        self.calculate_authority_scores()
        self.calculate_echo_chamber_scores()
        
        avg_echo_score = sum(s.echo_chamber_score for s in self.sources.values()) / len(self.sources) if self.sources else 0
        
        return {
            'total_sources': len(self.sources),
            'total_citations': len(self.citations),
            'avg_citations_per_source': len(self.citations) / len(self.sources) if self.sources else 0,
            'most_cited': self.get_most_cited_sources(5),
            'most_citing': self.get_most_citing_sources(5),
            'cross_bias_matrix': self.get_cross_bias_citations(),
            'avg_echo_chamber_score': avg_echo_score,
            'network_density': nx.density(self.graph) if len(self.graph.nodes) > 0 else 0
        }
    
    def export_for_visualization(self) -> Dict[str, Any]:
        """Export network data for visualization (e.g., D3.js, Cytoscape)."""
        nodes = []
        for name, source in self.sources.items():
            nodes.append({
                'id': name,
                'label': name,
                'bias': source.political_bias,
                'authority': source.authority_score,
                'echo_score': source.echo_chamber_score,
                'citations_made': source.citations_made,
                'citations_received': source.citations_received
            })
        
        edges = []
        for from_node, to_node, data in self.graph.edges(data=True):
            edges.append({
                'source': from_node,
                'target': to_node,
                'weight': data.get('weight', 1)
            })
        
        return {
            'nodes': nodes,
            'edges': edges
        }
