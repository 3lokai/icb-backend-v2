# Coffee Scraper Project Requirements Document (PRD)

## Project Overview

The Coffee Scraper is a comprehensive data collection system designed to extract detailed information about coffee products and roasters from various e-commerce platforms. The project aims to build a modular, scalable system that can handle different website structures, maintain data quality, and adapt to changing web environments.

## Scope

**This section describes requirements for product scraping only. Roaster scraping is already implemented and is not in scope here. All requirements, flows, and components below refer exclusively to product (coffee) data extraction.**

## Business Objectives

1. Create a reliable system to collect coffee product data from diverse web sources
2. Build a comprehensive database of coffee roasters and their products
3. Enable data-driven insights into coffee offerings, pricing, and trends
4. Support incremental updates with minimal resource consumption
5. Maximize data quality and completeness through fallback strategies

## Core Components

### 1. Scraper Infrastructure (Product Scraping Flow)

#### 1.1 Platform Detection (Hybrid Flow)
- Use `PlatformDetector` to identify the e-commerce platform for each target site.
- Assign a confidence score to each detection.
- Proceed with platform-specific logic for known platforms (Shopify, WooCommerce).
- If the platform is unknown or static, proceed to generic scraping.

#### 1.2 API-First Data Extraction
- For Shopify: Use the `/products.json` endpoint to extract product data.
- For WooCommerce: Use the `/wp-json/wc/store/products` endpoint.
- Map API responses to the internal product schema.
- If API endpoints are unavailable or incomplete, proceed to Crawl4AI fallback.

#### 1.3 Crawl4AI Deep Crawling & Enrichment
- Use Crawl4AI for:
  - Product discovery: Deep crawl to find product URLs on static/unknown platforms.
  - Field-level enrichment: For each product, fill missing fields (e.g., tasting notes, images) by crawling the product detail page.
- Integrate Crawl4AI enrichment even for products discovered via API, if fields are missing.

#### 1.4 Two-Phase Coffee Product Validation
- Phase 1: Validate products at the listing/discovery stage (filter out obvious non-coffee products).
- Phase 2: Validate again at the detailed product page level (using additional fields and context).

#### 1.5 Orchestration Logic
- The ProductScraper core orchestrates the above flow:
  1. Detect platform.
  2. Attempt API extraction if possible.
  3. If API fails or is incomplete, use Crawl4AI for discovery and/or enrichment.
  4. Apply two-phase validation to ensure only coffee products are retained.

### 2. Integration with Crawl4AI (Product Scraping)

#### 2.1 Product Discovery & Enrichment
- Use Crawl4AI to:
  - Discover product URLs when APIs are unavailable.
  - Enrich product data by crawling individual product pages for missing fields.
- Split Crawl4AI integration into two subtasks:
  - Discovery: Finding product URLs.
  - Enrichment: Filling in missing product fields.

- Apply selective LLM enrichment using Crawl4AI for missing fields
- Implement efficient token usage strategies for cost control
- Batch similar requests for efficiency

### 3. Database Integration

#### 3.1 Supabase Schema
- Implement database models matching predefined schema
- Support relational data (coffee-roaster, coffee-flavor relationships)
- Enable field-level update tracking

#### 3.2 Data Synchronization
- Implement efficient change detection
- Support incremental updates based on field stability
- Handle conflict resolution for concurrent updates

## Technical Requirements

### 1. Project Structure

```
scrapers/
├── __init__.py
├── roaster/
│   ├── __init__.py
│   ├── scraper.py
│   ├── extractors.py
│   ├── selectors.py
│   ├── location.py
│   ├── about.py
│   ├── enricher.py
│   └── batch.py
├── product/
│   ├── __init__.py
│   ├── scraper.py
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── attributes.py
│   │   ├── price.py
│   │   ├── validators.py
│   │   └── normalizers.py
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── shopify.py
│   │   ├── woocommerce.py
│   │   └── static.py
│   └── enrichment/
│       ├── __init__.py
│       └── deepseek.py
├── common/
│   ├── __init__.py
│   ├── platform_detector.py
│   ├── utils.py
│   ├── cache.py
│   └── enricher.py
└── db/
    ├── __init__.py
    ├── supabase.py
    └── models.py
```

### 2. Data Models

#### 2.1 Roaster Schema
Core fields include:
- id, name, slug, website_url, description, country, city, state
- founded_year, logo_url, image_url, contact information
- social_links, platform type, business features

#### 2.2 Coffee Product Schema
Core fields include:
- id, name, slug, roaster_id, description
- roast_level, bean_type, processing_method, region_id
- image_url, direct_buy_url, availability flags
- pricing data across different package sizes
- flavor profiles and brewing methods

### 3. Field Stability Categories
Fields are categorized by their update frequency needs:

1. **Highly Stable** (annual check):
   - name, slug, bean_type, region_id, is_single_origin

2. **Moderately Stable** (quarterly check):
   - description, roast_level, direct_buy_url

3. **Variable** (monthly check):
   - image_url, tags, is_seasonal, prices

4. **Highly Variable** (weekly check):
   - is_available, stock status

## Implementation Phases

### Phase 1: Core Infrastructure (2 weeks)
- Set up project structure and common utilities
- Implement platform detection and basic extractors
- Develop roaster data extraction functionality

### Phase 2: Platform-Specific Extraction (3 weeks)
- Implement Shopify product extraction
- Develop WooCommerce product extraction
- Create generic product extraction for other platforms

### Phase 3: Crawl4AI Integration (2 weeks)
- Integrate platform detection with Crawl4AI
- Implement deep crawling for product discovery
- Set up LLM enrichment for missing fields

### Phase 4: Database & Synchronization (2 weeks)
- Implement Supabase client and CRUD operations
- Develop field-level update strategy
- Create data validation and normalization pipeline

### Phase 5: Testing & Optimization (1 week)
- Build comprehensive testing suite
- Create monitoring dashboards
- Optimize for performance and resource usage

## Development Principles

1. **Modularity First**: Each function has a single responsibility
2. **Data Quality Over Quantity**: Prioritize reliability over volume
3. **Progressive Enhancement**: Extract definite data first, then enhance
4. **Defensive Scraping**: Implement multiple fallback methods for critical fields
5. **Respect Website Resources**: Apply rate limiting and ethical scraping practices
6. **Iterative Development**: Start with core functionality, then enhance

## Success Criteria

1. Successfully extract data from 95%+ of target websites
2. Achieve 90%+ field completion across all coffee products
3. Complete full database refresh within reasonable timeframe
4. Support incremental updates with minimal resource consumption
5. Produce well-structured data suitable for analytical queries

## Dependencies

1. **Python Libraries**:
   - httpx, beautifulsoup4, asyncio
   - supabase-py, re, pydantic
   - crawl4ai with all required components

2. **External Services**:
   - OpenAI API for LLM extraction
   - Supabase for database storage
   - Necessary API keys and access tokens

3. **Development Environment**:
   - Python 3.9+ environment
   - Windsurf AI IDE with Taskmaster integration
   - Appropriate testing tools and frameworks
