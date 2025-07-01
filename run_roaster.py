#!/usr/bin/env python
"""
Simple runner script for the roaster scraper.

Usage Examples:
    # Basic usage with defaults
    python run_roaster.py

    # Process with custom settings
    python run_roaster.py --input my_roasters.csv --output results.json --limit 10

    # Single roaster mode
    python run_roaster.py --single --input "Blue Tokai,https://bluetokai.com"

    # High-performance settings
    python run_roaster.py --concurrency 10 --rate-limit 20 --rate-period 30

    # Conservative settings for rate-limited sites
    python run_roaster.py --concurrency 2 --rate-limit 5 --rate-period 120

    # Test a new roaster
    python run_roaster.py --single --input "Ainmane,https://ainmane.com" --output test_roaster.json

    # Batch process with custom performance settings
    python run_roaster.py --input roasters.csv --output enriched_roasters.json --limit 5 --concurrency 3 --rate-limit 8 --rate-period 60 --max-retries 3

Available Arguments:
    --input: Input CSV file (default: ./data/input/roasters_input.csv)
    --output: Output JSON file (default: ./data/output/enriched_roasters.json)
    --limit: Limit number of roasters to scrape
    --single: Process a single roaster (input should be name,url)
    --concurrency: Max concurrent tasks (default: 5)
    --rate-limit: Max requests per rate period (default: 10)
    --rate-period: Rate limiting window in seconds (default: 60.0)
    --max-retries: Max retry attempts per roaster (default: 2)
"""

import argparse
import asyncio
import json
import logging
from pathlib import Path

from common.exporter import export_to_csv
from scrapers.roasters_crawl4ai.run import process_csv_batch, process_single

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    parser = argparse.ArgumentParser(description="Scrape coffee roaster websites.")

    # Input/Output options
    parser.add_argument("--input", default="./data/input/roasters_input.csv", help="Input CSV file")
    parser.add_argument("--output", default="./data/output/enriched_roasters.json", help="Output JSON file")
    parser.add_argument("--limit", type=int, help="Limit number of roasters to scrape")

    # Single roaster mode
    parser.add_argument("--single", action="store_true", help="Process a single roaster (input should be name,url)")

    # Performance options
    parser.add_argument("--concurrency", type=int, default=5, help="Max concurrent tasks (default: 5)")
    parser.add_argument("--rate-limit", type=int, default=10, help="Max requests per rate period (default: 10)")
    parser.add_argument(
        "--rate-period", type=float, default=60.0, help="Rate limiting window in seconds (default: 60.0)"
    )
    parser.add_argument("--max-retries", type=int, default=2, help="Max retry attempts per roaster (default: 2)")

    args = parser.parse_args()

    if args.single:
        # Process a single roaster
        try:
            name, url = args.input.split(",", 1)
            print(f"Processing single roaster: {name} ({url})")
            result = await process_single(name.strip(), url.strip())
            print(json.dumps(result, indent=2))

            # Save to output file if specified
            if args.output:
                with open(args.output, "w") as f:
                    json.dump([result], f, indent=2)
                print(f"Result saved to {args.output}")
        except ValueError:
            print("Error: For --single mode, input should be in format 'name,url'")
        return

    print(f"Starting roaster scraper with input: {args.input}")
    print(f"Performance settings: concurrency={args.concurrency}, rate_limit={args.rate_limit}/{args.rate_period}s")

    # Process roasters using Crawl4AI batch logic with all parameters
    results, errors = await process_csv_batch(
        args.input,
        args.output,
        args.limit,
        concurrency=args.concurrency,
        rate_limit=args.rate_limit,
        rate_period=args.rate_period,
    )

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
