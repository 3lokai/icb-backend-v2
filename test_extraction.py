#!/usr/bin/env python
"""
Simple test script to test LLM extraction on Ainmane product page
"""

import asyncio
import json
import os
from pathlib import Path
import sys
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(str(Path(__file__).parent))

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig, LLMConfig
from config import config
from crawl4ai.extraction_strategy import LLMExtractionStrategy, JsonCssExtractionStrategy

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent / ".env")
print("OPENAI_API_KEY loaded:", os.getenv("OPENAI_API_KEY"))

async def test_extraction():
    """Test LLM extraction on Ainmane product page"""
    
    # Simple schema for testing
    minimal_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Product name"},
            "price": {"type": "number", "description": "Price in local currency"},
            "description": {"type": "string", "description": "Product description"},
        }
        # No 'required' field, all fields optional
    }
    
    # Get OpenAI key from config
    openai_key = config.llm.openai_api_key
    if not openai_key:
        print("Error: OPENAI_API_KEY not found in config")
        return
    
    # LLM strategy
    llm_strategy = LLMExtractionStrategy(
        llm_config=LLMConfig(
            provider="openai/gpt-4o-mini",
            api_token=openai_key
        ),
        schema=minimal_schema,
        extraction_type="schema",
        instruction="Extract the product name, price, and description from this page.",
        input_format="html",
        chunk_token_threshold=5000,
        apply_chunking=True,
        extra_args={"temperature": 0.1},
    )
    
    # Crawler config
    crawler_config = CrawlerRunConfig(
        extraction_strategy=llm_strategy,
        page_timeout=30000,
        cache_mode=CacheMode.ENABLED
    )
    
    url = "http://babasbeanscoffee.com/product/ms-estate/"
    
    print(f"Testing extraction on: {url}")
    
    try:
        async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
            result = await crawler.arun(url=url, config=crawler_config)
            
            # Print the markdown input if available
            if hasattr(result, 'markdown') and result.markdown:
                print("\n[DEBUG] MARKDOWN SENT TO LLM:\n" + result.markdown[:2000] + ("..." if len(result.markdown) > 2000 else ""))

            print(f"Success: {result.success}")
            print(f"Has extracted content: {bool(result.extracted_content)}")
            
            if result.extracted_content:
                print(f"Extracted content: {result.extracted_content}")
                # Print the raw LLM output before parsing
                print("RAW LLM OUTPUT:")
                print(result.extracted_content)
                try:
                    parsed = json.loads(result.extracted_content)
                    print(f"Parsed JSON: {json.dumps(parsed, indent=2)}")
                except json.JSONDecodeError as e:
                    print(f"JSON parse error: {e}")
            else:
                print("No extracted content from LLM. Trying CSS extraction as backup...")
                # --- CSS Extraction Backup ---
                css_schema = {
                    "name": "TestProductNameExtraction",
                    "baseSelector": "div.product-info-main",
                    "fields": [
                        {"name": "name", "selector": "h1.page-title span.base", "type": "text"}
                    ]
                }
                css_strategy = JsonCssExtractionStrategy(css_schema, verbose=True)
                css_crawler_config = CrawlerRunConfig(
                    extraction_strategy=css_strategy,
                    page_timeout=30000,
                    cache_mode=CacheMode.ENABLED
                )
                css_result = await crawler.arun(url=url, config=css_crawler_config)
                if css_result.success and css_result.extracted_content:
                    print("[CSS Extraction] Extracted content:")
                    print(css_result.extracted_content)
                else:
                    print("[CSS Extraction] No content extracted.")
                if result.html:
                    print(f"HTML length: {len(result.html)}")
                    # Save HTML for inspection
                    with open("test_extraction_debug.html", "w", encoding="utf-8") as f:
                        f.write(result.html)
                    print("HTML saved to test_extraction_debug.html")
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_extraction()) 