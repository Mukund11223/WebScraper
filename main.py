from webscraper.pipeline import WebScrapingPipeline
from webscraper.Exception.exception import WebScraperException
from webscraper.Logging import logger
import sys

def main():
    """Main function to run the web scraping and summarization"""
    try:
        # Target website
        target_url = "https://timesofindia.indiatimes.com/home/headlines"
        
        # Initialize pipeline
        pipeline = WebScrapingPipeline(target_url)
        
        # Run the pipeline
        results = pipeline.run_pipeline()
        
        # Display results
        print("="*60)
        print("WEB SCRAPING + LLM SUMMARIZATION RESULTS")
        print("="*60)
        print(f"Website: {results['url']}")
        print(f"Total Headlines Found: {results['total_headlines']}")
        print("\nOVERALL SUMMARY:")
        print("-" * 20)
        print(results['overall_summary'])
        print("\nTOP 5 INDIVIDUAL SUMMARIES:")
        print("-" * 30)
        
        for i, item in enumerate(results['individual_summaries'][:5], 1):
            print(f"{i}. {item['summary']}")
            if item['link']:
                print(f"   Link: {item['link']}")
            print()
        
        print(f"Raw data saved to: {results['raw_data_file']}")
        
    except Exception as e:
        logger.logging.error(f"Main execution failed: {str(e)}")
        raise WebScraperException(e, sys)

if __name__ == "__main__":
    main()