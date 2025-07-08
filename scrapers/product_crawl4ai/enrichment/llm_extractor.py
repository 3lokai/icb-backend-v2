# Simplified LLM Extractor for Coffee Product Enrichment
# =====================================================
# File: scrapers/product_crawl4ai/enrichment/llm_extractor.py

import json
import logging
import re
from typing import Any, Dict, Optional
from urllib.parse import urlparse, quote

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig, LLMConfig as Crawl4AILLMConfig
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


def _validate_and_normalize_url(url: str) -> Optional[str]:
    """
    Validate and normalize URL for Crawl4AI compatibility.
    
    Args:
        url: URL to validate and normalize
        
    Returns:
        Normalized URL if valid, None if invalid
    """
    if not url or not isinstance(url, str):
        return None
    
    url = url.strip()
    if not url:
        return None
    
    try:
        # Parse URL to check if it's valid
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            # Try to add https if no scheme
            if not url.startswith(('http://', 'https://')):
                url = f"https://{url}"
                parsed = urlparse(url)
                if not parsed.netloc:
                    return None
        
        # Normalize URL by encoding special characters in path and query
        if parsed.path:
            # Encode path components that might cause issues
            path_parts = parsed.path.split('/')
            encoded_parts = []
            for part in path_parts:
                if part:
                    # Encode special characters but preserve common ones
                    encoded_part = quote(part, safe='')
                    encoded_parts.append(encoded_part)
                else:
                    encoded_parts.append(part)
            normalized_path = '/'.join(encoded_parts)
        else:
            normalized_path = parsed.path
        
        # Reconstruct URL
        normalized_url = f"{parsed.scheme}://{parsed.netloc}{normalized_path}"
        if parsed.query:
            normalized_url += f"?{parsed.query}"
        if parsed.fragment:
            normalized_url += f"#{parsed.fragment}"
        
        return normalized_url
        
    except Exception as e:
        logger.warning(f"Failed to normalize URL {url}: {e}")
        return None


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
    ]
    for field in simple_fields:
        if field in extracted and extracted[field] and not product.get(field):
            product[field] = extracted[field]
    
    # Handle aroma with standardization
    if "aroma" in extracted and extracted["aroma"] and not product.get("aroma"):
        from ..api_extractors.shopify import standardize_aroma_intensity
        product["aroma"] = standardize_aroma_intensity(extracted["aroma"])

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
    
    # Validate and normalize URL
    normalized_url = _validate_and_normalize_url(product["direct_buy_url"])
    if not normalized_url:
        logger.warning(f"Invalid URL for enrichment: {product.get('direct_buy_url', 'None')} - {product.get('name', 'Unknown')}")
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
            async for result in crawler.arun(url=normalized_url, config=config_simple):
                if result.success and result.extracted_content:
                    try:
                        extracted = json.loads(result.extracted_content)
                        _process_extracted_fields(product, extracted)

                        logger.info(f"Successfully enriched product: {product.get('name', 'Unknown')}")
                        product["deepseek_enriched"] = True
                        break  # Exit after first successful result
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse LLM response: {e}")
                        product["deepseek_enriched"] = False
                else:
                    logger.warning(f"LLM enrichment failed for: {product.get('name', 'Unknown')}")
                    product["deepseek_enriched"] = False

    except Exception as e:
        error_msg = str(e)
        if "Invalid URL" in error_msg:
            logger.error(f"Invalid URL error during enrichment for {product.get('name', 'Unknown')}: {error_msg}")
            logger.error(f"Original URL: {product.get('direct_buy_url', 'None')}")
            logger.error(f"Normalized URL: {normalized_url}")
        else:
            logger.error(f"Error during product enrichment: {e}")
        product["deepseek_enriched"] = False

    return product


async def extract_product_page(url: str, roaster_id: str) -> Optional[Dict[str, Any]]:
    """
    Extract product data from a product page URL.
    IMPROVED VERSION - focuses on core product data only.
    """
    logger.info(f"Extracting product data from URL: {url}")

    # Validate and normalize URL
    normalized_url = _validate_and_normalize_url(url)
    if not normalized_url:
        logger.error(f"Invalid URL for extraction: {url}")
        return None

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
            async for result in crawler.arun(url=normalized_url, config=config_simple):
                # Debug logging
                logger.debug(f"Extraction result for {url}:")
                logger.debug(f"  - Success: {result.success}")
                logger.debug(f"  - Has extracted_content: {bool(result.extracted_content)}")
                logger.debug(f"  - Extracted content length: {len(result.extracted_content) if result.extracted_content else 0}")
                
                if result.extracted_content:
                    logger.debug(f"  - Extracted content preview: {result.extracted_content[:200]}...")

                if result.success and result.extracted_content:
                    try:
                        extracted = json.loads(result.extracted_content)
                        logger.debug(f"  - Parsed JSON successfully: {list(extracted.keys())}")

                        # Get product name (required)
                        product_name = extracted.get("name")
                        if not product_name:
                            logger.warning(f"Could not extract product name from URL {url}")
                            logger.debug(f"  - Available fields: {list(extracted.keys())}")
                            logger.debug(f"  - Full extracted data: {extracted}")
                            return None

                        # Create base product
                        product = {
                            "name": product_name,
                            "slug": slugify(product_name),
                            "roaster_id": roaster_id,
                            "description": extracted.get("description", ""),
                            "direct_buy_url": url,  # Use original URL for storage
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
                        logger.debug(f"  - Raw extracted content: {result.extracted_content}")
                        return None

                # More detailed failure logging
                if not result.success:
                    logger.warning(f"Failed to extract product from {url} - crawler failed")
                    logger.debug(f"  - Error details: {getattr(result, 'error', 'No error details')}")
                elif not result.extracted_content:
                    logger.warning(f"Failed to extract product from {url} - no extracted content")
                    logger.debug(f"  - HTML length: {len(result.html) if result.html else 0}")
                    logger.debug(f"  - Markdown length: {len(result.markdown) if result.markdown else 0}")
                    # Log a snippet of the HTML to see what's available
                    if result.html:
                        logger.debug(f"  - HTML preview: {result.html[:500]}...")
                break  # Exit after first result (success or failure)
            return None

    except Exception as e:
        error_msg = str(e)
        if "Invalid URL" in error_msg:
            logger.error(f"Invalid URL error during extraction: {error_msg}")
            logger.error(f"Original URL: {url}")
            logger.error(f"Normalized URL: {normalized_url}")
        else:
            logger.error(f"Error during product extraction: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Full error details: {str(e)}")
        return None


def get_llm_config() -> Crawl4AILLMConfig:
    """Get LLM configuration - prefer OpenAI GPT-4o Mini, fallback to DeepSeek"""
    openai_key = config.llm.openai_api_key
    if openai_key:
        return Crawl4AILLMConfig(provider="openai/gpt-4o-mini", api_token=openai_key)

    deepseek_key = config.llm.deepseek_api_key
    if deepseek_key:
        return Crawl4AILLMConfig(provider="deepseek", api_token=deepseek_key)

    logger.warning("No LLM API keys found. Extraction will fail.")
    return Crawl4AILLMConfig(provider="openai/gpt-4o-mini", api_token="openai_key")
