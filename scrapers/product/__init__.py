# scrapers/product/scrapers/__init__.py
"""
Platform-specific scrapers for coffee products.
"""

from scrapers.product.shopify import scrape_shopify, scrape_single_product as scrape_shopify_product
from scrapers.product.woocommerce import scrape_woocommerce, scrape_single_product as scrape_woocommerce_product
from scrapers.product.static import scrape_static_site, scrape_single_product as scrape_static_product

__all__ = [
    'scrape_shopify',
    'scrape_shopify_product',
    'scrape_woocommerce',
    'scrape_woocommerce_product',
    'scrape_static_site',
    'scrape_static_product'
]
