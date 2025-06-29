"""
Utility functions for the Coffee Scraper.
Contains common helpers used across multiple modules.
"""

import asyncio
import csv
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from loguru import logger

from config import config


def slugify(name):
    """Create a URL-friendly slug from a name."""
    if not name:
        return ""
    # Replace special characters
    slug = name.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)  # Remove non-word chars except spaces and hyphens
    slug = re.sub(r"[\s_]+", "-", slug)  # Replace whitespace and underscores with hyphens
    slug = re.sub(r"-+", "-", slug)  # Remove duplicate hyphens
    return slug.strip("-")  # Trim hyphens from start and end


async def fetch_with_retry(
    url, client=None, max_retries=3, headers=None, timeout=None, rate_limit=False, rate_limiter=None, _visited_urls=None
):
    """Fetch URL with exponential backoff retry and optional rate limiting."""
    if not url:
        raise ValueError("URL cannot be empty")

    # Initialize visited URLs tracker to prevent redirect loops
    if _visited_urls is None:
        _visited_urls = set()

    # Check for redirect loops
    if url in _visited_urls:
        raise Exception(f"Redirect loop detected: {url}")
    _visited_urls.add(url)

    # Apply rate limiting if enabled
    if rate_limit and rate_limiter:
        await rate_limiter.wait()

    # Use default headers if none provided
    if headers is None:
        headers = {
            "User-Agent": config.scraper.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml",
            "Accept-Language": "en-US,en;q=0.9",
        }

    # Use default timeout if none provided
    if timeout is None:
        timeout = httpx.Timeout(config.scraper.request_timeout)

    # If no client provided, create a new one
    close_client = False
    if client is None:
        client = httpx.AsyncClient(timeout=timeout, follow_redirects=True)
        close_client = True

    # Perform retry logic
    backoff = 1
    last_error = None

    try:
        for attempt in range(max_retries):
            try:
                response = await client.get(url, headers=headers)

                # Check for rate limiting
                if response.status_code == 429:
                    wait_time = int(response.headers.get("Retry-After", str(backoff * 5)))
                    logger.warning(f"Rate limited (429) for {url}. Waiting {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue  # Retry immediately after waiting

                # Return successful responses
                if response.status_code == 200:
                    return response

                # Handle redirect
                if response.status_code in (301, 302, 307, 308):
                    redirect_url = response.headers.get("Location")
                    if redirect_url:
                        logger.info(f"Following redirect: {url} -> {redirect_url}")
                        return await fetch_with_retry(
                            urljoin(url, redirect_url),
                            client=None,  # Create new client for redirect
                            max_retries=max_retries - 1,
                            headers=headers,
                            timeout=timeout,
                            rate_limit=rate_limit,
                            rate_limiter=rate_limiter,
                            _visited_urls=_visited_urls.copy(),  # Pass visited URLs to prevent loops
                        )

                # Specific handling for common errors
                if response.status_code == 404:
                    raise Exception(f"404 Not Found: {url}")
                elif response.status_code == 403:
                    raise Exception(f"403 Forbidden: {url}")

                # General error handling
                raise Exception(f"HTTP error {response.status_code} for {url}")

            except Exception as e:
                last_error = e
                if "404 Not Found" in str(e):
                    logger.warning(f"404 Not Found: {url}. Stopping retries.")
                    break
                if attempt == max_retries - 1:
                    break

                # Exponential backoff with jitter
                jitter = 0.5 + (asyncio.get_event_loop().time() % 1) / 2  # 0.5-1.5 jitter factor
                wait_time = backoff * jitter
                logger.warning(f"Retry {attempt + 1}/{max_retries} for {url}: {e}. Waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
                backoff *= 2  # Exponential backoff

    finally:
        # ✅ FIX: Always close client if we created it
        if close_client and client:
            await client.aclose()

    # If we got here, all retries failed
    error_msg = f"Failed to fetch {url} after {max_retries} attempts"
    if last_error:
        error_msg += f": {last_error}"
    raise Exception(error_msg)


def clean_html(html_text):
    """Remove HTML tags from text."""
    if not html_text:
        return ""
    # Remove script and style tags
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", str(html_text), flags=re.DOTALL)
    # Remove all other HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_description(text: str) -> str:
    """Clean and normalize description text."""
    if not text:
        return ""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Filter out common JavaScript warnings
    if text.startswith("JavaScript seems to be disabled"):
        return ""
    return text


def is_coffee_product(name, description=None, product_type=None, tags=None, roaster_name="Unknown", url=""):
    """Determine if a product is coffee (beans or ground)."""
    if not name:
        return False

    name = name.lower()
    description = (description or "").lower()
    product_type = (product_type or "").lower()

    # Definitely coffee if product type says so
    if product_type in ["coffee", "beans", "ground coffee"]:
        logger.debug(f"✅ Accepted: '{name}' | Reason: product_type={product_type}")
        return True

    # Skip obvious non-coffee products
    non_coffee_terms = [
        "grinder",
        "machine",
        "mug",
        "cup",
        "filter",
        "chocolate",
        "tool",
        "course",
        "workshop",
        "kettle",
        "dripper",
        "aeropress",
        "v60",
        "chemex",
        "carafe",
        "equipment",
        "accessory",
        "maker",
        "bootcamp",
        "skills",
        "program",
        "sensory",
        "barista",
        "101:",
        "masterclass",
        "paper",
        "bag",
        "spoon",
        "french press",
        "scale",
        "stagg",
        "reusable",
        "class",
        "throwdown",
        "event",
        "course",
        "gift card",
        "subscription",
        "gift",
        "course",
        "workshop",
        "academy",
        "training",
        "espresso machine",
        "day in the life",
        "coffee maker",
        "coffee grinder",
        "coffee cup",
        "coffee mug",
        "coffee filter",
    ]

    for term in non_coffee_terms:
        if f" {term} " in f" {name} ":
            reason = f"excluded term '{term}' in name"
            logger.debug(f"⛔ Skipping: '{name}' | Reason: {reason}")
            record_skipped_product(name, reason, roaster_name, url)
            return False

    if "filter" in name and not re.search(r"filter\s+(coffee|blend)", name):
        reason = "filter in name but not coffee"
        logger.debug(f"⛔ Skipping: '{name}' | Reason: {reason}")
        record_skipped_product(name, reason, roaster_name, url)
        return False

    # These types are definitely coffee
    bean_types = ["beans", "coffee", "ground coffee", "whole bean"]
    if product_type in bean_types:
        logger.debug(f"✅ Accepted: '{name}' | Reason: product_type={product_type}")
        return True

    # Check for coffee keywords
    coffee_keywords = [
        "micro climate",
        "selection",
        "signature",
        "grand reserve",
        "pocket brew",
        "arabica",
        "robusta",
        "single origin",
        "blend",
        "specialty",
        "direct trade",
        "direct sourced",
        "freshly roasted",
        "civet",
        "moroccan",
        "liberica",
        "decaf",
        "vienna roast",
        "espresso roast",
        "attikan",
        "dark roast",
        "medium roast",
        "light roast",
        "coffee beans",
        "coffee blend",
        "filter coffee",
        "balmaadi wild",
        "malabar",
        "peaberry",
        "julien peak",
        "salawara reserve",
        "old kent vienna",
        "thogarihunkal",
        "salawara",
        "ratnagiri",
        "mandalkhan",
        "l&#8217;lmore",
        "turkish",
        "unakki",
        "terrazas del pisque sidra",
    ]

    for kw in coffee_keywords:
        if kw in name.lower():
            logger.debug(f"✅ Accepted: '{name}' | Reason: product has bean indicator '{kw}'")
            return True

    # 🛡️ Prevent NoneType errors
    if not tags:
        tags = []

    # Check for coffee keywords in tags
    if isinstance(tags, list) and any(kw in tag.lower() for tag in tags for kw in coffee_keywords):
        logger.debug(f"✅ Accepted: '{name}' | Reason: tag includes coffee keyword")
        return True

    # If name ends with "Estate" or contains "estate - " - likely a coffee
    if name.endswith(" estate") or " estate - " in name or name.endswith(" estate|") or "estate |" in name:
        logger.debug(f"✅ Accepted: '{name}' | Reason: name includes 'estate'")
        return True

    # Check for beans/roast/origin in description
    bean_indicators = [
        "medium roast",
        "light roast",
        "dark roast",
        "single origin",
        "arabica beans",
        "robusta beans",
        "fruity notes",
        "chocolate notes",
        "caramel notes",
    ]

    for indicator in bean_indicators:
        if indicator in description:
            logger.debug(f"✅ Accepted: '{name}' | Reason: bean/roast indicator in description")
            return True

    # Default - if unsure whether it's actual coffee beans, skip it
    reason = "doesn't appear to be coffee beans"
    logger.debug(f"⛔ Skipping: '{name}' | Reason: {reason}")
    record_skipped_product(name, reason, roaster_name, url)
    return False


def record_skipped_product(name, reason, roaster_name, url=""):
    """Write skipped product to CSV log."""
    csv_path = Path(config.CACHE_DIR) / "logs" / "skipped_products.csv"
    csv_path.parent.mkdir(exist_ok=True, parents=True)

    # ✅ FIX: Simple atomic write approach (cross-platform)
    try:
        # Check if file exists before opening
        file_exists = csv_path.exists() and csv_path.stat().st_size > 0

        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "reason", "roaster", "url", "skipped_at"])
            if not file_exists:
                writer.writeheader()

            writer.writerow(
                {
                    "name": name,
                    "reason": reason,
                    "roaster": roaster_name,
                    "url": url,
                    "skipped_at": datetime.now().isoformat(),
                }
            )
    except Exception as e:
        logger.warning(f"Failed to log skipped product {name}: {e}")


def normalize_phone_number(phone):
    """Normalize phone number format."""
    if not phone:
        return None

    # Remove non-digit characters
    digits = re.sub(r"\D", "", phone)

    # Format Indian phone numbers
    if len(digits) == 10:
        return f"+91 {digits[:5]} {digits[5:]}"
    elif len(digits) == 11 and digits.startswith("0"):
        return f"+91 {digits[1:6]} {digits[6:]}"
    elif len(digits) == 12 and digits.startswith("91"):
        return f"+91 {digits[2:7]} {digits[7:]}"

    # Return in international format
    return f"+{digits}"


def standardize_roast_level(roast_text):
    """Convert various roast level texts to standard enum values.

    Valid values: 'light', 'light-medium', 'medium', 'medium-dark', 'dark',
    'city', 'city-plus', 'full-city', 'french', 'italian', 'cinnamon',
    'filter', 'espresso', 'omniroast', 'unknown'
    """
    if not roast_text:
        return "unknown"

    roast_text = roast_text.lower().strip()

    # Define mapping of common terms to standard values
    roast_mapping = {
        # Light roasts
        "light": "light",
        "light roast": "light",
        "cinnamon": "cinnamon",
        "half city": "light",
        "blonde": "light",
        "new england": "light",
        # Light-medium roasts
        "light medium": "light-medium",
        "light-medium": "light-medium",
        "city": "light-medium",  # City is technically light-medium
        # Medium roasts
        "medium": "medium",
        "medium roast": "medium",
        "city+": "city-plus",
        "city plus": "city-plus",
        "full city": "full-city",
        "american": "medium",
        "breakfast": "medium",
        # Medium-dark roasts
        "medium dark": "medium-dark",
        "medium-dark": "medium-dark",
        "full city+": "medium-dark",
        "full-city+": "medium-dark",
        "vienna": "medium-dark",
        "continental": "medium-dark",
        # Dark roasts
        "dark": "dark",
        "dark roast": "dark",
        "french": "french",
        "french roast": "french",
        "italian": "italian",
        "italian roast": "italian",
        "espresso": "espresso",
        "espresso roast": "espresso",
        "high roast": "dark",
        "spanish": "dark",
        # Specialty roasts
        "omni": "omniroast",
        "omni roast": "omniroast",
        "omniroast": "omniroast",
    }

    # Check for exact matches
    if roast_text in roast_mapping:
        return roast_mapping[roast_text]

    # Check for partial matches
    for term, value in roast_mapping.items():
        if term in roast_text:
            return value

    # Handle special cases
    if "filter" in roast_text:
        # Log controversial "filter" roast level
        logger.debug(f"Using 'filter' as roast level for: {roast_text}")
        return "filter"

    # Default to unknown if no match found
    return "unknown"


def standardize_processing_method(method_text):
    """Convert various processing method texts to standard enum values.

    Valid values: 'washed', 'natural', 'honey', 'pulped-natural', 'anaerobic',
    'monsooned', 'wet-hulled', 'carbonic-maceration', 'double-fermented', 'unknown'
    """
    if not method_text:
        return "unknown"

    method_text = method_text.lower().strip()

    # Define mapping of common terms to standard values
    method_mapping = {
        # Washed process
        "washed": "washed",
        "wet": "washed",
        "wet process": "washed",
        "fully washed": "washed",
        "traditional washed": "washed",
        "water process": "washed",
        # Natural process
        "natural": "natural",
        "dry": "natural",
        "dry process": "natural",
        "sun dried": "natural",
        "sundried": "natural",
        "unwashed": "natural",
        "traditional natural": "natural",
        # Honey process
        "honey": "honey",
        "black honey": "honey",
        "red honey": "honey",
        "yellow honey": "honey",
        "white honey": "honey",
        "golden honey": "honey",
        "pulped natural": "pulped-natural",
        "semi-washed": "honey",
        "semi washed": "honey",
        # Anaerobic process
        "anaerobic": "anaerobic",
        "anaerobic natural": "anaerobic",
        "anaerobic washed": "anaerobic",
        "anaerobic fermentation": "anaerobic",
        "double anaerobic": "anaerobic",
        "carbonic": "carbonic-maceration",
        "carbonic maceration": "carbonic-maceration",
        # Wet hulled
        "wet hulled": "wet-hulled",
        "wet-hulled": "wet-hulled",
        "giling basah": "wet-hulled",
        # Monsooned
        "monsooned": "monsooned",
        "monsoon": "monsooned",
        "monsooning": "monsooned",
        "monsooned malabar": "monsooned",
        # Double fermented
        "double fermented": "double-fermented",
        "extended fermentation": "double-fermented",
        # Experimental (map to unknown)
        "experimental": "unknown",
        "experimental process": "unknown",
    }

    # Check for exact matches
    if method_text in method_mapping:
        return method_mapping[method_text]

    # Check for partial matches
    for term, value in method_mapping.items():
        if term in method_text:
            return value

    # Handle special cases with additional fallbacks
    if "double" in method_text and "ferment" in method_text:
        return "double-fermented"

    if "honey" in method_text:
        return "honey"

    if "anaerobic" in method_text:
        return "anaerobic"

    if "natural" in method_text or "dry" in method_text:
        return "natural"

    if "washed" in method_text:
        return "washed"

    # Default to unknown if no match found
    return "unknown"


def standardize_bean_type(bean_text):
    """Convert various bean type texts to standard enum values.

    Valid values: 'arabica', 'robusta', 'liberica', 'blend', 'mixed-arabica',
    'arabica-robusta', 'unknown'
    """
    if not bean_text:
        return "unknown"

    bean_text = bean_text.lower().strip()

    # Define mapping of common terms to standard values
    bean_mapping = {
        # Single origin types
        "arabica": "arabica",
        "100% arabica": "arabica",
        "bourbon": "arabica",  # Arabica varietal
        "typica": "arabica",  # Arabica varietal
        "gesha": "arabica",  # Arabica varietal
        "geisha": "arabica",  # Arabica varietal (alternative spelling)
        "sl-28": "arabica",  # Arabica varietal
        "sl28": "arabica",  # Arabica varietal
        "sl-34": "arabica",  # Arabica varietal
        "sl34": "arabica",  # Arabica varietal
        "caturra": "arabica",  # Arabica varietal
        "catuai": "arabica",  # Arabica varietal
        "catimor": "arabica",  # Arabica varietal
        "pacamara": "arabica",  # Arabica varietal
        "maragogipe": "arabica",  # Arabica varietal
        "pacas": "arabica",  # Arabica varietal
        "villa sarchi": "arabica",  # Arabica varietal
        "java": "arabica",  # Arabica varietal
        "mundo novo": "arabica",  # Arabica varietal
        "robusta": "robusta",
        "100% robusta": "robusta",
        "canephora": "robusta",  # Scientific name for robusta
        "liberica": "liberica",
        "100% liberica": "liberica",
        "excelsa": "liberica",  # Often classified as a type of liberica
        # Blends
        "blend": "blend",
        "coffee blend": "blend",
        "house blend": "blend",
        "espresso blend": "blend",
        "signature blend": "blend",
        # Specific blend types
        "arabica blend": "mixed-arabica",
        "mixed arabica": "mixed-arabica",
        "arabica mix": "mixed-arabica",
        "arabica robusta": "arabica-robusta",
        "arabica robusta blend": "arabica-robusta",
        "arabica/robusta": "arabica-robusta",
        "arabica and robusta": "arabica-robusta",
        "arabica & robusta": "arabica-robusta",
        "80/20 blend": "arabica-robusta",  # Common ratio for arabica-robusta
        "80/20": "arabica-robusta",
    }

    # Check for exact matches
    if bean_text in bean_mapping:
        return bean_mapping[bean_text]

    # Check for partial matches with context
    if "arabica" in bean_text and "robusta" in bean_text:
        return "arabica-robusta"

    if ("arabica" in bean_text and "blend" in bean_text) or ("arabica" in bean_text and "mix" in bean_text):
        return "mixed-arabica"

    # Check for varietals - these are all arabica
    arabica_varietals = [
        "bourbon",
        "typica",
        "gesha",
        "geisha",
        "sl-",
        "sl28",
        "sl34",
        "caturra",
        "catuai",
        "catimor",
        "pacamara",
        "maragogipe",
        "pacas",
    ]
    if any(v in bean_text for v in arabica_varietals):
        return "arabica"

    # Check for excelsa specifically
    if "excelsa" in bean_text:
        return "liberica"

    # Check for single bean types
    if "arabica" in bean_text:
        return "arabica"

    if "robusta" in bean_text:
        return "robusta"

    if "liberica" in bean_text:
        return "liberica"

    # If "blend" is mentioned but specifics aren't clear
    if "blend" in bean_text:
        return "blend"

    # Default to unknown if no match found
    return "unknown"


def get_domain_from_url(url):
    """Extract the domain from a URL."""
    if not url:
        return None

    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    # Remove www prefix
    domain = re.sub(r"^www\.", "", domain)

    return domain


def normalize_url(url):
    """Normalize URL for caching and comparison purposes."""
    # Parse URL
    parsed = urlparse(url)

    # Ensure it has a scheme
    if not parsed.scheme:
        url = f"https://{url}"
        parsed = urlparse(url)

    # Normalize domain (remove www)
    domain = parsed.netloc.lower()
    domain = re.sub(r"^www\.", "", domain)

    # Construct normalized base URL
    base_url = f"{parsed.scheme}://{domain}"

    # Add path without trailing slash
    path = parsed.path.rstrip("/")
    if path:
        base_url += path

    return base_url


def extract_instagram_handle(url: str) -> str | None:
    """Extract Instagram handle from an Instagram URL."""
    if not url or "instagram.com" not in url:
        return None

    try:
        # Handle different URL patterns
        if "/p/" in url:  # post URL, not profile
            return None

        parts = url.split("instagram.com/")
        if len(parts) > 1:
            handle = parts[1].split("/")[0].split("?")[0]
            if handle and not handle.startswith("?"):
                return handle
    except (IndexError, AttributeError, ValueError) as e:
        # ✅ FIX: Only catch specific exceptions, not ALL exceptions
        logger.debug(f"Error parsing Instagram URL {url}: {e}")

    return None


def ensure_absolute_url(url: str, base_url: str) -> str:
    """Ensure a URL is absolute."""
    from urllib.parse import urljoin, urlparse

    if not url:
        return ""

    if url.startswith(("http://", "https://", "//")):
        return url
    elif url.startswith("/"):
        parsed_base = urlparse(base_url)
        return f"{parsed_base.scheme}://{parsed_base.netloc}{url}"
    else:
        return urljoin(base_url.rstrip("/") + "/", url)
