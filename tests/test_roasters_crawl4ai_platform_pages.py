import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scrapers.roasters_crawl4ai.platform_pages import get_platform_page_paths

def test_get_platform_page_paths_known_platform():
    # Shopify about
    about = get_platform_page_paths("shopify", "about")
    assert "/pages/about" in about
    # Shopify contact
    contact = get_platform_page_paths("shopify", "contact")
    assert "/pages/contact" in contact
    # WooCommerce about
    about_wc = get_platform_page_paths("woocommerce", "about")
    assert "/about" in about_wc


def test_get_platform_page_paths_unknown_platform():
    # Unknown platform returns fallback
    about = get_platform_page_paths("unknown", "about")
    assert "/about" in about
    contact = get_platform_page_paths("unknown", "contact")
    assert "/contact" in contact


def test_get_platform_page_paths_no_platform():
    # No platform returns fallback
    about = get_platform_page_paths(page_type="about")
    assert "/about-us" in about
    contact = get_platform_page_paths(page_type="contact")
    assert "/contact-us" in contact


def test_get_platform_page_paths_invalid_type():
    # Invalid type returns empty list
    assert get_platform_page_paths("shopify", "foo") == []
    assert get_platform_page_paths(page_type="foo") == []
