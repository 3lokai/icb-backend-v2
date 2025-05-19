# Crawl4AI Integration Strategy for Coffee Scraper Project

## Executive Summary

This implementation plan integrates Crawl4AI with your existing coffee scraper project to significantly enhance data collection capabilities, handle challenging websites, and improve data quality. By leveraging Crawl4AI's advanced browser automation, content extraction, and AI-powered analysis features, we can complement your current scraping approach to create a more robust and comprehensive coffee data collection system.

## 1. Integration Architecture

### 1.1 Primary & Fallback Pattern

```
┌────────────────┐    ┌─────────────────┐    ┌───────────────┐
│                │    │                 │    │               │
│ Direct Scraper ├───►│ Pattern-Based   ├───►│ Crawl4AI with │
│ (Current)      │    │ Detection Fails │    │ LLM Extraction│
│                │    │                 │    │               │
└────────────────┘    └─────────────────┘    └───────────────┘
```

- **Primary Approach**: Continue using direct CSS/XPath selectors for known patterns (Shopify, WooCommerce)
- **Secondary Approach**: Use Crawl4AI for sites with unknown platforms, dynamic content, or when primary scraping fails
- **Data Enrichment**: Use Crawl4AI's LLM capabilities to fill missing data regardless of the source

## 2. Roaster Data Enhancement

### 2.1 Missing Roaster Data Enrichment

Implement LLM extraction for fields that are frequently missing in the direct scraping approach:

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from pydantic import BaseModel, Field
from typing import Optional, List

class RoasterEnrichmentData(BaseModel):
    description: Optional[str] = Field(None, description="About the company or roaster")
    founded_year: Optional[int] = Field(None, description="Year the company was established")
    has_subscription: Optional[bool] = Field(None, description="Whether they offer a subscription service")
    has_physical_store: Optional[bool] = Field(None, description="Whether they have a physical retail location")
    social_links: Optional[List[str]] = Field(None, description="Social media profile URLs")

async def enrich_roaster_data(roaster_data, url):
    """Use LLM to fill in missing roaster data"""
    # Only proceed if we're missing key fields
    missing_fields = []
    for field in ['description', 'founded_year', 'has_subscription', 'has_physical_store']:
        if not roaster_data.get(field):
            missing_fields.append(field)
    
    if not missing_fields:
        return roaster_data  # No enrichment needed
    
    # Prepare LLM extraction
    llm_strategy = LLLMExtractionStrategy(
        llm_config=LLMConfig(
            provider="openai/gpt-4o-mini", 
            api_token="env:OPENAI_API_KEY"
        ),
        schema=RoasterEnrichmentData.model_json_schema(),
        extraction_type="schema",
        instruction=f"Extract the following missing information about this coffee roaster: {', '.join(missing_fields)}. Only return information you're confident about.",
        input_format="html",
        chunk_token_threshold=4000,
        apply_chunking=True
    )
    
    config = CrawlerRunConfig(
        extraction_strategy=llm_strategy,
        cache_mode="ENABLED"
    )
    
    # Execute the crawl
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        
        if result.success and result.extracted_content:
            enriched_data = json.loads(result.extracted_content)
            
            # Update roaster data with enriched info
            for field, value in enriched_data.items():
                if value is not None and not roaster_data.get(field):
                    roaster_data[field] = value
                    roaster_data[f"{field}_source"] = "llm"
    
    return roaster_data
```

## 3. Coffee Product Extraction Enhancement

### 3.1 DeepCrawl for Product Discovery

Use Crawl4AI's deep crawling to discover all product pages when a site doesn't have a clear product listing structure:

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter, ContentTypeFilter
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer

async def discover_coffee_products(base_url):
    """Use deep crawling to find coffee product pages"""
    
    # Set up filters to focus on product pages
    filter_chain = FilterChain([
        URLPatternFilter(patterns=["*product*", "*coffee*", "*shop*", "*store*", "*collection*"]),
        ContentTypeFilter(allowed_types=["text/html"])
    ])
    
    # Set up scorer to prioritize coffee-related pages
    scorer = KeywordRelevanceScorer(
        keywords=["coffee", "bean", "roast", "arabica", "robusta", "espresso", "product"],
        weight=0.7
    )
    
    # Create crawler config with deep crawl strategy
    config = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=2,
            include_external=False,
            filter_chain=filter_chain,
            url_scorer=scorer,
            max_pages=50  # Limit to prevent overly long crawls
        ),
        cache_mode="ENABLED",
        stream=True
    )
    
    product_urls = []
    
    # Execute the crawl
    async with AsyncWebCrawler() as crawler:
        async for result in await crawler.arun(url=base_url, config=config):
            if result.success:
                # Analyze if this is a product page
                is_product = (
                    ("product" in result.url.lower()) or
                    ("<button" in result.html and "add to cart" in result.html.lower()) or
                    ("price" in result.html.lower() and "product" in result.html.lower())
                )
                
                if is_product:
                    product_urls.append(result.url)
    
    return product_urls
```

### 3.2 Missing Coffee Data Enrichment

Use LLM extraction to fill in missing details about coffee products:

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from pydantic import BaseModel, Field
from typing import Optional, List

class CoffeeProductEnrichment(BaseModel):
    roast_level: Optional[str] = Field(None, description="Roasting darkness level (light, medium, dark, etc.)")
    bean_type: Optional[str] = Field(None, description="Coffee bean variety")
    processing_method: Optional[str] = Field(None, description="Bean processing technique")
    region_origin: Optional[str] = Field(None, description="Coffee origin region")
    flavor_notes: Optional[List[str]] = Field(None, description="Flavor profile notes")
    is_single_origin: Optional[bool] = Field(None, description="Whether it's a single origin coffee or a blend")

async def enrich_coffee_product(coffee_data, url):
    """Use LLM to fill in missing coffee product data"""
    # Only proceed if we're missing key fields
    missing_fields = []
    for field in ['roast_level', 'bean_type', 'processing_method', 'region_origin', 'flavor_notes', 'is_single_origin']:
        if not coffee_data.get(field):
            missing_fields.append(field)
    
    if not missing_fields:
        return coffee_data  # No enrichment needed
    
    # Use pruning content filter to focus on main content
    prune_filter = PruningContentFilter(threshold=0.4, threshold_type="dynamic")
    md_generator = DefaultMarkdownGenerator(content_filter=prune_filter)
    
    # Prepare LLM extraction
    llm_strategy = LLLMExtractionStrategy(
        llm_config=LLMConfig(
            provider="openai/gpt-4o-mini", 
            api_token="env:OPENAI_API_KEY"
        ),
        schema=CoffeeProductEnrichment.model_json_schema(),
        extraction_type="schema",
        instruction=f"Extract the following missing information about this coffee product: {', '.join(missing_fields)}. Only return information you're confident about.",
        input_format="fit_markdown",  # Use the filtered content
        chunk_token_threshold=4000,
        apply_chunking=True
    )
    
    config = CrawlerRunConfig(
        markdown_generator=md_generator,
        extraction_strategy=llm_strategy,
        cache_mode="ENABLED"
    )
    
    # Execute the crawl
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        
        if result.success and result.extracted_content:
            enriched_data = json.loads(result.extracted_content)
            
            # Update coffee data with enriched info
            for field, value in enriched_data.items():
                if value is not None and not coffee_data.get(field):
                    coffee_data[field] = value
                    coffee_data[f"{field}_source"] = "llm"
    
    return coffee_data
```

## 4. Screenshot & PDF Capture

Capture screenshots and PDFs for verification, auditing, and visual records:

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from base64 import b64decode
import os

async def capture_visual_record(url, output_dir):
    """Capture screenshot and PDF of a coffee/roaster page"""
    config = CrawlerRunConfig(
        screenshot=True,
        pdf=True,
        cache_mode="ENABLED"
    )
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        
        if result.success:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filenames
            site_name = url.replace('https://', '').replace('http://', '').split('/')[0]
            screenshot_file = os.path.join(output_dir, f"{site_name}_screenshot.png")
            pdf_file = os.path.join(output_dir, f"{site_name}_page.pdf")
            
            # Save screenshot
            if result.screenshot:
                with open(screenshot_file, "wb") as f:
                    f.write(b64decode(result.screenshot))
            
            # Save PDF
            if result.pdf:
                with open(pdf_file, "wb") as f:
                    f.write(result.pdf)
            
            return {
                "screenshot": screenshot_file if result.screenshot else None,
                "pdf": pdf_file if result.pdf else None
            }
        
        return None
```

## 5. Integration with Existing Pipeline

### 5.1 Main Integration Strategy

```python
async def scrape_coffee_site(url):
    """Enhanced scraping with fallback to Crawl4AI"""
    
    # Step 1: Detect platform
    platform_info = await detect_platform_with_crawl4ai(url)
    platform = platform_info["platform"]
    
    # Step 2: Use appropriate scraper based on platform
    if platform in ["shopify", "woocommerce"] and platform_info["confidence"] > 0.7:
        # Use existing scrapers for known platforms with high confidence
        if platform == "shopify":
            roaster_data = await existing_shopify_scraper(url)
            products = await existing_shopify_product_scraper(url)
        else:  # woocommerce
            roaster_data = await existing_woocommerce_scraper(url)
            products = await existing_woocommerce_product_scraper(url)
    else:
        # Use Crawl4AI for unknown or uncertain platforms
        roaster_data = await scrape_roaster_with_crawl4ai(url)
        product_urls = await discover_coffee_products(url)
        products = []
        
        for product_url in product_urls:
            product_data = await scrape_product_with_crawl4ai(product_url)
            products.append(product_data)
    
    # Step 3: Enrich data regardless of source
    roaster_data = await enrich_roaster_data(roaster_data, url)
    
    for product in products:
        product = await enrich_coffee_product(product, product["url"])
    
    # Step 4: Capture visual records for verification
    visual_records = await capture_visual_record(url, "visual_records")
    
    return {
        "roaster": roaster_data,
        "products": products,
        "platform": platform,
        "visual_records": visual_records
    }
```

## 6. Incremental Update Strategy

Leverage Crawl4AI for detecting changes on already-scraped sites:

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
import hashlib

async def check_site_for_updates(url, last_content_hash):
    """Check if a site has been updated since last scrape"""
    
    # Configure efficient content filtering
    prune_filter = PruningContentFilter(threshold=0.4)
    md_generator = DefaultMarkdownGenerator(content_filter=prune_filter)
    
    config = CrawlerRunConfig(
        markdown_generator=md_generator,
        cache_mode="BYPASS"  # Force fresh content check
    )
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        
        if result.success:
            # Calculate hash of filtered content
            current_content = result.markdown.fit_markdown
            current_hash = hashlib.md5(current_content.encode()).hexdigest()
            
            # Compare with previous hash
            has_changed = current_hash != last_content_hash
            
            return {
                "has_changed": has_changed,
                "current_hash": current_hash
            }
        
        return {"has_changed": None, "error": result.error_message}
```

## 7. Intelligent Update Strategy

Implement the layered update strategies from `coffee_db.md` and `roaster_db.md`:

```python
async def determine_update_priority(field_name, last_updated_date):
    """Determine if a field should be updated based on its stability category"""
    today = datetime.now()
    days_since_update = (today - last_updated_date).days
    
    # Highly variable fields (check weekly)
    if field_name in ['is_available']:
        return days_since_update >= 7
        
    # Variable fields (check monthly)
    if field_name in ['image_url', 'tags', 'is_seasonal', 'price']:
        return days_since_update >= 30
        
    # Moderately stable fields (check quarterly)
    if field_name in ['description', 'roast_level', 'direct_buy_url']:
        return days_since_update >= 90
        
    # Highly stable fields (check yearly)
    if field_name in ['name', 'bean_type', 'processing_method', 'region_id', 'is_single_origin']:
        return days_since_update >= 365
        
    # Default to monthly updates for unspecified fields
    return days_since_update >= 30
```

## 8. Integration Implementation Plan

### Phase 1: Core Integration (Week 1-2)
- Implement enhanced platform detection
- Integrate fallback pattern for unknown platforms
- Setup basic LLM enrichment for missing data

### Phase 2: Advanced Features (Week 3-4)
- Implement deep crawling for product discovery
- Add comprehensive data enrichment
- Setup visual record capture for verification

### Phase 3: Update Strategy (Week 5-6)
- Implement incremental update checks
- Add intelligent update scheduling by field stability
- Setup change detection and tracking

### Phase 4: Testing & Optimization (Week 7-8)
- Test on diverse coffee sites
- Optimize LLM prompts for better data extraction
- Implement caching strategies for cost efficiency

## 9. Resource Requirements

### API Keys & Environment
- OpenAI API key for LLM extraction
- Sufficient storage for visual records (screenshots/PDFs)
- Adequate rate limiting for ethical scraping

### Computing Resources
- Memory: Minimum 4GB RAM for browser automation
- Storage: ~5GB for caching and visual records
- Bandwidth: Depends on number of sites scraped

## 10. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| High LLM costs | Use selective enrichment, caching, and batching |
| Crawl4AI reliability | Implement robust error handling and retry mechanisms |
| Site structure changes | Use CSS selectors with fallbacks, LLM adapts to structure changes |
| Duplicate data | Implement deduplication checks when merging data sources |
| Rate limiting/IP blocks | Use polite crawling with delays, proxy rotation if needed |
