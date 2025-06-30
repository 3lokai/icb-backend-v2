"""Batch processing for roaster scraping."""

import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

from .scraper import RoasterScraper

logger = logging.getLogger(__name__)


async def scrape_roasters_from_csv(
    csv_path: str, output_path: Optional[str] = None, limit: Optional[int] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Scrape roasters from a CSV file."""
    results = []
    errors = []

    # Validate input file
    if not Path(csv_path).exists():
        raise FileNotFoundError(f"Input CSV file not found: {csv_path}")

    # Initialize scraper
    scraper = RoasterScraper()

    # Read input CSV
    with open(csv_path, mode="r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)

        # Apply limit if specified
        rows = list(reader)
        if limit:
            rows = rows[:limit]

        # Process each roaster
        for row in rows:
            name = ""
            url = ""
            try:
                name = row.get("name", row.get("roaster", "")).strip()
                url = row.get("url", row.get("website", row.get("website_url", ""))).strip()

                if not name or not url:
                    errors.append({"name": name, "url": url, "error": "Missing name or URL in input"})
                    continue

                logger.info(f"Processing roaster: {name} ({url})")

                # Scrape the roaster
                roaster_data = await scraper.scrape_roaster(name, url)

                if roaster_data:
                    results.append(roaster_data)
                else:
                    errors.append({"name": name, "url": url, "error": "No data returned from scraper"})

            except Exception as e:
                logger.error(f"Error processing {name} ({url}): {str(e)}")
                errors.append({"name": name, "url": url, "error": str(e)})

    # Save results if output path specified
    if output_path:
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
            logger.info(f"Saved {len(results)} results to {output_path}")
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            errors.append({"error": f"Failed to save output: {str(e)}"})

    return results, errors


async def process_roaster_batch(
    scraper: RoasterScraper, roaster_list: List[Dict[str, str]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Process a batch of roasters with an existing scraper instance."""
    results = []
    errors = []

    for roaster in roaster_list:
        name = ""
        url = ""
        try:
            name = roaster.get("name", "").strip()
            url = roaster.get("url", "").strip()

            if not name or not url:
                errors.append({"name": name, "url": url, "error": "Missing name or URL in input"})
                continue

            logger.info(f"Processing roaster: {name} ({url})")

            # Scrape the roaster
            roaster_data = await scraper.scrape_roaster(name, url)

            if roaster_data:
                results.append(roaster_data)
            else:
                errors.append({"name": name, "url": url, "error": "No data returned from scraper"})

        except Exception as e:
            logger.error(f"Error processing {name} ({url}): {str(e)}")
            errors.append({"name": name, "url": url, "error": str(e)})

    return results, errors
