import requests
import os
from bs4 import BeautifulSoup
import pandas as pd
import sys
import json
from webscraper.Exception.exception import WebScraperException
from webscraper.Logging import logger

class WebScraper:
    def __init__(self, url):
        self.url = url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def fetch_page(self):
        """Fetch the web page content"""
        try:
            logger.logging.info(f"Fetching page: {self.url}")
            response = requests.get(self.url, headers=self.headers)
            response.raise_for_status()
            logger.logging.info("Page fetched successfully")
            return response.text
        except Exception as e:
            logger.logging.error(f"Error fetching page: {str(e)}")
            raise WebScraperException(e, sys)
    
    def parse_headlines(self, html_content):
        """Parse headlines from Times of India"""
        try:
            logger.logging.info("Parsing headlines from HTML content")
            soup = BeautifulSoup(html_content, 'html.parser')
            
            headlines = []
            
            # Find news links that look like articles
            news_links = soup.find_all('a', href=lambda x: x and '/news/' in x)
            
            # Extract from news links
            for link in news_links[:10]:  # Limit to 10 to avoid too much processing
                text = link.get_text(strip=True)
                if text and len(text) > 20:
                    full_link = link['href'] if link['href'].startswith('http') else f"https://timesofindia.indiatimes.com{link['href']}"
                    headlines.append({
                        'headline': text,
                        'link': full_link
                    })
            
            # Remove duplicates
            unique_headlines = []
            seen = set()
            for item in headlines:
                if item['headline'] not in seen:
                    seen.add(item['headline'])
                    unique_headlines.append(item)
            
            logger.logging.info(f"Parsed {len(unique_headlines)} unique headlines")
            return unique_headlines
            
        except Exception as e:
            logger.logging.error(f"Error parsing headlines: {str(e)}")
            raise WebScraperException(e, sys)
    
    def get_article_content(self, article_url):
        """Fetch full article content from URL"""
        try:
            logger.logging.info(f"Fetching article content from: {article_url}")
            response = requests.get(article_url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to find article content (common selectors for Times of India)
            content_selectors = [
                'div[class*="story"]',
                'div[class*="article"]',
                'div[class*="content"]',
                'p'
            ]
            
            content_text = ""
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content_text = " ".join([elem.get_text(strip=True) for elem in elements])
                    break
            
            # Clean and limit content
            if content_text and len(content_text) > 200:
                content_text = content_text[:2000]  # Limit for processing
                logger.logging.info("Article content extracted successfully")
                return content_text
            else:
                logger.logging.warning("No substantial content found")
                return None
                
        except Exception as e:
            logger.logging.error(f"Error fetching article content: {str(e)}")
            return None
    
    def save_data(self, data, format='json'):
        """Save scraped data to file"""
        try:
            
            os.makedirs('data', exist_ok=True)
            
            if format == 'json':
                filename = f"data/headlines_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            elif format == 'csv':
                filename = f"data/headlines_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
                df = pd.DataFrame(data)
                df.to_csv(filename, index=False, encoding='utf-8')
            
            logger.logging.info(f"Data saved to {filename}")
            return filename
            
        except Exception as e:
            logger.logging.error(f"Error saving data: {str(e)}")
            raise WebScraperException(e, sys)