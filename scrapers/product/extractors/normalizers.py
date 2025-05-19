# scrapers/product/extractors/normalizers.py
import re
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)

def normalize_text(text: str) -> str:
    """
    Normalize text by trimming whitespace, removing extra spaces, and converting to lowercase.
    
    Args:
        text: Text to normalize
        
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # Convert to string if needed
    if not isinstance(text, str):
        text = str(text)
    
    # Remove extra whitespace and trim
    normalized = re.sub(r'\s+', ' ', text).strip()
    
    # Convert to lowercase
    return normalized.lower()

def create_slug(name: str) -> str:
    """
    Create a URL-friendly slug from a name.
    
    Args:
        name: Name to convert to slug
        
    Returns:
        URL-friendly slug
    """
    if not name:
        return ""
    
    # Convert to lowercase
    slug = name.lower()
    
    # Replace non-alphanumeric characters with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    # Replace multiple consecutive hyphens with a single one
    slug = re.sub(r'-+', '-', slug)
    
    return slug

def normalize_coffee_name(name: str) -> str:
    """
    Normalize coffee product name.
    
    Args:
        name: Coffee product name
        
    Returns:
        Normalized coffee name
    """
    if not name:
        return ""
    
    # Remove common suffixes
    name = re.sub(r'\s+(?:coffee|beans|ground|whole\s+bean)$', '', name, flags=re.IGNORECASE)
    
    # Remove roaster name prefix if it appears to be redundant
    # This is a simplified approach and might need to be adjusted
    name_parts = name.split(' - ', 1)
    if len(name_parts) > 1 and len(name_parts[0]) < 30:  # Assume first part is roaster name if short enough
        name = name_parts[1]
    
    # Handle suffixes like "(Pack of 2)" in names
    name = re.sub(r'\s*\(Pack of \d+\)\s*$', '', name)
    
    # Handle percentage indicators in blends
    # e.g., "50% Arabica - 50% Robusta- Roasted Coffee Beans"
    # Should be simplified to "Arabica Robusta Blend"
    name = re.sub(r'\s*(\d+%)\s*([a-zA-Z]+)\s*-\s*(\d+%)\s*([a-zA-Z]+)(.*)', r'\2 \4 Blend', name)
    
    # Capitalize properly
    name = ' '.join(word.capitalize() if word.lower() not in ['and', 'or', 'the', 'in', 'on', 'at', 'by', 'for', 'with', 'a', 'an'] 
                   else word.lower() for word in name.split())
    
    return name

def normalize_price(price: Any) -> Optional[float]:
    """
    Normalize price value to a float.
    
    Args:
        price: Price value (string, int, float)
        
    Returns:
        Normalized price as float or None if invalid
    """
    if price is None:
        return None
    
    # If it's already a float, just return it
    if isinstance(price, float):
        return price
    
    # If it's an int, convert to float
    if isinstance(price, int):
        return float(price)
    
    # If it's a string, try to convert to float
    if isinstance(price, str):
        # Remove currency symbols and commas
        price_str = re.sub(r'[₹$€£,]', '', price.strip())
        try:
            return float(price_str)
        except ValueError:
            logger.warning(f"Could not convert price '{price}' to float")
            return None
    
    # For any other type, try to convert to float
    try:
        return float(price)
    except (ValueError, TypeError):
        logger.warning(f"Could not convert price '{price}' to float")
        return None

def normalize_image_url(url: str) -> Optional[str]:
    """
    Normalize image URL.
    
    Args:
        url: Image URL
        
    Returns:
        Normalized image URL or None if invalid
    """
    if not url:
        return None
    
    # Ensure URL starts with http:// or https://
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url.lstrip('/')
    
    # Remove tracking parameters
    url = re.sub(r'\?(utm_|fbclid|gclid|msclkid|ref).*$', '', url)
    
    # Add default image extensions if missing
    if not re.search(r'\.(jpg|jpeg|png|gif|webp|svg)($|\?)', url.lower()):
        if '?' in url:
            url = url.split('?')[0] + '.jpg?' + url.split('?')[1]
        else:
            url = url + '.jpg'
    
    return url

def normalize_flavor_profiles(flavors: Union[str, List[str]]) -> List[str]:
    """
    Normalize flavor profiles to a standard list.
    
    Args:
        flavors: Flavor profiles as string or list
        
    Returns:
        Normalized list of flavor profiles
    """
    if not flavors:
        return []
    
    # If it's a string, split it into a list
    if isinstance(flavors, str):
        # Split by commas, slashes, or "and"
        flavors = re.split(r'[,/&]|\s+and\s+', flavors)
    
    # Normalize each flavor
    normalized = []
    for flavor in flavors:
        if not flavor:
            continue
        
        # Trim and lowercase
        flavor = normalize_text(flavor)
        
        # Skip empty strings
        if not flavor:
            continue
        
        # Replace common variations with standard terms
        flavor_mapping = {
            'chocolatey': 'chocolate',
            'chocolaty': 'chocolate',
            'chocolate notes': 'chocolate',
            'cocoa notes': 'cocoa',
            'nuttyness': 'nutty',
            'nutiness': 'nutty',
            'caramelized': 'caramel',
            'fruityness': 'fruity',
            'fruity notes': 'fruity',
            'berries': 'berry',
            'citrusy': 'citrus',
            'floral notes': 'floral',
            'spicyness': 'spice',
            'spicy': 'spice',
            'earthyness': 'earthy',
            'woody notes': 'woody',
            'tobacco notes': 'tobacco',
            'honey notes': 'honey',
        }
        
        if flavor in flavor_mapping:
            flavor = flavor_mapping[flavor]
        
        # Add to normalized list if not already present
        if flavor not in normalized:
            normalized.append(flavor)
    
    return normalized

def normalize_boolean_field(value: Any) -> Optional[bool]:
    """
    Normalize a value to a boolean.
    
    Args:
        value: Value to normalize
        
    Returns:
        Normalized boolean value or None if unable to determine
    """
    if value is None:
        return None
    
    # If it's already a boolean, return it
    if isinstance(value, bool):
        return value
    
    # If it's a string, check common patterns
    if isinstance(value, str):
        value = value.lower().strip()
        
        # Positive indicators
        if value in ['yes', 'true', 'y', 't', '1', 'on']:
            return True
        
        # Negative indicators
        if value in ['no', 'false', 'n', 'f', '0', 'off']:
            return False
    
    # If it's a number, 0 is False, anything else is True
    if isinstance(value, (int, float)):
        return value != 0
    
    # If we can't determine, return None
    return None

def normalize_date(date_value: Union[str, datetime, None]) -> Optional[str]:
    """
    Normalize a date value to ISO format string.
    
    Args:
        date_value: Date value as string, datetime, or None
        
    Returns:
        ISO format date string or None if invalid
    """
    if date_value is None:
        return None
    
    # If it's already a datetime, convert to ISO format
    if isinstance(date_value, datetime):
        return date_value.isoformat()
    
    # If it's a string, try to parse it
    if isinstance(date_value, str):
        # Try different date formats
        date_formats = [
            '%Y-%m-%d',          # 2023-05-15
            '%Y-%m-%dT%H:%M:%S', # 2023-05-15T14:30:00
            '%d/%m/%Y',          # 15/05/2023
            '%m/%d/%Y',          # 05/15/2023
            '%B %d, %Y',         # May 15, 2023
            '%d %B %Y',          # 15 May 2023
            '%Y%m%d',            # 20230515
        ]
        
        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_value.strip(), fmt)
                return dt.isoformat()
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date '{date_value}'")
    
    return None

def normalize_description(description: str) -> str:
    """
    Normalize product description text.
    
    Args:
        description: Product description
        
    Returns:
        Normalized description text
    """
    if not description:
        return ""
    
    # Remove HTML tags
    description = re.sub(r'<[^>]+>', ' ', description)
    
    # Remove excess whitespace
    description = re.sub(r'\s+', ' ', description).strip()
    
    # Remove common boilerplate phrases
    boilerplate = [
        r'add to cart',
        r'buy now',
        r'shipping information',
        r'return policy',
        r'click here',
        r'learn more',
        r'see more',
        r'read more',
    ]
    
    for phrase in boilerplate:
        description = re.sub(rf'{phrase}', '', description, flags=re.IGNORECASE)
    
    return description

def normalize_coffee_data(coffee: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize all fields in a coffee product dict.
    
    Args:
        coffee: Coffee product dict
        
    Returns:
        Normalized coffee product dict
    """
    normalized = {}
    
    # Copy over non-normalized fields
    for key, value in coffee.items():
        if value is not None:
            normalized[key] = value
    
    # Normalize text fields
    if 'name' in coffee:
        normalized['name'] = normalize_coffee_name(coffee['name'])
    
    if 'description' in coffee:
        normalized['description'] = normalize_description(coffee['description'])
    
    # Generate slug if name exists
    if 'name' in normalized and 'slug' not in normalized:
        normalized['slug'] = create_slug(normalized['name'])
    
    # Normalize prices
    price_fields = ['price_100g', 'price_250g', 'price_500g', 'price_1kg']
    for field in price_fields:
        if field in coffee:
            normalized[field] = normalize_price(coffee[field])
    
    # Normalize image URL
    if 'image_url' in coffee:
        normalized['image_url'] = normalize_image_url(coffee['image_url'])
    
    # Normalize flavor profiles
    if 'flavor_profiles' in coffee:
        normalized['flavor_profiles'] = normalize_flavor_profiles(coffee['flavor_profiles'])
    
    # Normalize boolean fields
    boolean_fields = ['is_available', 'is_seasonal', 'is_single_origin', 'is_blend', 'is_featured']
    for field in boolean_fields:
        if field in coffee:
            normalized[field] = normalize_boolean_field(coffee[field])
    
    # Normalize date fields
    date_fields = ['created_at', 'updated_at', 'last_scraped_at']
    for field in date_fields:
        if field in coffee:
            normalized[field] = normalize_date(coffee[field])
    
    # Set default values for required fields if missing
    if 'is_available' not in normalized:
        normalized['is_available'] = True
    
    if 'last_scraped_at' not in normalized:
        normalized['last_scraped_at'] = datetime.now().isoformat()
    
    return normalized

def standardize_coffee_model(coffee: Dict[str, Any]) -> Dict[str, Any]:
    """
    Standardize coffee data to match the database model structure.
    
    Args:
        coffee: Coffee product dict with potentially non-standard fields
        
    Returns:
        Standardized coffee product dict matching the database model
    """
    # Normalize all fields first
    normalized = normalize_coffee_data(coffee)
    
    # Define standard model fields
    standard_fields = {
        # Core fields
        'name': str,
        'slug': str,
        'roaster_id': str,
        'roaster_slug': str,  # Temporary field for linking
        'description': str,
        'roast_level': str,
        'bean_type': str,
        'processing_method': str,
        'region_id': str,
        'region_name': str,  # Temporary field for linking
        'image_url': str,
        'direct_buy_url': str,
        
        # Boolean flags
        'is_seasonal': bool,
        'is_single_origin': bool,
        'is_available': bool,
        'is_featured': bool,
        'is_blend': bool,
        
        # Price fields
        'price_100g': float,
        'price_200g': float,
        'price_250g': float,
        'price_500g': float,
        'price_750g': float,
        'price_1kg': float,
        'price_2kg': float,
        
        # Related data
        'flavor_profiles': list,
        'brew_methods': list,
        
        # Metadata
        'tags': list,
        'confidence_scores': dict,
        'last_scraped_at': str,
        'scrape_status': str,
    }
    
    # Create standardized dict with correct types
    standardized = {}
    
    for field, field_type in standard_fields.items():
        if field in normalized:
            # Type conversion for basic types
            if field_type is str and normalized[field] is not None:
                standardized[field] = str(normalized[field])
            elif field_type is float and normalized[field] is not None:
                try:
                    standardized[field] = float(normalized[field])
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert {field}='{normalized[field]}' to float")
            elif field_type is bool and normalized[field] is not None:
                standardized[field] = bool(normalized[field])
            elif field_type is list and normalized[field] is not None:
                if not isinstance(normalized[field], list):
                    standardized[field] = [normalized[field]]
                else:
                    standardized[field] = normalized[field]
            elif field_type is dict and normalized[field] is not None:
                if not isinstance(normalized[field], dict):
                    standardized[field] = {'value': normalized[field]}
                else:
                    standardized[field] = normalized[field]
            else:
                standardized[field] = normalized[field]
    
    # Copy over any additional fields not in the standard model
    for field, value in normalized.items():
        if field not in standardized and value is not None:
            standardized[field] = value
    
    return standardized

def get_field_confidence(coffee: Dict[str, Any], field: str) -> float:
    """
    Get confidence score for a field from coffee data.
    
    Args:
        coffee: Coffee product dict
        field: Field name to get confidence for
        
    Returns:
        Confidence score (0.0-1.0) or 0.0 if not found
    """
    if 'confidence_scores' not in coffee:
        return 0.0
    
    confidence_scores = coffee['confidence_scores']
    if not isinstance(confidence_scores, dict):
        return 0.0
    
    return float(confidence_scores.get(field, 0.0))
