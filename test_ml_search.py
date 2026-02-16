#!/usr/bin/env python3
"""
Test script for the new ML-based search system.

Demonstrates searching for news articles and classifying them with ML model.
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_search(query: str, max_articles: int = 5):
    """Test topic search endpoint."""
    
    print(f"\n{'='*70}")
    print(f"TESTING TOPIC SEARCH: '{query}'")
    print(f"{'='*70}\n")
    
    # Make request
    url = f"{BASE_URL}/search/topic"
    params = {
        "topic": query,
        "max_articles": max_articles
    }
    
    try:
        response = requests.post(url, params=params, timeout=120)
        response.raise_for_status()
        
        data = response.json()
        
        # Display results
        if data.get("success"):
            print(f"✅ Search successful!")
            print(f"Query: {data.get('query')}")
            print(f"Articles found: {data.get('total_found')}\n")
            
            # Display articles
            articles = data.get("articles", [])
            if articles:
                for i, article in enumerate(articles, 1):
                    print(f"\n--- Article {i} ---")
                    print(f"Title: {article.get('title')}")
                    print(f"Source: {article.get('source_name')}")
                    print(f"URL: {article.get('link')}")
                    print(f"Published: {article.get('published')}")
                    
                    # ML Classification
                    print(f"\n📊 ML CLASSIFICATION:")
                    print(f"  Bias: {article.get('ml_bias')}")
                    print(f"  Confidence: {article.get('ml_confidence'):.2%}")
                    
                    if article.get('spectrum_left') is not None:
                        print(f"  Spectrum:")
                        print(f"    Left: {article.get('spectrum_left'):.2%}")
                        print(f"    Center: {article.get('spectrum_center'):.2%}")
                        print(f"    Right: {article.get('spectrum_right'):.2%}")
                    
                    if article.get('ml_explanation'):
                        print(f"  Reasoning: {article.get('ml_explanation')[:200]}...")
            else:
                print("❌ No articles found")
                print("\nPossible reasons:")
                print("1. NEWS_API_KEY is not set in .env")
                print("2. Query has no results in last 30 days")
                print("3. Free tier limit reached (100 requests/day)")
                
        else:
            print(f"❌ Search failed: {data.get('detail', 'Unknown error')}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def main():
    """Run all tests."""
    
    print("\n" + "="*70)
    print("POLITICAL BIAS DETECTOR - ML SEARCH SYSTEM")
    print("="*70)
    print("\nThis system:")
    print("1. Searches NewsAPI for relevant articles")
    print("2. Fetches full article content")
    print("3. Classifies each article using ML models")
    print("4. Returns political bias classification with confidence scores\n")
    
    # Test queries
    test_queries = [
        ("bangladesh", 3),
        ("climate change", 3),
        ("artificial intelligence", 2),
    ]
    
    for query, max_articles in test_queries:
        test_search(query, max_articles)
        print("\n")
    
    print("\n" + "="*70)
    print("SETUP REQUIRED")
    print("="*70)
    print("""
To get search results, you need a NewsAPI key:

1. Visit: https://newsapi.org/
2. Sign up for free tier (100 requests/day)
3. Copy your API key
4. Add to .env file:
   NEWS_API_KEY=your_api_key_here
5. Restart the backend

Then search will return real articles with ML bias classification!
    """)


if __name__ == "__main__":
    main()
