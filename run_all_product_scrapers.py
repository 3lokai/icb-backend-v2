#!/usr/bin/env python
"""
Batch runner to scrape products for each roaster in the input CSV.
"""

import asyncio
import csv
import logging
import sys
from pathlib import Path

from common.utils import slugify
from db.supabase import supabase
from scrapers.product_crawl4ai.scraper import ProductScraper
from scrapers.roasters_crawl4ai.run import process_single as extract_roaster

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("batch_scraper")

INPUT_CSV = "data/input/roasters_input.csv"
SCRAPER_MODULE = "scrapers.product_crawl4ai.run_product_scraper"
PYTHON_EXEC = sys.executable or "python"

# Output directory for per-roaster product data (optional)
OUTPUT_DIR = Path("data/output/products_by_roaster")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def process_roaster(row):
    name = row.get("name")
    url = row.get("website_url")
    if not name or not url:
        logger.warning(f"Skipping row with missing name or url: {row}")
        return
    roaster_id = slugify(name)
    roaster_name = name.strip()
    logger.info(f"\nProcessing roaster: {roaster_name} ({url})")
    # --- Extract and push roaster data ---
    try:
        roaster_data = await extract_roaster(roaster_name, url)
        logger.info(f"Extracted roaster data: {roaster_data}")
        supabase.upsert_roaster(roaster_data)
        logger.info(f"Pushed roaster to Supabase: {roaster_name}")
    except Exception as e:
        logger.error(f"Error extracting/pushing roaster {roaster_name}: {e}")
        return
    # --- Extract and push product data ---
    try:
        scraper = ProductScraper()
        products = await scraper.scrape_products(roaster_id, url, roaster_name)
        logger.info(f"Found {len(products)} products for {roaster_name}")
        pushed = 0
        for product in products:
            try:
                supabase.upsert_coffee(product)
                pushed += 1
            except Exception as e:
                logger.warning(f"  Error pushing product to Supabase: {e}")
        logger.info(f"Pushed {pushed} products to Supabase for {roaster_name}.")
    except Exception as e:
        logger.error(f"Error scraping/pushing products for {roaster_name}: {e}")
    input("Press Enter to continue to the next roaster...")


async def main():
    with open(INPUT_CSV, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            await process_roaster(row)


if __name__ == "__main__":
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
