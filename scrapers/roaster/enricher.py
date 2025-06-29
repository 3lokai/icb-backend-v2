"""LLM enrichment for roaster data."""

import logging
from typing import Any, Dict

from common.enricher import enricher as enrichment_service

logger = logging.getLogger(__name__)

# Updated critical fields - replaced city and state with address
CRITICAL_FIELDS = ["description", "founded_year", "address"]


async def enrich_missing_fields(roaster_data: Dict[str, Any], extracted_html: str = None) -> Dict[str, Any]:
    """Enrich missing critical fields with LLM."""
    # Check which critical fields are missing
    missing_fields = [field for field in CRITICAL_FIELDS if not roaster_data.get(field)]

    if not missing_fields:
        return roaster_data

    logger.info(f"Enriching missing fields: {missing_fields}")

    try:
        # Only try enrichment if we have the minimum required data
        if roaster_data.get("name"):
            # Call the enrichment service - this now directly updates roaster_data
            roaster_data = await enrichment_service.enhance_roaster_description(roaster_data)
            logger.info(f"Enriched roaster data: {roaster_data}")

            # Log which fields were enriched
            for field in CRITICAL_FIELDS:
                if field in roaster_data and field in missing_fields:
                    value = roaster_data[field]
                    if value:
                        logger.info(
                            f"Enriched {field} with: {str(value)[:100]}..."
                            if isinstance(value, str) and len(value) > 100
                            else f"Enriched {field} with: {value}"
                        )
        else:
            logger.warning("Cannot enhance data: Missing roaster name")

    except Exception as e:
        logger.error(f"Error during enrichment: {e}")

    return roaster_data
