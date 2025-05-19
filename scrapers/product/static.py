# scrapers/product/scrapers/static.py
"""
Static site implementation for coffee product scraping.
Handles sitemap parsing and HTML extraction for non-platform sites.
"""

import asyncio
import re
import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Tuple
import httpx
# Crawl4AI import for deep crawling fallback
try:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
except ImportError:
    AsyncWebCrawler = None
    CrawlerRunConfig = None
    # Warn at runtime if fallback is attempted without dependency
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from common.utils import clean_html, is_coffee_product, create_slug, get_domain_from_url, fetch_with_retry, normalize_url
from common.cache import get_cached_html, cache_html
from config import config

# Import the extractors
from scrapers.product.extractors import (
    extract_price_from_html,
    extract_all_attributes,
    validate_coffee_product,
    apply_validation_corrections,
    standardize_coffee_model
)

logger = logging.getLogger(__name__)

async def crawl4ai_deepcrawl_products(base_url: str, roaster: dict) -> list:
    """
    Use Crawl4AI's deep crawling to discover and scrape potential coffee product pages.
    """
    products = []
    # Defensive: Only run if dependency is present
    if AsyncWebCrawler is None or CrawlerRunConfig is None:
        logger.error("Crawl4AI is not installed. Cannot perform deep crawling fallback.")
        return []
    try:
        async with AsyncWebCrawler() as crawler:
            config = CrawlerRunConfig(
                max_depth=2,  # Tune as needed
                max_pages=50, # Tune as needed
                allowed_domains=[get_domain_from_url(base_url)]
            )
            result = await crawler.arun(base_url, config=config)
            # result.pages is a list of crawled pages (each with .url, .markdown, .html)
            for page in getattr(result, 'pages', []):
                try:
                    coffee = await extract_product_from_html(page.html, page.url, "", roaster)
                    if coffee:
                        products.append(coffee)
                except Exception as e:
                    logger.error(f"Error extracting coffee from Crawl4AI page {page.url}: {e}")
    except Exception as e:
        logger.error(f"Crawl4AI deep crawling failed: {e}")
    return products

async def scrape_static_site(roaster: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Scrape products from a static site using sitemaps and HTML parsing.
    
    Args:
        roaster: Roaster data dictionary
        
    Returns:
        List of coffee product dictionaries
    """
    base_url = roaster['website_url'].rstrip('/')
    roaster_name = roaster['name']
    
    logger.info(f"Starting static site scraper for {roaster_name}")
    
    # Check common sitemap locations
    sitemap_locations = [
        f"{base_url}/sitemap.xml",
        f"{base_url}/sitemap_index.xml",
        f"{base_url}/sitemap_products.xml",
        f"{base_url}/sitemap-products.xml",
        f"{base_url}/sitemaps/sitemap.xml"
    ]
    
    candidate_products = []
    scraped_coffees = []
    
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        # Step 1: Find and parse sitemaps
        sitemap_found = False
        
        for sitemap_url in sitemap_locations:
            try:
                logger.info(f"Checking sitemap: {sitemap_url}")
                
                # Check cache first
                cache_key = f"sitemap_{get_domain_from_url(base_url)}_{sitemap_url.split('/')[-1]}"
                cached_data = get_cached_html(cache_key)
                
                if cached_data:
                    root_xml = cached_data
                else:
                    response = await fetch_with_retry(sitemap_url, client=client)
                    root_xml = response.text
                    cache_html(cache_key, root_xml)
                
                product_urls = await parse_sitemap(root_xml, base_url, client)
                
                if product_urls:
                    candidate_products.extend(product_urls)
                    sitemap_found = True
                    logger.info(f"Found {len(product_urls)} candidate products in {sitemap_url}")
            
            except Exception as e:
                logger.warning(f"Failed to load sitemap {sitemap_url}: {e}")
                continue
        
        # Step 2: If no sitemap found, try catalog pages
        if not sitemap_found:
            logger.info("No sitemap found. Trying catalog pages.")
            catalog_products = await scrape_product_catalog_pages(base_url, roaster, client)
            if catalog_products:
                scraped_coffees.extend(catalog_products)
                logger.info(f"Found {len(catalog_products)} products via catalog pages")
                return scraped_coffees
        
        # Step 3: Process candidate products
        logger.info(f"Processing {len(candidate_products)} candidate products")
        
        for i, (url, title) in enumerate(candidate_products):
            if i % 10 == 0:
                logger.info(f"Processing product {i+1}/{len(candidate_products)}")
                
            try:
                # Check cache first
                url_normalized = normalize_url(url)
                cache_key = f"static_{get_domain_from_url(base_url)}_{url.split('/')[-1]}"
                cached_data = get_cached_html(cache_key)
                
                if cached_data:
                    html = cached_data
                else:
                    response = await fetch_with_retry(url_normalized, client=client)
                    html = response.text
                    cache_html(cache_key, html)
                
                coffee = await extract_product_from_html(html, url, title, roaster)
                if coffee:
                    scraped_coffees.append(coffee)
            
            except Exception as e:
                logger.error(f"Error processing product {url}: {e}")
                continue
    
    # FINAL FALLBACK: If no products found, use Crawl4AI deep crawling
    MIN_EXPECTED_PRODUCTS = 2
    if (not scraped_coffees or len(scraped_coffees) < MIN_EXPECTED_PRODUCTS):
        logger.warning(f"Fallback to Crawl4AI deep crawling for {roaster_name}")
        if AsyncWebCrawler is None:
            logger.error("Crawl4AI is not installed. Cannot perform deep crawling fallback.")
        else:
            try:
                crawl4ai_products = await crawl4ai_deepcrawl_products(base_url, roaster)
                scraped_coffees.extend(crawl4ai_products)
            except Exception as e:
                logger.error(f"Crawl4AI deep crawling failed: {e}")
    logger.info(f"Completed static site scraping for {roaster_name}. Found {len(scraped_coffees)} coffee products.")
    return scraped_coffees

async def parse_sitemap(sitemap_xml: str, base_url: str, client: httpx.AsyncClient) -> List[Tuple[str, str]]:
    """Parse sitemap XML to extract product URLs and titles.
    
    Args:
        sitemap_xml: Sitemap XML content
        base_url: Base URL of the site
        client: HTTPX client
        
    Returns:
        List of tuples (url, title)
    """
    product_urls = []
    
    try:
        root = ET.fromstring(sitemap_xml)
        
        # Define XML namespaces
        ns = {
            'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
            'image': 'http://www.google.com/schemas/sitemap-image/1.1'
        }
        
        # Check if this is a sitemap index
        sitemap_locations = root.findall('.//ns:sitemap/ns:loc', ns)
        
        if sitemap_locations:
            # This is a sitemap index, process child sitemaps
            for sitemap_loc in sitemap_locations:
                child_sitemap_url = sitemap_loc.text
                
                # Skip non-product sitemaps
                if not any(kw in child_sitemap_url.lower() for kw in ["product", "store", "shop", "catalog"]):
                    continue
                
                try:
                    logger.info(f"Processing child sitemap: {child_sitemap_url}")
                    
                    # Check cache first
                    child_sitemap_url_normalized = normalize_url(child_sitemap_url)
                    cache_key = f"sitemap_{get_domain_from_url(base_url)}_{child_sitemap_url.split('/')[-1]}"
                    cached_data = get_cached_html(cache_key)
                    
                    if cached_data:
                        child_xml = cached_data
                    else:
                        child_xml = await fetch_with_retry(child_sitemap_url_normalized, client)
                        cache_html(cache_key, child_xml)
                    
                    child_products = await parse_sitemap(child_xml, base_url, client)
                    product_urls.extend(child_products)
                
                except Exception as e:
                    logger.warning(f"Failed to parse child sitemap {child_sitemap_url}: {e}")
                    continue
        
        else:
            # This is a regular sitemap, extract URLs directly
            for url_element in root.findall('.//ns:url', ns):
                loc_element = url_element.find('./ns:loc', ns)
                
                if loc_element is None:
                    continue
                    
                url = loc_element.text
                
                # Skip if not a product URL
                if not any(kw in url.lower() for kw in ["/product/", "/products/", "/coffee/", "/shop/", "/p/"]):
                    continue
                
                # Try to extract title from image tag
                title = ""
                image_title = url_element.find('./image:image/image:title', ns)
                
                if image_title is not None:
                    title = image_title.text.strip()
                else:
                    # Extract title from URL if not found in image tag
                    title = url.split("/")[-1].replace("-", " ").title()
                
                # Check if likely a coffee product based on title keywords
                if any(kw in title.lower() for kw in ["coffee", "brew", "kaapi", "beans", "roast", "arabica", "blend"]):
                    product_urls.append((url, title))
    
    except Exception as e:
        logger.error(f"Error parsing sitemap: {e}")
    
    return product_urls

async def scrape_product_catalog_pages(base_url: str, roaster: Dict[str, Any], client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    """Fallback: Scrape product catalog pages when no sitemap is found.
    
    Args:
        base_url: Base URL of the site
        roaster: Roaster data dictionary
        client: HTTPX client
        
    Returns:
        List of coffee product dictionaries
    """
    coffee_products = []
    catalog_urls = [
        f"{base_url}/shop",
        f"{base_url}/products",
        f"{base_url}/coffee",
        f"{base_url}/collections/coffee",
        f"{base_url}/product-category/coffee",
        f"{base_url}/store"
    ]
    
    for url in catalog_urls:
        try:
            logger.info(f"Trying catalog page: {url}")
            html = await fetch_with_retry(url, client)
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for product links
            product_links = []
            
            # Strategy 1: Look for product grid
            product_grid = soup.find('div', class_=lambda c: c and any(x in c for x in ['products-grid', 'product-list', 'products-list']))
            if product_grid:
                for link in product_grid.find_all('a', href=True):
                    href = link.get('href')
                    if '/product/' in href or '/products/' in href:
                        product_links.append((href, link.get_text().strip()))
            
            # Strategy 2: Look for product cards
            if not product_links:
                product_cards = soup.find_all('div', class_=lambda c: c and any(x in c for x in ['product-card', 'product-item']))
                for card in product_cards:
                    link = card.find('a', href=True)
                    if link:
                        href = link.get('href')
                        title_elem = card.find(['h2', 'h3', 'h4']) or link
                        title = title_elem.get_text().strip()
                        product_links.append((href, title))
            
            # Strategy 3: Find all links with product in URL
            if not product_links:
                for link in soup.find_all('a', href=True):
                    href = link.get('href')
                    if '/product/' in href or '/products/' in href:
                        title = link.get_text().strip()
                        if title:
                            product_links.append((href, title))
            
            if not product_links:
                logger.warning(f"No product links found on {url}")
                continue
            
            logger.info(f"Found {len(product_links)} product links on {url}")
            
            # Process links (limit to 20 to be reasonable)
            for href, title in product_links[:20]:
                # Ensure absolute URL
                if not href.startswith('http'):
                    href = urljoin(base_url, href)
                
                href_normalized = normalize_url(href)
                try:
                    logger.info(f"Fetching product: {href_normalized}")
                    html = await fetch_with_retry(href_normalized, client)
                    
                    # Extract product data from HTML
                    coffee = await extract_product_from_html(html, href, title, roaster)
                    if coffee:
                        coffee_products.append(coffee)
                except Exception as e:
                    logger.error(f"Error processing product {href}: {e}")
                    continue
            
            # If we found some products, return them
            if coffee_products:
                return coffee_products
        
        except Exception as e:
            logger.warning(f"Error scraping catalog {url}: {e}")
            continue
    
    return coffee_products

async def extract_product_from_html(html: str, url: str, title: str, roaster: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract product data from HTML.
    
    Args:
        html: Product page HTML
        url: Product URL
        title: Product title
        roaster: Roaster data dictionary
        
    Returns:
        Coffee product dictionary or None if not a coffee product
    """
    # Use BeautifulSoup for more reliable parsing
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extract or use provided title
    if not title:
        title_elem = soup.find('h1')
        if title_elem:
            title = title_elem.get_text().strip()
        else:
            # Fallback to page title
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip().split('|')[0].strip()
            else:
                # Last resort: extract from URL
                title = url.split('/')[-1].replace('-', ' ').title()
    
    # Extract description
    description = ""
    
    # Try meta description first
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        description = meta_desc.get('content')
    
    # Try product description div
    if not description:
        desc_div = soup.find('div', class_=lambda c: c and any(x in c for x in ['product-description', 'description', 'product-details']))
        if desc_div:
            description = desc_div.get_text().strip()
    
    # Clean description
    description = clean_html(description)
    
    # Skip non-coffee products
    if not is_coffee_product(title, description, "", [], roaster['name'], url):
        logger.debug(f"Skipping non-coffee product: {title}")
        return None
    
    # Create base coffee object
    coffee = {
        "name": title,
        "slug": create_slug(title),
        "roaster_id": roaster.get('id'),
        "roaster_slug": roaster.get('slug'),
        "description": description,
        "direct_buy_url": url,
        "is_available": True,  # Default to available
        "last_scraped_at": datetime.now().isoformat(),
        "scrape_status": "success"
    }
    
    # Extract image URL
    img_url = None
    
    # Try og:image first
    og_image = soup.find('meta', property='og:image')
    if og_image and og_image.get('content'):
        img_url = og_image.get('content')
    
    # Try product image tag
    if not img_url:
        main_image = soup.find('img', class_=lambda c: c and any(x in c for x in ['product-image', 'main-image']))
        if main_image and main_image.get('src'):
            img_url = main_image.get('src')
    
    # Try first image in product container
    if not img_url:
        product_div = soup.find('div', class_=lambda c: c and any(x in c for x in ['product', 'product-container']))
        if product_div:
            img = product_div.find('img')
            if img and img.get('src'):
                img_url = img.get('src')
    
    # Ensure absolute URL for image
    if img_url and not img_url.startswith(('http://', 'https://')):
        img_url = urljoin(url, img_url)
    
    if img_url:
        coffee["image_url"] = img_url
    
    # Extract price
    extract_price_from_html(coffee, str(soup))
    
    # Extract attributes
    tags = []
    tag_elems = soup.find_all(['span', 'a'], class_=lambda c: c and 'tag' in c)
    for tag in tag_elems:
        tags.append(tag.get_text().strip())
    
    coffee = extract_all_attributes(
        coffee=coffee,
        text=description,
        tags=tags,
        name=title
    )
    
    # Run validation and corrections
    validation_results = validate_coffee_product(coffee)
    coffee = apply_validation_corrections(coffee, validation_results)
    
    # Standardize model before returning
    return standardize_coffee_model(coffee)

async def scrape_single_product(url: str, roaster: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Scrape a single product by URL.
    
    Args:
        url: Product URL
        roaster: Roaster data dictionary
        
    Returns:
        Coffee product dictionary or None if not a coffee product
    """
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        try:
            logger.info(f"Fetching product: {url}")
            response = await fetch_with_retry(url, client=client)
            html = response.text
            
            # Extract title from URL as fallback
            title = url.split('/')[-1].replace('-', ' ').title()
            
            return await extract_product_from_html(html, url, title, roaster)
            
        except Exception as e:
            logger.error(f"Error scraping product {url}: {e}")
            return None
