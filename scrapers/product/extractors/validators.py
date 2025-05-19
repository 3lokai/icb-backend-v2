# scrapers/product/extractors/validators.py
import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from enum import Enum

logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    """Validation severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

class ValidationResult:
    """Result of a validation check."""
    
    def __init__(self, field: str, valid: bool, level: ValidationLevel = ValidationLevel.WARNING, 
                 message: str = None, corrected_value: Any = None):
        """
        Initialize validation result.
        
        Args:
            field: Field name that was validated
            valid: Whether validation passed
            level: Severity level of validation issue
            message: Description of validation issue
            corrected_value: Corrected value if auto-correction was applied
        """
        self.field = field
        self.valid = valid
        self.level = level
        self.message = message
        self.corrected_value = corrected_value
    
    def __str__(self):
        """String representation of validation result."""
        valid_str = "Valid" if self.valid else f"Invalid ({self.level.value})"
        if self.message:
            return f"{valid_str}: {self.field} - {self.message}"
        return f"{valid_str}: {self.field}"

def validate_roast_level(value: str) -> ValidationResult:
    """
    Validate roast level against standard vocabulary.
    
    Args:
        value: Roast level to validate
        
    Returns:
        ValidationResult with validation status
    """
    valid_roast_levels = [
        'light', 'light-medium', 'medium', 'medium-dark', 'dark', 
        'city', 'city-plus', 'full-city', 'french', 'italian', 'cinnamon',
        'filter', 'espresso', 'omniroast', 'unknown'
    ]
    
    if not value:
        return ValidationResult('roast_level', False, ValidationLevel.WARNING, 
                               "Roast level is empty or not specified")
    
    value = value.lower().strip()
    
    if value in valid_roast_levels:
        return ValidationResult('roast_level', True)
    
    # Try to correct common variations
    roast_mapping = {
        'light roast': 'light',
        'medium roast': 'medium',
        'medium-light roast': 'light-medium',
        'medium light roast': 'light-medium',
        'medium-dark roast': 'medium-dark', 
        'medium dark roast': 'medium-dark',
        'dark roast': 'dark',
        'omni': 'omniroast',
        'omni roast': 'omniroast',
    }
    
    if value in roast_mapping:
        corrected = roast_mapping[value]
        return ValidationResult('roast_level', False, ValidationLevel.INFO,
                              f"Corrected roast level from '{value}' to '{corrected}'",
                              corrected)
    
    # Check for partial matches
    for valid_roast in valid_roast_levels:
        if valid_roast in value:
            return ValidationResult('roast_level', False, ValidationLevel.INFO,
                                  f"Corrected roast level from '{value}' to '{valid_roast}'",
                                  valid_roast)
    
    return ValidationResult('roast_level', False, ValidationLevel.WARNING,
                          f"Invalid roast level: '{value}'")

def validate_bean_type(value: str) -> ValidationResult:
    """
    Validate bean type against standard vocabulary.
    
    Args:
        value: Bean type to validate
        
    Returns:
        ValidationResult with validation status
    """
    valid_bean_types = [
        'arabica', 'robusta', 'liberica', 'blend', 'mixed-arabica',
        'arabica-robusta', 'unknown'
    ]
    
    if not value:
        return ValidationResult('bean_type', False, ValidationLevel.WARNING,
                              "Bean type is empty or not specified")
    
    value = value.lower().strip()
    
    if value in valid_bean_types:
        return ValidationResult('bean_type', True)
    
    # Try to correct common variations
    bean_mapping = {
        '100% arabica': 'arabica',
        'arabica blend': 'mixed-arabica',
        'mixed arabica': 'mixed-arabica',
        'arabica mix': 'mixed-arabica',
        'arabica robusta': 'arabica-robusta',
        'arabica robusta blend': 'arabica-robusta',
        'arabica/robusta': 'arabica-robusta',
        'arabica and robusta': 'arabica-robusta',
        'arabica & robusta': 'arabica-robusta',
    }
    
    if value in bean_mapping:
        corrected = bean_mapping[value]
        return ValidationResult('bean_type', False, ValidationLevel.INFO,
                              f"Corrected bean type from '{value}' to '{corrected}'",
                              corrected)
    
    # Check for partial matches
    if 'arabica' in value and 'robusta' in value:
        return ValidationResult('bean_type', False, ValidationLevel.INFO,
                              f"Corrected bean type from '{value}' to 'arabica-robusta'",
                              'arabica-robusta')
    
    if 'arabica' in value and 'blend' in value:
        return ValidationResult('bean_type', False, ValidationLevel.INFO,
                              f"Corrected bean type from '{value}' to 'mixed-arabica'",
                              'mixed-arabica')
    
    if 'arabica' in value:
        return ValidationResult('bean_type', False, ValidationLevel.INFO,
                              f"Corrected bean type from '{value}' to 'arabica'",
                              'arabica')
    
    if 'robusta' in value:
        return ValidationResult('bean_type', False, ValidationLevel.INFO,
                              f"Corrected bean type from '{value}' to 'robusta'",
                              'robusta')
    
    if 'liberica' in value:
        return ValidationResult('bean_type', False, ValidationLevel.INFO,
                              f"Corrected bean type from '{value}' to 'liberica'",
                              'liberica')
    
    if 'blend' in value or 'mix' in value:
        return ValidationResult('bean_type', False, ValidationLevel.INFO,
                              f"Corrected bean type from '{value}' to 'blend'",
                              'blend')
    
    return ValidationResult('bean_type', False, ValidationLevel.WARNING,
                          f"Invalid bean type: '{value}'")

def validate_processing_method(value: str) -> ValidationResult:
    """
    Validate processing method against standard vocabulary.
    
    Args:
        value: Processing method to validate
        
    Returns:
        ValidationResult with validation status
    """
    valid_processing_methods = [
        'washed', 'natural', 'honey', 'pulped-natural', 'anaerobic',
        'monsooned', 'wet-hulled', 'carbonic-maceration', 'double-fermented', 'unknown'
    ]
    
    if not value:
        return ValidationResult('processing_method', False, ValidationLevel.WARNING,
                              "Processing method is empty or not specified")
    
    value = value.lower().strip()
    
    if value in valid_processing_methods:
        return ValidationResult('processing_method', True)
    
    # Try to correct common variations
    process_mapping = {
        'wet': 'washed',
        'wet process': 'washed',
        'fully washed': 'washed',
        'traditional washed': 'washed',
        'water process': 'washed',
        'dry': 'natural',
        'dry process': 'natural',
        'sun dried': 'natural',
        'sundried': 'natural',
        'unwashed': 'natural',
        'traditional natural': 'natural',
        'black honey': 'honey',
        'red honey': 'honey',
        'yellow honey': 'honey',
        'white honey': 'honey',
        'golden honey': 'honey',
        'pulped natural': 'pulped-natural',
        'semi-washed': 'honey',
        'semi washed': 'honey',
        'anaerobic natural': 'anaerobic',
        'anaerobic washed': 'anaerobic',
        'anaerobic fermentation': 'anaerobic',
        'double anaerobic': 'anaerobic',
        'carbonic': 'carbonic-maceration',
        'carbonic maceration': 'carbonic-maceration',
        'wet hulled': 'wet-hulled',
        'giling basah': 'wet-hulled',
        'monsoon': 'monsooned',
        'monsooning': 'monsooned',
        'monsooned malabar': 'monsooned',
        'double fermented': 'double-fermented',
        'extended fermentation': 'double-fermented',
    }
    
    if value in process_mapping:
        corrected = process_mapping[value]
        return ValidationResult('processing_method', False, ValidationLevel.INFO,
                              f"Corrected processing method from '{value}' to '{corrected}'",
                              corrected)
    
    # Check for partial matches using keywords
    keywords_to_method = {
        'washed': 'washed',
        'wet': 'washed',
        'natural': 'natural',
        'dry': 'natural',
        'honey': 'honey',
        'pulped': 'pulped-natural',
        'anaerobic': 'anaerobic',
        'carbonic': 'carbonic-maceration',
        'monsoon': 'monsooned',
        'hulled': 'wet-hulled',
        'fermented': 'double-fermented',
    }
    
    for keyword, method in keywords_to_method.items():
        if keyword in value:
            return ValidationResult('processing_method', False, ValidationLevel.INFO,
                                  f"Corrected processing method from '{value}' to '{method}'",
                                  method)
    
    return ValidationResult('processing_method', False, ValidationLevel.WARNING,
                          f"Invalid processing method: '{value}'")

def validate_price(price: float, size_grams: int = None) -> ValidationResult:
    """
    Validate price is within reasonable ranges.
    
    Args:
        price: Price value to validate
        size_grams: Size in grams for context (optional)
        
    Returns:
        ValidationResult with validation status
    """
    field = 'price'
    if size_grams:
        field = f'price_{size_grams}g'
    
    if price is None:
        return ValidationResult(field, False, ValidationLevel.WARNING,
                              "Price is not specified")
    
    try:
        price_float = float(price)
    except (ValueError, TypeError):
        return ValidationResult(field, False, ValidationLevel.ERROR,
                              f"Price '{price}' is not a valid number")
    
    # Check if price is negative
    if price_float < 0:
        return ValidationResult(field, False, ValidationLevel.ERROR,
                              f"Price '{price_float}' is negative")
    
    # Check if price is zero
    if price_float == 0:
        return ValidationResult(field, False, ValidationLevel.WARNING,
                              "Price is zero")
    
    # Check typical price ranges based on size
    # These are rough estimates and should be adjusted based on your market
    if size_grams:
        # Define reasonable price ranges per size (in price units per gram)
        # These values should be adjusted based on your market/currency
        price_per_gram = price_float / size_grams
        
        if price_per_gram < 0.01:  # Extremely low price per gram
            return ValidationResult(field, False, ValidationLevel.WARNING,
                                  f"Price '{price_float}' seems unusually low for {size_grams}g")
        
        if price_per_gram > 0.25:  # Extremely high price per gram
            return ValidationResult(field, False, ValidationLevel.WARNING,
                                  f"Price '{price_float}' seems unusually high for {size_grams}g")
    else:
        # If no size provided, do basic sanity checks
        if price_float < 5:  # Extremely low absolute price
            return ValidationResult(field, False, ValidationLevel.WARNING,
                                  f"Price '{price_float}' seems unusually low")
        
        if price_float > 10000:  # Extremely high absolute price
            return ValidationResult(field, False, ValidationLevel.WARNING,
                                  f"Price '{price_float}' seems unusually high")
    
    return ValidationResult(field, True)

def validate_multi_size_prices(coffee: Dict[str, Any]) -> List[ValidationResult]:
    """
    Validate that prices across different sizes make logical sense.
    
    Args:
        coffee: Coffee product dict with price fields
        
    Returns:
        List of ValidationResult objects
    """
    results = []
    
    # Define standard sizes and their weight in grams
    sizes = {
        'price_100g': 100,
        'price_250g': 250,
        'price_500g': 500,
        'price_1kg': 1000
    }
    
    # Add explicit handling for bundles/multi-packs:
    # Some products like "Pack of 2" have prices that won't follow
    # the same per-gram pricing logic
    if coffee.get('is_multipack') or 'pack of' in coffee.get('name', '').lower() or 'multipack' in coffee.get('name', '').lower():
        # Skip strict price validation for multi-packs
        return results
    
    # Calculate price per gram for each size
    price_per_gram = {}
    for price_field, weight in sizes.items():
        if price_field in coffee and coffee[price_field] is not None:
            try:
                price = float(coffee[price_field])
                if price > 0:
                    price_per_gram[price_field] = price / weight
            except (ValueError, TypeError):
                results.append(ValidationResult(price_field, False, ValidationLevel.ERROR,
                                             f"Price '{coffee[price_field]}' is not a valid number"))
    
    # Skip validation if we have fewer than 2 prices to compare
    if len(price_per_gram) < 2:
        return results
    
    # Check that prices follow a logical progression (larger sizes should be cheaper per gram)
    price_fields = sorted(price_per_gram.keys(), key=lambda x: sizes[x])
    
    for i in range(len(price_fields) - 1):
        current_field = price_fields[i]
        next_field = price_fields[i+1]
        
        current_ppg = price_per_gram[current_field]
        next_ppg = price_per_gram[next_field]
        
        # If larger size has higher price per gram
        if next_ppg > current_ppg * 1.05:  # Allow 5% margin for rounding
            results.append(ValidationResult(
                next_field, 
                False, 
                ValidationLevel.WARNING,
                f"{next_field} (₹{coffee[next_field]}/{sizes[next_field]}g) has higher price per gram than " +
                f"{current_field} (₹{coffee[current_field]}/{sizes[current_field]}g)"
            ))
        
        # If larger size has significantly lower price per gram (might be a special promotion)
        if next_ppg < current_ppg * 0.7:  # More than 30% cheaper per gram
            results.append(ValidationResult(
                next_field, 
                False, 
                ValidationLevel.INFO,
                f"{next_field} is significantly cheaper per gram than {current_field} - possible bulk discount or error"
            ))
    
    return results

def validate_flavor_profiles(profiles: List[str]) -> ValidationResult:
    """
    Validate flavor profiles against known flavor vocabulary.
    
    Args:
        profiles: List of flavor profiles to validate
        
    Returns:
        ValidationResult with validation status
    """
    if not profiles:
        return ValidationResult('flavor_profiles', False, ValidationLevel.WARNING,
                              "Flavor profiles are not specified")
    
    # Common known coffee flavor profiles
    known_flavors = {
        "chocolate", "cocoa", "nutty", "nuts", "almond", "hazelnut",
        "caramel", "toffee", "butterscotch", "fruity", "berry", "blueberry", 
        "strawberry", "cherry", "citrus", "lemon", "orange", "lime",
        "floral", "jasmine", "rose", "spice", "cinnamon", "vanilla",
        "earthy", "woody", "tobacco", "cedar", "honey", "maple",
        "malt", "molasses", "stone fruit", "peach", "apricot", "plum",
        "tropical", "pineapple", "mango", "coconut", "apple", "pear",
        "wine", "winey", "grapes", "blackcurrant", "melon", "herbal"
    }
    
    valid_profiles = []
    invalid_profiles = []
    
    for profile in profiles:
        profile_lower = profile.lower().strip()
        if profile_lower in known_flavors:
            valid_profiles.append(profile_lower)
        else:
            # Try to find a close match
            matched = False
            for known in known_flavors:
                if known in profile_lower or profile_lower in known:
                    valid_profiles.append(known)
                    matched = True
                    break
            
            if not matched:
                invalid_profiles.append(profile_lower)
    
    if invalid_profiles:
        return ValidationResult('flavor_profiles', False, ValidationLevel.INFO,
                              f"Unknown flavor profiles: {', '.join(invalid_profiles)}. " +
                              f"Valid profiles: {', '.join(valid_profiles)}",
                              valid_profiles if valid_profiles else None)
    
    return ValidationResult('flavor_profiles', True)

def validate_url(url: str, field_name: str = 'url') -> ValidationResult:
    """
    Validate that a URL is properly formatted.
    
    Args:
        url: URL to validate
        field_name: Name of the field being validated
        
    Returns:
        ValidationResult with validation status
    """
    if not url:
        return ValidationResult(field_name, False, ValidationLevel.WARNING,
                              f"{field_name} is not specified")
    
    # Basic URL validation pattern
    url_pattern = r'^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(/[-\w%!$&\'()*+,;=:]*)*$'
    
    if re.match(url_pattern, url):
        return ValidationResult(field_name, True)
    
    # Try to correct common issues
    corrected_url = url
    
    # Add https:// if missing
    if not corrected_url.startswith('http'):
        corrected_url = 'https://' + corrected_url
        
        # Check if adding the protocol fixed it
        if re.match(url_pattern, corrected_url):
            return ValidationResult(field_name, False, ValidationLevel.INFO,
                                  f"Corrected {field_name} by adding protocol: '{corrected_url}'",
                                  corrected_url)
    
    return ValidationResult(field_name, False, ValidationLevel.WARNING,
                          f"Invalid {field_name}: '{url}'")

def validate_coffee_product(coffee: Dict[str, Any]) -> List[ValidationResult]:
    """
    Validate all fields in a coffee product.
    
    Args:
        coffee: Coffee product dict to validate
        
    Returns:
        List of ValidationResult objects
    """
    results = []
    
    # Required fields
    if 'name' not in coffee or not coffee['name']:
        results.append(ValidationResult('name', False, ValidationLevel.ERROR,
                                      "Product name is required"))
    
    if 'direct_buy_url' not in coffee or not coffee['direct_buy_url']:
        results.append(ValidationResult('direct_buy_url', False, ValidationLevel.ERROR,
                                      "Direct buy URL is required"))
    else:
        results.append(validate_url(coffee['direct_buy_url'], 'direct_buy_url'))
    
    # Optional fields with validation
    if 'roast_level' in coffee:
        results.append(validate_roast_level(coffee['roast_level']))
    
    if 'bean_type' in coffee:
        results.append(validate_bean_type(coffee['bean_type']))
    
    if 'processing_method' in coffee:
        results.append(validate_processing_method(coffee['processing_method']))
    
    if 'flavor_profiles' in coffee:
        results.append(validate_flavor_profiles(coffee['flavor_profiles']))
    
    # Price validations
    price_fields = {
        'price_100g': 100,
        'price_250g': 250,
        'price_500g': 500,
        'price_1kg': 1000
    }
    
    for field, size in price_fields.items():
        if field in coffee and coffee[field] is not None:
            results.append(validate_price(coffee[field], size))
    
    # Multi-size price logic validation
    results.extend(validate_multi_size_prices(coffee))
    
    # Image URL validation
    if 'image_url' in coffee and coffee['image_url']:
        results.append(validate_url(coffee['image_url'], 'image_url'))
    
    return results

def apply_validation_corrections(coffee: Dict[str, Any], results: List[ValidationResult]) -> Dict[str, Any]:
    """
    Apply corrections from validation results to the coffee dict.
    
    Args:
        coffee: Coffee product dict to update
        results: List of validation results
        
    Returns:
        Updated coffee dict with corrections applied
    """
    for result in results:
        if not result.valid and result.corrected_value is not None:
            coffee[result.field] = result.corrected_value
            logger.info(f"Applied correction to {result.field}: {result.message}")
    
    return coffee
