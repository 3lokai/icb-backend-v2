# LLM Extractor for Coffee Product Enrichment
# ==========================================
# File: scrapers/product_crawl4ai/enrichment/llm_extractor.py

import os
import json
import re
import logging
from typing import Dict, List, Optional, Any
import asyncio
from bs4 import BeautifulSoup

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from .schema import CoffeeProductSchema
from config import config  # Import the main config object
from common.utils import create_slug # Ensure create_slug is imported

logger = logging.getLogger(__name__)

async def enrich_coffee_product(product: Dict[str, Any], roaster_name: str) -> Dict[str, Any]:
    """
    Enrich a coffee product with missing details using LLM extraction.
    
    Args:
        product: Product dictionary with basic info
        roaster_name: Name of the roaster (for logging)
        
    Returns:
        Enriched product dictionary
    """
    # Skip if no direct_buy_url
    if not product.get('direct_buy_url'):
        logger.warning(f"Cannot enrich product without URL: {product.get('name', 'Unknown')}")
        return product
    
    # Check which fields are missing
    potential_enrichment_fields = [
        'roast_level', 'bean_type', 'processing_method', 'region_name', 'flavor_profiles',
        'acidity', 'body', 'sweetness', 'aroma', 
        'with_milk_suitable', 'varietals', 'altitude_meters'
    ]
    missing_fields = []
    for field in potential_enrichment_fields:
        # Consider a field missing if it's None or an empty list (for list types like varietals, flavor_profiles)
        value = product.get(field)
        if value is None or (isinstance(value, list) and not value):
            missing_fields.append(field)
    
    # Skip if no fields need enrichment
    if not missing_fields:
        logger.debug(f"No fields need enrichment for: {product.get('name', 'Unknown')}")
        return product
    
    logger.info(f"Enriching product {product.get('name', 'Unknown')} with missing fields: {missing_fields}")
    
    try:
        # JS to help with product page interactions
        js_code = """
        // Helper to try clicking on elements safely
        function tryClick(selector) {
            const elements = document.querySelectorAll(selector);
            for (const el of elements) {
                try { el.click(); } catch(e) {}
            }
        }
        // Expand any collapsed sections
        tryClick('.collapsible, .toggle, .accordion, .tab');
        // Force image loading
        const images = document.querySelectorAll('img[data-src], img[loading="lazy"]');
        for (const img of images) {
            if (img.dataset.src) img.src = img.dataset.src;
        }
        // Extract product name directly
        const productName = (() => {
            const selectors = [
                'h1.page-title', 'h1.product-title', '.product_title', 
                'h1', '.product-single__title', '.product-title'
            ];
            for (const sel of selectors) {
                const el = document.querySelector(sel);
                if (el) return el.innerText.trim();
            }
            return '';
        })();
        // Scroll to ensure lazy loaded elements appear
        window.scrollTo(0, document.body.scrollHeight);
        setTimeout(() => window.scrollTo(0, 0), 500);
        
        return { productName };
        """

        # Configure content filter
        content_filter = PruningContentFilter(
            threshold=0.35,
            threshold_type="dynamic",
            min_word_threshold=5
        )
        
        md_generator = DefaultMarkdownGenerator(
            content_filter=content_filter
        )
        
        # Prepare LLM extraction
        llm_strategy = LLMExtractionStrategy(
            llm_config=get_llm_config(),
            schema=CoffeeProductSchema.model_json_schema(),
            extraction_type="schema",
            instruction=f"""
            Extract coffee product details from this page.
            Focus on these missing fields: {', '.join(missing_fields)}.
            Only fill fields you're confident about based on the content.
            Look for:
            1. Product name (usually in a heading or title)
            2. Price (look for currency symbols and numerical values)
            3. Description (longer text explaining the coffee)
            4. Roast level (light, medium, dark, etc.)
            5. Bean type (arabica, robusta, or blend)
            6. Processing method (washed, natural, honey, etc.)
            7. Origin region or country
            8. Whether it's single origin or a blend
            9. Flavor notes (tasting notes, flavor profile)
            Additionally, try to find:
            10. Acidity: The perceived acidity (e.g., bright, mellow, low).
            11. Body: The mouthfeel (e.g., light, medium, full, syrupy).
            12. Sweetness: The perceived sweetness (e.g., honey-like, caramel).
            13. Aroma: The fragrance (e.g., floral, nutty, spicy). This can be a list or a comma-separated string.
            14. Suitability with Milk: Is it recommended for milk (true/false)?
            15. Varietals: Specific coffee varietals (e.g., Typica, Bourbon) as a list or comma-separated string.
            16. Altitude in Meters: Growing altitude (e.g., 1500, '1200-1800masl').
            For price, extract the main/default price option.
            For package size, look for weight in grams (typically 250g, 1kg, etc.).
            Only include information you find on the page - don't guess missing values.
            """,
            input_format="html",  # Switch to HTML for more complete data
            chunk_token_threshold=6000,  # Increase for better context
            apply_chunking=True,
            extra_args={"temperature": 0.1}
        )
        
        # Configure crawler with JS execution and longer timeout
        config = CrawlerRunConfig(
            markdown_generator=md_generator,
            extraction_strategy=llm_strategy,
            js_code=js_code,
            wait_for_images=True,
            remove_overlay_elements=True,
            page_timeout=60000,  # 60 second timeout
            cache_mode=CacheMode.BYPASS  # Don't use cache during debugging
        )
        
        # Run the crawler
        async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
            result = await crawler.arun(url=product['direct_buy_url'], config=config)
            
            # Extract product name from JS result
            js_product_name = ""
            if hasattr(result, 'js_result') and result.js_result and isinstance(result.js_result, dict):
                js_product_name = result.js_result.get('productName', '')
            
            if result.success and result.extracted_content:
                # Parse the extracted data
                extracted = json.loads(result.extracted_content)
                
                # Update product with extracted fields
                for field in missing_fields:
                    if field in extracted and extracted[field]:
                        product[field] = extracted[field]
                
                # Handle flavor profiles separately (list field)
                if 'flavor_notes' in extracted and extracted['flavor_notes']:
                    # If string, split into list
                    if isinstance(extracted['flavor_notes'], str):
                        product['flavor_profiles'] = [note.strip() for note in extracted['flavor_notes'].split(',')]
                    # If already a list, use directly
                    elif isinstance(extracted['flavor_notes'], list):
                        product['flavor_profiles'] = extracted['flavor_notes']

                # Post-processing for new fields
                new_fields_map = {
                    'acidity': 'acidity', 'body': 'body', 'sweetness': 'sweetness',
                    'with_milk_suitable': 'with_milk_suitable'
                    # varietals, aroma, altitude_meters are handled separately due to potential type conversion
                }
                for schema_key, product_key in new_fields_map.items():
                    if product.get(product_key) is None: # Check if field is currently None
                        if schema_key in extracted and extracted[schema_key] is not None:
                            # Type conversion for with_milk_suitable if LLM returns string
                            if product_key == 'with_milk_suitable' and isinstance(extracted[schema_key], str):
                                val_lower = extracted[schema_key].lower()
                                if val_lower in ['true', 'yes', '1', 'suitable']:
                                    product[product_key] = True
                                elif val_lower in ['false', 'no', '0', 'unsuitable']:
                                    product[product_key] = False
                                else:
                                    product[product_key] = None # Or log warning
                            elif product_key == 'with_milk_suitable' and isinstance(extracted[schema_key], int):
                                product[product_key] = bool(extracted[schema_key]) # Handle 0 or 1
                            else:
                                product[product_key] = extracted[schema_key]

                # Varietals processing
                if not product.get('varietals'): # Check if field is None or empty list
                    if 'varietals' in extracted and extracted['varietals']:
                        raw_varietals = extracted['varietals']
                        processed_varietals = []
                        if isinstance(raw_varietals, str):
                            processed_varietals = [v.strip() for v in raw_varietals.split(',') if v.strip()]
                        elif isinstance(raw_varietals, list):
                            processed_varietals = [str(v).strip() for v in raw_varietals if str(v).strip()]
                        
                        if processed_varietals: # Only assign if we got some varietals
                            product['varietals'] = processed_varietals
                        elif product.get('varietals') is None : # Ensure it's None if LLM gives empty and was None
                             product['varietals'] = None


                # Aroma processing
                if product.get('aroma') is None: # Check if field is currently None
                    if 'aroma' in extracted and extracted['aroma']:
                        aroma_data = extracted['aroma']
                        processed_aroma = None
                        if isinstance(aroma_data, list):
                            processed_aroma = ', '.join(filter(None, [str(a).strip() for a in aroma_data]))
                        elif isinstance(aroma_data, str):
                            processed_aroma = aroma_data.strip()
                        elif aroma_data is not None: # boolean or number from LLM
                            processed_aroma = str(aroma_data)
                        
                        if processed_aroma: # Assign only if there's actual content
                            product['aroma'] = processed_aroma
                        # else product['aroma'] remains None
                
                # Altitude_meters processing
                if product.get('altitude_meters') is None: # Check if field is currently None
                    if 'altitude_meters' in extracted and extracted['altitude_meters'] is not None:
                        alt_val = extracted['altitude_meters']
                        parsed_alt = None
                        if isinstance(alt_val, str):
                            match = re.search(r'^(\d+)', alt_val.strip())
                            if match:
                                try:
                                    parsed_alt = int(match.group(1))
                                except ValueError:
                                    logger.warning(f"Could not convert altitude_meters '{match.group(1)}' to int for {product.get('name')}")
                            else:
                                logger.warning(f"Could not parse altitude_meters string '{alt_val}' for {product.get('name')}")
                        elif isinstance(alt_val, int):
                            parsed_alt = alt_val
                        else: # Other types
                            try:
                                parsed_alt = int(alt_val)
                            except (ValueError, TypeError):
                                logger.warning(f"Could not convert altitude_meters type '{type(alt_val)}' to int for {product.get('name')}")
                        
                        if parsed_alt is not None:
                            product['altitude_meters'] = parsed_alt
                
                logger.info(f"Successfully enriched product: {product.get('name', 'Unknown')}")
            else:
                logger.warning(f"Failed to enrich product: {result.error_message if not result.success else 'No extracted content'}")
    
    except Exception as e:
        logger.error(f"Error during product enrichment: {e}")
    
    return product

async def extract_product_page(url: str, roaster_id: str) -> Optional[Dict[str, Any]]:
    """
    Extract product data from a product page URL.
    Used for both static sites and as a fallback for API extraction.
    
    Args:
        url: Product page URL
        roaster_id: Database ID of the roaster
        
    Returns:
        Product dictionary or None if extraction failed
    """
    logger.info(f"Extracting product data from URL: {url}")
    
    try:
        # JS to help with product page interactions
        js_code = """
        // Helper to try clicking on elements safely
        function tryClick(selector) {
            const elements = document.querySelectorAll(selector);
            for (const el of elements) {
                try { el.click(); } catch(e) {}
            }
        }
        // Expand any collapsed sections
        tryClick('.collapsible, .toggle, .accordion, .tab');
        // Force image loading
        const images = document.querySelectorAll('img[data-src], img[loading="lazy"]');
        for (const img of images) {
            if (img.dataset.src) img.src = img.dataset.src;
        }
        // Extract product name directly
        const productName = (() => {
            const selectors = [
                'h1.page-title', 'h1.product-title', '.product_title', 
                'h1', '.product-single__title', '.product-title'
            ];
            for (const sel of selectors) {
                const el = document.querySelector(sel);
                if (el) return el.innerText.trim();
            }
            return '';
        })();
        // Scroll to ensure lazy loaded elements appear
        window.scrollTo(0, document.body.scrollHeight);
        setTimeout(() => window.scrollTo(0, 0), 500);
        
        return { productName };
        """

        # Configure content filter
        content_filter = PruningContentFilter(
            threshold=0.35,
            threshold_type="dynamic",
            min_word_threshold=5
        )
        
        md_generator = DefaultMarkdownGenerator(
            content_filter=content_filter
        )
        
        # Prepare LLM extraction
        llm_strategy = LLMExtractionStrategy(
            llm_config=get_llm_config(),
            schema=CoffeeProductSchema.model_json_schema(),
            extraction_type="schema",
            instruction="""
            Extract complete coffee product details from this page.
            
            Look for:
            1. Product name (usually in a heading or title)
            2. Price (look for currency symbols and numerical values)
            3. Description (longer text explaining the coffee)
            4. Roast level (light, medium, dark, etc.)
            5. Bean type (arabica, robusta, or blend)
            6. Processing method (washed, natural, honey, etc.)
            7. Origin region or country
            8. Whether it's single origin or a blend
            9. Flavor notes (tasting notes, flavor profile)
            10. Acidity: The perceived acidity (e.g., bright, mellow, low).
            11. Body: The mouthfeel (e.g., light, medium, full, syrupy).
            12. Sweetness: The perceived sweetness (e.g., honey-like, caramel).
            13. Aroma: The fragrance (e.g., floral, nutty, spicy). This can be a list or a comma-separated string.
            14. Suitability with Milk: Is it recommended for milk (true/false)?
            15. Varietals: Specific coffee varietals (e.g., Typica, Bourbon) as a list or comma-separated string.
            16. Altitude in Meters: Growing altitude (e.g., 1500, '1200-1800masl').
            
            For price, extract the main/default price option.
            For package size, look for weight in grams (typically 250g, 1kg, etc.).
            
            Only include information you find on the page - don't guess missing values.
            """,
            input_format="html",  # Switch to HTML for more complete data
            chunk_token_threshold=6000,  # Increase for better context
            apply_chunking=True,
            extra_args={"temperature": 0.1}
        )
        
        # Configure crawler with JS execution and longer timeout
        config = CrawlerRunConfig(
            markdown_generator=md_generator,
            extraction_strategy=llm_strategy,
            js_code=js_code,
            wait_for_images=True,
            remove_overlay_elements=True,
            page_timeout=60000,  # 60 second timeout
            cache_mode=CacheMode.BYPASS  # Don't use cache during debugging
        )
        
        # Run the crawler
        async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
            result = await crawler.arun(url=url, config=config)
            
            # Extract product name from JS result first
            js_product_name = ""
            if hasattr(result, 'js_result') and result.js_result and isinstance(result.js_result, dict):
                js_product_name = result.js_result.get('productName', '')
                logger.debug(f"Extracted product name from JS: {js_product_name}")
            
            # Direct HTML parsing as fallback
            extracted_title = ""
            extracted_description = ""
            if result.html:
                soup = BeautifulSoup(result.html, 'html.parser')
                
                # Extract title using BeautifulSoup
                title_elem = soup.find('h1')
                if title_elem:
                    extracted_title = title_elem.get_text().strip()
                else:
                    # Try title tag
                    title_tag = soup.find('title')
                    if title_tag:
                        page_title = title_tag.get_text().strip()
                        # Remove site name if present
                        extracted_title = re.sub(r'\s+[-|]\s+.*$', '', page_title)
                
                # Extract description
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc and meta_desc.get('content'):
                    extracted_description = meta_desc.get('content')
                
                # Try product description div
                if not extracted_description:
                    desc_div = soup.find('div', class_=lambda c: c and any(x in c for x in [
                        'product-description', 'description', 'product-details'
                    ]))
                    if desc_div:
                        extracted_description = desc_div.get_text().strip()
                
                # Extract image URL
                product_image = None
                # Try og:image first
                og_image = soup.find('meta', property='og:image')
                if og_image and og_image.get('content'):
                    product_image = og_image.get('content')
                
                # Try product image tag
                if not product_image:
                    main_image = soup.find('img', class_=lambda c: c and any(x in c for x in [
                        'product-image', 'main-image', 'featured-image'
                    ]))
                    if main_image and main_image.get('src'):
                        product_image = main_image.get('src')
            
            # Now try to extract product data from LLM
            if result.success and result.extracted_content:
                try:
                    # Parse the extracted data
                    extracted = json.loads(result.extracted_content)
                    # Log the raw extraction for debugging
                    logger.debug(f"Raw LLM extraction for {url}: {json.dumps(extracted, indent=2)}")

                    # Handle case where LLM returns a list instead of a dictionary
                    if isinstance(extracted, list):
                        # Use the first item if it's a list of objects
                        if extracted and isinstance(extracted[0], dict):
                            extracted = extracted[0]
                        else:
                            logger.warning(f"LLM returned unexpected list format for URL {url}")
                            # Here instead of returning None, we'll fallback to direct HTML parsing
                    
                    # Prioritize name extraction in this order:
                    # 1. JS extraction (most reliable)
                    # 2. LLM extraction 
                    # 3. Direct HTML parsing
                    # 4. URL-based name
                    product_name = js_product_name or extracted.get('name') or extracted_title or os.path.basename(url).replace('.html', '').replace('-', ' ').title()
                    
                    # Skip if we still couldn't get a product name
                    if not product_name:
                        logger.warning(f"Could not extract product name from URL {url}")
                        return None
                    
                    # Create base product dictionary
                    product = {
                        'name': product_name,
                        'slug': create_slug(product_name), # Replaced call
                        'roaster_id': roaster_id,
                        'description': extracted.get('description') or extracted_description or "",
                        'direct_buy_url': url,
                        'image_url': extracted.get('image_url') or product_image,
                        'roast_level': extracted.get('roast_level'),
                        'bean_type': extracted.get('bean_type'),
                        'processing_method': extracted.get('processing_method'),
                        'region_name': extracted.get('region_name'),
                        'is_seasonal': None,
                        'is_single_origin': extracted.get('is_single_origin'),
                        'is_available': True,
                        'prices': [],
                        'source': 'crawl4ai_extraction'
                    }
                    
                    # Process price information
                    price = extracted.get('price')
                    if price:
                        # Extract numeric price
                        if isinstance(price, str):
                            price_match = re.search(r'[\d,.]+', price)
                            if price_match:
                                price = float(price_match.group(0).replace(',', ''))
                    
                        # Extract size
                        size = extracted.get('size_grams', 250)  # Default to 250g
                        if isinstance(size, str):
                            # Try to extract numeric value
                            size_match = re.search(r'(\d+\.?\d*)\s*(?:g|gram|gm|kg)', size, re.IGNORECASE)
                            if size_match:
                                size_value = float(size_match.group(1))
                                # Convert kg to grams if needed
                                if 'kg' in size.lower() or 'kilo' in size.lower():
                                    size_value *= 1000
                                size = int(size_value)
                    
                        # Add price entry
                        product['prices'].append({
                            'size_grams': size,
                            'price': price
                        })
                    
                    # Handle flavor profiles
                    if 'flavor_notes' in extracted and extracted['flavor_notes']:
                        # If string, split into list
                        if isinstance(extracted['flavor_notes'], str):
                            product['flavor_profiles'] = [note.strip() for note in extracted['flavor_notes'].split(',')]
                        # If already a list, use directly
                        elif isinstance(extracted['flavor_notes'], list):
                            product['flavor_profiles'] = extracted['flavor_notes']
                    
                        # Post-processing for new fields in extract_product_page, applying conditional logic
                        new_fields_map_extract = {
                            'acidity': 'acidity', 'body': 'body', 'sweetness': 'sweetness',
                            'with_milk_suitable': 'with_milk_suitable'
                        }
                        for schema_key, product_key in new_fields_map_extract.items():
                            if product.get(product_key) is None: # Check if field is currently None
                                if schema_key in extracted and extracted[schema_key] is not None:
                                    if product_key == 'with_milk_suitable' and isinstance(extracted[schema_key], str):
                                        val_lower = extracted[schema_key].lower()
                                        if val_lower in ['true', 'yes', '1', 'suitable']:
                                            product[product_key] = True
                                        elif val_lower in ['false', 'no', '0', 'unsuitable']:
                                            product[product_key] = False
                                        else:
                                            product[product_key] = None
                                    elif product_key == 'with_milk_suitable' and isinstance(extracted[schema_key], int):
                                        product[product_key] = bool(extracted[schema_key])
                                    else:
                                        product[product_key] = extracted[schema_key]
                        
                        # Varietals processing
                        if not product.get('varietals'): # Check if field is None or empty list
                            if 'varietals' in extracted and extracted['varietals']:
                                raw_varietals = extracted['varietals']
                                processed_varietals = []
                                if isinstance(raw_varietals, str):
                                    processed_varietals = [v.strip() for v in raw_varietals.split(',') if v.strip()]
                                elif isinstance(raw_varietals, list):
                                    processed_varietals = [str(v).strip() for v in raw_varietals if str(v).strip()]
                                if processed_varietals:
                                    product['varietals'] = processed_varietals
                                elif product.get('varietals') is None: # Ensure None if LLM gives empty and was None
                                    product['varietals'] = None
                        
                        # Aroma processing
                        if product.get('aroma') is None: # Check if field is currently None
                            if 'aroma' in extracted and extracted['aroma']:
                                aroma_data = extracted['aroma']
                                processed_aroma = None
                                if isinstance(aroma_data, list):
                                    processed_aroma = ', '.join(filter(None, [str(a).strip() for a in aroma_data]))
                                elif isinstance(aroma_data, str):
                                    processed_aroma = aroma_data.strip()
                                elif aroma_data is not None:
                                    processed_aroma = str(aroma_data)
                                if processed_aroma:
                                     product['aroma'] = processed_aroma

                        # Altitude_meters processing
                        if product.get('altitude_meters') is None: # Check if field is currently None
                            if 'altitude_meters' in extracted and extracted['altitude_meters'] is not None:
                                alt_val = extracted['altitude_meters']
                                parsed_alt = None
                                if isinstance(alt_val, str):
                                    match = re.search(r'^(\d+)', alt_val.strip())
                                    if match:
                                        try:
                                            parsed_alt = int(match.group(1))
                                        except ValueError:
                                            logger.warning(f"Could not convert altitude_meters '{match.group(1)}' to int for {product.get('name')}")
                                    else:
                                        logger.warning(f"Could not parse altitude_meters string '{alt_val}' for {product.get('name')}")
                                elif isinstance(alt_val, int):
                                    parsed_alt = alt_val
                                else: 
                                    try:
                                        parsed_alt = int(alt_val)
                                    except (ValueError, TypeError):
                                        logger.warning(f"Could not convert altitude_meters type '{type(alt_val)}' to int for {product.get('name')}")
                                if parsed_alt is not None:
                                    product['altitude_meters'] = parsed_alt
                                    
                    logger.info(f"Successfully extracted product: {product.get('name', 'Unknown')}")
                    return product
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse extracted content as JSON: {e}")
                    logger.debug(f"Raw extracted content: {result.extracted_content[:500]}...")

            # If LLM extraction failed but we have basic data from HTML, create a minimal product
            if (js_product_name or extracted_title) and result.html:
                product_name = js_product_name or extracted_title
                logger.info(f"Using fallback extraction for {url}: {product_name}")
                
                return {
                    'name': product_name,
                    'slug': create_slug(product_name), # Replaced call
                    'roaster_id': roaster_id,
                    'description': extracted_description,
                    'direct_buy_url': url,
                    'image_url': product_image,
                    'is_available': True,
                    'source': 'crawl4ai_fallback_extraction'
                }
                
            logger.warning(f"Failed to extract product: {result.error_message if not result.success else 'No extracted content'}")
            return None
    except Exception as e:
        logger.error(f"Error during product extraction: {e}")
        return None

def get_llm_config() -> LLMConfig:
    """
    Get LLM configuration based on environment variables.
    Falls back to default provider if necessary.
    
    Returns:
        LLMConfig object
    """
    # Check for DeepSeek API key in config
    deepseek_key = config.llm.deepseek_api_key
    if deepseek_key:
        return LLMConfig(provider="deepseek/deepseek-chat", api_token=deepseek_key)
    
    # Default to OpenAI with warning
    openai_key = config.llm.openai_api_key
    if openai_key:
        return LLMConfig(provider="openai/gpt-4o-mini", api_token=openai_key)
    logger.warning("No LLM API keys found in config. Extraction may fail without a valid API key.")
    return LLMConfig(provider="openai/gpt-4o-mini", api_token="")

# Removed local create_slug_from_name function