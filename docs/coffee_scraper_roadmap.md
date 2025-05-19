# Coffee Scraper Implementation Roadmap

## Executive Summary

This roadmap consolidates the coffee scraper project's development plan, incorporating best practices from the provided documentation. The project aims to build a modular, scalable system for extracting coffee product and roaster data from various e-commerce platforms, with a focus on data quality and maintainability.

## 1. Project Foundation (Week 1)

### Core Infrastructure Setup
- Create project structure following the modular design in `project_plan.md`
- Set up configuration management with environment variables for API keys
- Implement comprehensive logging system with rotation and levels
- Create data models matching Supabase schema (from `coffee_db.md` and `roaster_db.md`)
- Build platform detection module (from `common/platform_detector.py`) to identify website types

### Utility Development
- Develop caching system with expiration policy for network requests
- Create standardization functions for common fields (roast levels, processing methods)
- Build validation framework for data quality assurance
- Implement rate limiting and polite scraping utilities

### Sample Implementation
```python
# Example platform detector implementation
def detect_platform(soup, html_content):
    """
    Detect the e-commerce platform used by a website.
    
    Args:
        soup: BeautifulSoup object of the page
        html_content: Raw HTML content string
        
    Returns:
        str: Platform identifier ('shopify', 'woocommerce', etc.)
    """
    # Shopify indicators
    if soup.find('script', src=lambda x: x and 'cdn.shopify.com' in x):
        return 'shopify'
    if 'Shopify.theme' in html_content:
        return 'shopify'
        
    # WooCommerce indicators
    if soup.find('body', class_=lambda c: c and 'woocommerce' in c):
        return 'woocommerce'
    if soup.find('link', href=lambda x: x and 'woocommerce' in x):
        return 'woocommerce'
    
    # Other platforms...
    
    return 'static'  # Default fallback
```

## 2. Roaster Extraction (Week 2)

### Basic Extraction
- Implement roaster name extraction with multiple fallback strategies
- Build location data extraction (country, city, state)
- Create contact information extraction (email, phone)
- Develop social media link extraction and normalization

### Enhanced Extraction
- Implement founded year extraction with pattern matching
- Build subscription detection from product listings
- Create physical store detection logic
- Implement platform-specific optimizations for various e-commerce platforms

### LLM Enrichment
- Develop selective LLM enrichment for missing roaster descriptions
- Create prompt library for consistent LLM interactions
- Implement validation for LLM-generated content
- Build batching for cost-effective LLM API usage

## 3. Coffee Product Extraction - Shopify (Week 3)

### Basic Product Data
- Implement product name and slug extraction
- Build description and image URL extraction
- Create roast level detection with pattern matching
- Develop bean type and processing method extraction

### Enhanced Product Data
- Implement price extraction for different package sizes
- Build flavor profile extraction from descriptions
- Create brew method recommendation extraction
- Develop seasonal and availability detection

### Sample Implementation
```python
def extract_roast_level(soup, description_text):
    """
    Extract roast level from product attributes or description.
    Uses multiple strategies with fallbacks.
    
    Args:
        soup: BeautifulSoup object of the page
        description_text: Product description text
        
    Returns:
        str: Standardized roast level or None if not found
    """
    # Strategy 1: Look for dedicated attribute field
    roast_attr = soup.select_one('[data-attribute="roast-level"], .roast-level, .roast_level')
    if roast_attr:
        return standardize_roast_level(roast_attr.text.strip())
    
    # Strategy 2: Check product metadata table
    metadata_table = soup.select_one('.product-metadata, .product-attributes, table.shop_attributes')
    if metadata_table:
        rows = metadata_table.select('tr')
        for row in rows:
            header = row.select_one('th, td:first-child')
            if header and 'roast' in header.text.lower():
                value = row.select_one('td:last-child')
                if value:
                    return standardize_roast_level(value.text.strip())
    
    # Strategy 3: Extract from description using patterns
    roast_patterns = [
        (r'\b(light)\s+roast\b', 'light'),
        (r'\b(medium[\s-]*light)\s+roast\b', 'medium-light'),
        (r'\b(medium)\s+roast\b', 'medium'),
        (r'\b(medium[\s-]*dark)\s+roast\b', 'medium-dark'),
        (r'\b(dark)\s+roast\b', 'dark'),
        (r'roast:?\s*(light|medium[\s-]*light|medium|medium[\s-]*dark|dark)', lambda m: m.group(1).lower())
    ]
    
    for pattern, result in roast_patterns:
        match = re.search(pattern, description_text, re.IGNORECASE)
        if match:
            if callable(result):
                return standardize_roast_level(result(match))
            return result
    
    return None  # No roast level detected
```

## 4. Coffee Product Extraction - WooCommerce & Others (Week 4)

### WooCommerce Extraction
- Implement WooCommerce-specific product extraction
- Build variation and attribute handling for WooCommerce
- Create WooCommerce price extraction for different sizes
- Develop metadata extraction from WooCommerce structures

### Other Platform Support
- Implement generic fallback extraction for unknown platforms
- Build content-based extraction when structured data is unavailable
- Create adaptable extraction patterns for diverse site structures

## 5. Relational Data & Metadata (Week 5)

### Relationship Handling
- Implement coffee-to-roaster relationship mapping
- Build coffee-to-flavor profile relationships
- Create coffee-to-brew method relationships
- Develop external marketplace link extraction and normalization

### Data Enhancement
- Implement confidence scoring for all extracted fields
- Build extraction source tracking for debugging
- Create data validation and constraint enforcement
- Develop data normalization pipeline

## 6. Database Integration (Week 6)

### Supabase Integration
- Implement Supabase client in `db/supabase.py`
- Build CRUD operations for all tables
- Create data transformation functions for Supabase schema
- Implement error handling and retry mechanisms

### Data Synchronization
- Build incremental update strategy based on field stability
- Implement change detection and logging
- Create conflict resolution mechanisms
- Develop data integrity verification

## 7. Automation & Monitoring (Week 7)

### Scheduling System
- Implement scheduler for periodic updates
- Build tiered update frequency based on field stability
- Create priority queue for high-value updates
- Develop resource-aware scheduling to prevent overload

### Monitoring System
- Implement scrape success/failure tracking
- Build data quality monitoring metrics
- Create notification system for critical failures
- Develop performance analytics dashboard

## 8. Testing & Validation (Week 8)

### Comprehensive Testing
- Implement unit tests for all extraction methods
- Build integration tests for end-to-end pipeline
- Create regression tests with saved website snapshots
- Develop validation suite for data quality assurance

### System Validation
- Implement manual review UI for low-confidence data
- Build comparison tools for before/after data changes
- Create statistical anomaly detection for extracted data
- Develop audit logging for all data modifications

## Technical Decisions & Best Practices

### Following Project Rules
The implementation will adhere to the principles outlined in `rules.md`:

1. **Modularity First**: Every component is designed as a separate module with clear interfaces
2. **Data Quality Over Quantity**: Multiple validation layers ensure accuracy
3. **Progressive Enhancement**: Core data extracted first, then enhanced with additional methods
4. **Defensive Scraping**: Multiple fallback methods for critical fields
5. **Respect Website Resources**: Rate limiting, caching, and polite behavior built-in
6. **Iterative Development**: Core functionality first, then refinement

### Data Stability Strategy
Following the stability categories from `coffee_db.md` and `roaster_db.md`:

- **Highly Stable** (check annually): name, slug, bean_type, region_id
- **Moderately Stable** (check quarterly): description, roast_level, direct_buy_url
- **Variable** (check monthly): image_url, tags, is_seasonal
- **Highly Variable** (check weekly): is_available, price

### LLM Usage Guidelines
- Use pattern matching and structured extraction first
- Apply LLM selectively for complex cases or gaps
- Maintain a library of tested prompts
- Validate LLM outputs against constraints
- Batch similar items for efficiency

## Implementation Timeline

| Week | Primary Focus | Secondary Focus | Milestone |
|------|--------------|-----------------|-----------|
| 1 | Project Foundation | Utility Development | Basic infrastructure operational |
| 2 | Roaster Extraction | LLM Integration | Roaster data extraction functional |
| 3 | Shopify Product Extraction | Price/Variant Handling | Shopify scraper operational |
| 4 | WooCommerce/Others | Generic Fallbacks | Multi-platform support operational |
| 5 | Relational Data | Data Enhancement | Complete data model integration |
| 6 | Supabase Integration | Data Synchronization | Database operations functional |
| 7 | Scheduling System | Monitoring System | Automation framework operational |
| 8 | Comprehensive Testing | System Validation | Production-ready system |

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| Website structure changes | High | Medium | Multiple extraction methods, regular testing |
| Rate limiting/blocking | Medium | High | Polite scraping, exponential backoff, proxy rotation |
| Data quality issues | Medium | High | Multi-layered validation, confidence scoring |
| LLM cost escalation | Medium | Medium | Selective use, batching, caching valid results |
| Database scalability | Low | High | Efficient indexes, optimized queries, pagination |
