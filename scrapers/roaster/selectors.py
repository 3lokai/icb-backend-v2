"""Platform-specific selectors for roaster scraping."""

def get_platform_selectors(platform: str = None):
    """Get platform-specific selectors for different content types."""
    platform_selectors = {
            "shopify": {
                "contact_page": ["/pages/contact", "/pages/contact-us", "/pages/locations", "/contact"],
                "about_page": ["/pages/about", "/pages/about-us", "/pages/our-story", "/pages/story"],
                "contact_section": [".contact-form", "#ContactForm", ".contact-page", "footer .address", ".section--contact"],
                "address_elements": ["address", ".address", "[itemprop='address']", ".footer__store-info"],
                "social_links": [".social-links", ".social-icons", "footer .social", ".footer__social"],
                "logo": [".header__logo img", ".logo-image", "[data-header-logo]", ".site-header__logo img"]
            },
            "woocommerce": {
                "contact_page": ["/contact", "/contact-us", "/about/contact", "/locations"],
                "about_page": ["/about", "/about-us", "/our-story", "/story", "/about/story"],
                "contact_section": [".contact-form", "#contact-form", ".contact-page", ".widget_contact_info", ".wp-block-contact-form"],
                "address_elements": ["address", ".address", ".contact-info", ".store-address"],
                "social_links": [".social-links", ".social-icons", ".menu-social-container", ".footer-social"],
                "logo": [".site-logo img", ".custom-logo", "#logo img", ".header-logo img"]
            },
            "wordpress": {
                "contact_page": ["/contact", "/contact-us", "/get-in-touch", "/locations"],
                "about_page": ["/about", "/about-us", "/who-we-are", "/our-story"],
                "contact_section": [".contact-info", ".widget_contact_info", ".widget-contact", ".wp-block-contact-form"],
                "address_elements": ["address", ".address", ".location", ".footer-address"],
                "social_links": [".social-links", ".social-media", ".social-navigation", ".footer-social"],
                "logo": [".site-logo img", ".custom-logo", ".logo img", ".header-logo img"]
            },
            "magento": {
                "contact_page": ["/contact", "/contact-us", "/customer-service"],
                "about_page": ["/about", "/about-us", "/company", "/our-story"],
                "contact_section": [".contact-info", ".footer-contacts", ".footer-address", ".block-contact"],
                "address_elements": ["address", ".address", "[itemprop='address']", ".footer__address"],
                "social_links": [".social-links", ".social-icons", ".footer-social", ".footer__social"],
                "logo": [".logo img", ".header-logo img", ".site-logo img"]
            },
            "squarespace": {
                "contact_page": ["/contact", "/contact-us", "/locations"],
                "about_page": ["/about", "/about-us", "/our-story"],
                "contact_section": [".contact-info", ".footer-blocks", ".sqs-block-content", ".sqs-block-form"],
                "address_elements": ["address", ".address", ".contact-info", ".sqs-block-address"],
                "social_links": [".sqs-svg-icon--list", ".social-icons", ".social-links", ".footer-social"],
                "logo": [".header-logo-image", ".logo-image", ".logo img", ".site-logo img"]
            },
            "webflow": {
                "contact_page": ["/contact", "/contact-us", "/get-in-touch"],
                "about_page": ["/about", "/about-us", "/our-story"],
                "contact_section": [".contact-info", ".footer-contact", ".w-layout-grid", ".contact-form"],
                "address_elements": ["address", ".address", ".location-info", ".footer-address"],
                "social_links": [".social-links", ".social-icons", ".footer-social", ".footer__social"],
                "logo": [".logo-image", ".brand img", ".navbar-logo-link img", ".site-logo img"]
            },
            "static": {  # Fallback for unknown platforms
                "contact_page": ["/contact", "/contact-us", "/reach-us", "/locations"],
                "about_page": ["/about", "/about-us", "/our-story", "/who-we-are"],
                "contact_section": [".contact", "#contact", "footer", ".footer", ".address", ".contact-form"],
                "address_elements": ["address", ".address", "[itemprop='address']", ".contact-info", ".footer-address"],
                "social_links": [".social", ".social-media", ".social-links", ".social-icons", ".footer-social"],
                "logo": [".logo", "#logo", "header img", ".brand img", ".site-logo img"]
            }
        }
    
    if platform and platform in platform_selectors:
        return platform_selectors[platform]
    
    return platform_selectors["static"]
