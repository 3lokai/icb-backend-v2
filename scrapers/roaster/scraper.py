"""Core roaster scraper implementation."""

import json
import logging
import traceback
from typing import Any, Dict, Optional

import httpx
from bs4 import BeautifulSoup

from common.cache import cache
from common.platform_detector import detect_platform
from common.utils import clean_html, create_slug

from .about import extract_about_page_info, update_with_about_data
from .crawl4ai_enricher import enrich_roaster_data_with_crawl4ai
from .extractors import (
    check_business_features,
    extract_description,
    extract_email,
    extract_founded_year,
    extract_hero_image,
    extract_logo,
    extract_phone_number,
    extract_social_links,
    extract_tags,
)
from .location import extract_location

logger = logging.getLogger(__name__)


class RoasterScraper:
    """Scraper for coffee roaster websites."""

    def __init__(self, enrichment_service=None):
        """Initialize roaster scraper."""
        self.enrichment_service = enrichment_service

        # Fields and their stability ratings (for incremental updates)
        self.field_stability = {
            # Highly stable (annual check)
            "name": "highly_stable",
            "founded_year": "highly_stable",
            "city": "highly_stable",
            "state": "highly_stable",
            # Moderately stable (quarterly check)
            "description": "moderately_stable",
            "logo_url": "moderately_stable",
            "hero_image_url": "moderately_stable",
            # Volatile (monthly check)
            "website_url": "volatile",
            "email": "volatile",
            "phone": "volatile",
            "social_links": "volatile",
            "features": "volatile",
        }

    async def scrape_roaster(self, name: str, url: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """Scrape a roaster website to extract roaster information."""
        logger.info(f"Scraping roaster: {name} ({url})")

        # Initialize data structure
        roaster_data = {"name": name, "website_url": url, "slug": create_slug(name), "confidence": {}}

        # Check if site is active
        site_status = await self._check_site_activity(url)
        if not site_status.get("active"):
            roaster_data["active"] = False
            roaster_data["error"] = site_status.get("error", "Site not active")
            return roaster_data

        roaster_data["active"] = True

        try:
            # Fetch main page
            html_content = await self._fetch_page(url, force_refresh)
            soup = BeautifulSoup(html_content, "html.parser")

            # Detect platform - call only once and pass to other functions
            platform = await detect_platform(url)
            roaster_data["platform"] = platform

            # Extract basic info - pass platform parameter
            await self._extract_basic_info(roaster_data, soup, html_content, url, platform)

            # Extract contact info - pass platform parameter
            self._extract_contact_info(roaster_data, soup, html_content, platform)

            # Scrape about pages if needed - pass platform
            if not roaster_data.get("description") or not roaster_data.get("founded_year"):
                about_data = await extract_about_page_info(url, platform, force_refresh)
                roaster_data = update_with_about_data(roaster_data, about_data)

            # Enrich missing critical fields (Crawl4AI+DeepSeek, comprehensive)
            roaster_data = await enrich_roaster_data_with_crawl4ai(roaster_data, url)

            # Clean up data before returning
            roaster_data = self._cleanup_data(roaster_data)

            return roaster_data

        except Exception as e:
            logger.error(f"Error scraping {name} ({url}): {str(e)}")
            traceback.print_exc()
            roaster_data["error"] = str(e)
            return roaster_data

    async def _check_site_activity(self, url: str) -> Dict[str, Any]:
        """Check if a website is active and accessible."""
        # Implementation remains in the core class
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, follow_redirects=True, timeout=10)
                return {
                    "active": response.status_code < 400,
                    "final_url": str(response.url),
                    "status_code": response.status_code,
                }
        except Exception as e:
            return {"active": False, "error": str(e)}

    async def _fetch_page(self, url: str, force_refresh: bool = False) -> str:
        """Fetch a page with caching."""
        if not force_refresh:
            cached = cache.get_cached_html(url)
            if cached:
                return cached

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, follow_redirects=True, timeout=10)
                html = response.text
                cache.cache_html(url, html)
                return html
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            raise

    async def _extract_basic_info(
        self, roaster_data: Dict[str, Any], soup: BeautifulSoup, html_content: str, url: str, platform: str
    ) -> None:
        """Extract basic information from roaster homepage."""
        # Extract logo
        logo_url = extract_logo(soup, url)
        if logo_url:
            roaster_data["logo_url"] = logo_url

        # Extract hero image
        hero_image = extract_hero_image(soup, url)
        if hero_image:
            roaster_data["hero_image_url"] = hero_image

        # Extract founded year if available
        founded_year = extract_founded_year(html_content)
        if founded_year:
            roaster_data["founded_year"] = founded_year

        # Check business features
        roaster_data = check_business_features(roaster_data, soup, html_content)

        # Extract description
        description = extract_description(soup, html_content)
        if description:
            roaster_data["description"] = description
        # Extract location info
        roaster_data = await extract_location(roaster_data, soup, html_content, platform, url)

        # Extract tags
        roaster_data = extract_tags(soup, html_content, roaster_data)

    def _extract_contact_info(
        self, roaster_data: Dict[str, Any], soup: BeautifulSoup, html_content: str, platform: str
    ) -> None:
        """Extract all contact information using platform-specific selectors."""
        # Extract email
        email = extract_email(soup, html_content, roaster_data)
        if email:
            roaster_data["email"] = email

        # Extract phone number
        phone = extract_phone_number(soup, html_content)
        if phone:
            roaster_data["phone"] = phone

        # Extract social links
        social_links = extract_social_links(soup)
        if social_links:
            roaster_data["social_links"] = social_links

    def _extract_shopify_structured_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract Shopify specific structured data."""
        # Keep this helper in the core class
        structured_data = {}

        # Look for JSON-LD data
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)

                # Store JSON can have address
                if isinstance(data, dict) and data.get("@type") == "Store":
                    structured_data.update(
                        {
                            "name": data.get("name"),
                            "description": data.get("description"),
                            "address": data.get("address"),
                            "phone": data.get("telephone"),
                        }
                    )
            except Exception:
                continue

        return structured_data

    def _cleanup_data(self, roaster_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up roaster data before returning."""
        # Debug the address value before cleanup
        logger.info(f"Address before cleanup: {roaster_data.get('address')}")

        # Remove empty values, but keep address field even if empty
        cleaned_data = {}
        for k, v in roaster_data.items():
            if k == "address" or (v is not None and v != ""):
                cleaned_data[k] = v

        roaster_data = cleaned_data

        # Clean HTML from text fields
        for field in ["description", "address"]:
            if field in roaster_data and isinstance(roaster_data[field], str):
                roaster_data[field] = clean_html(roaster_data[field])

        # Debug the address value after cleanup
        logger.info(f"Address after cleanup: {roaster_data.get('address')}")

        # Normalize field names
        field_mapping = {"email": "contact_email", "phone": "contact_phone", "hero_image_url": "image_url"}

        for old_key, new_key in field_mapping.items():
            if old_key in roaster_data:
                roaster_data[new_key] = roaster_data.pop(old_key)

        # Extract instagram_handle from social_links if present
        if "social_links" in roaster_data:
            social_links_data = roaster_data["social_links"]
            # Ensure social_links is a list as required by the model
            if isinstance(social_links_data, dict):
                # Extract Instagram handle if available
                if "instagram_handle" in social_links_data:
                    roaster_data["instagram_handle"] = social_links_data.pop("instagram_handle")

                # Convert dict values to list of strings for social_links
                roaster_data["social_links"] = [str(v) for v in social_links_data.values() if v is not None]
            elif isinstance(social_links_data, list):
                # Ensure it's a list of strings
                roaster_data["social_links"] = [str(v) for v in social_links_data if v is not None]
            else:
                # Handle unexpected types, maybe set to empty list or log a warning
                roaster_data["social_links"] = []

        # Ensure is_active and is_verified fields exist
        # Use .pop() with a default to handle cases where 'active' might not exist
        roaster_data["is_active"] = roaster_data.pop("active", True)
        roaster_data["is_verified"] = roaster_data.pop(
            "is_verified", False
        )  # Keep existing if present, default to False

        # Remove temp fields if needed
        temp_fields = ["confidence", "error"]  # Removed 'active' as it's handled above
        for field in temp_fields:
            if field in roaster_data:
                roaster_data.pop(field)

        return roaster_data
