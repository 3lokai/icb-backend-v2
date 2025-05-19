# coffee_scraper/common/enricher.py

"""
Enrichment service for the Coffee Scraper.
Uses LLM models to enhance both roaster and coffee product data.
"""

import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path

from openai import OpenAI
from bs4 import BeautifulSoup

from config import CACHE_DIR, config

# Set up logging
logger = logging.getLogger(__name__)

class EnrichmentService:
    """Service for enriching scraped data using LLMs."""
    
    def __init__(self, api_key=None, model=None):
        """Initialize the enrichment service."""
        self.api_key = api_key or config.llm.deepseek_api_key
        self.model = model or "deepseek-chat"
        self.base_url = "https://api.deepseek.com"
        self.enabled = bool(self.api_key)
        
        if not self.enabled:
            logger.warning("DeepSeek enrichment disabled: No API key provided")
    
    async def enhance_roaster_description(self, roaster_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance roaster data using DeepSeek LLM."""
        if not self.enabled or not roaster_data.get("name"):
            return roaster_data
            
        try:
            # Simple, direct prompt
            prompt = f"""You are a coffee expert. Based on the roaster name '{roaster_data['name']}' and any additional info, 
            provide the following information in JSON format:
            1. description: A concise 2-3 sentence description of this coffee roaster
            2. founded_year: The year this roaster was likely founded (best guess, integer only)
            3. address: A likely address for this roaster, if you can determine one
            
            Additional context:
            Website: {roaster_data.get('website_url', 'Unknown')}
            City/State: {roaster_data.get('city', 'Unknown')}, {roaster_data.get('state', 'Unknown')}
            Social: {roaster_data.get('social_links', [])}
            
            Return ONLY valid JSON with these fields. If you're uncertain about a field, just set it to null.
            """
            
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a coffee expert who provides precise, factual information."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            # Parse response and update data
            result = self._extract_json_from_response(response.choices[0].message.content)
            if result:
                for field in ["description", "founded_year", "address"]:
                    if field in result and result[field] and (field not in roaster_data or not roaster_data[field]):
                        roaster_data[field] = result[field]
                        logger.info(f"Enhanced {field} for {roaster_data['name']}")
            
            return roaster_data
                
        except Exception as e:
            logger.error(f"Error enhancing data for {roaster_data['name']}: {e}")
            return roaster_data
        
    def _extract_json_from_response(self, text):
        """Extract JSON from LLM response."""
        try:
            # Find JSON in the response
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = text[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            logger.error(f"Error parsing LLM JSON: {e}")
        return None
    
    async def enhance_product(self, product: Dict[str, Any], roaster_name: str = None) -> Dict[str, Any]:
        """Enhance coffee product attributes using DeepSeek."""
        if not self.enabled or not product.get("name"):
            return product
        
        try:
            # Collect context for the LLM
            combined_text = f"""
            Product Name: {product.get('name', 'Unknown')}
            Roaster: {roaster_name or product.get('roaster_name', 'Unknown')}
            Original Description: {product.get('description', '')}
            """
            
            # Add markdown content if available
            if product.get("source_markdown"):
                combined_text += f"\nProduct Page Content:\n{product['source_markdown']}"
            
            prompt = f"""
            Based on the coffee product information provided, extract the following attributes:
            
            1. roast_level: (exactly one of: light, light-medium, medium, medium-dark, dark, city, city-plus, full-city, french, italian, cinnamon, filter, espresso, omniroast or unknown if unclear)
            2. bean_type: (exactly one of: arabica, robusta, blend, liberica, mixed-arabica, arabica-robusta or unknown if unclear)
            3. processing_method: (one of: washed, natural, honey, anaerobic, pulped-natural, monsooned, wet-hulled, carbonic-maceration, double-fermented or unknown if unclear)
            4. region_name: (geographic origin of the coffee beans)
            5. flavor_profiles: (array of common flavor categories like: chocolate, fruity, nutty, caramel, berry, citrus, floral, spice)
            6. brew_methods: (array of recommended brewing methods like: espresso, filter, pour-over, french-press, aeropress, moka-pot, cold-brew, and so on)
            7. is_single_origin: (boolean true if it's called out or implied as a single origin coffee)
            8. is_seasonal: (boolean true if it's described as a seasonal or limited release)
            9. tags: (array of tags or keywords that describe the coffee)

            
            DO NOT infer or guess any values. If a field is not clearly stated in the text, return null for that field.
            Return ONLY a valid JSON object with these fields and nothing else.
            """
            
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a coffee expert who extracts structured attributes from product descriptions."},
                    {"role": "user", "content": combined_text + "\n\n" + prompt}
                ],
                max_tokens=800,
                temperature=0.1
            )
            
            ai_response = response.choices[0].message.content
            
            # Extract JSON from response
            try:
                # Find JSON in the response
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = ai_response[json_start:json_end]
                    attributes = json.loads(json_str)
                    
                    # Update product with extracted attributes (only if not already present)
                    for key, value in attributes.items():
                        if value is not None and (key not in product or not product[key]):
                            # Special handling for altitude values to ensure they're integers
                            if key in ['altitude_min', 'altitude_max'] and value:
                                try:
                                    product[key] = int(value)
                                except (ValueError, TypeError):
                                    pass
                            else:
                                product[key] = value
                                product[f"{key}_source"] = "llm"
            except Exception as e:
                logger.error(f"Error parsing LLM JSON for {product.get('name')}: {e}")
        
            return product
            
        except Exception as e:
            logger.error(f"Error enhancing product {product.get('name')} with LLM: {e}")
            return product
    
    async def batch_enrich_products(self, products: List[Dict[str, Any]], roaster_name: str = None, batch_size: int = 5) -> List[Dict[str, Any]]:
        """Process products in batches to avoid overwhelming resources."""
        results = []
        
        if not self.enabled:
            return products
            
        for i in range(0, len(products), batch_size):
            batch = products[i:i+batch_size]
            batch_results = await asyncio.gather(
                *[self.enhance_product(product, roaster_name) for product in batch]
            )
            results.extend(batch_results)
            logger.info(f"Processed batch {i//batch_size + 1}/{(len(products) + batch_size - 1)//batch_size}")
            await asyncio.sleep(1)  # Be nice to servers
            
        return results

    async def save_enrichment_logs(self, data_list: List[Dict[str, Any]], data_type: str) -> None:
        """Save logs of what was enriched for analysis."""
        if not data_list:
            return
            
        log_dir = Path(CACHE_DIR) / "logs"
        log_dir.mkdir(exist_ok=True, parents=True)
        
        log_file = log_dir / f"llm_enriched_{data_type}.json"
        
        # Track what fields were enriched with LLM
        enrichment_stats = {
            "total_items": len(data_list),
            "enriched_items": 0,
            "enriched_fields": {}
        }
        
        # Track which items had fields enriched
        enriched_items = []
        
        for item in data_list:
            item_enriched = False
            enriched_fields = {}
            
            for key, value in item.items():
                if key.endswith("_source") and value == "llm":
                    field_name = key.replace("_source", "")
                    enriched_fields[field_name] = item.get(field_name)
                    
                    # Update stats
                    if field_name not in enrichment_stats["enriched_fields"]:
                        enrichment_stats["enriched_fields"][field_name] = 0
                    enrichment_stats["enriched_fields"][field_name] += 1
                    
                    item_enriched = True
            
            if item_enriched:
                enrichment_stats["enriched_items"] += 1
                enriched_items.append({
                    "id": item.get("id") or item.get("name"),
                    "enriched_fields": enriched_fields
                })
        
        # Save the stats
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "stats": enrichment_stats,
                    "items": enriched_items
                }, f, indent=2)
                
            logger.info(f"Saved enrichment logs to {log_file}")
        except Exception as e:
            logger.error(f"Failed to save enrichment logs: {e}")

# Create singleton instance for convenience
enricher = EnrichmentService()
