#!/usr/bin/env python3
"""Add default news sources to the database."""

import sys
import os

# Add project root to path
_project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, _project_root)

from src.backend.source_manager import SourceManager

def add_default_sources():
    """Add a curated list of news sources across the political spectrum."""
    
    sm = SourceManager("news_sources.db")
    
    # Default sources across the political spectrum
    sources = [
        # Left-leaning sources
        {
            "name": "The Guardian",
            "url": "https://www.theguardian.com/us-news",
            "rss_feed": "https://www.theguardian.com/us-news/rss",
            "political_bias": "Center-Left"
        },
        {
            "name": "HuffPost",
            "url": "https://www.huffpost.com/news/politics",
            "rss_feed": "https://www.huffpost.com/section/politics/feed",
            "political_bias": "Left-Leaning"
        },
        {
            "name": "MSNBC",
            "url": "https://www.msnbc.com/politics",
            "rss_feed": "https://www.msnbc.com/feeds/latest",
            "political_bias": "Left-Leaning"
        },
        
        # Center sources
        {
            "name": "Reuters",
            "url": "https://www.reuters.com/world/us/",
            "rss_feed": "https://www.reuters.com/rssfeed/worldNews",
            "political_bias": "Centrist"
        },
        {
            "name": "Associated Press",
            "url": "https://apnews.com/politics",
            "rss_feed": "https://apnews.com/apf-topnews",
            "political_bias": "Centrist"
        },
        {
            "name": "BBC News",
            "url": "https://www.bbc.com/news/world/us_and_canada",
            "rss_feed": "http://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml",
            "political_bias": "Centrist"
        },
        {
            "name": "The Hill",
            "url": "https://thehill.com/",
            "rss_feed": "https://thehill.com/feed/",
            "political_bias": "Centrist"
        },
        
        # Right-leaning sources
        {
            "name": "Fox News",
            "url": "https://www.foxnews.com/politics",
            "rss_feed": "https://moxie.foxnews.com/google-publisher/politics.xml",
            "political_bias": "Right-Leaning"
        },
        {
            "name": "The Wall Street Journal",
            "url": "https://www.wsj.com/news/politics",
            "rss_feed": "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",
            "political_bias": "Center-Right"
        },
        {
            "name": "National Review",
            "url": "https://www.nationalreview.com/",
            "rss_feed": "https://www.nationalreview.com/feed/",
            "political_bias": "Right-Leaning"
        },
    ]
    
    print("Adding default news sources...")
    print("=" * 60)
    
    success_count = 0
    for source in sources:
        result = sm.add_source(
            name=source["name"],
            url=source["url"],
            rss_feed=source.get("rss_feed"),
            political_bias=source["political_bias"]
        )
        
        if result["success"]:
            print(f"✅ {source['name']:<25} [{source['political_bias']}]")
            success_count += 1
        else:
            print(f"❌ {source['name']:<25} - {result['message']}")
    
    print("=" * 60)
    print(f"\n✓ Successfully added {success_count}/{len(sources)} sources")
    
    # Show all sources
    all_sources = sm.get_active_sources()
    print(f"\nTotal active sources in database: {len(all_sources)}")

if __name__ == "__main__":
    add_default_sources()
