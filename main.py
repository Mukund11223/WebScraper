# main.py - Simplified Web Scraping & Summarization API
from webscraper.pipeline import WebScrapingPipeline
from webscraper.Exception.exception import WebScraperException
from webscraper.Logging import logger
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import uvicorn
import sys
import argparse
import asyncio
import concurrent.futures
from functools import partial
import time

# FastAPI app
app = FastAPI(title="Web Scraping & Summarization API", version="1.0.0")

# Request/Response Models
class SummarizeRequest(BaseModel):
    urls: List[str]

class HeadlineResult(BaseModel):
    headline: str
    summary: str
    link: str

class URLResult(BaseModel):
    url: str
    status: str
    total_headlines: int = 0
    individual_summaries: List[HeadlineResult] = []
    overall_summary: str = ""
    error: str = ""

class SummarizeResponse(BaseModel):
    total_urls: int
    successful: int
    failed: int
    results: List[URLResult]

# Helper function to process a single URL
def process_single_url(url: str) -> URLResult:
    """Process a single URL and return URLResult"""
    start_time = time.time()
    logger.logging.info(f"STARTED processing {url} at {time.strftime('%H:%M:%S')}")
    
    try:
        # Run pipeline for each URL
        pipeline = WebScrapingPipeline(url)
        pipeline_result = pipeline.run_pipeline()
        
        # Process individual summaries if available
        individual_summaries = []
        if 'individual_summaries' in pipeline_result:
            for item in pipeline_result['individual_summaries']:
                individual_summaries.append(HeadlineResult(
                    headline=item.get('headline', ''),
                    summary=item.get('summary', ''),
                    link=item.get('link', '')
                ))
        
        # Create successful result
        result = URLResult(
            url=url,
            status="success",
            total_headlines=pipeline_result['total_headlines'],
            individual_summaries=individual_summaries,
            overall_summary=pipeline_result.get('overall_summary', '')
        )
        
        end_time = time.time()
        logger.logging.info(f"COMPLETED processing {url} at {time.strftime('%H:%M:%S')} (took {end_time - start_time:.2f}s)")
        return result
        
    except Exception as e:
        # Create failed result
        result = URLResult(
            url=url,
            status="failed",
            error=str(e)
        )
        
        end_time = time.time()
        logger.logging.error(f"FAILED processing {url} at {time.strftime('%H:%M:%S')} (took {end_time - start_time:.2f}s): {str(e)}")
        return result

# Main API Endpoint
@app.post("/summarize-urls/", response_model=SummarizeResponse)
async def summarize_multiple_urls(request: SummarizeRequest):
    """
    Summarize headlines from multiple URLs
    """
    overall_start_time = time.time()
    logger.logging.info(f"Processing {len(request.urls)} URLs - OVERALL START at {time.strftime('%H:%M:%S')}")
    
    # Use ThreadPoolExecutor for concurrent processing
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Submit all URLs for concurrent processing
        futures = [
            loop.run_in_executor(executor, process_single_url, url)
            for url in request.urls
        ]
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*futures)
    
    # Count successful and failed results
    successful_count = sum(1 for result in results if result.status == "success")
    failed_count = sum(1 for result in results if result.status == "failed")
    
    overall_end_time = time.time()
    total_time = overall_end_time - overall_start_time
    logger.logging.info(f"Processing {len(request.urls)} URLs - OVERALL COMPLETE at {time.strftime('%H:%M:%S')} (total time: {total_time:.2f}s)")
    
    return SummarizeResponse(
        total_urls=len(request.urls),
        successful=successful_count,
        failed=failed_count,
        results=results
    )

# Health Check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "web-scraping-api"}

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Web Scraping & Summarization API",
        "endpoint": "/summarize-urls/ - POST request with list of URLs",
        "docs": "/docs for API documentation"
    }

# Command Line Functions
def run_single_url(url: str):
    """Process a single URL from command line"""
    try:
        pipeline = WebScrapingPipeline(url)
        results = pipeline.run_pipeline()
        
        print("="*50)
        print("WEB SCRAPING RESULTS")
        print("="*50)
        print(f"Website: {results['url']}")
        print(f"Headlines Found: {results['total_headlines']}")
        
        # Display individual summaries if available
        if 'individual_summaries' in results and results['individual_summaries']:
            print("\nINDIVIDUAL SUMMARIES:")
            print("-" * 20)
            for i, item in enumerate(results['individual_summaries'], 1):
                print(f"{i}. Headline: {item.get('headline', 'N/A')}")
                print(f"   Summary: {item.get('summary', 'N/A')}")
                print(f"   Link: {item.get('link', 'N/A')}")
                print()
        
        # Display overall summary
        if 'overall_summary' in results and results['overall_summary']:
            print("OVERALL SUMMARY:")
            print("-" * 15)
            print(results['overall_summary'])
        
        print(f"\nData saved to: {results.get('raw_data_file', 'N/A')}")
        
    except Exception as e:
        logger.logging.error(f"Failed to process {url}: {str(e)}")
        print(f"Error: {str(e)}")

def run_api_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the API server"""
    print(f"Starting API server on {host}:{port}")
    print("API Documentation: http://localhost:8000/docs")
    print("Main endpoint: POST /summarize-urls/")
    uvicorn.run(app, host=host, port=port)

def main():
    """Main function with command line options"""
    parser = argparse.ArgumentParser(description="Web Scraping and Summarization Tool")
    parser.add_argument("--mode", choices=["api", "url"], default="api",
                       help="Mode: 'api' to start server, 'url' to process single URL")
    parser.add_argument("--url", type=str, help="URL to process (required for --mode url)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="API server host")
    parser.add_argument("--port", type=int, default=8000, help="API server port")
    
    args = parser.parse_args()
    
    try:
        if args.mode == "api":
            run_api_server(args.host, args.port)
        elif args.mode == "url":
            if not args.url:
                print("Error: --url is required when using --mode url")
                sys.exit(1)
            run_single_url(args.url)
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()