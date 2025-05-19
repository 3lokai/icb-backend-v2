#!/usr/bin/env python
"""
Coffee Product Scraper Runner
Script to run the coffee product scraper for one or more roasters.
"""

import argparse
import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
import sys
from common.exporter import export_to_json, export_to_csv

from scrapers.product.scraper import ProductScraper
from scrapers.product.extractors.validators import validate_coffee_product, apply_validation_corrections
from scrapers.product.extractors.normalizers import standardize_coffee_model

# Configure logging
logs_dir = Path("./logs")
logs_dir.mkdir(exist_ok=True, parents=True)
log_file = logs_dir / f"product_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger(__name__)

def load_roasters(file_path: str):
    """Load roaster data from JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            roasters = json.load(f)
        
        if isinstance(roasters, dict) and 'roasters' in roasters:
            # Handle case where roasters are in a nested field
            roasters = roasters['roasters']
        
        if not isinstance(roasters, list):
            logger.error(f"Invalid roaster data format in {file_path}. Expected a list.")
            return []
        
        return roasters
    except FileNotFoundError:
        logger.error(f"Roaster file not found: {file_path}")
        return []
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in roaster file: {file_path}")
        return []

def filter_roasters(roasters, platform=None, roaster_id=None, limit=None):
    """Filter roasters based on criteria."""
    filtered = roasters
    
    if platform:
        filtered = [r for r in filtered if platform.lower() in r.get('platform', '').lower()]
        logger.info(f"Filtered to {len(filtered)} roasters with platform '{platform}'")
    
    if roaster_id:
        filtered = [r for r in filtered if r.get('id') == roaster_id or r.get('slug') == roaster_id]
        logger.info(f"Filtered to {len(filtered)} roasters with ID/slug '{roaster_id}'")
    
    if limit is not None and limit > 0:
        filtered = filtered[:limit]
        logger.info(f"Limited to {len(filtered)} roasters")
    
    return filtered

async def scrape_roasters(args):
    """Run the product scraper for the specified roasters."""
    # Load roasters
    roasters = load_roasters(args.roasters)
    if not roasters:
        logger.error("No roasters found or unable to load roasters.")
        return 1

    # Patch ProductScraper.scrape_to_file to support returning the products for export
    from functools import wraps
    orig_scrape_to_file = ProductScraper.scrape_to_file
    @wraps(orig_scrape_to_file)
    async def scrape_to_file_with_products(self, roasters, output_file, return_products=False):
        result = await orig_scrape_to_file(self, roasters, output_file)
        # Reproduce serialization logic from ProductScraper.scrape_to_file
        # (should match the actual implementation)
        all_products = []
        for roaster in roasters:
            try:
                products = await self.scrape_roaster_products(roaster)
                if products:
                    all_products.extend(products)
            except Exception:
                continue
        serialized_products = []
        for coffee in all_products:
            if hasattr(coffee, 'model_dump'):
                serialized_products.append(coffee.model_dump())
            elif hasattr(coffee, 'dict'):
                serialized_products.append(coffee.dict())
            else:
                serialized_products.append(coffee)
        if return_products:
            return result[0], result[1], serialized_products
        return result
    ProductScraper.scrape_to_file = scrape_to_file_with_products

    
    # Filter roasters based on args
    roasters = filter_roasters(
        roasters, 
        platform=args.platform,
        roaster_id=args.roaster_id,
        limit=args.limit
    )
    
    if not roasters:
        logger.error("No roasters match the specified criteria.")
        return 1
    
    # Initialize scraper
    scraper = ProductScraper(
        force_refresh=args.force_refresh,
        use_enrichment=not args.no_enrichment,
        confidence_tracking=not args.no_confidence
    )
    
    # Prepare output path
    output_path = Path(args.output)
    output_path.parent.mkdir(exist_ok=True, parents=True)
    
    # Run scraper
    logger.info(f"Starting scraper for {len(roasters)} roasters")
    total_products, total_roasters, serialized_products = await scraper.scrape_to_file(roasters, args.output, return_products=True)

    # Export products in selected format
    export_format = getattr(args, 'export_format', 'json')
    if total_products > 0:
        if export_format == 'csv':
            # Use all keys from first product for fieldnames
            fieldnames = list(serialized_products[0].keys()) if serialized_products else []
            export_to_csv(serialized_products, str(output_path), fieldnames=fieldnames)
            logger.info(f"Exported products to CSV: {args.output}")
        else:
            export_to_json(serialized_products, str(output_path), indent=2)
            logger.info(f"Exported products to JSON: {args.output}")

    # Generate field coverage report if requested
    if args.analyze and total_products > 0:
        coverage_stats = scraper.analyze_field_coverage(serialized_products)
        source_stats = scraper.get_field_source_stats(serialized_products)
        analysis_path = output_path.parent / f"{output_path.stem}_analysis.json"
        export_to_json({
            "field_coverage": coverage_stats,
            "field_sources": source_stats,
            "total_products": len(serialized_products),
            "total_roasters": total_roasters,
            "timestamp": datetime.now().isoformat()
        }, str(analysis_path), indent=2)
        logger.info(f"Saved analysis report to {analysis_path}")

    # Print summary
    print("\n" + "="*60)
    print(f"COFFEE PRODUCT SCRAPER SUMMARY")
    print("="*60)
    print(f"Total roasters processed: {total_roasters}/{len(roasters)}")
    print(f"Total products scraped: {total_products}")
    print(f"Output file: {args.output}")
    print(f"Export format: {export_format}")
    print(f"Log file: {log_file}")
    print("="*60 + "\n")

    # Return error code based on results
    if total_roasters == 0:
        return 1
    return 0

async def scrape_single_url(args):
    """Scrape a single product URL directly."""
    # Initialize scraper
    scraper = ProductScraper(
        force_refresh=True,  # Always force refresh for single URLs
        use_enrichment=not args.no_enrichment,
        confidence_tracking=not args.no_confidence
    )
    
    # Run scraper
    logger.info(f"Scraping single URL: {args.url}")
    product = await scraper.scrape_single_url(args.url, args.roaster_name)
    
    if not product:
        logger.error(f"Failed to scrape product from {args.url}")
        return 1
    
    # Save output
    output_path = Path(args.output)
    output_path.parent.mkdir(exist_ok=True, parents=True)
    
    export_to_json(product, str(output_path), indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print(f"SINGLE PRODUCT SCRAPER SUMMARY")
    print("="*60)
    print(f"Product: {product.get('name', 'Unknown')}")
    print(f"Roast Level: {product.get('roast_level', 'Unknown')}")
    print(f"Bean Type: {product.get('bean_type', 'Unknown')}")
    print(f"Processing Method: {product.get('processing_method', 'Unknown')}")
    if 'flavor_profiles' in product:
        print(f"Flavor Profiles: {', '.join(product['flavor_profiles'])}")
    print(f"Price (250g): {product.get('price_250g', 'Unknown')}")
    print(f"Output file: {args.output}")
    print("="*60 + "\n")
    
    return 0

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Coffee Product Scraper")
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Batch scraper command
    batch_parser = subparsers.add_parser('batch', help='Scrape products from multiple roasters')
    batch_parser.add_argument('--roasters', required=True, help='JSON file containing roaster data')
    batch_parser.add_argument('--output', default='./output/products.json', help='Output file (JSON or CSV)')
    batch_parser.add_argument('--export-format', choices=['json', 'csv'], default='json', help='Export format: json or csv (default: json)')
    batch_parser.add_argument('--platform', help='Only scrape specific platform (shopify, woocommerce, static)')
    batch_parser.add_argument('--roaster-id', help='Only scrape specific roaster by ID or slug')
    batch_parser.add_argument('--limit', type=int, help='Limit number of roasters to scrape')
    batch_parser.add_argument('--force-refresh', action='store_true', help='Force refresh, ignore cache')
    batch_parser.add_argument('--no-enrichment', action='store_true', help='Disable LLM enrichment')
    batch_parser.add_argument('--no-confidence', action='store_true', help='Disable confidence tracking')
    batch_parser.add_argument('--analyze', action='store_true', help='Generate field coverage analysis report')

    # Add roaster link argument
    batch_parser.add_argument('--roaster-link', help='Roaster link to scrape')
    
    # Single URL scraper command
    url_parser = subparsers.add_parser('url', help='Scrape a single product URL')
    url_parser.add_argument('--url', required=True, help='Product URL to scrape')
    url_parser.add_argument('--output', default='./output/single_product.json', help='Output JSON file')
    url_parser.add_argument('--roaster-name', default='Unknown', help='Roaster name (for context)')
    url_parser.add_argument('--no-enrichment', action='store_true', help='Disable LLM enrichment')
    url_parser.add_argument('--no-confidence', action='store_true', help='Disable confidence tracking')
    
    # Add validation command for existing products
    validate_parser = subparsers.add_parser('validate', help='Validate and fix existing products')
    validate_parser.add_argument('--input', required=True, help='Input JSON file containing products')
    validate_parser.add_argument('--output', help='Output JSON file (defaults to overwriting input)')
    
    args = parser.parse_args()
    
    if args.command == 'batch':
        if args.roaster_link:
            return asyncio.run(scrape_roaster_link(args))
        else:
            return asyncio.run(scrape_roasters(args))
    elif args.command == 'url':
        return asyncio.run(scrape_single_url(args))
    elif args.command == 'validate':
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
        confidence_tracking=not args.no_confidence
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
            confidence_tracking=not args.no_confidence
        )
        
        # Scrape products for the roaster
        products = await product_scraper.scrape_roaster_products(roaster)
        
        # Prepare output path
        output_path = Path(args.output)
        output_path.parent.mkdir(exist_ok=True, parents=True)
        
        # Save products to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Scraped {len(products)} products from {args.roaster_link}")
        
        # Print summary
        print("\n" + "="*60)
        print(f"COFFEE PRODUCT SCRAPER SUMMARY")
        print("="*60)
        print(f"Total products scraped: {len(products)}")
        print(f"Output file: {args.output}")
        print("="*60 + "\n")
        
        return 0
    
    except Exception as e:
        logger.error(f"Error scraping roaster or products: {e}")
        return 1

def validate_products(args):
    """Validate and fix existing product data."""
    try:
        # Load products
        with open(args.input, 'r', encoding='utf-8') as f:
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
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(fixed_products, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Validated and fixed {len(fixed_products)} products")
        logger.info(f"Saved to {output_path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error validating products: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
