import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.enricher import EnrichmentService

@pytest.mark.asyncio
async def test_enhance_roaster_description_returns_input_if_disabled():
    service = EnrichmentService(api_key=None)
    roaster = {"name": "Test Roaster"}
    result = await service.enhance_roaster_description(roaster.copy())
    # Should contain at least the original fields
    for k, v in roaster.items():
        assert result[k] == v
    # If a generic description is added, that's acceptable
    assert "description" in result
    assert isinstance(result["description"], str)

@pytest.mark.asyncio
async def test_enhance_roaster_description_merges_fields():
    service = EnrichmentService(api_key="fake-key")
    roaster = {"name": "Test Roaster", "website_url": "https://test.com"}
    fake_response = MagicMock()
    fake_response.choices = [MagicMock()]
    fake_response.choices[0].message.content = '{"description": "A great roaster.", "founded_year": 2020, "address": "123 Main St"}'
    
    with patch.object(service, "_extract_json_from_response", return_value={
        "description": "A great roaster.",
        "founded_year": 2020,
        "address": "123 Main St"
    }):
        with patch("common.enricher.OpenAI") as mock_openai:
            mock_openai.return_value.chat.completions.create.return_value = fake_response
            result = await service.enhance_roaster_description(roaster.copy())
            assert result["description"] == "A great roaster."
            assert result["founded_year"] == 2020
            assert result["address"] == "123 Main St"

@pytest.mark.asyncio
async def test_enhance_roaster_description_handles_exception():
    service = EnrichmentService(api_key="fake-key")
    roaster = {"name": "Test Roaster"}
    with patch.object(service, "_extract_json_from_response", side_effect=Exception("fail")):
        with patch("common.enricher.OpenAI") as mock_openai:
            mock_openai.return_value.chat.completions.create.side_effect = Exception("fail")
            result = await service.enhance_roaster_description(roaster.copy())
            assert result == roaster
