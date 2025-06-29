import importlib.util
import os
import sys
from unittest.mock import AsyncMock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Dynamically import crawler.py from the hyphenated directory
crawler_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "scrapers", "roasters-crawl4ai", "crawler.py")
)
spec = importlib.util.spec_from_file_location("crawler", crawler_path)
crawler = importlib.util.module_from_spec(spec)
sys.modules["crawler"] = crawler
spec.loader.exec_module(crawler)

RoasterCrawler = crawler.RoasterCrawler


@pytest.mark.asyncio
async def test_extract_roaster_minimal(monkeypatch):
    # Patch enrich_missing_fields to avoid LLM calls
    monkeypatch.setattr(
        "scrapers.roasters_crawl4ai.enricher.enrich_missing_fields",
        AsyncMock(
            return_value={
                "name": "Test Roaster",
                "website_url": "https://test.com",
                "slug": "test-roaster",
                "country": "India",
                "is_active": True,
                "is_verified": False,
                "domain": "test.com",
            }
        ),
    )
    crawler = RoasterCrawler()
    result = await crawler.extract_roaster("Test Roaster", "https://test.com")
    assert result["name"] == "Test Roaster"
    assert result["website_url"] == "https://test.com"
    assert result["country"] == "India"
    assert result["is_active"] is True
    assert result["is_verified"] is False
    assert "slug" in result
    assert "domain" in result


@pytest.mark.asyncio
async def test_extract_roaster_handles_missing(monkeypatch):
    # Patch enrichment to fill missing fields
    monkeypatch.setattr(
        "scrapers.roasters-crawl4ai.enricher.enrich_missing_fields",
        AsyncMock(
            return_value={"name": "Test Roaster", "description": "desc", "founded_year": 2020, "address": "addr"}
        ),
    )
    crawler = RoasterCrawler()
    result = await crawler.extract_roaster("Test Roaster", "https://test.com")
    assert result["description"] == "desc"
    assert result["founded_year"] == 2020
    assert result["address"] == "addr"
