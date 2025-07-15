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
    
    def parse_headlines(self, html_content): # Renamed conceptually to extract_summary in explanation
        """
        Extracts a general summary of the website from the HTML content.
        This includes the page title, meta description, main headings,
        and a selection of prominent paragraphs.
        """
        try:
            logger.logging.info("Extracting general summary from HTML content")
            soup = BeautifulSoup(html_content, 'html.parser')
            
            summary_data = {}
            
            # 1. Page Title
            title_tag = soup.find('title')
            summary_data['title'] = title_tag.get_text(strip=True) if title_tag else "No Title Found"
            
            # 2. Meta Description
            meta_description = soup.find('meta', attrs={'name': 'description'})
            summary_data['meta_description'] = meta_description['content'].strip() if meta_description and 'content' in meta_description.attrs else "No Meta Description Found"
            
            # 3. Main Headings (h1, h2)
            headings = []
            for tag in soup.find_all(['h1', 'h2']):
                text = tag.get_text(strip=True)
                if text:
                    headings.append(text)
            summary_data['main_headings'] = headings[:5] # Limit to top 5 for conciseness
            
            # 4. Prominent Paragraphs (attempt to get some meaningful text)
            # Prioritize paragraphs within main content areas, if identifiable
            main_content_selectors = [
                'main', 'article', 'div[role="main"]',
                'div[class*="content"]', 'div[class*="body"]',
                'div#main-content', 'div#article-content'
            ]
            
            paragraphs = []
            for selector in main_content_selectors:
                content_block = soup.select_one(selector)
                if content_block:
                    paras = content_block.find_all('p')
                    paragraphs.extend([p.get_text(strip=True) for p in paras if p.get_text(strip=True) and len(p.get_text(strip=True)) > 50]) # Only add substantial paragraphs
                    if paragraphs:
                        break # Found content in a main block, stop searching
            
            # If no paragraphs from main selectors, fall back to general paragraphs
            if not paragraphs:
                all_paras = soup.find_all('p')
                paragraphs.extend([p.get_text(strip=True) for p in all_paras if p.get_text(strip=True) and len(p.get_text(strip=True)) > 50])
            
            summary_data['prominent_paragraphs'] = paragraphs[:3] # Limit to top 3 for summary
            
            logger.logging.info("General summary extracted successfully")
            return summary_data
            
        except Exception as e:
            logger.logging.error(f"Error extracting general summary: {str(e)}")
            raise WebScraperException(e, sys)
    
    def get_article_content(self, article_url): # Renamed conceptually to get_linked_page_content in explanation
        """
        Fetches the main textual content from a given URL.
        This is generalized to extract content from any linked page, not just articles.
        """
        try:
            logger.logging.info(f"Fetching content from linked page: {article_url}")
            response = requests.get(article_url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to find main textual content using common selectors
            content_selectors = [
                'main',                         # HTML5 semantic main content
                'article',                      # HTML5 semantic article content
                'div[role="main"]',             # ARIA role for main content
                'div[class*="content-body"]',   # Common class names
                'div[class*="article-body"]',
                'div[id*="main-content"]',
                'div[id*="article-content"]',
                'div[class*="post-content"]',
                'div[class*="page-content"]',
                'p'                             # General paragraphs as a last resort
            ]
            
            content_text = ""
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    # Concatenate text from all matched elements under this selector
                    content_text = " ".join([elem.get_text(strip=True) for elem in elements])
                    if content_text and len(content_text) > 100: # Ensure substantial content
                        break
            
            # Clean and limit content
            if content_text and len(content_text) > 200:
                content_text = content_text[:2000]  # Limit for processing and storage
                logger.logging.info("Linked page content extracted successfully")
                return content_text
            else:
                logger.logging.warning(f"No substantial content found for {article_url}")
                return None
                
        except Exception as e:
            logger.logging.error(f"Error fetching linked page content for {article_url}: {str(e)}")
            return None
    
    def save_data(self, data, format='json'):
        """Save scraped data to file"""
        try:
            
            os.makedirs('data', exist_ok=True)
            
            if format == 'json':
                filename = f"data/summary_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            elif format == 'csv':
                filename = f"data/summary_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
                # For CSV, assume 'data' is a list of dictionaries if multiple items,
                # or convert single dictionary summary to a suitable DataFrame.
                if isinstance(data, dict):
                    df = pd.DataFrame([data]) # Wrap in list for DataFrame conversion
                else:
                    df = pd.DataFrame(data)
                df.to_csv(filename, index=False, encoding='utf-8')
            
            logger.logging.info(f"Data saved to {filename}")
            return filename
            
        except Exception as e:
            logger.logging.error(f"Error saving data: {str(e)}")
            raise WebScraperException(e, sys)