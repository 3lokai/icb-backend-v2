import asyncio
import pytest
from unittest.mock import patch, AsyncMock, MagicMock, call

from scrapers.product_crawl4ai.scraper import ProductScraper
from db.models import Coffee
from common.pydantic_utils import preprocess_coffee_data # For real preprocessor if needed

# Sample data for tests
SAMPLE_ROASTER_ID = "test_roaster_id"
SAMPLE_URL = "https://example.com"
SAMPLE_ROASTER_NAME = "Test Roaster"

RAW_PRODUCT_1 = {
    "name": "Test Coffee A",
    "description": "A test coffee.",
    "product_type": "Coffee",
    "direct_buy_url": f"{SAMPLE_URL}/product-a"
    # RAW_PRODUCT_1 intentionally does not contain the new fields,
    # as they are expected to be added during enrichment.
}

ENRICHED_PRODUCT_1 = {
    **RAW_PRODUCT_1,
    "origin": "Test Origin", # Existing field from previous version of tests
    "tasting_notes": "Test notes", # Existing field
    # New fields for enrichment
    "acidity": "Bright",
    "body": "Medium",
    "sweetness": "Caramel",
    "aroma": "Floral, Nutty", # Kept as string for db.models.Coffee
    "with_milk_suitable": True,
    "varietals": ["Typica", "Bourbon"],
    "altitude_meters": 1500,
    # Ensure flavor_profiles is also handled if it's part of enrichment schema
    "flavor_profiles": ["Chocolate", "Fruity"] # Added to be consistent with enrichment
}

CACHED_PRODUCT_1_DICT = {
    **ENRICHED_PRODUCT_1, # Includes all new fields from ENRICHED_PRODUCT_1
    "id": "coffee_A_id",
    # aroma in cache should also be string
}

# This can be a real Coffee model instance or a MagicMock
MOCKED_COFFEE_MODEL_1 = MagicMock(spec=Coffee)
# Update attributes on the mock model to reflect new fields for assertions if needed
MOCKED_COFFEE_MODEL_1.name = ENRICHED_PRODUCT_1["name"]
MOCKED_COFFEE_MODEL_1.acidity = ENRICHED_PRODUCT_1["acidity"]
MOCKED_COFFEE_MODEL_1.body = ENRICHED_PRODUCT_1["body"]
MOCKED_COFFEE_MODEL_1.sweetness = ENRICHED_PRODUCT_1["sweetness"]
MOCKED_COFFEE_MODEL_1.aroma = ENRICHED_PRODUCT_1["aroma"]
MOCKED_COFFEE_MODEL_1.with_milk_suitable = ENRICHED_PRODUCT_1["with_milk_suitable"]
MOCKED_COFFEE_MODEL_1.varietals = ENRICHED_PRODUCT_1["varietals"]
MOCKED_COFFEE_MODEL_1.altitude_meters = ENRICHED_PRODUCT_1["altitude_meters"]
MOCKED_COFFEE_MODEL_1.flavor_profiles = ENRICHED_PRODUCT_1["flavor_profiles"]
# ... and other fields from RAW_PRODUCT_1 and ENRICHED_PRODUCT_1's older fields
MOCKED_COFFEE_MODEL_1.origin = ENRICHED_PRODUCT_1["origin"]
MOCKED_COFFEE_MODEL_1.tasting_notes = ENRICHED_PRODUCT_1["tasting_notes"]


@pytest.fixture
def scraper_instance():
    # PlatformDetector is instantiated in ProductScraper's __init__
    # We can patch its 'detect' method globally or pass a mock instance if ProductScraper allowed it
    with patch('scrapers.product_crawl4ai.scraper.PlatformDetector', autospec=True) as MockPlatformDetector:
        mock_detector_instance = MockPlatformDetector.return_value
        mock_detector_instance.detect = AsyncMock(return_value=("unknown", 0)) # Default mock for detect
        scraper = ProductScraper()
        # scraper.platform_detector = mock_detector_instance # if we could inject it
        yield scraper


# A decorator to patch all common dependencies
def patch_dependencies(func):
    @patch('scrapers.product_crawl4ai.scraper.get_cached_products', new_callable=MagicMock) # Sync function
    @patch('scrapers.product_crawl4ai.scraper.cache_products', new_callable=MagicMock) # Sync function
    @patch('scrapers.product_crawl4ai.scraper.extract_products_shopify', new_callable=AsyncMock)
    @patch('scrapers.product_crawl4ai.scraper.extract_products_woocommerce', new_callable=AsyncMock)
    @patch('scrapers.product_crawl4ai.scraper.discover_products_via_crawl4ai', new_callable=AsyncMock)
    @patch('scrapers.product_crawl4ai.scraper.enrich_coffee_product', new_callable=AsyncMock)
    @patch('scrapers.product_crawl4ai.scraper.is_coffee_product', return_value=True) # Sync function
    @patch('scrapers.product_crawl4ai.scraper.validate_enriched_product', return_value=True) # Sync function
    @patch('scrapers.product_crawl4ai.scraper.dict_to_pydantic_model') # Sync function
    @patch.object(ProductScraper, 'platform_detector', new_callable=AsyncMock) # Mock the instance's detector
    async def wrapper(*args, **kwargs):
        # The last arg is usually the function itself if not bound, or a mock if it's part of the class
        # args needs to include all mocks defined by @patch decorators
        # The instance of the test class (if any) or the scraper_instance fixture
        test_instance_or_fixture = args[0] if args and isinstance(args[0], ProductScraper) else args[1]
        
        # If platform_detector was patched as an attribute of the instance (it is on ProductScraper)
        # we can re-assign it here if needed, or ensure the global patch on PlatformDetector class is enough.
        # For this test, ProductScraper creates its own PlatformDetector.
        # So, we need to ensure the `detect` method of that instance is what we want.
        # The @patch.object for scraper_instance.platform_detector.detect might be more direct if ProductScraper was first arg
        # But ProductScraper is scraper_instance.
        # The fixture already patches PlatformDetector globally for when ProductScraper() is called.
        # The @patch.object here is if we want to override per-test.
        # Let's rely on the fixture's global patch of the class for `detect`.
        
        # Re-extract mocks passed by @patch
        # The order is from bottom-up for decorators:
        # mock_platform_detector_on_instance (not used if fixture patches class)
        # mock_dict_to_pydantic_model
        # mock_validate_enriched_product
        # mock_is_coffee_product
        # mock_enrich_coffee_product
        # mock_discover_products_via_crawl4ai
        # mock_extract_products_woocommerce
        # mock_extract_products_shopify
        # mock_cache_products
        # mock_get_cached_products
        
        # The actual mocks are passed in reverse order of @patch application
        # So, the first mock in the args list is the one from the topmost @patch decorator
        
        # Correct order of mocks as they will be passed to the test function:
        mock_get_cached_products = args[1]
        mock_cache_products = args[2]
        mock_extract_shopify = args[3]
        mock_extract_woocommerce = args[4]
        mock_discover_crawl4ai = args[5]
        mock_enrich = args[6]
        mock_is_coffee = args[7]
        mock_validate = args[8]
        mock_dict_to_pydantic = args[9]
        # The scraper_instance fixture is passed by pytest, not by mock.
        # So, it will be kwargs['scraper_instance'] or args[0] if not a method.
        # In pytest, fixtures are passed by name.

        # For clarity, let's pass them as kwargs to the actual test.
        # This requires the test functions to accept these as named arguments.
        kwargs.update({
            'mock_get_cached_products': mock_get_cached_products,
            'mock_cache_products': mock_cache_products,
            'mock_extract_shopify': mock_extract_shopify,
            'mock_extract_woocommerce': mock_extract_woocommerce,
            'mock_discover_crawl4ai': mock_discover_crawl4ai,
            'mock_enrich': mock_enrich,
            'mock_is_coffee': mock_is_coffee,
            'mock_validate': mock_validate,
            'mock_dict_to_pydantic': mock_dict_to_pydantic,
        })
        # The scraper_instance is already available via the fixture
        return await func(**kwargs)
    return wrapper


@pytest.mark.asyncio
@patch_dependencies
async def test_default_behavior_cache_miss(
    scraper_instance, mock_get_cached_products, mock_cache_products,
    mock_extract_shopify, mock_extract_woocommerce, mock_discover_crawl4ai,
    mock_enrich, mock_is_coffee, mock_validate, mock_dict_to_pydantic
):
    mock_get_cached_products.return_value = None  # Cache miss
    mock_discover_crawl4ai.return_value = [RAW_PRODUCT_1] # Default discovery
    mock_enrich.return_value = ENRICHED_PRODUCT_1
    mock_dict_to_pydantic.return_value = MOCKED_COFFEE_MODEL_1

    await scraper_instance.scrape_products(
        SAMPLE_ROASTER_ID, SAMPLE_URL, SAMPLE_ROASTER_NAME, force_refresh=False, use_enrichment=True
    )

    mock_get_cached_products.assert_called_once_with(SAMPLE_ROASTER_ID, max_age_days=7)
    scraper_instance.platform_detector.detect.assert_called_once_with(SAMPLE_URL) # detect is on the instance from fixture
    mock_discover_crawl4ai.assert_called_once_with(SAMPLE_URL, SAMPLE_ROASTER_ID, SAMPLE_ROASTER_NAME)
    mock_enrich.assert_called_once_with(RAW_PRODUCT_1, SAMPLE_ROASTER_NAME)
    mock_is_coffee.assert_called_once() # Called with RAW_PRODUCT_1 details
    mock_validate.assert_called_once_with(ENRICHED_PRODUCT_1) # ENRICHED_PRODUCT_1 now has new fields
    mock_dict_to_pydantic.assert_called_once_with(ENRICHED_PRODUCT_1, Coffee, preprocessor=preprocess_coffee_data)
    mock_cache_products.assert_called_once()


@pytest.mark.asyncio
@patch_dependencies
async def test_default_behavior_cache_hit(
    scraper_instance, mock_get_cached_products, mock_cache_products,
    mock_extract_shopify, mock_extract_woocommerce, mock_discover_crawl4ai,
    mock_enrich, mock_is_coffee, mock_validate, mock_dict_to_pydantic
):
    mock_get_cached_products.return_value = [CACHED_PRODUCT_1_DICT] # Cache hit
    # When dict_to_pydantic_model is called for cached products, it gets the dict directly
    mock_dict_to_pydantic.return_value = MOCKED_COFFEE_MODEL_1 

    results = await scraper_instance.scrape_products(
        SAMPLE_ROASTER_ID, SAMPLE_URL, SAMPLE_ROASTER_NAME, force_refresh=False, use_enrichment=True
    )

    mock_get_cached_products.assert_called_once_with(SAMPLE_ROASTER_ID, max_age_days=7)
    mock_dict_to_pydantic.assert_called_once_with(CACHED_PRODUCT_1_DICT, Coffee, preprocessor=preprocess_coffee_data)
    
    scraper_instance.platform_detector.detect.assert_not_called()
    mock_discover_crawl4ai.assert_not_called()
    mock_extract_shopify.assert_not_called()
    mock_extract_woocommerce.assert_not_called()
    mock_enrich.assert_not_called()
    mock_cache_products.assert_not_called() # Not called because data came from cache
    
    assert len(results) == 1
    assert results[0] == MOCKED_COFFEE_MODEL_1


@pytest.mark.asyncio
@patch_dependencies
async def test_force_refresh_bypasses_cache_and_enriches(
    scraper_instance, mock_get_cached_products, mock_cache_products,
    mock_extract_shopify, mock_extract_woocommerce, mock_discover_crawl4ai,
    mock_enrich, mock_is_coffee, mock_validate, mock_dict_to_pydantic
):
    # Even if cache has data, it should be ignored
    mock_get_cached_products.return_value = [CACHED_PRODUCT_1_DICT] 
    mock_discover_crawl4ai.return_value = [RAW_PRODUCT_1] # Discovered data
    mock_enrich.return_value = ENRICHED_PRODUCT_1 # Enriched data
    mock_dict_to_pydantic.return_value = MOCKED_COFFEE_MODEL_1

    await scraper_instance.scrape_products(
        SAMPLE_ROASTER_ID, SAMPLE_URL, SAMPLE_ROASTER_NAME, force_refresh=True, use_enrichment=True
    )

    # get_cached_products is NOT called to return early, but might be called by a logger.
    # The key is that its return value doesn't lead to an early exit.
    # Assert that the scraping process continues:
    scraper_instance.platform_detector.detect.assert_called_once_with(SAMPLE_URL)
    mock_discover_crawl4ai.assert_called_once_with(SAMPLE_URL, SAMPLE_ROASTER_ID, SAMPLE_ROASTER_NAME)
    mock_enrich.assert_called_once_with(RAW_PRODUCT_1, SAMPLE_ROASTER_NAME)
    mock_validate.assert_called_once_with(ENRICHED_PRODUCT_1) # ENRICHED_PRODUCT_1 now has new fields
    mock_dict_to_pydantic.assert_called_once_with(ENRICHED_PRODUCT_1, Coffee, preprocessor=preprocess_coffee_data)
    mock_cache_products.assert_called_once() # New data is cached


@pytest.mark.asyncio
@patch_dependencies
async def test_use_enrichment_false_skips_enrichment_call(
    scraper_instance, mock_get_cached_products, mock_cache_products,
    mock_extract_shopify, mock_extract_woocommerce, mock_discover_crawl4ai,
    mock_enrich, mock_is_coffee, mock_validate, mock_dict_to_pydantic
):
    mock_get_cached_products.return_value = None # Cache miss
    mock_discover_crawl4ai.return_value = [RAW_PRODUCT_1]
    # mock_enrich should not be called
    mock_dict_to_pydantic.return_value = MOCKED_COFFEE_MODEL_1 # Assume model conversion happens with raw data

    await scraper_instance.scrape_products(
        SAMPLE_ROASTER_ID, SAMPLE_URL, SAMPLE_ROASTER_NAME, force_refresh=False, use_enrichment=False
    )

    mock_get_cached_products.assert_called_once_with(SAMPLE_ROASTER_ID, max_age_days=7)
    scraper_instance.platform_detector.detect.assert_called_once_with(SAMPLE_URL)
    mock_discover_crawl4ai.assert_called_once_with(SAMPLE_URL, SAMPLE_ROASTER_ID, SAMPLE_ROASTER_NAME)
    
    mock_enrich.assert_not_called() # Key assertion for this test

    mock_is_coffee.assert_called_once() # Still called
    # validate_enriched_product is called with the raw product data in this case
    # RAW_PRODUCT_1 does not have the new fields, so they won't be in this call
    mock_validate.assert_called_once_with(RAW_PRODUCT_1)
    # dict_to_pydantic_model is called with the raw product data
    # The new fields should be absent or None if not in RAW_PRODUCT_1
    expected_data_for_pydantic = {
        **RAW_PRODUCT_1,
        # New fields should default to None or be absent if not in RAW_PRODUCT_1
        # and enrichment is skipped.
        # Depending on how dict_to_pydantic_model and Coffee model defaults work,
        # they might appear as None.
        # For this assertion, we expect exactly RAW_PRODUCT_1's content.
        # If Coffee model adds them as None by default, this assertion is fine.
        # If the `product_dict` passed to `validate_enriched_product` and then
        # `dict_to_pydantic_model` has them explicitly set to None, that's also fine.
        # The `product_dict` in `scraper.py` starts as `model_to_dict(product)`
        # and then `enriched_product_data = product_dict` if enrichment is skipped.
        # So `RAW_PRODUCT_1` is what's expected here.
    }
    mock_dict_to_pydantic.assert_called_once_with(expected_data_for_pydantic, Coffee, preprocessor=preprocess_coffee_data)
    mock_cache_products.assert_called_once()


@pytest.mark.asyncio
@patch_dependencies
async def test_shopify_platform_uses_shopify_extractor(
    scraper_instance, mock_get_cached_products, mock_cache_products,
    mock_extract_shopify, mock_extract_woocommerce, mock_discover_crawl4ai,
    mock_enrich, mock_is_coffee, mock_validate, mock_dict_to_pydantic
):
    mock_get_cached_products.return_value = None
    scraper_instance.platform_detector.detect = AsyncMock(return_value=("shopify", 90)) # Override fixture default
    mock_extract_shopify.return_value = [RAW_PRODUCT_1]
    mock_enrich.return_value = ENRICHED_PRODUCT_1
    mock_dict_to_pydantic.return_value = MOCKED_COFFEE_MODEL_1

    await scraper_instance.scrape_products(
        SAMPLE_ROASTER_ID, SAMPLE_URL, SAMPLE_ROASTER_NAME, force_refresh=False, use_enrichment=True
    )

    mock_extract_shopify.assert_called_once_with(SAMPLE_URL, SAMPLE_ROASTER_ID)
    mock_discover_crawl4ai.assert_not_called()
    mock_enrich.assert_called_once_with(RAW_PRODUCT_1, SAMPLE_ROASTER_NAME)


@pytest.mark.asyncio
@patch_dependencies
async def test_woocommerce_platform_uses_woocommerce_extractor(
    scraper_instance, mock_get_cached_products, mock_cache_products,
    mock_extract_shopify, mock_extract_woocommerce, mock_discover_crawl4ai,
    mock_enrich, mock_is_coffee, mock_validate, mock_dict_to_pydantic
):
    mock_get_cached_products.return_value = None
    scraper_instance.platform_detector.detect = AsyncMock(return_value=("woocommerce", 90)) # Override
    mock_extract_woocommerce.return_value = [RAW_PRODUCT_1]
    mock_enrich.return_value = ENRICHED_PRODUCT_1
    mock_dict_to_pydantic.return_value = MOCKED_COFFEE_MODEL_1

    await scraper_instance.scrape_products(
        SAMPLE_ROASTER_ID, SAMPLE_URL, SAMPLE_ROASTER_NAME, force_refresh=False, use_enrichment=True
    )

    mock_extract_woocommerce.assert_called_once_with(SAMPLE_URL, SAMPLE_ROASTER_ID)
    mock_discover_crawl4ai.assert_not_called()
    mock_enrich.assert_called_once_with(RAW_PRODUCT_1, SAMPLE_ROASTER_NAME)

@pytest.mark.asyncio
@patch_dependencies
async def test_no_products_found_returns_empty_list_and_does_not_cache(
    scraper_instance, mock_get_cached_products, mock_cache_products,
    mock_extract_shopify, mock_extract_woocommerce, mock_discover_crawl4ai,
    mock_enrich, mock_is_coffee, mock_validate, mock_dict_to_pydantic
):
    mock_get_cached_products.return_value = None
    scraper_instance.platform_detector.detect = AsyncMock(return_value=("unknown", 0))
    mock_discover_crawl4ai.return_value = [] # No products found

    results = await scraper_instance.scrape_products(
        SAMPLE_ROASTER_ID, SAMPLE_URL, SAMPLE_ROASTER_NAME, force_refresh=False, use_enrichment=True
    )

    assert results == []
    mock_enrich.assert_not_called()
    mock_cache_products.assert_not_called() # Cache should not be called if no products

@pytest.mark.asyncio
@patch_dependencies
async def test_product_filtered_out_by_is_coffee_product(
    scraper_instance, mock_get_cached_products, mock_cache_products,
    mock_extract_shopify, mock_extract_woocommerce, mock_discover_crawl4ai,
    mock_enrich, mock_is_coffee, mock_validate, mock_dict_to_pydantic
):
    mock_get_cached_products.return_value = None
    mock_discover_crawl4ai.return_value = [RAW_PRODUCT_1]
    mock_is_coffee.return_value = False # Product is not a coffee

    results = await scraper_instance.scrape_products(
        SAMPLE_ROASTER_ID, SAMPLE_URL, SAMPLE_ROASTER_NAME, force_refresh=False, use_enrichment=True
    )
    
    assert results == []
    mock_is_coffee.assert_called_once_with(
        RAW_PRODUCT_1.get('name', ''),
        RAW_PRODUCT_1.get('description', ''),
        RAW_PRODUCT_1.get('product_type', None),
        RAW_PRODUCT_1.get('tags', None),
        SAMPLE_ROASTER_NAME,
        RAW_PRODUCT_1.get('direct_buy_url', '')
    )
    mock_enrich.assert_not_called()
    mock_validate.assert_not_called()
    mock_dict_to_pydantic.assert_not_called()
    mock_cache_products.assert_not_called()

@pytest.mark.asyncio
@patch_dependencies
async def test_product_filtered_out_by_validation(
    scraper_instance, mock_get_cached_products, mock_cache_products,
    mock_extract_shopify, mock_extract_woocommerce, mock_discover_crawl4ai,
    mock_enrich, mock_is_coffee, mock_validate, mock_dict_to_pydantic
):
    mock_get_cached_products.return_value = None
    mock_discover_crawl4ai.return_value = [RAW_PRODUCT_1]
    mock_enrich.return_value = ENRICHED_PRODUCT_1
    mock_validate.return_value = False # Product fails validation

    results = await scraper_instance.scrape_products(
        SAMPLE_ROASTER_ID, SAMPLE_URL, SAMPLE_ROASTER_NAME, force_refresh=False, use_enrichment=True
    )

    assert results == []
    mock_enrich.assert_called_once_with(RAW_PRODUCT_1, SAMPLE_ROASTER_NAME)
    mock_validate.assert_called_once_with(ENRICHED_PRODUCT_1)
    mock_dict_to_pydantic.assert_not_called()
    mock_cache_products.assert_not_called()

# Example of testing platform detection fallback
@pytest.mark.asyncio
@patch_dependencies
async def test_shopify_low_confidence_falls_back_to_crawl4ai(
    scraper_instance, mock_get_cached_products, mock_cache_products,
    mock_extract_shopify, mock_extract_woocommerce, mock_discover_crawl4ai,
    mock_enrich, mock_is_coffee, mock_validate, mock_dict_to_pydantic
):
    mock_get_cached_products.return_value = None
    scraper_instance.platform_detector.detect = AsyncMock(return_value=("shopify", 50)) # Low confidence
    mock_extract_shopify.return_value = [] # Shopify returns no products (or not called aggressively)
    mock_discover_crawl4ai.return_value = [RAW_PRODUCT_1] # Crawl4AI is used
    mock_enrich.return_value = ENRICHED_PRODUCT_1
    mock_dict_to_pydantic.return_value = MOCKED_COFFEE_MODEL_1

    await scraper_instance.scrape_products(
        SAMPLE_ROASTER_ID, SAMPLE_URL, SAMPLE_ROASTER_NAME
    )

    mock_extract_shopify.assert_called_once_with(SAMPLE_URL, SAMPLE_ROASTER_ID) # It's still attempted
    mock_discover_crawl4ai.assert_called_once_with(SAMPLE_URL, SAMPLE_ROASTER_ID, SAMPLE_ROASTER_NAME)
    mock_enrich.assert_called_once_with(RAW_PRODUCT_1, SAMPLE_ROASTER_NAME)
    mock_cache_products.assert_called_once()

@pytest.mark.asyncio
@patch_dependencies
async def test_force_refresh_with_use_enrichment_false(
    scraper_instance, mock_get_cached_products, mock_cache_products,
    mock_extract_shopify, mock_extract_woocommerce, mock_discover_crawl4ai,
    mock_enrich, mock_is_coffee, mock_validate, mock_dict_to_pydantic
):
    mock_get_cached_products.return_value = [CACHED_PRODUCT_1_DICT] # Cache has data, but will be ignored
    mock_discover_crawl4ai.return_value = [RAW_PRODUCT_1]
    mock_dict_to_pydantic.return_value = MOCKED_COFFEE_MODEL_1

    await scraper_instance.scrape_products(
        SAMPLE_ROASTER_ID, SAMPLE_URL, SAMPLE_ROASTER_NAME, force_refresh=True, use_enrichment=False
    )
    
    scraper_instance.platform_detector.detect.assert_called_once_with(SAMPLE_URL)
    mock_discover_crawl4ai.assert_called_once_with(SAMPLE_URL, SAMPLE_ROASTER_ID, SAMPLE_ROASTER_NAME)
    mock_enrich.assert_not_called() # Enrichment disabled
    mock_validate.assert_called_once_with(RAW_PRODUCT_1) # Validated with raw data (no new fields)
    
    # Similar to test_use_enrichment_false_skips_enrichment_call
    expected_data_for_pydantic_force_refresh_no_enrich = {
        **RAW_PRODUCT_1
    }
    mock_dict_to_pydantic.assert_called_once_with(expected_data_for_pydantic_force_refresh_no_enrich, Coffee, preprocessor=preprocess_coffee_data)
    mock_cache_products.assert_called_once()

# Ensure logs are not excessively noisy during tests
@pytest.fixture(autouse=True)
def mute_scraper_logs():
    with patch('scrapers.product_crawl4ai.scraper.logger') as mock_logger:
        mock_logger.info = MagicMock()
        mock_logger.debug = MagicMock()
        mock_logger.warning = MagicMock()
        mock_logger.error = MagicMock()
        yield mock_logger

# To run these tests, you would typically use `pytest` in your terminal.
# Ensure `pytest-asyncio` is installed.
# Example: pytest tests/test_product_crawl4ai_scraper.py
```
