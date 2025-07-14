#!/usr/bin/env python3
"""
Article Scraping and Summarization API

This FastAPI application provides endpoints for scraping and summarizing full articles
from any given URLs. It extracts title, content, and metadata, then generates
AI-powered summaries using pre-trained language models.

Author: AI Assistant
Version: 1.0.0
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import List, Optional
import uvicorn
import sys
import argparse
import time
from datetime import datetime
import os

# Import our custom components
from webscraper.components.article_pipeline import ArticlePipeline
from webscraper.Exception.exception import WebScraperException
from webscraper.Logging import logger

# FastAPI app initialization
app = FastAPI(
    title="Article Scraping & Summarization API",
    description="Extract and summarize full articles from any website URL",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global pipeline instance (initialized on startup)
pipeline = None

# Request/Response Models
class ArticleURLRequest(BaseModel):
    """Request model for article URLs"""
    urls: List[str]
    
    @validator('urls')
    def validate_urls(cls, v):
        if not v:
            raise ValueError('At least one URL is required')
        if len(v) > 10:  # Limit to prevent abuse
            raise ValueError('Maximum 10 URLs allowed per request')
        return v

class ArticleResult(BaseModel):
    """Response model for a single article result"""
    url: str
    title: str
    content: str
    summary: str
    
    # Optional metadata fields
    author: Optional[str] = ""
    publish_date: Optional[str] = ""
    description: Optional[str] = ""
    
    # Error field for failed processing
    error: Optional[str] = ""

class ArticleResponse(BaseModel):
    """Response model for multiple articles"""
    results: List[ArticleResult]
    
    # Metadata about the processing
    total_urls: int
    successful: int
    failed: int
    processing_time_seconds: float
    timestamp: str

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the article processing pipeline on startup"""
    global pipeline
    try:
        logger.logging.info("Starting Article Scraping & Summarization API")
        
        # Initialize pipeline with default settings
        pipeline = ArticlePipeline(
            model_name='facebook/bart-large-cnn',  # Default summarization model
            rate_limit=1.0  # 1 second between requests
        )
        
        logger.logging.info("API startup completed successfully")
    except Exception as e:
        logger.logging.error(f"Failed to start API: {str(e)}")
        raise

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.logging.info("Shutting down Article Scraping & Summarization API")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "article-scraping-api",
        "timestamp": datetime.now().isoformat(),
        "pipeline_ready": pipeline is not None
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Article Scraping & Summarization API",
        "version": "1.0.0",
        "description": "Extract and summarize full articles from any website URL",
        "endpoints": {
            "POST /scrape-articles/": "Main endpoint for scraping and summarizing articles",
            "GET /health": "Health check endpoint",
            "GET /docs": "Interactive API documentation",
            "GET /redoc": "Alternative API documentation"
        },
        "example_request": {
            "urls": [
                "https://example.com/article1",
                "https://example.com/article2"
            ]
        }
    }

# Main article processing endpoint
@app.post("/scrape-articles/", response_model=ArticleResponse)
async def scrape_and_summarize_articles(request: ArticleURLRequest):
    """
    Scrape and summarize articles from the provided URLs
    
    This endpoint accepts a list of URLs, scrapes the full article content from each,
    and generates AI-powered summaries using a pre-trained language model.
    
    Args:
        request: ArticleURLRequest containing list of URLs to process
        
    Returns:
        ArticleResponse with scraped content and summaries for each URL
        
    Raises:
        HTTPException: If pipeline is not initialized or processing fails
    """
    start_time = time.time()
    
    try:
        if pipeline is None:
            raise HTTPException(
                status_code=503,
                detail="Article processing pipeline not available. Please try again later."
            )
        
        logger.logging.info(f"Received request to process {len(request.urls)} URLs")
        
        # Validate URLs
        valid_urls = pipeline.validate_urls(request.urls)
        
        if not valid_urls:
            raise HTTPException(
                status_code=400,
                detail="No valid URLs provided"
            )
        
        # Process all URLs
        results = pipeline.process_multiple_urls(valid_urls)
        
        # Convert results to response format
        article_results = []
        successful_count = 0
        failed_count = 0
        
        for result in results:
            # Check if processing was successful
            has_error = 'error' in result and result['error']
            
            if not has_error:
                successful_count += 1
            else:
                failed_count += 1
            
            # Create ArticleResult
            article_result = ArticleResult(
                url=result['url'],
                title=result['title'],
                content=result['content'],
                summary=result['summary'],
                author=result.get('author', ''),
                publish_date=result.get('publish_date', ''),
                description=result.get('description', ''),
                error=result.get('error', '')
            )
            
            article_results.append(article_result)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Create response
        response = ArticleResponse(
            results=article_results,
            total_urls=len(valid_urls),
            successful=successful_count,
            failed=failed_count,
            processing_time_seconds=round(processing_time, 2),
            timestamp=datetime.now().isoformat()
        )
        
        logger.logging.info(
            f"Completed processing {len(valid_urls)} URLs in {processing_time:.2f}s. "
            f"Success: {successful_count}, Failed: {failed_count}"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.logging.error(f"Unexpected error in article processing: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

# Alternative endpoint with simplified response format (as requested in the user requirements)
@app.post("/summarize/")
async def summarize_articles_simple(request: ArticleURLRequest):
    """
    Simplified endpoint that returns results in the exact format specified in requirements
    
    Returns a JSON array with the exact structure:
    [
        {
            "url": "http://example.com/article",
            "title": "Example Article Title",
            "content": "Full article content...",
            "summary": "Summarized content..."
        }
    ]
    """
    try:
        if pipeline is None:
            raise HTTPException(
                status_code=503,
                detail="Article processing pipeline not available"
            )
        
        # Validate URLs
        valid_urls = pipeline.validate_urls(request.urls)
        
        if not valid_urls:
            raise HTTPException(
                status_code=400,
                detail="No valid URLs provided"
            )
        
        # Process URLs
        results = pipeline.process_multiple_urls(valid_urls)
        
        # Format results to match the exact specification
        simplified_results = []
        for result in results:
            simplified_result = {
                "url": result['url'],
                "title": result['title'],
                "content": result['content'],
                "summary": result['summary']
            }
            simplified_results.append(simplified_result)
        
        return simplified_results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.logging.error(f"Error in simplified summarization: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )

# Statistics endpoint
@app.get("/stats")
async def get_api_stats():
    """Get API statistics and information"""
    return {
        "api_info": {
            "name": "Article Scraping & Summarization API",
            "version": "1.0.0",
            "model": "facebook/bart-large-cnn",
            "rate_limit": "1 second between requests"
        },
        "pipeline_status": "ready" if pipeline is not None else "not_ready",
        "supported_features": [
            "Full article content extraction",
            "AI-powered summarization",
            "Multiple URL processing",
            "Rate limiting",
            "Error handling",
            "Metadata extraction"
        ],
        "limits": {
            "max_urls_per_request": 10,
            "request_timeout": "30 seconds",
            "rate_limit": "1 second between requests"
        }
    }

# Command line interface functions
def run_single_url(url: str):
    """Process a single URL from command line"""
    try:
        # Initialize pipeline
        article_pipeline = ArticlePipeline()
        
        # Process URL
        result = article_pipeline.process_single_url(url)
        
        # Display results
        print("=" * 80)
        print("ARTICLE SCRAPING & SUMMARIZATION RESULTS")
        print("=" * 80)
        print(f"URL: {result['url']}")
        print(f"Title: {result['title']}")
        print(f"Author: {result.get('author', 'Not found')}")
        print(f"Publish Date: {result.get('publish_date', 'Not found')}")
        print("\nCONTENT:")
        print("-" * 40)
        content = result['content']
        print(content[:500] + "..." if len(content) > 500 else content)
        print("\nSUMMARY:")
        print("-" * 40)
        print(result['summary'])
        
        if 'error' in result and result['error']:
            print(f"\nERROR: {result['error']}")
        
    except Exception as e:
        print(f"Error processing URL: {str(e)}")

def run_api_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the FastAPI server"""
    print(f"Starting Article Scraping & Summarization API on {host}:{port}")
    print(f"API Documentation: http://localhost:{port}/docs")
    print(f"Main endpoint: POST /scrape-articles/")
    print(f"Simple endpoint: POST /summarize/")
    
    uvicorn.run(app, host=host, port=port)

def main():
    """Main function with command line options"""
    parser = argparse.ArgumentParser(description="Article Scraping and Summarization API")
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