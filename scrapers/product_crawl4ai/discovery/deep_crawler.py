# Deep Crawler for Product Discovery
# =================================
# File: scrapers/product_crawl4ai/discovery/deep_crawler.py

import logging
import re
from typing import Any, Dict, List
from urllib.parse import urlparse

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.filters import DomainFilter, FilterChain, URLPatternFilter
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from common.utils import is_coffee_product

from ..enrichment.llm_extractor import extract_product_page
from ..validators.coffee import validate_product_at_discovery

logger = logging.getLogger(__name__)


async def discover_products_via_crawl4ai(
    base_url: str, roaster_id: str, roaster_name: str, max_products: int = 50
) -> List[Dict[str, Any]]:
    """
    Use Crawl4AI's deep crawling capabilities to discover coffee product pages for static sites
    or unknown platforms.

    Args:
        base_url: Base URL of the roaster's website
        roaster_id: Database ID of the roaster
        roaster_name: Name of the roaster (for logging and validation)
        max_products: Maximum number of products to discover

    Returns:
        List of product dictionaries with standardized fields
    """
    logger.info(f"Starting deep crawler product discovery for {roaster_name} at {base_url}")

    # Extract domain for filtering
    domain = urlparse(base_url).netloc

    # Create URL filters to focus on product pages
    url_filters = FilterChain(
        [
            # Focus specifically on coffee product pages
            URLPatternFilter(
                patterns=[
                    # Coffee-specific URL patterns
                    "*/coffee/*",
                    "*/coffees/*",
                    "*/beans/*",
                    "*coffee*.html",
                    "*/single-origin/*",
                    "*/blend/*",
                    "*/roast/*",
                    "*/arabica/*",
                    # Product detail patterns (avoiding category pages)
                    "*-coffee.html",
                    "*-blend.html",
                    "*-beans.html",
                    "*-roast.html",
                    # Known product naming patterns
                    "*estate*",
                    "*origin*",
                    "*filter*-coffee*",
                    # Avoid category and utility pages
                    "!*/category/*",
                    "!*/product-category/*",
                    "!*/collection/*",
                    "!*/cart*",
                    "!*/checkout*",
                    "!*/account*",
                    "!*/login*",
                    "!*/contact*",
                    "!*/about*",
                    "!*/blog*",
                    "!*/search*",
                    "!*?p=*",
                    "!*?page=*",
                    "!*?sort=*",
                ]
            ),
            # Stay within the same domain
            DomainFilter(allowed_domains=[domain]),
        ]
    )

    # Create URL scorer to prioritize likely product pages
    url_scorer = KeywordRelevanceScorer(
        keywords=[
            "coffee",
            "bean",
            "roast",
            "arabica",
            "robusta",
            "espresso",
            "product",
            "single origin",
            "blend",
            "light",
            "medium",
            "dark",
            "buy",
            "purchase",
            # Additional scoring keywords
            "detail",
            "view",
            "item",
            "filter",
            "specialty",
            "brewing",
        ],
        weight=0.8,
    )

    # Configure deep crawling strategy
    deep_strategy = BestFirstCrawlingStrategy(
        max_depth=3,
        include_external=False,
        filter_chain=url_filters,
        url_scorer=url_scorer,
        max_pages=150,  # Limit to prevent overly long crawls
    )

    # Configure content filter for effective extraction
    content_filter = PruningContentFilter(threshold=0.35, threshold_type="dynamic", min_word_threshold=5)
    md_generator = DefaultMarkdownGenerator(content_filter=content_filter)
    # Create crawler configuration
    config = CrawlerRunConfig(
        deep_crawl_strategy=deep_strategy,
        markdown_generator=md_generator,
        cache_mode=CacheMode.ENABLED,
        stream=True,  # Must be True for async iteration
    )

    # Store product URLs for subsequent extraction
    product_urls = []

    # Run the deep crawler
    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        try:
            results: Any = await crawler.arun(url=base_url, config=config)
            for result in results:
                if not result or not result.success:
                    continue
                # Check if this appears to be a product page
                if is_product_page(result.url, result.html, result.markdown):
                    # Try to extract a product name for validation
                    product_name = ""
                    title_match = re.search(r"<h1[^>]*>([^<]+)</h1>", result.html) or re.search(
                        r"<title>([^<|]+)", result.html
                    )
                    if title_match:
                        product_name = title_match.group(1).strip()
                    # Extract description
                    description = ""
                    desc_match = re.search(
                        r'<meta\s+name=["|\']description["|\'][^>]*content=["|\']([^"\']+)["|\']', result.html
                    )
                    if desc_match:
                        description = desc_match.group(1).strip()
                    # Only add if it passes coffee validation
                    if validate_product_at_discovery(
                        name=product_name, description=description, roaster_name=roaster_name, url=result.url
                    ):
                        product_urls.append(result.url)
                        logger.debug(f"Found coffee product URL: {result.url}")
                        # Limit the number of products to process
                        if len(product_urls) >= max_products:
                            logger.info(f"Reached maximum product limit ({max_products})")
                            break
                    else:
                        logger.debug(f"Found product URL but not coffee: {result.url}")
        except Exception as e:
            logger.error(f"Error during deep crawling: {e}")

    logger.info(f"Discovered {len(product_urls)} potential product URLs")

    # Extract detailed product data from each URL
    products = []
    for url in product_urls:
        try:
            product = await extract_product_page(url, roaster_id)

            # Skip if extraction failed
            if not product:
                continue

            # Skip if not a coffee product
            if not is_coffee_product(
                product.get("name", ""),
                product.get("description", ""),
                product.get("product_type", None),
                product.get("tags", None),
                roaster_name,
                url,
            ):
                continue

            # Add source URL
            product["direct_buy_url"] = url

            # Debug: Verify URL was set correctly
            if not product.get("direct_buy_url"):
                logger.error(f"Failed to set direct_buy_url for product: {product.get('name', 'Unknown')}")
                continue

            # Add to products list
            products.append(product)
            logger.debug(f"Extracted product: {product.get('name', 'Unknown')} with URL: {product.get('direct_buy_url')}")

        except Exception as e:
            logger.error(f"Error extracting product data from {url}: {e}")

    logger.info(f"Successfully extracted {len(products)} coffee products")
    return products


# Precompile regex patterns for better performance
PRODUCT_SCHEMA_PATTERN = re.compile(r'itemtype=[\'"](http:|https:)?//schema.org/Product[\'"]')
PRICE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE) for pattern in [
        r'<[^>]*class="[^"]*price[^"]*"',
        r'<[^>]*itemprop="price"',
        r"[$€₹]\s*\d+\.?\d*",
        r'price"?:\s*["\']\d+',
        r"data-product-price",
    ]
]
CART_PATTERNS = [
    re.compile(pattern, re.IGNORECASE) for pattern in [
        r"add[_ -]to[_ -]cart",
        r"add[_ -]to[_ -]bag",
        r"buy[_ -]now",
        r"purchase",
        r"checkout"
    ]
]
DETAIL_PATTERNS = [
    re.compile(pattern, re.IGNORECASE) for pattern in [
        r'<[^>]*id="[^"]*product[_ -]detail',
        r'<[^>]*class="[^"]*product[_ -]detail',
        r'<[^>]*class="[^"]*product[_ -]info',
        r'<[^>]*id="[^"]*product[_ -]description',
        r'<[^>]*class="[^"]*product[_ -]image',
    ]
]
OPTION_PATTERNS = [
    re.compile(pattern, re.IGNORECASE | re.DOTALL) for pattern in [
        r"<select[^>]*>.*?</select>",
        r'<input[^>]*type=["|\']radio["|\'][^>]*>'
    ]
]
COFFEE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE) for pattern in [
        r"roast level",
        r"origin",
        r"bean type",
        r"single origin",
        r"tasting notes",
        r"flavor notes",
        r"processing method",
        r"arabica",
        r"robusta",
        r"altitude",
        r"brewing",
    ]
]
URL_PATTERNS = [
    re.compile(pattern, re.IGNORECASE) for pattern in [
        r"/product/",
        r"/products/",
        r"/coffee/",
        r"/coffees/",
        r"/beans/",
        r"/p/[^/]+$",
        r"\.html$",
        r"/item/",
        r"/buy/",
    ]
]
TITLE_PATTERN = re.compile(r"<h1[^>]*>([^<]+)</h1>")
ALT_TITLE_PATTERN = re.compile(r"<title>([^<|]+)")
DESC_PATTERN = re.compile(r'<meta\s+name=["|\']description["|\'][^>]*content=["|\']([^"\']+)["|\'"]')

def is_product_page(url: str, html: str, markdown: str) -> bool:
    """
    More robust general-purpose product page detection that works across platforms.
    Effectively identifies product pages regardless of URL structure.
    """
    product_indicators = 0

    # 1. Check for product schema markup (very reliable)
    if PRODUCT_SCHEMA_PATTERN.search(html):
        product_indicators += 2

    # 2. Check for pricing patterns
    if any(pattern.search(html) for pattern in PRICE_PATTERNS):
        product_indicators += 1

    # 3. Check for "Add to cart" or similar buttons
    if any(pattern.search(html) for pattern in CART_PATTERNS):
        product_indicators += 1

    # 4. Check for product detail elements
    if any(pattern.search(html) for pattern in DETAIL_PATTERNS):
        product_indicators += 1

    # 5. Check for product options (variants, sizes, etc.)
    if any(pattern.search(html) for pattern in OPTION_PATTERNS):
        product_indicators += 1

    # 6. Check for coffee-specific indicators
    coffee_matches = sum(1 for pattern in COFFEE_PATTERNS if pattern.search(html))
    if coffee_matches >= 2:
        product_indicators += 1

    # 7. Look for product structure in URL
    if any(pattern.search(url) for pattern in URL_PATTERNS):
        product_indicators += 1

    # Consider it a product page if multiple indicators are found
    if product_indicators < 3:
        return False

    # Extract product name from title or h1
    title_match = TITLE_PATTERN.search(html) or ALT_TITLE_PATTERN.search(html)
    if not title_match:
        return False
    
    product_name = title_match.group(1).strip()
    
    # Extract description
    description = ""
    desc_match = DESC_PATTERN.search(html)
    if desc_match:
        description = desc_match.group(1).strip()

    # Validate as coffee product
    return validate_product_at_discovery(name=product_name, description=description, url=url)
