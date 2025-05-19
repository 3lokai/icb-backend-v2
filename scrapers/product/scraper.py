# scrapers/product/scraper.py
"""
Main orchestrator for coffee product scraping.
Coordinates platform-specific scrapers and manages the scraping process.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
import json
from datetime import datetime
from pathlib import Path
from common.exporter import export_to_json

from common.platform_detector import detect_platform
from common.cache import get_cached_products, cache_products
from config import config

# Import platform-specific scrapers
from db.models import Coffee, CoffeePrice, ExternalLink
from scrapers.product.shopify import scrape_shopify, scrape_single_product as scrape_shopify_product
from  scrapers.product.woocommerce import scrape_woocommerce, scrape_single_product as scrape_woocommerce_product
from  scrapers.product.static import scrape_static_site, scrape_single_product as scrape_static_product

# Import validation and enrichment
from scrapers.product.extractors.validators import validate_coffee_product, apply_validation_corrections
from scrapers.product.extractors.normalizers import standardize_coffee_model
from scrapers.product.enrichment.deepseek import enhance_with_deepseek, batch_enhance_coffees, needs_enhancement

logger = logging.getLogger(__name__)

class ProductScraper:
    """Orchestrates coffee product scraping across different platforms."""
    
    def __init__(self, force_refresh=False, use_enrichment=True, confidence_tracking=True):
        """Initialize product scraper.
        
        Args:
            force_refresh: Whether to bypass cache
            use_enrichment: Whether to use LLM enrichment for missing fields
            confidence_tracking: Whether to track confidence scores
        """
        self.force_refresh = force_refresh
        self.use_enrichment = use_enrichment
        self.confidence_tracking = confidence_tracking
        
    async def scrape_roaster_products(self, roaster: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scrape products for a single roaster based on platform.
        
        Args:
            roaster: Roaster data dictionary
            
        Returns:
            List of coffee product dictionaries
        """
        logger.info(f"Scraping products for {roaster['name']}")
        
        # Check cache first if not forcing refresh
        if not self.force_refresh:
            cached = get_cached_products(roaster['id'] if 'id' in roaster else roaster['slug'])
            if cached:
                logger.info(f"Using {len(cached)} cached products for {roaster['name']}")
                return cached
        
        # Determine platform, detect if not already provided
        platform = roaster.get('platform', '').lower()
        if not platform or platform == 'unknown':
            logger.info(f"Detecting platform for {roaster['name']} at {roaster['website_url']}")
            platform = await detect_platform(roaster['website_url'])
            logger.info(f"Detected platform: {platform}")
        
        try:
            # Select appropriate scraper based on platform
            if 'shopify' in platform:
                raw_products = await scrape_shopify(roaster)
            elif 'woocommerce' in platform or 'wordpress' in platform:
                raw_products = await scrape_woocommerce(roaster)
            else:
                # Default to generic static site scraper
                raw_products = await scrape_static_site(roaster)
            
            # Process and standardize products
            processed_products = await self._process_products(raw_products, roaster)
            
            # Cache results
            if processed_products:
                cache_products(roaster['id'] if 'id' in roaster else roaster['slug'], processed_products)
                
            logger.info(f"Scraped {len(processed_products)} products for {roaster['name']}")
            return processed_products
            
        except Exception as e:
            logger.error(f"Error scraping products for {roaster['name']}: {e}", exc_info=True)
            return []
    
    async def _process_products(self, products: List[Dict[str, Any]], roaster: Dict[str, Any]) -> List[Coffee]:
        """Process raw product data to standardize and enhance.
        
        Args:
            products: Raw product data from platform-specific scraper
            roaster: Roaster data dictionary
            
        Returns:
            List of processed and standardized coffee products
        """
        if not products:
            return []
        
        processed_coffee_models = []
        products_to_enhance = []
        
        # First pass: standardize and validate
        for product in products:
            # Add roaster information
            product['roaster_id'] = roaster.get('id')
            product['roaster_slug'] = roaster.get('slug')
            
            # Standardize model
            standardized = standardize_coffee_model(product)
            
            # Validate fields
            validation_results = validate_coffee_product(standardized)
            standardized = apply_validation_corrections(standardized, validation_results)
            
            # Check if needs enrichment
            if self.use_enrichment and needs_enhancement(standardized):
                products_to_enhance.append(standardized)
            else:
                # Convert dict to model
                coffee_model = self.dict_to_coffee_model(standardized)
                processed_coffee_models.append(coffee_model)
        
        # Second pass: batch enhance products if needed
        if self.use_enrichment and products_to_enhance:
            logger.info(f"Enhancing {len(products_to_enhance)} products for {roaster['name']}")
            enhanced = await batch_enhance_coffees(products_to_enhance, roaster['name'])
            # Convert enhanced dicts to models
            for product in enhanced:
                coffee_model = self.dict_to_coffee_model(product)
                processed_coffee_models.append(coffee_model)
        
        return processed_coffee_models
    
    def dict_to_coffee_model(self, coffee_dict: Dict[str, Any]) -> Coffee:
        """Convert a standardized coffee dict to a Coffee model instance."""
        # Handle nested lists (prices, external_links)
        prices = []
        if 'prices' in coffee_dict and isinstance(coffee_dict['prices'], list):
            for price_dict in coffee_dict['prices']:
                try:
                    prices.append(CoffeePrice(**price_dict))
                except Exception as e:
                    logger.error(f"Error creating CoffeePrice model: {e}")
        
        external_links = []
        if 'external_links' in coffee_dict and isinstance(coffee_dict['external_links'], list):
            for link_dict in coffee_dict['external_links']:
                try:
                    external_links.append(ExternalLink(**link_dict))
                except Exception as e:
                    logger.error(f"Error creating ExternalLink model: {e}")
        
        # Make a copy to avoid modifying the original
        coffee_data = coffee_dict.copy()
        
        # Replace nested lists with model instances
        if prices:
            coffee_data['prices'] = prices
        if external_links:
            coffee_data['external_links'] = external_links
        
        # Create Coffee model
        try:
            return Coffee(**coffee_data)
        except Exception as e:
            logger.error(f"Error creating Coffee model: {e}")
            # Remove problematic fields and try again
            for field in ['confidence_scores', 'price_inconsistencies', 'is_multipack', 'pack_count']:
                if field in coffee_data:
                    del coffee_data[field]
            return Coffee(**coffee_data)
    
    async def scrape_all_roasters(self, roasters: List[Dict[str, Any]]) -> Dict[str, List[Coffee]]:
        """Scrape products for multiple roasters.
        
        Args:
            roasters: List of roaster data dictionaries
            
        Returns:
            Dictionary mapping roaster slugs to lists of coffee products
        """
        results = {}
        for roaster in roasters:
            products = await self.scrape_roaster_products(roaster)
            results[roaster.get('slug', '')] = [self.dict_to_coffee_model(p) for p in products]
        return results
    
    async def scrape_to_file(self, roasters: List[Dict[str, Any]], output_file: str) -> Tuple[int, int]:
        """Scrape products and save to a file.
        
        Args:
            roasters: List of roaster data dictionaries
            output_file: Path to save output JSON
            
        Returns:
            Tuple of (total products, total roasters)
        """
        # Create output directory if it doesn't exist
        output_path = Path(output_file)
        output_path.parent.mkdir(exist_ok=True, parents=True)
        
        all_products = []
        successful_roasters = 0
        
        for roaster in roasters:
            try:
                products = await self.scrape_roaster_products(roaster)
                if products:
                    all_products.extend(products)
                    successful_roasters += 1
            except Exception as e:
                logger.error(f"Error scraping {roaster['name']}: {e}", exc_info=True)
       
        # Convert Coffee models to dictionaries for JSON serialization
        serialized_products = []
        for coffee in all_products:
            # Check if it's a Coffee model
            if hasattr(coffee, 'model_dump'):
                # Pydantic v2
                serialized_products.append(coffee.model_dump())
            elif hasattr(coffee, 'dict'):
                # Pydantic v1
                serialized_products.append(coffee.dict())
            else:
                # Already a dict
                serialized_products.append(coffee)

        # Save to file using standardized export utility
        export_to_json(serialized_products, str(output_path), indent=2)
        
        logger.info(f"Saved {len(all_products)} products from {successful_roasters} roasters to {output_file}")
        return len(all_products), successful_roasters
    
    async def scrape_single_url(self, url: str, roaster_name: str = "Unknown") -> Optional[Coffee]:
        """Scrape a single product URL directly.
        
        Args:
            url: Product URL to scrape
            roaster_name: Name of the roaster (for enrichment context)
            
        Returns:
            Coffee product dictionary or None if scraping fails
        """
        logger.info(f"Scraping single product: {url}")
        
        # Create minimal roaster dict for context
        roaster = {
            'name': roaster_name,
            'slug': roaster_name.lower().replace(' ', '-'),
            'website_url': '/'.join(url.split('/')[:3])  # Extract base URL
        }
        
        # Detect platform
        platform = await detect_platform(roaster['website_url'])
        logger.info(f"Detected platform: {platform}")
        
        try:
            # Select scraper based on platform
            if 'shopify' in platform:
                product = await scrape_shopify_product(url, roaster)
            elif 'woocommerce' in platform or 'wordpress' in platform:
                product = await scrape_woocommerce_product(url, roaster)
            else:
                product = await scrape_static_product(url, roaster)
            
            if not product:
                logger.warning(f"No product found at {url}")
                return None
            
            # Process the product
            product['roaster_slug'] = roaster['slug']
            
            # Standardize model
            standardized = standardize_coffee_model(product)
            
            # Validate fields
            validation_results = validate_coffee_product(standardized)
            standardized = apply_validation_corrections(standardized, validation_results)
            
            # Enhance if needed
            if self.use_enrichment and needs_enhancement(standardized):
                standardized = await enhance_with_deepseek(standardized, roaster_name)
            
            return self.dict_to_coffee_model(standardized)
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}", exc_info=True)
            return None
    
    def analyze_field_coverage(self, products: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Analyze field coverage and confidence across products.
        
        Args:
            products: List of coffee product dictionaries
            
        Returns:
            Dictionary with field coverage statistics
        """
        if not products:
            return {}
        
        # Fields to analyze
        key_fields = [
            'name', 'roast_level', 'bean_type', 'processing_method', 
            'price_250g', 'image_url', 'is_single_origin', 'flavor_profiles'
        ]
        
        stats = {}
        for field in key_fields:
            field_stats = {
                'count': 0,
                'percent': 0,
                'avg_confidence': 0,
                'unknown_count': 0
            }
            
            confidence_sum = 0
            unknown_values = 0
            
            for product in products:
                # Handle both model objects and dictionaries
                if hasattr(product, field):
                    # It's a model object
                    value = getattr(product, field)
                    if value is not None:
                        field_stats['count'] += 1
                        
                        # Check if the value is "unknown"
                        if isinstance(value, str) and value.lower() == 'unknown':
                            unknown_values += 1
                elif isinstance(product, dict) and field in product and product[field] is not None:
                    # It's a dictionary
                    field_stats['count'] += 1
                    
                    # Check if the value is "unknown"
                    if isinstance(product[field], str) and product[field].lower() == 'unknown':
                        unknown_values += 1
                    
                    # Get confidence if available
                    if 'confidence_scores' in product and field in product['confidence_scores']:
                        confidence_sum += float(product['confidence_scores'][field])
                
            # Calculate percentages
            field_stats['percent'] = round((field_stats['count'] / len(products)) * 100, 1)
            
            # Calculate average confidence
            if field_stats['count'] > 0:
                field_stats['avg_confidence'] = round(confidence_sum / field_stats['count'], 2)
            
            field_stats['unknown_count'] = unknown_values
            stats[field] = field_stats
        
        return stats
    
    def get_field_source_stats(self, products: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
        """Analyze field extraction sources across products.
        
        Args:
            products: List of coffee product dictionaries
            
        Returns:
            Dictionary with field source statistics
        """
        if not products:
            return {}
        
        # Fields to analyze
        key_fields = [
            'roast_level', 'bean_type', 'processing_method', 'flavor_profiles'
        ]
        
        stats = {}
        for field in key_fields:
            source_counts = {
                'from_tags': 0,
                'from_description': 0,
                'from_structured_data': 0,
                'from_llm': 0,
                'unknown': 0
            }
            
            for product in products:
                # Check field source if available
                source_field = f"{field}_source"
                
                if hasattr(product, field):
                    # It's a model object
                    if hasattr(product, source_field):
                        source = getattr(product, source_field)
                        if source in source_counts:
                            source_counts[source] += 1
                        else:
                            source_counts['unknown'] += 1
                    elif getattr(product, field) is not None:
                        # No source information, but field exists
                        # Check if it has high confidence (likely from structured data)
                        if hasattr(product, 'confidence_scores') and field in product.confidence_scores:
                            confidence = float(product.confidence_scores[field])
                            if confidence >= 0.9:
                                source_counts['from_structured_data'] += 1
                            elif confidence >= 0.75:
                                source_counts['from_tags'] += 1
                            elif confidence >= 0.6:
                                source_counts['from_description'] += 1
                            elif confidence >= 0.4:
                                source_counts['from_llm'] += 1
                            else:
                                source_counts['unknown'] += 1
                        else:
                            source_counts['unknown'] += 1
                elif isinstance(product, dict):
                    # It's a dictionary
                    if source_field in product:
                        source = product[source_field]
                        if source in source_counts:
                            source_counts[source] += 1
                        else:
                            source_counts['unknown'] += 1
                    elif field in product and product[field] is not None:
                        # No source information, but field exists
                        # Check if it has high confidence (likely from structured data)
                        if 'confidence_scores' in product and field in product['confidence_scores']:
                            confidence = float(product['confidence_scores'][field])
                            if confidence >= 0.9:
                                source_counts['from_structured_data'] += 1
                            elif confidence >= 0.75:
                                source_counts['from_tags'] += 1
                            elif confidence >= 0.6:
                                source_counts['from_description'] += 1
                            elif confidence >= 0.4:
                                source_counts['from_llm'] += 1
                            else:
                                source_counts['unknown'] += 1
                        else:
                            source_counts['unknown'] += 1
            
            stats[field] = source_counts
        
        return stats
