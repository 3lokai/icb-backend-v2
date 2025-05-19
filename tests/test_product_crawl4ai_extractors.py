import sys
import os
import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock

# Ensure project root is in sys.path for imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scrapers.product_crawl4ai.api_extractors import shopify, woocommerce

# --- Shopify Extractor Tests ---
@pytest.mark.asyncio
@patch('scrapers.product_crawl4ai.api_extractors.shopify.httpx.AsyncClient')
async def test_extract_products_shopify_success(mock_client):
    # Mock response for Shopify API
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = AsyncMock(return_value={
        'products': [
            {
                'id': 1,
                'title': 'Test Coffee',
                'handle': 'test-coffee',
                'tags': ['Medium Roast'],
                'variants': [{'id': 11, 'price': '15.00', 'title': '250g'}],
                'body_html': 'Tasting notes: chocolate, caramel',
            }
        ]
    })
    mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

    products = await shopify.extract_products_shopify('https://test.myshopify.com', 'roaster123')
    assert isinstance(products, list)
    assert products
    assert products[0].name == 'Test Coffee'

# --- WooCommerce Extractor Tests ---
@pytest.mark.asyncio
@patch('scrapers.product_crawl4ai.api_extractors.woocommerce.httpx.AsyncClient')
async def test_extract_products_woocommerce_success(mock_client):
    # Mock response for WooCommerce API
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = AsyncMock(return_value=[
        {
            'id': 2,
            'name': 'Woo Coffee',
            'tags': ['Light Roast'],  # Should be list of strings
            'description': 'Floral, citrus',
            'variations': [],
        }
    ])
    mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

    products = await woocommerce.extract_products_woocommerce('https://test.com', 'roaster456')
    assert isinstance(products, list)
    assert products
    assert products[0].name == 'Woo Coffee'

# --- Standardizer and Helper Tests ---
def test_standardize_shopify_product_handles_missing_fields():
    product = {
        'id': 3,
        'title': 'No Tags Coffee',
        'handle': 'no-tags-coffee',
        'variants': [{'id': 12, 'price': '10.00', 'title': '250g'}],
        'body_html': 'Tasting notes: nutty',
    }
    result = shopify.standardize_shopify_product(product, 'https://test.myshopify.com', 'roaster123')
    assert isinstance(result, dict)
    assert result['name'] == 'No Tags Coffee'
    assert 'prices' in result

def test_standardize_woocommerce_product_handles_missing_fields():
    woo_product = {
        'id': 4,
        'name': 'No Tags Woo',
        'description': 'Berry, sweet',
        'variations': [],
    }
    result = woocommerce.standardize_woocommerce_product(woo_product, 'https://test.com', 'roaster456')
    assert isinstance(result, dict)
    assert result['name'] == 'No Tags Woo'
    assert 'prices' in result

# --- Attribute Extraction Edge Cases ---
def test_extract_roast_level_from_shopify_handles_tag_variants():
    product = {'title': 'Espresso Roast', 'handle': 'espresso-roast'}
    tags = ['Espresso', 'Limited Edition']
    roast = shopify.extract_roast_level_from_shopify(product, tags)
    assert isinstance(roast, str)
    assert 'espresso' in roast.lower() or roast

def test_extract_processing_method_from_shopify_handles_multiple_sources():
    product = {'title': 'Natural Process', 'handle': 'natural-process'}
    tags = ['Natural', 'Single Origin']
    name = 'Natural Ethiopia'
    slug = 'natural-ethiopia'
    method = shopify.extract_processing_method_from_shopify(product, tags, name, slug)
    assert isinstance(method, str)
    assert 'natural' in method.lower() or method
