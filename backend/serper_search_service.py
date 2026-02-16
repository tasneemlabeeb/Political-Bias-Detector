"""
Serper Search Service

Integrates Google search via Serper.dev API for comprehensive news and article search.
"""

import os
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SerperSearchService:
    """Service for searching using Serper API (Google Search)."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Serper search service.
        
        Args:
            api_key: Serper API key. If not provided, uses SERPER_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("SERPER_API_KEY")
        if not self.api_key:
            logger.warning("SERPER_API_KEY not configured")
        
        self.base_url = "https://google.serper.dev"
        self.headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
    
    def search_news(
        self,
        query: str,
        num_results: int = 10,
        tbs: str = "qdr:w"  # Last week by default (qdr:d = day, qdr:w = week, qdr:m = month)
    ) -> List[Dict[str, Any]]:
        """
        Search for news articles using Serper API.
        
        Args:
            query: Search query string
            num_results: Number of results to return (max 100)
            tbs: Time range filter (qdr:d, qdr:w, qdr:m, qdr:y)
        
        Returns:
            List of search results with article metadata
        """
        if not self.api_key:
            logger.error("Serper API key not configured")
            return []
        
        payload = {
            "q": query,
            "num": min(num_results, 100),
            "tbs": tbs,
            "type": "news"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/search",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Extract news results
            if "news" in data:
                for item in data["news"]:
                    result = {
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "source": item.get("source", "Unknown"),
                        "date": item.get("date", ""),
                        "image": item.get("image", "")
                    }
                    results.append(result)
            
            logger.info(f"Serper search returned {len(results)} results for '{query}'")
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Serper API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Error processing Serper response: {e}")
            return []
    
    def search_general(
        self,
        query: str,
        num_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        General web search using Serper API.
        
        Args:
            query: Search query string
            num_results: Number of results to return
        
        Returns:
            List of search results
        """
        if not self.api_key:
            logger.error("Serper API key not configured")
            return []
        
        payload = {
            "q": query,
            "num": min(num_results, 100)
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/search",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Extract organic results
            if "organic" in data:
                for item in data["organic"]:
                    result = {
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "source": item.get("source", "Unknown"),
                        "position": item.get("position", 0)
                    }
                    results.append(result)
            
            logger.info(f"Serper general search returned {len(results)} results for '{query}'")
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Serper API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Error processing Serper response: {e}")
            return []
    
    def fetch_article_content(self, url: str) -> Optional[str]:
        """
        Fetch full article content from URL.
        
        Args:
            url: Article URL
        
        Returns:
            Article content or None if fetch failed
        """
        try:
            from bs4 import BeautifulSoup
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text(separator=" ", strip=True)
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)
            
            return text if text else None
            
        except Exception as e:
            logger.warning(f"Failed to fetch content from {url}: {e}")
            return None
    
    def search_with_content(
        self,
        query: str,
        max_results: int = 20,
        fetch_content: bool = True,
        search_type: str = "news"
    ) -> List[Dict[str, Any]]:
        """
        Search and optionally fetch full content for results.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            fetch_content: Whether to fetch full article content
            search_type: "news" for news search, "general" for web search
        
        Returns:
            List of results with optional full content
        """
        # Search based on type
        if search_type == "news":
            results = self.search_news(query, num_results=max_results)
        else:
            results = self.search_general(query, num_results=max_results)
        
        # Optionally fetch full content
        if fetch_content:
            for result in results:
                content = self.fetch_article_content(result["link"])
                result["content"] = content
        
        return results


def get_serper_service() -> SerperSearchService:
    """Get or create Serper search service instance."""
    return SerperSearchService()
