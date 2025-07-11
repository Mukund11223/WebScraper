import sys
from webscraper.components.scraper import WebScraper
from webscraper.components.summarize import LLMSummarizer
from webscraper.Exception.exception import WebScraperException
from webscraper.Logging import logger

class WebScrapingPipeline:
    def __init__(self, target_url, model_name='facebook/bart-large-cnn'):
        """Initialize the complete pipeline"""
        self.target_url = target_url
        self.scraper = WebScraper(target_url)
        self.summarizer = LLMSummarizer(model_name)
        
    def run_pipeline(self):
        """Run the complete scraping and summarization pipeline"""
        try:
            logger.logging.info("Starting web scraping pipeline")
            
            # Step 1: Fetch the webpage
            html_content = self.scraper.fetch_page()
            
            # Step 2: Parse headlines
            headlines = self.scraper.parse_headlines(html_content)
            
            # Step 3: Save raw data
            raw_data_file = self.scraper.save_data(headlines, format='json')
            
            # Step 4: Generate overall summary
            overall_summary = self.summarizer.summarize_headlines(headlines)
            
            # Step 5: Generate individual summaries
            individual_summaries = self.summarizer.summarize_individual_headlines(headlines, self.scraper)
            
            # Step 6: Prepare final results
            results = {
                'url': self.target_url,
                'total_headlines': len(headlines),
                'overall_summary': overall_summary,
                'individual_summaries': individual_summaries,
                'raw_data_file': raw_data_file
            }
            
            # Step 7: Save summarized results
            summary_file = self.scraper.save_data(results, format='json')
            
            logger.logging.info("Pipeline completed successfully")
            return results
            
        except Exception as e:
            logger.logging.error(f"Pipeline failed: {str(e)}")
            raise WebScraperException(e, sys)