from .categories import FieldStability

# Example mappings for roaster and coffee DB fields
ROASTER_FIELD_STABILITY = {
    'name': FieldStability.HIGHLY_STABLE,
    'slug': FieldStability.HIGHLY_STABLE,
    'founded_year': FieldStability.HIGHLY_STABLE,
    'country': FieldStability.HIGHLY_STABLE,
    'website_url': FieldStability.MODERATELY_STABLE,
    'description': FieldStability.MODERATELY_STABLE,
    'city': FieldStability.MODERATELY_STABLE,
    'state': FieldStability.MODERATELY_STABLE,
    'logo_url': FieldStability.MODERATELY_STABLE,
    'has_physical_store': FieldStability.MODERATELY_STABLE,
    'platform': FieldStability.MODERATELY_STABLE,
    'image_url': FieldStability.VARIABLE,
    'contact_email': FieldStability.VARIABLE,
    'contact_phone': FieldStability.VARIABLE,
    'social_links': FieldStability.VARIABLE,
    'instagram_handle': FieldStability.VARIABLE,
    'has_subscription': FieldStability.VARIABLE,
    'tags': FieldStability.VARIABLE,
    'is_active': FieldStability.VARIABLE,
}

COFFEE_FIELD_STABILITY = {
    'name': FieldStability.HIGHLY_STABLE,
    'slug': FieldStability.HIGHLY_STABLE,
    'roaster_id': FieldStability.HIGHLY_STABLE,
    'bean_type': FieldStability.HIGHLY_STABLE,
    'processing_method': FieldStability.HIGHLY_STABLE,
    'region_id': FieldStability.HIGHLY_STABLE,
    'is_single_origin': FieldStability.HIGHLY_STABLE,
    'description': FieldStability.MODERATELY_STABLE,
    'roast_level': FieldStability.MODERATELY_STABLE,
    'direct_buy_url': FieldStability.MODERATELY_STABLE,
    'image_url': FieldStability.VARIABLE,
    'is_seasonal': FieldStability.VARIABLE,
    'tags': FieldStability.VARIABLE,
    'is_available': FieldStability.HIGHLY_VARIABLE,
}
