# scrapers/roasters-crawl4ai/crawler.py
"""Roaster data extraction using Crawl4AI."""

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig, LLMConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy, LLMExtractionStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from common.platform_detector import PlatformDetector
from common.utils import (
    clean_description,
    clean_html,
    slugify,
    ensure_absolute_url,
    extract_instagram_handle,
    fetch_with_retry,
    get_domain_from_url,
    normalize_phone_number,
)
from config import config as app_config

from .enricher import enrich_missing_fields
from .platform_pages import get_platform_page_paths
from .schemas import ABOUT_SCHEMA, CONTACT_SCHEMA, ROASTER_LLM_INSTRUCTIONS, ROASTER_LLM_SCHEMA


class RoasterCrawler:
    """Extract roaster information using Crawl4AI."""

    def __init__(self):
        """Initialize the roaster crawler."""
        self.cache_dir = Path(app_config.CACHE_DIR) / "crawl4ai"
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        self.page_cache = {}  # Store fetched results per run

    async def extract_roaster(self, name: str, url: str) -> Dict[str, Any]:
        """Extract roaster information using Crawl4AI."""
        print(f"Crawling roaster: {name} ({url})")

        # Reset page cache for this run
        self.page_cache = {}

        # Initialize roaster data
        roaster_data = {
            "name": name,
            "website_url": url,
            "slug": slugify(name),
            "country": "India",  # Default
            "is_active": True,
            "is_verified": False,
        }
        # Add domain info
        roaster_data["domain"] = get_domain_from_url(url)

        # Check if site is accessible
        site_status = await self._check_site_status(url)
        if not site_status.get("active"):
            roaster_data["is_active"] = False
            roaster_data["error"] = site_status.get("error", "Site not active")
            return roaster_data

        # Detect platform using PlatformDetector class (per workflow memory)
        detector = PlatformDetector()
        platform, confidence = await detector.detect(url)
        if platform:
            roaster_data["platform"] = platform
        # Always use get_platform_page_paths for about/contact paths
        base_url = url.rstrip("/")
        about_paths = get_platform_page_paths(platform, "about")
        contact_paths = get_platform_page_paths(platform, "contact")
        # If platform is None, get_platform_page_paths provides generic fallbacks
        # Prefetch all relevant URLs
        urls_to_prefetch = set([url])
        urls_to_prefetch.update([f"{base_url}{p}" for p in about_paths])
        urls_to_prefetch.update([f"{base_url}{p}" for p in contact_paths])
        await self._prefetch_pages(urls_to_prefetch)
        # Use canonical about/contact paths for extraction
        about_info = await self._extract_about_info(url, about_paths)
        if about_info:
            roaster_data.update(about_info)
        contact_info = await self._extract_contact_info(url, contact_paths)
        if contact_info:
            roaster_data.update(contact_info)
        # For location info, use contact_paths (could extend in future for location-specific paths)
        location_info = await self._extract_location_info(url, contact_paths)
        if location_info:
            roaster_data.update(location_info)

        # Use LLM to extract complex data
        llm_description = None
        if app_config.llm.deepseek_api_key:
            enriched_data = await self._extract_with_llm(url)
            if enriched_data:
                # Prefer LLM description if present (even if CSS already found one)
                if "description" in enriched_data and enriched_data["description"]:
                    llm_description = clean_description(enriched_data["description"])
                    print(f"[desc-debug] LLM description found: {llm_description}")
                else:
                    print(f"[desc-debug] No LLM description found in enriched_data: {enriched_data}")
                roaster_data.update(enriched_data)

        # Extract tags
        roaster_data = await self._extract_tags(url, roaster_data)

        # Fix logo URL if needed
        if roaster_data.get("logo_url") and roaster_data["logo_url"].startswith("//"):
            roaster_data["logo_url"] = "https:" + roaster_data["logo_url"]

        # Ensure description exists and is clean, always prefer LLM if available
        if llm_description:
            desc = llm_description
            print(f"[desc-debug] Using LLM description: {desc}")
        else:
            desc = roaster_data.get("description", "")
            print(f"[desc-debug] Initial description from roaster_data: {desc}")
            desc = clean_description(desc)
            print(f"[desc-debug] Cleaned initial description: {desc}")
            if not desc:
                # Try fallback from about_text or meta_description if present
                about_fallback = roaster_data.get("about_text") or roaster_data.get("meta_description")
                print(f"[desc-debug] Fallback about/meta description: {about_fallback}")
                if about_fallback:
                    desc = clean_description(about_fallback)
                    print(f"[desc-debug] Cleaned fallback description: {desc}")
        roaster_data["description"] = desc or ""
        print(f"[desc-debug] Final description set in roaster_data: {roaster_data['description']}")

        # Enrich missing critical fields (description, founded_year, address)
        roaster_data = await enrich_missing_fields(roaster_data)
        # Clean up the data
        cleaned_data = self._cleanup_data(roaster_data)
        return cleaned_data

    async def _prefetch_pages(self, urls: set) -> None:
        """Prefetch multiple pages in parallel."""
        import asyncio

        async def fetch_single(url: str):
            await self._fetch_page(url, CrawlerRunConfig(cache_mode=CacheMode.ENABLED))

        tasks = [fetch_single(url) for url in urls]
        await asyncio.gather(*tasks)

    async def _fetch_page(self, url: str, config: CrawlerRunConfig) -> Any:
        """Fetch page with Crawl4AI and cache per run."""
        if url in self.page_cache:
            return self.page_cache[url]
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url, config=config)
            self.page_cache[url] = result
            return result

    async def _check_site_status(self, url: str) -> Dict[str, Any]:
        """Check if a website is active and accessible."""
        try:
            result = await self._fetch_page(url, CrawlerRunConfig(cache_mode=CacheMode.BYPASS))
            return {"active": result.success, "final_url": result.url, "status_code": result.status_code}
        except Exception as e:
            # Fallback: use fetch_with_retry to check status
            try:
                response = await fetch_with_retry(url, max_retries=2)
                return {
                    "active": response.status_code == 200,
                    "final_url": str(response.url),
                    "status_code": response.status_code,
                }
            except Exception as e2:
                return {"active": False, "error": f"{e}; fallback: {e2}"}

    async def _extract_about_info(self, url: str, about_paths: list) -> Dict[str, Any]:
        """Extract general information about the roaster."""
        strategy = JsonCssExtractionStrategy(ABOUT_SCHEMA)

        # URLs to check
        about_urls = [url]
        base_url = url.rstrip("/")
        about_urls.extend([f"{base_url}{path}" for path in about_paths])

        results = {}

        for page_url in about_urls:
            try:
                config = CrawlerRunConfig(extraction_strategy=strategy, cache_mode=CacheMode.ENABLED)
                result = await self._fetch_page(page_url, config)
                if result.success and result.extracted_content:
                    # Parse the extracted data
                    data = json.loads(result.extracted_content)
                    if isinstance(data, list) and data:
                        data = data[0]  # Get first item if it's a list

                        # Clean description
                        if data.get("meta_description"):
                            # Clean HTML before cleaning description
                            raw = clean_html(data["meta_description"])
                            desc = clean_description(raw)
                            print(f"[desc-debug] Found meta_description: {desc}")
                            data["description"] = desc
                            del data["meta_description"]
                        elif data.get("about_text"):
                            raw = clean_html(data["about_text"])
                            desc = clean_description(raw)
                            print(f"[desc-debug] Found about_text: {desc}")
                            data["description"] = desc
                            del data["about_text"]
                        elif data.get("main_content"):
                            # Extract a reasonable paragraph from main content
                            content = clean_description(data["main_content"])
                            import re

                            paragraphs = re.split(r"\n\n|\r\n\r\n", content)
                            for paragraph in paragraphs:
                                if len(paragraph) > 100 and any(
                                    word in paragraph.lower() for word in ["coffee", "roast", "bean", "brew", "tokai"]
                                ):
                                    data["description"] = paragraph.strip()
                                    break
                            if not data.get("description") and paragraphs:
                                for paragraph in paragraphs:
                                    if len(paragraph) > 100:
                                        data["description"] = paragraph.strip()
                                        break
                            del data["main_content"]

                        # Ensure URLs are absolute
                        if data.get("logo_url"):
                            logo_url = ensure_absolute_url(data["logo_url"], page_url)
                            data["logo_url"] = logo_url
                            print(f"[desc-debug] Found logo_url: {logo_url}")

                        if data.get("hero_image_url"):
                            data["image_url"] = ensure_absolute_url(data["hero_image_url"], page_url)
                            del data["hero_image_url"]

                        # Update results
                        for key, value in data.items():
                            if value and (key not in results or not results[key]):
                                results[key] = value

                        # If we found a description, no need to check more pages
                        if results.get("description"):
                            print(f"[desc-debug] Saved description to results: {results['description'][:100]}...")
                            break

            except Exception as e:
                print(f"Error extracting about info from {page_url}: {str(e)}")
                continue
        # Ensure description and logo_url are preserved if found
        if results.get("description"):
            print(f"[desc-debug] Final description in results: {results['description'][:100]}...")
        if results.get("logo_url"):
            print(f"[desc-debug] Final logo_url in results: {results['logo_url']}")
        return results

    async def _extract_contact_info(self, url: str, contact_paths: list) -> Dict[str, Any]:
        """Extract contact info and social links using JSON CSS extraction."""
        strategy = JsonCssExtractionStrategy(CONTACT_SCHEMA)

        # URLs to check
        contact_urls = [url]
        base_url = url.rstrip("/")
        contact_urls.extend([f"{base_url}{path}" for path in contact_paths])

        results = {}

        for page_url in contact_urls:
            try:
                config = CrawlerRunConfig(extraction_strategy=strategy, cache_mode=CacheMode.ENABLED)
                result = await self._fetch_page(page_url, config)
                if result.success and result.extracted_content:
                    # Parse the extracted data
                    data = json.loads(result.extracted_content)
                    if isinstance(data, list) and data:
                        data = data[0]  # Get first item if it's a list

                        # Process email (remove mailto:)
                        if data.get("email") and data["email"].startswith("mailto:"):
                            data["email"] = data["email"][7:]

                        # Process phone (remove tel:)
                        if data.get("phone") and data["phone"].startswith("tel:"):
                            data["phone"] = normalize_phone_number(data["phone"][4:])

                        # Process social links
                        social_links = []
                        for platform in ["instagram", "facebook", "twitter", "linkedin"]:
                            if data.get(platform):
                                social_links.append(data[platform])

                                # Extract Instagram handle
                                if platform == "instagram":
                                    handle = extract_instagram_handle(data[platform])
                                    if handle:
                                        data["instagram_handle"] = handle

                        # Remove platform fields and set social_links
                        for platform in ["instagram", "facebook", "twitter", "linkedin"]:
                            if platform in data:
                                del data[platform]

                        if social_links:
                            data["social_links"] = social_links

                        # Check for address in contact_text
                        if data.get("contact_text") and not data.get("address"):
                            contact_text = data["contact_text"]
                            if any(
                                indicator in contact_text.lower()
                                for indicator in [
                                    "address",
                                    "location",
                                    "visit us",
                                    "find us",
                                    "street",
                                    "road",
                                    "ave",
                                    "lane",
                                    "bangalore",
                                    "mumbai",
                                    "delhi",
                                ]
                            ):
                                data["address"] = contact_text
                            del data["contact_text"]

                        # Update results
                        for key, value in data.items():
                            if value and (key not in results or not results[key]):
                                results[key] = value

            except Exception as e:
                print(f"Error extracting contact info from {page_url}: {str(e)}")
                continue

        # Rename fields to match model
        if "email" in results:
            results["contact_email"] = results.pop("email")
        if "phone" in results:
            results["contact_phone"] = results.pop("phone")

        return results

    async def _extract_with_llm(self, url: str) -> Dict[str, Any]:
        """Extract complex information using LLM."""
        # Skip LLM if key not configured
        if not app_config.llm.deepseek_api_key:
            return {}

        # Define a pruning filter
        pruning_filter = PruningContentFilter(
            threshold=0.5,  # Adjust threshold based on testing
            threshold_type="fixed",  # Fixed threshold works better for consistent filtering
            min_word_threshold=10,  # Skip very short sections
        )

        # Create markdown generator with pruning filter
        md_generator = DefaultMarkdownGenerator(
            content_filter=pruning_filter,
            options={"ignore_links": True, "body_width": 0},  # No line wrapping
        )

        # Define the LLM extraction strategy
        llm_strategy = LLMExtractionStrategy(
            llm_config=LLMConfig(provider="deepseek-ai/deepseek-chat", api_token=app_config.llm.deepseek_api_key),
            schema=ROASTER_LLM_SCHEMA,
            extraction_type="schema",
            instruction=ROASTER_LLM_INSTRUCTIONS,
            chunk_token_threshold=4000,
            apply_chunking=True,
            input_format="fit_markdown",
        )

        # Configure page crawler to look at home and about pages
        pages = [url]
        base_url = url.rstrip("/")
        about_paths = ["/about", "/about-us", "/our-story"]
        pages.extend([f"{base_url}{path}" for path in about_paths])

        async with AsyncWebCrawler() as crawler:
            for page_url in pages:
                try:
                    crawler_config = CrawlerRunConfig(
                        extraction_strategy=llm_strategy, markdown_generator=md_generator, cache_mode=CacheMode.ENABLED
                    )
                    result = await crawler.arun(page_url, config=crawler_config)

                    if result.success and result.extracted_content:
                        try:
                            # Parse the extracted data
                            data = json.loads(result.extracted_content)

                            # Handle different response formats
                            if isinstance(data, list):
                                if data and isinstance(data[0], dict):
                                    data = data[0]  # Get first item if it's a list of dicts
                                else:
                                    continue  # Skip this result if it's not in the expected format

                            # Only use the data if it's a dictionary with values
                            if isinstance(data, dict) and data:
                                # Check if there are any non-null values
                                has_values = False
                                for value in data.values():
                                    if value is not None:
                                        has_values = True
                                        break

                                if has_values:
                                    print(f"[LLM] Extracted data from {page_url} using pruned fit_markdown")
                                    return data
                        except (json.JSONDecodeError, AttributeError) as e:
                            print(f"Error parsing LLM result from {page_url}: {str(e)}")
                            continue

                except Exception as e:
                    print(f"Error extracting with LLM from {page_url}: {str(e)}")
                    continue

        return {}

    async def _extract_location_info(self, url: str, location_paths: list) -> Dict[str, Any]:
        """Extract location information from contact and locations pages."""
        # URLs to check
        base_url = url.rstrip("/")
        location_urls = [f"{base_url}{path}" for path in location_paths]

        # First, try using our alternative CSS-based approach
        location_results = await self._extract_location_with_css(url, location_urls)
        if location_results.get("address"):
            return location_results

        # If no address found, try using JavaScript approach as a fallback
        js_location_results = await self._extract_location_with_js(url, location_urls)
        if js_location_results.get("address"):
            return js_location_results

        # If still no address, return whatever we have (which might be empty)
        return location_results

    async def _extract_location_with_css(self, url: str, location_urls: List[str]) -> Dict[str, Any]:
        """Extract location information using CSS selectors."""
        from .schemas import ADDRESS_SCHEMA

        strategy = JsonCssExtractionStrategy(ADDRESS_SCHEMA)

        location_results = {}

        async with AsyncWebCrawler() as crawler:
            for page_url in location_urls:
                try:
                    crawler_config = CrawlerRunConfig(extraction_strategy=strategy, cache_mode=CacheMode.ENABLED)
                    result = await crawler.arun(page_url, config=crawler_config)

                    if result.success and result.extracted_content:
                        data = json.loads(result.extracted_content)
                        if isinstance(data, list) and data:
                            data = data[0]

                            # If we found an address directly, use it
                            if data.get("address"):
                                location_results["address"] = data["address"]
                                break

                            # Otherwise, try to extract address patterns from full text
                            if data.get("full_text"):
                                full_text = data["full_text"]

                                # Look for address patterns
                                address_patterns = [
                                    r"\d+[,\s]+[\w\s]+(Street|Road|Lane|Avenue|Plaza|Building|Complex|Tower)",
                                    r"[\w\s]+(Street|Road|Lane|Avenue|Plaza|Building|Complex|Tower)[,\s]+\d+",
                                    r"PIN\s+\d{6}",
                                    r"Pincode\s+\d{6}",
                                    r"Post Code\s+\d{6}",
                                ]

                                for pattern in address_patterns:
                                    matches = re.finditer(pattern, full_text, re.IGNORECASE)
                                    for match in matches:
                                        # Extract the match and some context around it
                                        start = max(0, match.start() - 50)
                                        end = min(len(full_text), match.end() + 50)
                                        context = full_text[start:end]

                                        # Clean up the context
                                        context = re.sub(r"\s+", " ", context).strip()

                                        if len(context) > 10 and len(context) < 300:
                                            location_results["address"] = context
                                            break

                                    if "address" in location_results:
                                        break

                            if "address" in location_results:
                                break

                except Exception as e:
                    print(f"Error extracting location with CSS from {page_url}: {str(e)}")
                    continue

        return location_results

    async def _extract_location_with_js(self, url: str, location_urls: List[str]) -> Dict[str, Any]:
        """Extract location information using JavaScript execution."""
        # Look for embedded Google Maps
        js_location_extractor = """
        (() => {
            // Try to find location info in the page
            const locationData = {
                addresses: []
            };
            
            // Look for Google Maps URLs
            const mapLinks = Array.from(document.querySelectorAll('a[href*="maps.google"], a[href*="google.com/maps"], iframe[src*="maps.google"], iframe[src*="google.com/maps"]'));
            if (mapLinks.length > 0) {
                mapLinks.forEach(link => {
                    let mapUrl = link.href || link.src;
                    if (mapUrl && (mapUrl.includes('maps.google') || mapUrl.includes('google.com/maps'))) {
                        locationData.mapUrl = mapUrl;
                    }
                });
            }
            
            // Look for address blocks
            const addressBlocks = Array.from(document.querySelectorAll('address, .address, [itemprop="address"], .store-address, .location'));
            if (addressBlocks.length > 0) {
                addressBlocks.forEach(block => {
                    locationData.addresses.push(block.innerText.trim());
                });
            }
            
            // Look for address patterns in paragraphs
            const paragraphs = Array.from(document.querySelectorAll('p, div'));
            paragraphs.forEach(p => {
                const text = p.innerText.trim();
                // Check for address patterns: street, road, lane, etc. with numbers
                if (
                    (text.match(/\\d+[\\s,]+[\\w\\s]+(Street|Road|Lane|Avenue|Plaza|Building|Complex|Tower)/i) ||
                    text.match(/[\\w\\s]+(Street|Road|Lane|Avenue|Plaza|Building|Complex|Tower)[\\s,]+\\d+/i) ||
                    text.includes('PIN') || text.includes('Pincode') || text.includes('Post Code') ||
                    text.match(/\\d{6}/) // Indian PIN code pattern
                    ) && 
                    text.length > 10 && text.length < 300 // Reasonable length for an address
                ) {
                    locationData.addresses.push(text);
                }
            });
            
            return JSON.stringify(locationData);  // Return as a string to ensure proper serialization
        })();
        """

        location_results = {}

        async with AsyncWebCrawler() as crawler:
            for page_url in location_urls:
                try:
                    crawler_config = CrawlerRunConfig(js_code=js_location_extractor, cache_mode=CacheMode.ENABLED)
                    result = await crawler.arun(page_url, config=crawler_config)

                    if result.success and hasattr(result, "js_result") and result.js_result:
                        try:
                            # Parse the JavaScript result
                            js_data = json.loads(result.js_result)

                            # Find addresses
                            if js_data.get("addresses") and isinstance(js_data["addresses"], list):
                                for address_text in js_data["addresses"]:
                                    if isinstance(address_text, str) and len(address_text) > 10:
                                        location_results["address"] = address_text
                                        break

                            # If we found a good address, no need to check more pages
                            if location_results.get("address"):
                                break
                        except (json.JSONDecodeError, TypeError) as e:
                            print(f"Error parsing JS result from {page_url}: {str(e)}")
                            continue

                except Exception as e:
                    print(f"Error extracting location with JS from {page_url}: {str(e)}")
                    continue

        return location_results

    async def _extract_tags(self, url: str, roaster_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract tags based on content keywords and set has_subscription/has_physical_store."""
        # Try to get the HTML content from cache if available
        html_content = ""
        if url in self.page_cache and hasattr(self.page_cache[url], "html"):
            html_content = self.page_cache[url].html
        else:
            async with AsyncWebCrawler() as crawler:
                config = CrawlerRunConfig(cache_mode=CacheMode.ENABLED)
                result = await crawler.arun(url, config=config)
                if hasattr(result, "success") and result.success:
                    html_content = result.html
        # Skip if no HTML content
        if not html_content:
            return roaster_data
        tags = []
        # Check for common tag indicators
        tag_indicators = {
            "specialty": ["specialty", "speciality", "artisanal", "craft", "premium"],
            "organic": ["organic", "natural", "chemical-free", "sustainable"],
            "single-origin": ["single origin", "single estate", "micro lot"],
            "fair-trade": ["fair trade", "ethical", "direct trade", "sustainable"],
            "local": ["local", "indian", "domestic"],
            "arabica": ["arabica", "100% arabica"],
            "robusta": ["robusta"],
            "subscription": ["subscription", "monthly delivery"],
        }
        # Combine all text content
        all_text = html_content.lower() + " " + roaster_data.get("description", "").lower()
        # Check for indicator presence
        for tag, indicators in tag_indicators.items():
            if any(indicator in all_text for indicator in indicators):
                tags.append(tag)
        # Add platform as a tag if it exists
        if "platform" in roaster_data and roaster_data["platform"] not in ["static", "unknown"]:
            tags.append(roaster_data["platform"])
        if tags:
            roaster_data["tags"] = tags
        # --- Add subscription/store detection ---
        sub_indicators = ["subscription", "subscribe", "recurring", "monthly delivery"]
        if any(indicator in all_text for indicator in sub_indicators):
            roaster_data["has_subscription"] = True
        store_indicators = [
            "visit us",
            "our store",
            "physical location",
            "cafe",
            "visit our",
            "directions",
            "opening hours",
            "open from",
            "coffee shop",
            "location",
        ]
        if any(indicator in all_text for indicator in store_indicators):
            roaster_data["has_physical_store"] = True
        return roaster_data

    def _cleanup_data(self, roaster_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up roaster data before returning, but never remove description, logo_url, has_subscription, or has_physical_store if present and non-empty."""
        # Remove empty values, but preserve required fields
        preserve_fields = {"description", "logo_url", "has_subscription", "has_physical_store"}
        cleaned_data = {}
        for k, v in roaster_data.items():
            if v is not None and v != "":
                cleaned_data[k] = v
            elif k in preserve_fields and v is not None:
                # Allow False boolean or empty string for these fields
                cleaned_data[k] = v
        # Ensure social_links is a list
        if "social_links" in cleaned_data:
            if isinstance(cleaned_data["social_links"], dict):
                # Extract Instagram handle if available
                if "instagram_handle" in cleaned_data["social_links"]:
                    cleaned_data["instagram_handle"] = cleaned_data["social_links"].pop("instagram_handle")
                # Convert dict values to list
                cleaned_data["social_links"] = [str(v) for v in cleaned_data["social_links"].values() if v is not None]
            elif not isinstance(cleaned_data["social_links"], list):
                cleaned_data["social_links"] = []
        return cleaned_data
