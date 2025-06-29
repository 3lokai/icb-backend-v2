import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from common import cache


def test_scraper_cache_smoke(tmp_path):
    # Use a temp cache dir
    test_cache_dir = tmp_path / "cache"
    test_cache_dir.mkdir()
    c = cache.ScraperCache(cache_dir=str(test_cache_dir))

    # Test cache_roaster and get_cached_roaster
    roaster = {"name": "Test Roaster", "website_url": "https://test.com"}
    c.cache_roaster(roaster)
    cached = c.get_cached_roaster("Test Roaster", "https://test.com")
    assert cached is not None
    assert cached["name"] == "Test Roaster"

    # Test cache_html and get_cached_html
    c.cache_html("https://test.com/page", "<html>data</html>")
    html = c.get_cached_html("https://test.com/page")
    assert html == "<html>data</html>"

    # Test cache_products and get_cached_products
    products = [{"id": 1, "name": "Coffee"}]
    c.cache_products("roaster1", products)
    cached_products = c.get_cached_products("roaster1")
    assert isinstance(cached_products, list)
    assert cached_products[0]["name"] == "Coffee"

    # Test clear_cache
    c.clear_cache()
    # Allow empty subdirectories to remain; check all files are deleted
    for root, dirs, files in os.walk(test_cache_dir):
        assert not files  # No files should remain
