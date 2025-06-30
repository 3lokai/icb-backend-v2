#!/usr/bin/env python
"""
Simple script to push scraped data to Supabase using existing upsert functions.
"""

import json
from loguru import logger
from db.supabase import supabase
from db.models import Roaster, Coffee
from common.pydantic_utils import preprocess_coffee_data


def push_roaster_with_lookup(roaster_data):
    """Push a roaster to Supabase, handling existing record lookup."""
    try:
        # Check if roaster already exists by name or slug
        existing_roaster = None
        
        # Try to find by name first
        result = supabase.client.table("roasters").select("id, name, slug").eq("name", roaster_data["name"]).execute()
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

        # If roaster exists, set the ID for upsert
        if existing_roaster:
            roaster_data['id'] = existing_roaster['id']

        # Create Roaster model and upsert
        roaster = Roaster(**roaster_data)
        result = supabase.upsert_roaster(roaster)
        
        if result:
            logger.info(f"✅ Successfully upserted roaster: {roaster.name}")
            return result
        else:
            logger.error(f"❌ Failed to upsert roaster: {roaster.name}")
            return None
            
    except Exception as e:
        logger.error(f"Error upserting roaster: {e}")
        return None


def push_coffee_with_lookup(coffee_data):
    """Push a coffee to Supabase using existing upsert function."""
    try:
        # Preprocess coffee data (handles region names, etc.)
        processed_data = preprocess_coffee_data(coffee_data)
        
        # Use existing upsert function
        result = supabase.upsert_coffee(processed_data)
        
        if result:
            logger.info(f"✅ Successfully upserted coffee: {coffee_data.get('name', 'Unknown')}")
            return result
        else:
            logger.error(f"❌ Failed to upsert coffee: {coffee_data.get('name', 'Unknown')}")
            return None
            
    except Exception as e:
        logger.error(f"Error upserting coffee: {e}")
        return None


def main():
    """Main function to push both roasters and products."""
    
    # Push roaster
    logger.info("=" * 60)
    logger.info("PUSHING ROASTER")
    logger.info("=" * 60)
    
    with open('bluetokai_roaster.json', 'r', encoding='utf-8') as f:
        roasters_data = json.load(f)
    
    roaster_result = push_roaster_with_lookup(roasters_data[0])
    
    if not roaster_result:
        logger.error("Failed to push roaster, stopping")
        return 1
    
    # Push products
    logger.info("=" * 60)
    logger.info("PUSHING PRODUCTS")
    logger.info("=" * 60)
    
    with open('bluetokai_products.json', 'r', encoding='utf-8') as f:
        products_data = json.load(f)
    
    successful = 0
    errors = 0
    
    for i, product_data in enumerate(products_data, 1):
        logger.info(f"[{i}/{len(products_data)}] Processing: {product_data.get('name', 'Unknown')}")
        
        result = push_coffee_with_lookup(product_data)
        if result:
            successful += 1
        else:
            errors += 1
    
    logger.info("=" * 60)
    logger.info("UPLOAD COMPLETE")
    logger.info(f"Products: {successful} successful, {errors} errors")
    logger.info("=" * 60)
    
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main()) 