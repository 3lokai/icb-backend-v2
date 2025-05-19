# Roaster Data Points: Analysis and Scraping Strategy

## Core Data Fields

| Field | Purpose | Stability | Scraping Strategy |
|-------|---------|-----------|-------------------|
| **id** | Unique database identifier (UUID) | Permanent | Generated on database insert |
| **name** | Roaster's business name | Highly Stable | Primarily from input, verified against website title |
| **slug** | URL-friendly version of name | Highly Stable | Generated from name |
| **website_url** | Roaster's website | Moderately Stable | Primarily from input, check for permanent redirects |
| **description** | About the company | Moderately Stable | Extract from About page, homepage, or meta description |
| **country** | Country location | Highly Stable | Default to "India" or extract from address sections |
| **city** | City location | Moderately Stable | Extract from contact/about pages |
| **state** | State/region location | Moderately Stable | Extract from contact/about pages |
| **founded_year** | Year established | Highly Stable | Extract from about page with pattern matching |
| **logo_url** | Company logo image | Moderately Stable | Extract main logo from header or footer |
| **image_url** | Banner/hero image | Variable | Extract hero image from homepage |
| **contact_email** | Primary contact email | Variable | Extract from contact page or footer |
| **contact_phone** | Contact phone number | Variable | Extract from contact page or footer |
| **social_links** | Array of social media URLs | Variable | Extract from footer or header social icons |
| **instagram_handle** | Instagram username | Variable | Extract from Instagram URL or social links |
| **has_subscription** | Offers subscription service | Variable | Detect from product listings or keywords |
| **has_physical_store** | Has retail location | Moderately Stable | Detect from contact/about pages, location markers |
| **platform** | E-commerce platform used | Moderately Stable | Detect from page source, headers, CSS classes |
| **tags** | Categorization array | Variable | Generated from product types and site keywords |
| **is_active** | Website accessibility status | Variable | Check if website is responding with valid content |
| **is_verified** | Manual verification status | Not Scraped | Set manually after verification process |
| **created_at** | Record creation timestamp | Not Scraped | Generated on database insert |
| **updated_at** | Record update timestamp | Not Scraped | Generated on database update |

## Stability Categories

### Highly Stable (Annual Check)
- **name**: Business names rarely change except in rebranding
- **slug**: Derived from name, changes only with rebranding
- **founded_year**: Historical fact, doesn't change
- **country**: Location changes are rare and significant

### Moderately Stable (Quarterly Check)
- **website_url**: May change with domain changes or redirects
- **description**: Updates during rebrands or marketing refreshes
- **city/state**: Changes with physical relocation only
- **logo_url**: Changes with rebranding
- **has_physical_store**: Changes with business expansion
- **platform**: Changes with website rebuilds (major technical change)

### Variable (Monthly Check)
- **image_url**: Banner images update with marketing campaigns
- **contact_email/phone**: Updates with staffing or system changes
- **social_links**: New platforms or handle changes
- **instagram_handle**: Marketing changes
- **has_subscription**: Service offering changes
- **tags**: Marketing and positioning changes
- **is_active**: Website availability may change if business closes or site undergoes major renovation

### Not Scraped (System Generated)
- **id**: Database-generated UUID
- **is_verified**: Set through verification workflow
- **created_at/updated_at**: Database timestamps

## Scraping Strategies

### For Roaster Name & Basic Info
```python
def extract_roaster_name(soup, url):
    """Extract roaster name from various sources with fallbacks."""
    # Strategy 1: From page title
    if soup.title:
        title = soup.title.text.strip()
        # Clean up title (remove suffix like "- Home" or "- Coffee Roaster")
        title = re.sub(r'\s+[-|]\s+.*$', '', title)
        return title
    
    # Strategy 2: From logo alt text
    logo = soup.select_one('header img, .logo img')
    if logo and logo.get('alt'):
        return logo['alt'].strip()
    
    # Strategy 3: From domain name
    domain = urlparse(url).netloc
    domain = re.sub(r'^www\.', '', domain)
    domain = domain.split('.')[0]
    return domain.replace('-', ' ').title()
```

### For Description
```python
def extract_roaster_description(soup):
    """Extract roaster description with multiple fallback strategies."""
    # Strategy 1: Meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content', '').strip():
        return meta_desc['content'].strip()
    
    # Strategy 2: About section on homepage
    about_section = soup.select_one('.about-us, #about, [class*=about]')
    if about_section:
        paragraphs = about_section.select('p')
        if paragraphs:
            return ' '.join(p.text.strip() for p in paragraphs[:2])
    
    # Strategy 3: First substantial paragraph
    for p in soup.select('main p, .content p'):
        if len(p.text.strip()) > 100:
            return p.text.strip()
    
    return None  # No good description found
```

### For Founded Year
```python
def check_site_activity(url):
    """Check if a website is active and accessible."""
    try:
        # First try a HEAD request (faster)
        response = requests.head(
            url, 
            timeout=10,
            allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        
        # If HEAD request fails, try a GET
        if response.status_code >= 400:
            response = requests.get(
                url,
                timeout=10,
                allow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
        
        # Site is active if we get a successful status code
        is_active = response.status_code < 400
        
        # Check if site redirected to a new domain
        final_url = response.url
        url_changed = final_url != url
        
        return {
            "is_active": is_active,
            "status_code": response.status_code,
            "url_changed": url_changed,
            "final_url": final_url if url_changed else url
        }
    except Exception as e:
        # Log the specific error type
        return {
            "is_active": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "url_changed": False,
            "final_url": url
        }
```

## Platform Detection
```python
def detect_platform(soup, html_content):
    """Detect the e-commerce platform used by a website."""
    # Shopify indicators
    if soup.find('script', src=lambda x: x and 'cdn.shopify.com' in x):
        return 'shopify'
    if 'Shopify.theme' in html_content:
        return 'shopify'
        
    # WooCommerce indicators
    if soup.find('body', class_=lambda c: c and 'woocommerce' in c):
        return 'woocommerce'
    if soup.find('link', href=lambda x: x and 'woocommerce' in x):
        return 'woocommerce'
        
    # WordPress (not WooCommerce)
    if soup.find('meta', attrs={"name": "generator", "content": lambda x: x and 'WordPress' in x}):
        return 'wordpress'
        
    # Other common platforms
    if 'Webflow' in html_content:
        return 'webflow'
    if 'Squarespace' in html_content:
        return 'squarespace'
    if 'Wix' in html_content:
        return 'wix'
        
    return 'static'  # Default fallback
```

## Incremental Update Strategy

For optimizing scraping operations, use differential updates based on field stability:

1. **Initial Scrape**: 
   - Collect all available data points
   - Store with high confidence

2. **Regular Updates (Monthly)**:
   - Always check variable fields
   - Verify only if moderately stable fields are older than 3 months
   - Verify only if highly stable fields are older than 1 year
   - Mark fields with last_checked date
   - Verify website accessibility and update is_active status

3. **Change Detection**:
   - Only update database when field value has actually changed
   - Log all changes with before/after values
   - Update confidence score based on consistency
   - Track site accessibility over time

4. **Confidence Scoring**:
   - Track extraction confidence for each field (1-10)
   - Increase confidence when value remains consistent across scrapes
   - Lower confidence when frequent changes occur
   - Flag fields with low confidence for manual review

By implementing this layered approach to data stability, the scraper can focus computational resources on fields most likely to change while maintaining accuracy for critical business information.