# scrapers/product/extractors/__init__.py
"""
Extractors for coffee product attributes and data.
"""

from scrapers.product.extractors.price import (
    process_variants, 
    extract_weight_from_string,
    process_woocommerce_variants,
    extract_price_from_html,
    validate_price_logic,
    standardize_price_fields
)

from scrapers.product.extractors.attributes import (
    extract_roast_level,
    extract_bean_type,
    extract_processing_method,
    extract_flavor_profiles,
    detect_is_single_origin,
    detect_is_seasonal,
    extract_all_attributes
)

from scrapers.product.extractors.normalizers import (
    normalize_text,
    create_slug,
    normalize_coffee_name,
    normalize_price,
    normalize_image_url,
    normalize_flavor_profiles,
    normalize_boolean_field,
    normalize_coffee_data,
    standardize_coffee_model
)

from scrapers.product.extractors.validators import (
    ValidationLevel,
    ValidationResult,
    validate_roast_level,
    validate_bean_type,
    validate_processing_method,
    validate_price,
    validate_multi_size_prices,
    validate_flavor_profiles,
    validate_url,
    validate_coffee_product,
    apply_validation_corrections
)

__all__ = [
    # From price.py
    'process_variants', 
    'extract_weight_from_string',
    'process_woocommerce_variants',
    'extract_price_from_html',
    'validate_price_logic',
    'standardize_price_fields',
    
    # From attributes.py
    'extract_roast_level',
    'extract_bean_type',
    'extract_processing_method',
    'extract_flavor_profiles',
    'detect_is_single_origin',
    'detect_is_seasonal',
    'extract_all_attributes',
    
    # From normalizers.py
    'normalize_text',
    'create_slug',
    'normalize_coffee_name',
    'normalize_price',
    'normalize_image_url',
    'normalize_flavor_profiles',
    'normalize_boolean_field',
    'normalize_coffee_data',
    'standardize_coffee_model',
    
    # From validators.py
    'ValidationLevel',
    'ValidationResult',
    'validate_roast_level',
    'validate_bean_type',
    'validate_processing_method',
    'validate_price',
    'validate_multi_size_prices',
    'validate_flavor_profiles',
    'validate_url',
    'validate_coffee_product',
    'apply_validation_corrections'
]