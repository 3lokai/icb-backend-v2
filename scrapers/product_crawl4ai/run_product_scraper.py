
import asyncio
import json
import sys
import os
import logging
from pprint import pprint

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.product_crawl4ai.scraper import ProductScraper
from db.models import Coffee

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Scrape coffee products for a given roaster.")
    parser.add_argument("--roaster_id", required=True, help="Unique ID for the roaster (e.g., slug)")
    parser.add_argument("--url", required=True, help="Roaster's website URL")
    parser.add_argument("--roaster_name", required=True, help="Roaster's display name")
    args = parser.parse_args()

    scraper = ProductScraper()
    roaster_id = args.roaster_id
    url = args.url
    roaster_name = args.roaster_name

    print(f"\n--- Scraping products for: {roaster_name} ({url}) ---")
    products = await scraper.scrape_products(roaster_id, url, roaster_name)
    print(f"Found {len(products)} coffee products")
    if products:
        print("\nSample product:")
        print_product_summary(products[0])
    else:
        print("No coffee products found.")

def print_product_summary(product: Coffee):
    """Print a concise summary of a coffee product."""
    # Convert to dictionary for easier printing
    if hasattr(product, 'model_dump'):
        product_dict = product.model_dump()
    elif hasattr(product, 'dict'):
        product_dict = product.dict()
    else:
        product_dict = product
    
    # Extract key fields
    summary = {
        'name': product_dict.get('name', 'Unknown'),
        'roast_level': product_dict.get('roast_level', 'Not specified'),
        'bean_type': product_dict.get('bean_type', 'Not specified'),
        'processing_method': product_dict.get('processing_method', 'Not specified'),
        'region': product_dict.get('region_name', 'Not specified'),
        'is_single_origin': product_dict.get('is_single_origin', None),
        'prices': product_dict.get('prices', []),
    }
    
    # Print summary
    print(f"Name: {summary['name']}")
    print(f"Roast Level: {summary['roast_level']}")
    print(f"Bean Type: {summary['bean_type']}")
    print(f"Processing: {summary['processing_method']}")
    print(f"Region: {summary['region']}")
    print(f"Single Origin: {summary['is_single_origin']}")
    
    # Print prices
    if summary['prices']:
        print("Prices:")
        for price in summary['prices']:
            size = price.get('size_grams', 'Unknown')
            price_value = price.get('price', 'Unknown')
            print(f"  {size}g: {price_value}")
    else:
        print("Prices: None available")

if __name__ == "__main__":
    asyncio.run(main())
