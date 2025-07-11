import sys
from transformers import pipeline
from webscraper.Exception.exception import WebScraperException
from webscraper.Logging import logger

class LLMSummarizer:
    def __init__(self, model_name='facebook/bart-large-cnn'):
        """Initialize the summarizer with specified model"""
        try:
            logger.logging.info(f"Loading model: {model_name}")
            self.summarizer = pipeline("summarization", model=model_name)
            logger.logging.info("Model loaded successfully")
        except Exception as e:
            logger.logging.error(f"Error loading model: {str(e)}")
            raise WebScraperException(e, sys)
    
    def summarize_headlines(self, headlines, max_length=150, min_length=50):
        """Summarize a list of headlines"""
        try:
            logger.logging.info(f"Summarizing {len(headlines)} headlines")
            
            # Combine headlines into text
            text_to_summarize = " ".join([item['headline'] for item in headlines])
            
            # Truncate if too long (BART has token limits)
            if len(text_to_summarize) > 1000:
                text_to_summarize = text_to_summarize[:1000]
            
            # Generate summary
            summary = self.summarizer(
                text_to_summarize,
                max_length=max_length,
                min_length=min_length,
                do_sample=False # same summary for same output
            )
            
            logger.logging.info("Summary generated successfully")
            return summary[0]['summary_text']
            
        except Exception as e:
            logger.logging.error(f"Error generating summary: {str(e)}")
            raise WebScraperException(e, sys)
    
    def summarize_individual_headlines(self, headlines, scraper):
        """Summarize each news article content"""
        try:
            logger.logging.info("Summarizing individual news articles")
            summarized_articles = []
            
            for item in headlines:
                # Get full article content
                article_content = scraper.get_article_content(item['link'])
                
                if article_content:
                    try:
                        # Summarize the actual article content
                        summary = self.summarizer(
                            article_content,
                            max_length=100,
                            min_length=30,
                            do_sample=False
                        )
                        summarized_articles.append({
                            'headline': item['headline'],
                            'summary': summary[0]['summary_text'],
                            'link': item['link']
                        })
                    except:
                        # If summarization fails, use headline
                        summarized_articles.append({
                            'headline': item['headline'],
                            'summary': item['headline'],
                            'link': item['link']
                        })
                else:
                    # If no content found, use headline
                    summarized_articles.append({
                        'headline': item['headline'],
                        'summary': item['headline'],
                        'link': item['link']
                    })
            
            logger.logging.info("Individual articles summarized successfully")
            return summarized_articles
            
        except Exception as e:
            logger.logging.error(f"Error summarizing individual articles: {str(e)}")
            raise WebScraperException(e, sys)
