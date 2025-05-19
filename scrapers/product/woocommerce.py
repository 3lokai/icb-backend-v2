# scrapers/product/scrapers/woocommerce.py
"""
WooCommerce-specific implementation for coffee product scraping.
Handles API endpoints, fallbacks, and extraction from WooCommerce stores.
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
    process_woocommerce_variants,
    extract_weight_from_string,
    extract_all_attributes,
    validate_coffee_product,
    apply_validation_corrections,
    standardize_coffee_model
)

logger = logging.getLogger(__name__)

class WooRateLimiter:
    """Rate limiter for WooCommerce API to avoid hitting limits."""
    
    def __init__(self, requests_per_second=1.5):
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
rate_limiter = WooRateLimiter()

async def scrape_woocommerce(roaster: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Scrape products from a WooCommerce store.
    
    Args:
        roaster: Roaster data dictionary
        
    Returns:
        List of coffee product dictionaries
    """
    base_url = roaster['website_url'].rstrip('/')
    roaster_name = roaster['name']
    
    logger.info(f"Starting WooCommerce scraper for {roaster_name}")
    
    # Try each API endpoint in order
    api_endpoints = [
        "/wp-json/wc/v3/products",
        "/wp-json/wc/v2/products",
        "/wp-json/wp/v2/product",
        "/products.json"
    ]
    
    coffees = []
    
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        # Try each API endpoint until we find one that works
        for endpoint in api_endpoints:
            products_url = f"{base_url}{endpoint}?per_page=100"
            logger.info(f"Trying WooCommerce API endpoint: {products_url}")
            
            try:
                # Check cache first
                products_url_normalized = normalize_url(products_url)
                cache_key = f"woo_{get_domain_from_url(base_url)}_{endpoint.replace('/', '_')}"
                cached_data = get_cached_html(cache_key)

                if cached_data:
                    logger.info(f"Using cached data for {endpoint}")
                    products = json.loads(cached_data)
                else:
                    response = await fetch_with_retry(products_url, client=client, rate_limit=True, rate_limiter=rate_limiter)
                    products = response.json()
                    cache_html(cache_key, json.dumps(products))
                
                if isinstance(products, list) and len(products) > 0:
                    logger.info(f"Found {len(products)} products via API endpoint {endpoint}")
                    
                    # Process each product
                    coffee_products = []
                    for product in products:
                        try:
                            coffee = await process_woocommerce_product(product, roaster, client)
                            if coffee:
                                coffee_products.append(coffee)
                        except Exception as e:
                            product_name = product.get('name', product.get('title', {}).get('rendered', 'Unknown'))
                            logger.error(f"Error processing product {product_name}: {e}")
                            continue
                    
                    if coffee_products:
                        coffees.extend(coffee_products)
                        logger.info(f"Successfully processed {len(coffee_products)} coffee products")
                        return coffees
            
            except Exception as e:
                logger.warning(f"API endpoint {endpoint} failed: {e}")
                continue
        
        # If no API endpoints worked, try catalog page scraping
        logger.info("No products found via API. Trying catalog pages...")
        catalog_products = await scrape_product_catalog_pages(base_url, roaster, client)
        if catalog_products:
            coffees.extend(catalog_products)
            logger.info(f"Found {len(catalog_products)} products via catalog pages")
    
    logger.info(f"Completed WooCommerce scraping for {roaster_name}. Found {len(coffees)} coffee products.")
    return coffees

async def process_woocommerce_product(product: Dict[str, Any], roaster: Dict[str, Any], client: httpx.AsyncClient) -> Optional[Dict[str, Any]]:
    """Process a single WooCommerce product.
    
    Args:
        product: WooCommerce product data
        roaster: Roaster data dictionary
        client: HTTPX client
        
    Returns:
        Coffee product dictionary or None if not a coffee product
    """
    # Extract basic product data - handle different API versions
    name = product.get('name', product.get('title', {}).get('rendered', ''))
    if not name:
        logger.warning("Product missing name, skipping")
        return None
    
    # Extract description - handle different API versions
    description = ""
    if 'description' in product:
        if isinstance(product['description'], str):
            description = clean_html(product['description'])
        elif isinstance(product['description'], dict) and 'rendered' in product['description']:
            description = clean_html(product['description']['rendered'])
    elif 'content' in product and 'rendered' in product['content']:
        description = clean_html(product['content']['rendered'])
    
    # Extract product type and tags
    product_type = extract_product_type(product)
    tags = extract_tags(product)
    
    # Get product URL
    product_url = product.get('permalink', 
                    product.get('link', 
                            f"{roaster['website_url'].rstrip('/')}/product/{product.get('slug', create_slug(name))}"))
    
    # Skip non-coffee products
    if not is_coffee_product(
        name=name, 
        description=description, 
        product_type=product_type, 
        tags=tags, 
        roaster_name=roaster['name'], 
        url=product_url
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
        "direct_buy_url": product_url,
        "is_available": product.get('in_stock', product.get('stock_status', '') == 'instock'),
        "last_scraped_at": datetime.now().isoformat(),
        "scrape_status": "success"
    }
    
    # Get product image
    if 'images' in product and len(product['images']) > 0:
        coffee["image_url"] = product['images'][0].get('src', product['images'][0].get('source_url', ''))
    
    # Process price
    if 'price' in product:
        try:
            coffee["price_250g"] = float(product['price'])
        except (ValueError, TypeError):
            pass
    
    # Process variants if available
    if 'variations' in product and product['variations']:
        await process_woo_variations(coffee, product, roaster['website_url'], client)
    
    # Extract structured metadata if available
    metadata = extract_woocommerce_metadata(product)
    
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

async def process_woo_variations(coffee: Dict[str, Any], product: Dict[str, Any], base_url: str, client: httpx.AsyncClient):
    """Process WooCommerce product variations.
    
    Args:
        coffee: Coffee product dict to update
        product: WooCommerce product data
        base_url: Base URL of the store
        client: HTTPX client
        
    Returns:
        None (updates coffee dict in place)
    """
    variations = product.get('variations', [])
    
    # If variations are URLs, we need to fetch them
    if isinstance(variations, list) and all(isinstance(x, str) for x in variations):
        all_variations = []
        
        # Limit to first 5 variations to avoid too many requests
        for var_url in variations[:5]:
            try:
                if not var_url.startswith('http'):
                    var_url = urljoin(base_url, var_url)
                
                var_url_normalized = normalize_url(var_url)
                response = await fetch_with_retry(var_url_normalized, client)
                var_data = response.json()
                all_variations.append(var_data)
            except Exception as e:
                logger.warning(f"Error fetching variation: {e}")
                continue
        
        # Process the variations
        process_woocommerce_variants(coffee, all_variations)
    
    # If variations are already objects, process them directly
    elif isinstance(variations, list) and all(isinstance(x, dict) for x in variations):
        process_woocommerce_variants(coffee, variations)

def extract_product_type(product: Dict[str, Any]) -> str:
    """Extract product type from WooCommerce product data.
    
    Args:
        product: WooCommerce product data
        
    Returns:
        Product type string
    """
    # Try different locations based on API version
    if 'categories' in product:
        categories = product['categories']
        
        # Different APIs return categories differently
        if isinstance(categories, list):
            # Check for coffee in category names
            for cat in categories:
                if isinstance(cat, dict) and 'name' in cat:
                    if 'coffee' in cat['name'].lower():
                        return 'coffee'
                elif isinstance(cat, str) and 'coffee' in cat.lower():
                    return 'coffee'
    
    # Try from product type field
    product_type = product.get('type', '')
    if isinstance(product_type, str) and 'coffee' in product_type.lower():
        return 'coffee'
    
    # Default
    return ''

def extract_tags(product: Dict[str, Any]) -> List[str]:
    """Extract tags from WooCommerce product data.
    
    Args:
        product: WooCommerce product data
        
    Returns:
        List of tag strings
    """
    tags = []
    
    # Try tags array
    if 'tags' in product:
        product_tags = product['tags']
        if isinstance(product_tags, list):
            for tag in product_tags:
                if isinstance(tag, dict) and 'name' in tag:
                    tags.append(tag['name'].lower())
                elif isinstance(tag, str):
                    tags.append(tag.lower())
    
    # Try product attributes
    if 'attributes' in product:
        attributes = product['attributes']
        if isinstance(attributes, list):
            for attr in attributes:
                if isinstance(attr, dict) and 'options' in attr:
                    options = attr['options']
                    if isinstance(options, list):
                        for opt in options:
                            if isinstance(opt, str):
                                tags.append(opt.lower())
    
    return tags

def extract_woocommerce_metadata(product: Dict[str, Any]) -> Dict[str, Any]:
    """Extract structured metadata from WooCommerce product.
    
    Args:
        product: WooCommerce product data
        
    Returns:
        Dictionary of extracted metadata
    """
    metadata = {}
    
    # Extract from attributes
    if 'attributes' in product:
        attributes = product['attributes']
        if isinstance(attributes, list):
            for attr in attributes:
                if not isinstance(attr, dict):
                    continue
                
                name = attr.get('name', '').lower()
                options = attr.get('options', [])
                
                if not options or not isinstance(options, list) or not options[0]:
                    continue
                
                # Map attribute names to standard fields
                if name in ['roast', 'roast level', 'roast-level']:
                    metadata['roast_level'] = options[0]
                elif name in ['bean', 'bean type', 'bean-type', 'variety']:
                    metadata['bean_type'] = options[0]
                elif name in ['process', 'processing', 'processing method']:
                    metadata['processing_method'] = options[0]
                elif name in ['flavor', 'flavor notes', 'tasting notes']:
                    metadata['flavor_profiles'] = options
                elif name in ['origin', 'region']:
                    metadata['region_name'] = options[0]
    
    # Extract from meta_data if available (WooCommerce API v3)
    if 'meta_data' in product:
        meta_data = product['meta_data']
        if isinstance(meta_data, list):
            for meta in meta_data:
                if not isinstance(meta, dict):
                    continue
                
                key = meta.get('key', '').lower()
                value = meta.get('value')
                
                if key in ['roast_level', 'roast', 'roastlevel']:
                    metadata['roast_level'] = value
                elif key in ['bean_type', 'beantype', 'variety']:
                    metadata['bean_type'] = value
                elif key in ['processing', 'process', 'processingmethod']:
                    metadata['processing_method'] = value
                elif key in ['flavor_notes', 'flavors', 'tasting_notes']:
                    if isinstance(value, str):
                        metadata['flavor_profiles'] = [v.strip() for v in value.split(',')]
                    elif isinstance(value, list):
                        metadata['flavor_profiles'] = value
                elif key in ['origin', 'region', 'region_name']:
                    metadata['region_name'] = value
    
    return metadata

async def scrape_product_catalog_pages(base_url: str, roaster: Dict[str, Any], client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    """Fallback: Scrape product catalog pages when API fails.
    
    Args:
        base_url: Base URL of the store
        roaster: Roaster data dictionary
        client: HTTPX client
        
    Returns:
        List of coffee product dictionaries
    """
    coffee_products = []
    catalog_urls = [
        f"{base_url}/shop",
        f"{base_url}/product-category/coffee",
        f"{base_url}/coffee",
        f"{base_url}/products",
        f"{base_url}/collections/coffee"
    ]
    
    for url in catalog_urls:
        try:
            logger.info(f"Trying catalog page: {url}")
            response = await fetch_with_retry(url, client)
            html = response.text
            
            # Extract product links
            # This is a simplified approach - in production, use a proper HTML parser
            product_links = re.findall(r'<a href="([^"]+)"[^>]*class="[^"]*product[^"]*"', html)
            if not product_links:
                product_links = re.findall(r'<a href="([^"]+/product/[^"]+)"', html)
            
            if not product_links:
                logger.warning(f"No product links found on {url}")
                continue
                
            logger.info(f"Found {len(product_links)} product links on {url}")
            
            # Process links (limit to 20 to be reasonable)
            for link in product_links[:20]:
                # Ensure absolute URL
                if not link.startswith('http'):
                    link = urljoin(base_url, link)
                
                link_normalized = normalize_url(link)
                try:
                    logger.info(f"Fetching product: {link_normalized}")
                    response = await fetch_with_retry(link_normalized, client)
                    product_html = response.text
                    
                    # Extract product data from HTML
                    coffee = await extract_product_from_html(product_html, url, roaster)
                    if coffee:
                        coffee_products.append(coffee)
                except Exception as e:
                    logger.error(f"Error processing product {link}: {e}")
                    continue
            
            # If we found some products, return them
            if coffee_products:
                return coffee_products
                
        except Exception as e:
            logger.warning(f"Error scraping catalog {url}: {e}")
            continue
    
    return coffee_products

async def extract_product_from_html(html: str, url: str, roaster: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract product data from HTML.
    
    Args:
        html: Product page HTML
        url: Product URL
        roaster: Roaster data dictionary
        
    Returns:
        Coffee product dictionary or None if not a coffee product
    """
    # Extract basic product data
    title_match = re.search(r'<h1[^>]*class="[^"]*product_title[^"]*"[^>]*>([^<]+)</h1>', html)
    if not title_match:
        title_match = re.search(r'<title>([^<|]+)', html)
    
    if not title_match:
        logger.warning(f"Could not extract title from {url}")
        return None
    
    name = title_match.group(1).strip()
    
    # Extract description
    desc_match = re.search(r'<div[^>]*class="[^"]*product-description[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
    if not desc_match:
        desc_match = re.search(r'<div[^>]*class="[^"]*woocommerce-product-details__short-description[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
    if not desc_match:
        desc_match = re.search(r'<div[^>]*id="tab-description"[^>]*>(.*?)</div>', html, re.DOTALL)
    
    description = clean_html(desc_match.group(1) if desc_match else "")
    
    # Skip non-coffee products
    if not is_coffee_product(name, description, "", [], roaster['name'], url):
        logger.debug(f"Skipping non-coffee product: {name}")
        return None
    
    # Create base coffee object
    coffee = {
        "name": name,
        "slug": create_slug(name),
        "roaster_id": roaster.get('id'),
        "roaster_slug": roaster.get('slug'),
        "description": description,
        "direct_buy_url": url,
        "is_available": True,  # Default to available
        "last_scraped_at": datetime.now().isoformat(),
        "scrape_status": "success"
    }
    
    # Extract image URL
    img_match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
    if not img_match:
        img_match = re.search(r'<img[^>]*class="[^"]*wp-post-image[^"]*"[^>]*src="([^"]+)"', html)
    if not img_match:
        img_match = re.search(r'<div[^>]*class="[^"]*product-images[^"]*"[^>]*>.*?<img[^>]*src="([^"]+)"', html, re.DOTALL)
    
    if img_match:
        coffee["image_url"] = img_match.group(1)
    
    # Extract price
    price_match = re.search(r'<span class="woocommerce-Price-amount amount">\s*<[^>]*>\s*[^<]*</[^>]*>\s*([0-9,.]+)', html, re.DOTALL)
    if not price_match:
        price_match = re.search(r'<p[^>]*class="[^"]*price[^"]*"[^>]*>\s*<span[^>]*>\s*<[^>]*>\s*[^<]*</[^>]*>\s*([0-9,.]+)', html, re.DOTALL)
    if not price_match:
        price_match = re.search(r'<span[^>]*id="price[^"]*"[^>]*>\s*<[^>]*>\s*([0-9,.]+)', html, re.DOTALL)
    
    if price_match:
        try:
            coffee["price_250g"] = float(price_match.group(1).replace(',', ''))
        except (ValueError, TypeError):
            pass
    
    # Extract variants
    extract_price_from_html(coffee, html)
    
    # Extract attributes
    coffee = extract_all_attributes(
        coffee=coffee,
        text=description,
        tags=[],  # No tags available from HTML directly
        name=name
    )
    
    # Run validation and corrections
    validation_results = validate_coffee_product(coffee)
    coffee = apply_validation_corrections(coffee, validation_results)
    
    # Standardize model before returning
    return standardize_coffee_model(coffee)

def extract_price_from_html(coffee: Dict[str, Any], html: str):
    """Extract price and variant information from HTML.
    
    Args:
        coffee: Coffee product dict to update
        html: Product page HTML
        
    Returns:
        None (updates coffee dict in place)
    """
    # Extract variants from variations form
    variant_container_patterns = [
        r'<table[^>]*class="[^"]*variations[^"]*"[^>]*>(.*?)</table>',
        r'<form[^>]*class="[^"]*variations_form[^"]*"[^>]*>(.*?)</form>'
    ]
    
    for pattern in variant_container_patterns:
        container_match = re.search(pattern, html, re.DOTALL)
        if container_match:
            variants_html = container_match.group(1)
            
            # Look for weight options
            weight_options = re.findall(r'<option[^>]*value="([^"]+)"[^>]*>([^<]+)', variants_html)
            
            weight_prices = []
            for value, label in weight_options:
                # Skip empty or default options
                if not value or value.lower() == 'choose an option':
                    continue
                
                # Extract weight from label
                weight_grams, confidence = extract_weight_from_string(label)
                
                if not weight_grams:
                    continue
                
                # Try to find price for this option
                price_match = re.search(fr'data-value="{re.escape(value)}"[^>]*>.*?([0-9,.]+)', variants_html, re.DOTALL)
                if price_match:
                    try:
                        price = float(price_match.group(1).replace(',', ''))
                        if price > 0:
                            # Map to standardized weight categories
                            if weight_grams <= 100:
                                coffee["price_100g"] = price
                            elif weight_grams <= 250:
                                coffee["price_250g"] = price
                            elif weight_grams <= 500:
                                coffee["price_500g"] = price
                            else:
                                coffee["price_1kg"] = price
                    except ValueError:
                        continue
            
            # If found variants, we're done
            if "price_100g" in coffee or "price_250g" in coffee or "price_500g" in coffee or "price_1kg" in coffee:
                return
    
    # If no variants found, try to extract weight from product name/description
    if "price_250g" in coffee:
        name = coffee.get('name', '')
        description = coffee.get('description', '')
        
        weight_match = re.search(r'(\d+\.?\d*)\s*(g|gram|gm|kg)', (name + ' ' + description).lower())
        
        if weight_match:
            weight_value = float(weight_match.group(1))
            weight_unit = weight_match.group(2).lower()
            
            # Convert to grams
            if 'kg' in weight_unit:
                weight_grams = int(weight_value * 1000)
            else:
                weight_grams = int(weight_value)
            
            # Move price to appropriate category
            current_price = coffee["price_250g"]
            
            if weight_grams <= 100:
                coffee["price_100g"] = current_price
                del coffee["price_250g"]
            elif weight_grams <= 250:
                # Already in the right category
                pass
            elif weight_grams <= 500:
                coffee["price_500g"] = current_price
                del coffee["price_250g"]
            else:
                coffee["price_1kg"] = current_price
                del coffee["price_250g"]

async def scrape_single_product(url: str, roaster: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Scrape a single WooCommerce product by URL.
    
    Args:
        url: Product URL
        roaster: Roaster data dictionary
        
    Returns:
        Coffee product dictionary or None if not a coffee product
    """
    # Extract product slug from URL
    slug_match = re.search(r'/product/([^/?#]+)', url)
    if not slug_match:
        logger.warning(f"Could not extract product slug from URL: {url}")
        return None
    
    slug = slug_match.group(1)
    base_url = roaster['website_url'].rstrip('/')
    
    # Try API endpoints
    api_endpoints = [
        f"{base_url}/wp-json/wc/v3/products?slug={slug}",
        f"{base_url}/wp-json/wc/v2/products?slug={slug}",
        f"{base_url}/wp-json/wp/v2/product?slug={slug}"
    ]
    
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        # Try API endpoints first
        for endpoint in api_endpoints:
            try:
                response = await fetch_with_retry(endpoint, client=client, rate_limit=True, rate_limiter=rate_limiter)
                products = response.json()
                
                if isinstance(products, list) and len(products) > 0:
                    return await process_woocommerce_product(products[0], roaster, client)
                
            except Exception as e:
                logger.warning(f"API endpoint {endpoint} failed: {e}")
                continue
        
        # Fallback to scraping HTML
        try:
            response = await fetch_with_retry(url, client=client, rate_limit=True, rate_limiter=rate_limiter)
            html = response.text
            return await extract_product_from_html(html, url, roaster)
            
        except Exception as e:
            logger.error(f"Error scraping product {url}: {e}")
            return None
