# scrapers/roasters-crawl4ai/run.py
"""Script to run the Crawl4AI roaster extraction."""

import argparse
import asyncio
import csv
import json
from pathlib import Path
from typing import Any, Dict, Optional

from .crawler import RoasterCrawler


async def process_csv_batch(
    csv_path: str,
    output_path: "Optional[str]" = None,
    limit: "Optional[int]" = None,
    concurrency: int = 5,
    rate_limit: int = 10,
    rate_period: float = 60.0,
):
    """Process roasters from a CSV file using async batch processing."""
    from .batch import batch_process_roasters

    results = []
    errors = []

    # Validate input file
    if not Path(csv_path).exists():
        raise FileNotFoundError(f"Input CSV file not found: {csv_path}")

    # Read input CSV
    with open(csv_path, mode="r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        rows = list(reader)
        if limit:
            rows = rows[:limit]
        roaster_list = []
        for row in rows:
            name = row.get("name", row.get("roaster", "")).strip()
            url = row.get("website_url", row.get("website", row.get("url", ""))).strip()
            if not name or not url:
                errors.append({"name": name, "url": url, "error": "Missing name or URL in input"})
                continue
            roaster_list.append((name, url))

    if not roaster_list:
        print("No valid roasters found in input CSV.")
        return [], errors

    # Process batch
    print(
        f"Processing {len(roaster_list)} roasters (concurrency={concurrency}, rate_limit={rate_limit}/{rate_period}s)..."
    )
    results = await batch_process_roasters(
        roaster_list, concurrency=concurrency, rate_limit=rate_limit, rate_period=rate_period, export_path=output_path
    )
    print(f"Processed {len(results)} roasters.")
    return results, errors


async def process_single(name: str, url: str) -> Dict[str, Any]:
    """Process a single roaster."""
    crawler = RoasterCrawler()
    return await crawler.extract_roaster(name, url)


async def main():
    """Run the Crawl4AI roaster extraction."""
    parser = argparse.ArgumentParser(description="Extract roaster data using Crawl4AI")
    parser.add_argument("input", help="Input CSV file with roaster names and URLs")
    parser.add_argument("-o", "--output", help="Output JSON file for results")
    parser.add_argument("-l", "--limit", type=int, help="Limit number of roasters to process")
    parser.add_argument(
        "-s", "--single", action="store_true", help="Process a single roaster (input should be name,url)"
    )

    args = parser.parse_args()

    if args.single:
        # Process a single roaster
        try:
            name, url = args.input.split(",", 1)
            result = await process_single(name.strip(), url.strip())
            print(json.dumps(result, indent=2))
        except ValueError:
            print("Error: For --single mode, input should be in format 'name,url'")
    else:
        # Process CSV file using batch async logic
        results, errors = await process_csv_batch(args.input, args.output, args.limit)
        print(f"Processed {len(results)} roasters with {len(errors)} input errors")

        if errors:
            print("\nInput Errors:")
            for error in errors[:5]:  # Show first 5 errors
                print(
                    f"  {error.get('name', 'Unknown')} ({error.get('url', 'No URL')}): {error.get('error', 'Unknown error')}"
                )

            if len(errors) > 5:
                print(f"  ... and {len(errors) - 5} more errors")


if __name__ == "__main__":
    asyncio.run(main())
