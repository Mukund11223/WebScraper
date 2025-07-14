# Article Scraping & Summarization API

A comprehensive Python-based solution for web scraping, content extraction, and LLM-powered summarization of full articles from any website. This FastAPI application can process multiple URLs simultaneously, extract complete article content, and generate intelligent summaries using pre-trained language models.

## Features

- 🌐 **Universal Web Scraping**: Extract full articles from any website URL
- 🤖 **AI-Powered Summarization**: Uses HuggingFace transformers for intelligent content summarization
- 🚀 **FastAPI Integration**: RESTful API with automatic documentation
- ⚡ **Multiple URL Processing**: Handle multiple articles in a single request
- 🔒 **Rate Limiting**: Built-in protection against overwhelming target websites
- 🛡️ **Robust Error Handling**: Graceful handling of failed requests
- 📊 **Detailed Metadata**: Extract titles, authors, publish dates, and descriptions
- 🔄 **Flexible Response Formats**: Support for different output formats

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd article-scraping-api
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the API server:
```bash
python article_main.py --mode api
```

4. Open your browser to `http://localhost:8000/docs` for interactive API documentation.

### Basic Usage

#### API Endpoint (Recommended)

**POST** `/summarize/` - Simple endpoint with exact format as specified

```bash
curl -X POST "http://localhost:8000/summarize/" \
     -H "Content-Type: application/json" \
     -d '{
       "urls": [
         "https://example.com/article1",
         "https://example.com/article2"
       ]
     }'
```

**Response Format:**
```json
[
  {
    "url": "https://example.com/article1",
    "title": "Example Article Title 1",
    "content": "Full article content 1...",
    "summary": "Summarized content 1..."
  },
  {
    "url": "https://example.com/article2",
    "title": "Example Article Title 2", 
    "content": "Full article content 2...",
    "summary": "Summarized content 2..."
  }
]
```

#### Command Line Usage

Process a single URL:
```bash
python article_main.py --mode url --url "https://example.com/article"
```

Start the API server:
```bash
python article_main.py --mode api --host 0.0.0.0 --port 8000
```

## API Endpoints

### 1. `/summarize/` (POST)
- **Purpose**: Main endpoint for article scraping and summarization
- **Input**: JSON with `urls` array
- **Output**: Array of article objects with exact format specified in requirements
- **Rate Limit**: 1 second between requests per URL

### 2. `/scrape-articles/` (POST)
- **Purpose**: Extended endpoint with detailed metadata and statistics
- **Input**: JSON with `urls` array
- **Output**: Comprehensive response with processing statistics

### 3. `/health` (GET)
- **Purpose**: Health check endpoint
- **Output**: API status and pipeline readiness

### 4. `/stats` (GET)
- **Purpose**: API information and feature details
- **Output**: Supported features, limits, and configuration

### 5. `/` (GET)
- **Purpose**: Root endpoint with API information
- **Output**: Welcome message and endpoint descriptions

## Architecture

### Components

1. **ArticleScraper** (`webscraper/components/article_scraper.py`)
   - Universal content extraction from any website
   - Support for multiple content selectors
   - Rate limiting and error handling
   - Metadata extraction (title, author, date, description)

2. **ArticleSummarizer** (`webscraper/components/article_summarizer.py`)
   - HuggingFace transformers integration
   - Support for long articles via intelligent chunking
   - Configurable summary length and quality
   - GPU acceleration when available

3. **ArticlePipeline** (`webscraper/components/article_pipeline.py`)
   - Orchestrates scraping and summarization
   - Handles multiple URLs efficiently
   - Comprehensive error handling and statistics

4. **FastAPI Application** (`article_main.py`)
   - RESTful API with multiple endpoints
   - Request validation and response formatting
   - Command-line interface support

## Configuration

### Environment Variables

```bash
# Model configuration
SUMMARIZATION_MODEL=facebook/bart-large-cnn
RATE_LIMIT=1.0

# API configuration  
API_HOST=0.0.0.0
API_PORT=8000
MAX_URLS_PER_REQUEST=10
```

### Customizing the Summarization Model

The default model is `facebook/bart-large-cnn`, but you can use any HuggingFace summarization model:

```python
pipeline = ArticlePipeline(
    model_name='google/pegasus-xsum',  # Alternative model
    rate_limit=2.0  # Custom rate limit
)
```

## Examples

### Example 1: News Articles

```python
import requests

response = requests.post(
    "http://localhost:8000/summarize/",
    json={
        "urls": [
            "https://www.bbc.com/news/world-12345",
            "https://www.cnn.com/politics/article-123",
            "https://www.reuters.com/business/tech-456"
        ]
    }
)

articles = response.json()
for article in articles:
    print(f"Title: {article['title']}")
    print(f"Summary: {article['summary']}")
    print("-" * 50)
```

### Example 2: Blog Posts

```python
import requests

response = requests.post(
    "http://localhost:8000/summarize/",
    json={
        "urls": [
            "https://medium.com/@author/article-title",
            "https://dev.to/developer/programming-tutorial",
            "https://blog.example.com/latest-post"
        ]
    }
)

for article in response.json():
    if len(article['content']) > 1000:
        print(f"Long article: {article['title']}")
        print(f"Summary: {article['summary']}")
```

### Example 3: Research Papers

```python
import requests

response = requests.post(
    "http://localhost:8000/summarize/",
    json={
        "urls": [
            "https://arxiv.org/abs/2301.12345",
            "https://research.example.edu/paper123"
        ]
    }
)

papers = response.json()
for paper in papers:
    print(f"Paper: {paper['title']}")
    print(f"Summary: {paper['summary'][:200]}...")
```

## Performance Optimization

### 1. GPU Acceleration
Ensure PyTorch with CUDA is installed for GPU acceleration:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 2. Model Caching
Models are automatically cached after first load. For production, consider:
- Pre-downloading models during container build
- Using smaller, faster models for real-time applications
- Implementing model warm-up procedures

### 3. Concurrent Processing
The API supports concurrent processing with built-in rate limiting:
```python
# Process URLs concurrently (experimental)
results = await pipeline.process_multiple_urls_async(urls)
```

## Error Handling

The API handles various error scenarios gracefully:

- **Invalid URLs**: Validation and sanitization
- **Network timeouts**: Configurable timeout settings
- **Content extraction failures**: Fallback methods
- **Summarization errors**: Error messages in response
- **Rate limiting**: Automatic throttling

Example error response:
```json
{
  "url": "https://invalid-url.com",
  "title": "Error",
  "content": "Failed to extract content",
  "summary": "Processing failed: HTTP 404 Not Found"
}
```

## Rate Limiting & Ethics

### Built-in Protections
- 1-second minimum delay between requests per URL
- Maximum 10 URLs per API request
- Respect for robots.txt (manual verification recommended)
- User-Agent rotation and proper headers

### Best Practices
1. **Check robots.txt**: Always verify `website.com/robots.txt`
2. **Respect rate limits**: Don't overwhelm target servers
3. **Terms of service**: Ensure compliance with website ToS
4. **Commercial usage**: Consider reaching out for permission
5. **Caching**: Cache results to avoid repeated requests

## Deployment

### Docker Deployment

1. Create Dockerfile:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "article_main.py", "--mode", "api"]
```

2. Build and run:
```bash
docker build -t article-scraper .
docker run -p 8000:8000 article-scraper
```

### Production Considerations

1. **Environment Variables**: Use for configuration
2. **Logging**: Configure appropriate log levels
3. **Monitoring**: Set up health checks and metrics
4. **Scaling**: Consider multiple worker processes
5. **Security**: Implement authentication for production use

## Troubleshooting

### Common Issues

1. **Model Download Errors**
   ```bash
   # Clear HuggingFace cache
   rm -rf ~/.cache/huggingface/
   ```

2. **Memory Issues**
   - Use smaller models: `distilbart-cnn-12-6`
   - Reduce max URLs per request
   - Enable text chunking for long articles

3. **Network Timeouts**
   - Increase timeout settings
   - Check internet connectivity
   - Verify target website accessibility

4. **Content Extraction Failures**
   - Websites with heavy JavaScript may require Selenium
   - Some sites block automated requests
   - Consider alternative content sources

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure code follows project standards
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is intended for educational and research purposes. Users are responsible for:
- Respecting website terms of service
- Complying with applicable laws and regulations  
- Ensuring ethical use of scraped content
- Respecting intellectual property rights

## Support

For issues, questions, or contributions:
- Create an issue on GitHub
- Check existing documentation
- Review the API documentation at `/docs` when running locally