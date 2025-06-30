# Simplified LLM Extractor for Coffee Product Enrichment
# =====================================================
# File: scrapers/product_crawl4ai/enrichment/llm_extractor.py

import json
import logging
import re
from typing import Any, Dict, Optional

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy

from common.utils import slugify
from config import config

logger = logging.getLogger(__name__)

# Complete schema for all coffee fields (simplified structure)
COFFEE_COMPLETE_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "description": "Product name"},
        "price": {"type": "number", "description": "Price in local currency"},
        "description": {"type": "string", "description": "Product description"},
        "roast_level": {"type": "string", "enum": ["light", "medium", "dark", "medium-dark", "french", "unknown"]},
        "bean_type": {"type": "string", "enum": ["arabica", "robusta", "blend", "arabica-robusta", "unknown"]},
        "processing_method": {"type": "string", "enum": ["washed", "natural", "honey", "monsooned", "pulp-sun-dried", "unknown"]},
        "region_name": {"type": "string", "description": "Coffee origin region"},
        "is_single_origin": {"type": "boolean", "description": "True if single origin, false if blend"},
        "flavor_notes": {"type": "string", "description": "Comma-separated flavor notes"},
        # Advanced coffee characteristics
        "acidity": {"type": "string", "description": "Acidity level (bright, medium, low, etc.)"},
        "body": {"type": "string", "description": "Body/mouthfeel (light, medium, full, etc.)"},
        "sweetness": {"type": "string", "description": "Sweetness level (high, medium, low, etc.)"},
        "aroma": {"type": "string", "description": "Aroma description"},
        "with_milk_suitable": {"type": "boolean", "description": "Suitable for milk drinks"},
        "varietals": {"type": "string", "description": "Coffee varietals (comma-separated)"},
        "altitude_meters": {"type": "string", "description": "Growing altitude (e.g. '1500m' or '1200-1800m')"},
        "brew_methods": {"type": "string", "description": "Recommended brew methods (comma-separated)"},
    },
}


def _process_extracted_fields(product: Dict, extracted: Dict) -> None:
    """Process and normalize extracted fields from LLM (shared logic)"""

    # Handle flavor profiles (convert string to list)
    if "flavor_notes" in extracted and extracted["flavor_notes"]:
        if isinstance(extracted["flavor_notes"], str):
            product["flavor_profiles"] = [note.strip() for note in extracted["flavor_notes"].split(",") if note.strip()]
        elif isinstance(extracted["flavor_notes"], list):
            product["flavor_profiles"] = extracted["flavor_notes"]

    # Copy simple string fields (only if not already present)
    simple_fields = [
        "roast_level",
        "bean_type",
        "processing_method",
        "region_name",
        "acidity",
        "body",
        "sweetness",
        "aroma",
    ]
    for field in simple_fields:
        if field in extracted and extracted[field] and not product.get(field):
            product[field] = extracted[field]

    # Handle boolean fields (only if not already present)
    if (
        "is_single_origin" in extracted
        and extracted["is_single_origin"] is not None
        and product.get("is_single_origin") is None
    ):
        product["is_single_origin"] = extracted["is_single_origin"]

    if (
        "with_milk_suitable" in extracted
        and extracted["with_milk_suitable"] is not None
        and product.get("with_milk_suitable") is None
    ):
        if isinstance(extracted["with_milk_suitable"], str):
            val_lower = extracted["with_milk_suitable"].lower()
            product["with_milk_suitable"] = val_lower in ["true", "yes", "1", "suitable"]
        else:
            product["with_milk_suitable"] = bool(extracted["with_milk_suitable"])

    # Handle varietals (convert string to list)
    if "varietals" in extracted and extracted["varietals"] and not product.get("varietals"):
        if isinstance(extracted["varietals"], str):
            product["varietals"] = [v.strip() for v in extracted["varietals"].split(",") if v.strip()]
        elif isinstance(extracted["varietals"], list):
            product["varietals"] = extracted["varietals"]

    # Handle altitude (convert to integer)
    if "altitude_meters" in extracted and extracted["altitude_meters"] and product.get("altitude_meters") is None:
        alt_val = extracted["altitude_meters"]
        if isinstance(alt_val, str):
            # Extract first number from string like "1500m" or "1200-1800m"
            match = re.search(r"(\d+)", alt_val)
            if match:
                try:
                    product["altitude_meters"] = int(match.group(1))
                except ValueError:
                    pass
        elif isinstance(alt_val, (int, float)):
            product["altitude_meters"] = int(alt_val)

    # Handle brew methods (convert string to list)
    if "brew_methods" in extracted and extracted["brew_methods"] and not product.get("brew_methods"):
        if isinstance(extracted["brew_methods"], str):
            methods = [method.strip() for method in extracted["brew_methods"].split(",") if method.strip()]
            # Normalize common brew method names
            normalized_methods = []
            for method in methods:
                method_lower = method.lower()
                if "espresso" in method_lower:
                    normalized_methods.append("espresso")
                elif "pour over" in method_lower or "pourover" in method_lower:
                    normalized_methods.append("pour over")
                elif "french press" in method_lower:
                    normalized_methods.append("french press")
                elif "aeropress" in method_lower:
                    normalized_methods.append("aeropress")
                elif "moka pot" in method_lower:
                    normalized_methods.append("moka pot")
                elif "drip" in method_lower:
                    normalized_methods.append("drip")
                elif "cold brew" in method_lower:
                    normalized_methods.append("cold brew")
                elif "turkish" in method_lower:
                    normalized_methods.append("turkish")
                else:
                    normalized_methods.append(method)
            product["brew_methods"] = normalized_methods
        elif isinstance(extracted["brew_methods"], list):
            product["brew_methods"] = extracted["brew_methods"]


async def enrich_coffee_product(product: Dict[str, Any], roaster_name: str) -> Dict[str, Any]:
    """
    Enrich a coffee product with missing details using LLM extraction.
    IMPROVED VERSION - only extracts fields that are still missing after attribute extraction.
    """
    # Skip if no URL
    if not product.get("direct_buy_url"):
        logger.warning(f"Cannot enrich product without URL: {product.get('name', 'Unknown')}")
        product["deepseek_enriched"] = False
        return product

    # Check which fields are missing (including advanced fields)
    all_fields = [
        "roast_level",
        "bean_type",
        "processing_method",
        "region_name",
        "flavor_profiles",
        "acidity",
        "body",
        "sweetness",
        "aroma",
        "with_milk_suitable",
        "varietals",
        "altitude_meters",
        "brew_methods",
    ]
    missing_fields = [field for field in all_fields if not product.get(field)]

    # Skip if no fields need enrichment
    if not missing_fields:
        logger.debug(f"No fields need enrichment for: {product.get('name', 'Unknown')}")
        product["deepseek_enriched"] = False
        return product

    logger.info(f"Enriching product {product.get('name', 'Unknown')} - missing: {missing_fields}")

    try:
        # Create a focused schema for only missing fields
        focused_schema = {
            "type": "object",
            "properties": {field: COFFEE_COMPLETE_SCHEMA["properties"][field] for field in missing_fields}
        }

        # Simple LLM extraction strategy
        llm_strategy = LLMExtractionStrategy(
            llm_config=get_llm_config(),
            schema=focused_schema,
            extraction_type="schema",
            instruction=f"""
            Extract these missing coffee details: {", ".join(missing_fields)}.
            
            Look for:
            - Basic: roast level, bean type, processing method, origin region
            - Characteristics: acidity, body, sweetness levels  
            - Details: aroma, varietals, growing altitude
            - Flavor notes: any taste descriptions
            - Milk compatibility: good for lattes/cappuccinos?
            - Brew methods: recommended brewing techniques
            
            Only fill fields you're confident about. Use 'unknown' if unsure.
            For varietals, list specific varieties like 'Bourbon, Typica'.
            For altitude, include numbers like '1500' or '1200-1800'.
            For brew methods, list common methods like 'espresso, pour over, french press'.
            """,
            input_format="markdown",
            chunk_token_threshold=5000,  # Increased for more fields
            apply_chunking=True,
            extra_args={"temperature": 0.1},
        )

        # Simple crawler config - no JS, no complex processing
        config_simple = CrawlerRunConfig(
            extraction_strategy=llm_strategy,
            page_timeout=30000,  # 30 seconds max
            cache_mode=CacheMode.ENABLED,  # Use cache to save costs
        )

        # Run the crawler
        async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
            result = await crawler.arun(url=product["direct_buy_url"], config=config_simple)

            if result.success and result.extracted_content:
                try:
                    extracted = json.loads(result.extracted_content)
                    _process_extracted_fields(product, extracted)

                    logger.info(f"Successfully enriched product: {product.get('name', 'Unknown')}")
                    product["deepseek_enriched"] = True
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse LLM response: {e}")
                    product["deepseek_enriched"] = False
            else:
                logger.warning(f"LLM enrichment failed for: {product.get('name', 'Unknown')}")
                product["deepseek_enriched"] = False

    except Exception as e:
        logger.error(f"Error during product enrichment: {e}")
        product["deepseek_enriched"] = False

    return product


async def extract_product_page(url: str, roaster_id: str) -> Optional[Dict[str, Any]]:
    """
    Extract product data from a product page URL.
    IMPROVED VERSION - focuses on core product data only.
    """
    logger.info(f"Extracting product data from URL: {url}")

    try:
        # Simple extraction strategy
        llm_strategy = LLMExtractionStrategy(
            llm_config=get_llm_config(),
            schema=COFFEE_COMPLETE_SCHEMA,
            extraction_type="schema",
            instruction="""
            Extract complete coffee product details from this page.
            
            Look for:
            - Basic info: name, price, description
            - Coffee basics: roast level, bean type, processing method, origin
            - Characteristics: acidity, body, sweetness, aroma
            - Details: varietals, altitude, milk compatibility
            - Flavor notes: tasting notes and flavor descriptions
            - Brew methods: recommended brewing techniques
            
            Only include information clearly stated on the page.
            For varietals, list specific varieties like 'Bourbon, Typica'.
            For altitude, include numbers like '1500m' or '1200-1800masl'.
            For brew methods, list common methods like 'espresso, pour over, french press'.
            """,
            input_format="markdown",
            chunk_token_threshold=5000,
            apply_chunking=True,
            extra_args={"temperature": 0.1},
        )

        # Simple crawler config
        config_simple = CrawlerRunConfig(
            extraction_strategy=llm_strategy, page_timeout=30000, cache_mode=CacheMode.ENABLED
        )

        # Run the crawler
        async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
            result = await crawler.arun(url=url, config=config_simple)

            if result.success and result.extracted_content:
                try:
                    extracted = json.loads(result.extracted_content)

                    # Get product name (required)
                    product_name = extracted.get("name")
                    if not product_name:
                        logger.warning(f"Could not extract product name from URL {url}")
                        return None

                    # Create base product
                    product = {
                        "name": product_name,
                        "slug": slugify(product_name),
                        "roaster_id": roaster_id,
                        "description": extracted.get("description", ""),
                        "direct_buy_url": url,
                        "is_available": True,
                        "prices": [],
                        "source": "crawl4ai_extraction",
                    }

                    # Process price if available
                    if extracted.get("price"):
                        price = extracted["price"]
                        # Default to 250g if no size specified
                        product["prices"].append({"size_grams": 250, "price": price})

                    # Process extracted fields
                    _process_extracted_fields(product, extracted)

                    logger.info(f"Successfully extracted product: {product_name}")
                    return product

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse extracted content: {e}")
                    return None

            logger.warning(f"Failed to extract product from {url}")
            return None

    except Exception as e:
        logger.error(f"Error during product extraction: {e}")
        return None


def get_llm_config() -> LLMConfig:
    """Get LLM configuration - prefer DeepSeek, fallback to OpenAI"""
    deepseek_key = config.llm.deepseek_api_key
    if deepseek_key:
        return LLMConfig(provider="deepseek/deepseek-chat", api_token=deepseek_key)

    openai_key = config.llm.openai_api_key
    if openai_key:
        return LLMConfig(provider="openai/gpt-4o-mini", api_token=openai_key)

    logger.warning("No LLM API keys found. Extraction will fail.")
    return LLMConfig(provider="openai/gpt-4o-mini", api_token="")
