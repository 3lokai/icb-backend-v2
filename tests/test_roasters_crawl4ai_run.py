import os
import sys
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scrapers.roasters_crawl4ai import run


@pytest.mark.asyncio
async def test_process_single():
    with patch("scrapers.roasters_crawl4ai.run.RoasterCrawler.extract_roaster", new_callable=AsyncMock) as mock_extract:
        mock_extract.return_value = {"name": "Test", "website_url": "https://r.com"}
        result = await run.process_single("Test", "https://r.com")
        assert result["name"] == "Test"
        assert result["website_url"] == "https://r.com"


@pytest.mark.asyncio
async def test_process_csv_batch(tmp_path):
    csv_content = "name,website_url\nRoaster1,https://r1.com\nRoaster2,https://r2.com\n"
    csv_path = tmp_path / "input.csv"
    output_path = tmp_path / "output.json"
    csv_path.write_text(csv_content)
    with patch("scrapers.roasters_crawl4ai.batch.batch_process_roasters", new_callable=AsyncMock) as mock_batch:
        mock_batch.return_value = [
            {"name": "Roaster1", "website_url": "https://r1.com"},
            {"name": "Roaster2", "website_url": "https://r2.com"},
        ]
        results, errors = await run.process_csv_batch(str(csv_path), str(output_path), limit=None, concurrency=2)
        assert len(results) == 2
        assert errors == []
        mock_batch.assert_called_once()


@pytest.mark.asyncio
async def test_process_csv_batch_handles_missing_file():
    with pytest.raises(FileNotFoundError):
        await run.process_csv_batch("notfound.csv")


@pytest.mark.asyncio
async def test_process_csv_batch_handles_missing_fields(tmp_path):
    csv_content = "name,website_url\n,\nRoaster2,\n"
    csv_path = tmp_path / "input.csv"
    csv_path.write_text(csv_content)
    with patch("scrapers.roasters_crawl4ai.batch.batch_process_roasters", new_callable=AsyncMock) as mock_batch:
        mock_batch.return_value = []
        results, errors = await run.process_csv_batch(str(csv_path))
        assert results == []
        assert len(errors) == 2
