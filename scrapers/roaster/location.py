"""Location extraction for roaster scraping."""

import json
import re
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
import logging
import requests 

from .selectors import get_platform_selectors
from common.utils import fetch_with_retry # Added import for fetch_with_retry
import urllib.parse # Added import for URL decoding

logger = logging.getLogger(__name__)

def extract_address_from_text(text: str) -> Optional[str]:
    """Extract address components from text using regex and keywords."""
    # Clean up the text, removing excessive whitespace and newlines
    cleaned_text = re.sub(r'\s+', ' ', text).strip()

    # Look for common address patterns (e.g., with PIN codes)
    # This regex is a starting point and can be refined
    address_pattern = r'\b\d{6}\b' # Look for a 6-digit PIN code
    match = re.search(address_pattern, cleaned_text)
    if match:
        # Attempt to extract a larger block around the PIN code
        start = max(0, match.start() - 100)
        end = min(len(cleaned_text), match.end() + 100)
        context = cleaned_text[start:end]
        # Further refine extraction from context if needed
        return context.strip()

    # Look for lines containing address keywords
    address_lines = [line.strip() for line in cleaned_text.split('\n') if any(word in line.lower() for word in ['address', 'location', 'find us', 'visit us'])]
    if address_lines:
        # Return the most substantial line or a combination
        return max(address_lines, key=len) if address_lines else None

    # If no specific patterns matched, return the cleaned text if it seems address-like
    # This is a fallback and might return non-address text
    if len(cleaned_text) > 20 and any(word in cleaned_text.lower() for word in ['street', 'road', 'area', 'nagar', 'colony']):
         return cleaned_text

    return None


async def extract_location_from_contact_page(base_url: str, platform: str, force_refresh: bool = False) -> Optional[str]:
    """Extract address from dedicated contact page."""
    # Get platform-specific selectors
    selectors = get_platform_selectors(platform)
    
    # Use platform-specific contact page paths and add more common suffixes
    contact_suffixes = selectors["contact_page"] 
    
    for suffix in contact_suffixes:
        try:
            contact_url = base_url.rstrip('/') + suffix
            logger.info(f"Trying contact page for address: {contact_url}")
            
            # Fetch the contact page with more robust error handling
            try:
                response = await fetch_with_retry(contact_url)
                response.raise_for_status() # Raise an exception for bad status codes
                html_content = response.text
            except requests.exceptions.RequestException as e:
                logger.debug(f"Failed to fetch contact page {contact_url}: {e}")
                continue
            except Exception as e:
                logger.debug(f"An unexpected error occurred while fetching {contact_url}: {e}")
                continue
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Try to find address blocks first (highest confidence)
            address_blocks = soup.select('address, .address, [itemprop="address"], .address-block, .location-address, div[class*="address"]')
            if address_blocks:
                # Use the most substantial address block
                addresses = [block.text.strip() for block in address_blocks]
                if addresses:
                    return max(addresses, key=len)
            
            # Try contact sections with more general selectors
            contact_section_selectors = selectors["contact_section"] + ["div[class*='contact']", "section[class*='contact']", "aside[class*='contact']"]
            for selector in contact_section_selectors:
                sections = soup.select(selector)
                for section in sections:
                    # Look for paragraphs that likely contain addresses
                    section_text = section.text.strip()
                    if any(word in section_text.lower() for word in ['address', 'location', 'find us']):
                        # Use the helper function to extract and clean the address
                        address = extract_address_from_text(section_text)
                        if address:
                            return address
                        
            # Look for embedded Google Maps iframe
            map_iframe = soup.find('iframe', src=lambda s: s and 'google.com/maps' in s)
            if map_iframe and map_iframe.get('src'):
                src = map_iframe['src']
                # Extract address from Google Maps URL using a more robust regex
                match = re.search(r'(?:q=|\/place\/)([^&/]+)', src)
                if match:
                    address = match.group(1).replace('+', ' ')
                    # URL-decode the address
                    address = urllib.parse.unquote(address)
                    return address
        
        except Exception as e:
            logger.warning(f"Error accessing contact page {suffix} for address: {e}")
    
    return None

async def extract_location(roaster_data: Dict[str, Any], soup: BeautifulSoup, html_content: str, platform: str, base_url: str) -> Dict[str, Any]:
    """Extract full address from website."""
    # Initialize with country (default to India)
    roaster_data["country"] = "India"

    # Debug logging
    logger.info(f"Extracting location from {base_url} (platform: {platform})")

    # First try to get address from main page
    address = extract_location_from_page(soup, html_content, platform)
    if address:
        logger.info(f"Found address on main page: {address}")
        roaster_data["address"] = address
    else:
        logger.debug("No address found on main page")

    # If no address found on main page, try contact page
    try:
        contact_address = await extract_location_from_contact_page(base_url, platform)
        if contact_address:
            logger.info(f"Found address on contact page: {contact_address}")
            roaster_data["address"] = contact_address
        else:
            logger.debug("No address found on contact page")
    except Exception as e:
        logger.error(f"Error extracting address from contact page: {str(e)}")

    # Final validation
    if roaster_data.get("address"):
        logger.info(f"✅ Final extracted address: {roaster_data['address']}")
    else:
        logger.warning(f"No address found for {base_url}, setting default city/state")
        roaster_data["city"] = None
        roaster_data["state"] = None

    return roaster_data

def extract_location_from_page(soup: BeautifulSoup, html_content: str, platform: str) -> Optional[str]:
    """Extract address from the current page."""
    # Get platform-specific selectors
    selectors = get_platform_selectors(platform)

    # Debug logging
    logger.debug(f"Extracting location from page (platform: {platform})")

    # Try to find address blocks first (highest confidence)
    address_blocks = soup.select('address, .address, [itemprop="address"], .address-block, .location-address, div[class*="address"]')
    if address_blocks:
        # Use the most substantial address block
        addresses = [block.text.strip() for block in address_blocks]
        if addresses:
            address = max(addresses, key=len)
            logger.debug(f"Found address in address block: {address}")
            return address

    # Try contact sections next
    for selector in selectors["contact_section"]:
        sections = soup.select(selector)
        if sections:
            logger.debug(f"Found {len(sections)} contact sections with selector: {selector}")
            for section in sections:
                # Look for paragraphs that likely contain addresses
                section_text = section.text.strip()
                if any(word in section_text.lower() for word in ['address', 'location', 'find us']):
                    # Use the helper function to extract and clean the address
                    address = extract_address_from_text(section_text)
                    if address:
                        logger.debug(f"Found address in contact section: {address}")
                        return address

    # Look for footer sections, which often contain address
    footer = soup.select_one('footer')
    if footer:
        logger.debug("Checking footer for address")
        # Look for address-like content in footer using more specific selectors
        footer_address_elements = footer.select('address, .address, [itemprop="address"], .contact-info, .footer-address')
        if footer_address_elements:
             addresses = [elem.text.strip() for elem in footer_address_elements]
             if addresses:
                 address = max(addresses, key=len)
                 # Use the helper function to extract and clean the address
                 extracted_address = extract_address_from_text(address)
                 if extracted_address:
                     logger.debug(f"Found address in footer using specific selectors: {extracted_address}")
                     return extracted_address


        # Fallback to looking for address-like content in paragraphs and divs
        for elem in footer.select('p, div'):
            text = elem.text.strip()
            if len(text) > 10 and any(word in text.lower() for word in ['address', 'location', 'visit', 'find us']):
                # Use the helper function to extract and clean the address
                address = extract_address_from_text(text)
                if address:
                    logger.debug(f"Found potential address in footer: {address}")
                    return address

    # Check for structured data
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and data.get("address"):
                address_parts = []
                address_obj = data["address"]
                for field in ["streetAddress", "addressLocality", "addressRegion", "postalCode"]:
                    if address_obj.get(field):
                        address_parts.append(address_obj[field])

                if address_parts:
                    address = ", ".join(address_parts)
                    # Use the helper function to extract and clean the address
                    extracted_address = extract_address_from_text(address)
                    if extracted_address:
                        logger.debug(f"Found address in structured data: {extracted_address}")
                        return extracted_address
        except Exception as e:
            logger.debug(f"Error parsing structured data for address: {e}")

    # Look for embedded Google Maps iframe, which often has address in URL
    map_iframe = soup.find('iframe', src=lambda s: s and 'google.com/maps' in s)
    if map_iframe and map_iframe.get('src'):
        src = map_iframe['src']
        # Extract address from Google Maps URL using a more robust regex
        match = re.search(r'(?:q=|\/place\/)([^&/]+)', src)
        if match:
            address = match.group(1).replace('+', ' ')
            # URL-decode the address
            address = urllib.parse.unquote(address)
            # Use the helper function to extract and clean the address
            extracted_address = extract_address_from_text(address)
            if extracted_address:
                logger.debug(f"Found address in Google Maps iframe: {extracted_address}")
                return extracted_address

    logger.debug("No address found on page")
    return None
