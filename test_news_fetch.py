#!/usr/bin/env python3
"""
Quick test script for news fetching functionality
"""

import sys
sys.path.insert(0, '.')

from src.backend.source_manager import SourceManager
from src.backend.news_crawler import NewsCrawler

def main():
    print("🔍 Checking news sources...")
    
    # Initialize source manager
    sm = SourceManager()
    
    # Get active sources
    sources = sm.get_active_sources()
    print(f"\n✅ Found {len(sources)} active sources:")
    for source in sources:
        print(f"   - {source['name']}: {source['political_bias']}")
    
    if not sources:
        print("\n❌ No sources found! Run: python3 add_default_sources.py")
        return
    
    print(f"\n📰 Fetching news from first 3 sources...")
    
    # Create crawler
    crawler = NewsCrawler(
        source_manager=sm,
        max_articles_per_source=10
    )
    
    # Fetch articles
    articles_df = crawler.crawl(sources[:3])
    
    if articles_df.empty:
        print("\n❌ No articles fetched")
    else:
        print(f"\n✅ Successfully fetched {len(articles_df)} articles!")
        print("\nSample articles:")
        for _, article in articles_df.head(5).iterrows():
            print(f"   📌 {article['title'][:80]}...")
            print(f"      Source: {article['source_name']} ({article['political_bias']})")
            print(f"      URL: {article['url'][:60]}...")
            print()

if __name__ == "__main__":
    main()
