# Consolidated Refactoring Plan for roaster.py

Here's a comprehensive plan that allows for incremental refactoring while maintaining functionality at each step. You'll be able to test each component individually against your `roasters_input.csv` file.

## 1. Directory Structure

```
scrapers/
├── __init__.py
├── roaster/
│   ├── __init__.py             # Exposes main functions 
│   ├── scraper.py              # Core scraper (simplified)
│   ├── extractors.py           # Basic extractors
│   ├── selectors.py            # Platform-specific selector configs
│   ├── location.py             # Location extraction logic
│   ├── about.py                # About page extraction
│   ├── enricher.py             # LLM fallback logic
│   └── batch.py                # Batch processing
```

## 2. Step-by-Step Implementation

### Step 1: Create the Package Structure

```bash
mkdir -p scrapers/roaster
touch scrapers/roaster/__init__.py
```

### Step 2: Create selectors.py

Extract the platform selector configuration to make it independently maintainable:

```python
"""Platform-specific selectors for roaster scraping."""

def get_platform_selectors(platform: str = None):
    """Get platform-specific selectors for different content types."""
    platform_selectors = {
        "shopify": {
            "contact_page": ["/pages/contact", "/pages/contact-us", "/pages/locations", "/contact"],
            "about_page": ["/pages/about", "/pages/about-us", "/pages/our-story", "/pages/story"],
            "contact_section": [".contact-form", "#ContactForm", ".contact-page", "footer .address", ".section--contact"],
            "address_elements": ["address", ".address", "[itemprop='address']", ".footer__store-info"],
            "social_links": [".social-links", ".social-icons", "footer .social", ".footer__social"],
            "logo": [".header__logo img", ".logo-image", "[data-header-logo]", ".site-header__logo img"]
        },
        # ... other platforms ...
        "static": {  # Fallback for unknown platforms
            "contact_page": ["/contact", "/contact-us", "/reach-us", "/locations"],
            "about_page": ["/about", "/about-us", "/our-story", "/who-we-are"],
            "contact_section": [".contact", "#contact", "footer", ".footer", ".address", ".contact-form"],
            "address_elements": ["address", ".address", "[itemprop='address']", ".contact-info", ".footer-address"],
            "social_links": [".social", ".social-media", ".social-links", ".social-icons", ".footer-social"],
            "logo": [".logo", "#logo", "header img", ".brand img", ".site-logo img"]
        }
    }
    
    if platform and platform in platform_selectors:
        return platform_selectors[platform]
    
    return platform_selectors["static"]
```

### Step 3: Create extractors.py

```python
"""Basic extraction utilities for roaster scraping."""

import re
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import logging

from common.utils import normalize_phone_number

logger = logging.getLogger(__name__)

def extract_logo(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    """Extract logo URL from website."""
    # Implementation from the _extract_logo method
    # ...

def extract_email(soup: BeautifulSoup, html_content: str, roaster_data: Dict[str, Any]) -> Optional[str]:
    """Extract email address from page content."""
    # Implementation from the _extract_email method 
    # ...

def extract_hero_image(soup: BeautifulSoup, url: str) -> Optional[str]:
    """Extract hero/banner image from website."""
    # Implementation from the _extract_hero_image method
    # ...

def extract_phone_number(soup: BeautifulSoup, html_content: str) -> Optional[str]:
    """Extract phone number from website."""
    # Implementation from the _extract_phone_number method
    # ...

def extract_founded_year(html_content: str) -> Optional[int]:
    """Extract founded year from website."""
    # Implementation from the _extract_founded_year method
    # ...

def check_business_features(roaster_data: Dict[str, Any], soup: BeautifulSoup, html_content: str) -> Dict[str, Any]:
    """Check for business features like subscription and physical store."""
    # Implementation from the _check_business_features method
    # ... 
    return roaster_data

def ensure_absolute_url(url: str, base_url: str) -> str:
    """Ensure a URL is absolute."""
    # Implementation from the _ensure_absolute_url method
    # ...

def get_domain_from_url(url: str) -> str:
    """Extract the domain from a URL."""
    # Implementation from the _get_domain_from_url method
    # ...
```

### Step 4: Create location.py

```python
"""Location extraction for roaster scraping."""

import re
from typing import Dict, Any
from bs4 import BeautifulSoup
import logging

from .selectors import get_platform_selectors

logger = logging.getLogger(__name__)

# State lookup mapping for standardization
STATE_MAPPING = {
    'karnataka': 'Karnataka',
    'bangalore': 'Karnataka',
    'bengaluru': 'Karnataka',
    # ... other states ...
}

def extract_location(roaster_data: Dict[str, Any], soup: BeautifulSoup, html_content: str, platform: str) -> Dict[str, Any]:
    """Extract location information from a website."""
    # Implementation based on _extract_location_from_platform method
    # ...
    return roaster_data

def parse_address(roaster_data: Dict[str, Any], address_text: str) -> Dict[str, Any]:
    """Parse address text to extract location information."""
    # Implementation based on _parse_address method
    # ...
    return roaster_data
```

### Step 5: Create about.py

```python
"""About page extraction for roaster scraping."""

import re
from typing import Dict, Any, Optional
import logging
import httpx
from bs4 import BeautifulSoup

from common.cache import cache
from common.utils import fetch_with_retry
from .selectors import get_platform_selectors

logger = logging.getLogger(__name__)

async def extract_about_page_info(base_url: str, platform: str, force_refresh: bool = False) -> Dict[str, Any]:
    """Extract information from about pages."""
    # Implementation based on _scrape_about_pages method
    # ...
    return about_data

def update_with_about_data(roaster_data: Dict[str, Any], about_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update roaster data with information from about pages."""
    # Implementation based on _update_with_about_data method
    # ...
    return roaster_data
```

### Step 6: Create enricher.py

```python
"""LLM enrichment for roaster data."""

from typing import Dict, Any, Optional
import logging

from common.enricher import enricher

logger = logging.getLogger(__name__)

# Define critical fields that should be enriched if missing
CRITICAL_FIELDS = ["description", "founded_year", "city", "state"]

async def enrich_missing_fields(roaster_data: Dict[str, Any], extracted_html: str = None) -> Dict[str, Any]:
    """Enrich missing critical fields with LLM."""
    # Implementation as described earlier
    # ...
    return roaster_data
```

### Step 7: Create batch.py

```python
"""Batch processing for roaster scraping."""

import csv
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

from .scraper import RoasterScraper

logger = logging.getLogger(__name__)

async def scrape_roasters_from_csv(csv_path: str, output_path: str = None, limit: int = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Scrape roasters from a CSV file."""
    # Implementation from the existing function
    # ...
    return results, errors
```

### Step 8: Create the core scraper.py

```python
"""Core roaster scraper implementation."""

import re
import logging
import asyncio
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup

from common.utils import create_slug, clean_html
from common.cache import cache
from common.platform_detector import detect_platform

from .extractors import (
    extract_logo, extract_email, extract_hero_image, 
    extract_founded_year, check_business_features, 
    ensure_absolute_url
)
from .location import extract_location, parse_address
from .about import extract_about_page_info, update_with_about_data
from .enricher import enrich_missing_fields
from .selectors import get_platform_selectors

logger = logging.getLogger(__name__)

class RoasterScraper:
    """Scraper for coffee roaster websites."""
    
    def __init__(self, enrichment_service=None):
        """Initialize roaster scraper."""
        self.enrichment_service = enrichment_service
        
        # Fields and their stability ratings (for incremental updates)
        self.field_stability = {
            # Highly stable (annual check)
            "name": "highly_stable",
            # ... other fields ...
        }
    
    async def scrape_roaster(self, name: str, url: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """Scrape a roaster website to extract roaster information."""
        logger.info(f"Scraping roaster: {name} ({url})")
        
        # Core implementation that delegates to the appropriate modules
        # ...
        
        return roaster_data
        
    async def _check_site_activity(self, url: str) -> Dict[str, Any]:
        """Check if a website is active and accessible."""
        # Implementation remains in the core class
        # ...
        
    async def _fetch_page(self, url: str, force_refresh: bool = False) -> str:
        """Fetch a page with caching."""
        # Implementation remains in the core class
        # ...
        
    def _extract_basic_info(self, roaster_data: Dict[str, Any], soup: BeautifulSoup, html_content: str, url: str, platform: str) -> None:
        """Extract basic information from roaster homepage."""
        # This now delegates to the other modules
        # ...
        
    def _extract_contact_info(self, roaster_data: Dict[str, Any], soup: BeautifulSoup, html_content: str, platform: str) -> None:
        """Extract all contact information using platform-specific selectors."""
        # This now delegates to the extractors
        # ...
        
    def _extract_shopify_structured_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract Shopify specific structured data."""
        # Keep this helper in the core class
        # ...
        
    def _cleanup_data(self, roaster_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up roaster data before returning."""
        # Keep this helper in the core class
        # ...
```

### Step 9: Create the __init__.py with the API

```python
"""Roaster scraper package."""

from .scraper import RoasterScraper
from .batch import scrape_roasters_from_csv

__all__ = ['RoasterScraper', 'scrape_roasters_from_csv']
```

## 3. Migration Strategy

1. **Start with non-core components**: Begin with selectors.py and extractors.py
2. **Test each module**: After each component creation, ensure it works independently
3. **Integrate step-by-step**: Update scraper.py to use each new module one at a time
4. **Parallel testing**: Run both old and new implementations against the same data
5. **Validate outputs**: Ensure the outputs match between old and new implementations
