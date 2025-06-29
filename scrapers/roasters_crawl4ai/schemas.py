# scrapers/roasters-crawl4ai/schemas.py
"""Extraction schemas for Crawl4AI."""

# CSS/XPath extraction schemas
CONTACT_SCHEMA = {
    "name": "RoasterContact",
    "baseSelector": "body",
    "fields": [
        {"name": "email", "selector": "a[href^='mailto:']", "type": "attribute", "attribute": "href"},
        {"name": "phone", "selector": "a[href^='tel:']", "type": "attribute", "attribute": "href"},
        {
            "name": "address",
            "selector": "address, .address, [itemprop='address'], .footer-address, .location, .contact-info, .store-info, .location-info, .store-address, .contact-details",
            "type": "text",
        },
        {"name": "instagram", "selector": "a[href*='instagram.com']", "type": "attribute", "attribute": "href"},
        {"name": "facebook", "selector": "a[href*='facebook.com']", "type": "attribute", "attribute": "href"},
        {
            "name": "twitter",
            "selector": "a[href*='twitter.com'], a[href*='x.com']",
            "type": "attribute",
            "attribute": "href",
        },
        {"name": "linkedin", "selector": "a[href*='linkedin.com']", "type": "attribute", "attribute": "href"},
    ],
}

ADDRESS_SCHEMA = {
    "name": "AddressInfo",
    "baseSelector": "body",
    "fields": [
        {
            "name": "address",
            "selector": "address, .address, [itemprop='address'], .footer-address, .location, .contact-info, .store-info, .contact-details, .store-address, .location-details, footer p, .footer p, .contact-us p",
            "type": "text",
        },
        {
            "name": "stores_text",
            "selector": ".store-locations, .cafe-locations, .locations, .contact-address",
            "type": "text",
        },
        {"name": "footer_text", "selector": "footer, .footer", "type": "text"},
        {"name": "full_text", "selector": "body", "type": "text"},
    ],
}

ABOUT_SCHEMA = {
    "name": "RoasterAbout",
    "baseSelector": "body",
    "fields": [
        {
            "name": "meta_description",
            "selector": "meta[name='description'], meta[property='og:description']",
            "type": "attribute",
            "attribute": "content",
        },
        {
            "name": "about_text",
            "selector": ".about-content p, .about-us p, .our-story p, .about p, .story p, .about-section p, section p, .page-content p",
            "type": "text",
        },
        {
            "name": "main_content",
            "selector": "main, #MainContent, #main-content, .main-content, .page-width",
            "type": "text",
        },
        {
            "name": "logo_url",
            "selector": "a.logo img, .logo img, header img, img[alt*='logo']",
            "type": "attribute",
            "attribute": "src",
        },
        {
            "name": "hero_image_url",
            "selector": ".hero img, .banner img, .hero-image, .banner-image, .main-banner img",
            "type": "attribute",
            "attribute": "src",
        },
    ],
}

# LLM extraction schema
ROASTER_LLM_SCHEMA = {
    "description": {"type": "string", "description": "About the company or roaster"},
    "founded_year": {"type": "integer", "description": "Year the company was established"},
    "has_subscription": {"type": "boolean", "description": "Whether they offer a subscription service"},
    "has_physical_store": {"type": "boolean", "description": "Whether they have a physical retail location"},
    "city": {"type": "string", "description": "The city where the roaster is located"},
    "state": {"type": "string", "description": "The state where the roaster is located"},
    "address": {"type": "string", "description": "The address of the roaster main office or headquarters"},
}

# LLM extraction instructions
ROASTER_LLM_INSTRUCTIONS = """
Extract the following information about this coffee roaster:
- description: A concise description of the company or roaster (paragraph form)
- founded_year: The year the company was established (integer only)
- has_subscription: Whether they offer a subscription service (boolean)
- has_physical_store: Whether they have a physical retail location (boolean)
- city: The city where the roaster is located in India (string)
- state: The state where the roaster is located in India (string)
- address: The address of the roaster main office or headquarters (string)

For the description:
- If you can't find an explicit description, synthesize one based on what you can infer about the company from the website.
- Include information about their coffee sourcing, roasting methods, or philosophy if available.
- Aim for 2-3 sentences that capture the essence of the business.

For address information:
- Look for full street addresses (e.g., "123 Coffee Street, Bangalore")
- Check for contact pages, about pages, and footers
- Look for PIN codes (6-digit numbers) which indicate Indian addresses
- Note locations of cafes, stores, or headquarters

Only return information you're confident about
Return values as a JSON object. Do not include fields where no information was found.
"""
