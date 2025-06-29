"""
Supabase client for interacting with the database.
Includes integration with existing Supabase functions.
"""

import logging
from typing import Any, Dict, List, Optional, Set, Type, TypeVar, Union

from pydantic import BaseModel
from supabase import create_client

from common.pydantic_utils import model_to_dict
from config import config
from db.models import Coffee, CoffeePrice, ExternalLink, Roaster

# Set up logging
logger = logging.getLogger(__name__)

# Type variable for generic database functions
T = TypeVar("T", bound=BaseModel)


class SupabaseClient:
    def __init__(self):
        """Initialize the Supabase client."""
        if not config.supabase.url or not config.supabase.url.startswith("https://"):
            raise ValueError(f"Invalid Supabase URL: '{config.supabase.url}'. Must start with https://")
        if not config.supabase.key or len(config.supabase.key) < 10:
            raise ValueError("Invalid Supabase API key")

        self.client = create_client(config.supabase.url, config.supabase.key)
        self._test_connection()

    def _test_connection(self) -> bool:
        """Test the connection to Supabase."""
        try:
            # Simple query to test connection
            self.client.table("roasters").select("id").limit(1).execute()
            logger.info("Successfully connected to Supabase.")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            raise ConnectionError(f"Could not connect to Supabase: {e}")

    # Generic CRUD operations

    def _get_table_name(self, model_class: Type[BaseModel]) -> str:
        """Get the table name for a model class."""
        table_map = {
            Coffee: "coffees",
            Roaster: "roasters",
            CoffeePrice: "coffee_prices",
            ExternalLink: "external_links",
        }

        if model_class not in table_map:
            raise ValueError(f"Unknown model class: {model_class}")

        return table_map[model_class]

    def create(self, model: BaseModel, table_name: Optional[str] = None) -> Dict[str, Any]:
        """Create a new record in the database."""
        if not table_name:
            table_name = self._get_table_name(model.__class__)

        data = model.model_dump(exclude_none=True, exclude={"id", "created_at", "updated_at"})

        try:
            result = self.client.table(table_name).insert(data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Error creating {table_name} record: {e}")
            raise

    def update(self, model: BaseModel, table_name: Optional[str] = None) -> Dict[str, Any]:
        """Update an existing record in the database."""
        model_id = getattr(model, "id", None)
        if not model_id:
            raise ValueError("Cannot update a model without an ID")

        if not table_name:
            table_name = self._get_table_name(model.__class__)

        data = model.model_dump(exclude_none=True, exclude={"created_at", "updated_at"})

        try:
            result = self.client.table(table_name).update(data).eq("id", model_id).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Error updating {table_name} record: {e}")
            raise

    def get_by_id(self, model_class: Type[T], id: str, table_name: Optional[str] = None) -> Optional[T]:
        """Get a record by ID."""
        if not table_name:
            table_name = self._get_table_name(model_class)

        try:
            result = self.client.table(table_name).select("*").eq("id", id).execute()
            return model_class(**result.data[0]) if result.data else None
        except Exception as e:
            logger.error(f"Error getting {table_name} record by ID: {e}")
            raise

    def get_by_field(self, model_class: Type[T], field: str, value: Any, table_name: Optional[str] = None) -> List[T]:
        """Get records by a field value."""
        if not table_name:
            table_name = self._get_table_name(model_class)

        try:
            result = self.client.table(table_name).select("*").eq(field, value).execute()
            return [model_class(**item) for item in result.data]
        except Exception as e:
            logger.error(f"Error getting {table_name} records by field: {e}")
            raise

    def list_all(self, model_class: Type[T], table_name: Optional[str] = None, limit: int = 1000) -> List[T]:
        """List all records of a model type."""
        if not table_name:
            table_name = self._get_table_name(model_class)

        try:
            result = self.client.table(table_name).select("*").limit(limit).execute()
            return [model_class(**item) for item in result.data]
        except Exception as e:
            logger.error(f"Error listing {table_name} records: {e}")
            raise

    def delete(self, model_class: Type[BaseModel], id: str, table_name: Optional[str] = None) -> bool:
        """Delete a record by ID."""
        if not table_name:
            table_name = self._get_table_name(model_class)

        try:
            result = self.client.table(table_name).delete().eq("id", id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error deleting {table_name} record: {e}")
            raise

    def get_coffees_by_roaster(self, roaster_id: str) -> List[Coffee]:
        """Get all coffees for a roaster."""
        try:
            result = self.client.table("coffees").select("*").eq("roaster_id", roaster_id).execute()
            return [Coffee(**item) for item in result.data]
        except Exception as e:
            logger.error(f"Error getting coffees for roaster: {e}")
            raise

    def get_roaster_by_website(self, website_url: str) -> Optional[Roaster]:
        """Get a roaster by website URL."""
        try:
            # Normalize URL by removing protocol and trailing slash
            normalized_url = website_url.lower()
            normalized_url = normalized_url.replace("http://", "").replace("https://", "")
            normalized_url = normalized_url.rstrip("/")

            # Try to find an exact match first
            result = self.client.table("roasters").select("*").ilike("website_url", f"%{normalized_url}%").execute()

            if result.data:
                return Roaster(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error getting roaster by website: {e}")
            raise

    # SmartUpsert functionality (moved from smart_upsert.py)
    def upsert_model(
        self, model: T, table_name: str, primary_key: str = "id", protected_fields: Optional[List[str]] = None
    ) -> Optional[T]:
        """
        Upsert a model to Supabase, preserving manually entered data.

        Args:
            model: The model to upsert
            table_name: The Supabase table name
            primary_key: The primary key field name (default: 'id')
            protected_fields: List of fields that should never be updated

        Returns:
            The updated model, or None if operation failed
        """
        # Default protected fields to empty list
        protected_fields = protected_fields or []

        # System fields that should never be updated by scraper
        system_fields = {"created_at", "updated_at", "is_verified"}

        # Add system fields to protected fields
        all_protected = set(protected_fields) | system_fields

        # Get primary key value
        pk_value = getattr(model, primary_key, None)

        # Handle insert vs update logic
        if not pk_value:
            # This is a new record - insert it
            return self._insert_model(model, table_name)
        else:
            # This is an update - get existing record first
            try:
                existing_data = self.client.table(table_name).select("*").eq(primary_key, pk_value).execute()

                if not existing_data.data or len(existing_data.data) == 0:
                    # Record doesn't exist despite having an ID - treat as insert
                    logger.warning(f"Record with {primary_key}={pk_value} not found, inserting as new")
                    return self._insert_model(model, table_name)

                # Get existing record
                existing_record = existing_data.data[0]

                # Convert model to dict, excluding None values
                new_data = model_to_dict(model)

                # Merge data carefully
                update_data = self._merge_record_data(existing_record, new_data, all_protected)

                # Only perform update if there are actual changes
                if update_data:
                    logger.info(
                        f"Updating {table_name} ({primary_key}={pk_value}) with fields: {', '.join(update_data.keys())}"
                    )
                    result = self.client.table(table_name).update(update_data).eq(primary_key, pk_value).execute()

                    if result.data and len(result.data) > 0:
                        # Return the model class with updated data
                        return self._dict_to_model(result.data[0], model.__class__)
                    else:
                        logger.error(f"Update failed for {table_name} ({primary_key}={pk_value})")
                        return None
                else:
                    logger.info(f"No changes detected for {table_name} ({primary_key}={pk_value}), skipping update")
                    return self._dict_to_model(existing_record, model.__class__)

            except Exception as e:
                logger.error(f"Error selectively updating {table_name}: {e}")
                raise

    def _insert_model(self, model: T, table_name: str) -> Optional[T]:
        """Insert a new model."""
        try:
            data = model_to_dict(model)

            # Remove id if it's None (let Supabase generate it)
            if "id" in data and data["id"] is None:
                del data["id"]

            logger.info(f"Inserting new record into {table_name}")
            result = self.client.table(table_name).insert(data).execute()

            if result.data and len(result.data) > 0:
                return self._dict_to_model(result.data[0], model.__class__)
            else:
                logger.error(f"Insert failed for {table_name}")
                return None
        except Exception as e:
            logger.error(f"Error inserting model: {e}")
            raise

    @staticmethod
    def _merge_record_data(existing: Dict[str, Any], new: Dict[str, Any], protected_fields: Set[str]) -> Dict[str, Any]:
        """
        Carefully merge existing and new record data.

        Rules:
        1. Never replace existing non-NULL with NULL
        2. Don't update protected fields
        3. Only include fields that actually changed

        Returns a dict with only the fields that need updating.
        """
        update_data = {}

        for key, new_value in new.items():
            # Skip protected fields
            if key in protected_fields:
                continue

            # Skip if field doesn't exist in existing record
            if key not in existing:
                # This is a new field
                update_data[key] = new_value
                continue

            existing_value = existing[key]

            # Skip if trying to overwrite non-NULL with NULL
            if new_value is None and existing_value is not None:
                continue

            # Skip if value is unchanged
            if existing_value == new_value:
                continue

            # Add field to the update
            update_data[key] = new_value

        return update_data

    @staticmethod
    def _dict_to_model(data: Dict[str, Any], model_class: Type[T]) -> T:
        """Convert a dictionary to a model instance."""
        return model_class(**data)

    # Example usage functions - keeping the same interface

    def upsert_roaster(self, roaster: Roaster) -> Optional[Roaster]:
        """Upsert a roaster with smart field preservation."""
        # Fields that should never be auto-updated by scraper
        protected_fields = ["is_verified"]

        # Fields that can be auto-updated
        return self.upsert_model(roaster, table_name="roasters", protected_fields=protected_fields)

    def upsert_coffee(self, coffee: Union[Coffee, Dict[str, Any]]) -> Optional[Coffee]:
        """Upsert a coffee with smart field preservation and related data."""

        # Convert dict to Coffee object if needed
        if isinstance(coffee, dict):
            try:
                coffee = Coffee(**coffee)
            except Exception as e:
                logger.error(f"Error converting coffee dict to Coffee object: {e}")
                return None

        # Handle region first if provided as a name instead of ID
        if coffee.region_name and not coffee.region_id:
            try:
                result = self.client.rpc("upsert_region", {"region_name": coffee.region_name}).execute()
                if result.data:
                    coffee.region_id = result.data[0]
            except Exception as e:
                logger.warning(f"Error upserting region: {e}")

        # Smart upsert for the coffee record
        updated_coffee = self.upsert_model(
            coffee,
            table_name="coffees",
            protected_fields=["is_featured"],  # Protect manually featured coffees
        )

        if not updated_coffee or not updated_coffee.id:
            logger.error("Coffee upsert failed")
            return None

        coffee_id = updated_coffee.id

        # Handle prices if provided
        if coffee.prices:
            try:
                # First delete existing prices for this coffee - prices are fully managed by scraper
                self.client.table("coffee_prices").delete().eq("coffee_id", coffee_id).execute()

                # Insert new prices
                for price in coffee.prices:
                    price_data = model_to_dict(price)
                    price_data["coffee_id"] = coffee_id
                    self.client.table("coffee_prices").insert(price_data).execute()
            except Exception as e:
                logger.warning(f"Error managing coffee prices: {e}")

        # Handle brew methods if provided
        if coffee.brew_methods:
            # Use the existing Supabase function to upsert brew methods
            for method in coffee.brew_methods:
                try:
                    self.client.rpc(
                        "upsert_brew_method_and_link", {"coffee": coffee_id, "method_name": method}
                    ).execute()
                except Exception as e:
                    logger.warning(f"Error upserting brew method: {e}")

        # Handle flavor profiles if provided
        if coffee.flavor_profiles:
            # Use the existing Supabase function to upsert flavor profiles
            for flavor in coffee.flavor_profiles:
                try:
                    self.client.rpc("upsert_flavor_and_link", {"coffee": coffee_id, "flavor_name": flavor}).execute()
                except Exception as e:
                    logger.warning(f"Error upserting flavor profile: {e}")

        # Handle external links if provided
        if coffee.external_links:
            # Use the existing Supabase function to upsert external links
            for link in coffee.external_links:
                try:
                    self.client.rpc(
                        "upsert_external_link", {"coffee": coffee_id, "provider": link.provider, "link": str(link.url)}
                    ).execute()
                except Exception as e:
                    logger.warning(f"Error upserting external link: {e}")

        # Return the fully updated coffee with ID
        try:
            result = self.client.table("coffees").select("*").eq("id", coffee_id).execute()
            if result.data and len(result.data) > 0:
                return Coffee(**result.data[0])
            return updated_coffee
        except Exception as e:
            logger.warning(f"Error fetching updated coffee: {e}")
            return updated_coffee


# Initialize a singleton instance for importing in other modules
supabase = SupabaseClient()
