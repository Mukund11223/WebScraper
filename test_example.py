#!/usr/bin/env python3
"""
Test script for Article Scraping & Summarization API

This script demonstrates the functionality of the article scraping and summarization
pipeline with real-world examples.

Usage:
    python test_example.py
"""

import requests
import json
import time
from typing import List, Dict

def test_local_api():
    """Test the local API endpoints"""
    base_url = "http://localhost:8000"
    
    # Test URLs - using publicly accessible news articles
    test_urls = [
        "https://www.bbc.com/news",  # BBC News homepage - may work for testing
        "https://httpbin.org/html",  # Simple HTML page for testing
    ]
    
    print("Testing Article Scraping & Summarization API")
    print("=" * 60)
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print("❌ Health check failed")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure the server is running:")
        print("   python article_main.py --mode api")
        return False
    
    print()
    
    # Test 2: API stats
    print("2. Testing stats endpoint...")
    try:
        response = requests.get(f"{base_url}/stats")
        if response.status_code == 200:
            print("✅ Stats endpoint working")
            stats = response.json()
            print(f"   Model: {stats['api_info']['model']}")
            print(f"   Pipeline Status: {stats['pipeline_status']}")
        else:
            print("❌ Stats endpoint failed")
    except Exception as e:
        print(f"❌ Stats endpoint error: {e}")
    
    print()
    
    # Test 3: Simple summarization endpoint
    print("3. Testing /summarize/ endpoint...")
    try:
        payload = {"urls": test_urls}
        response = requests.post(
            f"{base_url}/summarize/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Summarization endpoint working")
            results = response.json()
            
            for i, result in enumerate(results):
                print(f"\n   Article {i+1}:")
                print(f"   URL: {result['url']}")
                print(f"   Title: {result['title'][:100]}...")
                print(f"   Content Length: {len(result['content'])} characters")
                print(f"   Summary Length: {len(result['summary'])} characters")
                print(f"   Summary: {result['summary'][:200]}...")
                
        else:
            print(f"❌ Summarization failed: HTTP {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Summarization error: {e}")
    
    print()
    
    # Test 4: Extended endpoint
    print("4. Testing /scrape-articles/ endpoint...")
    try:
        payload = {"urls": test_urls[:1]}  # Test with one URL
        response = requests.post(
            f"{base_url}/scrape-articles/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Extended endpoint working")
            results = response.json()
            print(f"   Total URLs: {results['total_urls']}")
            print(f"   Successful: {results['successful']}")
            print(f"   Failed: {results['failed']}")
            print(f"   Processing Time: {results['processing_time_seconds']}s")
            
        else:
            print(f"❌ Extended endpoint failed: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Extended endpoint error: {e}")
    
    return True

def test_pipeline_directly():
    """Test the pipeline components directly"""
    print("\nTesting Pipeline Components Directly")
    print("=" * 60)
    
    try:
        from webscraper.components.article_pipeline import ArticlePipeline
        
        print("1. Initializing pipeline...")
        pipeline = ArticlePipeline(rate_limit=0.5)  # Faster for testing
        print("✅ Pipeline initialized")
        
        # Test with a simple URL
        test_url = "https://httpbin.org/html"
        
        print(f"2. Testing single URL: {test_url}")
        result = pipeline.process_single_url(test_url)
        
        print("✅ Single URL processing completed")
        print(f"   Title: {result['title']}")
        print(f"   Content Length: {len(result['content'])}")
        print(f"   Summary Length: {len(result['summary'])}")
        
        if 'error' in result and result['error']:
            print(f"   Error: {result['error']}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Pipeline test error: {e}")
        return False

def demonstrate_real_world_usage():
    """Demonstrate real-world usage patterns"""
    print("\nReal-World Usage Examples")
    print("=" * 60)
    
    # Example: Processing news articles
    news_urls = [
        "https://httpbin.org/html",  # Safe test URL
    ]
    
    print("Example 1: Processing news articles")
    print("URLs to process:", news_urls)
    
    try:
        response = requests.post(
            "http://localhost:8000/summarize/",
            json={"urls": news_urls},
            timeout=60  # Allow time for processing
        )
        
        if response.status_code == 200:
            articles = response.json()
            
            print(f"✅ Successfully processed {len(articles)} articles")
            
            for i, article in enumerate(articles, 1):
                print(f"\nArticle {i}:")
                print(f"Title: {article['title']}")
                print(f"Content preview: {article['content'][:200]}...")
                print(f"Summary: {article['summary']}")
                
                # Calculate compression ratio
                if len(article['content']) > 0:
                    compression = len(article['summary']) / len(article['content']) * 100
                    print(f"Compression ratio: {compression:.1f}%")
        else:
            print(f"❌ Request failed: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ API not available. Start it with:")
        print("   python article_main.py --mode api")
    except Exception as e:
        print(f"❌ Error: {e}")

def performance_test():
    """Test performance with multiple URLs"""
    print("\nPerformance Test")
    print("=" * 60)
    
    # Multiple test URLs
    test_urls = [
        "https://httpbin.org/html",
        "https://httpbin.org/robots.txt",
    ]
    
    print(f"Testing performance with {len(test_urls)} URLs...")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            "http://localhost:8000/scrape-articles/",
            json={"urls": test_urls},
            timeout=120
        )
        
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            results = response.json()
            
            print("✅ Performance test completed")
            print(f"   Total processing time: {processing_time:.2f}s")
            print(f"   API reported time: {results['processing_time_seconds']}s")
            print(f"   URLs processed: {results['total_urls']}")
            print(f"   Success rate: {results['successful']}/{results['total_urls']}")
            print(f"   Average time per URL: {processing_time/len(test_urls):.2f}s")
            
        else:
            print(f"❌ Performance test failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Performance test error: {e}")

def main():
    """Main test function"""
    print("Article Scraping & Summarization API - Test Suite")
    print("=" * 80)
    print()
    
    # Test 1: API endpoints
    api_success = test_local_api()
    
    if api_success:
        # Test 2: Direct pipeline
        test_pipeline_directly()
        
        # Test 3: Real-world examples
        demonstrate_real_world_usage()
        
        # Test 4: Performance
        performance_test()
    
    print("\n" + "=" * 80)
    print("Test suite completed!")
    print("\nNext steps:")
    print("1. Try the interactive API docs: http://localhost:8000/docs")
    print("2. Test with real article URLs")
    print("3. Experiment with different summarization models")
    print("4. Deploy to production environment")

if __name__ == "__main__":
    main()