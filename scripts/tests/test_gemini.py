#!/usr/bin/env python3
"""
Test Gemini API Key

Usage:
  python test_gemini.py YOUR_API_KEY
  or set GEMINI_API_KEY environment variable and run without arguments
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.llm_service import GeminiService


def test_gemini_api(api_key=None):
    """Test Gemini API with query generation and bias classification."""
    
    print("=" * 60)
    print("GEMINI API TEST")
    print("=" * 60)
    
    # Initialize service
    service = GeminiService(api_key=api_key)
    
    if not service.enabled:
        print("❌ Gemini service not enabled!")
        print("\nPossible reasons:")
        print("1. API key not set (provide as argument or GEMINI_API_KEY env var)")
        print("2. google-generativeai package not installed")
        print("3. Invalid API key")
        return False
    
    print("✅ Gemini service initialized successfully!\n")
    
    # Test 1: Query Generation
    print("-" * 60)
    print("TEST 1: Query Generation")
    print("-" * 60)
    test_topic = "climate change policy"
    print(f"Topic: {test_topic}")
    print("\nGenerating search queries...")
    
    try:
        queries = service.generate_search_queries(test_topic, num_queries=5)
        print(f"\n✅ Generated {len(queries)} queries:")
        for i, query in enumerate(queries, 1):
            print(f"  {i}. {query}")
    except Exception as e:
        print(f"\n❌ Query generation failed: {e}")
        return False
    
    # Test 2: Bias Classification
    print("\n" + "-" * 60)
    print("TEST 2: Bias Classification")
    print("-" * 60)
    
    test_article = {
        'title': 'Government Unveils Bold New Climate Initiative',
        'text': """The administration announced a sweeping new climate policy today that 
        environmental groups are calling a historic step forward. Critics, however, warn 
        that the economic costs could be devastating for working families."""
    }
    
    print(f"Title: {test_article['title']}")
    print(f"Text: {test_article['text'][:100]}...")
    print("\nClassifying bias...")
    
    try:
        result = service.classify_bias(test_article['text'], test_article['title'])
        print(f"\n✅ Classification complete:")
        print(f"  Bias: {result['ml_bias']}")
        print(f"  Confidence: {result['ml_confidence']:.2%}")
        print(f"  Reasoning: {result['ml_reasoning']}")
    except Exception as e:
        print(f"\n❌ Bias classification failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nGemini API is ready to use!")
    print("Update your .env file with:")
    print(f'GEMINI_API_KEY={api_key or os.getenv("GEMINI_API_KEY")}')
    
    return True


if __name__ == "__main__":
    # Get API key from argument or environment
    api_key = None
    
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        print(f"Using API key from command line argument")
    elif os.getenv("GEMINI_API_KEY"):
        api_key = os.getenv("GEMINI_API_KEY")
        print(f"Using API key from GEMINI_API_KEY environment variable")
    else:
        print("ERROR: No API key provided!")
        print("\nUsage:")
        print("  python test_gemini.py YOUR_API_KEY")
        print("  or")
        print("  export GEMINI_API_KEY=YOUR_API_KEY && python test_gemini.py")
        sys.exit(1)
    
    # Run test
    success = test_gemini_api(api_key)
    sys.exit(0 if success else 1)
