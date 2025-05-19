#!/usr/bin/env python
"""
Simple runner script for the roaster scraper.
"""

import argparse
import asyncio
from pathlib import Path
import argparse
import asyncio
import csv
import logging
from pathlib import Path
from scrapers.roaster.batch import scrape_roasters_from_csv
from scrapers.roaster.scraper import RoasterScraper
from common.exporter import export_to_csv, export_to_json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    parser = argparse.ArgumentParser(description='Scrape coffee roaster websites.')
    parser.add_argument('--input', default='./data/input/roasters_input.csv', help='Input CSV file')
    parser.add_argument('--output', default='./data/output/enriched_roasters.json', help='Output JSON file')
    parser.add_argument('--limit', type=int, help='Limit number of roasters to scrape')
    args = parser.parse_args()

    print(f"Starting roaster scraper with input: {args.input}")

    # Process roasters
    results, errors = await scrape_roasters_from_csv(args.input, args.output, args.limit)

    print(f"Scraped {len(results)} roasters, encountered {len(errors)} errors")

    # Save errors to CSV
    if errors:
        error_file = Path('errors.csv')
        # Use standardized export utility
        export_to_csv(
            [
                {
                    'name': error.get('name', 'unknown'),
                    'url': error.get('url', 'unknown'),
                    'error': error.get('error', 'Unknown error')
                } for error in errors
            ],
            str(error_file),
            fieldnames=['name', 'url', 'error']
        )
        print(f"Errors saved to {error_file}")

    # Print sample results
    if results:
        sample = results[0]
        print("\n" + "="*40)
        print(f"SAMPLE ROASTER: {sample['name']}")
        print("="*40)
        for key, value in sample.items():
            print(f"{key}: {value}")

if __name__ == "__main__":
    asyncio.run(main())
