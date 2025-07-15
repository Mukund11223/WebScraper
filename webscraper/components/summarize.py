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
    
    def summarize_headlines(self, website_summary_data, max_length=150, min_length=50):
        """
        Summarize the overall content of a website based on the extracted summary data.
        'website_summary_data' is expected to be the dictionary returned by WebScraper.parse_headlines
        (which extracts general website summary elements like title, meta, headings, paragraphs).
        """
        try:
            logger.logging.info("Generating overall website summary from extracted data.")
            
            text_components = []
            if website_summary_data.get('title') and website_summary_data['title'] != "No Title Found":
                text_components.append(f"Title: {website_summary_data['title']}")
            if website_summary_data.get('meta_description') and website_summary_data['meta_description'] != "No Meta Description Found":
                text_components.append(f"Description: {website_summary_data['meta_description']}")
            if website_summary_data.get('main_headings'):
                text_components.extend(website_summary_data['main_headings'])
            if website_summary_data.get('prominent_paragraphs'):
                text_components.extend(website_summary_data['prominent_paragraphs'])
            
            # Combine relevant components into a single text string for summarization
            text_to_summarize = " ".join(text_components)
            
            if not text_to_summarize.strip():
                logger.logging.warning("No sufficient text components found for overall summarization.")
                return "No content available for overall summary."

            # Truncate if too long (BART has token limits, typically around 1024 tokens)
            # A simple character limit is a rough proxy for token limit
            if len(text_to_summarize) > 3000: # Increased limit as content can be richer
                text_to_summarize = text_to_summarize[:3000]
            
            # Generate summary
            summary = self.summarizer(
                text_to_summarize,
                max_length=max_length,
                min_length=min_length,
                do_sample=False
            )
            
            logger.logging.info("Overall website summary generated successfully")
            return summary[0]['summary_text']
            
        except Exception as e:
            logger.logging.error(f"Error generating overall website summary: {str(e)}")
            raise WebScraperException(e, sys)
    
    def summarize_individual_headlines(self, prominent_paragraphs, max_length=100, min_length=30):
        """
        Summarize individual prominent paragraphs or key textual blocks from the website.
        'prominent_paragraphs' is expected to be a list of strings extracted from the website.
        This function no longer fetches external content but operates on provided text blocks.
        """
        try:
            logger.logging.info(f"Summarizing individual prominent text blocks. Found {len(prominent_paragraphs)} blocks.")
            summarized_blocks = []
            
            if not prominent_paragraphs:
                logger.logging.warning("No prominent paragraphs provided for individual summarization.")
                return []

            for i, block_text in enumerate(prominent_paragraphs):
                # Ensure the block is substantial enough to summarize
                if block_text and len(block_text) > min_length:
                    try:
                        # Truncate individual block if very long before sending to model
                        if len(block_text) > 1000:
                            block_text = block_text[:1000]

                        summary = self.summarizer(
                            block_text,
                            max_length=max_length,
                            min_length=min_length,
                            do_sample=False
                        )
                        summarized_blocks.append({
                            'original_text_snippet': block_text[:150] + "..." if len(block_text) > 150 else block_text, # Snippet for context
                            'summary': summary[0]['summary_text']
                        })
                        logger.logging.debug(f"Summarized block {i+1}/{len(prominent_paragraphs)}")
                    except Exception as summarization_e:
                        logger.logging.warning(f"Failed to summarize block {i+1}: {str(summarization_e)}. Using original snippet.")
                        summarized_blocks.append({
                            'original_text_snippet': block_text[:150] + "..." if len(block_text) > 150 else block_text,
                            'summary': block_text # Fallback to original snippet if summarization fails
                        })
                else:
                    logger.logging.debug(f"Skipping small block {i+1}. Length: {len(block_text) if block_text else 0}")
                    # Optionally, include even small blocks as their original text if meaningful
                    # summarized_blocks.append({
                    #     'original_text_snippet': block_text,
                    #     'summary': block_text
                    # })
            
            logger.logging.info("Individual prominent text blocks summarized successfully")
            return summarized_blocks
            
        except Exception as e:
            logger.logging.error(f"Error summarizing individual text blocks: {str(e)}")
            raise WebScraperException(e, sys)