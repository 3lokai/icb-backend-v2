# Coffee Product Schema for LLM Extraction
# =======================================
# File: scrapers/product_crawl4ai/enrichment/schema.py

from pydantic import BaseModel, Field
from typing import Optional, List, Union

class CoffeeProductSchema(BaseModel):
    """Schema for coffee product LLM extraction"""
    
    name: str = Field(
        description="The full name of the coffee product as shown on the product page"
    )
    
    description: Optional[str] = Field(
        None,
        description="A detailed description of the coffee, including any marketing text about its taste, origin, etc."
    )
    
    roast_level: Optional[str] = Field(
        None,
        description="The roast level of the coffee (e.g., light, medium, medium-dark, dark, espresso, city, full-city)"
    )
    
    bean_type: Optional[str] = Field(
        None,
        description="The type of coffee bean (e.g., arabica, robusta, liberica, blend, mixed-arabica)"
    )
    
    processing_method: Optional[str] = Field(
        None,
        description="The processing method used for the coffee beans (e.g., washed, natural, honey, pulped-natural, anaerobic)"
    )
    
    region_name: Optional[str] = Field(
        None,
        description="The geographical origin of the coffee - country, region, estate, or farm name"
    )
    
    is_single_origin: Optional[bool] = Field(
        None,
        description="Whether the coffee is single origin (true) or a blend of multiple origins (false)"
    )
    
    flavor_notes: Optional[Union[str, List[str]]] = Field(
        None,
        description="The flavor notes or tasting profile of the coffee (e.g., chocolate, fruity, nutty, caramel, floral)"
    )
    
    price: Optional[Union[float, str]] = Field(
        None,
        description="The price of the coffee (either a number or with currency symbol like $19.99, ₹450)"
    )
    
    size_grams: Optional[Union[int, str]] = Field(
        None,
        description="The package size in grams (e.g., 250g, 500g, 1kg). Convert kg to grams if needed."
    )
    
    image_url: Optional[str] = Field(
        None,
        description="Full URL of the main product image, including the domain name"
    )
    
    brew_methods: Optional[List[str]] = Field(
        None,
        description="Recommended brewing methods for this coffee (e.g., espresso, filter, french press, pour over)"
    )
    
    # altitude: Optional[str] = Field( # This field is replaced by altitude_meters
    #     None,
    #     description="The altitude at which the coffee was grown, if specified"
    # )
    
    harvest_period: Optional[str] = Field(
        None,
        description="When the coffee was harvested or the harvest season"
    )
    
    acidity: Optional[str] = Field(
        None, 
        description="The perceived acidity of the coffee (e.g., bright, mellow, sharp, low). Often described with fruit analogies like 'citrus acidity'."
    )
    
    body: Optional[str] = Field(
        None, 
        description="The body or mouthfeel of the coffee (e.g., light, medium, full, syrupy, tea-like)."
    )
    
    sweetness: Optional[str] = Field(
        None, 
        description="The perceived sweetness of the coffee (e.g., honey-like, caramel, brown sugar, low)."
    )
    
    aroma: Optional[Union[str, List[str]]] = Field(
        None, 
        description="The aroma or fragrance of the coffee (e.g., floral, nutty, spicy, chocolaty). Can be a list or a comma-separated string."
    )
    
    with_milk_suitable: Optional[bool] = Field(
        None, 
        description="Whether the coffee is particularly recommended for or suitable with milk (true or false)."
    )
    
    varietals: Optional[List[str]] = Field(
        None, 
        description="Specific coffee varietals used, if listed (e.g., Typica, Bourbon, Geisha, SL28, Caturra). Provide as a list of strings."
    )
    
    altitude_meters: Optional[Union[int, str]] = Field(
        None, 
        description="The altitude in meters at which the coffee was grown (e.g., 1500, '1200-1800masl'). Extract the numerical value or range if possible."
    )