import os
import sys
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scrapers.roasters_crawl4ai import batch


@pytest.mark.asyncio
async def test_batch_process_roasters_smoke(tmp_path):
    roaster_list = [("Roaster1", "https://r1.com"), ("Roaster2", "https://r2.com")]
    fake_result = {"name": "Roaster1", "website_url": "https://r1.com", "data": 123}
    export_path = tmp_path / "results.json"

    with (
        patch(
            "scrapers.roasters_crawl4ai.batch.RoasterCrawler.extract_roaster", new_callable=AsyncMock
        ) as mock_extract,
        patch("scrapers.roasters_crawl4ai.batch.cache.cache_roaster") as mock_cache_roaster,
        patch("scrapers.roasters_crawl4ai.batch.export_to_json") as mock_export_json,
    ):
        mock_extract.return_value = fake_result
        results = await batch.batch_process_roasters(
            roaster_list, concurrency=2, rate_limit=10, rate_period=60, export_path=str(export_path)
        )
        assert len(results) == 2
        for r in results:
            assert r["name"].startswith("Roaster")
        mock_cache_roaster.assert_called()
        mock_export_json.assert_called_once()
