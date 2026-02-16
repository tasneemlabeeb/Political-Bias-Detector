"""
News Search Service

Search for news articles using NewsAPI and fetch full article content.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class NewsSearchService:
    """Service for searching news articles and fetching their content."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize news search service.
        
        Args:
            api_key: NewsAPI key (or uses NEWS_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("NEWS_API_KEY")
        self.base_url = "https://newsapi.org/v2"
        self.enabled = bool(self.api_key)
        
        if not self.enabled:
            logger.warning("NEWS_API_KEY not set. Search functionality will be limited.")
    
    def search_articles(
        self, 
        query: str, 
        max_results: int = 20,
        days_back: int = 30,
        language: str = "en"
    ) -> List[Dict]:
        """
        Search for news articles using NewsAPI.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            days_back: How many days back to search
            language: Language code (default: en)
            
        Returns:
            List of article dictionaries with title, description, url, source, etc.
        """
        if not self.enabled:
            logger.error("NewsAPI not configured. Please set NEWS_API_KEY.")
            return []
        
        try:
            # Calculate date range
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days_back)
            
            params = {
                "q": query,
                "apiKey": self.api_key,
                "language": language,
                "sortBy": "relevancy",
                "pageSize": min(max_results, 100),  # NewsAPI max is 100
                "from": from_date.strftime("%Y-%m-%d"),
                "to": to_date.strftime("%Y-%m-%d"),
            }
            
            response = requests.get(
                f"{self.base_url}/everything",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") != "ok":
                logger.error(f"NewsAPI error: {data.get('message', 'Unknown error')}")
                return []
            
            articles = data.get("articles", [])
            logger.info(f"Found {len(articles)} articles for query: {query}")
            
            return articles[:max_results]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to search NewsAPI: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in search: {e}")
            return []
    
    def fetch_article_content(self, url: str) -> Optional[str]:
        """
        Fetch and extract article content from URL.
        
        Uses BeautifulSoup to extract main article text.
        
        Args:
            url: Article URL
            
        Returns:
            Extracted article text or None if failed
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) "
                             "Chrome/91.0.4472.124 Safari/537.36"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                script.decompose()
            
            # Try common article content selectors
            article_selectors = [
                "article",
                '[role="main"]',
                ".article-content",
                ".post-content",
                ".entry-content",
                ".story-body",
                ".article-body",
                "main",
            ]
            
            content = None
            for selector in article_selectors:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text(separator=" ", strip=True)
                    if len(content) > 200:  # Reasonable article length
                        break
            
            # Fallback: get all paragraphs
            if not content or len(content) < 200:
                paragraphs = soup.find_all("p")
                content = " ".join(p.get_text(strip=True) for p in paragraphs)
            
            if content and len(content) > 50:
                # Clean up whitespace
                content = " ".join(content.split())
                return content[:10000]  # Limit to 10k chars
            
            logger.warning(f"Could not extract meaningful content from {url}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch article from {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None
    
    def search_with_content(
        self,
        query: str,
        max_results: int = 20,
        fetch_full_content: bool = True
    ) -> List[Dict]:
        """
        Search for articles and optionally fetch their full content.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            fetch_full_content: Whether to fetch full article text
            
        Returns:
            List of article dictionaries with fetched content
        """
        articles = self.search_articles(query, max_results)
        
        if not fetch_full_content:
            return articles
        
        # Fetch full content for each article
        enriched_articles = []
        for article in articles:
            url = article.get("url")
            if url:
                content = self.fetch_article_content(url)
                if content:
                    article["full_content"] = content
            enriched_articles.append(article)
        
        logger.info(f"Fetched full content for {sum(1 for a in enriched_articles if 'full_content' in a)} articles")
        
        return enriched_articles


# Global singleton
_news_search_service: Optional[NewsSearchService] = None


def get_news_search_service() -> NewsSearchService:
    """Get or create NewsSearchService singleton."""
    global _news_search_service
    if _news_search_service is None:
        _news_search_service = NewsSearchService()
    return _news_search_service
