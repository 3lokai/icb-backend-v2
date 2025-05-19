"""
Batch processing for roaster scraping using Crawl4AI.
- Async batch processing of multiple roaster websites
- Concurrency control with rate limiting
- Progress tracking and reporting
- Error handling with retry logic
- Result aggregation and export
- Integration with database/cache for storage
"""

import asyncio
from typing import List, Dict, Any, Tuple, Optional
from loguru import logger
from pathlib import Path

from .crawler import RoasterCrawler
from common.utils import fetch_with_retry
from common.exporter import export_to_json, export_to_csv
from common.cache import cache

class AsyncRateLimiter:
    """Simple asyncio-based rate limiter."""
    def __init__(self, max_calls: int, period: float):
        self._max_calls = max_calls
        self._period = period
        self._calls = []

    async def wait(self):
        now = asyncio.get_event_loop().time()
        self._calls = [t for t in self._calls if now - t < self._period]
        if len(self._calls) >= self._max_calls:
            sleep_time = self._period - (now - self._calls[0])
            await asyncio.sleep(max(sleep_time, 0))
        self._calls.append(asyncio.get_event_loop().time())

async def process_roaster(crawler: RoasterCrawler, name: str, url: str, rate_limiter: AsyncRateLimiter, max_retries: int = 2) -> Dict[str, Any]:
    for attempt in range(max_retries + 1):
        try:
            await rate_limiter.wait()
            data = await crawler.extract_roaster(name, url)
            return data
        except Exception as e:
            logger.error(f"Error processing {name} ({url}), attempt {attempt+1}: {e}")
            if attempt == max_retries:
                return {"name": name, "website_url": url, "error": str(e)}
            await asyncio.sleep(2 ** attempt)

async def batch_process_roasters(
    roaster_list: List[Tuple[str, str]],
    concurrency: int = 5,
    rate_limit: int = 10,
    rate_period: float = 60.0,
    export_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Batch process multiple roaster websites asynchronously.
    Args:
        roaster_list: List of (name, url) tuples.
        concurrency: Max concurrent tasks.
        rate_limit: Max requests per rate_period seconds.
        rate_period: Seconds for rate limiting window.
        export_path: Optional path to export results as JSON.
    Returns:
        List of roaster data dicts.
    """
    crawler = RoasterCrawler()
    rate_limiter = AsyncRateLimiter(rate_limit, rate_period)
    semaphore = asyncio.Semaphore(concurrency)
    results = []
    total = len(roaster_list)

    async def sem_task(idx: int, name: str, url: str):
        async with semaphore:
            logger.info(f"[{idx+1}/{total}] Processing: {name} ({url})")
            result = await process_roaster(crawler, name, url, rate_limiter)
            # Cache/store result
            cache.cache_roaster(result)
            results.append(result)
            logger.info(f"[{idx+1}/{total}] Done: {name}")

    tasks = [sem_task(i, name, url) for i, (name, url) in enumerate(roaster_list)]
    await asyncio.gather(*tasks)

    # Export results if path provided
    if export_path:
        export_to_json(results, export_path)
        logger.info(f"Exported batch results to {export_path}")

    return results

# Example usage (to be called from CLI or test):
# import asyncio
# roasters = [("Roaster1", "https://roaster1.com"), ("Roaster2", "https://roaster2.com")]
# asyncio.run(batch_process_roasters(roasters, concurrency=3, rate_limit=10, rate_period=60, export_path="batch_results.json"))
