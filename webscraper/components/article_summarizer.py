import sys
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
from typing import Dict, List
import re
from webscraper.Exception.exception import WebScraperException
from webscraper.Logging import logger

class ArticleSummarizer:
    def __init__(self, model_name: str = 'facebook/bart-large-cnn'):
        """
        Initialize the article summarizer with specified model
        
        Args:
            model_name: HuggingFace model name for summarization
        """
        try:
            logger.logging.info(f"Loading summarization model: {model_name}")
            
            # Check if CUDA is available
            device = 0 if torch.cuda.is_available() else -1
            logger.logging.info(f"Using device: {'GPU' if device == 0 else 'CPU'}")
            
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            
            # Create pipeline
            self.summarizer = pipeline(
                "summarization",
                model=self.model,
                tokenizer=self.tokenizer,
                device=device,
                framework="pt"
            )
            
            # Model configuration
            self.max_input_length = self.tokenizer.model_max_length
            self.max_chunk_length = min(1024, self.max_input_length - 50)  # Leave room for special tokens
            
            logger.logging.info("Summarization model loaded successfully")
            
        except Exception as e:
            logger.logging.error(f"Error loading summarization model: {str(e)}")
            raise WebScraperException(f"Failed to load model {model_name}: {str(e)}", sys)
    
    def summarize_article(self, article_data: Dict[str, str], 
                         max_length: int = 150, 
                         min_length: int = 50) -> str:
        """
        Summarize a single article
        
        Args:
            article_data: Dictionary containing article data
            max_length: Maximum length of summary
            min_length: Minimum length of summary
            
        Returns:
            Summary text
        """
        try:
            content = article_data.get('content', '')
            title = article_data.get('title', '')
            
            if not content or content == "No content found":
                logger.logging.warning(f"No content to summarize for: {article_data.get('url', 'Unknown URL')}")
                return f"Summary not available - insufficient content. Title: {title}"
            
            # Prepare text for summarization
            text_to_summarize = self._prepare_text_for_summarization(content, title)
            
            # Handle long articles by chunking
            if len(text_to_summarize) > self.max_chunk_length:
                summary = self._summarize_long_text(text_to_summarize, max_length, min_length)
            else:
                summary = self._summarize_text(text_to_summarize, max_length, min_length)
            
            logger.logging.info(f"Generated summary for article: {title[:50]}...")
            return summary
            
        except Exception as e:
            logger.logging.error(f"Error summarizing article: {str(e)}")
            return f"Summary generation failed: {str(e)}"
    
    def summarize_multiple_articles(self, articles_data: List[Dict[str, str]],
                                  max_length: int = 150,
                                  min_length: int = 50) -> List[str]:
        """
        Summarize multiple articles
        
        Args:
            articles_data: List of article data dictionaries
            max_length: Maximum length of each summary
            min_length: Minimum length of each summary
            
        Returns:
            List of summaries
        """
        summaries = []
        
        for i, article_data in enumerate(articles_data):
            try:
                logger.logging.info(f"Summarizing article {i+1}/{len(articles_data)}")
                summary = self.summarize_article(article_data, max_length, min_length)
                summaries.append(summary)
            except Exception as e:
                logger.logging.error(f"Failed to summarize article {i+1}: {str(e)}")
                summaries.append(f"Summary generation failed: {str(e)}")
        
        return summaries
    
    def _prepare_text_for_summarization(self, content: str, title: str = "") -> str:
        """
        Prepare text for summarization by cleaning and formatting
        
        Args:
            content: Article content
            title: Article title
            
        Returns:
            Cleaned text ready for summarization
        """
        # Clean the content
        content = self._clean_content(content)
        
        # Combine title and content if title is available
        if title and title != "No title found":
            text = f"{title}. {content}"
        else:
            text = content
        
        # Ensure text isn't too long for the model
        tokens = self.tokenizer.encode(text, truncation=False)
        if len(tokens) > self.max_chunk_length:
            # Truncate to fit model limits
            tokens = tokens[:self.max_chunk_length]
            text = self.tokenizer.decode(tokens, skip_special_tokens=True)
        
        return text
    
    def _clean_content(self, content: str) -> str:
        """
        Clean content text for better summarization
        
        Args:
            content: Raw content text
            
        Returns:
            Cleaned content
        """
        if not content:
            return ""
        
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove common web artifacts
        patterns_to_remove = [
            r'Cookie Policy.*?(?=\.|$)',
            r'Privacy Policy.*?(?=\.|$)',
            r'Terms of Service.*?(?=\.|$)',
            r'Advertisement.*?(?=\.|$)',
            r'ADVERTISEMENT.*?(?=\.|$)',
            r'Click here.*?(?=\.|$)',
            r'Read more.*?(?=\.|$)',
            r'Continue reading.*?(?=\.|$)',
            r'Sign up.*?(?=\.|$)',
            r'Subscribe.*?(?=\.|$)',
            r'Share this.*?(?=\.|$)',
            r'Follow us.*?(?=\.|$)',
            r'© \d{4}.*?(?=\.|$)',
            r'All rights reserved.*?(?=\.|$)'
        ]
        
        for pattern in patterns_to_remove:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        # Remove URLs
        content = re.sub(r'http[s]?://\S+', '', content)
        
        # Remove email addresses
        content = re.sub(r'\S+@\S+', '', content)
        
        # Remove excessive punctuation
        content = re.sub(r'[.]{3,}', '...', content)
        content = re.sub(r'[!]{2,}', '!', content)
        content = re.sub(r'[?]{2,}', '?', content)
        
        # Clean up spacing
        content = re.sub(r'\s+', ' ', content)
        
        return content.strip()
    
    def _summarize_text(self, text: str, max_length: int, min_length: int) -> str:
        """
        Summarize text using the model
        
        Args:
            text: Text to summarize
            max_length: Maximum summary length
            min_length: Minimum summary length
            
        Returns:
            Summary text
        """
        try:
            # Ensure min_length is reasonable
            min_length = min(min_length, max_length // 2)
            
            summary = self.summarizer(
                text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False,
                early_stopping=True,
                num_beams=4,
                length_penalty=2.0,
                no_repeat_ngram_size=3
            )
            
            return summary[0]['summary_text'].strip()
            
        except Exception as e:
            logger.logging.error(f"Error in text summarization: {str(e)}")
            raise WebScraperException(f"Summarization failed: {str(e)}", sys)
    
    def _summarize_long_text(self, text: str, max_length: int, min_length: int) -> str:
        """
        Summarize long text by chunking and combining summaries
        
        Args:
            text: Long text to summarize
            max_length: Maximum final summary length
            min_length: Minimum final summary length
            
        Returns:
            Combined summary
        """
        try:
            # Split text into chunks
            chunks = self._split_text_into_chunks(text)
            
            if len(chunks) == 1:
                return self._summarize_text(chunks[0], max_length, min_length)
            
            # Summarize each chunk
            chunk_summaries = []
            chunk_max_length = max_length // 2  # Shorter summaries for chunks
            chunk_min_length = min_length // 2
            
            for i, chunk in enumerate(chunks):
                try:
                    summary = self._summarize_text(chunk, chunk_max_length, chunk_min_length)
                    chunk_summaries.append(summary)
                    logger.logging.info(f"Summarized chunk {i+1}/{len(chunks)}")
                except Exception as e:
                    logger.logging.warning(f"Failed to summarize chunk {i+1}: {str(e)}")
                    continue
            
            if not chunk_summaries:
                return "Failed to generate summary for long text"
            
            # Combine chunk summaries
            combined_text = " ".join(chunk_summaries)
            
            # Final summarization if combined text is still long
            if len(combined_text) > self.max_chunk_length:
                final_summary = self._summarize_text(combined_text, max_length, min_length)
            else:
                final_summary = combined_text
            
            return final_summary
            
        except Exception as e:
            logger.logging.error(f"Error in long text summarization: {str(e)}")
            return f"Failed to summarize long content: {str(e)}"
    
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """
        Split long text into manageable chunks
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        # Split by sentences first
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # Check if adding this sentence would exceed the limit
            test_chunk = current_chunk + " " + sentence if current_chunk else sentence
            
            # Count tokens in the test chunk
            token_count = len(self.tokenizer.encode(test_chunk, truncation=False))
            
            if token_count <= self.max_chunk_length:
                current_chunk = test_chunk
            else:
                # Save current chunk and start new one
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [text[:self.max_chunk_length]]