# Coffee Scraper Project Rules and Guidelines

## Core Principles

1. **Modularity First**: Every distinct functionality should be isolated in separate functions for better testing, maintenance, and reuse.

2. **Data Quality Over Quantity**: Prioritize accurate data extraction over collection size. When in doubt, mark fields as unknown rather than making assumptions.

3. **Progressive Enhancement**: Extract definite data first, then progressively enhance with more speculative methods.

4. **Defensive Scraping**: Always assume websites might change structure. Implement multiple fallback methods for critical data.

5. **Respect Website Resources**: Implement rate limiting, caching, and polite scraping practices to avoid overloading target websites.

6. **Iterative Development**: Start with a simple implementation focusing on core functionality and refactor into more modular components as the project evolves.

## Technical Guidelines

### Code Structure

- **Single Responsibility Functions**: Each function should do one thing well (e.g., `extract_price_from_html()`, `extract_roast_level_from_text()`).

- **Clear Error Boundaries**: Use try/except blocks liberally with specific error types and meaningful error messages.

- **Type Hints**: Use Python type hints throughout the codebase for better IDE support and documentation.

- **Consistent Documentation**: Document all functions, classes, and modules with docstrings following a consistent format.

### Data Extraction

- **Multiple Extraction Methods**: For critical fields, implement at least two different extraction methods as fallbacks.

- **Validation Functions**: Create separate validators for all extracted data (e.g., `validate_price()`, `validate_roast_level()`).

- **Confidence Scores**: Where possible, assign confidence scores to extracted data to prioritize more reliable sources.

- **Metadata Preservation**: Store metadata about how each field was extracted for debugging and improvement.

### LLM Usage

- **Selective LLM Usage**: Use pattern matching and structured extraction first, then selectively use LLM for complex cases or gaps where the value justifies the cost.

- **Discrete LLM Functions**: Create separate LLM extraction functions for different groups of attributes (e.g., `extract_flavor_attributes_with_llm()`, `extract_origin_attributes_with_llm()`).

- **Prompt Consistency**: Maintain a library of tested prompts that produce reliable results.

- **LLM Validation**: Validate LLM outputs against known constraints and expected values.

- **Batched LLM Processing**: Group similar items for batch LLM processing to reduce API calls and improve consistency.

## Team Collaboration

- **Clear Module Ownership**: Assign clear ownership for each scraper and common module to ensure accountability and focused development.
- **Standardized Data Interfaces**: Define and adhere to standardized data structures and interfaces for sharing data between modules to minimize integration issues.

## Data Quality Guidelines

- **Standardized Vocabularies**: Maintain predefined lists for categorical fields (roast levels, processing methods, etc.).

- **Normalization Functions**: Implement functions to normalize common variations (e.g., "Medium-Light" and "Medium Light" to "medium-light").

- **Missing Data Tracking**: Record which fields required enrichment for analysis and improvement.

- **Confidence Thresholds**: Define minimum confidence thresholds for accepting extracted or enriched data.

## Technical Debt Prevention

- **Regular Refactoring**: Schedule regular refactoring sessions to prevent complexity build-up.

- **Comprehensive Integration Tests**: Create robust integration tests that verify the entire pipeline works correctly with a diverse set of sample websites, covering various platforms and edge cases.

- **Mandatory Regression Tests**: Build and maintain a comprehensive suite of regression tests based on previously successful extractions to prevent the reintroduction of bugs and ensure stability after changes.

- **Code Reviews**: Implement pull request reviews before merging new features.
