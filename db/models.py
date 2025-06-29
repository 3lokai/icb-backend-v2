"""
Database models for the Coffee Scraper.
These models should match the Supabase schema.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, HttpUrl

class RoastLevel(str):
    """Roast level enum values."""

    LIGHT = "light"
    LIGHT_MEDIUM = "light-medium"
    MEDIUM = "medium"
    MEDIUM_DARK = "medium-dark"
    DARK = "dark"
    CITY = "city"
    CITY_PLUS = "city-plus"
    FULL_CITY = "full-city"
    FRENCH = "french"
    ITALIAN = "italian"
    CINNAMON = "cinnamon"
    FILTER = "filter"
    ESPRESSO = "espresso"
    OMNIROAST = "omniroast"
    UNKNOWN = "unknown"

    ALL = {
        LIGHT,
        LIGHT_MEDIUM,
        MEDIUM,
        MEDIUM_DARK,
        DARK,
        CITY,
        CITY_PLUS,
        FULL_CITY,
        FRENCH,
        ITALIAN,
        CINNAMON,
        FILTER,
        ESPRESSO,
        OMNIROAST,
        UNKNOWN,
    }

class BeanType(str):
    """Bean type enum values."""

    ARABICA = "arabica"
    ROBUSTA = "robusta"
    LIBERICA = "liberica"
    BLEND = "blend"
    MIXED_ARABICA = "mixed-arabica"
    ARABICA_ROBUSTA = "arabica-robusta"
    UNKNOWN = "unknown"

    ALL = {ARABICA, ROBUSTA, LIBERICA, BLEND, MIXED_ARABICA, ARABICA_ROBUSTA, UNKNOWN}

class ProcessingMethod(str):
    """Processing method enum values."""

    WASHED = "washed"
    NATURAL = "natural"
    HONEY = "honey"
    PULPED_NATURAL = "pulped-natural"
    ANAEROBIC = "anaerobic"
    MONSOONED = "monsooned"
    WET_HULLED = "wet-hulled"
    CARBONIC_MACERATION = "carbonic-maceration"
    DOUBLE_FERMENTED = "double-fermented"
    UNKNOWN = "unknown"

    ALL = {
        WASHED,
        NATURAL,
        HONEY,
        PULPED_NATURAL,
        ANAEROBIC,
        MONSOONED,
        WET_HULLED,
        CARBONIC_MACERATION,
        DOUBLE_FERMENTED,
        UNKNOWN,
    }

class BaseDBModel(BaseModel):
    """Base model with common fields."""

    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Roaster(BaseDBModel):
    """Model for coffee roasters."""

    name: str
    slug: str
    website_url: HttpUrl
    description: Optional[str] = None
    address: Optional[str] = None  # Add this new field
    country: str = "India"
    city: Optional[str] = None
    state: Optional[str] = None
    founded_year: Optional[int] = None
    logo_url: Optional[HttpUrl] = None
    image_url: Optional[HttpUrl] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    social_links: Optional[List[str]] = None  # Not a SocialLinks object
    instagram_handle: Optional[str] = None
    has_subscription: Optional[bool] = None
    has_physical_store: Optional[bool] = None
    platform: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: bool = True
    is_verified: bool = False

class CoffeePrice(BaseModel):
    """Model for coffee prices at different sizes."""

    coffee_id: Optional[str] = None
    size_grams: int
    price: float

class ExternalLink(BaseModel):
    """Model for external marketplace links."""

    id: Optional[str] = None
    coffee_id: Optional[str] = None
    provider: str
    url: HttpUrl

class Coffee(BaseDBModel):
    """Model for coffee products."""

    name: str
    slug: str
    roaster_id: str
    description: Optional[str] = None
    roast_level: Optional[str] = None  # RoastLevel enum
    bean_type: Optional[str] = None  # BeanType enum
    processing_method: Optional[str] = None  # ProcessingMethod enum
    region_id: Optional[str] = None
    region_name: Optional[str] = None  # For use with upsert_region function
    image_url: Optional[HttpUrl] = None
    direct_buy_url: HttpUrl
    is_seasonal: Optional[bool] = None
    is_single_origin: Optional[bool] = None
    is_available: bool = True
    is_featured: bool = False
    tags: Optional[List[str]] = None
    deepseek_enriched: bool = False
    price_250g: Optional[float] = None
    acidity: Optional[str] = None
    body: Optional[str] = None
    sweetness: Optional[str] = None
    aroma: Optional[str] = None
    with_milk_suitable: Optional[bool] = None
    varietals: Optional[List[str]] = None
    altitude_meters: Optional[int] = None

    # Related data (not stored directly in the table)
    prices: Optional[List[CoffeePrice]] = None
    brew_methods: Optional[List[str]] = None
    flavor_profiles: Optional[List[str]] = None
    external_links: Optional[List[ExternalLink]] = None

class CoffeeBrewMethod(BaseModel):
    """Model for the relationship between coffee and brew methods."""

    coffee_id: Optional[str] = None
    brew_method_id: Optional[str] = None

class CoffeeFlavorProfile(BaseModel):
    """Model for the relationship between coffee and flavor profiles."""

    coffee_id: Optional[str] = None
    flavor_profile_id: str

class BrewMethod(BaseDBModel):
    """Model for brew method lookup table."""

    name: str

class FlavorProfile(BaseDBModel):
    """Model for flavor profile lookup table."""

    name: str

class ScrapingState(BaseModel):
    """Model for tracking scraping state."""

    url: str
    last_scraped: datetime
    status: str  # "success", "error", "pending"
    field_timestamps: Dict[str, datetime]  # Track when each field was last updated
    field_confidence: Dict[str, int]  # Confidence score for each field (1-10)
    error_message: Optional[str] = None
