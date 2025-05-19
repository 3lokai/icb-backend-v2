# scrapers/product/enrichment/deepseek.py
import json
import logging
from typing import Dict, List, Any

from common.enricher import enricher

logger = logging.getLogger(__name__)

def needs_enhancement(coffee: Dict[str, Any]) -> bool:
    """Check if coffee object needs LLM enhancement."""
    missing_fields = []
    
    if "roast_level" not in coffee or coffee.get("roast_level") == "unknown":
        missing_fields.append("roast_level")
        
    if "bean_type" not in coffee or coffee.get("bean_type") == "unknown":
        missing_fields.append("bean_type")
        
    if "processing_method" not in coffee and not coffee.get("is_blend", False):
        missing_fields.append("processing_method")
        
    if "flavor_profiles" not in coffee:
        missing_fields.append("flavor_profiles")
        
    # Only enhance if multiple fields are missing - saves on API calls
    return len(missing_fields) >= 2

async def enhance_with_deepseek(coffee: Dict[str, Any], roaster_name: str = None) -> Dict[str, Any]:
    """
    Enhance coffee product attributes using DeepSeek via the central enrichment service.
    This is a simplified wrapper around the EnrichmentService.enhance_product method.
    """
    if not needs_enhancement(coffee):
        logger.debug(f"Skipping enhancement for {coffee.get('name')}: No enhancement needed")
        return coffee
    
    # Call the existing enrichment service
    return await enricher.enhance_product(coffee, roaster_name)

async def batch_enhance_coffees(coffees: List[Dict[str, Any]], roaster_name: str = None, batch_size: int = 5) -> List[Dict[str, Any]]:
    """
    Process multiple coffee products in batches to avoid overwhelming resources.
    Uses the central enrichment service for batch processing.
    """
    # Filter to only coffees that need enhancement
    coffees_to_enhance = [c for c in coffees if needs_enhancement(c)]
    
    if not coffees_to_enhance:
        logger.info("No coffees need enhancement")
        return coffees
    
    logger.info(f"Enhancing {len(coffees_to_enhance)} out of {len(coffees)} coffees")
    
    # Use the batch enrichment from the central service
    enhanced_coffees = await enricher.batch_enrich_products(coffees_to_enhance, roaster_name, batch_size)
    
    # Create a mapping to merge back into the original list
    enhanced_map = {c.get('name'): c for c in enhanced_coffees}
    
    # Update the original list with enhanced data
    result = []
    for coffee in coffees:
        name = coffee.get('name')
        if name in enhanced_map:
            result.append(enhanced_map[name])
        else:
            result.append(coffee)
    
    # Log enhancement statistics
    await enricher.save_enrichment_logs(result, "coffee_products")
    
    return result