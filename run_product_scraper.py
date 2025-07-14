#!/usr/bin/env python
"""
Coffee Product Scraper Runner
Script to run the coffee product scraper for one or more roasters.

Usage Examples:
    # Scrape products from a roaster link
    python run_product_scraper.py batch --roaster-link "https://bluetokai.com"

    # Scrape products from multiple roasters
    python run_product_scraper.py batch --roasters roasters.json --limit 5

    # Scrape a single product URL
    python run_product_scraper.py url --url "https://bluetokai.com/products/light-roast" --roaster-name "Blue Tokai"

    # Validate existing products
    python run_product_scraper.py validate --input products.json

    # Test a new roaster with custom settings
    python run_product_scraper.py batch --roaster-link "https://ainmane.com" --output ainmane_products.json --force-refresh --no-enrichment

    # Batch scrape with platform filtering
    python run_product_scraper.py batch --roasters roasters.json --platform shopify --limit 3 --export-format csv

    # Single product with enrichment disabled
    python run_product_scraper.py url --url "https://example.com/product" --roaster-name "Test Roaster" --no-enrichment --no-confidence

    # Validate and fix existing products
    python run_product_scraper.py validate --input products.json --output fixed_products.json

Available Commands and Arguments:

BATCH COMMAND (python run_product_scraper.py batch):
    --roasters: JSON file containing roaster data
    --roaster-link: Single roaster URL to scrape
    --output: Output file (default: ./output/products.json)
    --export-format: Export format: json or csv (default: json)
    --platform: Only scrape specific platform (shopify, woocommerce, static)
    --roaster-id: Only scrape specific roaster by ID or slug
    --limit: Limit number of roasters to scrape
    --force-refresh: Force refresh, ignore cache
    --no-enrichment: Disable LLM enrichment
    --no-confidence: Disable confidence tracking
    --analyze: Generate field coverage analysis report

URL COMMAND (python run_product_scraper.py url):
    --url: Product URL to scrape (required)
    --output: Output JSON file (default: ./output/single_product.json)
    --roaster-name: Roaster name (default: Unknown)
    --roaster-id: Roaster ID (default: unknown)
    --no-enrichment: Disable LLM enrichment
    --no-confidence: Disable confidence tracking

VALIDATE COMMAND (python run_product_scraper.py validate):
    --input: Input JSON file containing products (required)
    --output: Output JSON file (defaults to overwriting input)
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import List, Union
from urllib.parse import urlparse

from loguru import logger

from scrapers.product_crawl4ai.extractors.normalizers import standardize_coffee_model
from scrapers.product_crawl4ai.extractors.validators import apply_validation_corrections, validate_coffee_product
from scrapers.product_crawl4ai.scraper import ProductScraper


def to_json_serializable(obj) -> dict:
    """Convert Pydantic model to JSON-serializable dict."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    elif hasattr(obj, "dict"):
        return obj.dict()
    elif isinstance(obj, dict):
        return obj
    else:
        return obj


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Coffee Product Scraper")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Batch scraper command
    batch_parser = subparsers.add_parser("batch", help="Scrape products from multiple roasters")
    batch_parser.add_argument("--roasters", help="JSON file containing roaster data")
    batch_parser.add_argument("--output", default="./output/products.json", help="Output file (JSON or CSV)")
    batch_parser.add_argument(
        "--export-format", choices=["json", "csv"], default="json", help="Export format: json or csv (default: json)"
    )
    batch_parser.add_argument("--platform", help="Only scrape specific platform (shopify, woocommerce, static)")
    batch_parser.add_argument("--roaster-id", help="Only scrape specific roaster by ID or slug")
    batch_parser.add_argument("--limit", type=int, help="Limit number of roasters to scrape")
    batch_parser.add_argument("--force-refresh", action="store_true", help="Force refresh, ignore cache")
    batch_parser.add_argument("--no-enrichment", action="store_true", help="Disable LLM enrichment")
    batch_parser.add_argument("--no-confidence", action="store_true", help="Disable confidence tracking")
    batch_parser.add_argument("--analyze", action="store_true", help="Generate field coverage analysis report")
    batch_parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    batch_parser.add_argument("--roaster-link", help="Roaster link to scrape")

    # Single URL scraper command
    url_parser = subparsers.add_parser("url", help="Scrape a single product URL")
    url_parser.add_argument("--url", required=True, help="Product URL to scrape")
    url_parser.add_argument("--output", default="./output/single_product.json", help="Output JSON file")
    url_parser.add_argument("--roaster-name", default="Unknown", help="Roaster name (for context)")
    url_parser.add_argument("--roaster-id", default="unknown", help="Roaster ID (for context)")
    url_parser.add_argument("--no-enrichment", action="store_true", help="Disable LLM enrichment")
    url_parser.add_argument("--no-confidence", action="store_true", help="Disable confidence tracking")
    url_parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    # Add validation command for existing products
    validate_parser = subparsers.add_parser("validate", help="Validate and fix existing products")
    validate_parser.add_argument("--input", required=True, help="Input JSON file containing products")
    validate_parser.add_argument("--output", help="Output JSON file (defaults to overwriting input)")

    args = parser.parse_args()

    # Enable debug logging if requested
    if hasattr(args, 'debug') and args.debug:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG", format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>")
        
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
        for name in logging.root.manager.loggerDict:
            logging.getLogger(name).setLevel(logging.DEBUG)
        
        logger.info("Debug logging enabled")

    if args.command == "batch":
        if args.roaster_link:
            return await scrape_roaster_link(args)
        elif args.roasters:
            return await scrape_roasters(args)
        else:
            logger.error("Either --roaster-link or --roasters must be specified for batch mode")
            return 1
    elif args.command == "url":
        return await scrape_single_url(args)
    elif args.command == "validate":
        return validate_products(args)
    else:
        parser.print_help()
        return 1


async def scrape_roasters(args):
    """Scrape products from multiple roasters."""
    try:
        # Load roasters from JSON file
        with open(args.roasters, "r", encoding="utf-8") as f:
            roasters = json.load(f)

        if not isinstance(roasters, list):
            logger.error(f"Invalid roaster data format in {args.roasters}. Expected a list.")
            return 1

        # Apply filters
        if args.limit:
            roasters = roasters[:args.limit]

        if args.platform:
            roasters = [r for r in roasters if r.get("platform") == args.platform]

        if args.roaster_id:
            roasters = [r for r in roasters if r.get("id") == args.roaster_id or r.get("slug") == args.roaster_id]

        logger.info(f"Processing {len(roasters)} roasters")

        # Initialize product scraper
        product_scraper = ProductScraper()
        all_products = []

        for roaster in roasters:
            try:
                roaster_id = roaster.get("id", roaster.get("slug", "unknown"))
                roaster_name = roaster.get("name", "Unknown")
                website_url = roaster.get("website_url", "")

                if not website_url:
                    logger.warning(f"Skipping {roaster_name}: no website URL")
                    continue

                logger.info(f"Scraping products for {roaster_name} ({website_url})")

                # Scrape products (returns list of Pydantic models)
                products = await product_scraper.scrape_products(
                    roaster_id=roaster_id,
                    url=website_url,
                    roaster_name=roaster_name,
                    force_refresh=args.force_refresh,
                    use_enrichment=not args.no_enrichment,
                )

                # Keep as Pydantic models, only convert when saving
                all_products.extend(products)
                logger.info(f"Found {len(products)} products for {roaster_name}")

            except Exception as e:
                logger.error(f"Error scraping products for {roaster.get('name', 'Unknown')}: {e}")
                continue

        # Save results
        output_path = Path(args.output)
        output_path.parent.mkdir(exist_ok=True, parents=True)

        if args.export_format == "json":
            # Convert to JSON-serializable format only when saving
            json_data = [to_json_serializable(product) for product in all_products]
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
        else:  # CSV
            from common.exporter import export_to_csv
            # Convert to dicts for CSV export
            csv_data = [to_json_serializable(product) for product in all_products]
            export_to_csv(csv_data, str(output_path))

        logger.info(f"Scraped {len(all_products)} total products")
        logger.info(f"Saved to {args.output}")

        # Print summary
        print("\n" + "=" * 60)
        print("COFFEE PRODUCT SCRAPER SUMMARY")
        print("=" * 60)
        print(f"Total roasters processed: {len(roasters)}")
        print(f"Total products scraped: {len(all_products)}")
        print(f"Output file: {args.output}")
        print("=" * 60 + "\n")

        return 0

    except Exception as e:
        logger.error(f"Error in batch scraping: {e}")
        return 1


async def scrape_single_url(args):
    """Scrape a single product URL."""
    try:
        product_scraper = ProductScraper()
        logger.info(f"Scraping single product: {args.url}")

        # Scrape the single product (returns Pydantic model)
        product = await product_scraper.scrape_single_product(
            product_url=args.url, 
            roaster_id=args.roaster_id, 
            roaster_name=args.roaster_name
        )

        if not product:
            logger.error(f"Failed to scrape product from {args.url}")
            return 1

        # Use direct attribute access on Pydantic model
        logger.info(f"Successfully scraped product: {product.name}")
        logger.info(f"Saved to {args.output}")

        # Save to file (convert to JSON only here)
        output_path = Path(args.output)
        output_path.parent.mkdir(exist_ok=True, parents=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([to_json_serializable(product)], f, indent=2, ensure_ascii=False)

        # Print summary with direct attribute access
        print("\n" + "=" * 60)
        print("SINGLE PRODUCT SCRAPER SUMMARY")
        print("=" * 60)
        print(f"Product: {product.name}")
        print(f"Roaster: {args.roaster_name}")
        print(f"URL: {args.url}")
        print(f"Output file: {args.output}")
        print("=" * 60 + "\n")

        return 0

    except Exception as e:
        logger.error(f"Error scraping single product: {e}")
        return 1


async def scrape_roaster_link(args):
    """Scrape roaster information from a link and then scrape products."""
    from scrapers.roasters_crawl4ai.crawler import RoasterCrawler

    roaster_crawler = RoasterCrawler()

    try:
        # Extract name from URL
        roaster_name = "Unknown Roaster"
        roaster_url = args.roaster_link
        
        parsed_url = urlparse(roaster_url)
        if parsed_url.netloc:
            domain_parts = parsed_url.netloc.replace('www.', '').split('.')
            if domain_parts:
                roaster_name = domain_parts[0].replace('-', ' ').replace('_', ' ').title()

        # Extract roaster info (returns Pydantic model)
        roaster = await roaster_crawler.extract_roaster(roaster_name, roaster_url)

        if not roaster:
            logger.error(f"Failed to scrape roaster from {args.roaster_link}")
            return 1

        # Initialize product scraper
        product_scraper = ProductScraper()

        # Use direct attribute access on Pydantic roaster model
        products = await product_scraper.scrape_products(
            roaster_id=roaster.get("roaster_id") or args.roaster_id,
            url=roaster.get("website_url") or args.roaster_link,
            roaster_name=roaster.get("name") or roaster_name,
            force_refresh=args.force_refresh,
            use_enrichment=not args.no_enrichment,
        )

        # Save products (convert to JSON only when saving)
        output_path = Path(args.output)
        output_path.parent.mkdir(exist_ok=True, parents=True)

        json_data = [to_json_serializable(product) for product in products]
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Scraped {len(products)} products from {args.roaster_link}")

        # Print summary with direct attribute access
        print("\n" + "=" * 60)
        print("COFFEE PRODUCT SCRAPER SUMMARY")
        print("=" * 60)
        print(f"Roaster: {roaster.get('name', 'Unknown')}")
        print(f"Total products scraped: {len(products)}")
        print(f"Output file: {args.output}")
        print("=" * 60 + "\n")

        return 0

    except Exception as e:
        logger.error(f"Error scraping roaster or products: {e}")
        return 1


def validate_products(args):
    """Validate and fix existing product data."""
    try:
        # Load products
        with open(args.input, "r", encoding="utf-8") as f:
            products = json.load(f)

        if not isinstance(products, list):
            logger.error(f"Invalid product data format in {args.input}. Expected a list.")
            return 1

        logger.info(f"Validating {len(products)} products")

        # Process each product
        fixed_products = []
        for product in products:
            # Standardize model
            standardized = standardize_coffee_model(product)
            
            # Validate fields
            validation_results = validate_coffee_product(standardized)
            fixed = apply_validation_corrections(standardized, validation_results)
            
            fixed_products.append(fixed)

        # Save output
        output_path = args.output if args.output else args.input
        json_data = [to_json_serializable(product) for product in fixed_products]
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Validated and fixed {len(fixed_products)} products")
        logger.info(f"Saved to {output_path}")

        return 0

    except Exception as e:
        logger.error(f"Error validating products: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))