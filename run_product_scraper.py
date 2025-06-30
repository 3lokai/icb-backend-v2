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
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from loguru import logger

from scrapers.product_crawl4ai.extractors.normalizers import standardize_coffee_model
from scrapers.product_crawl4ai.extractors.validators import apply_validation_corrections, validate_coffee_product
from scrapers.product_crawl4ai.scraper import ProductScraper


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

    # Add roaster link argument
    batch_parser.add_argument("--roaster-link", help="Roaster link to scrape")

    # Single URL scraper command
    url_parser = subparsers.add_parser("url", help="Scrape a single product URL")
    url_parser.add_argument("--url", required=True, help="Product URL to scrape")
    url_parser.add_argument("--output", default="./output/single_product.json", help="Output JSON file")
    url_parser.add_argument("--roaster-name", default="Unknown", help="Roaster name (for context)")
    url_parser.add_argument("--roaster-id", default="unknown", help="Roaster ID (for context)")
    url_parser.add_argument("--no-enrichment", action="store_true", help="Disable LLM enrichment")
    url_parser.add_argument("--no-confidence", action="store_true", help="Disable confidence tracking")

    # Add validation command for existing products
    validate_parser = subparsers.add_parser("validate", help="Validate and fix existing products")
    validate_parser.add_argument("--input", required=True, help="Input JSON file containing products")
    validate_parser.add_argument("--output", help="Output JSON file (defaults to overwriting input)")

    args = parser.parse_args()

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
        # Handle validation command (this is not async)
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

        # Apply limit if specified
        if args.limit:
            roasters = roasters[: args.limit]

        # Filter by platform if specified
        if args.platform:
            roasters = [r for r in roasters if r.get("platform") == args.platform]

        # Filter by roaster ID if specified
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

                # Scrape products for this roaster
                products = await product_scraper.scrape_products(
                    roaster_id=roaster_id,
                    url=website_url,
                    roaster_name=roaster_name,
                    force_refresh=args.force_refresh,
                    use_enrichment=not args.no_enrichment,
                )

                # Convert to dict for JSON serialization
                product_dicts = []
                for product in products:
                    if hasattr(product, "model_dump"):
                        product_dicts.append(product.model_dump(mode="json"))
                    elif hasattr(product, "dict"):
                        product_dicts.append(product.dict())
                    else:
                        product_dicts.append(product)

                all_products.extend(product_dicts)
                logger.info(f"Found {len(products)} products for {roaster_name}")

            except Exception as e:
                logger.error(f"Error scraping products for {roaster.get('name', 'Unknown')}: {e}")
                continue

        # Save results
        output_path = Path(args.output)
        output_path.parent.mkdir(exist_ok=True, parents=True)

        if args.export_format == "json":
            # Convert all products to plain dicts for JSON serialization
            def to_primitive(obj):
                if hasattr(obj, "model_dump"):
                    return obj.model_dump(mode="json")
                elif hasattr(obj, "dict"):
                    return obj.dict()
                return obj
            all_products_primitive = [to_primitive(p) for p in all_products]
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(all_products_primitive, f, indent=2, ensure_ascii=False)
        else:  # CSV
            from common.exporter import export_to_csv

            export_to_csv(all_products, str(output_path))

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
        # Initialize product scraper
        product_scraper = ProductScraper()

        logger.info(f"Scraping single product: {args.url}")

        # Scrape the single product
        product = await product_scraper.scrape_single_product(
            product_url=args.url, roaster_id=args.roaster_id, roaster_name=args.roaster_name
        )

        if not product:
            logger.error(f"Failed to scrape product from {args.url}")
            return 1

        # Convert to dict for JSON serialization
        if hasattr(product, "model_dump"):
            product_dict = product.model_dump(mode="json")
        elif hasattr(product, "dict"):
            product_dict = product.dict()
        else:
            product_dict = product

        # Save result
        output_path = Path(args.output)
        output_path.parent.mkdir(exist_ok=True, parents=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([product_dict], f, indent=2, ensure_ascii=False)

        logger.info(f"Successfully scraped product: {product_dict.get('name', 'Unknown')}")
        logger.info(f"Saved to {args.output}")

        # Print summary
        print("\n" + "=" * 60)
        print("SINGLE PRODUCT SCRAPER SUMMARY")
        print("=" * 60)
        print(f"Product: {product_dict.get('name', 'Unknown')}")
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
    from scrapers.roaster.scraper import RoasterScraper  # Import here to avoid circular dependency

    roaster_scraper = RoasterScraper()

    try:
        # Scrape roaster information
        roaster = await roaster_scraper.scrape_roaster(args.roaster_link)

        if not roaster:
            logger.error(f"Failed to scrape roaster from {args.roaster_link}")
            return 1

        # Initialize product scraper
        product_scraper = ProductScraper()

        # Scrape products for the roaster
        products = await product_scraper.scrape_products(
            roaster_id=roaster.get("id", roaster.get("slug", "unknown")),
            url=roaster.get("website_url", args.roaster_link),
            roaster_name=roaster.get("name", "Unknown"),
            force_refresh=args.force_refresh,
            use_enrichment=not args.no_enrichment,
        )

        # Convert to dict for JSON serialization
        product_dicts = []
        for product in products:
            if hasattr(product, "model_dump"):
                product_dicts.append(product.model_dump(mode="json"))
            elif hasattr(product, "dict"):
                product_dicts.append(product.dict())
            else:
                product_dicts.append(product)

        # Prepare output path
        output_path = Path(args.output)
        output_path.parent.mkdir(exist_ok=True, parents=True)

        # Save products to file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(product_dicts, f, indent=2, ensure_ascii=False)

        logger.info(f"Scraped {len(products)} products from {args.roaster_link}")

        # Print summary
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

        # Determine output path
        output_path = args.output if args.output else args.input

        # Save output
        fixed_products_primitive = [p if not hasattr(p, "model_dump") else p.model_dump(mode="json") for p in fixed_products]
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(fixed_products_primitive, f, indent=2, ensure_ascii=False)

        logger.info(f"Validated and fixed {len(fixed_products)} products")
        logger.info(f"Saved to {output_path}")

        return 0

    except Exception as e:
        logger.error(f"Error validating products: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
