#!/usr/bin/env python
"""
Batch runner to scrape products for each roaster in the input CSV.
"""
import csv
import subprocess
import sys
from pathlib import Path
import re

def slugify(text):
    # Simple slugify: lowercase, replace spaces and special chars with hyphens
    text = text.strip().lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

INPUT_CSV = 'data/input/roasters_input.csv'
SCRAPER_MODULE = 'scrapers.product_crawl4ai.run_product_scraper'
PYTHON_EXEC = sys.executable or 'python'

# Output directory for per-roaster product data (optional)
OUTPUT_DIR = Path('data/output/products_by_roaster')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def main():
    with open(INPUT_CSV, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            name = row.get('name')
            url = row.get('website_url')
            if not name or not url:
                print(f"Skipping row with missing name or url: {row}")
                continue
            roaster_id = slugify(name)
            roaster_name = name.strip()
            output_file = OUTPUT_DIR / f"{roaster_id}_products.json"
            # Build the command to run the product scraper
            cmd = [
                PYTHON_EXEC,
                '-m', SCRAPER_MODULE,
                '--roaster_id', roaster_id,
                '--url', url,
                '--roaster_name', roaster_name,
                '--output', str(output_file)
            ]
            print(f"\nRunning scraper for {roaster_name} ({url})...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error scraping {roaster_name}: {result.stderr}")
            else:
                print(f"Scraped products for {roaster_name} saved to {output_file}")

if __name__ == '__main__':
    main()
