import requests
import time
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Dict, Optional
import sys
import asyncio
import aiohttp
from webscraper.Exception.exception import WebScraperException
from webscraper.Logging import logger

class ArticleScraper:
    def __init__(self, rate_limit: float = 1.0):
        """
        Initialize the article scraper
        
        Args:
            rate_limit: Minimum time between requests in seconds
        """
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def _rate_limit_wait(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit:
            sleep_time = self.rate_limit - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def fetch_article(self, url: str) -> Dict[str, str]:
        """
        Fetch and extract article content from a URL
        
        Args:
            url: The article URL to scrape
            
        Returns:
            Dictionary containing title, content, and metadata
        """
        try:
            self._rate_limit_wait()
            logger.logging.info(f"Fetching article from: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract article data
            article_data = {
                'url': url,
                'title': self._extract_title(soup),
                'content': self._extract_content(soup),
                'author': self._extract_author(soup),
                'publish_date': self._extract_publish_date(soup),
                'description': self._extract_description(soup)
            }
            
            logger.logging.info(f"Successfully extracted article from {url}")
            return article_data
            
        except requests.RequestException as e:
            logger.logging.error(f"Request error for {url}: {str(e)}")
            raise WebScraperException(f"Failed to fetch article from {url}: {str(e)}", sys)
        except Exception as e:
            logger.logging.error(f"Unexpected error for {url}: {str(e)}")
            raise WebScraperException(f"Error processing article from {url}: {str(e)}", sys)
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title"""
        # Try multiple selectors for title
        title_selectors = [
            'h1',
            'title',
            '[property="og:title"]',
            '[name="twitter:title"]',
            '.article-title',
            '.post-title',
            '.entry-title',
            'h1.title',
            'h1.headline'
        ]
        
        for selector in title_selectors:
            if selector.startswith('['):
                element = soup.select_one(selector)
                if element:
                    return element.get('content', '').strip()
            else:
                element = soup.find(selector)
                if element and element.get_text(strip=True):
                    return element.get_text(strip=True)
        
        return "No title found"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content"""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form']):
            element.decompose()
        
        # Try multiple selectors for content
        content_selectors = [
            'article',
            '[role="main"]',
            '.article-content',
            '.post-content',
            '.entry-content',
            '.content',
            '.article-body',
            '.story-body',
            '.post-body',
            'main',
            '.main-content'
        ]
        
        # Try specific selectors first
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                content = self._clean_text(element.get_text())
                if len(content) > 200:  # Ensure substantial content
                    return content
        
        # Fallback: extract all paragraphs
        paragraphs = soup.find_all('p')
        if paragraphs:
            content = ' '.join([p.get_text() for p in paragraphs])
            content = self._clean_text(content)
            if len(content) > 200:
                return content
        
        # Last resort: get all text
        all_text = soup.get_text()
        content = self._clean_text(all_text)
        return content if content else "No content found"
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract article author"""
        author_selectors = [
            '[rel="author"]',
            '[property="article:author"]',
            '[name="author"]',
            '.author',
            '.byline',
            '.post-author',
            '.article-author'
        ]
        
        for selector in author_selectors:
            if selector.startswith('['):
                element = soup.select_one(selector)
                if element:
                    return element.get('content', element.get_text(strip=True))
            else:
                element = soup.select_one(selector)
                if element:
                    return element.get_text(strip=True)
        
        return ""
    
    def _extract_publish_date(self, soup: BeautifulSoup) -> str:
        """Extract article publish date"""
        date_selectors = [
            '[property="article:published_time"]',
            '[name="publish_date"]',
            '[datetime]',
            '.publish-date',
            '.date',
            '.post-date',
            '.article-date'
        ]
        
        for selector in date_selectors:
            if selector.startswith('['):
                element = soup.select_one(selector)
                if element:
                    return element.get('content', element.get('datetime', ''))
            else:
                element = soup.select_one(selector)
                if element:
                    return element.get_text(strip=True)
        
        return ""
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract article description/summary"""
        desc_selectors = [
            '[name="description"]',
            '[property="og:description"]',
            '[name="twitter:description"]'
        ]
        
        for selector in desc_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get('content', '').strip()
        
        return ""
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common noise patterns
        noise_patterns = [
            r'Advertisement\s*',
            r'ADVERTISEMENT\s*',
            r'Click here.*?(?=\.|$)',
            r'Read more.*?(?=\.|$)',
            r'Continue reading.*?(?=\.|$)',
            r'Sign up.*?(?=\.|$)',
            r'Subscribe.*?(?=\.|$)'
        ]
        
        for pattern in noise_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    async def fetch_multiple_articles(self, urls: list) -> list:
        """
        Fetch multiple articles asynchronously with rate limiting
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            List of article data dictionaries
        """
        results = []
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers=self.headers
        ) as session:
            
            semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
            
            async def fetch_single(url):
                async with semaphore:
                    await asyncio.sleep(self.rate_limit)  # Rate limiting
                    try:
                        async with session.get(url) as response:
                            if response.status == 200:
                                html = await response.text()
                                soup = BeautifulSoup(html, 'html.parser')
                                
                                return {
                                    'url': url,
                                    'title': self._extract_title(soup),
                                    'content': self._extract_content(soup),
                                    'author': self._extract_author(soup),
                                    'publish_date': self._extract_publish_date(soup),
                                    'description': self._extract_description(soup)
                                }
                            else:
                                raise Exception(f"HTTP {response.status}")
                    except Exception as e:
                        logger.logging.error(f"Error fetching {url}: {str(e)}")
                        raise
            
            # Execute all requests
            tasks = [fetch_single(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            return results