import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

import importlib.util

import scrapers.roasters_crawl4ai.enricher as enricher

@pytest.mark.asyncio
async def test_enrich_missing_fields_enriches_missing():
    roaster_data = {"name": "Test Roaster", "description": None, "founded_year": None, "address": None}
    enriched = {**roaster_data, "description": "A great roaster" , "founded_year": 2020, "address": "123 Brew St"}
    enricher.enrichment_service.enhance_roaster_description = AsyncMock(return_value=enriched)
    result = await enricher.enrich_missing_fields(roaster_data)
    assert result["description"] == "A great roaster"
    assert result["founded_year"] == 2020
    assert result["address"] == "123 Brew St"

@pytest.mark.asyncio
async def test_enrich_missing_fields_no_missing():
    roaster_data = {"name": "Test Roaster", "description": "desc", "founded_year": 2020, "address": "addr"}
    mock = AsyncMock()
    enricher.enrichment_service.enhance_roaster_description = mock
    result = await enricher.enrich_missing_fields(roaster_data)
    mock.assert_not_called()
    assert result == roaster_data

@pytest.mark.asyncio
async def test_enrich_missing_fields_missing_name():
    roaster_data = {"name": None, "description": None, "founded_year": None, "address": None}
    mock = AsyncMock()
    enricher.enrichment_service.enhance_roaster_description = mock
    result = await enricher.enrich_missing_fields(roaster_data)
    mock.assert_not_called()
    assert result == roaster_data

@pytest.mark.asyncio
async def test_enrich_missing_fields_error_handling():
    roaster_data = {"name": "Test Roaster", "description": None, "founded_year": None, "address": None}
    enricher.enrichment_service.enhance_roaster_description = AsyncMock(side_effect=Exception("LLM error"))
    result = await enricher.enrich_missing_fields(roaster_data)
    assert result == roaster_data
