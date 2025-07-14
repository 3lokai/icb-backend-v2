# Path: scrapers/product/extractors/woocommerce_api_extractor.py

import logging
import re
from typing import Any, Dict, List, Optional, Union

import httpx

from common.pydantic_utils import dict_to_pydantic_model, preprocess_coffee_data
from common.utils import (
    clean_description,
    ensure_absolute_url,
    extract_brew_methods_from_grind_size,
    is_coffee_product,
    slugify,
    standardize_bean_type,
    standardize_processing_method,
    standardize_roast_level,
)
from scrapers.product_crawl4ai.extractors import (
    detect_is_seasonal,
    detect_is_single_origin,
    extract_all_attributes,
    extract_flavor_profiles,
    normalize_coffee_data,
    process_woocommerce_variants,
    standardize_coffee_model,
)
from .shopify import standardize_aroma_intensity
from db.models import Coffee

logger = logging.getLogger(__name__)


def _parse_altitude_string(value_str: Any) -> Optional[int]:
    if isinstance(value_str, int):
        return value_str
    if not isinstance(value_str, str):
        return None
    match = re.search(r"^(\d+)", value_str.strip())
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


def _extract_attributes_from_tags(tags: List[str]) -> Dict[str, Any]:
    """Extracts attributes from tags based on key:value patterns."""
    extracted_attrs = {}
    if not tags:
        return extracted_attrs

    possible_keys_map = {
        "acidity": ["acidity", "acid level"],
        "body": ["body", "mouthfeel"],
        "sweetness": ["sweetness", "sweetness level"],
        "aroma": ["aroma", "fragrance", "scent"],
        "with_milk_suitable": ["milk suitable", "with milk", "suitable for milk"],
        "varietals": ["varietal", "varietals", "cultivar", "bean varietals"],
        "altitude_meters": ["altitude", "elevation", "altitude meters", "masl", "grown at"],
    }

    for tag in tags:
        for field_name, keys in possible_keys_map.items():
            if field_name in extracted_attrs:  # Already found a value for this field
                continue
            for key in keys:
                # Try to match "key: value" or "key : value"
                match = re.match(rf"{re.escape(key)}\s*:\s*(.+)", tag, re.IGNORECASE)
                if match:
                    extracted_attrs[field_name] = match.group(1).strip()
                    break  # Move to the next field_name once a key is matched for it
            if field_name in extracted_attrs:
                continue  # Move to next tag if field_name was populated by inner loop

    return extracted_attrs


async def extract_products_woocommerce(
    base_url: str, roaster_id: str, product_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Extract coffee products from a WooCommerce store using the WP REST API.

    Args:
        base_url: Base URL of the WooCommerce store
        roaster_id: Database ID of the roaster
        product_id: Optional specific product ID to fetch

    Returns:
        List of Coffee Model instances
    """
    # Normalize base URL
    if base_url.endswith("/"):
        base_url = base_url[:-1]

    # Determine the API endpoint - try different common WooCommerce API paths
    api_paths = [
        "/wp-json/wc/store/products",  # WooCommerce Blocks API
        "/wp-json/wc/v3/products",  # WooCommerce REST API
        "/index.php/wp-json/wc/v3/products",  # Alternate path structure
    ]

    woo_products = []

    for path in api_paths:
        if product_id:
            api_url = f"{base_url}{path}/{product_id}"
        else:
            api_url = f"{base_url}{path}?per_page=100"

        logger.info(f"Trying WooCommerce API endpoint: {api_url}")

        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(api_url)

                if response.status_code == 200:
                    data = response.json()

                    # Check if we got a valid response
                    if product_id:
                        # Single product response
                        if isinstance(data, dict) and "id" in data:
                            woo_products = [data]
                            break
                    else:
                        # Multiple products response
                        if isinstance(data, list) and len(data) > 0:
                            woo_products = data
                            break
                else:
                    logger.debug(f"API endpoint {api_url} returned: {response.status_code}")
        except Exception as e:
            logger.debug(f"Error trying API endpoint {api_url}: {e}")
            continue

    if not woo_products:
        logger.warning(f"No products found through WooCommerce API for {base_url}")
        # Try fallback store/products/collection data endpoint
        try:
            api_url = f"{base_url}/wp-json/wc/store/products/collection-data"
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(api_url)

                if response.status_code == 200:
                    data = response.json()
                    if "products" in data and len(data["products"]) > 0:
                        woo_products = data["products"]
                        logger.info(f"Found {len(woo_products)} products via collection-data endpoint")
        except Exception as e:
            logger.debug(f"Error trying collection-data API: {e}")

    # If still no products, try the /products.json endpoint (some WooCommerce sites mimic Shopify)
    if not woo_products:
        try:
            api_url = f"{base_url}/products.json"
            if product_id:
                api_url = f"{base_url}/products/{product_id}.json"

            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(api_url)

                if response.status_code == 200:
                    data = response.json()
                    if product_id and "product" in data:
                        woo_products = [data["product"]]
                    elif "products" in data:
                        woo_products = data["products"]
        except Exception as e:
            logger.debug(f"Error trying products.json endpoint: {e}")

    # Convert to standardized format
    standardized_products = []
    for product in woo_products:
        try:
            # First, check if product is actually coffee
            title = product.get("name", product.get("title", ""))
            product_type = product.get("type", product.get("product_type", ""))
            description = product.get("description", product.get("short_description", ""))
            tags = product.get("tags", [])

            if not is_coffee_product(name=title, description=description, product_type=product_type, tags=tags):
                logger.debug(f"Skipping non-coffee product: {title}")
                continue

            std_product_dict = standardize_woocommerce_product(product, base_url, roaster_id)
            if std_product_dict:
                coffee_model = dict_to_pydantic_model(std_product_dict, Coffee, preprocessor=preprocess_coffee_data)
                if coffee_model:
                    standardized_products.append(coffee_model)
                else:
                    # Fallback to dict if model validation fails
                    logger.warning(f"Validation failed for {std_product_dict.get('name')}, using dict instead")
                    standardized_products.append(std_product_dict)
        except Exception as e:
            logger.error(f"Error standardizing WooCommerce product: {e}", exc_info=True)
            continue

    logger.info(f"Extracted {len(standardized_products)} standardized WooCommerce products")
    return standardized_products


def standardize_woocommerce_product(
    woo_product: Dict[str, Any], base_url: str, roaster_id: str
) -> Optional[Dict[str, Any]]:
    """
    Convert a WooCommerce product to our standardized product schema.

    Args:
        woo_product: Product data from WooCommerce API
        base_url: Base URL of the WooCommerce store
        roaster_id: Database ID of the roaster

    Returns:
        Standardized product dictionary or None if invalid
    """
    # Skip if no name/slug
    name = woo_product.get("name", woo_product.get("title", ""))
    if not name:
        return None

    # Get slug from various possible fields
    slug = woo_product.get("slug", woo_product.get("handle", ""))
    if not slug and "permalink" in woo_product:
        # Try to extract slug from permalink
        permalink = woo_product["permalink"]
        if isinstance(permalink, str):
            slug = permalink.rstrip("/").split("/")[-1]

    # Combine short_description and description for more comprehensive text analysis
    description = ""
    if "short_description" in woo_product and woo_product["short_description"]:
        description += woo_product["short_description"] + " "
    if "description" in woo_product and woo_product["description"]:
        description += woo_product["description"]

    # Clean HTML tags from description
    description = clean_description(description)

    # Create base product - match the Coffee model structure exactly
    product = {
        "name": name,
        "slug": slug or slugify(name),
        "roaster_id": roaster_id,  # This should match the Coffee model field
        "description": description,
        "direct_buy_url": "",
        "image_url": None,
        "is_available": True,
        "is_featured": False,
        "deepseek_enriched": False,
        "product_type": woo_product.get("type", woo_product.get("product_type", "")),  # Add product_type field
        "roast_level": None,
        "bean_type": None,
        "processing_method": None,
        "region_name": None,
        "region_id": None,
        "is_single_origin": None,
        "is_seasonal": None,
        "price_250g": None,  # Add this field to match Coffee model
        "acidity": None,
        "body": None,
        "sweetness": None,
        "aroma": None,
        "with_milk_suitable": None,
        "varietals": None,
        "altitude_meters": None,
        "tags": _process_tags(woo_product.get("tags", [])),
        # Related data fields (not stored directly in DB)
        "prices": [],
        "brew_methods": [],
        "flavor_profiles": [],
        "external_links": [],
        "source": "woocommerce_api",
    }

    # Extract permalink
    if "permalink" in woo_product and woo_product["permalink"]:
        product["direct_buy_url"] = woo_product["permalink"]
    else:
        # Construct URL from slug
        product["direct_buy_url"] = ensure_absolute_url(f"/product/{slug}", base_url)

    # Extract availability
    if "stock_status" in woo_product:
        product["is_available"] = woo_product["stock_status"] == "instock"
    elif "is_in_stock" in woo_product:
        product["is_available"] = woo_product["is_in_stock"]

    # Extract image URL
    if "images" in woo_product and woo_product["images"] and len(woo_product["images"]) > 0:
        if isinstance(woo_product["images"][0], dict) and "src" in woo_product["images"][0]:
            product["image_url"] = woo_product["images"][0]["src"]
        elif isinstance(woo_product["images"][0], str):
            product["image_url"] = woo_product["images"][0]
    elif "image" in woo_product and woo_product["image"]:
        if isinstance(woo_product["image"], dict) and "src" in woo_product["image"]:
            product["image_url"] = woo_product["image"]["src"]
        elif isinstance(woo_product["image"], str):
            product["image_url"] = woo_product["image"]

    # Extract categories as tags
    if "categories" in woo_product and woo_product["categories"]:
        if isinstance(woo_product["categories"], list):
            for category in woo_product["categories"]:
                if isinstance(category, dict) and "name" in category:
                    product["tags"].append(category["name"])
                elif isinstance(category, str):
                    product["tags"].append(category)

    # Use shared extractor for pricing
    product = process_woocommerce_variants(product, woo_product.get("variations", []), confidence_tracking=True)
    
    # Fallback: If no prices found from variants, set price_250g directly from base price
    if not product.get("price_250g"):
        logger.info(f"No structured pricing found for {product['name']}, using base price for price_250g")
        base_price = None
        if "variations" in woo_product and woo_product["variations"]:
            for variation in woo_product["variations"]:
                if variation.get("price") and float(variation["price"]) > 0:
                    base_price = float(variation["price"])
                    break
        elif "price" in woo_product and woo_product["price"]:
            base_price = float(woo_product["price"])
        
        if base_price:
            product["price_250g"] = base_price
            logger.info(f"Set price_250g directly for {product['name']}: {base_price}")
        else:
            logger.warning(f"Failed to extract any prices for {product['name']}")

    # Use shared extractors for comprehensive attribute extraction
    product = extract_all_attributes(
        product,
        product["description"],
        product.get("tags", []),
        woo_product,  # structured_data
        product["name"],
        confidence_tracking=True
    )

    # Extract additional attributes from WooCommerce-specific fields
    if "attributes" in woo_product and woo_product["attributes"]:
        for attr in woo_product["attributes"]:
            attr_name = attr.get("name", "").lower()
            attr_value = attr.get("option", "")
            
            if not attr_value and "options" in attr and attr["options"]:
                if isinstance(attr["options"], list) and len(attr["options"]) > 0:
                    attr_value = attr["options"][0]
                elif isinstance(attr["options"], str):
                    attr_value = attr["options"]

            # Handle WooCommerce-specific attribute mappings
            if attr_value:
                if any(term in attr_name for term in ["varietal", "varietals", "cultivar", "bean varietals"]):
                    raw_varietals = attr_value
                    if isinstance(raw_varietals, str):
                        product["varietals"] = [v.strip() for v in raw_varietals.split(",") if v.strip()]
                    elif isinstance(raw_varietals, list):
                        product["varietals"] = [str(v).strip() for v in raw_varietals if str(v).strip()]
                    elif raw_varietals is not None:  # Handle any other non-None type
                        product["varietals"] = [str(raw_varietals).strip()] if str(raw_varietals).strip() else None
                    else:
                        product["varietals"] = None
                elif any(term in attr_name for term in ["altitude", "elevation", "grown at", "masl"]):
                    product["altitude_meters"] = _parse_altitude_string(attr_value)
                # Extract flavor notes
                elif any(term in attr_name for term in ["flavor", "flavour", "tasting notes", "notes"]):
                    # Split by commas or similar delimiters
                    notes = re.split(r"[,;/&]", attr_value)
                    product["flavor_profiles"] = [note.strip() for note in notes if note.strip()]
                # Extract brewing methods - and check for grind size
                elif any(term in attr_name for term in ["brew", "brewing", "method"]):
                    methods = re.split(r"[,;/&]", attr_value)
                    product["brew_methods"] = [method.strip() for method in methods if method.strip()]
                # NEW: Handle grind size as brewing method
                elif any(term in attr_name for term in ["grind", "grind size", "grind-size"]):
                    brew_methods = extract_brew_methods_from_grind_size(attr_value)
                    if brew_methods:
                        if not product["brew_methods"]:
                            product["brew_methods"] = []
                        for method in brew_methods:
                            if method not in product["brew_methods"]:
                                product["brew_methods"].append(method)
                # Check for single origin indicator
                elif "single origin" in attr_name.lower():
                    product["is_single_origin"] = attr_value.lower() not in ("no", "false", "0")

    # Note: Meta data extraction removed - requires API authentication
    # Meta data fields will be populated through LLM enrichment if needed

    # Extract attributes from tags as a fallback
    tag_extracted_attrs = _extract_attributes_from_tags(product.get("tags", []))

    if product.get("acidity") is None and tag_extracted_attrs.get("acidity"):
        product["acidity"] = tag_extracted_attrs["acidity"]
    if product.get("body") is None and tag_extracted_attrs.get("body"):
        product["body"] = tag_extracted_attrs["body"]
    if product.get("sweetness") is None and tag_extracted_attrs.get("sweetness"):
        product["sweetness"] = tag_extracted_attrs["sweetness"]

    if product.get("aroma") is None and tag_extracted_attrs.get("aroma"):
        # Value from tag is expected to be a string already
        product["aroma"] = standardize_aroma_intensity(tag_extracted_attrs["aroma"])

    if product.get("with_milk_suitable") is None and tag_extracted_attrs.get("with_milk_suitable"):
        raw_milk_from_tag = tag_extracted_attrs["with_milk_suitable"]
        if isinstance(raw_milk_from_tag, str):
            product["with_milk_suitable"] = raw_milk_from_tag.lower() in ["true", "yes", "1", "suitable"]
        # Note: boolean directly from regex match is not typical, usually string

    if product.get("varietals") is None and tag_extracted_attrs.get("varietals"):
        raw_varietals = tag_extracted_attrs["varietals"]
        if isinstance(raw_varietals, str):
            product["varietals"] = [v.strip() for v in raw_varietals.split(",") if v.strip()]
        elif isinstance(raw_varietals, list):
            product["varietals"] = [str(v).strip() for v in raw_varietals if str(v).strip()]
        elif raw_varietals is not None:  # Handle any other non-None type
            product["varietals"] = [str(raw_varietals).strip()] if str(raw_varietals).strip() else None
        else:
            product["varietals"] = None

    if product.get("altitude_meters") is None and tag_extracted_attrs.get("altitude_meters"):
        product["altitude_meters"] = _parse_altitude_string(tag_extracted_attrs["altitude_meters"])

    # Use shared extractors for flavor profiles if not already set
    if not product.get("flavor_profiles"):
        flavor_profiles, _ = extract_flavor_profiles(
            product["description"], product.get("tags", []), woo_product
        )
        if flavor_profiles:
            product["flavor_profiles"] = flavor_profiles
        else:
            product["flavor_profiles"] = []

    # Extract brew methods from description
    if not product.get("brew_methods"):
        product["brew_methods"] = extract_brew_methods(product["description"])

    # Use shared extractors for single origin and seasonal detection if not set
    if product["is_single_origin"] is None:
        is_single_origin, _ = detect_is_single_origin(
            product["name"], product["description"], product.get("tags", [])
        )
        product["is_single_origin"] = is_single_origin

    if product["is_seasonal"] is None:
        is_seasonal, _ = detect_is_seasonal(
            product["name"], product["description"], product.get("tags", [])
        )
        product["is_seasonal"] = is_seasonal

    # Look for estate mentions in tags or product name/description
    estates = extract_estates(product["name"], product["description"], product.get("tags", []))
    if estates:
        product["estates"] = estates
        # Add estates to tags if not already there
        for estate in estates:
            estate_tag = f"estate:{estate}"
            if estate_tag not in product["tags"]:
                product["tags"].append(estate_tag)

    return product


def _process_tags(tags: Union[List[Dict[str, str]], List[str], str]) -> List[str]:
    """Process tags from WooCommerce to standardized format."""
    result = []

    if isinstance(tags, str):
        # Split comma-separated string
        result = [tag.strip() for tag in tags.split(",") if tag.strip()]
    elif isinstance(tags, list):
        for tag in tags:
            if isinstance(tag, dict) and "name" in tag:
                result.append(tag["name"].strip())
            elif isinstance(tag, str):
                result.append(tag.strip())

    return result


# Removed duplicate functions - now using shared extractors


def extract_coffee_metadata_from_description(description: str) -> dict:
    """
    Extract coffee metadata from product description text.
    Many coffee sites include structured information in the description.

    Args:
        description: Product description text

    Returns:
        Dictionary with extracted metadata
    """
    if not description:
        return {}

    metadata = {}

    # Common patterns in coffee descriptions
    patterns = [
        # Region/Origin patterns
        (r"region\s*:?\s*([^\.,:;\n]+)", "region_name"),
        (r"origin\s*:?\s*([^\.,:;\n]+)", "region_name"),
        (r"from\s+([^\.,:;\n]+)", "region_name"),  # e.g. "from Ethiopia"
        # Elevation patterns
        (r"elevation\s*:?\s*([^\.,:;\n]+)", "elevation"),
        (r"altitude\s*:?\s*([^\.,:;\n]+)", "elevation"),
        (r"grown at\s+([^\.,:;\n]+)", "elevation"),
        # Roast level patterns - improved to handle "Roast Profile : Light Roast" format
        (r"roast\s+(?:level|profile)\s*:?\s*([^\.,:;\n]+)", "roast_level"),
        (r"([^\.,:;\n]+)\s+roast", "roast_level"),
        # Bean type patterns - improved to handle "Variety : Arabica" format
        (r"(?:bean|variety)\s+type\s*:?\s*([^\.,:;\n]+)", "bean_type"),
        (r"variety\s*:?\s*([^\.,:;\n]+)", "bean_type"),
        # Processing method patterns - improved to handle "pulp-sundried" and other formats
        (r"process(?:ing)?\s+(?:method)?\s*:?\s*([^\.,:;\n]+)", "processing_method"),
        (r"(?:washed|natural|honey|pulped|anaerobic|monsooned|wet-hulled|pulp-sundried)", "processing_method"),
        # Flavor notes patterns
        (r"(?:flavor|tasting)\s+notes\s*:?\s*([^\.,:;\n]+)", "flavor_notes"),
        (r"notes\s+of\s+([^\.,:;\n]+)", "flavor_notes"),
    ]

    for pattern, key in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            # Extract either the full match (for direct matches) or the capture group
            value = match.group(1) if len(match.groups()) > 0 else match.group(0)
            if value and (key not in metadata or not metadata[key]):
                metadata[key] = value.strip()

    # Special case for detecting single origin
    if re.search(r"single\s*(?:origin|estate|farm|producer)", description, re.IGNORECASE):
        metadata["is_single_origin"] = True
    elif re.search(r"blend", description, re.IGNORECASE):
        metadata["is_single_origin"] = False

    # Special case for detecting seasonal offerings
    if re.search(r"(?:seasonal|limited|special|edition|harvest)", description, re.IGNORECASE):
        metadata["is_seasonal"] = True

    # Special case for direct bean type detection if not found by patterns
    if "bean_type" not in metadata:
        if re.search(r"\b(?:variety|type)\s*:?\s*(arabica)\b", description, re.IGNORECASE):
            metadata["bean_type"] = "arabica"
        elif re.search(r"\b(?:variety|type)\s*:?\s*(robusta)\b", description, re.IGNORECASE):
            metadata["bean_type"] = "robusta"
        elif re.search(r"\b(?:variety|type)\s*:?\s*(liberica)\b", description, re.IGNORECASE):
            metadata["bean_type"] = "liberica"
        elif re.search(r"\b(arabica)\b", description, re.IGNORECASE) and not re.search(r"\b(robusta|liberica)\b", description, re.IGNORECASE):
            metadata["bean_type"] = "arabica"
        elif re.search(r"\b(robusta)\b", description, re.IGNORECASE) and not re.search(r"\b(arabica|liberica)\b", description, re.IGNORECASE):
            metadata["bean_type"] = "robusta"
        elif re.search(r"\b(liberica)\b", description, re.IGNORECASE) and not re.search(r"\b(arabica|robusta)\b", description, re.IGNORECASE):
            metadata["bean_type"] = "liberica"

    # Special case for direct roast level detection if not found by patterns
    if "roast_level" not in metadata:
        if re.search(r"\b(?:roast\s+(?:level|profile))\s*:?\s*(light)\b", description, re.IGNORECASE):
            metadata["roast_level"] = "light"
        elif re.search(r"\b(?:roast\s+(?:level|profile))\s*:?\s*(medium)\b", description, re.IGNORECASE):
            metadata["roast_level"] = "medium"
        elif re.search(r"\b(?:roast\s+(?:level|profile))\s*:?\s*(dark)\b", description, re.IGNORECASE):
            metadata["roast_level"] = "dark"
        elif re.search(r"\b(light)\s+roast\b", description, re.IGNORECASE):
            metadata["roast_level"] = "light"
        elif re.search(r"\b(medium)\s+roast\b", description, re.IGNORECASE):
            metadata["roast_level"] = "medium"
        elif re.search(r"\b(dark)\s+roast\b", description, re.IGNORECASE):
            metadata["roast_level"] = "dark"

    # Special case for processing method detection if not found by patterns
    if "processing_method" not in metadata:
        if re.search(r"\b(pulp-sundried)\b", description, re.IGNORECASE):
            metadata["processing_method"] = "pulped-natural"
        elif re.search(r"\b(monsooned)\b", description, re.IGNORECASE):
            metadata["processing_method"] = "monsooned"
        elif re.search(r"\b(washed)\b", description, re.IGNORECASE):
            metadata["processing_method"] = "washed"
        elif re.search(r"\b(natural)\b", description, re.IGNORECASE):
            metadata["processing_method"] = "natural"
        elif re.search(r"\b(honey)\b", description, re.IGNORECASE):
            metadata["processing_method"] = "honey"

    return metadata


# Removed duplicate pricing functions - now using shared extractors


# Removed duplicate flavor profiles and brew methods functions - now using shared extractors


def extract_brew_methods(description: str) -> List[str]:
    """Extract recommended brewing methods from product description."""
    brew_methods = [
        "espresso",
        "filter",
        "pour over",
        "pourover",
        "french press",
        "aeropress",
        "cold brew",
        "moka pot",
        "siphon",
        "chemex",
        "drip",
        "v60",
        "hario v60",
        "kalita",
        "clever dripper",
        "immersion",
        "percolator",
        "turkish",
        "ibrik",
        "south indian filter",
        "vietnamese press",
    ]

    found_methods = []

    # Check for phrases like "perfect for X" or "ideal for Y"
    recommendation_patterns = [
        r"(?:perfect|ideal|great|excellent|recommended)\s+for\s+([A-Za-z0-9,\s&+]+)",
        r"(?:best\s+(?:when\s+)?(?:brewed|prepared|made))\s+(?:as|with|using)?\s+([A-Za-z0-9,\s&+]+)",
        r"(?:recommended|suggested)\s+(?:brewing\s+)?method:?\s+([A-Za-z0-9,\s&+:]+)",
    ]

    for pattern in recommendation_patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            # Split the matched text into individual methods
            methods_text = match.group(1).lower()
            # Replace common separators with commas
            methods_text = re.sub(r"\s+and\s+", ",", methods_text)
            methods_text = re.sub(r"\s*[&+]\s*", ",", methods_text)
            methods_text = re.sub(r"\s*:\s*", ",", methods_text)

            # Split by comma and clean up
            potential_methods = [m.strip() for m in methods_text.split(",")]
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
            pattern = r"\b" + re.escape(method) + r"\b"
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
        if "estate" in tag_lower:
            # Extract the estate name
            estate_name = None
            if ":" in tag:
                estate_name = tag.split(":", 1)[1].strip()
            elif "-" in tag:
                estate_name = tag.split("-", 1)[1].strip()
            elif " " in tag:
                # Take everything after "estate"
                parts = tag_lower.split("estate", 1)
                if len(parts) > 1 and parts[1].strip():
                    estate_name = parts[1].strip()

            if estate_name and estate_name not in estates:
                estates.append(estate_name)

    # Check product name for estate mentions
    estate_patterns = [
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+Estate",  # Attikan Estate
        r"Estate\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",  # Estate of Attikan
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Estate|Estates|Farm|Plantation)",  # Matches any ending
    ]

    for pattern in estate_patterns:
        matches = re.finditer(pattern, name, re.IGNORECASE)
        for match in matches:
            estate_name = match.group(1).strip()
            if estate_name and estate_name not in estates:
                estates.append(estate_name)

    # Check description similarly
    desc_matches = re.finditer(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+Estate", description, re.IGNORECASE)
    for match in desc_matches:
        estate_name = match.group(1).strip()
        if estate_name and estate_name not in estates:
            estates.append(estate_name)

    return estates


# --- Enhanced roast level extraction ---
def extract_roast_level_from_woocommerce(woo_product: Dict[str, Any], tags: List[str]) -> str:
    """Extract roast level from tags, slug, or title, using standardizer directly."""
    # First check tags for direct roast level indications
    for tag in tags:
        tag_lower = tag.lower()
        if "roast" in tag_lower:
            # Pass to standardizer directly
            return standardize_roast_level(tag_lower)

    # Check slug for roast level mentions
    slug = woo_product.get("slug", "").lower()
    if "roast" in slug:
        return standardize_roast_level(slug)

    # Check title for explicit roast mentions
    title = woo_product.get("name", "").lower()
    if "roast" in title:
        return standardize_roast_level(title)

    # At this point, let's check for specific keywords in any of these sources
    sources = [" ".join(tags), slug, title]
    for source in sources:
        if any(keyword in source.lower() for keyword in ["light", "medium", "dark", "espresso", "filter"]):
            return standardize_roast_level(source)

    # Fallback to the regular attribute extraction method
    return standardize_roast_level(
        extract_attribute_from_woocommerce(woo_product, "roast_level", ["roast", "roast level", "roast-level"])
    )


# --- Enhanced processing method extraction ---
def extract_processing_method_from_woocommerce(
    woo_product: Dict[str, Any], tags: List[str], name: str, slug: str
) -> str:
    """Extract processing method from tags, slug, or name, using standardizer directly."""
    # Check tags for processing method terms
    for tag in tags:
        tag_lower = tag.lower()
        if any(term in tag_lower for term in ["process", "washed", "natural", "honey", "anaerobic", "ferment"]):
            return standardize_processing_method(tag_lower)

    # Check product slug and name
    if any(term in slug.lower() for term in ["washed", "natural", "honey", "anaerobic"]):
        return standardize_processing_method(slug)

    if any(term in name.lower() for term in ["washed", "natural", "honey", "anaerobic"]):
        return standardize_processing_method(name)

    # Combine and check all sources for key processing terms
    all_text = f"{' '.join(tags)} {slug} {name}".lower()
    process_terms = ["washed", "natural", "honey", "pulped", "anaerobic", "monsooned", "wet-hulled", "carbonic"]
    if any(term in all_text for term in process_terms):
        return standardize_processing_method(all_text)

    # Fall back to regular attribute extraction
    return standardize_processing_method(
        extract_attribute_from_woocommerce(woo_product, "processing_method", ["process", "processing", "processing-method"])
    )


def extract_attribute_from_woocommerce(woo_product: Dict[str, Any], field_name: str, possible_keys: List[str]) -> Optional[str]:
    """
    Extract attribute value from WooCommerce product attributes or options.
    Similar to Shopify's extract_attribute function.

    Args:
        woo_product: Product data from WooCommerce API
        field_name: Field name to extract
        possible_keys: List of possible key names to match

    Returns:
        Attribute value if found, None otherwise
    """
    # Check attributes first
    if "attributes" in woo_product and woo_product["attributes"]:
        for attr in woo_product["attributes"]:
            if not isinstance(attr, dict):
                continue
            attr_name = attr.get("name", "").lower()
            if any(possible_key in attr_name for possible_key in possible_keys):
                attr_value = attr.get("option", "")
                if not attr_value and "options" in attr and attr["options"]:
                    if isinstance(attr["options"], list) and len(attr["options"]) > 0:
                        attr_value = attr["options"][0]
                    elif isinstance(attr["options"], str):
                        attr_value = attr["options"]
                if attr_value:
                    return attr_value

    # Check tags for specific attributes, including key:value patterns
    if woo_product.get("tags"):
        tags = _process_tags(woo_product["tags"])
        for tag in tags:
            tag_lower = tag.lower()
            # Check for key:value pattern
            if ":" in tag_lower:
                tag_key, tag_value = tag_lower.split(":", 1)
                tag_key = tag_key.strip()
                if any(possible_key == tag_key for possible_key in possible_keys):
                    return tag_value.strip()

            # Original tag check (if key is just part of the tag)
            for key_search in possible_keys:
                if key_search in tag_lower:
                    # Attempt to extract value if tag is like "roast level light"
                    parts = tag_lower.split(key_search)
                    if len(parts) > 1 and parts[1].strip():
                        # Clean up common separators if it's not a key:value pair
                        value_part = parts[1].strip().replace("-", " ").replace(":", "").strip()
                        if value_part:
                            return value_part

    # Check product type as fallback for some fields
    product_type = woo_product.get("type", "").lower()

    # Extract roast level from product type
    if field_name == "roast_level":
        roast_patterns = ["light", "medium", "dark", "espresso", "filter", "omniroast"]
        for level in roast_patterns:
            if level in product_type:
                return level

    # Try to extract from description for key attributes
    description = woo_product.get("description", "").lower()

    # Common patterns for attributes in descriptions
    patterns = {
        "roast_level": [
            r"(light|medium|dark)(?:\s+roast)",
            r"roast(?:ed)?\s+(?:to\s+)?(?:a\s+)?(light|medium|dark)",
            r"(light|medium|dark)\s+roasted",
            r"roast\s+(?:level|profile)\s*:?\s*(light|medium|dark)",
        ],
        "bean_type": [
            r"(arabica|robusta|liberica)(?:\s+beans?)",
            r"(?:100%\s+)?(arabica|robusta|liberica)",
            r"(single\s+origin)",
            r"(?:a\s+)?(blend)",
            r"variety\s*:?\s*(arabica|robusta|liberica)",
        ],
        "processing_method": [
            r"(washed|natural|honey|pulped\s+natural|anaerobic)(?:\s+process)",
            r"process(?:ed)?\s+(?:using\s+)?(?:the\s+)?(washed|natural|honey|pulped\s+natural|anaerobic)",
            r"(pulp-sundried)",
        ],
        "region_name": [r"(?:grown|cultivated|produced|harvested)\s+in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"],
    }

    if field_name in patterns:
        for pattern in patterns[field_name]:
            match = re.search(pattern, description)
            if match:
                return match.group(1)

    return None
