# Coffee Scraper Backend v2

A modular, async-enabled backend for scraping coffee roaster and product data. Includes CLI tools for scraping, enrichment, and platform detection. Roaster scraping is powered by the canonical `scrapers/roasters_crawl4ai` pipeline.

## Features
- **Roaster Scraping**: Batch and single mode, using Crawl4AI logic
- **Product Scraping**: Batch and single mode, with enrichment support
- **Platform Detection**: Detects e-commerce platforms (Shopify, WooCommerce, etc.)
- **Database Integration**: Upserts roaster and product data via Supabase
- **Extensible CLI**: All main features are accessible via CLI commands

## Requirements
- Python 3.8+
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```
- Set up your `.env` file with required API keys and DB credentials

## CLI Usage
All commands are run from the project root:

### 1. Scrape Roasters (Main CLI)
#### Single Roaster
```
python main.py scrape-roaster "Roaster Name,https://roaster.com"
```

#### Batch (CSV)
```
python main.py scrape-roaster path/to/roasters.csv --csv [--url-col url] [--name-col name] [--limit N] [--concurrent N]
```
- **CSV columns required**: `name` and `url` (or specify with `--name-col`/`--url-col`)

### 2. Scrape Roasters (Scripted/Advanced)
You can also run the canonical roaster scraping pipeline directly:
```
python scrapers/roasters_crawl4ai/run.py <input_csv> [-o <output_json>] [--limit N]
```
- Example:
```
python scrapers/roasters_crawl4ai/run.py data/roasters.csv -o out.json --limit 10
```

### 3. Scrape Products (Main CLI)
#### Single Roaster
```
python main.py scrape-products "Roaster Name,https://roaster.com"
```

#### Batch (CSV)
```
python main.py scrape-products path/to/roasters.csv --csv [--url-col url] [--limit N] [--concurrent N]
```

### 4. Scrape Products (Scripted/Advanced)
You can also run the product scraper directly:
```
python scrapers/product_crawl4ai/run_product_scraper.py --roaster_id=<id> --url=<roaster_url> --roaster_name="Name"
```
- Example:
```
python scrapers/product_crawl4ai/run_product_scraper.py --roaster_id=onyx --url=https://onyxcoffeelab.com --roaster_name="Onyx Coffee Lab"
```

### 2. Scrape Products
#### Single Roaster
```
python main.py scrape-products "Roaster Name,https://roaster.com"
```

#### Batch (CSV)
```
python main.py scrape-products path/to/roasters.csv --csv [--url-col url] [--limit N] [--concurrent N]
```

### 3. Detect Platform
```
python main.py detect https://somesite.com
```
- Returns the detected e-commerce platform and confidence score.

### 4. Enrich Coffee Data
```
python main.py enrich <roaster_id> [--all] [--csv path/to/file.csv] [--id-col id]
```

### 5. List Roasters
```
python main.py list-roasters [--csv] [--output path/to/output.csv]
```

### 6. Scrape Products for All DB Roasters
```
python main.py scrape-db-roasters [--limit N] [--force] [--enrich] [--concurrent N] [--active-only]
```

## Development & Testing
- Run all tests:
  ```bash
  pytest tests
  ```
- Test coverage includes CLI, scraping flows, and platform detection.

## Project Structure
- `main.py` — CLI entry point
- `scrapers/roasters_crawl4ai/` — Canonical roaster scraping logic
- `scrapers/product_crawl4ai/` — Product scraping logic
- `db/` — Supabase integration
- `common/` — Utilities, platform detection, and shared code
- `tests/` — Test suite

## Notes
- All roaster scraping logic must use the canonical implementation in `scrapers/roasters_crawl4ai`.
- Ensure environment variables are set for API keys and DB access.
- For platform detection, the `PlatformDetector` class is used (async, class-based).

---

For further details, see code comments or contact the maintainers.
