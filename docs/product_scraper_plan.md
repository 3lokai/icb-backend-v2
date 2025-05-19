# Coffee Scraper Refactoring Plan

## Project Overview
This plan outlines the refactoring approach for the coffee scraper project to bring it in line with the established project rules while taking a practical, API-first approach to data extraction.

## Target File Structure
```
scrapers/
└── product/
    ├── __init__.py
    ├── scraper.py (Orchestrator)
    ├── extractors/
    │   ├── __init__.py
    │   ├── attributes.py (Attribute extraction from text/tags)
    │   ├── price.py (Price & weight extraction)
    │   ├── validators.py (Data validation)
    │   └── normalizers.py (Field standardization)
    ├── scrapers/
    │   ├── __init__.py
    │   ├── shopify.py (Shopify-specific extraction)
    │   ├── woocommerce.py (WooCommerce-specific extraction)
    │   └── static.py (Generic HTML scraping fallback)
    └── enrichment/
        ├── __init__.py
        └── deepseek.py (LLM-based enrichment)
```

## Phase 1: Shopify Extractor Optimization

### 1.1 Refactor Variant Processing
- [x] Move `process_variants` to `extractors/price.py`
- [x] Improve weight pattern matching with more fallbacks
- [x] Add confidence scores to extracted weights
- [x] Handle edge cases like "2 x 250g" pack formats
- [x] Add validation to ensure prices make sense (no 1kg cheaper than 250g)

### 1.2 Enhance Attribute Extraction
- [x] Move attribute extraction to `extractors/attributes.py`
- [x] Add multiple pattern matching strategies for each attribute
- [x] Prioritize tag-based extraction over description-based
- [x] Track extraction source for debugging (tag vs description)

### 1.3 Implement Data Validation
- [x] Create `extractors/validators.py` with validation functions
- [x] Add validations for:
  - Roast levels against standard vocabulary
  - Price ranges (flag unusual prices)
  - Bean types
  - Processing methods

### 1.4 Shopify API-Specific Improvements
- [x] Add better error handling for API pagination
- [x] Implement rate limiting protection
- [x] Add retry logic for failed API calls
- [x] Log API failures for monitoring

## Phase 2: WooCommerce Extractor Optimization

### 2.1 API Endpoint Consolidation
- [x] Prioritize v3 API endpoints
- [x] Improve authentication handling if needed
- [x] Better organizing of API response processing

### 2.2 Extract Common Patterns
- [x] Share extraction logic with Shopify where possible
- [x] Use the same validation functions
- [x] Implement consistent error handling

### 2.3 HTML Fallback Improvements
- [x] Only scrape when API fails
- [x] Make HTML selectors more resilient
- [x] Add multiple fallback selectors for key fields

## Phase 3: Static Site Scraper Enhancement

### 3.1 Improve HTML Pattern Recognition
- [x] Enhance selector patterns for product identification
- [x] Add multiple strategies for price extraction
- [x] Better extraction of product attributes from unstructured text

### 3.2 Sitemap Handling Improvement
- [x] Better sitemap discovery (try multiple locations)
- [x] Add support for sitemap index files
- [x] Implement intelligent URL filtering

## Phase 4: Shared Improvements

### 4.1 Unified Data Model
- [x] Ensure all scrapers output the same data structure
- [x] Add metadata about extraction confidence
- [x] Track extraction sources for each field

### 4.2 Better LLM Integration
- [x] Improve criteria for when to use LLM
- [x] Batch similar products for cost efficiency
- [x] Implement validation of LLM outputs

### 4.3 Caching Enhancements
- [x] Add differential update detection
- [x] Implement field-level caching
- [x] Support for invalidating specific fields

## Implementation Strategy

### For Each Platform:
1. [x] Start with the data acquisition (API/HTML)
2. [x] Extract basic product data
3. [x] Apply specialized extractors for complex fields
4. [x] Validate all extracted data
5. [x] Only enhance with LLM when needed

### Code Organization Principles:
1. **Single Responsibility**: Each extractor handles one data field type
2. **Multiple Strategies**: Each extraction has primary + fallback methods
3. **Confidence Tracking**: Track how reliable each extraction is
4. **Progressive Enhancement**: Extract definite data first, then enrich

## Prioritization
1. Shopify (most structured data, easiest to improve)
2. WooCommerce (semi-structured data via API)
3. Static sites (most complex, requires more fallbacks)

## Evaluation Metrics
- Extraction success rate
- Field completion percentage
- Extraction confidence scores
- LLM usage efficiency
- Runtime performance
