import sys
import asyncio
from typing import List, Dict, Any
from webscraper.components.article_scraper import ArticleScraper
from webscraper.components.article_summarizer import ArticleSummarizer
from webscraper.Exception.exception import WebScraperException
from webscraper.Logging import logger

class ArticlePipeline:
    def __init__(self, 
                 model_name: str = 'facebook/bart-large-cnn',
                 rate_limit: float = 1.0):
        """
        Initialize the article processing pipeline
        
        Args:
            model_name: HuggingFace model name for summarization
            rate_limit: Minimum time between requests in seconds
        """
        try:
            logger.logging.info("Initializing Article Pipeline")
            
            # Initialize components
            self.scraper = ArticleScraper(rate_limit=rate_limit)
            self.summarizer = ArticleSummarizer(model_name=model_name)
            
            logger.logging.info("Article Pipeline initialized successfully")
            
        except Exception as e:
            logger.logging.error(f"Failed to initialize Article Pipeline: {str(e)}")
            raise WebScraperException(f"Pipeline initialization failed: {str(e)}", sys)
    
    def process_single_url(self, url: str) -> Dict[str, Any]:
        """
        Process a single URL: scrape content and generate summary
        
        Args:
            url: The URL to process
            
        Returns:
            Dictionary with processed article data
        """
        try:
            logger.logging.info(f"Processing single URL: {url}")
            
            # Step 1: Scrape article content
            article_data = self.scraper.fetch_article(url)
            
            # Step 2: Generate summary
            summary = self.summarizer.summarize_article(article_data)
            
            # Step 3: Prepare response
            result = {
                "url": url,
                "title": article_data.get('title', 'No title found'),
                "content": article_data.get('content', 'No content found'),
                "summary": summary,
                "author": article_data.get('author', ''),
                "publish_date": article_data.get('publish_date', ''),
                "description": article_data.get('description', '')
            }
            
            logger.logging.info(f"Successfully processed URL: {url}")
            return result
            
        except Exception as e:
            logger.logging.error(f"Error processing URL {url}: {str(e)}")
            return {
                "url": url,
                "title": "Error",
                "content": "Failed to extract content",
                "summary": f"Processing failed: {str(e)}",
                "author": "",
                "publish_date": "",
                "description": "",
                "error": str(e)
            }
    
    def process_multiple_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Process multiple URLs sequentially with rate limiting
        
        Args:
            urls: List of URLs to process
            
        Returns:
            List of processed article data
        """
        results = []
        
        logger.logging.info(f"Processing {len(urls)} URLs sequentially")
        
        for i, url in enumerate(urls, 1):
            try:
                logger.logging.info(f"Processing URL {i}/{len(urls)}: {url}")
                
                result = self.process_single_url(url)
                results.append(result)
                
                logger.logging.info(f"Completed URL {i}/{len(urls)}")
                
            except Exception as e:
                logger.logging.error(f"Failed to process URL {i}/{len(urls)} ({url}): {str(e)}")
                results.append({
                    "url": url,
                    "title": "Error",
                    "content": "Failed to extract content",
                    "summary": f"Processing failed: {str(e)}",
                    "author": "",
                    "publish_date": "",
                    "description": "",
                    "error": str(e)
                })
        
        logger.logging.info(f"Completed processing {len(urls)} URLs")
        return results
    
    async def process_multiple_urls_async(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Process multiple URLs asynchronously (experimental)
        
        Args:
            urls: List of URLs to process
            
        Returns:
            List of processed article data
        """
        logger.logging.info(f"Processing {len(urls)} URLs asynchronously")
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(3)  # Max 3 concurrent requests
        
        async def process_url_async(url: str) -> Dict[str, Any]:
            async with semaphore:
                try:
                    # Note: This is a simplified async version
                    # For full async support, the scraper and summarizer would need async methods
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, self.process_single_url, url)
                    return result
                except Exception as e:
                    logger.logging.error(f"Async processing failed for {url}: {str(e)}")
                    return {
                        "url": url,
                        "title": "Error",
                        "content": "Failed to extract content",
                        "summary": f"Async processing failed: {str(e)}",
                        "author": "",
                        "publish_date": "",
                        "description": "",
                        "error": str(e)
                    }
        
        # Execute all URLs concurrently
        tasks = [process_url_async(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions that occurred
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.logging.error(f"Exception for URL {urls[i]}: {str(result)}")
                processed_results.append({
                    "url": urls[i],
                    "title": "Error",
                    "content": "Failed to extract content",
                    "summary": f"Exception occurred: {str(result)}",
                    "author": "",
                    "publish_date": "",
                    "description": "",
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        logger.logging.info(f"Completed async processing of {len(urls)} URLs")
        return processed_results
    
    def get_pipeline_stats(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate statistics about the pipeline results
        
        Args:
            results: List of processed article results
            
        Returns:
            Statistics dictionary
        """
        total_urls = len(results)
        successful = sum(1 for r in results if 'error' not in r or not r['error'])
        failed = total_urls - successful
        
        # Content statistics
        total_content_length = sum(len(r.get('content', '')) for r in results if 'error' not in r)
        total_summary_length = sum(len(r.get('summary', '')) for r in results if 'error' not in r)
        
        avg_content_length = total_content_length / successful if successful > 0 else 0
        avg_summary_length = total_summary_length / successful if successful > 0 else 0
        
        stats = {
            "total_urls": total_urls,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total_urls * 100) if total_urls > 0 else 0,
            "average_content_length": avg_content_length,
            "average_summary_length": avg_summary_length,
            "compression_ratio": (avg_summary_length / avg_content_length * 100) if avg_content_length > 0 else 0
        }
        
        return stats
    
    def validate_urls(self, urls: List[str]) -> List[str]:
        """
        Validate and clean URLs
        
        Args:
            urls: List of URLs to validate
            
        Returns:
            List of valid URLs
        """
        valid_urls = []
        
        for url in urls:
            url = url.strip()
            
            # Basic URL validation
            if not url:
                continue
                
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Simple URL pattern check
            if '.' in url and len(url) > 10:
                valid_urls.append(url)
            else:
                logger.logging.warning(f"Invalid URL skipped: {url}")
        
        logger.logging.info(f"Validated {len(valid_urls)} out of {len(urls)} URLs")
        return valid_urls