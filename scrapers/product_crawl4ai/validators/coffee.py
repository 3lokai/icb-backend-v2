# Coffee Product Validator
# =======================
# File: scrapers/product_crawl4ai/validators/coffee.py

import re
import logging
from typing import Dict, Any, Optional

from common.utils import is_coffee_product

logger = logging.getLogger(__name__)

def validate_product_at_discovery(name: str, description: Optional[str] = None, 
                                  product_type: Optional[str] = None, tags: Optional[list] = None, 
                                  roaster_name: str = "Unknown", url: str = "") -> bool:
    """
    First-phase validation at discovery time.
    Uses the existing is_coffee_product utility function.
    
    Args:
        name: Product name
        description: Product description (if available)
        product_type: Product type/category (if available)
        tags: Product tags (if available)
        roaster_name: Name of the roaster (for logging)
        url: Product URL (for logging)
        
    Returns:
        True if the product appears to be coffee, False otherwise
    """
    return is_coffee_product(name, description, product_type, tags, roaster_name, url)

def validate_enriched_product(coffee_dict: Dict[str, Any]) -> bool:
    """
    Second-phase validation after product enrichment.
    Uses additional fields available after detailed page processing.
    
    Args:
        coffee_dict: Enriched coffee product dictionary
        
    Returns:
        True if product is validated as coffee, False otherwise
    """
    # Basic validation first
    name = coffee_dict.get('name', '')
    description = coffee_dict.get('description', '')
    product_type = coffee_dict.get('product_type', '')
    tags = coffee_dict.get('tags', [])
    roaster_name = coffee_dict.get('roaster_name', 'Unknown')
    url = coffee_dict.get('direct_buy_url', '')
    
    if not is_coffee_product(name, description, product_type, tags, roaster_name, url):
        logger.debug(f"Product failed basic validation: {name}")
        return False
    
    # Additional validation using enriched data
    
    # Check for coffee-specific attributes
    bean_type = coffee_dict.get('bean_type')
    processing_method = coffee_dict.get('processing_method')
    roast_level = coffee_dict.get('roast_level')
    
    # Stronger confidence if we have these coffee-specific attributes
    if bean_type or processing_method or roast_level:
        logger.debug(f"Product validated by coffee-specific attributes: {name}")
        return True
    
    # Check for coffee-specific keywords in the full description
    full_description = coffee_dict.get('description', '').lower()
    coffee_indicators = [
        'single origin', 'blend', 'roasted', 'coffee beans', 
        'arabica', 'robusta', 'flavor notes', 'tasting notes'
    ]
    
    if any(indicator in full_description for indicator in coffee_indicators):
        logger.debug(f"Product validated by coffee indicators in description: {name}")
        return True
    
    # Check for flavor profiles
    flavor_profiles = coffee_dict.get('flavor_profiles', [])
    if flavor_profiles and len(flavor_profiles) > 0:
        logger.debug(f"Product validated by flavor profiles: {name}")
        return True
    
    # Check price structure for coffee-like packages
    prices = coffee_dict.get('prices', [])
    if prices:
        # Check if any price entry has a coffee-typical size
        coffee_sizes = [250, 500, 1000]  # Common coffee sizes in grams
        size_tolerance = 50  # Allow some variation
        
        for price_entry in prices:
            size = price_entry.get('size_grams')
            if size and any(abs(size - coffee_size) <= size_tolerance for coffee_size in coffee_sizes):
                logger.debug(f"Product validated by typical coffee package size: {name}")
                return True
    
    # If none of the above specific checks passed, but it passed basic validation,
    # we still return True since it passed the initial filter
    logger.debug(f"Product passed basic validation only: {name}")
    return True