# Coffee Product Data Points: Analysis and Scraping Strategy

## Core Data Fields

| Field | Purpose | Stability | Scraping Strategy |
|-------|---------|-----------|-------------------|
| **id** | Unique database identifier (UUID) | Permanent | Generated on database insert |
| **name** | Coffee product name | Highly Stable | Extract from product page heading |
| **slug** | URL-friendly version of name | Highly Stable | Generated from name |
| **roaster_id** | Reference to roaster | Highly Stable | Foreign key from roaster table |
| **description** | Product description | Moderately Stable | Extract from product details |
| **roast_level** | Roasting darkness (enum) | Moderately Stable | Extract from attributes or description |
| **bean_type** | Coffee bean variety (enum) | Highly Stable | Extract from attributes or description |
| **processing_method** | Bean processing technique | Highly Stable | Extract from attributes or description |
| **region_id** | Coffee origin region | Highly Stable | Foreign key from regions table |
| **image_url** | Product image | Variable | Extract from product page media |
| **direct_buy_url** | Purchase page URL | Moderately Stable | URL of product page |
| **is_seasonal** | Limited seasonal offering | Variable | Detect from description or tags |
| **is_single_origin** | Single vs blend | Highly Stable | Detect from product name or description |
| **is_available** | Current stock status | Highly Variable | Extract from stock status indicator |
| **is_featured** | Internally featured | Not Scraped | Set manually for platform |
| **tags** | Categorization array | Variable | Extract from product page tags |
| **deepseek_enriched** | AI-enhanced flag | Not Scraped | Set based on enrichment process |
| **price_250g** | Normalized price | Calculated | Calculated by Supabase trigger |
| **created_at** | Record creation timestamp | Not Scraped | Generated on database insert |
| **updated_at** | Record update timestamp | Not Scraped | Generated on database update |

## Related Tables

### Coffee Prices

| Field | Purpose | Stability | Scraping Strategy |
|-------|---------|-----------|-------------------|
| **coffee_id** | Reference to coffee | Highly Stable | Foreign key from coffee table |
| **size_grams** | Package size in grams | Moderately Stable | Extract from product variants |
| **price** | Price for this size | Variable | Extract from product variants pricing |

### Coffee Brew Methods

| Field | Purpose | Stability | Scraping Strategy |
|-------|---------|-----------|-------------------|
| **coffee_id** | Reference to coffee | Highly Stable | Foreign key from coffee table |
| **brew_method_id** | Reference to brew method | Highly Stable | Foreign key from lookup table |

### Coffee Flavor Profiles

| Field | Purpose | Stability | Scraping Strategy |
|-------|---------|-----------|-------------------|
| **coffee_id** | Reference to coffee | Highly Stable | Foreign key from coffee table |
| **flavor_profile_id** | Reference to flavor | Highly Stable | Foreign key from lookup table |

### External Links

| Field | Purpose | Stability | Scraping Strategy |
|-------|---------|-----------|-------------------|
| **id** | Unique identifier | Permanent | Generated on database insert |
| **coffee_id** | Reference to coffee | Highly Stable | Foreign key from coffee table |
| **provider** | Marketplace name | Highly Stable | Identify from URL pattern |
| **url** | External purchase URL | Variable | Extract from product page links |

## Stability Categories

### Highly Stable (Annual Check)
- **name**: Product names rarely change
- **slug**: Derived from name
- **roaster_id**: Relationship to roaster
- **bean_type**: Intrinsic characteristic of the product
- **processing_method**: Production characteristic
- **region_id**: Origin location
- **is_single_origin**: Fundamental product characteristic

### Moderately Stable (Quarterly Check)
- **description**: Updates with marketing refreshes
- **roast_level**: May change with recipe adjustments
- **direct_buy_url**: Changes with website restructuring

### Variable (Monthly Check)
- **image_url**: Updated with new photography
- **is_seasonal**: Changes with availability
- **tags**: Product categorization updates
- **price**: All price points in coffee_prices table

### Highly Variable (Weekly Check)
- **is_available**: Stock status changes frequently

### Not Scraped (System Generated)
- **id**: Database-generated UUID
- **is_featured**: Set manually for the platform
- **deepseek_enriched**: Set during enrichment process
- **created_at/updated_at**: Database timestamps
- **price_250g**: Calculated via Supabase trigger

## Scraping Strategies

### For Coffee Name & Basic Details
```python
def extract_coffee_name(soup):
    """Extract coffee product name from product page."""
    # Strategy 1: Product title heading
    product_title = soup.select_one('h1.product-title, .product-single__title, .product_title')
    if product_title:
        return product_title.text.strip()
    
    # Strategy 2: First heading in product container
    product_container = soup.select_one('.product, .product-container, [itemtype*="Product"]')
    if product_container:
        heading = product_container.select_one('h1, h2')
        if heading:
            return heading.text.strip()
    
    # Strategy 3: Page title as fallback
    if soup.title:
        title = soup.title.text
        # Remove site name suffix if present
        title = re.sub(r'\s+[-|]\s+.*$', '', title)
        return title.strip()
    
    return None
```

### For Roast Level & Bean Type
```python
def extract_roast_level(soup, description_text):
    """Extract roast level from product attributes or description."""
    # Strategy 1: Look for dedicated attribute field
    roast_attr = soup.select_one('[data-attribute="roast-level"], .roast-level, .roast_level')
    if roast_attr:
        return standardize_roast_level(roast_attr.text.strip())
    
    # Strategy 2: Check product metadata table
    metadata_table = soup.select_one('.product-metadata, .product-attributes, table.shop_attributes')
    if metadata_table:
        rows = metadata_table.select('tr')
        for row in rows:
            header = row.select_one('th, td:first-child')
            if header and 'roast' in header.text.lower():
                value = row.select_one('td:last-child')
                if value:
                    return standardize_roast_level(value.text.strip())
    
    # Strategy 3: Extract from description using patterns
    roast_patterns = [
        (r'\b(light)\s+roast\b', 'light'),
        (r'\b(medium[\s-]*light)\s+roast\b', 'medium-light'),
        (r'\b(medium)\s+roast\b', 'medium'),
        (r'\b(medium[\s-]*dark)\s+roast\b', 'medium-dark'),
        (r'\b(dark)\s+roast\b', 'dark'),
        (r'roast:?\s*(light|medium[\s-]*light|medium|medium[\s-]*dark|dark)', lambda m: m.group(1).lower())
    ]
    
    for pattern, result in roast_patterns:
        match = re.search(pattern, description_text, re.IGNORECASE)
        if match:
            if callable(result):
                return standardize_roast_level(result(match))
            return result
    
    return None  # No roast level detected
```

### For Processing Method
```python
def extract_processing_method(soup, description_text):
    """Extract coffee processing method."""
    # Strategy 1: Look for dedicated attribute field
    process_attr = soup.select_one('[data-attribute="processing-method"], .processing-method, .process_method')
    if process_attr:
        return standardize_processing_method(process_attr.text.strip())
    
    # Strategy 2: Extract from description using patterns
    process_patterns = [
        (r'\b(washed|wet)\s+process', 'washed'),
        (r'\b(natural|dry)\s+process', 'natural'),
        (r'\b(honey|pulped natural)\s+process', 'honey'),
        (r'\b(anaerobic|carbonic maceration)', 'anaerobic'),
        (r'process(?:ing)?:?\s*(washed|natural|honey|anaerobic)', lambda m: m.group(1).lower())
    ]
    
    for pattern, result in process_patterns:
        match = re.search(pattern, description_text, re.IGNORECASE)
        if match:
            if callable(result):
                return standardize_processing_method(result(match))
            return result
    
    # Strategy 3: Check if blend (might not have a processing method)
    if "blend" in description_text.lower() or "blend" in soup.select_one('h1, h2').text.lower():
        return None  # Blends often don't specify processing method
    
    return None  # No processing method detected
```

### For Price Extraction
```python
def extract_coffee_prices(soup, platform):
    """Extract coffee prices for different weights."""
    prices = []
    
    if platform == 'shopify':
        # Shopify-specific extraction
        variant_json = re.search(r'var\s+meta\s*=\s*(\{.*?\});', str(soup), re.DOTALL)
        if variant_json:
            try:
                meta_data = json.loads(variant_json.group(1))
                for variant in meta_data.get('product', {}).get('variants', []):
                    title = variant.get('name', '')
                    price = float(variant.get('price', 0)) / 100  # Shopify prices in cents
                    
                    # Extract weight from variant title
                    weight_match = re.search(r'(\d+\.?\d*)\s*(g|gram|gm|kg)', title.lower())
                    if weight_match:
                        weight = float(weight_match.group(1))
                        unit = weight_match.group(2).lower()
                        weight_grams = weight * 1000 if 'kg' in unit else weight
                        
                        prices.append({
                            'size_grams': int(weight_grams),
                            'price': price
                        })
            except json.JSONDecodeError:
                pass
    
    elif platform == 'woocommerce':
        # WooCommerce-specific extraction
        # Try to find variations JSON
        variations_json = re.search(r'var\s+product_variations\s*=\s*(\[.*?\]);', str(soup), re.DOTALL)
        if variations_json:
            try:
                variations = json.loads(variations_json.group(1))
                for variation in variations:
                    # Extract attributes
                    attributes = variation.get('attributes', {})
                    weight_attr = None
                    
                    # Look for weight attribute
                    for attr_name, attr_value in attributes.items():
                        if any(w in attr_name.lower() for w in ['weight', 'size', 'amount']):
                            weight_attr = attr_value
                            break
                    
                    if weight_attr and variation.get('display_price'):
                        # Extract weight from attribute value
                        weight_match = re.search(r'(\d+\.?\d*)\s*(g|gram|gm|kg)', weight_attr.lower())
                        if weight_match:
                            weight = float(weight_match.group(1))
                            unit = weight_match.group(2).lower()
                            weight_grams = weight * 1000 if 'kg' in unit else weight
                            
                            prices.append({
                                'size_grams': int(weight_grams),
                                'price': float(variation.get('display_price', 0))
                            })
            except json.JSONDecodeError:
                pass
    
    # Generic extraction (fallback for all platforms)
    if not prices:
        # Look for structured price information
        price_options = []
        
        # Strategy 1: Radio buttons or selects with weight options
        weight_options = soup.select('input[type="radio"][name*="weight"], select[name*="weight"] option')
        for option in weight_options:
            option_text = option.get('value', '') or option.text
            if not option_text:
                continue
                
            # Try to find associated price
            price_text = None
            label = soup.select_one(f'label[for="{option.get("id", "")}"]')
            if label:
                price_match = re.search(r'([$€£₹]\s*[\d,.]+)', label.text)
                if price_match:
                    price_text = price_match.group(1)
            
            # If no price in label, look for data attributes
            if not price_text and option.get('data-price'):
                price_text = option.get('data-price')
            
            # Extract weight and price
            weight_match = re.search(r'(\d+\.?\d*)\s*(g|gram|gm|kg)', option_text.lower())
            price_match = re.search(r'[\d,.]+', price_text) if price_text else None
            
            if weight_match and price_match:
                weight = float(weight_match.group(1))
                unit = weight_match.group(2).lower()
                weight_grams = weight * 1000 if 'kg' in unit else weight
                price = float(price_match.group(0).replace(',', ''))
                
                price_options.append({
                    'size_grams': int(weight_grams),
                    'price': price
                })
        
        if price_options:
            prices = price_options
    
    return prices
```

### For Flavor Profiles
```python
def extract_flavor_profiles(soup, description_text):
    """Extract flavor profiles from product description."""
    # Common flavor profiles in coffee
    known_flavors = [
        "chocolate", "cocoa", "nutty", "nuts", "almond", "hazelnut",
        "caramel", "toffee", "butterscotch", "fruity", "berry", "blueberry", 
        "strawberry", "cherry", "citrus", "lemon", "orange", "lime",
        "floral", "jasmine", "rose", "spice", "cinnamon", "vanilla",
        "earthy", "woody", "tobacco", "cedar", "honey", "maple",
        "malt", "molasses", "stone fruit", "peach", "apricot", "plum",
        "tropical", "pineapple", "mango", "coconut", "apple", "pear",
        "wine", "winey", "grapes", "blackcurrant", "melon", "herbal"
    ]
    
    # Strategy 1: Look for dedicated flavor notes section
    flavor_section = soup.select_one('.flavor-notes, .tasting-notes, .flavor-profile')
    if flavor_section:
        text = flavor_section.text.lower()
        return [flavor for flavor in known_flavors if flavor in text]
    
    # Strategy 2: Extract from description text
    # First look for "notes of" or "flavors of" patterns
    notes_match = re.search(r'(?:notes|flavors|flavours|aromas)\s+of\s+([\w\s,&+]+)', description_text, re.IGNORECASE)
    if notes_match:
        notes_text = notes_match.group(1).lower()
        extracted = []
        for flavor in known_flavors:
            if flavor in notes_text:
                extracted.append(flavor)
        if extracted:
            return extracted
    
    # Strategy 3: Just look for flavor words in description
    return [flavor for flavor in known_flavors if flavor in description_text.lower()]
```

### For Brew Methods
```python
def extract_brew_methods(soup, description_text):
    """Extract recommended brew methods from product description."""
    # Common brewing methods
    known_methods = [
        "espresso", "filter", "pour over", "french press", "aeropress", 
        "cold brew", "moka pot", "siphon", "chemex", "drip", "v60",
        "kalita", "clever dripper", "immersion", "percolator", "turkish"
    ]
    
    # Strategy 1: Look for dedicated brew section
    brew_section = soup.select_one('.brew-methods, .brewing-guide, .preparation')
    if brew_section:
        text = brew_section.text.lower()
        return [method for method in known_methods if method in text]
    
    # Strategy 2: Look for "perfect for" or "ideal for" in description
    ideal_match = re.search(r'(?:perfect|ideal|great|excellent|recommended)\s+for\s+([\w\s,&+]+)', 
                           description_text, re.IGNORECASE)
    if ideal_match:
        ideal_text = ideal_match.group(1).lower()
        return [method for method in known_methods if method in ideal_text]
    
    # Strategy 3: Just look for method words in description
    return [method for method in known_methods if method in description_text.lower()]
```

### For External Links
```python
def extract_external_links(soup):
    """Extract external marketplace links."""
    external_links = []
    
    # Known marketplaces and their identifiers
    marketplaces = [
        {"name": "amazon", "pattern": r'amazon\.(in|com)'},
        {"name": "flipkart", "pattern": r'flipkart\.com'},
        {"name": "instamojo", "pattern": r'instamojo\.com'},
        {"name": "quicksell", "pattern": r'quicksell\.co'},
        {"name": "razorpay", "pattern": r'razorpay\.com'}
    ]
    
    # Find all links
    for link in soup.select('a[href]'):
        href = link.get('href', '')
        
        for marketplace in marketplaces:
            if re.search(marketplace["pattern"], href):
                external_links.append({
                    "provider": marketplace["name"],
                    "url": href
                })
                break
    
    return external_links
```

## Incremental Update Strategy

The coffee product scraper should use a staged approach for efficiency:

1. **Initial Product Listing Scan**:
   - Scrape the product listing/collection pages first
   - Extract basic information (name, URL, image)
   - Compare with existing database entries to identify:
     - New products to add
     - Potentially removed products
     - Products to update

2. **Differential Product Detail Scraping**:
   - For new products: Scrape all details
   - For existing products: Check modification indicators first
     - Price changes
     - Availability changes
     - Image changes

3. **Layered Update Strategy**:
   - **Weekly**: Update highly variable fields (is_available, prices)
   - **Monthly**: Update variable fields (image_url, tags, is_seasonal)
   - **Quarterly**: Update moderately stable fields (description, roast_level)
   - **Yearly**: Verify highly stable fields (name, processing_method, bean_type)

4. **Update Decision Logic**:
   ```python
   def should_update_field(field_name, last_updated_date, coffee):
       """Determine if a field should be updated based on its stability category."""
       today = datetime.now()
       days_since_update = (today - last_updated_date).days
       
       # Highly variable fields (check weekly)
       if field_name in ['is_available']:
           return days_since_update >= 7
           
       # Variable fields (check monthly)
       if field_name in ['image_url', 'tags', 'is_seasonal', 'external_links']:
           return days_since_update >= 30
           
       # Moderately stable fields (check quarterly)
       if field_name in ['description', 'roast_level', 'direct_buy_url']:
           return days_since_update >= 90
           
       # Highly stable fields (check yearly)
       if field_name in ['name', 'bean_type', 'processing_method', 'region_id', 'is_single_origin']:
           return days_since_update >= 365
           
       # Default to monthly updates for unspecified fields
       return days_since_update >= 30
   ```

5. **Change Detection**:
   - Only update database when values actually change
   - Log all changes with before/after values
   - Track fields that change frequently for analysis

This strategy ensures efficient use of resources while maintaining data freshness, focusing more frequent updates on the fields most likely to change.