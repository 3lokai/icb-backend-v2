# scrapers/product_crawl4ai/extractors/__init__.py
"""
Extractors for coffee product attributes and data.
"""

from scrapers.product_crawl4ai.extractors.attributes import (
    detect_is_seasonal,
    detect_is_single_origin,
    extract_all_attributes,
    extract_bean_type,
    extract_flavor_profiles,
    extract_processing_method,
    extract_roast_level,
)
from scrapers.product_crawl4ai.extractors.normalizers import (
    normalize_boolean_field,
    normalize_coffee_data,
    normalize_coffee_name,
    normalize_flavor_profiles,
    normalize_image_url,
    normalize_price,
    normalize_text,
    standardize_coffee_model,
)
from scrapers.product_crawl4ai.extractors.price import (
    extract_price_from_html,
    extract_weight_from_string,
    process_variants,
    process_woocommerce_variants,
    standardize_price_fields,
    validate_price_logic,
)
from scrapers.product_crawl4ai.extractors.validators import (
    validate_coffee_product,
    validate_price,
)

__all__ = [
    # From attributes.py
    "extract_all_attributes",
    "extract_roast_level",
    "extract_processing_method",
    "extract_bean_type",
    "extract_flavor_profiles",
    "detect_is_single_origin",
    "detect_is_seasonal",
    # From normalizers.py
    "normalize_text",
    "normalize_coffee_name",
    "normalize_price",
    "normalize_image_url",
    "normalize_flavor_profiles",
    "normalize_boolean_field",
    "normalize_coffee_data",
    "standardize_coffee_model",
    # From price.py
    "extract_price_from_html",
    "extract_weight_from_string",
    "process_variants",
    "process_woocommerce_variants",
    "standardize_price_fields",
    "validate_price_logic",
    # From validators.py
    "validate_coffee_product",
    "validate_price",
]
