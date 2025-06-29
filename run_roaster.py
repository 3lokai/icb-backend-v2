#!/usr/bin/env python
"""
Simple runner script for the roaster scraper.
"""

import argparse
import asyncio
import logging
from pathlib import Path

from common.exporter import export_to_csv
from scrapers.roasters_crawl4ai.run import process_csv_batch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    parser = argparse.ArgumentParser(description="Scrape coffee roaster websites.")
    parser.add_argument("--input", default="./data/input/roasters_input.csv", help="Input CSV file")
    parser.add_argument("--output", default="./data/output/enriched_roasters.json", help="Output JSON file")
    parser.add_argument("--limit", type=int, help="Limit number of roasters to scrape")
    args = parser.parse_args()

    print(f"Starting roaster scraper with input: {args.input}")

    # Process roasters using Crawl4AI batch logic
    results, errors = await process_csv_batch(args.input, args.output, args.limit)

    print(f"Scraped {len(results)} roasters, encountered {len(errors)} errors")

    # Save errors to CSV
    if errors:
        error_file = Path("errors.csv")
        # Use standardized export utility
        export_to_csv(
            [
                {
                    "name": error.get("name", "unknown"),
                    "url": error.get("url", "unknown"),
                    "error": error.get("error", "Unknown error"),
                }
                for error in errors
            ],
            str(error_file),
            fieldnames=["name", "url", "error"],
        )
        print(f"Errors saved to {error_file}")

    # Print sample results
    if results:
        sample = results[0]
        print("\n" + "=" * 40)
        print(f"SAMPLE ROASTER: {sample['name']}")
        print("=" * 40)
        for key, value in sample.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
