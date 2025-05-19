# Roaster Data Extraction with Crawl4AI

This module implements modular, schema-driven extraction of coffee roaster information from websites, leveraging Crawl4AI and LLM enrichment.

## Code Reuse & Extension Points

- **Schemas:** Extraction schemas for contact, about, and address info are defined in `schemas.py` and reused across all extraction methods.
- **Platform Detection:** Platform-specific page discovery is handled by `get_platform_page_paths` in `platform_pages.py`.
- **Extraction Logic:** All field extraction is performed by the `RoasterCrawler` class in `crawler.py`, which delegates to specialized async methods for contact, about, location, and tag extraction. These methods reuse schemas and utilities rather than duplicating extraction logic.
- **Fallbacks:** If a field is missing after initial extraction, `enrich_missing_fields` in `enricher.py` provides LLM-based enrichment as a fallback. This ensures completeness without duplicating logic.
- **Utility Functions:** Common helpers (e.g., slug creation, phone normalization) are imported from `common/utils.py` to avoid duplication. Always check this module before adding new helpers.

## How to Extend
- To add a new field, update the relevant schema in `schemas.py` and extend the corresponding extraction method in `crawler.py`.
- For new platform-specific page patterns, update `platform_pages.py`.
- For additional enrichment logic, extend `enricher.py`.

## Test Coverage
- Enrichment logic is tested in `tests/test_roasters_crawl4ai_enricher.py`.
- If you add new extractor methods or schemas, add or update tests in the `tests/` directory.

## Notes
- All extraction is async and modular for easy extension and batch processing.
- Platform detection uses `PlatformDetector` from `common/platform_detector.py`.
- Fallbacks and enrichment are only triggered for missing critical fields.
- Sensitive configuration (API keys, etc.) must be managed via environment variables.

---

For questions or to contribute, see inline comments in each source file for further documentation on code reuse and extension points.
