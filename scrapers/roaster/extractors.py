"""Basic extraction utilities for roaster scraping."""

import logging
import re
from typing import Any, Dict, Optional

from bs4 import BeautifulSoup

from common.utils import get_domain_from_url, normalize_phone_number, normalize_url

logger = logging.getLogger(__name__)


def extract_logo(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    """Extract logo URL from website."""
    # Check for logo in image filenames
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if "logo" in src.lower():
            # Make sure it's an absolute URL
            url = ensure_absolute_url(src, base_url)
            return normalize_url(url)

    # If no logo found, try header image
    header = soup.find("header")
    if header:
        header_img = header.find("img")
        if header_img and header_img.get("src"):
            url = ensure_absolute_url(header_img["src"], base_url)
            return normalize_url(url)

    # Favicon fallback
    favicon_link = soup.find("link", rel=lambda r: r and ("icon" in r.lower()))
    if favicon_link and favicon_link.get("href"):
        url = ensure_absolute_url(favicon_link["href"], base_url)
        return normalize_url(url)

    # Try default favicon.ico
    url = f"{base_url.rstrip('/')}/favicon.ico"
    return normalize_url(url)


def extract_description(soup: BeautifulSoup, html_content: str) -> Optional[str]:
    """Extract meaningful description from website."""
    # First try meta description (usually high quality)
    meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", property="og:description")
    if meta_desc and meta_desc.get("content", "").strip():
        desc = meta_desc["content"].strip()
        # Filter out common JavaScript warnings
        if not desc.startswith("JavaScript seems to be disabled"):
            return desc

    # Look for main content areas and substantial paragraphs
    content_selectors = ["main", "#content", ".content", "article", ".main-content", "#main-content"]

    for selector in content_selectors:
        content = soup.select_one(selector)
        if content:
            # Find all paragraphs in this content area
            paragraphs = content.select("p")
            substantial_paragraphs = [p.text.strip() for p in paragraphs if len(p.text.strip()) > 100]

            if substantial_paragraphs:
                # Find the most relevant paragraph (mentions coffee, beans, etc.)
                coffee_paragraphs = [
                    p
                    for p in substantial_paragraphs
                    if any(word in p.lower() for word in ["coffee", "roast", "bean", "brew"])
                ]
                if coffee_paragraphs:
                    return coffee_paragraphs[0]
                # Otherwise return the longest paragraph
                return max(substantial_paragraphs, key=len)

    # As a fallback, check the entire page for substantial paragraphs
    all_paragraphs = [p.text.strip() for p in soup.select("p") if len(p.text.strip()) > 100]
    if all_paragraphs:
        return max(all_paragraphs, key=len)

    return None


def extract_email(soup: BeautifulSoup, html_content: str, roaster_data: Dict[str, Any]) -> Optional[str]:
    """Extract email address from page content."""
    # Try to find mailto links
    email_links = soup.select('a[href^="mailto:"]')
    if email_links:
        href = email_links[0].get("href", "")
        email_match = re.search(r"mailto:([\w.+-]+@[\w-]+\.[\w.-]+)", href)
        if email_match:
            return email_match.group(1)

    # Try to find emails in text
    email_pattern = r"[\w.+-]+@[\w-]+\.[\w.-]+"

    # First look for business emails with the domain matching the website
    domain = get_domain_from_url(roaster_data.get("website_url", ""))
    if domain:
        domain_email_pattern = f"[\\w.+-]+@{re.escape(domain)}"
        domain_matches = re.findall(domain_email_pattern, html_content)
        if domain_matches:
            return domain_matches[0]

    # Look for common business email patterns
    business_patterns = [
        r"info@[\w-]+\.[\w.-]+",
        r"contact@[\w-]+\.[\w.-]+",
        r"hello@[\w-]+\.[\w.-]+",
        r"support@[\w-]+\.[\w.-]+",
    ]

    for pattern in business_patterns:
        matches = re.findall(pattern, html_content)
        if matches:
            return matches[0]

    # Try general email pattern
    email_matches = re.findall(email_pattern, html_content)

    if email_matches:
        # Filter out common false positives
        filtered_emails = [
            email
            for email in email_matches
            if not any(fp in email for fp in ["@example", "@domain", "@email", "@godaddy", "filler@"])
        ]
        if filtered_emails:
            return filtered_emails[0]

    return None


def extract_hero_image(soup: BeautifulSoup, url: str) -> Optional[str]:
    """Extract hero/banner image from website."""
    # Common selectors for hero/banner images
    selectors = [
        ".hero img",
        ".banner img",
        ".hero-image",
        ".banner-image",
        ".main-banner img",
        ".slideshow img:first-child",
        ".hero-banner img",
        ".slides img:first-child",
        ".splash img",
        ".carousel-item:first-child img",
        ".carousel img:first-child",
        ".home-banner img",
        ".featured-image img",
        '[data-section-type="hero"] img',
        '[data-section-type="slideshow"] img',
    ]

    # Try each selector
    for selector in selectors:
        elements = soup.select(selector)
        if elements and elements[0].get("src"):
            src = elements[0]["src"]
            url = ensure_absolute_url(src, url)
            return normalize_url(url)

    # Try to find large images (likely to be banner/hero)
    large_images = []
    for img in soup.find_all("img"):
        # Skip small icons, logos, etc.
        if img.get("width") and img.get("height"):
            try:
                width = int(img["width"])
                height = int(img["height"])
                if width >= 800 and height >= 400:
                    large_images.append((img, width * height))
            except (ValueError, TypeError):
                pass

    # Sort by size (largest first)
    large_images.sort(key=lambda x: x[1], reverse=True)

    # Return the largest image
    if large_images and large_images[0][0].get("src"):
        src = large_images[0][0]["src"]
        url = ensure_absolute_url(src, url)
        return normalize_url(url)

    return None


def extract_phone_number(soup: BeautifulSoup, html_content: str) -> Optional[str]:
    """Extract phone number from website."""
    # Try finding phone number in link
    phone_links = soup.select('a[href^="tel:"]')
    if phone_links:
        href = phone_links[0].get("href", "")
        phone_match = re.search(r"tel:([\d\+\-\(\)\s]+)", href)
        if phone_match:
            return phone_match.group(1)

    # Try finding phone number in text
    phone_patterns = [
        r"\+91[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{4}",  # +91 format
        r"0?\d{3}[-\s]?\d{3}[-\s]?\d{4}",  # 10 digit format
        r"0?\d{10}",  # 10 digits without separators
    ]

    for pattern in phone_patterns:
        matches = re.findall(pattern, html_content)
        if matches:
            phone_number = matches[0]
            normalized_phone_number = normalize_phone_number(phone_number)
            return normalized_phone_number

    return None


def extract_founded_year(html_content: str) -> Optional[int]:
    """Extract founded year from website."""
    if not html_content:
        return None

    # Enhanced patterns
    founded_patterns = [
        r"founded in (\d{4})",
        r"established in (\d{4})",
        r"since (\d{4})",
        r"est\. (\d{4})",
        r"started in (\d{4})",
        r"began in (\d{4})",
        r"founded.*?(\d{4})",
        r"established.*?(\d{4})",
        # New patterns
        r"[Ss]tarted in (\d{4})[,\s]",  # For "Started in 1896, Baarbara Estate"
        r"in (\d{4}),.*?[Bb]egan",  # For pattern like "In 1896, the estate began..."
        r"[Ff]ounded:?\s*(\d{4})",  # For "Founded: 1896"
        r"[Ee]stablished:?\s*(\d{4})",  # For "Established: 1896"
    ]

    for pattern in founded_patterns:
        matches = re.search(pattern, html_content, re.IGNORECASE)
        if matches:
            try:
                year = int(matches.group(1))
                if 1800 < year < 2024:  # Sanity check for valid years
                    return year
            except ValueError:
                continue

    return None


def check_business_features(roaster_data: Dict[str, Any], soup: BeautifulSoup, html_content: str) -> Dict[str, Any]:
    """Check for business features like subscription and physical store."""
    # Check for subscription
    sub_indicators = ["subscription", "subscribe", "recurring", "monthly delivery"]
    roaster_data["has_subscription"] = any(indicator in html_content.lower() for indicator in sub_indicators)

    # Check for physical store
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

    # Higher confidence if there's an embedded map
    if soup.find("iframe", src=lambda s: s and ("map" in s.lower() or "google.com/maps" in s.lower())):
        roaster_data["has_physical_store"] = True
    else:
        # Check for address indicators
        roaster_data["has_physical_store"] = any(indicator in html_content.lower() for indicator in store_indicators)

    return roaster_data


def ensure_absolute_url(url: str, base_url: str) -> str:
    """Ensure a URL is absolute."""
    if url.startswith(("http://", "https://", "//")):
        return url
    elif url.startswith("/"):
        return f"{base_url.rstrip('/')}{url}"
    else:
        return f"{base_url.rstrip('/')}/{url}"


def extract_social_links(soup: BeautifulSoup) -> Dict[str, str]:
    """Extract social media links from website."""
    social_links = {}
    social_platforms = {
        "facebook": ["facebook.com", "fb.com"],
        "twitter": ["twitter.com", "x.com"],
        "instagram": ["instagram.com"],
        "linkedin": ["linkedin.com"],
        "youtube": ["youtube.com"],
    }

    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        for platform, domains in social_platforms.items():
            if any(domain in href for domain in domains):
                social_links[platform] = normalize_url(href)
                # Special handling for Instagram to extract handle
                if platform == "instagram" and "/p/" not in href:
                    handle = href.split("instagram.com/")[-1].split("/")[0]
                    if handle and not handle.startswith("?"):
                        social_links["instagram_handle"] = handle
                break

    return social_links


def extract_tags(soup, html_content, roaster_data):
    """Extract tags based on content keywords."""
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

    # Add platform as a tag
    if "platform" in roaster_data and roaster_data["platform"] not in ["static", "unknown"]:
        tags.append(roaster_data["platform"])

    if tags:
        roaster_data["tags"] = tags

    return roaster_data
