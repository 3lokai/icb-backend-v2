#!/usr/bin/env python
"""
Coffee Scraper - Main Entry Point
---
Central orchestrator with command line interface for the Coffee Scraper.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import click
import tqdm
from loguru import logger

from common.exporter import export_to_csv, export_to_json
from common.platform_detector import PlatformDetector
from common.utils import slugify
from db.models import Coffee, Roaster
from db.supabase import supabase
from scrapers.product_crawl4ai.scraper import ProductScraper

# Import project components
from scrapers.roasters_crawl4ai.crawler import RoasterCrawler as RoasterScraper


# Configure logging
def setup_logging(log_dir_override=None):
    """Configure logging for the application."""
    log_dir = Path(log_dir_override) if log_dir_override else Path("./logs")
    log_dir.mkdir(exist_ok=True)

    # Remove default logger
    logger.remove()

    # Add file logger with rotation
    log_file = log_dir / f"coffee_scraper_{datetime.now().strftime('%Y%m%d')}.log"
    logger.add(
        log_file,
        rotation="10 MB",
        retention="1 week",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    )

    # Add console logger
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>",
    )

    return logger


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Coffee Scraper - Tool for scraping coffee roaster data."""
    # Check database connection on startup
    try:
        logger.info("Testing database connection...")
        supabase._test_connection()
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        sys.exit(1)


@cli.command()
@click.argument("url")
def detect(url):
    """Detect the e-commerce platform of a given URL."""
    logger.info(f"Detecting platform for {url}...")

    async def run_detection():
        detector = PlatformDetector()
        return await detector.detect(url)

    try:
        platform, confidence = asyncio.run(run_detection())
        logger.info(f"Detected platform: {platform} (confidence={confidence})")
        click.echo(f"Website {url} is using platform: {platform} (confidence={confidence})")
    except Exception as e:
        logger.error(f"Platform detection failed: {e}")
        click.echo(f"Error: {e}")


@cli.command()
@click.argument("url_or_file")
@click.option("--force", is_flag=True, help="Force re-scrape even if data exists")
@click.option("--is-csv", is_flag=True, help="Input is a CSV file with URLs")
@click.option("--url-col", default="url", help="Column name for URLs in CSV")
@click.option("--name-col", default="name", help="Column name for roaster names in CSV")
@click.option("--limit", type=int, help="Limit number of URLs to process from CSV")
@click.option("--concurrent", type=int, default=1, help="Number of concurrent scraping tasks")
def scrape_roaster(url_or_file, force, is_csv, url_col, name_col, limit, concurrent):
    """Scrape roasters using the Crawl4AI pipeline (async, batch or single)."""
    try:
        if is_csv:
            logger.info(f"Scraping roasters from CSV: {url_or_file}")
            import csv as pycsv

            async def run_batch():
                roaster_scraper = RoasterScraper()
                results = []
                errors = []
                with open(url_or_file, "r", encoding="utf-8") as f:
                    reader = pycsv.DictReader(f)
                    rows = list(reader)
                    if limit:
                        rows = rows[:limit]
                    semaphore = asyncio.Semaphore(concurrent)

                    async def scrape_row(row):
                        async with semaphore:
                            name = row.get(name_col, row.get("roaster", "")).strip()
                            url = row.get(url_col, row.get("website", row.get("url", ""))).strip()
                            if not name or not url:
                                errors.append({"name": name, "url": url, "error": "Missing name or URL in input"})
                                return None
                            try:
                                data = await roaster_scraper.extract_roaster(name, url)
                                return data
                            except Exception as e:
                                errors.append({"name": name, "url": url, "error": str(e)})
                                return None

                    tasks = [scrape_row(row) for row in rows]
                    import tqdm as tqdm_mod

                    for coro in tqdm_mod.tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Scraping roasters"):
                        result = await coro
                        if result:
                            results.append(result)
                            supabase.upsert_roaster(Roaster(**result))
                click.echo(f"Scraped {len(results)} roasters. {len(errors)} errors.")
                if errors:
                    click.echo("\nInput Errors:")
                    for error in errors[:5]:
                        click.echo(
                            f"  {error.get('name', 'Unknown')} ({error.get('url', 'No URL')}): {error.get('error', 'Unknown error')}"
                        )
                    if len(errors) > 5:
                        click.echo(f"  ... and {len(errors) - 5} more errors")

            try:
                asyncio.run(run_batch())
            except RuntimeError:
                # For environments with existing event loops (rare in CLI)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(run_batch())
        else:
            logger.info(f"Scraping single roaster from {url_or_file}")
            # Expecting 'name,url' format for single
            name_url = url_or_file.split(",")
            if len(name_url) != 2:
                click.echo("Error: For single roaster, provide input as 'name,url'")
                return
            name, url = name_url[0].strip(), name_url[1].strip()

            async def run_single():
                roaster_scraper = RoasterScraper()
                try:
                    result = await roaster_scraper.extract_roaster(name, url)
                    if result:
                        supabase.upsert_roaster(Roaster(**result))
                        click.echo(f"Successfully scraped roaster: {result.get('name', name)}")
                    else:
                        click.echo("No roaster data found.")
                except Exception as e:
                    click.echo(f"Error scraping roaster: {e}")

            try:
                asyncio.run(run_single())
            except RuntimeError:
                # For environments with existing event loops (rare in CLI)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(run_single())
    except Exception as e:
        logger.error(f"Roaster scraping failed: {e}")
        click.echo(f"Error: {e}")


@cli.command()
@click.argument("url_or_file")
@click.option("--force", is_flag=True, help="Force re-scrape even if data exists")
@click.option(
    "--force", is_flag=True, help="Force re-scrape even if data exists"
)  # Keep this, it's used in the new logic
@click.option("--enrich", is_flag=True, help="Use LLM to enrich missing data")  # Keep this
@click.option("--is-csv", is_flag=True, help="Input is a CSV file with URLs")
@click.option("--url-col", default="url", help="Column name for URLs in CSV")
@click.option("--name-col", default="name", help="Column name for roaster names in CSV")  # Added
@click.option("--id-col", default="id", help="Column name for roaster IDs in CSV")  # Added
@click.option("--limit", type=int, help="Limit number of URLs to process from CSV")
@click.option("--concurrent", type=int, default=1, help="Number of concurrent scraping tasks")
def scrape_products(
    url_or_file, force, enrich, is_csv, url_col, name_col, id_col, limit, concurrent
):  # Added name_col, id_col
    """Scrape coffee products from the given URL or CSV file with URLs."""
    scraper = ProductScraper()  # Instantiate ProductScraper here
    try:
        if is_csv:
            logger.info(f"Scraping products from CSV: {url_or_file}")

            # Parse CSV
            items_to_scrape = []  # Changed from urls to items_to_scrape
            with open(url_or_file, "r", encoding="utf-8") as f:
                # Ensure we are using the python csv module, not click.types.Path
                import csv as pycsv

                reader = pycsv.DictReader(f)
                if not reader.fieldnames:
                    logger.error(f"CSV file {url_or_file} is empty or has no header row.")
                    click.echo(f"Error: CSV file {url_or_file} is empty or has no header row.")
                    return

                if url_col not in reader.fieldnames:
                    logger.error(f"Column '{url_col}' not found in CSV file {url_or_file}.")
                    click.echo(f"Error: Column '{url_col}' not found in CSV file {url_or_file}.")
                    return

                for row in reader:
                    url = row.get(url_col, "").strip()
                    if url:
                        items_to_scrape.append(
                            {"url": url, "name": row.get(name_col, "").strip(), "id": row.get(id_col, "").strip()}
                        )

            if limit and limit > 0:
                items_to_scrape = items_to_scrape[:limit]

            logger.info(f"Found {len(items_to_scrape)} items in CSV file")

            # Define async scraping function
            async def scrape_all():
                semaphore = asyncio.Semaphore(concurrent)
                all_results = []

                async def scrape_with_semaphore(item):  # Signature updated
                    async with semaphore:
                        try:
                            url = item["url"]
                            roaster_name = item["name"]
                            roaster_id = item["id"]

                            if not roaster_name and url:  # If name is missing, try to derive from URL or use domain
                                parsed_url_item = urlparse(url)
                                domain_parts = parsed_url_item.netloc.split(".")
                                roaster_name = domain_parts[-2] if len(domain_parts) >= 2 else parsed_url_item.netloc

                            if not roaster_id and roaster_name:  # If ID is missing but name is present
                                roaster_id = slugify(roaster_name)
                            elif not roaster_id and not roaster_name:  # Both missing, critical issue
                                logger.error(
                                    f"Skipping URL {url} due to missing roaster name and ID in CSV or derivation failed."
                                )
                                return []

                            logger.info(
                                f"Preparing to scrape products for {roaster_name} (ID: {roaster_id}) from {url}"
                            )
                            results = await scraper.scrape_products(
                                roaster_id=roaster_id,
                                url=url,
                                roaster_name=roaster_name,
                                force_refresh=force,
                                use_enrichment=enrich,
                            )
                            return results
                        except Exception as e:
                            logger.error(f"Failed to scrape products from {item.get('url', 'unknown URL')}: {e}")
                            return []

                # Start all tasks
                tasks = [scrape_with_semaphore(item) for item in items_to_scrape]  # Updated loop

                # Process with progress bar
                for task in tqdm.tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Scraping products"):
                    results = await task
                    all_results.extend(results)
                    for coffee in results:  # Assuming results is a list of Coffee objects
                        supabase.upsert_coffee(coffee)  # supabase expects a Coffee model or dict

                return all_results

            # Run async scraping in a safe way
            # This logic for running asyncio seems fine, no changes needed here for now.
            if asyncio.get_event_loop().is_running():

                async def run_products_in_current_loop():
                    return await scrape_all()

                results = asyncio.create_task(run_products_in_current_loop())
                while not results.done():
                    pass  # Minimal busy wait, consider asyncio.wait for better control
                results = results.result()
            else:
                results = asyncio.run(scrape_all())

            # Report results
            click.echo(f"Successfully scraped {len(results)} coffee products from {len(items_to_scrape)} URLs")

        else:  # Single URL processing
            logger.info(f"Scraping products from single URL: {url_or_file}")

            async def process_single_url():
                parsed_url_single = urlparse(url_or_file)
                domain_parts = parsed_url_single.netloc.split(".")
                # Simplified name derivation
                roaster_name = domain_parts[-2] if len(domain_parts) >= 2 else parsed_url_single.netloc
                roaster_id = slugify(roaster_name)  # Simplified ID

                logger.info(f"Preparing to scrape products for {roaster_name} (ID: {roaster_id}) from {url_or_file}")
                results = await scraper.scrape_products(
                    roaster_id=roaster_id,
                    url=url_or_file,
                    roaster_name=roaster_name,
                    force_refresh=force,
                    use_enrichment=enrich,
                )

                click.echo(f"Successfully scraped {len(results)} coffee products")
                for coffee in results:  # Assuming results is a list of Coffee objects
                    supabase.upsert_coffee(coffee)  # supabase expects a Coffee model or dict
                    click.echo(f"- {coffee.name if hasattr(coffee, 'name') else 'Unknown Product'}")
                return results

            # Run the async function
            # This logic for running asyncio seems fine.
            if asyncio.get_event_loop().is_running():

                async def run_single_product_in_current_loop():
                    return await process_single_url()

                results = asyncio.create_task(run_single_product_in_current_loop())
                while not results.done():
                    pass  # Minimal busy wait
                results = results.result()
            else:
                results = asyncio.run(process_single_url())

    except Exception as e:
        logger.error(f"Product scraping failed: {e}")
        click.echo(f"Error: {e}")


@cli.command()
@click.argument("roaster_id", required=False)
@click.option("--all", is_flag=True, help="Enrich all coffees")
@click.option("--csv", is_flag=True, help="Input is a CSV file with roaster IDs")
@click.option("--id-col", default="id", help="Column name for roaster IDs in CSV")
def enrich(roaster_id, all, csv, id_col):
    """Enrich coffee data using LLM."""
    try:
        from common.enricher import enrich_coffee_data

        if csv and roaster_id:
            # Process CSV of roaster IDs
            roaster_ids = []
            with open(roaster_id, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if id_col in row:
                        rid = row[id_col].strip()
                        if rid:
                            roaster_ids.append(rid)

            logger.info(f"Found {len(roaster_ids)} roaster IDs in CSV file")

            # Get coffees for each roaster
            all_coffees = []
            for rid in roaster_ids:
                coffees = supabase.get_coffees_by_roaster(rid)
                all_coffees.extend(coffees)

            enriched_count = enrich_coffee_data(all_coffees)
            click.echo(f"Successfully enriched {enriched_count} coffee products")

        elif all:
            logger.info("Enriching all coffee data...")
            coffees = supabase.list_all(Coffee)
            enriched_count = enrich_coffee_data(coffees)
            click.echo(f"Successfully enriched {enriched_count} coffee products")

        elif roaster_id:
            logger.info(f"Enriching coffee data for roaster {roaster_id}...")
            coffees = supabase.get_coffees_by_roaster(roaster_id)
            enriched_count = enrich_coffee_data(coffees)
            click.echo(f"Successfully enriched {enriched_count} coffee products")

        else:
            click.echo("Error: Please provide a roaster_id, use --all, or use --csv with a file")
            return

    except ImportError:
        logger.error("Enricher module not implemented yet")
        click.echo("Error: Enricher not implemented yet")
    except Exception as e:
        logger.error(f"Enrichment failed: {e}")
        click.echo(f"Error: {e}")


@cli.command()
@click.option("--csv", is_flag=True, help="Output as CSV")
@click.option("--json", is_flag=True, help="Output as JSON")
@click.option("--output", type=click.Path(), help="Output file path for CSV")
def list_roasters(csv, json, output):
    """List all roasters in the database."""
    try:
        roasters = supabase.list_all(Roaster)

        if not roasters:
            click.echo("No roasters found in database.")
            return

        if csv:
            # Output as CSV using standardized exporter
            output = output or "roasters.csv"
            fieldnames = ["id", "name", "website_url", "city", "state", "country", "platform"]
            export_to_csv(
                [
                    {
                        "id": roaster.id,
                        "name": roaster.name,
                        "website_url": roaster.website_url,
                        "city": roaster.city,
                        "state": roaster.state,
                        "country": roaster.country,
                        "platform": roaster.platform,
                    }
                    for roaster in roasters
                ],
                output,
                fieldnames=fieldnames,
            )
            click.echo(f"Wrote {len(roasters)} roasters to {output}")

        elif json:
            # Output as JSON using standardized exporter
            json_output = output or "roasters.json"
            export_to_json(
                [
                    {
                        "id": roaster.id,
                        "name": roaster.name,
                        "website_url": roaster.website_url,
                        "city": roaster.city,
                        "state": roaster.state,
                        "country": roaster.country,
                        "platform": roaster.platform,
                    }
                    for roaster in roasters
                ],
                json_output,
            )
            click.echo(f"Wrote {len(roasters)} roasters to {json_output}")

        else:
            # Output to console
            click.echo(f"Found {len(roasters)} roasters:")
            for roaster in roasters:
                click.echo(f"- {roaster.name}: {roaster.website_url}")

    except Exception as e:
        logger.error(f"Listing roasters failed: {e}")
        click.echo(f"Error: {e}")


def main():
    """Non-async entry point for the application."""
    # Ensure we get a clean event loop for each run
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    cli()


@cli.command()
@click.option("--roaster-id", help="Specific roaster ID to scrape (optional)")
@click.option("--limit", type=int, default=None, help="Limit number of roasters to process")
@click.option("--force", is_flag=True, help="Force re-scrape even if data exists")
@click.option("--enrich", is_flag=True, help="Use LLM to enrich missing data")
@click.option("--concurrent", type=int, default=1, help="Number of concurrent scraping tasks")
@click.option("--active-only", is_flag=True, help="Only scrape active roasters")
def scrape_db_roasters(roaster_id, limit, force, enrich, concurrent, active_only):
    """Scrape products for roasters already in the database."""
    scraper = ProductScraper()
    try:
        # Fetch roasters from database
        if roaster_id:
            # Get specific roaster
            roaster = supabase.get_by_id(Roaster, roaster_id)
            if not roaster:
                logger.error(f"Roaster with ID {roaster_id} not found.")
                click.echo(f"Error: Roaster with ID {roaster_id} not found.")
                return
            roasters = [roaster]
        else:
            # Get all roasters or filtered subset
            query = supabase.client.table("roasters").select("*")

            if active_only:
                query = query.eq("is_active", True)

            result = query.execute()

            if not result.data:
                logger.error("No roasters found in database.")
                click.echo("Error: No roasters found in database.")
                return

            # Convert to Roaster objects
            roasters = [Roaster(**item) for item in result.data]

            # Apply limit if specified
            if limit and limit > 0:
                roasters = roasters[:limit]

        logger.info(f"Found {len(roasters)} roasters in database to process")

        # Define async scraping function
        async def scrape_all():
            semaphore = asyncio.Semaphore(concurrent)
            all_results = []

            async def scrape_with_semaphore(roaster):
                async with semaphore:
                    try:
                        # Skip if no website URL
                        if not roaster.website_url:
                            logger.warning(f"Roaster {roaster.name} (ID: {roaster.id}) has no website URL.")
                            return []

                        logger.info(f"Scraping products for {roaster.name} ({roaster.website_url})")

                        # Instantiate ProductScraper - moved outside the loop
                        # scraper = ProductScraper() # Instantiated at the start of scrape_db_roasters

                        # Scrape products
                        results = await scraper.scrape_products(
                            roaster_id=roaster.id,
                            url=str(roaster.website_url),  # Ensure URL is string
                            roaster_name=roaster.name,
                            force_refresh=force,
                            use_enrichment=enrich,
                        )
                        logger.info(f"Found {len(results)} products for {roaster.name}")

                        # Upsert to database
                        for coffee in results:
                            try:
                                supabase.upsert_coffee(coffee)
                            except Exception as e:
                                logger.error(
                                    f"Error upserting coffee {coffee.name if hasattr(coffee, 'name') else 'Unknown'}: {e}"
                                )

                        # Return serializable versions for aggregation
                        serializable_results = []
                        for coffee in results:
                            if hasattr(coffee, "model_dump"):
                                # Pydantic v2
                                serializable_results.append(coffee.model_dump(exclude_none=True))
                            elif hasattr(coffee, "dict"):
                                # Pydantic v1
                                serializable_results.append(coffee.dict(exclude_none=True))
                            else:
                                # Already a dict
                                serializable_results.append(coffee)

                        return serializable_results
                    except Exception as e:
                        logger.error(f"Failed to scrape products for {roaster.name}: {e}")
                        return []

            # Start all tasks
            tasks = [scrape_with_semaphore(roaster) for roaster in roasters]

            # Process with progress bar
            for task in tqdm.tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Scraping roasters"):
                results = await task
                all_results.extend(results)
                for coffee in results:
                    supabase.upsert_coffee(coffee)

            return all_results

        # Run async scraping in a safe way
        if asyncio.get_event_loop().is_running():
            # We're already in an event loop
            async def run_db_scraping_in_current_loop():
                return await scrape_all()

            results = asyncio.create_task(run_db_scraping_in_current_loop())
            # Wait for the task to complete
            while not results.done():
                pass
            results = results.result()
        else:
            # No event loop running, create a new one
            results = asyncio.run(scrape_all())

        # Report results
        click.echo(f"Successfully scraped {len(results)} coffee products from {len(roasters)} roasters")

    except Exception as e:
        logger.error(f"Error scraping from database roasters: {e}")
        click.echo(f"Error: {e}")


if __name__ == "__main__":
    # Use non-async main to avoid event loop conflicts
    main()
