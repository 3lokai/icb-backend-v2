#!/usr/bin/env python
"""
Coffee Product Scraper Runner
Script to run the coffee product scraper for one or more roasters.
"""

import sys
import argparse
import json
from pathlib import Path

from scrapers.product_crawl4ai.scraper import ProductScraper


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Coffee Product Scraper")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Batch scraper command
    batch_parser = subparsers.add_parser("batch", help="Scrape products from multiple roasters")
    batch_parser.add_argument("--roasters", required=True, help="JSON file containing roaster data")
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
    url_parser.add_argument("--no-enrichment", action="store_true", help="Disable LLM enrichment")
    url_parser.add_argument("--no-confidence", action="store_true", help="Disable confidence tracking")

    # Add validation command for existing products
    validate_parser = subparsers.add_parser("validate", help="Validate and fix existing products")
    validate_parser.add_argument("--input", required=True, help="Input JSON file containing products")
    validate_parser.add_argument("--output", help="Output JSON file (defaults to overwriting input)")

    args = parser.parse_args()

    if args.command == "batch":
        if args.roaster_link:
            return asyncio.run(scrape_roaster_link(args))
        else:
            return asyncio.run(scrape_roasters(args))
    elif args.command == "url":
        return asyncio.run(scrape_single_url(args))
    elif args.command == "validate":
        # Handle validation command
        return validate_products(args)
    else:
        parser.print_help()
        return 1


async def scrape_roaster_link(args):
    """Scrape roaster information from a link and then scrape products."""
    from scrapers.roaster.scraper import RoasterScraper  # Import here to avoid circular dependency

    roaster_scraper = RoasterScraper(
        force_refresh=args.force_refresh,
        use_enrichment=not args.no_enrichment,
        confidence_tracking=not args.no_confidence,
    )

    try:
        # Scrape roaster information
        roaster = await roaster_scraper.scrape_roaster(args.roaster_link)

        if not roaster:
            logger.error(f"Failed to scrape roaster from {args.roaster_link}")
            return 1

        # Initialize product scraper
        product_scraper = ProductScraper(
            force_refresh=args.force_refresh,
            use_enrichment=not args.no_enrichment,
            confidence_tracking=not args.no_confidence,
        )

        # Scrape products for the roaster
        products = await product_scraper.scrape_roaster_products(roaster)

        # Prepare output path
        output_path = Path(args.output)
        output_path.parent.mkdir(exist_ok=True, parents=True)

        # Save products to file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(products, f, indent=2, ensure_ascii=False)

        logger.info(f"Scraped {len(products)} products from {args.roaster_link}")

        # Print summary
        print("\n" + "=" * 60)
        print("COFFEE PRODUCT SCRAPER SUMMARY")
        print("=" * 60)
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
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(fixed_products, f, indent=2, ensure_ascii=False)

        logger.info(f"Validated and fixed {len(fixed_products)} products")
        logger.info(f"Saved to {output_path}")

        return 0

    except Exception as e:
        logger.error(f"Error validating products: {e}")
        return 1


if __name__ == "__main__":
    import asyncio

    sys.exit(asyncio.run(main()))
