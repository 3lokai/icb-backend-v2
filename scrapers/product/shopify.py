# scrapers/product/scrapers/shopify.py
"""
Shopify-specific implementation for coffee product scraping.
Handles API pagination, rate limiting, and extraction from Shopify stores.
"""

import json
import re
import asyncio
import random
import logging
from typing import Dict, List, Any, Optional, Tuple
import httpx
from datetime import datetime
from urllib.parse import urljoin

from common.utils import clean_html, is_coffee_product, create_slug, get_domain_from_url, fetch_with_retry, normalize_url
from common.cache import get_cached_html, cache_html
from config import config

# Import the extractors
from scrapers.product.extractors import (
    process_variants,
    extract_all_attributes,
    validate_coffee_product,
    apply_validation_corrections,
    standardize_coffee_model
)

logger = logging.getLogger(__name__)

class ShopifyRateLimiter:
    """Rate limiter for Shopify API to avoid hitting limits."""
    
    def __init__(self, requests_per_second=2):
        """Initialize rate limiter.
        
        Args:
            requests_per_second: Maximum requests per second
        """
        self.delay = 1.0 / requests_per_second
        self.last_request_time = 0
        self.lock = asyncio.Lock()
    
    async def wait(self):
        """Wait for next available request slot."""
        async with self.lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self.last_request_time
            
            if elapsed < self.delay:
                # Add jitter to avoid thundering herd
                jitter = random.uniform(0, 0.1)
                sleep_time = self.delay - elapsed + jitter
                await asyncio.sleep(sleep_time)
            
            self.last_request_time = asyncio.get_event_loop().time()

# Create global rate limiter instance
rate_limiter = ShopifyRateLimiter()

async def get_product_count(base_url: str, client: httpx.AsyncClient) -> int:
    """Get total product count from a Shopify store.
    
    Args:
        base_url: Shopify store base URL
        client: HTTPX client
        
    Returns:
        Total product count
    """
    count_url = f"{base_url}/products/count.json"
    
    try:
        response = await fetch_with_retry(count_url, client)
        data = response.json()
        return data.get('count', 0)
    except Exception as e:
        logger.warning(f"Failed to get product count: {e}")
        return 0

async def scrape_shopify(roaster: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Scrape products from a Shopify store.
    
    Args:
        roaster: Roaster data dictionary
        
    Returns:
        List of coffee product dictionaries
    """
    base_url = roaster['website_url'].rstrip('/')
    roaster_name = roaster['name']
    
    logger.info(f"Starting Shopify scraper for {roaster_name}")
    
    coffees = []
    page = 1
    per_page = 250  # Maximum allowed by Shopify API
    has_more = True
    
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        # First try to get total product count for better progress reporting
        total_products = await get_product_count(base_url, client)
        if total_products:
            logger.info(f"Found {total_products} total products on {roaster_name}")
        
        # Paginate through products
        while has_more:
            products_url = f"{base_url}/products.json?limit={per_page}&page={page}"
            logger.info(f"Fetching page {page} from {roaster_name}")
            
            try:
                # Check cache first
                products_url_normalized = normalize_url(products_url)
                cache_key = f"shopify_{get_domain_from_url(base_url)}_page_{page}"
                cached_data = get_cached_html(cache_key)
                
                if cached_data:
                    products_data = json.loads(cached_data)
                else:
                    response = await fetch_with_retry(products_url_normalized, client)
                    products_data = response.json()
                    cache_html(cache_key, json.dumps(products_data))
                
                products = products_data.get('products', [])
                
                if not products:
                    logger.info(f"No more products found for {roaster_name}")
                    break
                
                # If we got fewer than the requested limit, we've reached the end
                if len(products) < per_page:
                    has_more = False
                
                logger.info(f"Processing {len(products)} products from page {page}")
                
                # Process each product
                for product in products:
                    try:
                        coffee = await process_shopify_product(product, roaster, client)
                        if coffee:
                            coffees.append(coffee)
                    except Exception as e:
                        logger.error(f"Error processing product {product.get('title', 'Unknown')}: {e}")
                        continue
                
                page += 1
                
            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                has_more = False
    
    logger.info(f"Completed Shopify scraping for {roaster_name}. Found {len(coffees)} coffee products.")
    return coffees

async def process_shopify_product(product: Dict[str, Any], roaster: Dict[str, Any], client: httpx.AsyncClient) -> Optional[Dict[str, Any]]:
    """Process a single Shopify product.
    
    Args:
        product: Shopify product data
        roaster: Roaster data dictionary
        client: HTTPX client
        
    Returns:
        Coffee product dictionary or None if not a coffee product
    """
    # Extract basic product data
    name = product.get('title', '')
    if not name:
        logger.warning("Product missing title, skipping")
        return None
    
    handle = product.get('handle', '')
    description = clean_html(product.get('body_html', ''))
    product_type = product.get('product_type', '')
    tags = product.get('tags', [])
    
    # Skip non-coffee products
    if not is_coffee_product(
        name=name, 
        description=description, 
        product_type=product_type, 
        tags=tags, 
        roaster_name=roaster['name'], 
        url=handle
    ):
        logger.debug(f"Skipping non-coffee product: {name}")
        return None
    
    # Create base coffee object
    coffee = {
        "name": name,
        "slug": create_slug(name),
        "roaster_id": roaster.get('id'),
        "roaster_slug": roaster.get('slug'),
        "description": description,
        "direct_buy_url": normalize_url(f"{roaster['website_url'].rstrip('/')}/products/{handle}"),
        "is_available": product.get('available', True),
        "last_scraped_at": datetime.now().isoformat(),
        "scrape_status": "success"
    }
    
    # Get product image
    if product.get('images') and len(product.get('images')) > 0:
        coffee["image_url"] = product['images'][0].get('src')
    
    # Process variants and pricing
    coffee = process_variants(coffee, product)
    
    # Extract structured metadata if available
    metadata = extract_shopify_metadata(product)
    
    # Extract all attributes using our extractors
    coffee = extract_all_attributes(
        coffee=coffee,
        text=description,
        tags=tags,
        structured_data=metadata,
        name=name
    )
    
    # Run validation and corrections
    validation_results = validate_coffee_product(coffee)
    coffee = apply_validation_corrections(coffee, validation_results)
    
    # Standardize model before returning
    return standardize_coffee_model(coffee)

def extract_shopify_metadata(product: Dict[str, Any]) -> Dict[str, Any]:
    """Extract structured metadata from Shopify product.
    
    Args:
        product: Shopify product data
        
    Returns:
        Dictionary of extracted metadata
    """
    metadata = {}
    
    # Look for metafields
    metafields = product.get('metafields', [])
    for field in metafields:
        key = field.get('key', '').lower()
        value = field.get('value')
        
        if key in ['roast_level', 'roast', 'roastlevel']:
            metadata['roast_level'] = value
        elif key in ['bean_type', 'beantype', 'variety']:
            metadata['bean_type'] = value
        elif key in ['processing', 'process', 'processingmethod']:
            metadata['processing_method'] = value
        elif key in ['flavor_notes', 'flavors', 'tasting_notes']:
            metadata['flavor_profiles'] = value
    
    # Extract from options
    options = product.get('options', [])
    for option in options:
        name = option.get('name', '').lower()
        values = option.get('values', [])
        
        if name in ['roast', 'roast level']:
            if values and len(values) > 0:
                metadata['roast_level'] = values[0]
        elif name in ['processing', 'process']:
            if values and len(values) > 0:
                metadata['processing_method'] = values[0]
    
    return metadata

async def scrape_single_product(url: str, roaster: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Scrape a single Shopify product by URL.
    
    Args:
        url: Product URL
        roaster: Roaster data dictionary
        
    Returns:
        Coffee product dictionary or None if not a coffee product
    """
    # Extract product handle from URL
    handle_match = re.search(r'/products/([^/?#]+)', url)
    if not handle_match:
        logger.warning(f"Could not extract product handle from URL: {url}")
        return None
    
    handle = handle_match.group(1)
    base_url = roaster['website_url'].rstrip('/')
    product_json_url = f"{base_url}/products/{handle}.json"
    
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        try:
            product_json_url_normalized = normalize_url(product_json_url)
            response = await fetch_with_retry(product_json_url_normalized, client)
            product_data = response.json()
            
            # Shopify returns a wrapper object with a 'product' key
            product = product_data.get('product')
            if not product:
                logger.warning(f"No product data found at {product_json_url}")
                return None
            
            return await process_shopify_product(product, roaster, client)
            
        except Exception as e:
            logger.error(f"Error scraping product {url}: {e}")
            return None
