"""About page extraction for roaster scraping."""

import logging
from typing import Any, Dict

from bs4 import BeautifulSoup

from common.utils import fetch_with_retry

from .extractors import extract_founded_year
from .location import extract_location
from .selectors import get_platform_selectors

logger = logging.getLogger(__name__)


async def extract_about_page_info(base_url: str, platform: str, force_refresh: bool = False) -> Dict[str, Any]:
    """Extract information from about pages."""
    about_data = {}
    confidence_score = 0  # Track how confident we are in the data

    # Get platform-specific selectors
    selectors = get_platform_selectors(platform)

    # Use platform-specific about page paths
    about_suffixes = selectors["about_page"]

    for suffix in about_suffixes:
        try:
            about_url = base_url.rstrip("/") + suffix
            logger.info(f"Trying about page: {about_url}")

            # Fetch the about page
            try:
                response = await fetch_with_retry(about_url)
                html_content = response.text
            except Exception as e:
                logger.debug(f"Failed to fetch about page {about_url}: {e}")
                continue

            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_content, "html.parser")

            # Extract description if not already found
            if not about_data.get("description"):
                # First try to find sections with "about" or "story" in the heading
                about_sections = []
                for heading in soup.find_all(["h1", "h2", "h3"]):
                    if any(term in heading.text.lower() for term in ["about", "story", "journey", "who we are"]):
                        # Get next element which might be a paragraph
                        next_elem = heading.find_next(["p", "div"])
                        if next_elem and len(next_elem.text.strip()) > 100:
                            about_sections.append(next_elem.text.strip())
                            confidence_score += 5  # Higher confidence as it's under a relevant heading

                if about_sections:
                    about_data["description"] = about_sections[0]
                else:
                    # Fall back to any substantial paragraph
                    paragraphs = [p.text.strip() for p in soup.find_all("p") if len(p.text.strip()) > 100]
                    if paragraphs:
                        about_data["description"] = paragraphs[0]
                        confidence_score += 2  # Lower confidence as it's just a paragraph

            # Look for founded year
            founded_year = extract_founded_year(html_content)
            if founded_year:
                about_data["founded_year"] = founded_year
                confidence_score += 4

            # Extract location from about page
            await extract_location(about_data, soup, html_content, platform, about_url)

            # If we got both description and founded year with high confidence, we can stop
            if about_data.get("description") and about_data.get("founded_year") and confidence_score >= 8:
                break

        except Exception as e:
            logger.warning(f"Error accessing about page {suffix}: {e}")

    # Add confidence scores
    about_data["confidence"] = confidence_score
    return about_data


def update_with_about_data(roaster_data: Dict[str, Any], about_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update roaster data with information from about pages."""
    if not about_data:
        return roaster_data

    # Update description if the about page version is better
    if about_data.get("description") and (
        not roaster_data.get("description") or len(about_data["description"]) > len(roaster_data["description"]) * 1.5
    ):
        roaster_data["description"] = about_data["description"]
        # Update confidence score
        if about_data.get("confidence", 0) > roaster_data.get("confidence", {}).get("description", 0):
            roaster_data["confidence"]["description"] = about_data["confidence"]

    # Update founded year if found on about page
    if about_data.get("founded_year") and not roaster_data.get("founded_year"):
        roaster_data["founded_year"] = about_data["founded_year"]

    # Update address if found on about page
    if about_data.get("address") and not roaster_data.get("address"):
        roaster_data["address"] = about_data["address"]

    return roaster_data
