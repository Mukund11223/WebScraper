#!/usr/bin/env python3
"""
Setup script for Article Scraping & Summarization API

This script helps users install dependencies and verify the installation.

Usage:
    python setup.py
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {command}")
        print(f"   Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print("🔍 Checking Python version...")
    version = sys.version_info
    
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is not compatible")
        print("   Required: Python 3.8 or higher")
        return False

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    
    # Check if requirements.txt exists
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found")
        return False
    
    # Install dependencies
    commands = [
        ("pip install --upgrade pip", "Upgrading pip"),
        ("pip install -r requirements.txt", "Installing dependencies")
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    return True

def verify_installation():
    """Verify that key packages are installed"""
    print("\n🔍 Verifying installation...")
    
    required_packages = [
        "fastapi",
        "uvicorn", 
        "requests",
        "beautifulsoup4",
        "transformers",
        "torch",
        "pydantic"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} installed")
        except ImportError:
            print(f"❌ {package} missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        return False
    
    print("✅ All required packages are installed")
    return True

def test_components():
    """Test that our components can be imported"""
    print("\n🧪 Testing components...")
    
    try:
        from webscraper.components.article_scraper import ArticleScraper
        print("✅ ArticleScraper imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import ArticleScraper: {e}")
        return False
    
    try:
        from webscraper.components.article_summarizer import ArticleSummarizer
        print("✅ ArticleSummarizer imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import ArticleSummarizer: {e}")
        return False
    
    try:
        from webscraper.components.article_pipeline import ArticlePipeline
        print("✅ ArticlePipeline imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import ArticlePipeline: {e}")
        return False
    
    return True

def download_model():
    """Download the default summarization model"""
    print("\n🤖 Downloading summarization model...")
    print("   This may take a few minutes on first run...")
    
    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        
        model_name = "facebook/bart-large-cnn"
        print(f"   Downloading {model_name}...")
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        
        print("✅ Model downloaded and cached successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to download model: {e}")
        print("   The model will be downloaded on first use")
        return False

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = ["data", "logs"]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        except Exception as e:
            print(f"❌ Failed to create directory {directory}: {e}")
            return False
    
    return True

def show_usage_instructions():
    """Show how to use the application"""
    print("\n" + "="*60)
    print("🎉 Setup completed successfully!")
    print("="*60)
    print("\n🚀 How to use the Article Scraping & Summarization API:")
    print()
    print("1. Start the API server:")
    print("   python article_main.py --mode api")
    print()
    print("2. Open your browser to:")
    print("   http://localhost:8000/docs")
    print()
    print("3. Test a single URL from command line:")
    print("   python article_main.py --mode url --url \"https://example.com/article\"")
    print()
    print("4. Run the test suite:")
    print("   python test_example.py")
    print()
    print("📖 API Endpoints:")
    print("   POST /summarize/          - Main endpoint (simple format)")
    print("   POST /scrape-articles/    - Extended endpoint with metadata")
    print("   GET  /health             - Health check")
    print("   GET  /stats              - API information")
    print()
    print("📝 Example request:")
    print('   curl -X POST "http://localhost:8000/summarize/" \\')
    print('        -H "Content-Type: application/json" \\')
    print('        -d \'{"urls": ["https://example.com/article"]}\'')
    print()
    print("📚 For more information, see README.md")

def main():
    """Main setup function"""
    print("Article Scraping & Summarization API - Setup")
    print("="*60)
    
    # Step 1: Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Step 2: Install dependencies
    if not install_dependencies():
        print("\n❌ Dependency installation failed")
        sys.exit(1)
    
    # Step 3: Verify installation
    if not verify_installation():
        print("\n❌ Installation verification failed")
        sys.exit(1)
    
    # Step 4: Test components
    if not test_components():
        print("\n❌ Component testing failed")
        sys.exit(1)
    
    # Step 5: Create directories
    if not create_directories():
        print("\n❌ Directory creation failed")
        sys.exit(1)
    
    # Step 6: Download model (optional)
    download_model()  # Don't fail if this doesn't work
    
    # Step 7: Show usage instructions
    show_usage_instructions()

if __name__ == "__main__":
    main()