from enum import Enum


class FieldStability(Enum):
    HIGHLY_STABLE = "never"  # e.g., name, slug, founded_year, country
    MODERATELY_STABLE = (
        "quarterly"  # e.g., website_url, description, city, state, logo_url, has_physical_store, platform
    )
    VARIABLE = "monthly"  # e.g., image_url, contact_email, contact_phone, social_links, instagram_handle, has_subscription, tags, is_active
    HIGHLY_VARIABLE = "weekly"  # e.g., is_available (for coffee), stock (for products)


# Add docstring for reference
"""
FieldStability categories are based on field update frequency requirements:
- HIGHLY_STABLE: Annual check
- MODERATELY_STABLE: Quarterly check
- VARIABLE: Monthly check
- HIGHLY_VARIABLE: Weekly check

Refer to docs/roaster_db.md and docs/coffee_db.md for field assignments.
"""
