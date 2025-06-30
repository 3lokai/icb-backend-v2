# scrapers/product/extractors/price.py
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def process_variants(
    coffee: Dict[str, Any], product: Dict[str, Any], confidence_tracking: bool = True
) -> Dict[str, Any]:
    """
    Process product variants to extract pricing information.

    Args:
        coffee: The coffee product dictionary to update
        product: The raw product data containing variants
        confidence_tracking: Whether to track confidence scores

    Returns:
        Updated coffee dictionary with pricing information
    """
    variants = product.get("variants", [])
    if not variants:
        return coffee

    # Extract all weight/price pairs with confidence
    weight_prices = []

    for variant in variants:
        variant_title = variant.get("title", "").lower()
        price = float(variant.get("price", 0))

        # Skip if no price
        if price <= 0:
            continue

        # Try multiple patterns for weight extraction
        weight_grams, confidence = extract_weight_from_string(variant_title)

        if weight_grams:
            weight_prices.append((weight_grams, price, confidence))
        else:
            # Try backup strategies for weights
            option_values = []
            for option in product.get("options", []):
                if option.get("name", "").lower() in ["size", "weight", "amount", "quantity"]:
                    option_values.extend(option.get("values", []))

            # Check if this variant has an option index
            position = variant.get("position", 0) - 1
            if 0 <= position < len(option_values):
                weight_grams, confidence = extract_weight_from_string(option_values[position])
                if weight_grams:
                    weight_prices.append((weight_grams, price, confidence))

    # Sort by weight ascending
    weight_prices.sort(key=lambda x: x[0])

    # Track confidence by field
    confidence_scores = {}

    # Map to our standardized weight categories
    for weight_grams, price, confidence in weight_prices:
        if weight_grams <= 100:
            coffee["price_100g"] = price
            confidence_scores["price_100g"] = confidence
        elif weight_grams <= 200:
            coffee["price_200g"] = price
            confidence_scores["price_200g"] = confidence
        elif weight_grams <= 250:
            coffee["price_250g"] = price
            confidence_scores["price_250g"] = confidence
        elif weight_grams <= 500:
            coffee["price_500g"] = price
            confidence_scores["price_500g"] = confidence
        elif weight_grams <= 750:
            coffee["price_750g"] = price
            confidence_scores["price_750g"] = confidence
        elif weight_grams <= 1000:
            coffee["price_1kg"] = price
            confidence_scores["price_1kg"] = confidence
        else:
            coffee["price_2kg"] = price
            confidence_scores["price_2kg"] = confidence

    # Handle multi-packs (e.g., "2 x 250g")
    if not weight_prices:
        for variant in variants:
            variant_title = variant.get("title", "").lower()
            price = float(variant.get("price", 0))

            # Skip if no price
            if price <= 0:
                continue

            multi_match = re.search(r"(\d+)\s*x\s*(\d+\.?\d*)\s*(g|gram|gm|kg)", variant_title)
            if multi_match:
                pack_count = int(multi_match.group(1))
                weight_value = float(multi_match.group(2))
                weight_unit = multi_match.group(3).lower()

                # Convert to grams
                if "kg" in weight_unit:
                    weight_grams = int(weight_value * 1000)
                else:
                    weight_grams = int(weight_value)

                # For multipacks, calculate price per pack
                single_price = price / pack_count

                # Store as a single price with special flag
                if weight_grams <= 100:
                    coffee["price_100g"] = single_price
                    coffee["is_multipack"] = True
                    coffee["pack_count"] = pack_count
                    confidence_scores["price_100g"] = 0.9  # High confidence for explicit declaration
                elif weight_grams <= 250:
                    coffee["price_250g"] = single_price
                    coffee["is_multipack"] = True
                    coffee["pack_count"] = pack_count
                    confidence_scores["price_250g"] = 0.9
                elif weight_grams <= 500:
                    coffee["price_500g"] = single_price
                    coffee["is_multipack"] = True
                    coffee["pack_count"] = pack_count
                    confidence_scores["price_500g"] = 0.9
                else:
                    coffee["price_1kg"] = single_price
                    coffee["is_multipack"] = True
                    coffee["pack_count"] = pack_count
                    confidence_scores["price_1kg"] = 0.9

                break

    # If no variant has detected weight, use first variant price as default 250g with low confidence
    if not any(k in coffee for k in ["price_100g", "price_250g", "price_500g", "price_1kg"]) and variants:
        coffee["price_250g"] = float(variants[0].get("price", 0))
        confidence_scores["price_250g"] = 0.3  # Low confidence for default assumption

        # Validate prices make logical sense (larger sizes should never be cheaper per gram)
        coffee = validate_price_logic(coffee)

    # Add confidence scores if tracking enabled
    if confidence_tracking and confidence_scores:
        if "confidence_scores" not in coffee:
            coffee["confidence_scores"] = {}
        coffee["confidence_scores"].update(confidence_scores)

    return coffee


def extract_weight_from_string(text: str) -> Tuple[Optional[int], float]:
    """
    Extract weight in grams from text string with confidence score.

    Args:
        text: String to extract weight from

    Returns:
        Tuple of (weight_in_grams, confidence_score)
    """
    if not text:
        return None, 0.0

    # Pattern 1: Standard format (e.g., "250g", "250 grams", "0.25kg")
    # This is the most reliable
    match = re.search(r"(\d+\.?\d*)\s*(g|gram|gm|kg|grams)", text.lower())
    if match:
        weight_value = float(match.group(1))
        weight_unit = match.group(2).lower()

        # Convert to grams
        if "kg" in weight_unit:
            weight_grams = int(weight_value * 1000)
        else:
            weight_grams = int(weight_value)

        return weight_grams, 0.9  # High confidence for standard format

    # Pattern 2: Number followed by weight indicator
    match = re.search(r"(\d+\.?\d*)\s*(?:size|weight|pack)", text.lower())
    if match:
        # Try to infer if this is grams by the magnitude
        weight_value = float(match.group(1))
        if 100 <= weight_value <= 1000:
            # Likely grams
            return int(weight_value), 0.7  # Medium confidence

    # Pattern 3: Common coffee sizes in the name
    common_sizes = {
        "quarter pound": 113,
        "half pound": 227,
        "one pound": 454,
        "1 pound": 454,
        "1 lb": 454,
        "1lb": 454,
        "half kilo": 500,
        "one kilo": 1000,
        "1 kilo": 1000,
        "1 kg": 1000,
        "1kg": 1000,
    }

    for size_text, weight in common_sizes.items():
        if size_text in text.lower():
            return weight, 0.8  # Good confidence for named sizes

    # Pattern 4: Size indicators without units (used when we know we're dealing with sizes)
    if text.strip() in ["250", "500", "1000"]:
        return int(text.strip()), 0.6  # Medium-low confidence

    return None, 0.0


def process_woocommerce_variants(
    coffee: Dict[str, Any], variations: List[Dict[str, Any]], confidence_tracking: bool = True
) -> Dict[str, Any]:
    """
    Process WooCommerce product variations to extract pricing.

    Args:
        coffee: The coffee product dictionary to update
        variations: List of product variations
        confidence_tracking: Whether to track confidence scores

    Returns:
        Updated coffee dictionary with pricing information
    """
    if not variations:
        return coffee

    # Extract all weight/price pairs with confidence
    weight_prices = []
    confidence_scores = {}

    for variation in variations:
        # Skip if not available
        if not variation.get("purchasable", True):
            continue

        # Get price
        price = 0
        try:
            price = float(variation.get("price", variation.get("regular_price", 0)))
        except (ValueError, TypeError):
            continue

        if price <= 0:
            continue

        # Get weight from attributes
        attributes = variation.get("attributes", [])
        weight_grams = None
        confidence = 0.0

        for attr in attributes:
            attr_name = attr.get("name", "").lower()
            attr_value = attr.get("option", "")

            if any(term in attr_name for term in ["weight", "size", "amount"]):
                weight_grams, confidence = extract_weight_from_string(attr_value)
                if weight_grams:
                    break

        # If no weight found in attributes, try variation name
        if not weight_grams:
            weight_grams, confidence = extract_weight_from_string(variation.get("name", ""))

        # If weight found, add to our list
        if weight_grams:
            weight_prices.append((weight_grams, price, confidence))

    # Sort by weight ascending
    weight_prices.sort(key=lambda x: x[0])

    # Map to our standardized weight categories
    for weight_grams, price, confidence in weight_prices:
        if weight_grams <= 100:
            coffee["price_100g"] = price
            confidence_scores["price_100g"] = confidence
        elif weight_grams <= 200:
            coffee["price_200g"] = price
            confidence_scores["price_200g"] = confidence
        elif weight_grams <= 250:
            coffee["price_250g"] = price
            confidence_scores["price_250g"] = confidence
        elif weight_grams <= 500:
            coffee["price_500g"] = price
            confidence_scores["price_500g"] = confidence
        elif weight_grams <= 750:
            coffee["price_750g"] = price
            confidence_scores["price_750g"] = confidence
        elif weight_grams <= 1000:
            coffee["price_1kg"] = price
            confidence_scores["price_1kg"] = confidence
        else:
            coffee["price_2kg"] = price
            confidence_scores["price_2kg"] = confidence

    # If no variant has detected weight, use first variant price as default 250g
    if not any(k in coffee for k in ["price_100g", "price_250g", "price_500g", "price_1kg"]) and variations:
        try:
            price = float(variations[0].get("price", variations[0].get("regular_price", 0)))
            if price > 0:
                coffee["price_250g"] = price
                confidence_scores["price_250g"] = 0.3  # Low confidence for default assumption
        except (ValueError, TypeError):
            pass

    # Add confidence scores if tracking enabled
    if confidence_tracking and confidence_scores:
        if "confidence_scores" not in coffee:
            coffee["confidence_scores"] = {}
        coffee["confidence_scores"].update(confidence_scores)

    return coffee


def extract_price_from_html(coffee: Dict[str, Any], html: str, confidence_tracking: bool = True) -> Dict[str, Any]:
    """
    Extract price information from HTML content.

    Args:
        coffee: The coffee product dictionary to update
        html: HTML content to extract prices from
        confidence_tracking: Whether to track confidence scores

    Returns:
        Updated coffee dictionary with pricing information
    """
    confidence_scores = {}

    # Try to find price
    price_patterns = [
        (r'<span class="woocommerce-Price-amount amount">\s*<[^>]*>\s*[^<]*</[^>]*>\s*([0-9,.]+)', 0.8),
        (r'<p[^>]*class="[^"]*price[^"]*"[^>]*>\s*<span[^>]*>\s*<[^>]*>\s*[^<]*</[^>]*>\s*([0-9,.]+)', 0.75),
        (r'<span[^>]*id="price[^"]*"[^>]*>\s*<[^>]*>\s*([0-9,.]+)', 0.7),
        (r'data-product_price="([0-9,.]+)"', 0.75),
        (r'<span[^>]*class="[^"]*price[^"]*"[^>]*>\s*(?:<[^>]*>\s*)?([0-9,.]+)', 0.7),
        (r'<div[^>]*class="[^"]*price[^"]*"[^>]*>\s*(?:<[^>]*>\s*)?([0-9,.]+)', 0.65),
    ]

    for pattern, confidence in price_patterns:
        match = re.search(pattern, html, re.DOTALL)
        if match:
            try:
                price = float(match.group(1).replace(",", ""))
                if price > 0:
                    # Default to 250g price if no weight information
                    coffee["price_250g"] = price
                    confidence_scores["price_250g"] = confidence
                    break
            except ValueError:
                continue

    # Try to extract weight-specific prices
    weight_price_map = extract_weight_price_map_from_html(html)

    if weight_price_map:
        for weight_grams, price, confidence in weight_price_map:
            if weight_grams <= 100:
                coffee["price_100g"] = price
                confidence_scores["price_100g"] = confidence
            elif weight_grams <= 250:
                coffee["price_250g"] = price
                confidence_scores["price_250g"] = confidence
            elif weight_grams <= 500:
                coffee["price_500g"] = price
                confidence_scores["price_500g"] = confidence
            else:
                coffee["price_1kg"] = price
                confidence_scores["price_1kg"] = confidence

    # Add confidence scores if tracking enabled
    if confidence_tracking and confidence_scores:
        if "confidence_scores" not in coffee:
            coffee["confidence_scores"] = {}
        coffee["confidence_scores"].update(confidence_scores)

    return coffee


def extract_weight_price_map_from_html(html: str) -> List[Tuple[int, float, float]]:
    """
    Extract weight and price information from HTML content.

    Args:
        html: HTML content to extract from

    Returns:
        List of tuples (weight_in_grams, price, confidence)
    """
    weight_prices = []

    # Extraction strategy 1: Find variation form or table
    variation_blocks = []

    # Pattern for WooCommerce variations table
    table_match = re.search(r'<table[^>]*class="[^"]*variations[^"]*"[^>]*>(.*?)</table>', html, re.DOTALL)
    if table_match:
        variation_blocks.append(table_match.group(1))

    # Pattern for general variation form
    form_match = re.search(r'<form[^>]*class="[^"]*variations_form[^"]*"[^>]*>(.*?)</form>', html, re.DOTALL)
    if form_match:
        variation_blocks.append(form_match.group(1))

    # Process each variation block
    for block in variation_blocks:
        # Try to find weight options and associated prices
        options = re.findall(r'<option[^>]*value="([^"]*)"[^>]*>([^<]+)', block)

        for value, label in options:
            # Skip empty or default options
            if not value or value.lower() == "choose an option":
                continue

            # Extract weight from label
            weight_grams, confidence = extract_weight_from_string(label)

            if not weight_grams:
                continue

            # Try to find price for this option
            price_match = re.search(rf'data-value="{re.escape(value)}"[^>]*>.*?([0-9,.]+)', block, re.DOTALL)
            if price_match:
                try:
                    price = float(price_match.group(1).replace(",", ""))
                    if price > 0:
                        weight_prices.append((weight_grams, price, confidence))
                except ValueError:
                    continue

    # Extraction strategy 2: Find radio buttons
    radio_patterns = re.findall(
        r'<input[^>]*type="radio"[^>]*value="([^"]*)"[^>]*>[^<]*([^<]+).*?([0-9,.]+)', html, re.DOTALL
    )

    for value, label, price_str in radio_patterns:
        # Extract weight from label
        weight_grams, confidence = extract_weight_from_string(label)

        if weight_grams:
            try:
                price = float(price_str.replace(",", ""))
                if price > 0:
                    weight_prices.append((weight_grams, price, confidence))
            except ValueError:
                continue

    # Extraction strategy 3: Find product options list
    option_list = re.search(r'<ul[^>]*class="[^"]*product-options[^"]*"[^>]*>(.*?)</ul>', html, re.DOTALL)
    if option_list:
        list_items = re.findall(r"<li[^>]*>(.*?)</li>", option_list.group(1), re.DOTALL)

        for item in list_items:
            # Try to find weight and price in the same list item
            weight_match = re.search(r"(\d+\.?\d*)\s*(g|gram|gm|kg)", item.lower())
            price_match = re.search(r"(?:[\$₹€£]|rs\.?)\s*([0-9,.]+)", item.lower())

            if weight_match and price_match:
                weight_value = float(weight_match.group(1))
                weight_unit = weight_match.group(2).lower()

                # Convert to grams
                if "kg" in weight_unit:
                    weight_grams = int(weight_value * 1000)
                else:
                    weight_grams = int(weight_value)

                try:
                    price = float(price_match.group(1).replace(",", ""))
                    if price > 0:
                        weight_prices.append((weight_grams, price, 0.7))  # Medium confidence for list extraction
                except ValueError:
                    continue

    return weight_prices


def validate_price_logic(coffee: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that prices make logical sense (larger sizes should never be cheaper per gram).
    Corrects illogical prices or flags them for review.

    Args:
        coffee: The coffee product dictionary to validate

    Returns:
        Validated coffee dictionary
    """
    # Define standard weights for calculations
    weights = {
        "price_100g": 100,
        "price_200g": 200,
        "price_250g": 250,
        "price_500g": 500,
        "price_750g": 750,
        "price_1kg": 1000,
        "price_2kg": 2000,
    }

    # Calculate price per gram for each size
    price_per_gram = {}
    for price_key, weight in weights.items():
        if price_key in coffee and coffee[price_key] > 0:
            price_per_gram[price_key] = coffee[price_key] / weight

    # Check if we have multiple prices to compare
    if len(price_per_gram) < 2:
        return coffee

    # Sort by weight (ascending order)
    sorted_prices = sorted(price_per_gram.items(), key=lambda x: weights[x[0]])

    # Check for logical inconsistencies (smaller package should have higher price per gram)
    issues = []
    for i in range(len(sorted_prices) - 1):
        current_key, current_ppm = sorted_prices[i]
        next_key, next_ppm = sorted_prices[i + 1]

        # If larger size is more expensive per gram than smaller size
        if next_ppm > current_ppm * 1.1:  # Allow a small margin for rounding errors
            issues.append((next_key, weights[next_key], next_ppm))
            # Log the issue for analysis
            logger.warning(
                f"Price inconsistency: {weights[next_key]}g pack has higher price per gram than {weights[current_key]}g pack"
            )

    # If issues were found, add a flag to the coffee object
    if issues:
        coffee["price_inconsistencies"] = True

    return coffee


def standardize_price_fields(coffee: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure all price fields use consistent naming and format.

    Args:
        coffee: The coffee product dictionary to standardize

    Returns:
        Standardized coffee dictionary
    """
    # Handle legacy field names
    field_mapping = {
        "price_100": "price_100g",
        "price_200": "price_200g",
        "price_250": "price_250g",
        "price_500": "price_500g",
        "price_750": "price_750g",
        "price_1000": "price_1kg",
        "price_2000": "price_2kg",
    }

    for old_field, new_field in field_mapping.items():
        if old_field in coffee and old_field != new_field:
            coffee[new_field] = coffee[old_field]
            del coffee[old_field]

    # Calculate price_250g equivalent if it's missing but other sizes are present
    if "price_250g" not in coffee:
        # Try to derive from closest weight
        if "price_200g" in coffee:
            # 1.25x the 200g price as the most reliable estimate
            coffee["price_250g"] = coffee["price_200g"] * 1.25
            if "confidence_scores" in coffee:
                coffee["confidence_scores"]["price_250g"] = coffee["confidence_scores"].get("price_200g", 0.7) * 0.9
        elif "price_500g" in coffee:
            # Half the 500g price
            coffee["price_250g"] = coffee["price_500g"] / 2
            if "confidence_scores" in coffee:
                coffee["confidence_scores"]["price_250g"] = coffee["confidence_scores"].get("price_500g", 0.7) * 0.8
        elif "price_100g" in coffee:
            # 2.5x the 100g price
            coffee["price_250g"] = coffee["price_100g"] * 2.5
            if "confidence_scores" in coffee:
                coffee["confidence_scores"]["price_250g"] = coffee["confidence_scores"].get("price_100g", 0.7) * 0.7
        elif "price_750g" in coffee:
            # One-third of the 750g price
            coffee["price_250g"] = coffee["price_750g"] / 3
            if "confidence_scores" in coffee:
                coffee["confidence_scores"]["price_250g"] = coffee["confidence_scores"].get("price_750g", 0.7) * 0.7
        elif "price_1kg" in coffee:
            # Quarter the 1kg price
            coffee["price_250g"] = coffee["price_1kg"] / 4
            if "confidence_scores" in coffee:
                coffee["confidence_scores"]["price_250g"] = coffee["confidence_scores"].get("price_1kg", 0.7) * 0.7
        elif "price_2kg" in coffee:
            # Eighth of the 2kg price
            coffee["price_250g"] = coffee["price_2kg"] / 8
            if "confidence_scores" in coffee:
                coffee["confidence_scores"]["price_250g"] = coffee["confidence_scores"].get("price_2kg", 0.7) * 0.6

    return coffee
