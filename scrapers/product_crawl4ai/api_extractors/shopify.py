# Path: scrapers/product/extractors/shopify_api_extractor.py

import asyncio
import json
import re
import logging
from typing import Dict, List, Optional, Any, Union
import httpx

from common.utils import is_coffee_product, ensure_absolute_url, create_slug, clean_description
from common.utils import standardize_roast_level, standardize_processing_method, standardize_bean_type
from db.models import Coffee, RoastLevel, BeanType, ProcessingMethod
from common.pydantic_utils import dict_to_pydantic_model, preprocess_coffee_data

logger = logging.getLogger(__name__)

# --- Improved roast level extraction ---
def extract_roast_level_from_shopify(shopify_product: Dict[str, Any], tags: List[str]) -> str:
    """Extract roast level from tags, slug, or title, using standardizer directly."""
    # First check tags for direct roast level indications
    for tag in tags:
        tag_lower = tag.lower()
        if 'roast' in tag_lower:
            # Pass to standardizer directly
            return standardize_roast_level(tag_lower)

    # Check handle/slug for roast level mentions
    handle = shopify_product.get('handle', '').lower()
    if 'roast' in handle:
        return standardize_roast_level(handle)

    # Check title for explicit roast mentions
    title = shopify_product.get('title', '').lower()
    if 'roast' in title:
        return standardize_roast_level(title)

    # At this point, let's check for specific keywords in any of these sources
    sources = [' '.join(tags), handle, title]
    for source in sources:
        if any(keyword in source.lower() for keyword in ['light', 'medium', 'dark', 'espresso', 'filter']):
            return standardize_roast_level(source)

    # Fallback to the regular attribute extraction method
    return standardize_roast_level(extract_attribute(shopify_product, 'roast_level', ['roast', 'roast level', 'roast-level']))

# --- Improved processing method extraction ---
def extract_processing_method_from_shopify(shopify_product: Dict[str, Any], tags: List[str], name: str, slug: str) -> str:
    """Extract processing method from tags, slug, or name, using standardizer directly."""
    # Check tags for processing method terms
    for tag in tags:
        tag_lower = tag.lower()
        if any(term in tag_lower for term in ['process', 'washed', 'natural', 'honey', 'anaerobic', 'ferment']):
            return standardize_processing_method(tag_lower)

    # Check product slug and name
    if any(term in slug.lower() for term in ['washed', 'natural', 'honey', 'anaerobic']):
        return standardize_processing_method(slug)

    if any(term in name.lower() for term in ['washed', 'natural', 'honey', 'anaerobic']):
        return standardize_processing_method(name)

    # Combine and check all sources for key processing terms
    all_text = f"{' '.join(tags)} {slug} {name}".lower()
    process_terms = ['washed', 'natural', 'honey', 'pulped', 'anaerobic', 'monsooned', 'wet-hulled', 'carbonic']
    if any(term in all_text for term in process_terms):
        return standardize_processing_method(all_text)

    # Fall back to regular attribute extraction
    return standardize_processing_method(extract_attribute(shopify_product, 'processing_method', ['process', 'processing', 'processing-method']))

async def extract_products_shopify(base_url: str, roaster_id: str, product_handle: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Extract coffee products from a Shopify store using the products.json API endpoint.
    
    Args:
        base_url: Base URL of the Shopify store
        roaster_id: Database ID of the roaster
        product_handle: Optional specific product handle to fetch
        
    Returns:
        List of Coffee Model instances
    """
    # Normalize base URL
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    
    # Determine the API endpoint
    if product_handle:
        api_url = f"{base_url}/products/{product_handle}.json"
    else:
        api_url = f"{base_url}/products.json?limit=250"
    
    logger.info(f"Fetching Shopify products from: {api_url}")
    
    # Make API request
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(api_url)
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch Shopify products: {response.status_code}")
                return []
                
            data = response.json()
            
        # Extract products
        if product_handle:
            # Single product response
            if 'product' in data:
                shopify_products = [data['product']]
            else:
                logger.warning(f"No product data found for handle: {product_handle}")
                return []
        else:
            # Multiple products response
            if 'products' in data:
                shopify_products = data['products']
            else:
                logger.warning("No products found in Shopify API response")
                return []
                
        # Convert to standardized format
        standardized_products = []
        for product in shopify_products:
            try:
                # First, check if product is actually coffee
                if not is_coffee_product(
                    name=product.get('title', ''), 
                    description=product.get('body_html', ''),
                    product_type=product.get('product_type', ''),
                    tags=product.get('tags', [])
                ):
                    logger.debug(f"Skipping non-coffee product: {product.get('title', '')}")
                    continue
                
                std_product_dict = standardize_shopify_product(product, base_url, roaster_id)
                if std_product_dict:
                    coffee_model = dict_to_pydantic_model(std_product_dict, Coffee, preprocessor=preprocess_coffee_data)
                if coffee_model:  
                    standardized_products.append(coffee_model)
                else:
                    # Fallback to dict if model validation fails
                    logger.warning(f"Validation failed for {std_product_dict.get('name')}, using dict instead")
                    standardized_products.append(std_product_dict)
            except Exception as e:
                logger.error(f"Error standardizing Shopify product: {e}")
                continue
                
        logger.info(f"Extracted {len(standardized_products)} standardized Shopify products")
        return standardized_products
        
    except Exception as e:
        logger.error(f"Error fetching Shopify products: {e}")
        return []

def standardize_shopify_product(shopify_product: Dict[str, Any], base_url: str, roaster_id: str) -> Optional[Dict[str, Any]]:
    """
    Convert a Shopify product to our standardized product schema.
    
    Args:
        shopify_product: Product data from Shopify API
        base_url: Base URL of the Shopify store
        roaster_id: Database ID of the roaster
        
    Returns:
        Standardized product dictionary or None if invalid
    """
    # Skip if no title/handle
    if not shopify_product.get('title') or not shopify_product.get('handle'):
        return None
        
    # Create base product
    product = {
        'name': shopify_product.get('title', ''),
        'slug': shopify_product.get('handle', ''),
        'roaster_id': roaster_id,
        'description': clean_description(shopify_product.get('body_html', '')),
        'direct_buy_url': ensure_absolute_url(f"/products/{shopify_product.get('handle')}", base_url),
        'image_url': None,
        'is_available': any(variant.get('available', False) for variant in shopify_product.get('variants', [])),
        'is_featured': False,  # This is set manually on our platform
        'deepseek_enriched': False,  # This is set during enrichment process
        'product_type': shopify_product.get('product_type', ''),
        'tags': _process_tags(shopify_product.get('tags', [])),
        'prices': [],
        'external_links': [],
        'source': 'shopify_api'
    }
    
    # Extract image URL
    if shopify_product.get('image') and shopify_product['image'].get('src'):
        product['image_url'] = shopify_product['image']['src']
    elif shopify_product.get('images') and len(shopify_product['images']) > 0:
        product['image_url'] = shopify_product['images'][0].get('src')
    
    # Extract prices from variants
    if 'variants' in shopify_product and shopify_product['variants']:
        product['prices'] = extract_prices_from_variants(shopify_product['variants'])
        
        # Calculate normalized 250g price if we have price data
        if product['prices']:
            product['price_250g'] = calculate_normalized_price(product['prices'], 250)
    
    # Extract metadata/attributes from product
    # Improved roast level and processing method extraction
    product['roast_level'] = extract_roast_level_from_shopify(shopify_product, product.get('tags', []))
    product['bean_type'] = standardize_bean_type(extract_attribute(shopify_product, 'bean_type', ['bean type', 'bean-type', 'beans', 'variety']))
    product['processing_method'] = extract_processing_method_from_shopify(shopify_product, product.get('tags', []), product['name'], product['slug'])
    product['region_name'] = extract_attribute(shopify_product, 'region_name', ['origin', 'region', 'country'])
    
    # Determine single origin status
    product['is_single_origin'] = _determine_single_origin(
        product['name'], 
        product['description'],
        product.get('product_type', ''),
        product.get('tags', [])
    )
    
    # Determine if product is seasonal
    product['is_seasonal'] = _is_seasonal_product(
        product.get('tags', []),
        product['description'],
        product['name']
    )
    
    # Extract flavor profiles and brew methods through regex patterns in description
    product['flavor_profiles'] = extract_flavor_profiles(product['description'])
    product['brew_methods'] = extract_brew_methods(product['description'])

    # Extract brew methods from grind size options
    for option in shopify_product.get('options', []):
        if any(term in option.get('name', '').lower() for term in ['grind', 'grind size', 'grind-size']):
            for value in option.get('values', []):
                brew_methods = extract_brew_methods_from_grind_size(value)
                if brew_methods:
                    if not product['brew_methods']:
                        product['brew_methods'] = []
                    for method in brew_methods:
                        if method not in product['brew_methods']:
                            product['brew_methods'].append(method)

    
    # Look for estate mentions in tags or product name/description
    estates = extract_estates(product['name'], product['description'], product.get('tags', []))
    if estates:
        product['estates'] = estates
        # Add estates to tags if not already there
        for estate in estates:
            estate_tag = f"estate:{estate}"
            if estate_tag not in product['tags']:
                product['tags'].append(estate_tag)
    
    return product

def _process_tags(tags: Union[List[str], str]) -> List[str]:
    """Process tags from Shopify to standardized format."""
    if isinstance(tags, str):
        tags = tags.split(', ')
    return [tag.strip() for tag in tags if tag.strip()]

def _determine_single_origin(name: str, description: str, product_type: str, tags: List[str]) -> bool:
    """Determine if a product is single origin based on various signals."""
    name_lower = name.lower()
    desc_lower = description.lower()
    
    # Check for blend indicators 
    blend_indicators = ['blend', 'mixed', 'combination', 'composite']
    for indicator in blend_indicators:
        if indicator in name_lower or indicator in desc_lower:
            return False
    
    # Check for single origin indicators
    single_origin_indicators = ['single origin', 'single-origin', 'estate', 'farm', 'microlot']
    for indicator in single_origin_indicators:
        if indicator in name_lower or indicator in desc_lower:
            return True
    
    # Check tags
    for tag in tags:
        tag = tag.lower()
        if any(indicator in tag for indicator in blend_indicators):
            return False
        if any(indicator in tag for indicator in single_origin_indicators):
            return True
    
    # Default: If "Estate" is in the name, it's likely single origin
    if 'estate' in name_lower:
        return True
        
    # Default to False if we can't determine
    return False

def _is_seasonal_product(tags: List[str], description: str, name: str) -> bool:
    """Determine if a product is seasonal based on tags and description."""
    # Check tags first
    if any(tag.lower() in ['seasonal', 'limited', 'limited-edition', 'limited edition'] for tag in tags):
        return True
    
    # Check description
    desc_lower = description.lower()
    seasonal_indicators = [
        'seasonal', 'limited', 'limited edition', 'limited-edition',
        'special release', 'for a limited time', 'while supplies last',
        'short run', 'small batch', 'exclusive release'
    ]
    
    for indicator in seasonal_indicators:
        if indicator in desc_lower:
            return True
    
    # Check name
    name_lower = name.lower()
    for indicator in seasonal_indicators:
        if indicator in name_lower:
            return True
    
    return False

def extract_attribute(shopify_product: Dict[str, Any], field_name: str, possible_keys: List[str]) -> Optional[str]:
    """
    Extract attribute value from Shopify product metafields or options.
    
    Args:
        shopify_product: Product data from Shopify API
        field_name: Field name to extract
        possible_keys: List of possible key names to match
        
    Returns:
        Attribute value if found, None otherwise
    """
    # Check metafields first
    if 'metafields' in shopify_product:
        for metafield in shopify_product['metafields']:
            key = metafield.get('key', '').lower()
            if any(possible_key in key for possible_key in possible_keys):
                return metafield.get('value')
    
    # Check options
    if 'options' in shopify_product:
        for option in shopify_product['options']:
            name = option.get('name', '').lower()
            if any(possible_key in name for possible_key in possible_keys):
                # Return first value if available
                if 'values' in option and option['values']:
                    return option['values'][0]
    
    # Check tags for specific attributes
    if shopify_product.get('tags'):
        tags = _process_tags(shopify_product['tags'])
        for tag in tags:
            tag_lower = tag.lower()
            # Look for tags that might indicate an attribute value
            for key in possible_keys:
                if key in tag_lower:
                    # Extract the value after the key
                    parts = tag_lower.split(key)
                    if len(parts) > 1 and parts[1].strip():
                        return parts[1].strip().replace('-', '').replace(':', '').strip()
    
    # Check product type as fallback for some fields
    product_type = shopify_product.get('product_type', '').lower()
    
    # Extract roast level from product type
    if field_name == 'roast_level':
        roast_patterns = ['light', 'medium', 'dark', 'espresso', 'filter', 'omniroast']
        for level in roast_patterns:
            if level in product_type:
                return level
    
    # Try to extract from description for key attributes
    description = shopify_product.get('body_html', '').lower()
    
    # Common patterns for attributes in descriptions
    patterns = {
        'roast_level': [
            r'(light|medium|dark)(?:\s+roast)',
            r'roast(?:ed)?\s+(?:to\s+)?(?:a\s+)?(light|medium|dark)',
            r'(light|medium|dark)\s+roasted'
        ],
        'bean_type': [
            r'(arabica|robusta|liberica)(?:\s+beans?)',
            r'(?:100%\s+)?(arabica|robusta|liberica)',
            r'(single\s+origin)',
            r'(?:a\s+)?(blend)'
        ],
        'processing_method': [
            r'(washed|natural|honey|pulped\s+natural|anaerobic)(?:\s+process)',
            r'process(?:ed)?\s+(?:using\s+)?(?:the\s+)?(washed|natural|honey|pulped\s+natural|anaerobic)',
        ],
        'region_name': [
            r'(?:grown|cultivated|produced|harvested)\s+in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
        ]
    }
    
    if field_name in patterns:
        for pattern in patterns[field_name]:
            match = re.search(pattern, description)
            if match:
                return match.group(1)
    
    return None

def extract_prices_from_variants(variants: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract pricing information from Shopify variants.
    Fixes duplication by consolidating by size_grams.
    """
    prices_by_size = {}
    weight_patterns = [
        r'(\d+\.?\d*)\s*(?:g|grams?|gm)',
        r'(\d+\.?\d*)\s*(?:kg|kilos?|kilograms?)'
    ]
    for variant in variants:
        if not variant.get('price'):
            continue
        weight_grams = None
        variant_title = variant.get('title', '')
        # Try to extract weight from title
        for pattern in weight_patterns:
            match = re.search(pattern, variant_title, re.IGNORECASE)
            if match:
                weight = float(match.group(1))
                if 'kg' in variant_title.lower() or 'kilo' in variant_title.lower():
                    weight *= 1000
                weight_grams = int(weight)
                break
        # If not found, check options
        if not weight_grams and 'option1' in variant:
            for i in range(1, 4):
                option_key = f'option{i}'
                if option_key not in variant:
                    continue
                option_value = variant[option_key]
                if not option_value:
                    continue
                for pattern in weight_patterns:
                    match = re.search(pattern, str(option_value), re.IGNORECASE)
                    if match:
                        weight = float(match.group(1))
                        if 'kg' in str(option_value).lower() or 'kilo' in str(option_value).lower():
                            weight *= 1000
                        weight_grams = int(weight)
                        break
                if weight_grams:
                    break
        # Add/replace price if weight found
        if weight_grams and float(variant['price']) > 0:
            if weight_grams not in prices_by_size or float(variant['price']) < prices_by_size[weight_grams]:
                prices_by_size[weight_grams] = float(variant['price'])
    return [
        {"size_grams": size, "price": price}
        for size, price in prices_by_size.items()
    ]

def calculate_normalized_price(prices: List[Dict[str, Any]], target_size: int = 250) -> Optional[float]:
    """
    Calculate a normalized price for a standard weight (default 250g).
    Uses linear interpolation between package sizes.
    
    Args:
        prices: List of price objects with size_grams and price
        target_size: Target size in grams to normalize to
        
    Returns:
        Normalized price or None if cannot be calculated
    """
    if not prices:
        return None
    
    # Sort prices by size
    sorted_prices = sorted(prices, key=lambda x: x['size_grams'])
    
    # If we have a direct match, use it
    for price in sorted_prices:
        if price['size_grams'] == target_size:
            return price['price']
    
    # If target is smaller than smallest size, scale down from smallest
    if target_size < sorted_prices[0]['size_grams']:
        smallest = sorted_prices[0]
        return (target_size / smallest['size_grams']) * smallest['price']
    
    # If target is larger than largest size, scale up from largest
    if target_size > sorted_prices[-1]['size_grams']:
        largest = sorted_prices[-1]
        return (target_size / largest['size_grams']) * largest['price']
    
    # Find the two sizes that bracket the target size
    for i in range(len(sorted_prices) - 1):
        lower = sorted_prices[i]
        upper = sorted_prices[i + 1]
        
        if lower['size_grams'] <= target_size <= upper['size_grams']:
            # Linear interpolation
            size_ratio = (target_size - lower['size_grams']) / (upper['size_grams'] - lower['size_grams'])
            price_diff = upper['price'] - lower['price']
            return lower['price'] + (size_diff * price_ratio)
    
    # Fallback: use the closest size
    closest = min(sorted_prices, key=lambda x: abs(x['size_grams'] - target_size))
    return (target_size / closest['size_grams']) * closest['price']

def extract_flavor_profiles(description: str) -> List[str]:
    """Extract flavor profile notes from product description."""
    # List of common coffee flavor descriptors
    flavor_profiles = [
        # Fruity
        "berry", "blueberry", "strawberry", "raspberry", "blackberry", "cherry", 
        "cranberry", "apple", "pear", "grape", "raisin", "plum", "peach", "apricot",
        "mango", "papaya", "pineapple", "banana", "melon", "watermelon", "citrus", 
        "lemon", "lime", "orange", "grapefruit", "passion fruit", "kiwi", "pomegranate",
        "prune", "date", "fig", "black currant", "red currant", "tropical",
        
        # Floral
        "floral", "jasmine", "rose", "lavender", "chamomile", "hibiscus", "elderflower",
        
        # Sweet
        "sweet", "honey", "caramel", "toffee", "butterscotch", "molasses", "maple",
        "brown sugar", "vanilla", "marshmallow", "chocolate", "cocoa", "candy",
        
        # Nutty
        "nut", "nutty", "almond", "hazelnut", "peanut", "cashew", "walnut", "pecan",
        
        # Spicy
        "spice", "cinnamon", "clove", "pepper", "anise", "cardamom", "ginger",
        
        # Earthy
        "earthy", "woody", "musty", "herbaceous", "moss", "leaf", "soil",
        
        # Other
        "tobacco", "leather", "toasted", "smoky", "malty", "graham cracker", "biscuit",
        "cereal", "bread", "buttery", "creamy", "winey", "tea-like", "black tea",
        "green tea"
    ]
    
    found_flavors = []
    
    # Check for phrases like "notes of X, Y, and Z"
    notes_patterns = [
        r"notes?\s+of\s+([A-Za-z0-9,\s&+]+)",
        r"flavou?rs?\s+of\s+([A-Za-z0-9,\s&+]+)",
        r"hints?\s+of\s+([A-Za-z0-9,\s&+]+)",
        r"aromas?\s+of\s+([A-Za-z0-9,\s&+]+)",
        r"tasting\s+notes:?\s+([A-Za-z0-9,\s&+:]+)"
    ]
    
    for pattern in notes_patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            # Split the matched text into individual flavors
            flavor_text = match.group(1).lower()
            # Replace common separators with commas
            flavor_text = re.sub(r'\s+and\s+', ',', flavor_text)
            flavor_text = re.sub(r'\s*[&+]\s*', ',', flavor_text)
            flavor_text = re.sub(r'\s*:\s*', ',', flavor_text) 
            
            # Split by comma and clean up
            potential_flavors = [f.strip() for f in flavor_text.split(',')]
            for flavor in potential_flavors:
                # Add exact matches
                if flavor in flavor_profiles:
                    found_flavors.append(flavor)
                else:
                    # Look for partial matches
                    for profile in flavor_profiles:
                        if profile in flavor and profile not in found_flavors:
                            found_flavors.append(profile)
    
    # If we didn't find any flavors from specific phrases, look for any mentions
    if not found_flavors:
        for flavor in flavor_profiles:
            # Ensure we're matching whole words/phrases
            pattern = r'\b' + re.escape(flavor) + r'\b'
            if re.search(pattern, description.lower(), re.IGNORECASE):
                found_flavors.append(flavor)
    
    return found_flavors

def extract_brew_methods(description: str) -> List[str]:
    """Extract recommended brewing methods from product description."""
    brew_methods = [
        "espresso", "filter", "pour over", "pourover", "french press", "aeropress",
        "cold brew", "moka pot", "siphon", "chemex", "drip", "v60", "hario v60",
        "kalita", "clever dripper", "immersion", "percolator", "turkish", "ibrik", 
        "south indian filter", "vietnamese press"
    ]
    
    found_methods = []
    
    # Check for phrases like "perfect for X" or "ideal for Y"
    recommendation_patterns = [
        r"(?:perfect|ideal|great|excellent|recommended)\s+for\s+([A-Za-z0-9,\s&+]+)",
        r"(?:best\s+(?:when\s+)?(?:brewed|prepared|made))\s+(?:as|with|using)?\s+([A-Za-z0-9,\s&+]+)",
        r"(?:recommended|suggested)\s+(?:brewing\s+)?method:?\s+([A-Za-z0-9,\s&+:]+)"
    ]
    
    for pattern in recommendation_patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            # Split the matched text into individual methods
            methods_text = match.group(1).lower()
            # Replace common separators with commas
            methods_text = re.sub(r'\s+and\s+', ',', methods_text)
            methods_text = re.sub(r'\s*[&+]\s*', ',', methods_text)
            methods_text = re.sub(r'\s*:\s*', ',', methods_text)
            
            # Split by comma and clean up
            potential_methods = [m.strip() for m in methods_text.split(',')]
            for method in potential_methods:
                # Add exact matches
                if method in brew_methods:
                    found_methods.append(method)
                else:
                    # Look for partial matches
                    for brew_method in brew_methods:
                        if brew_method in method and brew_method not in found_methods:
                            found_methods.append(brew_method)
    
    # If we didn't find any specific recommendations, look for any mentions
    if not found_methods:
        for method in brew_methods:
            # Ensure we're matching whole words/phrases
            pattern = r'\b' + re.escape(method) + r'\b'
            if re.search(pattern, description.lower(), re.IGNORECASE):
                found_methods.append(method)
    
    return found_methods

def extract_estates(name: str, description: str, tags: List[str]) -> List[str]:
    """
    Extract estate names from product name, description, and tags.
    
    Args:
        name: Product name
        description: Product description
        tags: Product tags
        
    Returns:
        List of estate names
    """
    estates = []
    
    # Check tags first for estate mentions
    for tag in tags:
        tag_lower = tag.lower()
        if 'estate' in tag_lower:
            # Extract the estate name
            estate_name = None
            if ':' in tag:
                estate_name = tag.split(':', 1)[1].strip()
            elif '-' in tag:
                estate_name = tag.split('-', 1)[1].strip()
            elif ' ' in tag:
                # Take everything after "estate"
                parts = tag_lower.split('estate', 1)
                if len(parts) > 1 and parts[1].strip():
                    estate_name = parts[1].strip()
            
            if estate_name and estate_name not in estates:
                estates.append(estate_name)
    
    # Check product name for estate mentions
    estate_patterns = [
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+Estate',  # Attikan Estate
        r'Estate\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # Estate of Attikan
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Estate|Estates|Farm|Plantation)'  # Matches any ending
    ]
    
    for pattern in estate_patterns:
        matches = re.finditer(pattern, name, re.IGNORECASE)
        for match in matches:
            estate_name = match.group(1).strip()
            if estate_name and estate_name not in estates:
                estates.append(estate_name)
    
    # Check description similarly
    desc_matches = re.finditer(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+Estate', description, re.IGNORECASE)
    for match in desc_matches:
        estate_name = match.group(1).strip()
        if estate_name and estate_name not in estates:
            estates.append(estate_name)
    
    return estates