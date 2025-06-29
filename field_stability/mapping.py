from .categories import FieldStability

# Example mappings for roaster and coffee DB fields
ROASTER_FIELD_STABILITY = {
    # Highly Stable - Almost never change
    "name": FieldStability.HIGHLY_STABLE,
    "slug": FieldStability.HIGHLY_STABLE,
    "founded_year": FieldStability.HIGHLY_STABLE,
    "country": FieldStability.HIGHLY_STABLE,
    "address": FieldStability.HIGHLY_STABLE,
    # Moderately Stable - Change occasionally
    "website_url": FieldStability.MODERATELY_STABLE,
    "description": FieldStability.MODERATELY_STABLE,
    "city": FieldStability.MODERATELY_STABLE,
    "state": FieldStability.MODERATELY_STABLE,
    "logo_url": FieldStability.MODERATELY_STABLE,
    "has_physical_store": FieldStability.MODERATELY_STABLE,
    "platform": FieldStability.MODERATELY_STABLE,
    # Variable - Change regularly
    "image_url": FieldStability.VARIABLE,
    "contact_email": FieldStability.VARIABLE,
    "contact_phone": FieldStability.VARIABLE,
    "social_links": FieldStability.VARIABLE,
    "instagram_handle": FieldStability.VARIABLE,
    "has_subscription": FieldStability.VARIABLE,
    "tags": FieldStability.VARIABLE,
    "is_active": FieldStability.VARIABLE,
}

COFFEE_FIELD_STABILITY = {
    # Highly Stable - Coffee fundamentals rarely change
    "name": FieldStability.HIGHLY_STABLE,
    "slug": FieldStability.HIGHLY_STABLE,
    "roaster_id": FieldStability.HIGHLY_STABLE,
    "bean_type": FieldStability.HIGHLY_STABLE,
    "processing_method": FieldStability.HIGHLY_STABLE,
    "region_id": FieldStability.HIGHLY_STABLE,
    "region_name": FieldStability.HIGHLY_STABLE,
    "is_single_origin": FieldStability.HIGHLY_STABLE,
    "varietals": FieldStability.HIGHLY_STABLE,
    "altitude_meters": FieldStability.HIGHLY_STABLE,
    # Moderately Stable - Product details that change occasionally
    "description": FieldStability.MODERATELY_STABLE,
    "roast_level": FieldStability.MODERATELY_STABLE,
    "direct_buy_url": FieldStability.MODERATELY_STABLE,
    "acidity": FieldStability.MODERATELY_STABLE,
    "body": FieldStability.MODERATELY_STABLE,
    "sweetness": FieldStability.MODERATELY_STABLE,
    "aroma": FieldStability.MODERATELY_STABLE,
    "with_milk_suitable": FieldStability.MODERATELY_STABLE,
    # Variable - Marketing and seasonal content
    "image_url": FieldStability.VARIABLE,
    "is_seasonal": FieldStability.VARIABLE,
    "tags": FieldStability.VARIABLE,
    "price_250g": FieldStability.VARIABLE,
    # Highly Variable - Stock and availability
    "is_available": FieldStability.HIGHLY_VARIABLE,
    "is_featured": FieldStability.HIGHLY_VARIABLE,
    # Note: Related data (prices, brew_methods, flavor_profiles, external_links)
    # are handled separately as they're stored in junction tables
}
