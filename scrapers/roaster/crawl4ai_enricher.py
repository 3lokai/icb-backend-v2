"""
Crawl4AI-based enrichment for roaster data using DeepSeek LLM.
Crawls home, about, and contact pages to fill missing fields.
"""

import json
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

from config import config

try:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
    from crawl4ai import LLMConfig as Crawl4AILLMConfig
    from crawl4ai.extraction_strategy import LLMExtractionStrategy
    from pydantic import BaseModel, Field
except ImportError:
    AsyncWebCrawler = None
    CrawlerRunConfig = None
    Crawl4AILLMConfig = None
    LLMExtractionStrategy = None
    BaseModel = object


def Field(*a, **k):
    return None


class RoasterEnrichmentData(BaseModel):
    description: Optional[str] = Field(None, description="About the company or roaster")
    founded_year: Optional[int] = Field(None, description="Year the company was established")
    has_subscription: Optional[bool] = Field(None, description="Whether they offer a subscription service")
    has_physical_store: Optional[bool] = Field(None, description="Whether they have a physical retail location")
    social_links: Optional[List[str]] = Field(None, description="Social media profile URLs")


async def fetch_html(url: str) -> Optional[str]:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, follow_redirects=True)
            if resp.status_code == 200:
                return resp.text
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
    return None


def find_about_contact_links(soup) -> Dict[str, str]:
    """Find about/contact page links from a BeautifulSoup object."""
    links = {}
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        if "about" in href and "contact" not in href:
            links["about"] = a["href"]
        elif "contact" in href:
            links["contact"] = a["href"]
    return links


async def get_roaster_pages(url: str) -> Dict[str, str]:
    """Return HTML for home, about, and contact pages if available."""
    from bs4 import BeautifulSoup

    pages = {"home": None, "about": None, "contact": None}
    home_html = await fetch_html(url)
    pages["home"] = home_html
    if home_html:
        soup = BeautifulSoup(home_html, "html.parser")
        links = find_about_contact_links(soup)
        base = url.rstrip("/")
        if "about" in links:
            about_url = links["about"]
            if about_url.startswith("/"):
                about_url = base + about_url
            elif not about_url.startswith("http"):
                about_url = base + "/" + about_url
            pages["about"] = await fetch_html(about_url)
        if "contact" in links:
            contact_url = links["contact"]
            if contact_url.startswith("/"):
                contact_url = base + contact_url
            elif not contact_url.startswith("http"):
                contact_url = base + "/" + contact_url
            pages["contact"] = await fetch_html(contact_url)
    return pages


async def enrich_roaster_data_with_crawl4ai(roaster_data: Dict[str, Any], url: str) -> Dict[str, Any]:
    """Use Crawl4AI+DeepSeek to fill in missing roaster data fields from home, about, and contact pages."""
    if AsyncWebCrawler is None or Crawl4AILLMConfig is None or LLMExtractionStrategy is None:
        # Crawl4AI not installed, skip
        return roaster_data

    fields_to_enrich = ["description", "founded_year", "has_subscription", "has_physical_store", "social_links"]
    missing_fields = [f for f in fields_to_enrich if not roaster_data.get(f)]
    if not missing_fields:
        return roaster_data

    # Aggregate HTML from all relevant pages
    pages = await get_roaster_pages(url)
    html_input = "\n\n".join([p for p in pages.values() if p])
    if not html_input:
        return roaster_data

    llm_strategy = LLMExtractionStrategy(
        llm_config=Crawl4AILLMConfig(provider="deepseek", api_token=config.llm.deepseek_api_key),
        schema=RoasterEnrichmentData.model_json_schema(),
        extraction_type="schema",
        instruction=f"Extract the following missing information about this coffee roaster: {', '.join(missing_fields)}. Only return information you're confident about.",
        input_format="html",
        chunk_token_threshold=4000,
        apply_chunking=True,
    )
    config_obj = CrawlerRunConfig(extraction_strategy=llm_strategy, cache_mode="ENABLED")
    try:
        async with AsyncWebCrawler() as crawler:
            async for result in crawler.arun(html=html_input, url=url, config=config_obj):
                if getattr(result, "success", False) and getattr(result, "extracted_content", None):
                    try:
                        enriched_data = json.loads(result.extracted_content)
                        for field in missing_fields:
                            val = enriched_data.get(field)
                            if val is not None and val != "":
                                roaster_data[field] = val
                    except Exception as e:
                        logger.error(f"Crawl4AI enrichment JSON parse error: {e}")
                break  # Exit after first result
    except Exception as e:
        logger.error(f"Crawl4AI enrichment failed: {e}")
    return roaster_data
