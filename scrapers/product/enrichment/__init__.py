# scrapers/product/enrichment/__init__.py
"""
Enrichment modules for enhancing coffee product data.
"""

from scrapers.product.enrichment.deepseek import (
    enhance_with_deepseek,
    batch_enhance_coffees,
    needs_enhancement
)

__all__ = [
    'enhance_with_deepseek',
    'batch_enhance_coffees',
    'needs_enhancement'
]