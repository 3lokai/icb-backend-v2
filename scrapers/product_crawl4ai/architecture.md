# Product Scraper Architecture and Flow
# ===================================

## Overview

The coffee product scraper module follows a multi-tiered approach to extract product data from e-commerce websites regardless of their platform. The system prioritizes high-quality, structured data extraction while maximizing performance and success rates.

## Architectural Components

### 1. Main Orchestrator (ProductScraper)

The `ProductScraper` class coordinates the entire product extraction process:

```
1. Platform Detection → 2. API-First Extraction → 3. Fallback to Deep Crawling → 4. Product Enrichment → 5. Validation
```

This orchestrator handles roaster-level product extraction with intelligent caching, validation, and error handling.

### 2. API-First Extractors

For known e-commerce platforms, we first attempt extraction using the platform's API endpoints:

- **Shopify**: Uses `/products.json` endpoint to fetch structured product data
- **WooCommerce**: Uses `/wp-json/wc/store/products` endpoints with fallbacks

These extractors provide high-performance data collection with minimal network requests.

### 3. Deep Crawling Discovery

For unknown or static platforms, the system employs Crawl4AI deep crawling to:

1. Discover product page URLs using intelligent scoring and filtering
2. Focus crawling on pages likely to contain coffee products
3. Prioritize highest relevance pages first

The discovery phase implements URL patterns, domain filtering, and content relevance scoring.

### 4. Page-Level Enrichment

For each discovered product, whether from API or deep crawling, we perform LLM-based enrichment:

1. Filter product page content using `PruningContentFilter` to focus on important content
2. Extract structured data using LLM with a specialized coffee product schema
3. Fill missing fields with high-confidence predictions

This ensures even products with limited initial data become complete database entries.

### 5. Two-Phase Validation

To ensure we only collect coffee products (not accessories, equipment, etc.):

1. **Initial Validation**: Applied at discovery time using basic product information
2. **Detailed Validation**: Applied after enrichment using complete product data

This sequential validation minimizes resource usage on non-coffee products.

## Data Flow

```
┌────────────┐     ┌───────────────────┐     ┌─────────────────┐
│            │     │                   │     │                 │
│  Platform  │     │  Platform-Specific│     │  Standardized   │
│  Detection │───▶│  Extraction        │───▶│  Product Data   │
│            │     │  (API-first)      │     │                 │
└────────────┘     └───────────────────┘     └────────┬────────┘
                                                      │
                                                      │
┌──────────────┐   ┌─────────────────┐      ┌─────────▼────────┐
│              │   │                 │      │                  │
│  Database    │◀─│  Two-Phase      │◀─────│  Product         │
│  Storage     │   │  Validation     │      │  Enrichment      │
│              │   │                 │      │                  │
└──────────────┘   └─────────────────┘      └──────────────────┘
```

## Key Technology Integrations

1. **Crawl4AI**: Powers deep crawling, content filtering, and LLM-based extraction 
2. **PruningContentFilter**: Focuses extraction on the most relevant page content
3. **BestFirstCrawlingStrategy**: Prioritizes product pages using smart scoring
4. **LLMExtractionStrategy**: Provides AI-powered structured data extraction

## Performance Considerations

1. **Cache Management**: The system implements efficient caching at all levels
2. **Incremental Updates**: Designed to support field-level stability categories for updates
3. **Parallel Processing**: The deep crawler processes discoveries in a streaming manner
4. **Resource Optimization**: Ensures LLM usage is targeted only where needed

## Extensibility

The architecture is designed for easy extension:

1. **New Platforms**: Add new platform-specific extractors in the `api_extractors` directory
2. **Additional Fields**: Extend the schema in `enrichment/schema.py` 
3. **Custom Validation**: Enhance the validator logic for special cases

## Error Handling and Logging

The system implements comprehensive logging and error handling:

1. Detailed per-stage logging
2. Graceful fallbacks at each processing step
3. Record-keeping of skipped products for analysis

This multi-layered architecture ensures robust coffee product extraction across diverse e-commerce platforms while maintaining high data quality and performance.
