
import requests
import pandas as pd
from slugify import slugify

from scrapers.product_crawl4ai.extractors.normalizers import normalize_tags, normalize_description
from scrapers.product_crawl4ai.extractors.price import extract_prices_from_shopify_product
from scrapers.product_crawl4ai.enrichment import enrich_coffee_product
from db.models import Coffee, CoffeePrice
from common.utils import is_coffee_product

def fetch_shopify_products(shop_url: str) -> list:
    try:
        url = f"https://{shop_url}/products.json"
        print(f"[→] Fetching: {url}")
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json().get("products", [])
    except Exception as e:
        print(f"[X] Failed to fetch from {shop_url}: {e}")
        return []

def process_product(product: dict, roaster_id: str) -> tuple:
    if not is_coffee_product(product):
        return None, None

    product_id = str(product["id"])
    slug = product["handle"]
    name = product["title"]
    description = normalize_description(product.get("body_html", ""))
    image_url = product["image"]["src"] if product.get("image") else None
    direct_buy_url = f"https://{roaster_id}/products/{slug}"
    tags = normalize_tags(product.get("tags", []))

    prices = extract_prices_from_shopify_product(product)
    enriched = enrich_coffee_product({
        "name": name,
        "description": description,
        "tags": tags
    })

    coffee = Coffee(
        id=product_id,
        name=name,
        slug=slugify(slug),
        description=description,
        image_url=image_url,
        direct_buy_url=direct_buy_url,
        roaster_id=roaster_id.replace(".", "_"),
        is_available=True,
        is_featured=False,
        tags=tags,
        roast_level=enriched.roast_level,
        bean_type=enriched.bean_type,
        processing_method=enriched.processing_method,
        acidity=enriched.acidity,
        sweetness=enriched.sweetness,
        body=enriched.body,
        varietals=enriched.varietals,
        origin_country=enriched.origin_country,
    )

    price_models = [
        CoffeePrice(size_grams=p.size_grams, price=p.price)
        for p in prices if p.size_grams and p.price
    ]

    return coffee, price_models

def scrape_and_export(shop_url: str, output_prefix: str):
    products = fetch_shopify_products(shop_url)
    coffees = []
    all_prices = []

    for product in products:
        coffee, prices = process_product(product, shop_url)
        if coffee and prices:
            coffees.append(coffee.model_dump())
            for p in prices:
                all_prices.append({
                    "coffee_id": coffee.id,
                    "size_grams": p.size_grams,
                    "price": p.price,
                })

    if not coffees:
        print("[!] No valid coffee products found.")
        return

    coffee_df = pd.DataFrame(coffees)
    price_df = pd.DataFrame(all_prices)

    coffee_df.to_csv("coffees_enriched.csv", index=False)
    price_df.to_csv("coffee_prices.csv", index=False)

    print(f"[✓] Exported {len(coffee_df)} coffees and {len(price_df)} prices.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("shop_url", help="Shopify domain, e.g., bluetokaicoffee.com")
    args = parser.parse_args()

    scrape_and_export(args.shop_url, args.shop_url)
