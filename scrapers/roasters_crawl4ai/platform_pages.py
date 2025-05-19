def get_platform_page_paths(platform: str = None, page_type: str = "about"):
    """
    Return a list of about/contact page paths for the given platform.
    page_type: "about" or "contact"
    """
    # Hardcoded mapping (do not import from selectors.py)
    platform_selectors = {
        "shopify": {
            "contact": ["/pages/contact", "/pages/contact-us", "/pages/locations", "/contact"],
            "about": ["/pages/about", "/pages/about-us", "/pages/our-story", "/pages/story"]
        },
        "woocommerce": {
            "contact": ["/contact", "/contact-us", "/about/contact", "/locations"],
            "about": ["/about", "/about-us", "/our-story", "/story", "/about/story"]
        },
        "wordpress": {
            "contact": ["/contact", "/contact-us", "/get-in-touch", "/locations"],
            "about": ["/about", "/about-us", "/who-we-are", "/our-story"]
        },
        "magento": {
            "contact": ["/contact", "/contact-us", "/customer-service"],
            "about": ["/about", "/about-us", "/company", "/our-story"]
        },
        "squarespace": {
            "contact": ["/contact", "/contact-us", "/locations"],
            "about": ["/about", "/about-us", "/our-story"]
        },
        "webflow": {
            "contact": ["/contact", "/contact-us", "/get-in-touch"],
            "about": ["/about", "/about-us", "/our-story"]
        }
    }
    
    if platform and platform.lower() in platform_selectors:
        return platform_selectors[platform.lower()].get(page_type, [])
    # Default fallback
    if page_type == "about":
        return ["/about", "/about-us", "/our-story", "/about/story", "/story"]
    elif page_type == "contact":
        return ["/contact", "/contact-us", "/reach-us", "/get-in-touch", "/locations", "/stores", "/cafes", "/our-stores", "/our-cafes"]
    return []
