"""
Citation Network Engine

Builds and analyzes citation graphs between news sources.
Uses NetworkX for graph operations, PageRank for authority scoring,
and community detection for echo chamber identification.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

try:
    from community import community_louvain
    HAS_LOUVAIN = True
except ImportError:
    HAS_LOUVAIN = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

logger = logging.getLogger(__name__)

# Known news domains for citation extraction
NEWS_DOMAINS = {
    "cnn.com", "foxnews.com", "nytimes.com", "washingtonpost.com",
    "wsj.com", "bbc.com", "bbc.co.uk", "reuters.com", "apnews.com",
    "npr.org", "msnbc.com", "nbcnews.com", "cbsnews.com", "abcnews.go.com",
    "politico.com", "thehill.com", "breitbart.com", "huffpost.com",
    "vox.com", "dailywire.com", "theguardian.com", "usatoday.com",
    "latimes.com", "nypost.com", "newsweek.com", "time.com",
    "theatlantic.com", "slate.com", "salon.com", "nationalreview.com",
    "thedailybeast.com", "axios.com", "buzzfeednews.com", "vice.com",
    "jacobin.com", "reason.com",
}

# Domain to display name mapping
DOMAIN_TO_NAME = {
    "cnn.com": "CNN",
    "foxnews.com": "Fox News",
    "nytimes.com": "New York Times",
    "washingtonpost.com": "Washington Post",
    "wsj.com": "Wall Street Journal",
    "bbc.com": "BBC",
    "bbc.co.uk": "BBC",
    "reuters.com": "Reuters",
    "apnews.com": "AP News",
    "npr.org": "NPR",
    "msnbc.com": "MSNBC",
    "nbcnews.com": "NBC News",
    "cbsnews.com": "CBS News",
    "abcnews.go.com": "ABC News",
    "politico.com": "Politico",
    "thehill.com": "The Hill",
    "breitbart.com": "Breitbart",
    "huffpost.com": "HuffPost",
    "vox.com": "Vox",
    "dailywire.com": "Daily Wire",
    "theguardian.com": "The Guardian",
    "usatoday.com": "USA Today",
    "latimes.com": "LA Times",
    "nypost.com": "New York Post",
    "newsweek.com": "Newsweek",
    "time.com": "Time",
    "theatlantic.com": "The Atlantic",
    "slate.com": "Slate",
    "salon.com": "Salon",
    "nationalreview.com": "National Review",
    "thedailybeast.com": "The Daily Beast",
    "axios.com": "Axios",
    "buzzfeednews.com": "BuzzFeed News",
    "vice.com": "Vice",
    "jacobin.com": "Jacobin",
    "reason.com": "Reason",
}

# Mention patterns for text-based citation extraction
MENTION_PATTERNS = [
    r"(?:according to|reported by|as reported by|citing)\s+(?:the\s+)?([A-Z][A-Za-z\s]+?)(?:\s*,|\s+said|\s+reported|\s+found)",
    r"(?:a|an)\s+(?:report|article|story|piece|investigation)\s+(?:by|from|in)\s+(?:the\s+)?([A-Z][A-Za-z\s]+?)(?:\s*,|\s+said|\s+found|\s+showed)",
]


@dataclass
class Citation:
    """A single citation between two sources."""
    from_source: str
    to_source: str
    from_article_id: Optional[int] = None
    to_url: Optional[str] = None
    context: Optional[str] = None
    citation_type: str = "hyperlink"  # hyperlink, mention, reference
    from_bias: Optional[str] = None
    to_bias: Optional[str] = None


@dataclass
class SourceStats:
    """Aggregated statistics for a news source in the network."""
    name: str
    domain: str = ""
    political_bias: str = "unknown"
    citations_made: int = 0
    citations_received: int = 0
    authority_score: float = 0.0
    echo_chamber_score: float = 0.0
    cited_sources: list = field(default_factory=list)
    citing_sources: list = field(default_factory=list)
    same_bias_citations: int = 0
    different_bias_citations: int = 0


@dataclass
class EchoChamber:
    """A detected echo chamber in the citation network."""
    chamber_id: int
    sources: list
    dominant_bias: str
    internal_citations: int = 0
    external_citations: int = 0
    insularity_score: float = 0.0
    avg_authority: float = 0.0


class CitationExtractor:
    """Extracts citations from article content."""

    @staticmethod
    def extract_hyperlinks(html_content: str) -> list[dict]:
        """Extract news source hyperlinks from HTML content."""
        citations = []

        if HAS_BS4:
            soup = BeautifulSoup(html_content, "html.parser")
            for link in soup.find_all("a", href=True):
                href = link["href"]
                for domain in NEWS_DOMAINS:
                    if domain in href:
                        citations.append({
                            "url": href,
                            "domain": domain,
                            "source_name": DOMAIN_TO_NAME.get(domain, domain),
                            "context": link.get_text(strip=True)[:200],
                            "type": "hyperlink",
                        })
                        break
        else:
            # Fallback: regex-based extraction
            url_pattern = r'href=["\']?(https?://[^"\'\s>]+)["\']?'
            urls = re.findall(url_pattern, html_content)
            for url in urls:
                for domain in NEWS_DOMAINS:
                    if domain in url:
                        citations.append({
                            "url": url,
                            "domain": domain,
                            "source_name": DOMAIN_TO_NAME.get(domain, domain),
                            "context": "",
                            "type": "hyperlink",
                        })
                        break

        return citations

    @staticmethod
    def extract_mentions(text: str) -> list[dict]:
        """Extract source mentions from plain text."""
        citations = []
        known_names = set(DOMAIN_TO_NAME.values())

        for pattern in MENTION_PATTERNS:
            matches = re.finditer(pattern, text)
            for match in matches:
                source_name = match.group(1).strip()
                if source_name in known_names:
                    citations.append({
                        "source_name": source_name,
                        "context": match.group(0)[:200],
                        "type": "mention",
                    })

        # Direct name matching
        for name in known_names:
            if name.lower() in text.lower():
                # Avoid duplicates from pattern matching
                if not any(c["source_name"] == name for c in citations):
                    citations.append({
                        "source_name": name,
                        "context": "",
                        "type": "reference",
                    })

        return citations


class CitationNetwork:
    """
    Graph-based citation network for analyzing inter-source relationships.

    Uses NetworkX DiGraph for:
    - PageRank authority scoring
    - Community detection for echo chambers
    - Cross-bias citation analysis
    """

    def __init__(self):
        if not HAS_NETWORKX:
            raise ImportError("networkx is required for CitationNetwork. Install with: pip install networkx")
        self.graph = nx.DiGraph()
        self.sources: dict[str, SourceStats] = {}
        self.citations: list[Citation] = []
        self.extractor = CitationExtractor()

    def add_source(self, name: str, domain: str = "", political_bias: str = "unknown"):
        """Add a news source to the network."""
        if name not in self.sources:
            self.sources[name] = SourceStats(
                name=name,
                domain=domain,
                political_bias=political_bias,
            )
            self.graph.add_node(name, bias=political_bias, domain=domain)

    def add_citation(self, citation: Citation):
        """Add a citation edge to the network."""
        # Ensure both sources exist
        if citation.from_source not in self.sources:
            self.add_source(citation.from_source)
        if citation.to_source not in self.sources:
            self.add_source(citation.to_source)

        self.citations.append(citation)

        # Update graph
        if self.graph.has_edge(citation.from_source, citation.to_source):
            self.graph[citation.from_source][citation.to_source]["weight"] += 1
        else:
            self.graph.add_edge(citation.from_source, citation.to_source, weight=1)

        # Update source stats
        from_stats = self.sources[citation.from_source]
        to_stats = self.sources[citation.to_source]

        from_stats.citations_made += 1
        to_stats.citations_received += 1

        if citation.to_source not in from_stats.cited_sources:
            from_stats.cited_sources.append(citation.to_source)
        if citation.from_source not in to_stats.citing_sources:
            to_stats.citing_sources.append(citation.from_source)

        # Track same vs cross-bias citations
        from_bias = self.sources[citation.from_source].political_bias
        to_bias = self.sources[citation.to_source].political_bias
        if from_bias == to_bias:
            from_stats.same_bias_citations += 1
        else:
            from_stats.different_bias_citations += 1

    def extract_citations_from_article(
        self,
        from_source: str,
        article_id: int,
        content: str,
        is_html: bool = False,
    ) -> list[Citation]:
        """Extract and add citations from article content."""
        extracted = []

        if is_html:
            hyperlinks = self.extractor.extract_hyperlinks(content)
            for link in hyperlinks:
                if link["source_name"] != from_source:
                    citation = Citation(
                        from_source=from_source,
                        to_source=link["source_name"],
                        from_article_id=article_id,
                        to_url=link.get("url"),
                        context=link.get("context"),
                        citation_type="hyperlink",
                    )
                    self.add_citation(citation)
                    extracted.append(citation)

        mentions = self.extractor.extract_mentions(content)
        for mention in mentions:
            if mention["source_name"] != from_source:
                # Avoid duplicate if already found via hyperlink
                if not any(
                    c.to_source == mention["source_name"] and c.from_article_id == article_id
                    for c in extracted
                ):
                    citation = Citation(
                        from_source=from_source,
                        to_source=mention["source_name"],
                        from_article_id=article_id,
                        context=mention.get("context"),
                        citation_type=mention["type"],
                    )
                    self.add_citation(citation)
                    extracted.append(citation)

        return extracted

    def calculate_authority_scores(self) -> dict[str, float]:
        """Calculate PageRank-based authority scores."""
        if len(self.graph.nodes) == 0:
            return {}

        try:
            scores = nx.pagerank(self.graph, weight="weight")
        except nx.PowerIterationFailedConvergence:
            scores = {node: 1.0 / len(self.graph.nodes) for node in self.graph.nodes}

        for name, score in scores.items():
            if name in self.sources:
                self.sources[name].authority_score = score

        return scores

    def calculate_echo_chamber_scores(self):
        """Calculate echo chamber scores for each source."""
        for name, stats in self.sources.items():
            total = stats.same_bias_citations + stats.different_bias_citations
            if total > 0:
                stats.echo_chamber_score = stats.same_bias_citations / total
            else:
                stats.echo_chamber_score = 0.0

    def detect_echo_chambers(self) -> list[EchoChamber]:
        """Detect echo chambers using community detection."""
        if len(self.graph.nodes) < 2:
            return []

        undirected = self.graph.to_undirected()

        # Use Louvain community detection if available
        if HAS_LOUVAIN:
            try:
                partition = community_louvain.best_partition(undirected)
            except Exception:
                partition = self._simple_bias_grouping()
        else:
            partition = self._simple_bias_grouping()

        # Group sources by community
        communities: dict[int, list[str]] = defaultdict(list)
        for node, comm_id in partition.items():
            communities[comm_id].append(node)

        chambers = []
        for comm_id, members in communities.items():
            if len(members) < 2:
                continue

            # Determine dominant bias
            bias_counts: dict[str, int] = defaultdict(int)
            for member in members:
                if member in self.sources:
                    bias_counts[self.sources[member].political_bias] += 1
            dominant_bias = max(bias_counts, key=bias_counts.get) if bias_counts else "unknown"

            # Count internal vs external citations
            internal = 0
            external = 0
            for citation in self.citations:
                if citation.from_source in members:
                    if citation.to_source in members:
                        internal += 1
                    else:
                        external += 1

            total = internal + external
            insularity = internal / total if total > 0 else 0.0

            # Average authority
            authorities = [
                self.sources[m].authority_score
                for m in members
                if m in self.sources
            ]
            avg_auth = sum(authorities) / len(authorities) if authorities else 0.0

            chambers.append(EchoChamber(
                chamber_id=comm_id,
                sources=members,
                dominant_bias=dominant_bias,
                internal_citations=internal,
                external_citations=external,
                insularity_score=insularity,
                avg_authority=avg_auth,
            ))

        return chambers

    def _simple_bias_grouping(self) -> dict[str, int]:
        """Fallback: group sources by political bias."""
        bias_to_id: dict[str, int] = {}
        partition: dict[str, int] = {}
        next_id = 0

        for name, stats in self.sources.items():
            bias = stats.political_bias
            if bias not in bias_to_id:
                bias_to_id[bias] = next_id
                next_id += 1
            partition[name] = bias_to_id[bias]

        return partition

    def get_cross_bias_citations(self) -> dict:
        """Build a cross-bias citation matrix."""
        biases = sorted(set(s.political_bias for s in self.sources.values()))
        matrix: dict[str, dict[str, int]] = {b: {b2: 0 for b2 in biases} for b in biases}

        total_cross = 0
        total_same = 0

        for citation in self.citations:
            from_bias = self.sources.get(citation.from_source, SourceStats(name="")).political_bias
            to_bias = self.sources.get(citation.to_source, SourceStats(name="")).political_bias
            if from_bias in matrix and to_bias in matrix[from_bias]:
                matrix[from_bias][to_bias] += 1
                if from_bias == to_bias:
                    total_same += 1
                else:
                    total_cross += 1

        return {
            "cross_bias_matrix": matrix,
            "total_cross_bias_citations": total_cross,
            "total_same_bias_citations": total_same,
        }

    def get_network_summary(self) -> dict:
        """Get comprehensive network statistics."""
        self.calculate_authority_scores()
        self.calculate_echo_chamber_scores()

        most_cited = sorted(
            self.sources.items(),
            key=lambda x: x[1].citations_received,
            reverse=True,
        )[:5]

        most_citing = sorted(
            self.sources.items(),
            key=lambda x: x[1].citations_made,
            reverse=True,
        )[:5]

        echo_scores = [s.echo_chamber_score for s in self.sources.values()]
        avg_echo = sum(echo_scores) / len(echo_scores) if echo_scores else 0.0

        n = len(self.graph.nodes)
        density = nx.density(self.graph) if n > 1 else 0.0

        return {
            "total_sources": len(self.sources),
            "total_citations": len(self.citations),
            "avg_citations_per_source": (
                len(self.citations) / len(self.sources) if self.sources else 0
            ),
            "most_cited": [[name, s.citations_received] for name, s in most_cited],
            "most_citing": [[name, s.citations_made] for name, s in most_citing],
            "avg_echo_chamber_score": avg_echo,
            "network_density": density,
        }

    def get_sources_list(self, sort_by: str = "authority") -> list[dict]:
        """Get all sources with stats, sorted by the given field."""
        self.calculate_authority_scores()
        self.calculate_echo_chamber_scores()

        sources_list = []
        for name, stats in self.sources.items():
            sources_list.append({
                "name": stats.name,
                "domain": stats.domain,
                "political_bias": stats.political_bias,
                "citations_made": stats.citations_made,
                "citations_received": stats.citations_received,
                "authority_score": stats.authority_score,
                "echo_chamber_score": stats.echo_chamber_score,
                "same_bias_citations": stats.same_bias_citations,
                "different_bias_citations": stats.different_bias_citations,
            })

        sort_keys = {
            "authority": lambda x: x["authority_score"],
            "citations_received": lambda x: x["citations_received"],
            "citations_made": lambda x: x["citations_made"],
            "echo_chamber_score": lambda x: x["echo_chamber_score"],
            "name": lambda x: x["name"],
        }
        key_fn = sort_keys.get(sort_by, sort_keys["authority"])
        reverse = sort_by != "name"
        sources_list.sort(key=key_fn, reverse=reverse)

        return sources_list

    def export_for_visualization(self) -> dict:
        """Export network data for D3.js / Cytoscape visualization."""
        self.calculate_authority_scores()

        nodes = []
        for name, stats in self.sources.items():
            nodes.append({
                "id": name,
                "domain": stats.domain,
                "bias": stats.political_bias,
                "authority": stats.authority_score,
                "citations_received": stats.citations_received,
                "citations_made": stats.citations_made,
            })

        edges = []
        for u, v, data in self.graph.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "weight": data.get("weight", 1),
            })

        return {"nodes": nodes, "edges": edges}

    def reset(self):
        """Clear the entire network."""
        self.graph.clear()
        self.sources.clear()
        self.citations.clear()


def create_demo_network() -> CitationNetwork:
    """Create a demo citation network with sample data."""
    network = CitationNetwork()

    # Add sources with known biases
    demo_sources = [
        ("CNN", "cnn.com", "left"),
        ("Fox News", "foxnews.com", "right"),
        ("New York Times", "nytimes.com", "left_leaning"),
        ("Wall Street Journal", "wsj.com", "right_leaning"),
        ("Reuters", "reuters.com", "center"),
        ("MSNBC", "msnbc.com", "left"),
        ("Breitbart", "breitbart.com", "right"),
        ("NPR", "npr.org", "center"),
    ]

    for name, domain, bias in demo_sources:
        network.add_source(name, domain, bias)

    # Add demo citations
    demo_citations = [
        ("CNN", "MSNBC", "hyperlink"),
        ("CNN", "New York Times", "mention"),
        ("MSNBC", "CNN", "hyperlink"),
        ("New York Times", "CNN", "mention"),
        ("New York Times", "NPR", "reference"),
        ("Fox News", "Breitbart", "hyperlink"),
        ("Fox News", "Wall Street Journal", "mention"),
        ("Breitbart", "Fox News", "hyperlink"),
        ("Wall Street Journal", "Fox News", "reference"),
        ("Reuters", "CNN", "mention"),
        ("Reuters", "Fox News", "reference"),
        ("NPR", "New York Times", "mention"),
        ("NPR", "Wall Street Journal", "reference"),
    ]

    for from_src, to_src, ctype in demo_citations:
        network.add_citation(Citation(
            from_source=from_src,
            to_source=to_src,
            citation_type=ctype,
        ))

    return network
