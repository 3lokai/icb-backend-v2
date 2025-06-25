# Product Scraper Module
# =====================
# File: scrapers/product_crawl4ai/scraper.py

import logging
from typing import List, Optional, Dict, Any, Union

from common.utils import is_coffee_product
from common.platform_detector import PlatformDetector
from common.cache import cache_products, get_cached_products
from db.models import Coffee
from common.pydantic_utils import dict_to_pydantic_model, preprocess_coffee_data

# Import extractors
from .api_extractors.shopify import extract_products_shopify
from .api_extractors.woocommerce import extract_products_woocommerce
from .discovery.deep_crawler import discover_products_via_crawl4ai
from .enrichment.llm_extractor import enrich_coffee_product
from .validators.coffee import validate_enriched_product

logger = logging.getLogger(__name__)

def model_to_dict(obj: Any) -> Dict[str, Any]:
    """Convert a Pydantic model to a dictionary if needed."""
    if hasattr(obj, "model_dump"):  # Pydantic v2
        return obj.model_dump()
    elif hasattr(obj, "dict"):      # Pydantic v1
        return obj.dict()
    else:
        return obj  # Already a dict or similar

class ProductScraper:
    """
    Main orchestrator for coffee product scraping.
    Coordinates platform detection, API-first approach, deep crawling fallback,
    and product enrichment.
    """
    
    def __init__(self):
        self.platform_detector = PlatformDetector()
        
    async def scrape_products(self, roaster_id: str, url: str, roaster_name: str, force_refresh: bool = False, use_enrichment: bool = True) -> List[Coffee]:
        """
        Main entry point for product scraping.
        
        Args:
            roaster_id: Database ID of the roaster
            url: Base URL of the roaster's website
            roaster_name: Name of the roaster (for logging and validation)
            force_refresh: If True, bypass cache and re-scrape
            use_enrichment: If True, use LLM enrichment
            
        Returns:
            List of Coffee model instances that were scraped
        """
        logger.info(f"Starting product scraping for {roaster_name} ({url}) with force_refresh={force_refresh}, use_enrichment={use_enrichment}")
        if not force_refresh:
            cached_products = get_cached_products(roaster_id, max_age_days=7)
            if cached_products:
                logger.info(f"Using {len(cached_products)} cached products for {roaster_name}")
                return [dict_to_pydantic_model(p, Coffee, preprocessor=preprocess_coffee_data) 
                        for p in cached_products if p]
        else:
            logger.info(f"Force refresh enabled for {roaster_name}. Bypassing cache read.")
        
        # 1. Detect platform
        platform, confidence = await self.platform_detector.detect(url)
        logger.info(f"Detected platform: {platform} (confidence: {confidence}%)")
        
        # 2. API-first approach for known platforms
        products = []
        if platform == "shopify" and confidence >= 70:
            logger.info(f"Using Shopify API extractor for {roaster_name}")
            products = await extract_products_shopify(url, roaster_id)
        elif platform == "woocommerce" and confidence >= 70:
            logger.info(f"Using WooCommerce API extractor for {roaster_name}")
            products = await extract_products_woocommerce(url, roaster_id)
        
        # 3. Fallback to deep crawling for unknown platforms or if API extraction failed
        if not products:
            logger.info(f"Fallback to deep crawling for {roaster_name} (platform: {platform})")
            products = await discover_products_via_crawl4ai(url, roaster_id, roaster_name)
        
        # 4. Perform enrichment for each product
        coffee_models = []
        for product in products:
            # Convert to dict if it's a model
            product_dict = model_to_dict(product)
            
            # Skip non-coffee products at this stage
            if not is_coffee_product(
                product_dict.get('name', ''), 
                product_dict.get('description', ''),
                product_dict.get('product_type', None),
                product_dict.get('tags', None),
                roaster_name,
                product_dict.get('direct_buy_url', '')
            ):
                logger.debug(f"Skipping non-coffee product: {product_dict.get('name', 'Unknown')}")
                continue
                
            # Enrich product with missing data
            if use_enrichment:
                enriched_product_data = await enrich_coffee_product(product_dict, roaster_name)
            else:
                logger.info(f"Skipping LLM enrichment for product {product_dict.get('name', 'Unknown')} from {roaster_name} as per 'use_enrichment=False'.")
                enriched_product_data = product_dict # Use the product_dict directly if not enriching
            
            # Validate enriched product (phase 2)
            # The validator should be able to handle data that hasn't been through LLM enrichment
            if validate_enriched_product(enriched_product_data): 
                coffee_model = dict_to_pydantic_model(
                    enriched_product_data, 
                    Coffee, 
                    preprocessor=preprocess_coffee_data
                )
                if coffee_model:
                    coffee_models.append(coffee_model)
        
        # 5. Cache products
        if coffee_models:
            cache_products(roaster_id, [model_to_dict(c) for c in coffee_models])
            
        logger.info(f"Completed scraping for {roaster_name}. Found {len(coffee_models)} coffee products.")
        return coffee_models
        
    async def scrape_single_product(self, product_url: str, roaster_id: str, roaster_name: str) -> Optional[Coffee]:
        """
        Scrape a single product page directly.
        
        Args:
            product_url: URL of the product page
            roaster_id: Database ID of the roaster
            roaster_name: Name of the roaster
            
        Returns:
            Coffee model instance if successful, None otherwise
        """
        # Extract basic product data
        product = {}
        
        # Determine platform
        domain = product_url.split('/')[2]
        base_url = f"https://{domain}"
        platform, _ = await self.platform_detector.detect(base_url)
        
        # Use platform-specific extraction if possible
        if platform == "shopify":
            # Extract product handle from URL
            product_handle = product_url.split('/')[-1]
            if '?' in product_handle:
                product_handle = product_handle.split('?')[0]
            products = await extract_products_shopify(base_url, roaster_id, product_handle=product_handle)
            if products:
                product = products[0]
        elif platform == "woocommerce":
            # Extract product ID from URL (if possible)
            product_id = None
            if 'product=' in product_url:
                product_id = product_url.split('product=')[1].split('&')[0]
            products = await extract_products_woocommerce(base_url, roaster_id, product_id=product_id)
            if products:
                product = products[0]
        
        # If platform-specific extraction failed, use general approach
        if not product:
            # Use Crawl4AI to extract the product
            from .enrichment.llm_extractor import extract_product_page
            product = await extract_product_page(product_url, roaster_id)
        
        # Convert to dict if it's a model
        product_dict = model_to_dict(product)
        
        # Skip if not a coffee product
        if not product_dict or not is_coffee_product(
            product_dict.get('name', ''),
            product_dict.get('description', ''),
            product_dict.get('product_type', None),
            product_dict.get('tags', None),
            roaster_name,
            product_dict.get('direct_buy_url', '')
        ):
            logger.info(f"Not a coffee product: {product_url}")
            return None
            
        # Enrich and validate
        enriched_product = await enrich_coffee_product(product_dict, roaster_name)
        if validate_enriched_product(enriched_product):
            return dict_to_pydantic_model(
                enriched_product,
                Coffee,
                preprocessor=preprocess_coffee_data
            )
            
        return None