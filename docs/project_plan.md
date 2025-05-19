# Coffee Scraper Project Plan

## File Structure and Changes

### Configuration Files

| File | Status | Changes Needed |
|------|--------|----------------|
| `config.py` | Update | Add Supabase credentials, update paths, add LLM API keys |
| `requirements.txt` | Update | Add new dependencies: httpx, supabase-py, asyncio, etc. |

### Main Entry Points

| File | Status | Changes Needed |
|------|--------|----------------|
| `main.py` | Create New | Central orchestrator with command line interface |

### Scrapers

| File | Status | Changes Needed |
|------|--------|----------------|
| `scrapers/__init__.py` | Create New | Package initialization |
| `scrapers/shopify.py` | Update | Refine product extraction, enhance price detection, map to new schema |
| `scrapers/woocommerce.py` | Update | Refine product extraction, enhance price detection, map to new schema |
| `scrapers/static.py` | Update | Improve generic scraper for unknown platforms |

### Common Utilities

| File | Status | Changes Needed |
|------|--------|----------------|
| `common/__init__.py` | Create New | Package initialization |
| `common/platform_detector.py` | Update | Move from existing code, improve detection reliability |
| `common/utils.py` | Update | Move core utilities from existing codebase, enhance |
| `common/cache.py` | Update | Improve caching mechanisms |
| `common/enricher.py` | Create New | Consolidate LLM enrichment logic from existing code |

### Database Integration

| File | Status | Changes Needed |
|------|--------|----------------|
| `db/__init__.py` | Create New | Package initialization |
| `db/supabase.py` | Create New | Supabase client and CRUD operations |
| `db/models.py` | Create New | Define data models matching Supabase schema |

## Project Implementation Stages

### Stage 0: Project Setup
- [x] Create project structure in Windows VSCode
- [x] Setup configuration (`config.py`) with Supabase credentials and other settings
- [x] Define data models in `db/models.py` to match Supabase schema
- [x] Set up basic logging configuration
- [x] Install required dependencies
- [x] Create common/utils.py and common/cache.py for utility functions and caching

### Stage 1: Roaster Scraping
- [x] Implement platform detection in `common/platform_detector.py`
- [x] Develop roaster data extraction in platform-specific scrapers
- [x] Add data validation and normalization
- [x] Implement LLM-based enrichment for missing data
- [ ] Export roaster data to CSV/JSON

### Stage 2: Shopify Product Scraping
- [ ] Enhance Shopify scraper for product data
- [ ] Improve variant and price extraction for different weights
- [ ] Extract flavor profiles, brewing methods, and other attributes
- [ ] Map data to Supabase schema format
- [ ] Export product data to CSV/JSON

### Stage 3: WooCommerce Product Scraping
- [ ] Enhance WooCommerce scraper for product data
- [ ] Improve variation and price extraction
- [ ] Extract product attributes and metadata
- [ ] Map data to Supabase schema format
- [ ] Export product data to CSV/JSON

### Stage 4: Static/Other Platform Scraping
- [ ] Improve generic scraper for unknown platforms
- [ ] Implement fallback extraction mechanisms
- [ ] Enhance data validation for varied structures
- [ ] Map data to Supabase schema format
- [ ] Export product data to CSV/JSON

### Stage 5: Supabase Integration
- [ ] Implement Supabase client in `db/supabase.py`
- [ ] Develop CRUD operations for all relevant tables
- [ ] Create data transformation functions to map scraped data to Supabase schema
- [ ] Implement relational data handling (coffee-flavor relationships, etc.)
- [ ] Add error handling and retry mechanisms

### Stage 6: Additional Enhancements
- [ ] Add missing fields if needed
- [ ] Improve data quality through additional validation
- [ ] Add comprehensive logging and error reporting
- [ ] Create data exploration and validation tools
- [ ] Optimize performance for large-scale scraping

### Stage 7: Automation
- [ ] Implement scheduling mechanisms
- [ ] Add incremental update functionality
- [ ] Create monitoring and notification systems
- [ ] Document the automation process
- [ ] Set up recurring scrape jobs

## Priority Order
1. Basic scraping infrastructure
2. Roaster data extraction
3. Product data extraction (platform-specific)
4. Data enrichment
5. Supabase integration
6. Automation