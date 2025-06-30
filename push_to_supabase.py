#!/usr/bin/env python
"""
Push scraped data to Supabase
Script to upload roasters and products from JSON files to Supabase database.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

from loguru import logger

from db.supabase import supabase
from db.models import Roaster, Coffee
from common.pydantic_utils import dict_to_pydantic_model, preprocess_coffee_data


def push_roasters_to_supabase(roasters_file: str, dry_run: bool = False) -> int:
    """Push roasters from JSON file to Supabase using smart upsert."""
    try:
        # Load roasters
        with open(roasters_file, "r", encoding="utf-8") as f:
            roasters_data = json.load(f)

        if not isinstance(roasters_data, list):
            logger.error(f"Invalid roaster data format in {roasters_file}. Expected a list.")
            return 1

        logger.info(f"Processing {len(roasters_data)} roasters")

        successful = 0
        errors = 0

        for i, roaster_data in enumerate(roasters_data, 1):
            try:
                roaster_name = roaster_data.get('name', 'Unknown')
                logger.info(f"[{i}/{len(roasters_data)}] Processing roaster: {roaster_name}")

                if dry_run:
                    logger.info(f"DRY RUN: Would upsert roaster {roaster_name}")
                    successful += 1
                    continue

                # Check if roaster already exists by name or slug
                existing_roaster = None
                try:
                    # Try to find by name first
                    result = supabase.client.table("roasters").select("id, name, slug").eq("name", roaster_name).execute()
                    if result.data:
                        existing_roaster = result.data[0]
                        logger.info(f"Found existing roaster by name: {existing_roaster['id']}")
                    else:
                        # Try to find by slug
                        slug = roaster_data.get('slug')
                        if slug:
                            result = supabase.client.table("roasters").select("id, name, slug").eq("slug", slug).execute()
                            if result.data:
                                existing_roaster = result.data[0]
                                logger.info(f"Found existing roaster by slug: {existing_roaster['id']}")

                except Exception as e:
                    logger.warning(f"Error checking for existing roaster: {e}")

                # If roaster exists, set the ID for upsert
                if existing_roaster:
                    roaster_data['id'] = existing_roaster['id']

                # Convert to Roaster model
                roaster = Roaster(**roaster_data)

                # Use smart upsert
                result = supabase.upsert_roaster(roaster)

                if result:
                    logger.info(f"✅ Successfully upserted roaster: {roaster.name}")
                    successful += 1
                else:
                    logger.error(f"❌ Failed to upsert roaster: {roaster.name}")
                    errors += 1

            except Exception as e:
                logger.error(f"Error processing roaster {i}: {e}")
                errors += 1

        logger.info(f"Roaster upload complete: {successful} successful, {errors} errors")
        return 0 if errors == 0 else 1

    except Exception as e:
        logger.error(f"Error loading roasters file: {e}")
        return 1


def push_products_to_supabase(products_file: str, roaster_id: str = None, dry_run: bool = False) -> int:
    """Push products from JSON file to Supabase using smart upsert."""
    try:
        # Load products
        with open(products_file, "r", encoding="utf-8") as f:
            products_data = json.load(f)

        if not isinstance(products_data, list):
            logger.error(f"Invalid product data format in {products_file}. Expected a list.")
            return 1

        logger.info(f"Processing {len(products_data)} products")

        successful = 0
        errors = 0

        for i, product_data in enumerate(products_data, 1):
            try:
                product_name = product_data.get('name', 'Unknown')
                logger.info(f"[{i}/{len(products_data)}] Processing product: {product_name}")

                if dry_run:
                    logger.info(f"DRY RUN: Would upsert product {product_name}")
                    successful += 1
                    continue

                # If roaster_id is provided, use it instead of the slug
                if roaster_id:
                    product_data['roaster_id'] = roaster_id
                    logger.info(f"Using provided roaster_id: {roaster_id}")

                # Preprocess coffee data (handles region names, etc.)
                processed_data = preprocess_coffee_data(product_data)

                # Use smart upsert
                result = supabase.upsert_coffee(processed_data)

                if result:
                    logger.info(f"✅ Successfully upserted product: {product_name}")
                    successful += 1
                else:
                    logger.error(f"❌ Failed to upsert product: {product_name}")
                    errors += 1

            except Exception as e:
                logger.error(f"Error processing product {i}: {e}")
                errors += 1

        logger.info(f"Product upload complete: {successful} successful, {errors} errors")
        return 0 if errors == 0 else 1

    except Exception as e:
        logger.error(f"Error loading products file: {e}")
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Push scraped data to Supabase")
    parser.add_argument("--type", choices=["roasters", "products", "both"], required=True, 
                       help="Type of data to push")
    parser.add_argument("--roasters-file", help="JSON file containing roaster data")
    parser.add_argument("--products-file", help="JSON file containing product data")
    parser.add_argument("--roaster-id", help="UUID of the roaster (for products)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")

    args = parser.parse_args()

    # Validate arguments
    if args.type in ["roasters", "both"] and not args.roasters_file:
        logger.error("--roasters-file is required when pushing roasters")
        return 1

    if args.type in ["products", "both"] and not args.products_file:
        logger.error("--products-file is required when pushing products")
        return 1

    # Check if files exist
    if args.roasters_file and not Path(args.roasters_file).exists():
        logger.error(f"Roasters file not found: {args.roasters_file}")
        return 1

    if args.products_file and not Path(args.products_file).exists():
        logger.error(f"Products file not found: {args.products_file}")
        return 1

    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made to the database")

    roaster_id = None

    # Push roasters
    if args.type in ["roasters", "both"]:
        logger.info("=" * 60)
        logger.info("PUSHING ROASTERS TO SUPABASE")
        logger.info("=" * 60)
        
        result = push_roasters_to_supabase(args.roasters_file, dry_run=args.dry_run)
        if result != 0:
            return result

        # Get the roaster ID for products if not provided
        if args.type == "both" and not args.roaster_id:
            try:
                with open(args.roasters_file, "r", encoding="utf-8") as f:
                    roasters_data = json.load(f)
                roaster_name = roasters_data[0].get('name')
                result = supabase.client.table("roasters").select("id").eq("name", roaster_name).execute()
                if result.data:
                    roaster_id = result.data[0]['id']
                    logger.info(f"Found roaster ID for products: {roaster_id}")
            except Exception as e:
                logger.warning(f"Could not get roaster ID: {e}")

    # Push products
    if args.type in ["products", "both"]:
        logger.info("=" * 60)
        logger.info("PUSHING PRODUCTS TO SUPABASE")
        logger.info("=" * 60)
        
        # Use provided roaster_id or the one we found
        product_roaster_id = args.roaster_id or roaster_id
        if not product_roaster_id:
            logger.error("No roaster_id provided or found for products")
            return 1
        
        result = push_products_to_supabase(args.products_file, roaster_id=product_roaster_id, dry_run=args.dry_run)
        if result != 0:
            return result

    logger.info("=" * 60)
    logger.info("UPLOAD COMPLETE")
    logger.info("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
