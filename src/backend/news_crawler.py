import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List
from urllib.parse import urljoin, urlparse

import feedparser
import pandas as pd
import requests
from bs4 import BeautifulSoup

from src.backend.source_manager import SourceManager

logger = logging.getLogger(__name__)


class NewsCrawler:
    """Concurrent news crawler supporting RSS feeds and web scraping."""

    ARTICLE_PATH_KEYWORDS = (
        "/news/",
        "/article/",
        "/story/",
        "/politics/",
        "/opinion/",
        "/world/",
        "/us/",
        "/202",
    )

    SKIP_PATH_KEYWORDS = (
        "/video/",
        "/live/",
        "/podcast/",
        "/tag/",
        "/author/",
        "/topic/",
        "/search",
    )

    _SPACE_RE = re.compile(r"\s+")

    def __init__(
        self,
        source_manager: SourceManager,
        max_workers: int = 10,
        max_articles_per_source: int = 40,
        enrich_article_content: bool = True,
        article_fetch_workers: int = 6,
    ):
        self.source_manager = source_manager
        self.max_workers = max_workers
        self.max_articles_per_source = max_articles_per_source
        self.enrich_article_content = enrich_article_content
        self.article_fetch_workers = max(1, article_fetch_workers)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (compatible; PoliticalBiasDetector/2.0; "
                    "+https://github.com/example/political-bias-detector)"
                )
            }
        )

    @classmethod
    def _clean_text(cls, text: str) -> str:
        if not text:
            return ""
        cleaned = BeautifulSoup(str(text), "html.parser").get_text(" ")
        cleaned = cls._SPACE_RE.sub(" ", cleaned).strip()
        return cleaned

    def _is_article_link(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            path = parsed.path.lower()
        except Exception:
            return False

        if not path:
            return False
        if any(kw in path for kw in self.SKIP_PATH_KEYWORDS):
            return False
        return any(kw in path for kw in self.ARTICLE_PATH_KEYWORDS)

    def _extract_rss_content(self, entry: Dict) -> str:
        content = ""
        raw_content = entry.get("content")
        if isinstance(raw_content, list) and raw_content:
            content = raw_content[0].get("value", "")
        if not content:
            content = entry.get("summary", "")
        return self._clean_text(content)

    def _extract_article_body(self, url: str) -> str:
        """Fetch a news article page and extract likely body text."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            ctype = response.headers.get("Content-Type", "").lower()
            if "html" not in ctype:
                return ""

            soup = BeautifulSoup(response.content, "html.parser")
            for bad in soup(["script", "style", "noscript", "svg", "nav", "footer"]):
                bad.decompose()

            def _extract_from_node(node) -> str:
                chunks = []
                for element in node.find_all(["p", "h2", "h3", "li"]):
                    text = self._clean_text(element.get_text(" ", strip=True))
                    if len(text) >= 45:
                        chunks.append(text)
                return " ".join(chunks)

            candidate_nodes = []
            selectors = [
                "article",
                "main",
                "[role='main']",
                ".article-body",
                ".story-body",
                ".post-content",
                ".entry-content",
            ]
            for selector in selectors:
                candidate_nodes.extend(soup.select(selector))

            # Deduplicate nodes while preserving order.
            seen_nodes = set()
            deduped_nodes = []
            for node in candidate_nodes:
                marker = id(node)
                if marker in seen_nodes:
                    continue
                seen_nodes.add(marker)
                deduped_nodes.append(node)

            best_text = ""
            for node in deduped_nodes[:5]:
                extracted = _extract_from_node(node)
                if len(extracted) > len(best_text):
                    best_text = extracted

            if len(best_text) < 350:
                fallback_chunks = []
                for p in soup.find_all("p"):
                    text = self._clean_text(p.get_text(" ", strip=True))
                    if len(text) >= 60:
                        fallback_chunks.append(text)
                    if len(" ".join(fallback_chunks)) > 4000:
                        break
                if fallback_chunks:
                    best_text = " ".join(fallback_chunks)

            return best_text[:8000]

        except Exception as exc:
            logger.debug("Article content fetch failed for %s: %s", url, exc)
            return ""

    def _dedupe_and_trim_articles(self, articles: List[Dict]) -> List[Dict]:
        deduped = []
        seen_links = set()
        seen_title_source = set()

        for article in articles:
            link = article.get("link", "").strip()
            title = article.get("title", "").strip().lower()
            source = article.get("source_name", "").strip().lower()

            if not link or not title:
                continue
            if link in seen_links:
                continue

            title_key = (title, source)
            if title_key in seen_title_source:
                continue

            seen_links.add(link)
            seen_title_source.add(title_key)
            deduped.append(article)
            if len(deduped) >= self.max_articles_per_source:
                break

        return deduped

    def _enrich_articles_with_content(self, articles: List[Dict]) -> List[Dict]:
        if not self.enrich_article_content or not articles:
            return articles

        candidates = [
            idx
            for idx, article in enumerate(articles)
            if len(article.get("content", "")) < 200
        ]
        if not candidates:
            return articles

        with ThreadPoolExecutor(max_workers=self.article_fetch_workers) as executor:
            future_to_idx = {
                executor.submit(self._extract_article_body, articles[idx]["link"]): idx
                for idx in candidates
            }

            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                text = future.result()
                if text:
                    articles[idx]["content"] = text
                    if not articles[idx].get("summary"):
                        preview = text[:300]
                        if len(text) > 300:
                            preview += "..."
                        articles[idx]["summary"] = preview

        return articles

    def crawl_rss_feed(self, source: Dict) -> List[Dict]:
        """Parse an RSS feed and return structured article data."""
        try:
            feed = feedparser.parse(source["rss_feed"])
            articles = []

            for entry in feed.entries[: self.max_articles_per_source * 3]:
                link = str(entry.get("link", "")).strip()
                title = self._clean_text(str(entry.get("title", "")))
                if not link or len(title) < 8:
                    continue

                summary = self._clean_text(str(entry.get("summary", "")))
                content = self._extract_rss_content(entry)

                if not summary and content:
                    summary = f"{content[:300]}..." if len(content) > 300 else content

                articles.append(
                    {
                        "title": title,
                        "link": link,
                        "published": entry.get("published", ""),
                        "summary": summary,
                        "content": content,
                        "source_name": source["name"],
                        "political_bias": source["political_bias"],
                    }
                )

            articles = self._dedupe_and_trim_articles(articles)
            articles = self._enrich_articles_with_content(articles)

            logger.info(
                "Crawled %d articles from RSS feed: %s",
                len(articles),
                source["name"],
            )
            return articles

        except Exception as exc:
            logger.error("Error crawling RSS feed %s: %s", source["name"], exc)
            return []

    def crawl_website(self, source: Dict) -> List[Dict]:
        """Scrape a website for article links when no RSS feed is available."""
        url = source["url"]
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            articles = []
            seen_links = set()

            for anchor in soup.find_all("a", href=True):
                href = str(anchor["href"]).strip()
                full_url = urljoin(url, href)

                if full_url in seen_links:
                    continue
                if not self._is_article_link(full_url):
                    continue

                seen_links.add(full_url)

                title = self._clean_text(
                    anchor.get_text(" ", strip=True)
                    or anchor.get("title", "")
                    or anchor.get("aria-label", "")
                )
                if len(title) < 10:
                    continue

                articles.append(
                    {
                        "title": title,
                        "link": full_url,
                        "published": "",
                        "summary": "",
                        "content": "",
                        "source_name": source["name"],
                        "political_bias": source["political_bias"],
                    }
                )

                if len(articles) >= self.max_articles_per_source * 3:
                    break

            articles = self._dedupe_and_trim_articles(articles)
            articles = self._enrich_articles_with_content(articles)

            logger.info(
                "Scraped %d articles from website: %s", len(articles), source["name"]
            )
            return articles

        except Exception as exc:
            logger.error("Error scraping %s: %s", source["name"], exc)
            return []

    def _crawl_source(self, source: Dict) -> List[Dict]:
        """Crawl a single source using the appropriate method."""
        if source.get("rss_feed"):
            articles = self.crawl_rss_feed(source)
        else:
            articles = self.crawl_website(source)

        self.source_manager.update_last_scraped(source["id"])
        return articles

    def crawl_all_sources(self) -> pd.DataFrame:
        """Crawl all active news sources concurrently and return a DataFrame."""
        sources = self.source_manager.get_active_sources()

        if not sources:
            logger.warning("No active sources to crawl")
            return pd.DataFrame()

        all_articles = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_source = {
                executor.submit(self._crawl_source, source): source for source in sources
            }

            for future in as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    articles = future.result()
                    all_articles.extend(articles)
                except Exception as exc:
                    logger.error("Failed to crawl %s: %s", source["name"], exc)

        df = pd.DataFrame(all_articles)
        if not df.empty:
            df.drop_duplicates(subset=["link"], inplace=True)
            df.reset_index(drop=True, inplace=True)

        logger.info("Total articles collected: %d", len(df))
        return df

    def crawl_single_source(self, source_name: str) -> pd.DataFrame:
        """Crawl a single source by name."""
        sources = self.source_manager.get_active_sources()
        match = [source for source in sources if source["name"] == source_name]

        if not match:
            logger.warning("Source '%s' not found or inactive", source_name)
            return pd.DataFrame()

        articles = self._crawl_source(match[0])
        return pd.DataFrame(articles)
