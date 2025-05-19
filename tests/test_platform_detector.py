import pytest
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.platform_detector import PlatformDetector

# Real world test cases
TEST_CASES = [
    ("https://bluetokaicoffee.com", "shopify"),
    ("https://arakucoffee.in", "shopify"),
    ("https://ainmane.com", "magento"),
    ("https://babasbeanscoffee.com", "woocommerce"),
]

@pytest.mark.asyncio
@pytest.mark.parametrize("url,expected_platform", TEST_CASES)
async def test_platform_detector_real_sites(url, expected_platform):
    detector = PlatformDetector()
    platform, confidence = await detector.detect(url)
    print(f"{url}: Detected {platform} (confidence={confidence})")
    assert platform == expected_platform
    assert confidence >= 40  # Should be confident for these known sites

# Synthetic/edge case tests can be added here as needed
# Example:
# @pytest.mark.asyncio
# async def test_platform_detector_unknown():
#     detector = PlatformDetector()
#     platform, confidence = await detector.detect("https://example.com")
#     assert platform in ("unknown", "static")
#     assert confidence <= 40
