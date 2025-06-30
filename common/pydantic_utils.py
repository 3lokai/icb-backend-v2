"""
Utility for safely converting dicts to Pydantic models (e.g., Roaster, Coffee) with validation.
Usage:
    from db.models import Roaster, Coffee
    from common.pydantic_utils import dict_to_pydantic_model

    roaster = dict_to_pydantic_model(data_dict, Roaster)
    coffee = dict_to_pydantic_model(data_dict, Coffee)
"""

import logging
from collections.abc import Mapping
from datetime import datetime
from inspect import isclass
from typing import Any, Callable, Dict, Optional, Set, Type, TypeVar

from pydantic import BaseModel, HttpUrl, ValidationError

from common.utils import (
    clean_description,
    normalize_phone_number,
    slugify,
    standardize_bean_type,
    standardize_processing_method,
    standardize_roast_level,
)


def model_to_dict(
    model: BaseModel,
    exclude_none: bool = True,
    exclude_defaults: bool = False,
    exclude_unset: bool = False,
    exclude: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """
    Convert a Pydantic model to a database-friendly dictionary.
    Args:
        model: The Pydantic model to convert
        exclude_none: Whether to exclude None values
        exclude_defaults: Whether to exclude fields with default values
        exclude_unset: Whether to exclude fields that were not explicitly set
        exclude: A set of field names to exclude
    Returns:
        A dictionary suitable for database operations
    """
    model_dict = model.model_dump(
        exclude_none=exclude_none,
        exclude_defaults=exclude_defaults,
        exclude_unset=exclude_unset,
        exclude=exclude or set(),
    )
    return _process_dict_for_db(model_dict)


def _process_dict_for_db(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process a dictionary to make it suitable for database operations."""
    result = {}
    for key, value in data.items():
        if isinstance(value, HttpUrl):
            result[key] = str(value)
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, dict):
            result[key] = _process_dict_for_db(value)
        elif isinstance(value, list):
            result[key] = [
                _process_dict_for_db(item)
                if isinstance(item, dict)
                else str(item)
                if isinstance(item, HttpUrl)
                else item.isoformat()
                if isinstance(item, datetime)
                else item
                for item in value
            ]
        else:
            result[key] = value
    return result


T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


def _filter_and_coerce_fields(
    data: Dict[str, Any], model_class: Type[BaseModel], field_map: Optional[dict] = None
) -> dict:
    """
    Filter and coerce fields in data to match model_class, with optional field name mapping.
    """
    if field_map is None:
        field_map = {}
    model_fields = set(model_class.model_fields.keys())
    result = {}
    for k, v in data.items():
        # Map field names if needed
        field_name = field_map.get(k, k)
        if field_name not in model_fields:
            continue
        # Trim whitespace for strings
        if isinstance(v, str):
            v = v.strip()
        # Convert 'true'/'false' strings to bool
        if isinstance(v, str) and v.lower() in ("true", "false"):
            v = v.lower() == "true"
        # Convert numbers in string form
        if isinstance(v, str) and v.replace(".", "", 1).isdigit():
            if "." in v:
                try:
                    v = float(v)
                except Exception:
                    pass
            else:
                try:
                    v = int(v)
                except Exception:
                    pass
        # Recursively handle nested models/lists
        if isinstance(v, list):
            subfield = model_class.model_fields[field_name]
            annotation = getattr(subfield, "annotation", None)
            if annotation is not None and hasattr(annotation, "__origin__") and annotation.__origin__ is list:
                submodel = annotation.__args__[0]
                if isclass(submodel) and issubclass(submodel, BaseModel):
                    v = [
                        _filter_and_coerce_fields(dict(item), submodel) if isinstance(item, Mapping) else item
                        for item in v
                    ]
        elif isinstance(v, dict):
            subfield = model_class.model_fields[field_name]
            submodel = getattr(subfield.annotation, "__args__", [None])[0] or subfield.annotation
            if isclass(submodel) and issubclass(submodel, BaseModel):
                v = _filter_and_coerce_fields(v, submodel)
        result[field_name] = v
    return result


def dict_to_pydantic_model(
    data: Dict[str, Any],
    model_class: Type[T],
    field_map: Optional[dict] = None,
    preprocessor: Optional[Callable[[dict], dict]] = None,
) -> Optional[T]:
    """
    Convert a dict to a Pydantic model instance, with preprocessing and type coercion.
    - field_map: dict for renaming fields (e.g., {'about_url': 'aboutUrl'})
    - preprocessor: function to further clean data before model instantiation
    """
    try:
        clean_data = _filter_and_coerce_fields(data, model_class, field_map)
        if preprocessor:
            clean_data = preprocessor(clean_data)
        return model_class(**clean_data)
    except ValidationError as e:
        logger.error(f"Validation error for {model_class.__name__}: {e}")
        return None


def preprocess_roaster_data(data: dict) -> dict:
    # Normalize phone fields
    for phone_field in ["contact_phone", "phone", "mobile"]:
        if phone_field in data and data[phone_field]:
            data[phone_field] = normalize_phone_number(data[phone_field])
    # Clean description
    if "description" in data and data["description"]:
        data["description"] = clean_description(data["description"])
    # Create slug
    if "name" in data and data["name"]:
        data["slug"] = slugify(data["name"])
    # Lowercase domain
    if "domain" in data and data["domain"]:
        data["domain"] = data["domain"].lower()
    return data


def preprocess_coffee_data(data: dict) -> dict:
    # Standardize roast level
    if "roast_level" in data and data["roast_level"]:
        data["roast_level"] = standardize_roast_level(data["roast_level"])
    # Standardize processing method
    if "processing_method" in data and data["processing_method"]:
        data["processing_method"] = standardize_processing_method(data["processing_method"])
    # Standardize bean type
    if "bean_type" in data and data["bean_type"]:
        data["bean_type"] = standardize_bean_type(data["bean_type"])
    # Clean description
    if "description" in data and data["description"]:
        data["description"] = clean_description(data["description"])
    # Create slug
    if "name" in data and data["name"]:
        data["slug"] = slugify(data["name"])
    return data
