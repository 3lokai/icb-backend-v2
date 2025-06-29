"""
Caching module for the Coffee Scraper.
Provides functions for caching and retrieving scraped data.

Cache invalidation respects field stability categories as defined in the PRD:
- "stable": fields rarely change, cache can be long-lived
- "semi-stable": fields change occasionally, cache should be refreshed more often
- "volatile": fields change frequently, cache should be short-lived

Note: File-based cache is not fully thread/process safe for concurrent writes. For high concurrency, use file locks or a dedicated cache backend.
"""

import hashlib
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from loguru import logger
from pydantic import AnyUrl, HttpUrl

from config import CACHE_DIR
from db.models import Coffee


class ScraperCache:
    """Cache manager for scraper data."""

    def __init__(self, cache_dir=None):
        """Initialize the cache manager."""
        self.cache_dir = Path(cache_dir or CACHE_DIR)
        self.roaster_cache_dir = self.cache_dir / "roasters"
        self.product_cache_dir = self.cache_dir / "products"
        self.page_cache_dir = self.cache_dir / "pages"

        # Create cache directories
        self.roaster_cache_dir.mkdir(exist_ok=True, parents=True)
        self.product_cache_dir.mkdir(exist_ok=True, parents=True)
        self.page_cache_dir.mkdir(exist_ok=True, parents=True)

    def _get_cache_key(self, url: str) -> str:
        """Generate a unique cache key for a URL."""
        # Normalize URL for consistent hashing
        url = url.lower().strip()
        url = re.sub(r"https?://(www\.)?", "", url)
        url = re.sub(r"/+$", "", url)  # Remove trailing slashes

        return hashlib.md5(url.encode()).hexdigest()

    def _get_roaster_cache_key(self, name: str, url: str) -> str:
        """Generate a unique cache key for a roaster."""
        return hashlib.md5(f"{name}_{url}".encode()).hexdigest()

    def get_cached_html(self, url: str, max_age_days: int = 7, field_stability: Optional[str] = None) -> Optional[str]:
        """
        Get cached HTML for a URL if it exists and is fresh.
        Optionally, adjust cache TTL based on field stability category (stable, semi-stable, volatile).
        """
        cache_key = self._get_cache_key(url)
        cache_file = self.page_cache_dir / f"{cache_key}.html"

        if not cache_file.exists():
            return None

        # Adjust TTL based on field stability
        if field_stability:
            max_age_days = self._ttl_for_stability(field_stability, max_age_days)
        # Check if cache is older than specified age
        file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        if file_age > timedelta(days=max_age_days):
            logger.debug(f"Cache for {url} is {file_age.days} days old, exceeding max age of {max_age_days} days")
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Error reading HTML cache for {url}: {e}")
            return None

    def cache_html(self, url: str, html_content: str) -> bool:
        """Cache HTML content for a URL."""
        if not html_content:
            return False

        cache_key = self._get_cache_key(url)
        cache_file = self.page_cache_dir / f"{cache_key}.html"

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            return True
        except Exception as e:
            logger.warning(f"Error writing HTML cache for {url}: {e}")
            return False

    def get_cached_roaster(
        self, name: str, url: str, max_age_days: int = 30, field_stability: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached roaster if it exists and is fresh.
        Optionally, adjust cache TTL based on field stability category.
        """
        cache_key = self._get_roaster_cache_key(name, url)
        cache_file = self.roaster_cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        # Adjust TTL based on field stability
        if field_stability:
            max_age_days = self._ttl_for_stability(field_stability, max_age_days)
        # Check if cache is older than specified age
        file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        if file_age > timedelta(days=max_age_days):
            logger.debug(f"Cache for roaster {name} is {file_age.days} old, exceeding max age of {max_age_days} days")
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error reading roaster cache for {name}: {e}")
            return None

    def cache_roaster(self, roaster: Dict[str, Any]) -> bool:
        """Cache roaster data."""
        if not roaster or "name" not in roaster or "website_url" not in roaster:
            return False

        cache_key = self._get_roaster_cache_key(roaster["name"], roaster["website_url"])
        cache_file = self.roaster_cache_dir / f"{cache_key}.json"

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(roaster, f, indent=2)
            return True
        except Exception as e:
            logger.warning(f"Error writing roaster cache for {roaster['name']}: {e}")
            return False

    def get_cached_products(
        self, roaster_id: str, max_age_days: int = 7, field_stability: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached products for a roaster if they exist and are fresh.
        Optionally, adjust cache TTL based on field stability category.
        """
        cache_file = self.product_cache_dir / f"{roaster_id}.json"

        if not cache_file.exists():
            return None

        # Adjust TTL based on field stability
        if field_stability:
            max_age_days = self._ttl_for_stability(field_stability, max_age_days)
        # Check if cache is older than specified age
        file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        if file_age > timedelta(days=max_age_days):
            logger.debug(
                f"Cache for roaster products {roaster_id} is {file_age.days} days old, exceeding max age of {max_age_days} days"
            )
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error reading products cache for roaster {roaster_id}: {e}")
            return None

    def _convert_to_serializable(self, obj):
        """Recursively convert objects to serializable types."""
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, (HttpUrl, AnyUrl)) or hasattr(obj, "url"):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: self._convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple, set)):
            return [self._convert_to_serializable(item) for item in obj]
        elif hasattr(obj, "model_dump"):  # Pydantic v2
            return self._convert_to_serializable(obj.model_dump())
        elif hasattr(obj, "dict"):  # Pydantic v1
            return self._convert_to_serializable(obj.dict())
        elif hasattr(obj, "__dict__"):  # Other objects with __dict__
            return self._convert_to_serializable(obj.__dict__)
        else:
            # Try to convert to string as a last resort
            try:
                return str(obj)
            except Exception:
                logger.warning(f"Could not serialize object of type {type(obj)}: {obj}")
                return None

    def _ttl_for_stability(self, field_stability: str, default_ttl: int) -> int:
        """
        Return TTL (in days) for a field based on its stability category.
        """
        stability_map = {
            "stable": 30,  # e.g. months/years
            "semi-stable": 7,  # e.g. weekly refresh
            "volatile": 1,  # e.g. daily refresh
        }
        return stability_map.get(field_stability.lower(), default_ttl)

    def cache_products(self, roaster_id: str, products: List[Union[Dict[str, Any], "Coffee"]]) -> bool:
        """Cache products for a roaster.

        Args:
            roaster_id: The ID of the roaster
            products: List of product dictionaries or Coffee model instances

        Returns:
            bool: True if caching was successful, False otherwise
        """
        if not roaster_id or not products:
            return False

        cache_file = self.product_cache_dir / f"{roaster_id}.json"

        try:
            # Convert products to serializable format
            serializable_products = [self._convert_to_serializable(product) for product in products]

            # Write to cache file
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(serializable_products, f, indent=2, ensure_ascii=False)
            return True

        except Exception as e:
            logger.warning(f"Error writing products cache for roaster {roaster_id}: {e}")
            return False

    def clear_cache(
        self, cache_type: Optional[str] = None, roaster_id: Optional[str] = None, url: Optional[str] = None
    ) -> int:
        files_removed = 0

        if cache_type == "html" or cache_type is None:
            if url:
                cache_key = self._get_cache_key(url)
                cache_file = self.page_cache_dir / f"{cache_key}.html"
                if cache_file.exists():
                    cache_file.unlink()
                    files_removed += 1
            else:
                for cache_file in self.page_cache_dir.glob("*.html"):
                    cache_file.unlink()
                    files_removed += 1

        if cache_type == "roaster" or cache_type is None:
            if roaster_id:
                cache_file = self.roaster_cache_dir / f"{roaster_id}.json"
                if cache_file.exists():
                    cache_file.unlink()
                    files_removed += 1
            else:
                for cache_file in self.roaster_cache_dir.glob("*.json"):
                    cache_file.unlink()
                    files_removed += 1

        if cache_type == "product" or cache_type is None:
            if roaster_id:
                cache_file = self.product_cache_dir / f"{roaster_id}.json"
                if cache_file.exists():
                    cache_file.unlink()
                    files_removed += 1
            else:
                for cache_file in self.product_cache_dir.glob("*.json"):
                    cache_file.unlink()
                    files_removed += 1

        return files_removed

# At the bottom of cache.py

# Create singleton instance
_cache = ScraperCache()

# Export ALL the cache functions your scrapers expect
def cache_products(roaster_id, products):
    return _cache.cache_products(roaster_id, products)

def get_cached_products(roaster_id, max_age_days=7):
    return _cache.get_cached_products(roaster_id, max_age_days)

def cache_html(url, content):
    return _cache.cache_html(url, content)

def get_cached_html(url, max_age_days=7, field_stability=None):
    return _cache.get_cached_html(url, max_age_days, field_stability)

def cache_roaster(roaster):
    return _cache.cache_roaster(roaster)

def get_cached_roaster(name, url, max_age_days=30, field_stability=None):
    return _cache.get_cached_roaster(name, url, max_age_days, field_stability)

def clear_cache(cache_type=None, roaster_id=None, url=None):
    return _cache.clear_cache(cache_type, roaster_id, url)

# Bonus: Export the instance itself if someone needs more control
cache = _cache