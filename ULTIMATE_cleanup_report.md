# Ultimate Coffee Scraper Code Quality Report

*From your humble 10-line script to this nuclear-powered analyzer!*

## Executive Summary

- **MyPy Issues**: 16 files with type issues
- **Ruff Issues**: 5 categories with problems
- **Coffee-Specific Issues**: 8 found

## Coffee Scraper Specific Issues (TOP PRIORITY)

### Common Folder Conflicts
- Potential conflicts in cache.py
- Potential conflicts in enricher.py
- Potential conflicts in exporter.py
- Potential conflicts in platform_detector.py
- Potential conflicts in pydantic_utils.py
- Potential conflicts in utils.py
- Potential conflicts in __init__.py

## MyPy Type Checking Results

### main.py
```
common\pydantic_utils.py:65: error: Incompatible types in assignment (expression has type "dict[str, Any]", target has type "str")  [assignment]
common\pydantic_utils.py:67: error: Incompatible types in assignment (expression has type "list[dict[str, Any] | str | Any]", target has type "str")  [assignment]
scrapers\product_crawl4ai\api_extractors\woocommerce.py:40: error: Need type annotation for "extracted_attrs" (hint: "extracted_attrs: dict[<type>, <type>] = ...")  [var-annotated]
scrapers\product_crawl4ai\api_extractors\woocommerce.py:186: error: Argument 1 to "append" of "list" has incompatible type "dict[str, Any]"; expected "Coffee"  [arg-type]
scrapers\product_crawl4ai\api_extractors\woocommerce.py:192: error: Incompatible return value type (got "list[Coffee]", expected "list[dict[str, Any]]")  [return-value]
scrapers\product_crawl4ai\api_extractors\woocommerce.py:632: error: Need type annotation for "metadata" (hint: "metadata: dict[<type>, <type>] = ...")  [var-annotated]
scrapers\product_crawl4ai\api_extractors\shopify.py:165: error: Argument 1 to "append" of "list" has incompatible type "dict[str, Any]"; expected "Coffee"  [arg-type]
scrapers\product_crawl4ai\api_extractors\shopify.py:171: error: Incompatible return value type (got "list[Coffee]", expected "list[dict[str, Any]]")  [return-value]
scrapers\product_crawl4ai\api_extractors\shopify.py:542: error: Need type annotation for "prices_by_size" (hint: "prices_by_size: dict[<type>, <type>] = ...")  [var-annotated]
scrapers\product_crawl4ai\scraper.py:183: error: Incompatible types in assignment (expression has type "dict[str, Any] | None", variable has type "dict[str, Any]")  [assignment]
scrapers\roasters_crawl4ai\crawler.py:184: error: Need type annotation for "results" (hint: "results: dict[<type>, <type>] = ...")  [var-annotated]
scrapers\roasters_crawl4ai\crawler.py:268: error: Need type annotation for "results" (hint: "results: dict[<type>, <type>] = ...")  [var-annotated]
scrapers\roasters_crawl4ai\batch.py:28: error: Need type annotation for "_calls" (hint: "_calls: list[<type>] = ...")  [var-annotated]
Found 13 errors in 6 files (checked 1 source file)

```

### config.py
```
Success: no issues found in 1 source file

```

### common/utils.py
```
Success: no issues found in 1 source file

```

### db/models.py
```
Success: no issues found in 1 source file

```

### run_product_scraper.py
```
scrapers\roaster\selectors.py:4: error: Incompatible default for argument "platform" (default has type "None", argument has type "str")  [assignment]
scrapers\roaster\selectors.py:4: note: PEP 484 prohibits implicit Optional. Accordingly, mypy has changed its default to no_implicit_optional=True
scrapers\roaster\selectors.py:4: note: Use https://github.com/hauntsaninja/no_implicit_optional to automatically upgrade your codebase
scrapers\product_crawl4ai\extractors\validators.py:386: error: Need type annotation for "results" (hint: "results: list[<type>] = ...")  [var-annotated]
scrapers\roaster\crawl4ai_enricher.py:24: error: Cannot assign to a type  [misc]
scrapers\roaster\crawl4ai_enricher.py:24: error: Incompatible types in assignment (expression has type "type[object]", variable has type "type[BaseModel]")  [assignment]
scrapers\roaster\crawl4ai_enricher.py:25: error: Incompatible types in assignment (expression has type "Callable[[VarArg(Any), KwArg(Any)], None]", variable has type overloaded function)  [assignment]
scrapers\roaster\crawl4ai_enricher.py:65: error: Incompatible types in assignment (expression has type "str | None", target has type "None")  [assignment]
scrapers\roaster\crawl4ai_enricher.py:76: error: Incompatible types in assignment (expression has type "str | None", target has type "None")  [assignment]
scrapers\roaster\crawl4ai_enricher.py:83: error: Incompatible types in assignment (expression has type "str | None", target has type "None")  [assignment]
scrapers\roaster\crawl4ai_enricher.py:84: error: Incompatible return value type (got "dict[str, None]", expected "dict[str, str]")  [return-value]
scrapers\roaster\location.py:9: error: Library stubs not installed for "requests"  [import-untyped]
scrapers\roaster\location.py:9: note: Hint: "python3 -m pip install types-requests"
scrapers\roaster\location.py:9: note: (or run "mypy --install-types" to install all missing stub packages)
scrapers\roaster\location.py:9: note: See https://mypy.readthedocs.io/en/stable/running_mypy.html#missing-imports
common\pydantic_utils.py:65: error: Incompatible types in assignment (expression has type "dict[str, Any]", target has type "str")  [assignment]
common\pydantic_utils.py:67: error: Incompatible types in assignment (expression has type "list[dict[str, Any] | str | Any]", target has type "str")  [assignment]
scrapers\product_crawl4ai\extractors\normalizers.py:442: error: Incompatible types in assignment (expression has type "float", target has type "str")  [assignment]
scrapers\product_crawl4ai\extractors\normalizers.py:446: error: Incompatible types in assignment (expression has type "bool", target has type "str")  [assignment]
scrapers\product_crawl4ai\extractors\normalizers.py:449: error: Incompatible types in assignment (expression has type "list[Any]", target has type "str")  [assignment]
scrapers\product_crawl4ai\extractors\normalizers.py:454: error: Incompatible types in assignment (expression has type "dict[str, Any]", target has type "str")  [assignment]
scrapers\roaster\about.py:19: error: Need type annotation for "about_data" (hint: "about_data: dict[<type>, <type>] = ...")  [var-annotated]
scrapers\product_crawl4ai\api_extractors\woocommerce.py:40: error: Need type annotation for "extracted_attrs" (hint: "extracted_attrs: dict[<type>, <type>] = ...")  [var-annotated]
scrapers\product_crawl4ai\api_extractors\woocommerce.py:186: error: Argument 1 to "append" of "list" has incompatible type "dict[str, Any]"; expected "Coffee"  [arg-type]
scrapers\product_crawl4ai\api_extractors\woocommerce.py:192: error: Incompatible return value type (got "list[Coffee]", expected "list[dict[str, Any]]")  [return-value]
scrapers\product_crawl4ai\api_extractors\woocommerce.py:632: error: Need type annotation for "metadata" (hint: "metadata: dict[<type>, <type>] = ...")  [var-annotated]
scrapers\product_crawl4ai\api_extractors\shopify.py:165: error: Argument 1 to "append" of "list" has incompatible type "dict[str, Any]"; expected "Coffee"  [arg-type]
scrapers\product_crawl4ai\api_extractors\shopify.py:171: error: Incompatible return value type (got "list[Coffee]", expected "list[dict[str, Any]]")  [return-value]
scrapers\product_crawl4ai\api_extractors\shopify.py:542: error: Need type annotation for "prices_by_size" (hint: "prices_by_size: dict[<type>, <type>] = ...")  [var-annotated]
scrapers\roaster\scraper.py:12: error: Module "common.platform_detector" has no attribute "detect_platform"  [attr-defined]
scrapers\roaster\scraper.py:13: error: Module "common.utils" has no attribute "create_slug"  [attr-defined]
scrapers\product_crawl4ai\scraper.py:183: error: Incompatible types in assignment (expression has type "dict[str, Any] | None", variable has type "dict[str, Any]")  [assignment]
Found 27 errors in 11 files (checked 1 source file)

```

### run_roaster.py
```
scrapers\roasters_crawl4ai\crawler.py:184: error: Need type annotation for "results" (hint: "results: dict[<type>, <type>] = ...")  [var-annotated]
scrapers\roasters_crawl4ai\crawler.py:268: error: Need type annotation for "results" (hint: "results: dict[<type>, <type>] = ...")  [var-annotated]
scrapers\roasters_crawl4ai\batch.py:28: error: Need type annotation for "_calls" (hint: "_calls: list[<type>] = ...")  [var-annotated]
Found 3 errors in 2 files (checked 1 source file)

```

### ast-analyzer.py
```
ast-analyzer.py:18: error: Need type annotation for "function_definitions"  [var-annotated]
ast-analyzer.py:19: error: Need type annotation for "function_calls"  [var-annotated]
ast-analyzer.py:20: error: Need type annotation for "imports"  [var-annotated]
ast-analyzer.py:21: error: Need type annotation for "undefined_functions" (hint: "undefined_functions: list[<type>] = ...")  [var-annotated]
ast-analyzer.py:22: error: Need type annotation for "duplicate_functions" (hint: "duplicate_functions: list[<type>] = ...")  [var-annotated]
ast-analyzer.py:23: error: Need type annotation for "common_conflicts" (hint: "common_conflicts: list[<type>] = ...")  [var-annotated]
ast-analyzer.py:24: error: Need type annotation for "all_files_analyzed" (hint: "all_files_analyzed: list[<type>] = ...")  [var-annotated]
ast-analyzer.py:38: error: Need type annotation for "file_info"  [var-annotated]
Found 8 errors in 1 file (checked 1 source file)

```

### check.py
```
check.py:25: error: Need type annotation for "results" (hint: "results: dict[<type>, <type>] = ...")  [var-annotated]
check.py:26: error: Need type annotation for "function_definitions"  [var-annotated]
check.py:27: error: Need type annotation for "function_calls"  [var-annotated]
check.py:28: error: Need type annotation for "imports"  [var-annotated]
check.py:29: error: Need type annotation for "common_functions" (hint: "common_functions: set[<type>] = ...")  [var-annotated]
check.py:197: error: Need type annotation for "issues"  [var-annotated]
check.py:243: error: Need type annotation for "file_info"  [var-annotated]
Found 7 errors in 1 file (checked 1 source file)

```

### file-tree.py
```
Success: no issues found in 1 source file

```

### push_to_supabase.py
```
common\pydantic_utils.py:65: error: Incompatible types in assignment (expression has type "dict[str, Any]", target has type "str")  [assignment]
common\pydantic_utils.py:67: error: Incompatible types in assignment (expression has type "list[dict[str, Any] | str | Any]", target has type "str")  [assignment]
Found 2 errors in 1 file (checked 1 source file)

```

### triage-errors.py
```
triage-errors.py:17: error: Need type annotation for "errors_by_type"  [var-annotated]
triage-errors.py:18: error: Need type annotation for "errors_by_file"  [var-annotated]
Found 2 errors in 1 file (checked 1 source file)

```

### __init__.py
```
Success: no issues found in 1 source file

```

### common\cache.py
```
Success: no issues found in 1 source file

```

### common\enricher.py
```
Success: no issues found in 1 source file

```

### common\exporter.py
```
Success: no issues found in 1 source file

```

### common\platform_detector.py
```
Success: no issues found in 1 source file

```

## Ruff Linting Results

### Basic Issues
```
push_to_supabase.py:7:1: I001 [*] Import block is un-sorted or un-formatted
   |
 5 |   """
 6 |
 7 | / import argparse
 8 | | import json
 9 | | import sys
10 | | from pathlib import Path
11 | | from typing import List, Dict, Any
12 | |
13 | | from loguru import logger
14 | |
15 | | from db.supabase import supabase
16 | | from db.models import Roaster, Coffee
17 | | from common.pydantic_utils import dict_to_pydantic_model, preprocess_coffee_data
   | |________________________________________________________________________________^ I001
   |
   = help: Organize imports

push_to_supabase.py:11:20: F401 [*] `typing.List` imported but unused
   |
 9 | import sys
10 | from pathlib import Path
11 | from typing import List, Dict, Any
   |                    ^^^^ F401
12 |
13 | from loguru import logger
   |
   = help: Remove unused import

push_to_supabase.py:11:26: F401 [*] `typing.Dict` imported but unused
   |
 9 | import sys
10 | from pathlib import Path
11 | from typing import List, Dict, Any
   |                          ^^^^ F401
12 |
13 | from loguru import logger
   |
   = help: Remove unused import

push_to_supabase.py:11:32: F401 [*] `typing.Any` imported but unused
   |
 9 | import sys
10 | from pathlib import Path
11 | from typing import List, Dict, Any
   |                                ^^^ F401
12 |
13 | from loguru import logger
   |
   = help: Remove unused import

refactored\shopify_refactored.py:2:1: I001 [*] Import block is un-sorted or un-formatted
   |
 2 | / import requests
 3 | | import pandas as pd
 4 | | from slugify import slugify
 5 | |
 6 | | from scrapers.product_crawl4ai.extractors.normalizers import normalize_tags, normalize_description
 7 | | from scrapers.product_crawl4ai.extractors.price import extract_prices_from_shopify_product
 8 | | from scrapers.product_crawl4ai.enrichment import enrich_coffee_product
 9 | | from db.models import Coffee, CoffeePrice
10 | | from common.utils import is_coffee_product
   | |__________________________________________^ I001
11 |
12 |   def fetch_shopify_products(shop_url: str) -> list:
   |
   = help: Organize imports

run_product_scraper.py:20:1: I001 [*] Import block is un-sorted or un-formatted
   |
18 |   """
19 |
20 | / import argparse
21 | | import asyncio
22 | | import json
23 | | import sys
24 | | from pathlib import Path
25 | | from typing import List, Dict, Any
26 | |
27 | | from loguru import logger
28 | |
29 | | from scrapers.product_crawl4ai.scraper import ProductScraper
30 | | from scrapers.product_crawl4ai.extractors.normalizers import standardize_coffee_model
31 | | from scrapers.product_crawl4ai.extractors.validators import validate_coffee_product, apply_validation_corrections
   | |_________________________________________________________________________________________________________________^ I001
   |
   = help: Organize imports

run_product_scraper.py:25:20: F401 [*] `typing.List` imported but unused
   |
23 | import sys
24 | from pathlib import Path
25 | from typing import List, Dict, Any
   |                    ^^^^ F401
26 |
27 | from loguru import logger
   |
   = help: Remove unused import

run_product_scraper.py:25:26: F401 [*] `typing.Dict` imported but unused
   |
23 | import sys
24 | from pathlib import Path
25 | from typing import List, Dict, Any
   |                          ^^^^ F401
26 |
27 | from loguru import logger
   |
   = help: Remove unused import

run_product_scraper.py:25:32: F401 [*] `typing.Any` imported but unused
   |
23 | import sys
24 | from pathlib import Path
25 | from typing import List, Dict, Any
   |                                ^^^ F401
26 |
27 | from loguru import logger
   |
   = help: Remove unused import

scrapers\product_crawl4ai\extractors\attributes.py:653:43: E712 Avoid equality comparisons to `False`; use `not coffee["is_single_origin"]:` for false checks
    |
651 |     if "bean_type" in coffee and coffee["bean_type"] == "blend":
652 |         blend_detected = True
653 |     elif "is_single_origin" in coffee and coffee["is_single_origin"] == False:
    |                                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ E712
654 |         blend_detected = True
655 |     elif "blend" in name.lower():
    |
    = help: Replace with `not coffee["is_single_origin"]`

scrapers\roaster\batch.py:3:1: I001 [*] Import block is un-sorted or un-formatted
   |
 1 |   """Batch processing for roaster scraping."""
 2 |
 3 | / import csv
 4 | | import json
 5 | | import logging
 6 | | from pathlib import Path
 7 | | from typing import Any, Dict, List, Tuple, Optional
 8 | |
 9 | | from .scraper import RoasterScraper
   | |___________________________________^ I001
10 |
11 |   logger = logging.getLogger(__name__)
   |
   = help: Organize imports

scrapers\roaster\crawl4ai_enricher.py:25:5: E731 Do not assign a `lambda` expression, use a `def`
   |
23 |     LLMExtractionStrategy = None
24 |     BaseModel = object
25 |     Field = lambda *a, **k: None
   |     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^ E731
   |
   = help: Rewrite `Field` as a `def`

Found 12 errors.
[*] 10 fixable with the `--fix` option (2 hidden fixes can be enabled with the `--unsafe-fixes` option).

```

### Imports Issues
```
push_to_supabase.py:7:1: I001 [*] Import block is un-sorted or un-formatted
   |
 5 |   """
 6 |
 7 | / import argparse
 8 | | import json
 9 | | import sys
10 | | from pathlib import Path
11 | | from typing import List, Dict, Any
12 | |
13 | | from loguru import logger
14 | |
15 | | from db.supabase import supabase
16 | | from db.models import Roaster, Coffee
17 | | from common.pydantic_utils import dict_to_pydantic_model, preprocess_coffee_data
   | |________________________________________________________________________________^ I001
   |
   = help: Organize imports

refactored\shopify_refactored.py:2:1: I001 [*] Import block is un-sorted or un-formatted
   |
 2 | / import requests
 3 | | import pandas as pd
 4 | | from slugify import slugify
 5 | |
 6 | | from scrapers.product_crawl4ai.extractors.normalizers import normalize_tags, normalize_description
 7 | | from scrapers.product_crawl4ai.extractors.price import extract_prices_from_shopify_product
 8 | | from scrapers.product_crawl4ai.enrichment import enrich_coffee_product
 9 | | from db.models import Coffee, CoffeePrice
10 | | from common.utils import is_coffee_product
   | |__________________________________________^ I001
11 |
12 |   def fetch_shopify_products(shop_url: str) -> list:
   |
   = help: Organize imports

run_product_scraper.py:20:1: I001 [*] Import block is un-sorted or un-formatted
   |
18 |   """
19 |
20 | / import argparse
21 | | import asyncio
22 | | import json
23 | | import sys
24 | | from pathlib import Path
25 | | from typing import List, Dict, Any
26 | |
27 | | from loguru import logger
28 | |
29 | | from scrapers.product_crawl4ai.scraper import ProductScraper
30 | | from scrapers.product_crawl4ai.extractors.normalizers import standardize_coffee_model
31 | | from scrapers.product_crawl4ai.extractors.validators import validate_coffee_product, apply_validation_corrections
   | |_________________________________________________________________________________________________________________^ I001
   |
   = help: Organize imports

scrapers\roaster\batch.py:3:1: I001 [*] Import block is un-sorted or un-formatted
   |
 1 |   """Batch processing for roaster scraping."""
 2 |
 3 | / import csv
 4 | | import json
 5 | | import logging
 6 | | from pathlib import Path
 7 | | from typing import Any, Dict, List, Tuple, Optional
 8 | |
 9 | | from .scraper import RoasterScraper
   | |___________________________________^ I001
10 |
11 |   logger = logging.getLogger(__name__)
   |
   = help: Organize imports

Found 4 errors.
[*] 4 fixable with the `--fix` option.

```

### Unused Issues
```
push_to_supabase.py:11:20: F401 [*] `typing.List` imported but unused
   |
 9 | import sys
10 | from pathlib import Path
11 | from typing import List, Dict, Any
   |                    ^^^^ F401
12 |
13 | from loguru import logger
   |
   = help: Remove unused import

push_to_supabase.py:11:26: F401 [*] `typing.Dict` imported but unused
   |
 9 | import sys
10 | from pathlib import Path
11 | from typing import List, Dict, Any
   |                          ^^^^ F401
12 |
13 | from loguru import logger
   |
   = help: Remove unused import

push_to_supabase.py:11:32: F401 [*] `typing.Any` imported but unused
   |
 9 | import sys
10 | from pathlib import Path
11 | from typing import List, Dict, Any
   |                                ^^^ F401
12 |
13 | from loguru import logger
   |
   = help: Remove unused import

run_product_scraper.py:25:20: F401 [*] `typing.List` imported but unused
   |
23 | import sys
24 | from pathlib import Path
25 | from typing import List, Dict, Any
   |                    ^^^^ F401
26 |
27 | from loguru import logger
   |
   = help: Remove unused import

run_product_scraper.py:25:26: F401 [*] `typing.Dict` imported but unused
   |
23 | import sys
24 | from pathlib import Path
25 | from typing import List, Dict, Any
   |                          ^^^^ F401
26 |
27 | from loguru import logger
   |
   = help: Remove unused import

run_product_scraper.py:25:32: F401 [*] `typing.Any` imported but unused
   |
23 | import sys
24 | from pathlib import Path
25 | from typing import List, Dict, Any
   |                                ^^^ F401
26 |
27 | from loguru import logger
   |
   = help: Remove unused import

Found 6 errors.
[*] 6 fixable with the `--fix` option.

```

### Complexity - Clean!

### Security Issues
```
check.py:82:26: S603 `subprocess` call: check for execution of untrusted input
   |
81 |                 # Try with package-aware flags first
82 |                 result = subprocess.run(
   |                          ^^^^^^^^^^^^^^ S603
83 |                     [
84 |                         sys.executable,
   |

check.py:100:30: S603 `subprocess` call: check for execution of untrusted input
    |
 98 |                 if "is not a valid Python package name" in result.stderr:
 99 |                     print("  ðŸ“¦ Package name issue detected, trying alternative approach...")
100 |                     result = subprocess.run(
    |                              ^^^^^^^^^^^^^^ S603
101 |                         [
102 |                             sys.executable,
    |

check.py:136:22: S603 `subprocess` call: check for execution of untrusted input
    |
134 |         for file_path in other_files[:10]:  # Limit to avoid spam
135 |             relative_path = file_path.relative_to(self.project_root)
136 |             result = subprocess.run(
    |                      ^^^^^^^^^^^^^^ S603
137 |                 [
138 |                     sys.executable,
    |

check.py:179:26: S603 `subprocess` call: check for execution of untrusted input
    |
177 |             cmd = ["ruff", "check"] + args + [str(self.project_root)]
178 |             try:
179 |                 result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
    |                          ^^^^^^^^^^^^^^ S603
180 |                 ruff_results[check_name] = {
181 |                     "stdout": result.stdout,
    |

common\cache.py:49:16: S324 Probable use of insecure hash functions in `hashlib`: `md5`
   |
47 |         url = re.sub(r"/+$", "", url)  # Remove trailing slashes
48 |
49 |         return hashlib.md5(url.encode()).hexdigest()
   |                ^^^^^^^^^^^ S324
50 |
51 |     def _get_roaster_cache_key(self, name: str, url: str) -> str:
   |

common\cache.py:53:16: S324 Probable use of insecure hash functions in `hashlib`: `md5`
   |
51 |     def _get_roaster_cache_key(self, name: str, url: str) -> str:
52 |         """Generate a unique cache key for a roaster."""
53 |         return hashlib.md5(f"{name}_{url}".encode()).hexdigest()
   |                ^^^^^^^^^^^ S324
54 |
55 |     def get_cached_html(self, url: str, max_age_days: int = 7, field_stability: Optional[str] = None) -> Optional[str]:
   |

common\pydantic_utils.py:112:17: S110 `try`-`except`-`pass` detected, consider logging the exception
    |
110 |                   try:
111 |                       v = float(v)
112 | /                 except Exception:
113 | |                     pass
    | |________________________^ S110
114 |               else:
115 |                   try:
    |

common\pydantic_utils.py:117:17: S110 `try`-`except`-`pass` detected, consider logging the exception
    |
115 |                   try:
116 |                       v = int(v)
117 | /                 except Exception:
118 | |                     pass
    | |________________________^ S110
119 |           # Recursively handle nested models/lists
120 |           if isinstance(v, list):
    |

scrapers\roaster\scraper.py:211:13: S112 `try`-`except`-`continue` detected, consider logging the exception
    |
209 |                           }
210 |                       )
211 | /             except Exception:
212 | |                 continue
    | |________________________^ S112
213 |
214 |           return structured_data
    |

tests\test_common_cache.py:18:5: S101 Use of `assert` detected
   |
16 |     c.cache_roaster(roaster)
17 |     cached = c.get_cached_roaster("Test Roaster", "https://test.com")
18 |     assert cached is not None
   |     ^^^^^^ S101
19 |     assert cached["name"] == "Test Roaster"
   |

tests\test_common_cache.py:19:5: S101 Use of `assert` detected
   |
17 |     cached = c.get_cached_roaster("Test Roaster", "https://test.com")
18 |     assert cached is not None
19 |     assert cached["name"] == "Test Roaster"
   |     ^^^^^^ S101
20 |
21 |     # Test cache_html and get_cached_html
   |

tests\test_common_cache.py:24:5: S101 Use of `assert` detected
   |
22 |     c.cache_html("https://test.com/page", "<html>data</html>")
23 |     html = c.get_cached_html("https://test.com/page")
24 |     assert html == "<html>data</html>"
   |     ^^^^^^ S101
25 |
26 |     # Test cache_products and get_cached_products
   |

tests\test_common_cache.py:30:5: S101 Use of `assert` detected
   |
28 |     c.cache_products("roaster1", products)
29 |     cached_products = c.get_cached_products("roaster1")
30 |     assert isinstance(cached_products, list)
   |     ^^^^^^ S101
31 |     assert cached_products[0]["name"] == "Coffee"
   |

tests\test_common_cache.py:31:5: S101 Use of `assert` detected
   |
29 |     cached_products = c.get_cached_products("roaster1")
30 |     assert isinstance(cached_products, list)
31 |     assert cached_products[0]["name"] == "Coffee"
   |     ^^^^^^ S101
32 |
33 |     # Test clear_cache
   |

tests\test_common_cache.py:37:9: S101 Use of `assert` detected
   |
35 |     # Allow empty subdirectories to remain; check all files are deleted
36 |     for root, dirs, files in os.walk(test_cache_dir):
37 |         assert not files  # No files should remain
   |         ^^^^^^ S101
   |

tests\test_common_enricher.py:18:9: S101 Use of `assert` detected
   |
16 |     # Should contain at least the original fields
17 |     for k, v in roaster.items():
18 |         assert result[k] == v
   |         ^^^^^^ S101
19 |     # If a generic description is added, that's acceptable
20 |     assert "description" in result
   |

tests\test_common_enricher.py:20:5: S101 Use of `assert` detected
   |
18 |         assert result[k] == v
19 |     # If a generic description is added, that's acceptable
20 |     assert "description" in result
   |     ^^^^^^ S101
21 |     assert isinstance(result["description"], str)
   |

tests\test_common_enricher.py:21:5: S101 Use of `assert` detected
   |
19 |     # If a generic description is added, that's acceptable
20 |     assert "description" in result
21 |     assert isinstance(result["description"], str)
   |     ^^^^^^ S101
   |

tests\test_common_enricher.py:42:13: S101 Use of `assert` detected
   |
40 |             mock_openai.return_value.chat.completions.create.return_value = fake_response
41 |             result = await service.enhance_roaster_description(roaster.copy())
42 |             assert result["description"] == "A great roaster."
   |             ^^^^^^ S101
43 |             assert result["founded_year"] == 2020
44 |             assert result["address"] == "123 Main St"
   |

tests\test_common_enricher.py:43:13: S101 Use of `assert` detected
   |
41 |             result = await service.enhance_roaster_description(roaster.copy())
42 |             assert result["description"] == "A great roaster."
43 |             assert result["founded_year"] == 2020
   |             ^^^^^^ S101
44 |             assert result["address"] == "123 Main St"
   |

tests\test_common_enricher.py:44:13: S101 Use of `assert` detected
   |
42 |             assert result["description"] == "A great roaster."
43 |             assert result["founded_year"] == 2020
44 |             assert result["address"] == "123 Main St"
   |             ^^^^^^ S101
   |

tests\test_common_enricher.py:55:13: S101 Use of `assert` detected
   |
53 |             mock_openai.return_value.chat.completions.create.side_effect = Exception("fail")
54 |             result = await service.enhance_roaster_description(roaster.copy())
55 |             assert result == roaster
   |             ^^^^^^ S101
   |

tests\test_common_exporter.py:19:5: S101 Use of `assert` detected
   |
17 |     # Test export_to_csv
18 |     exporter.export_to_csv(data, str(csv_path))
19 |     assert os.path.exists(csv_path)
   |     ^^^^^^ S101
20 |     with open(csv_path, "r", encoding="utf-8-sig") as f:
21 |         lines = f.readlines()
   |

tests\test_common_exporter.py:22:9: S101 Use of `assert` detected
   |
20 |     with open(csv_path, "r", encoding="utf-8-sig") as f:
21 |         lines = f.readlines()
22 |         assert "name" in lines[0] and "price" in lines[0]
   |         ^^^^^^ S101
23 |         assert "Coffee1" in lines[1]
24 |         assert "Coffee2" in lines[2]
   |

tests\test_common_exporter.py:23:9: S101 Use of `assert` detected
   |
21 |         lines = f.readlines()
22 |         assert "name" in lines[0] and "price" in lines[0]
23 |         assert "Coffee1" in lines[1]
   |         ^^^^^^ S101
24 |         assert "Coffee2" in lines[2]
   |

tests\test_common_exporter.py:24:9: S101 Use of `assert` detected
   |
22 |         assert "name" in lines[0] and "price" in lines[0]
23 |         assert "Coffee1" in lines[1]
24 |         assert "Coffee2" in lines[2]
   |         ^^^^^^ S101
25 |
26 |     # Test export_to_json
   |

tests\test_common_exporter.py:28:5: S101 Use of `assert` detected
   |
26 |     # Test export_to_json
27 |     exporter.export_to_json(data, str(json_path))
28 |     assert os.path.exists(json_path)
   |     ^^^^^^ S101
29 |     import json as pyjson
   |

tests\test_common_exporter.py:33:9: S101 Use of `assert` detected
   |
31 |     with open(json_path, "r", encoding="utf-8") as f:
32 |         loaded = pyjson.load(f)
33 |         assert loaded == data
   |         ^^^^^^ S101
   |

tests\test_common_pydantic_utils.py:26:5: S101 Use of `assert` detected
   |
24 |     model = TestModel(name="Coffee")
25 |     result = pydantic_utils.model_to_dict(model)
26 |     assert result["name"] == "Coffee"
   |     ^^^^^^ S101
27 |     assert result["url"] == "https://example.com"
28 |     assert result["value"] == 42
   |

tests\test_common_pydantic_utils.py:27:5: S101 Use of `assert` detected
   |
25 |     result = pydantic_utils.model_to_dict(model)
26 |     assert result["name"] == "Coffee"
27 |     assert result["url"] == "https://example.com"
   |     ^^^^^^ S101
28 |     assert result["value"] == 42
29 |     assert "optional" not in result  # exclude_none=True by default
   |

tests\test_common_pydantic_utils.py:28:5: S101 Use of `assert` detected
   |
26 |     assert result["name"] == "Coffee"
27 |     assert result["url"] == "https://example.com"
28 |     assert result["value"] == 42
   |     ^^^^^^ S101
29 |     assert "optional" not in result  # exclude_none=True by default
   |

tests\test_common_pydantic_utils.py:29:5: S101 Use of `assert` detected
   |
27 |     assert result["url"] == "https://example.com"
28 |     assert result["value"] == 42
29 |     assert "optional" not in result  # exclude_none=True by default
   |     ^^^^^^ S101
   |

tests\test_common_pydantic_utils.py:37:5: S101 Use of `assert` detected
   |
35 |     model = TestModel(name="Coffee")
36 |     result = pydantic_utils.model_to_dict(model, exclude_none=False)
37 |     assert "optional" in result
   |     ^^^^^^ S101
38 |     assert result["optional"] is None
   |

tests\test_common_pydantic_utils.py:38:5: S101 Use of `assert` detected
   |
36 |     result = pydantic_utils.model_to_dict(model, exclude_none=False)
37 |     assert "optional" in result
38 |     assert result["optional"] is None
   |     ^^^^^^ S101
   |

tests\test_common_pydantic_utils.py:46:5: S101 Use of `assert` detected
   |
44 |     data = {"name": "Test", "url": "https://test.com", "value": 100}
45 |     model = pydantic_utils.dict_to_pydantic_model(data, TestModel)
46 |     assert isinstance(model, TestModel)
   |     ^^^^^^ S101
47 |     assert model.name == "Test"
48 |     assert str(model.url) == "https://test.com/"
   |

tests\test_common_pydantic_utils.py:47:5: S101 Use of `assert` detected
   |
45 |     model = pydantic_utils.dict_to_pydantic_model(data, TestModel)
46 |     assert isinstance(model, TestModel)
47 |     assert model.name == "Test"
   |     ^^^^^^ S101
48 |     assert str(model.url) == "https://test.com/"
49 |     assert model.value == 100
   |

tests\test_common_pydantic_utils.py:48:5: S101 Use of `assert` detected
   |
46 |     assert isinstance(model, TestModel)
47 |     assert model.name == "Test"
48 |     assert str(model.url) == "https://test.com/"
   |     ^^^^^^ S101
49 |     assert model.value == 100
   |

tests\test_common_pydantic_utils.py:49:5: S101 Use of `assert` detected
   |
47 |     assert model.name == "Test"
48 |     assert str(model.url) == "https://test.com/"
49 |     assert model.value == 100
   |     ^^^^^^ S101
   |

tests\test_common_pydantic_utils.py:57:5: S101 Use of `assert` detected
   |
55 |     data = {"url": "https://test.com"}
56 |     model = pydantic_utils.dict_to_pydantic_model(data, TestModel)
57 |     assert model is None
   |     ^^^^^^ S101
   |

tests\test_common_pydantic_utils.py:65:5: S101 Use of `assert` detected
   |
63 |     data = {"the_name": "Test", "url": "https://test.com", "value": 99}
64 |     model = pydantic_utils.dict_to_pydantic_model(data, TestModel, field_map={"the_name": "name"})
65 |     assert model.name == "Test"
   |     ^^^^^^ S101
66 |     assert model.value == 99
   |

tests\test_common_pydantic_utils.py:66:5: S101 Use of `assert` detected
   |
64 |     model = pydantic_utils.dict_to_pydantic_model(data, TestModel, field_map={"the_name": "name"})
65 |     assert model.name == "Test"
66 |     assert model.value == 99
   |     ^^^^^^ S101
   |

tests\test_common_pydantic_utils.py:73:5: S101 Use of `assert` detected
   |
71 |     data = {"name": "Roaster", "website_url": "https://roaster.com"}
72 |     out = pydantic_utils.preprocess_roaster_data(data)
73 |     assert isinstance(out, dict)
   |     ^^^^^^ S101
74 |     assert out["name"] == "Roaster"
   |

tests\test_common_pydantic_utils.py:74:5: S101 Use of `assert` detected
   |
72 |     out = pydantic_utils.preprocess_roaster_data(data)
73 |     assert isinstance(out, dict)
74 |     assert out["name"] == "Roaster"
   |     ^^^^^^ S101
   |

tests\test_common_pydantic_utils.py:80:5: S101 Use of `assert` detected
   |
78 |     data = {"name": "Coffee", "direct_buy_url": "https://buy.com"}
79 |     out = pydantic_utils.preprocess_coffee_data(data)
80 |     assert isinstance(out, dict)
   |     ^^^^^^ S101
81 |     assert out["name"] == "Coffee"
   |

tests\test_common_pydantic_utils.py:81:5: S101 Use of `assert` detected
   |
79 |     out = pydantic_utils.preprocess_coffee_data(data)
80 |     assert isinstance(out, dict)
81 |     assert out["name"] == "Coffee"
   |     ^^^^^^ S101
   |

tests\test_common_utils.py:21:5: S101 Use of `assert` detected
   |
19 | )
20 | def test_create_slug(name, expected):
21 |     assert utils.create_slug(name) == expected
   |     ^^^^^^ S101
   |

tests\test_common_utils.py:29:5: S101 Use of `assert` detected
   |
27 | )
28 | def test_normalize_phone_number(phone, expected):
29 |     assert utils.normalize_phone_number(phone) == expected
   |     ^^^^^^ S101
   |

tests\test_common_utils.py:38:5: S101 Use of `assert` detected
   |
36 | )
37 | def test_clean_html(html, expected):
38 |     assert utils.clean_html(html) == expected
   |     ^^^^^^ S101
   |

tests\test_common_utils.py:46:5: S101 Use of `assert` detected
   |
44 | )
45 | def test_clean_description(desc, expected):
46 |     assert utils.clean_description(desc) == expected
   |     ^^^^^^ S101
   |

tests\test_common_utils.py:54:5: S101 Use of `assert` detected
   |
52 | )
53 | def test_get_domain_from_url(url, expected):
54 |     assert utils.get_domain_from_url(url) == expected
   |     ^^^^^^ S101
   |

tests\test_common_utils.py:67:5: S101 Use of `assert` detected
   |
65 | )
66 | def test_normalize_url(url, expected):
67 |     assert utils.normalize_url(url) == expected
   |     ^^^^^^ S101
   |

tests\test_config.py:28:5: S101 Use of `assert` detected
   |
26 |     patch_env(monkeypatch, {"SUPABASE_URL": "https://test.supabase.io", "SUPABASE_KEY": "secret"})
27 |     cfg = config_module.SupabaseConfig.from_env()
28 |     assert cfg.url == "https://test.supabase.io"
   |     ^^^^^^ S101
29 |     assert cfg.key == "secret"
   |

tests\test_config.py:29:5: S101 Use of `assert` detected
   |
27 |     cfg = config_module.SupabaseConfig.from_env()
28 |     assert cfg.url == "https://test.supabase.io"
29 |     assert cfg.key == "secret"
   |     ^^^^^^ S101
   |

tests\test_config.py:50:5: S101 Use of `assert` detected
   |
49 |     importlib.reload(config_module)
50 |     assert cache_dir.exists()
   |     ^^^^^^ S101
51 |     # Clean up
52 |     shutil.rmtree(cache_dir)
   |

tests\test_config.py:59:5: S101 Use of `assert` detected
   |
57 |     expected_url = "https://xrgmpplicqnlyowbhhrj.supabase.co"
58 |     cfg = config_module.SupabaseConfig.from_env()
59 |     assert cfg.url == expected_url
   |     ^^^^^^ S101
   |

tests\test_config.py:77:5: S101 Use of `assert` detected
   |
75 |     # Patch Config.from_env to not raise
76 |     config = config_module.Config.from_env()
77 |     assert config.supabase.url == "https://test.supabase.io"
   |     ^^^^^^ S101
78 |     assert config.supabase.key == "secret"
79 |     assert hasattr(config, "scraper")
   |

tests\test_config.py:78:5: S101 Use of `assert` detected
   |
76 |     config = config_module.Config.from_env()
77 |     assert config.supabase.url == "https://test.supabase.io"
78 |     assert config.supabase.key == "secret"
   |     ^^^^^^ S101
79 |     assert hasattr(config, "scraper")
80 |     assert hasattr(config, "llm")
   |

tests\test_config.py:79:5: S101 Use of `assert` detected
   |
77 |     assert config.supabase.url == "https://test.supabase.io"
78 |     assert config.supabase.key == "secret"
79 |     assert hasattr(config, "scraper")
   |     ^^^^^^ S101
80 |     assert hasattr(config, "llm")
81 |     assert config.llm.openai_api_key == "oa-key"
   |

tests\test_config.py:80:5: S101 Use of `assert` detected
   |
78 |     assert config.supabase.key == "secret"
79 |     assert hasattr(config, "scraper")
80 |     assert hasattr(config, "llm")
   |     ^^^^^^ S101
81 |     assert config.llm.openai_api_key == "oa-key"
82 |     assert config.llm.deepseek_api_key == "ds-key"
   |

tests\test_config.py:81:5: S101 Use of `assert` detected
   |
79 |     assert hasattr(config, "scraper")
80 |     assert hasattr(config, "llm")
81 |     assert config.llm.openai_api_key == "oa-key"
   |     ^^^^^^ S101
82 |     assert config.llm.deepseek_api_key == "ds-key"
   |

tests\test_config.py:82:5: S101 Use of `assert` detected
   |
80 |     assert hasattr(config, "llm")
81 |     assert config.llm.openai_api_key == "oa-key"
82 |     assert config.llm.deepseek_api_key == "ds-key"
   |     ^^^^^^ S101
   |

tests\test_db_models.py:13:5: S101 Use of `assert` detected
   |
12 | def test_roastlevel_enum():
13 |     assert "light" in models.RoastLevel.ALL
   |     ^^^^^^ S101
14 |     assert models.RoastLevel.LIGHT == "light"
   |

tests\test_db_models.py:14:5: S101 Use of `assert` detected
   |
12 | def test_roastlevel_enum():
13 |     assert "light" in models.RoastLevel.ALL
14 |     assert models.RoastLevel.LIGHT == "light"
   |     ^^^^^^ S101
   |

tests\test_db_models.py:18:5: S101 Use of `assert` detected
   |
17 | def test_beantype_enum():
18 |     assert "arabica" in models.BeanType.ALL
   |     ^^^^^^ S101
19 |     assert models.BeanType.ARABICA == "arabica"
   |

tests\test_db_models.py:19:5: S101 Use of `assert` detected
   |
17 | def test_beantype_enum():
18 |     assert "arabica" in models.BeanType.ALL
19 |     assert models.BeanType.ARABICA == "arabica"
   |     ^^^^^^ S101
   |

tests\test_db_models.py:23:5: S101 Use of `assert` detected
   |
22 | def test_processingmethod_enum():
23 |     assert "washed" in models.ProcessingMethod.ALL
   |     ^^^^^^ S101
24 |     assert models.ProcessingMethod.WASHED == "washed"
   |

tests\test_db_models.py:24:5: S101 Use of `assert` detected
   |
22 | def test_processingmethod_enum():
23 |     assert "washed" in models.ProcessingMethod.ALL
24 |     assert models.ProcessingMethod.WASHED == "washed"
   |     ^^^^^^ S101
   |

tests\test_db_models.py:29:5: S101 Use of `assert` detected
   |
27 | def test_roaster_model_valid():
28 |     r = models.Roaster(name="Test Roaster", slug="test-roaster", website_url="https://test.com")
29 |     assert r.name == "Test Roaster"
   |     ^^^^^^ S101
30 |     assert str(r.website_url) == "https://test.com/"
   |

tests\test_db_models.py:30:5: S101 Use of `assert` detected
   |
28 |     r = models.Roaster(name="Test Roaster", slug="test-roaster", website_url="https://test.com")
29 |     assert r.name == "Test Roaster"
30 |     assert str(r.website_url) == "https://test.com/"
   |     ^^^^^^ S101
   |

tests\test_db_models.py:40:5: S101 Use of `assert` detected
   |
38 | def test_coffee_model_valid():
39 |     c = models.Coffee(name="Test Coffee", slug="test-coffee", roaster_id="r1", direct_buy_url="https://buy.com")
40 |     assert c.name == "Test Coffee"
   |     ^^^^^^ S101
41 |     assert str(c.direct_buy_url) == "https://buy.com/"
   |

tests\test_db_models.py:41:5: S101 Use of `assert` detected
   |
39 |     c = models.Coffee(name="Test Coffee", slug="test-coffee", roaster_id="r1", direct_buy_url="https://buy.com")
40 |     assert c.name == "Test Coffee"
41 |     assert str(c.direct_buy_url) == "https://buy.com/"
   |     ^^^^^^ S101
   |

tests\test_db_models.py:56:5: S101 Use of `assert` detected
   |
54 | def test_coffeeprice_and_externallink():
55 |     price = models.CoffeePrice(size_grams=250, price=500)
56 |     assert price.size_grams == 250
   |     ^^^^^^ S101
57 |     link = models.ExternalLink(provider="Amazon", url="https://amz.com")
58 |     assert link.provider == "Amazon"
   |

tests\test_db_models.py:58:5: S101 Use of `assert` detected
   |
56 |     assert price.size_grams == 250
57 |     link = models.ExternalLink(provider="Amazon", url="https://amz.com")
58 |     assert link.provider == "Amazon"
   |     ^^^^^^ S101
59 |     assert str(link.url) == "https://amz.com/"
   |

tests\test_db_models.py:59:5: S101 Use of `assert` detected
   |
57 |     link = models.ExternalLink(provider="Amazon", url="https://amz.com")
58 |     assert link.provider == "Amazon"
59 |     assert str(link.url) == "https://amz.com/"
   |     ^^^^^^ S101
   |

tests\test_db_models.py:71:5: S101 Use of `assert` detected
   |
69 |         field_confidence={"foo": 100},
70 |     )
71 |     assert state.url == "https://site.com"
   |     ^^^^^^ S101
72 |     assert state.status == "done"
73 |     assert state.field_timestamps["foo"] == now
   |

tests\test_db_models.py:72:5: S101 Use of `assert` detected
   |
70 |     )
71 |     assert state.url == "https://site.com"
72 |     assert state.status == "done"
   |     ^^^^^^ S101
73 |     assert state.field_timestamps["foo"] == now
74 |     assert state.field_confidence["foo"] == 100
   |

tests\test_db_models.py:73:5: S101 Use of `assert` detected
   |
71 |     assert state.url == "https://site.com"
72 |     assert state.status == "done"
73 |     assert state.field_timestamps["foo"] == now
   |     ^^^^^^ S101
74 |     assert state.field_confidence["foo"] == 100
   |

tests\test_db_models.py:74:5: S101 Use of `assert` detected
   |
72 |     assert state.status == "done"
73 |     assert state.field_timestamps["foo"] == now
74 |     assert state.field_confidence["foo"] == 100
   |     ^^^^^^ S101
   |

tests\test_main.py:18:5: S101 Use of `assert` detected
   |
16 |     if log_dir.exists():
17 |         shutil.rmtree(log_dir)
18 |     assert log_dir.exists(), "Log directory should be created by setup_logging()"
   |     ^^^^^^ S101
   |

tests\test_main.py:26:5: S101 Use of `assert` detected
   |
24 |     monkeypatch.setattr(main, "detect_platform", lambda url: ("shopify", 0.99))
25 |     result = runner.invoke(main.detect, ["https://example.com"])
26 |     assert result.exit_code == 0
   |     ^^^^^^ S101
27 |     assert "shopify" in result.output
   |

tests\test_main.py:27:5: S101 Use of `assert` detected
   |
25 |     result = runner.invoke(main.detect, ["https://example.com"])
26 |     assert result.exit_code == 0
27 |     assert "shopify" in result.output
   |     ^^^^^^ S101
   |

tests\test_main.py:41:5: S101 Use of `assert` detected
   |
39 |     monkeypatch.setattr(main.supabase, "upsert_roaster", lambda r: None)
40 |     result = runner.invoke(main.scrape_roaster, ["Test Roaster,https://roaster.com"])
41 |     assert result.exit_code == 0
   |     ^^^^^^ S101
42 |     assert "Successfully scraped roaster" in result.output
   |

tests\test_main.py:42:5: S101 Use of `assert` detected
   |
40 |     result = runner.invoke(main.scrape_roaster, ["Test Roaster,https://roaster.com"])
41 |     assert result.exit_code == 0
42 |     assert "Successfully scraped roaster" in result.output
   |     ^^^^^^ S101
   |

tests\test_main.py:62:5: S101 Use of `assert` detected
   |
60 |         writer.writerow({"name": "Batch Roaster", "url": "https://batch.com"})
61 |     result = runner.invoke(main.scrape_roaster, [str(csv_path), "--csv"])
62 |     assert result.exit_code == 0
   |     ^^^^^^ S101
63 |     assert "Scraped 1 roasters" in result.output
   |

tests\test_main.py:63:5: S101 Use of `assert` detected
   |
61 |     result = runner.invoke(main.scrape_roaster, [str(csv_path), "--csv"])
62 |     assert result.exit_code == 0
63 |     assert "Scraped 1 roasters" in result.output
   |     ^^^^^^ S101
   |

tests\test_main.py:83:5: S101 Use of `assert` detected
   |
81 |         writer.writerow({"name": "", "url": "https://bad.com"})
82 |     result = runner.invoke(main.scrape_roaster, [str(csv_path), "--csv"])
83 |     assert result.exit_code == 0
   |     ^^^^^^ S101
84 |     assert "Input Errors" in result.output
   |

tests\test_main.py:84:5: S101 Use of `assert` detected
   |
82 |     result = runner.invoke(main.scrape_roaster, [str(csv_path), "--csv"])
83 |     assert result.exit_code == 0
84 |     assert "Input Errors" in result.output
   |     ^^^^^^ S101
   |

tests\test_main.py:90:5: S101 Use of `assert` detected
   |
88 |     runner = CliRunner()
89 |     result = runner.invoke(main.scrape_roaster, ["badinput"])
90 |     assert result.exit_code == 0
   |     ^^^^^^ S101
91 |     assert "Error: For single roaster, provide input as 'name,url'" in result.output
   |

tests\test_main.py:91:5: S101 Use of `assert` detected
   |
89 |     result = runner.invoke(main.scrape_roaster, ["badinput"])
90 |     assert result.exit_code == 0
91 |     assert "Error: For single roaster, provide input as 'name,url'" in result.output
   |     ^^^^^^ S101
   |

tests\test_main.py:108:5: S101 Use of `assert` detected
    |
106 |     monkeypatch.setattr(main.supabase, "upsert_coffee", lambda c: None)
107 |     result = runner.invoke(main.scrape_products, ["Test Roaster,https://roaster.com"])
108 |     assert result.exit_code == 0
    |     ^^^^^^ S101
109 |     assert "Successfully scraped" in result.output
    |

tests\test_main.py:109:5: S101 Use of `assert` detected
    |
107 |     result = runner.invoke(main.scrape_products, ["Test Roaster,https://roaster.com"])
108 |     assert result.exit_code == 0
109 |     assert "Successfully scraped" in result.output
    |     ^^^^^^ S101
    |

tests\test_platform_detector.py:24:5: S101 Use of `assert` detected
   |
22 |     platform, confidence = await detector.detect(url)
23 |     print(f"{url}: Detected {platform} (confidence={confidence})")
24 |     assert platform == expected_platform
   |     ^^^^^^ S101
25 |     assert confidence >= 40  # Should be confident for these known sites
   |

tests\test_platform_detector.py:25:5: S101 Use of `assert` detected
   |
23 |     print(f"{url}: Detected {platform} (confidence={confidence})")
24 |     assert platform == expected_platform
25 |     assert confidence >= 40  # Should be confident for these known sites
   |     ^^^^^^ S101
   |

tests\test_product_crawl4ai_deep_crawler.py:46:5: S101 Use of `assert` detected
   |
44 |     with patch("scrapers.product_crawl4ai.discovery.deep_crawler.is_coffee_product", return_value=True):
45 |         products = await discover_products_via_crawl4ai("https://test.com", "roaster1", "Test Roaster", max_products=1)
46 |     assert isinstance(products, list)
   |     ^^^^^^ S101
47 |     assert products
48 |     assert products[0]["name"] == "Test Coffee"
   |

tests\test_product_crawl4ai_deep_crawler.py:47:5: S101 Use of `assert` detected
   |
45 |         products = await discover_products_via_crawl4ai("https://test.com", "roaster1", "Test Roaster", max_products=1)
46 |     assert isinstance(products, list)
47 |     assert products
   |     ^^^^^^ S101
48 |     assert products[0]["name"] == "Test Coffee"
   |

tests\test_product_crawl4ai_deep_crawler.py:48:5: S101 Use of `assert` detected
   |
46 |     assert isinstance(products, list)
47 |     assert products
48 |     assert products[0]["name"] == "Test Coffee"
   |     ^^^^^^ S101
   |

tests\test_product_crawl4ai_deep_crawler.py:62:5: S101 Use of `assert` detected
   |
61 |     products = await discover_products_via_crawl4ai("https://test.com", "roaster1", "Test Roaster", max_products=1)
62 |     assert products == []
   |     ^^^^^^ S101
   |

tests\test_product_crawl4ai_deep_crawler.py:79:9: S101 Use of `assert` detected
   |
77 |     markdown = "# Ethiopia Coffee\nPrice: $15\nRoast level: Medium\nArabica beans"
78 |     with patch("scrapers.product_crawl4ai.discovery.deep_crawler.validate_product_at_discovery", return_value=True):
79 |         assert is_product_page(url, html, markdown) is True
   |         ^^^^^^ S101
   |

tests\test_product_crawl4ai_deep_crawler.py:88:5: S101 Use of `assert` detected
   |
86 |     html = "<html><h1>About Us</h1></html>"
87 |     markdown = "# About Us"
88 |     assert is_product_page(url, html, markdown) is False
   |     ^^^^^^ S101
   |

tests\test_product_crawl4ai_extractors.py:39:5: S101 Use of `assert` detected
   |
38 |     products = await shopify.extract_products_shopify("https://test.myshopify.com", "roaster123")
39 |     assert isinstance(products, list)
   |     ^^^^^^ S101
40 |     assert products
41 |     assert products[0]["name"] == "Test Coffee"
   |

tests\test_product_crawl4ai_extractors.py:40:5: S101 Use of `assert` detected
   |
38 |     products = await shopify.extract_products_shopify("https://test.myshopify.com", "roaster123")
39 |     assert isinstance(products, list)
40 |     assert products
   |     ^^^^^^ S101
41 |     assert products[0]["name"] == "Test Coffee"
   |

tests\test_product_crawl4ai_extractors.py:41:5: S101 Use of `assert` detected
   |
39 |     assert isinstance(products, list)
40 |     assert products
41 |     assert products[0]["name"] == "Test Coffee"
   |     ^^^^^^ S101
   |

tests\test_product_crawl4ai_extractors.py:65:5: S101 Use of `assert` detected
   |
64 |     products = await woocommerce.extract_products_woocommerce("https://test.com", "roaster456")
65 |     assert isinstance(products, list)
   |     ^^^^^^ S101
66 |     assert products
67 |     assert products[0]["name"] == "Woo Coffee"
   |

tests\test_product_crawl4ai_extractors.py:66:5: S101 Use of `assert` detected
   |
64 |     products = await woocommerce.extract_products_woocommerce("https://test.com", "roaster456")
65 |     assert isinstance(products, list)
66 |     assert products
   |     ^^^^^^ S101
67 |     assert products[0]["name"] == "Woo Coffee"
   |

tests\test_product_crawl4ai_extractors.py:67:5: S101 Use of `assert` detected
   |
65 |     assert isinstance(products, list)
66 |     assert products
67 |     assert products[0]["name"] == "Woo Coffee"
   |     ^^^^^^ S101
   |

tests\test_product_crawl4ai_extractors.py:80:5: S101 Use of `assert` detected
   |
78 |     }
79 |     result = shopify.standardize_shopify_product(product, "https://test.myshopify.com", "roaster123")
80 |     assert isinstance(result, dict)
   |     ^^^^^^ S101
81 |     assert result["name"] == "No Tags Coffee"
82 |     assert "prices" in result
   |

tests\test_product_crawl4ai_extractors.py:81:5: S101 Use of `assert` detected
   |
79 |     result = shopify.standardize_shopify_product(product, "https://test.myshopify.com", "roaster123")
80 |     assert isinstance(result, dict)
81 |     assert result["name"] == "No Tags Coffee"
   |     ^^^^^^ S101
82 |     assert "prices" in result
   |

tests\test_product_crawl4ai_extractors.py:82:5: S101 Use of `assert` detected
   |
80 |     assert isinstance(result, dict)
81 |     assert result["name"] == "No Tags Coffee"
82 |     assert "prices" in result
   |     ^^^^^^ S101
   |

tests\test_product_crawl4ai_extractors.py:93:5: S101 Use of `assert` detected
   |
91 |     }
92 |     result = woocommerce.standardize_woocommerce_product(woo_product, "https://test.com", "roaster456")
93 |     assert isinstance(result, dict)
   |     ^^^^^^ S101
94 |     assert result["name"] == "No Tags Woo"
95 |     assert "prices" in result
   |

tests\test_product_crawl4ai_extractors.py:94:5: S101 Use of `assert` detected
   |
92 |     result = woocommerce.standardize_woocommerce_product(woo_product, "https://test.com", "roaster456")
93 |     assert isinstance(result, dict)
94 |     assert result["name"] == "No Tags Woo"
   |     ^^^^^^ S101
95 |     assert "prices" in result
   |

tests\test_product_crawl4ai_extractors.py:95:5: S101 Use of `assert` detected
   |
93 |     assert isinstance(result, dict)
94 |     assert result["name"] == "No Tags Woo"
95 |     assert "prices" in result
   |     ^^^^^^ S101
   |

tests\test_product_crawl4ai_extractors.py:103:5: S101 Use of `assert` detected
    |
101 |     tags = ["Espresso", "Limited Edition"]
102 |     roast = shopify.extract_roast_level_from_shopify(product, tags)
103 |     assert isinstance(roast, str)
    |     ^^^^^^ S101
104 |     assert "espresso" in roast.lower() or roast
    |

tests\test_product_crawl4ai_extractors.py:104:5: S101 Use of `assert` detected
    |
102 |     roast = shopify.extract_roast_level_from_shopify(product, tags)
103 |     assert isinstance(roast, str)
104 |     assert "espresso" in roast.lower() or roast
    |     ^^^^^^ S101
    |

tests\test_product_crawl4ai_extractors.py:113:5: S101 Use of `assert` detected
    |
111 |     slug = "natural-ethiopia"
112 |     method = shopify.extract_processing_method_from_shopify(product, tags, name, slug)
113 |     assert isinstance(method, str)
    |     ^^^^^^ S101
114 |     assert "natural" in method.lower() or method
    |

tests\test_product_crawl4ai_extractors.py:114:5: S101 Use of `assert` detected
    |
112 |     method = shopify.extract_processing_method_from_shopify(product, tags, name, slug)
113 |     assert isinstance(method, str)
114 |     assert "natural" in method.lower() or method
    |     ^^^^^^ S101
    |

tests\test_product_crawl4ai_scraper.py:218:5: S101 Use of `assert` detected
    |
216 |     mock_cache_products.assert_not_called()  # Not called because data came from cache
217 |
218 |     assert len(results) == 1
    |     ^^^^^^ S101
219 |     assert results[0] == MOCKED_COFFEE_MODEL_1
    |

tests\test_product_crawl4ai_scraper.py:219:5: S101 Use of `assert` detected
    |
218 |     assert len(results) == 1
219 |     assert results[0] == MOCKED_COFFEE_MODEL_1
    |     ^^^^^^ S101
    |

tests\test_product_crawl4ai_scraper.py:392:5: S101 Use of `assert` detected
    |
390 |     )
391 |
392 |     assert results == []
    |     ^^^^^^ S101
393 |     mock_enrich.assert_not_called()
394 |     mock_cache_products.assert_not_called()  # Cache should not be called if no products
    |

tests\test_product_crawl4ai_scraper.py:419:5: S101 Use of `assert` detected
    |
417 |     )
418 |
419 |     assert results == []
    |     ^^^^^^ S101
420 |     mock_is_coffee.assert_called_once_with(
421 |         RAW_PRODUCT_1.get("name", ""),
    |

tests\test_product_crawl4ai_scraper.py:457:5: S101 Use of `assert` detected
    |
455 |     )
456 |
457 |     assert results == []
    |     ^^^^^^ S101
458 |     mock_enrich.assert_called_once_with(RAW_PRODUCT_1, SAMPLE_ROASTER_NAME)
459 |     mock_validate.assert_called_once_with(ENRICHED_PRODUCT_1)
    |

tests\test_roasters_crawl4ai_batch.py:28:9: S101 Use of `assert` detected
   |
26 |             roaster_list, concurrency=2, rate_limit=10, rate_period=60, export_path=str(export_path)
27 |         )
28 |         assert len(results) == 2
   |         ^^^^^^ S101
29 |         for r in results:
30 |             assert r["name"].startswith("Roaster")
   |

tests\test_roasters_crawl4ai_batch.py:30:13: S101 Use of `assert` detected
   |
28 |         assert len(results) == 2
29 |         for r in results:
30 |             assert r["name"].startswith("Roaster")
   |             ^^^^^^ S101
31 |         mock_cache_roaster.assert_called()
32 |         mock_export_json.assert_called_once()
   |

tests\test_roasters_crawl4ai_crawler.py:41:5: S101 Use of `assert` detected
   |
39 |     crawler = RoasterCrawler()
40 |     result = await crawler.extract_roaster("Test Roaster", "https://test.com")
41 |     assert result["name"] == "Test Roaster"
   |     ^^^^^^ S101
42 |     assert result["website_url"] == "https://test.com"
43 |     assert result["country"] == "India"
   |

tests\test_roasters_crawl4ai_crawler.py:42:5: S101 Use of `assert` detected
   |
40 |     result = await crawler.extract_roaster("Test Roaster", "https://test.com")
41 |     assert result["name"] == "Test Roaster"
42 |     assert result["website_url"] == "https://test.com"
   |     ^^^^^^ S101
43 |     assert result["country"] == "India"
44 |     assert result["is_active"] is True
   |

tests\test_roasters_crawl4ai_crawler.py:43:5: S101 Use of `assert` detected
   |
41 |     assert result["name"] == "Test Roaster"
42 |     assert result["website_url"] == "https://test.com"
43 |     assert result["country"] == "India"
   |     ^^^^^^ S101
44 |     assert result["is_active"] is True
45 |     assert result["is_verified"] is False
   |

tests\test_roasters_crawl4ai_crawler.py:44:5: S101 Use of `assert` detected
   |
42 |     assert result["website_url"] == "https://test.com"
43 |     assert result["country"] == "India"
44 |     assert result["is_active"] is True
   |     ^^^^^^ S101
45 |     assert result["is_verified"] is False
46 |     assert "slug" in result
   |

tests\test_roasters_crawl4ai_crawler.py:45:5: S101 Use of `assert` detected
   |
43 |     assert result["country"] == "India"
44 |     assert result["is_active"] is True
45 |     assert result["is_verified"] is False
   |     ^^^^^^ S101
46 |     assert "slug" in result
47 |     assert "domain" in result
   |

tests\test_roasters_crawl4ai_crawler.py:46:5: S101 Use of `assert` detected
   |
44 |     assert result["is_active"] is True
45 |     assert result["is_verified"] is False
46 |     assert "slug" in result
   |     ^^^^^^ S101
47 |     assert "domain" in result
   |

tests\test_roasters_crawl4ai_crawler.py:47:5: S101 Use of `assert` detected
   |
45 |     assert result["is_verified"] is False
46 |     assert "slug" in result
47 |     assert "domain" in result
   |     ^^^^^^ S101
   |

tests\test_roasters_crawl4ai_crawler.py:61:5: S101 Use of `assert` detected
   |
59 |     crawler = RoasterCrawler()
60 |     result = await crawler.extract_roaster("Test Roaster", "https://test.com")
61 |     assert result["description"] == "desc"
   |     ^^^^^^ S101
62 |     assert result["founded_year"] == 2020
63 |     assert result["address"] == "addr"
   |

tests\test_roasters_crawl4ai_crawler.py:62:5: S101 Use of `assert` detected
   |
60 |     result = await crawler.extract_roaster("Test Roaster", "https://test.com")
61 |     assert result["description"] == "desc"
62 |     assert result["founded_year"] == 2020
   |     ^^^^^^ S101
63 |     assert result["address"] == "addr"
   |

tests\test_roasters_crawl4ai_crawler.py:63:5: S101 Use of `assert` detected
   |
61 |     assert result["description"] == "desc"
62 |     assert result["founded_year"] == 2020
63 |     assert result["address"] == "addr"
   |     ^^^^^^ S101
   |

tests\test_roasters_crawl4ai_enricher.py:19:5: S101 Use of `assert` detected
   |
17 |     enricher.enrichment_service.enhance_roaster_description = AsyncMock(return_value=enriched)
18 |     result = await enricher.enrich_missing_fields(roaster_data)
19 |     assert result["description"] == "A great roaster"
   |     ^^^^^^ S101
20 |     assert result["founded_year"] == 2020
21 |     assert result["address"] == "123 Brew St"
   |

tests\test_roasters_crawl4ai_enricher.py:20:5: S101 Use of `assert` detected
   |
18 |     result = await enricher.enrich_missing_fields(roaster_data)
19 |     assert result["description"] == "A great roaster"
20 |     assert result["founded_year"] == 2020
   |     ^^^^^^ S101
21 |     assert result["address"] == "123 Brew St"
   |

tests\test_roasters_crawl4ai_enricher.py:21:5: S101 Use of `assert` detected
   |
19 |     assert result["description"] == "A great roaster"
20 |     assert result["founded_year"] == 2020
21 |     assert result["address"] == "123 Brew St"
   |     ^^^^^^ S101
   |

tests\test_roasters_crawl4ai_enricher.py:31:5: S101 Use of `assert` detected
   |
29 |     result = await enricher.enrich_missing_fields(roaster_data)
30 |     mock.assert_not_called()
31 |     assert result == roaster_data
   |     ^^^^^^ S101
   |

tests\test_roasters_crawl4ai_enricher.py:41:5: S101 Use of `assert` detected
   |
39 |     result = await enricher.enrich_missing_fields(roaster_data)
40 |     mock.assert_not_called()
41 |     assert result == roaster_data
   |     ^^^^^^ S101
   |

tests\test_roasters_crawl4ai_enricher.py:49:5: S101 Use of `assert` detected
   |
47 |     enricher.enrichment_service.enhance_roaster_description = AsyncMock(side_effect=Exception("LLM error"))
48 |     result = await enricher.enrich_missing_fields(roaster_data)
49 |     assert result == roaster_data
   |     ^^^^^^ S101
   |

tests\test_roasters_crawl4ai_platform_pages.py:11:5: S101 Use of `assert` detected
   |
 9 |     # Shopify about
10 |     about = get_platform_page_paths("shopify", "about")
11 |     assert "/pages/about" in about
   |     ^^^^^^ S101
12 |     # Shopify contact
13 |     contact = get_platform_page_paths("shopify", "contact")
   |

tests\test_roasters_crawl4ai_platform_pages.py:14:5: S101 Use of `assert` detected
   |
12 |     # Shopify contact
13 |     contact = get_platform_page_paths("shopify", "contact")
14 |     assert "/pages/contact" in contact
   |     ^^^^^^ S101
15 |     # WooCommerce about
16 |     about_wc = get_platform_page_paths("woocommerce", "about")
   |

tests\test_roasters_crawl4ai_platform_pages.py:17:5: S101 Use of `assert` detected
   |
15 |     # WooCommerce about
16 |     about_wc = get_platform_page_paths("woocommerce", "about")
17 |     assert "/about" in about_wc
   |     ^^^^^^ S101
   |

tests\test_roasters_crawl4ai_platform_pages.py:23:5: S101 Use of `assert` detected
   |
21 |     # Unknown platform returns fallback
22 |     about = get_platform_page_paths("unknown", "about")
23 |     assert "/about" in about
   |     ^^^^^^ S101
24 |     contact = get_platform_page_paths("unknown", "contact")
25 |     assert "/contact" in contact
   |

tests\test_roasters_crawl4ai_platform_pages.py:25:5: S101 Use of `assert` detected
   |
23 |     assert "/about" in about
24 |     contact = get_platform_page_paths("unknown", "contact")
25 |     assert "/contact" in contact
   |     ^^^^^^ S101
   |

tests\test_roasters_crawl4ai_platform_pages.py:31:5: S101 Use of `assert` detected
   |
29 |     # No platform returns fallback
30 |     about = get_platform_page_paths(page_type="about")
31 |     assert "/about-us" in about
   |     ^^^^^^ S101
32 |     contact = get_platform_page_paths(page_type="contact")
33 |     assert "/contact-us" in contact
   |

tests\test_roasters_crawl4ai_platform_pages.py:33:5: S101 Use of `assert` detected
   |
31 |     assert "/about-us" in about
32 |     contact = get_platform_page_paths(page_type="contact")
33 |     assert "/contact-us" in contact
   |     ^^^^^^ S101
   |

tests\test_roasters_crawl4ai_platform_pages.py:38:5: S101 Use of `assert` detected
   |
36 | def test_get_platform_page_paths_invalid_type():
37 |     # Invalid type returns empty list
38 |     assert get_platform_page_paths("shopify", "foo") == []
   |     ^^^^^^ S101
39 |     assert get_platform_page_paths(page_type="foo") == []
   |

tests\test_roasters_crawl4ai_platform_pages.py:39:5: S101 Use of `assert` detected
   |
37 |     # Invalid type returns empty list
38 |     assert get_platform_page_paths("shopify", "foo") == []
39 |     assert get_platform_page_paths(page_type="foo") == []
   |     ^^^^^^ S101
   |

tests\test_roasters_crawl4ai_run.py:16:9: S101 Use of `assert` detected
   |
14 |         mock_extract.return_value = {"name": "Test", "website_url": "https://r.com"}
15 |         result = await run.process_single("Test", "https://r.com")
16 |         assert result["name"] == "Test"
   |         ^^^^^^ S101
17 |         assert result["website_url"] == "https://r.com"
   |

tests\test_roasters_crawl4ai_run.py:17:9: S101 Use of `assert` detected
   |
15 |         result = await run.process_single("Test", "https://r.com")
16 |         assert result["name"] == "Test"
17 |         assert result["website_url"] == "https://r.com"
   |         ^^^^^^ S101
   |

tests\test_roasters_crawl4ai_run.py:32:9: S101 Use of `assert` detected
   |
30 |         ]
31 |         results, errors = await run.process_csv_batch(str(csv_path), str(output_path), limit=None, concurrency=2)
32 |         assert len(results) == 2
   |         ^^^^^^ S101
33 |         assert errors == []
34 |         mock_batch.assert_called_once()
   |

tests\test_roasters_crawl4ai_run.py:33:9: S101 Use of `assert` detected
   |
31 |         results, errors = await run.process_csv_batch(str(csv_path), str(output_path), limit=None, concurrency=2)
32 |         assert len(results) == 2
33 |         assert errors == []
   |         ^^^^^^ S101
34 |         mock_batch.assert_called_once()
   |

tests\test_roasters_crawl4ai_run.py:51:9: S101 Use of `assert` detected
   |
49 |         mock_batch.return_value = []
50 |         results, errors = await run.process_csv_batch(str(csv_path))
51 |         assert results == []
   |         ^^^^^^ S101
52 |         assert len(errors) == 2
   |

tests\test_roasters_crawl4ai_run.py:52:9: S101 Use of `assert` detected
   |
50 |         results, errors = await run.process_csv_batch(str(csv_path))
51 |         assert results == []
52 |         assert len(errors) == 2
   |         ^^^^^^ S101
   |

tests\test_roasters_crawl4ai_schemas.py:10:5: S101 Use of `assert` detected
   |
 8 | def test_contact_schema_structure():
 9 |     schema = schemas.CONTACT_SCHEMA
10 |     assert schema["name"] == "RoasterContact"
   |     ^^^^^^ S101
11 |     assert any(f["name"] == "email" for f in schema["fields"])
12 |     assert any(f["name"] == "address" for f in schema["fields"])
   |

tests\test_roasters_crawl4ai_schemas.py:11:5: S101 Use of `assert` detected
   |
 9 |     schema = schemas.CONTACT_SCHEMA
10 |     assert schema["name"] == "RoasterContact"
11 |     assert any(f["name"] == "email" for f in schema["fields"])
   |     ^^^^^^ S101
12 |     assert any(f["name"] == "address" for f in schema["fields"])
13 |     assert any(f["name"] == "instagram" for f in schema["fields"])
   |

tests\test_roasters_crawl4ai_schemas.py:12:5: S101 Use of `assert` detected
   |
10 |     assert schema["name"] == "RoasterContact"
11 |     assert any(f["name"] == "email" for f in schema["fields"])
12 |     assert any(f["name"] == "address" for f in schema["fields"])
   |     ^^^^^^ S101
13 |     assert any(f["name"] == "instagram" for f in schema["fields"])
   |

tests\test_roasters_crawl4ai_schemas.py:13:5: S101 Use of `assert` detected
   |
11 |     assert any(f["name"] == "email" for f in schema["fields"])
12 |     assert any(f["name"] == "address" for f in schema["fields"])
13 |     assert any(f["name"] == "instagram" for f in schema["fields"])
   |     ^^^^^^ S101
   |

tests\test_roasters_crawl4ai_schemas.py:18:5: S101 Use of `assert` detected
   |
16 | def test_address_schema_structure():
17 |     schema = schemas.ADDRESS_SCHEMA
18 |     assert schema["name"] == "AddressInfo"
   |     ^^^^^^ S101
19 |     assert any(f["name"] == "address" for f in schema["fields"])
20 |     assert any(f["name"] == "footer_text" for f in schema["fields"])
   |

tests\test_roasters_crawl4ai_schemas.py:19:5: S101 Use of `assert` detected
   |
17 |     schema = schemas.ADDRESS_SCHEMA
18 |     assert schema["name"] == "AddressInfo"
19 |     assert any(f["name"] == "address" for f in schema["fields"])
   |     ^^^^^^ S101
20 |     assert any(f["name"] == "footer_text" for f in schema["fields"])
   |

tests\test_roasters_crawl4ai_schemas.py:20:5: S101 Use of `assert` detected
   |
18 |     assert schema["name"] == "AddressInfo"
19 |     assert any(f["name"] == "address" for f in schema["fields"])
20 |     assert any(f["name"] == "footer_text" for f in schema["fields"])
   |     ^^^^^^ S101
   |

tests\test_roasters_crawl4ai_schemas.py:25:5: S101 Use of `assert` detected
   |
23 | def test_about_schema_structure():
24 |     schema = schemas.ABOUT_SCHEMA
25 |     assert schema["name"] == "RoasterAbout"
   |     ^^^^^^ S101
26 |     assert any(f["name"] == "meta_description" for f in schema["fields"])
27 |     assert any(f["name"] == "about_text" for f in schema["fields"])
   |

tests\test_roasters_crawl4ai_schemas.py:26:5: S101 Use of `assert` detected
   |
24 |     schema = schemas.ABOUT_SCHEMA
25 |     assert schema["name"] == "RoasterAbout"
26 |     assert any(f["name"] == "meta_description" for f in schema["fields"])
   |     ^^^^^^ S101
27 |     assert any(f["name"] == "about_text" for f in schema["fields"])
   |

tests\test_roasters_crawl4ai_schemas.py:27:5: S101 Use of `assert` detected
   |
25 |     assert schema["name"] == "RoasterAbout"
26 |     assert any(f["name"] == "meta_description" for f in schema["fields"])
27 |     assert any(f["name"] == "about_text" for f in schema["fields"])
   |     ^^^^^^ S101
   |

tests\test_roasters_crawl4ai_schemas.py:33:9: S101 Use of `assert` detected
   |
31 |     schema = schemas.ROASTER_LLM_SCHEMA
32 |     for key in ["description", "founded_year", "has_subscription", "city", "address"]:
33 |         assert key in schema
   |         ^^^^^^ S101
34 |     assert schema["founded_year"]["type"] == "integer"
35 |     assert schema["description"]["type"] == "string"
   |

tests\test_roasters_crawl4ai_schemas.py:34:5: S101 Use of `assert` detected
   |
32 |     for key in ["description", "founded_year", "has_subscription", "city", "address"]:
33 |         assert key in schema
34 |     assert schema["founded_year"]["type"] == "integer"
   |     ^^^^^^ S101
35 |     assert schema["description"]["type"] == "string"
   |

tests\test_roasters_crawl4ai_schemas.py:35:5: S101 Use of `assert` detected
   |
33 |         assert key in schema
34 |     assert schema["founded_year"]["type"] == "integer"
35 |     assert schema["description"]["type"] == "string"
   |     ^^^^^^ S101
   |

tests\test_roasters_crawl4ai_schemas.py:40:5: S101 Use of `assert` detected
   |
38 | def test_roaster_llm_instructions_content():
39 |     instr = schemas.ROASTER_LLM_INSTRUCTIONS
40 |     assert "description" in instr
   |     ^^^^^^ S101
41 |     assert "founded_year" in instr
42 |     assert "address" in instr
   |

tests\test_roasters_crawl4ai_schemas.py:41:5: S101 Use of `assert` detected
   |
39 |     instr = schemas.ROASTER_LLM_INSTRUCTIONS
40 |     assert "description" in instr
41 |     assert "founded_year" in instr
   |     ^^^^^^ S101
42 |     assert "address" in instr
43 |     assert "Return values as a JSON object" in instr
   |

tests\test_roasters_crawl4ai_schemas.py:42:5: S101 Use of `assert` detected
   |
40 |     assert "description" in instr
41 |     assert "founded_year" in instr
42 |     assert "address" in instr
   |     ^^^^^^ S101
43 |     assert "Return values as a JSON object" in instr
   |

tests\test_roasters_crawl4ai_schemas.py:43:5: S101 Use of `assert` detected
   |
41 |     assert "founded_year" in instr
42 |     assert "address" in instr
43 |     assert "Return values as a JSON object" in instr
   |     ^^^^^^ S101
   |

tests\test_supabase_serialization.py:51:5: S101 Use of `assert` detected
   |
49 | def test_model_to_dict_serialization(model, expected):
50 |     result = SupabaseClient.model_to_dict(model)
51 |     assert result == expected
   |     ^^^^^^ S101
   |

tests\test_supabase_serialization.py:62:5: S101 Use of `assert` detected
   |
60 |     m = Model(number=5, flag=True)
61 |     result = SupabaseClient.model_to_dict(m)
62 |     assert result == {"number": 5, "flag": True, "none_val": None}
   |     ^^^^^^ S101
   |

tests\test_supabase_serialization.py:72:5: S101 Use of `assert` detected
   |
70 |     m = Model()
71 |     result = SupabaseClient.model_to_dict(m)
72 |     assert result == {"url": None, "nested": None}
   |     ^^^^^^ S101
   |

Found 173 errors.

```

## Action Plan (In Order of Priority)

1. **FIRST**: Fix duplicate `run_product_scraper.py` files
2. **SECOND**: Resolve any common/ function conflicts
3. **THIRD**: Fix MyPy type issues in priority files
4. **FOURTH**: Run ruff auto-fixes
5. **FIFTH**: Clean up remaining linting issues

### Auto-Fix Commands:
```bash
# Fix basic ruff issues
ruff check --fix .

# Fix import organization
ruff check --select I --fix .

# Format everything
ruff format .

# Re-run this analyzer
python ultimate_checker.py
```