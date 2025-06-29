# **Coffee Scraper Fix-It Plan - Tomorrow**
*Goal: Get your existing codebase running smoothly*

## **🎯 Session Overview (2-3 hours total)**

### **Session 1: Quick Fixes (30 minutes)**
**Goal:** Get basic imports working

#### **Fix 1: Missing Functions (15 minutes)**
```python
# common/utils.py - Add this line
def create_slug(text):
    return slugify(text)

# common/pydantic_utils.py - Add these functions  
def dict_to_pydantic_model(data, model_class, preprocessor=None):
    # Implementation
    
def preprocess_coffee_data(data):
    return data

# common/cache.py - Add module exports at bottom
_cache = ScraperCache()
def cache_products(roaster_id, products):
    return _cache.cache_products(roaster_id, products)
def get_cached_products(roaster_id, max_age_days=7):
    return _cache.get_cached_products(roaster_id, max_age_days)
```

#### **Fix 2: Variable Name Typos (5 minutes)**
```python
# shopify.py line 680 - Fix this:
return lower["price"] + (size_ratio * price_diff)  # ✅ Fixed

# woocommerce.py line 873 - Fix this: 
return lower["price"] + (size_ratio * price_diff)  # ✅ Fixed
```

#### **Fix 3: Missing Function (10 minutes)**
```python
# shopify.py - Add this function
def extract_brew_methods_from_grind_size(grind_size):
    # Simple implementation
```

---

### **Session 2: File Understanding (45 minutes)**
**Goal:** Map out what each file actually does

#### **Core Files Review (15 minutes each)**
1. **`main.py`** - Understand CLI commands and async handling
2. **`scrapers/product_crawl4ai/scraper.py`** - Main product scraping logic  
3. **`scrapers/roasters_crawl4ai/crawler.py`** - Main roaster scraping logic

**For each file, document:**
- What's the main function?
- What does it return? 
- What are the key dependencies?
- Any obvious issues?

---

### **Session 3: Test One Complete Flow (30 minutes)**
**Goal:** Get ONE roaster working end-to-end

#### **Pick Blue Tokai and trace through:**
```python
# Test this exact flow:
python main.py detect https://bluetokai.com
python main.py scrape-roaster "Blue Tokai,https://bluetokai.com"  
python main.py scrape-products https://bluetokai.com
```

**Document what breaks and where**

---

### **Session 4: Logic Review & Fixes (45 minutes)**
**Goal:** Fix broken logic and merge duplicates

#### **Common Issues to Look For:**
- Functions doing the same thing in different files
- Complex functions that should be split up
- Missing error handling
- Async/sync mixing issues

#### **Priority Fixes:**
1. **Duplicate code** - merge similar extraction logic
2. **Error handling** - add try/catch where missing  
3. **Data flow** - ensure data passes correctly between functions
4. **Type issues** - fix obvious Pydantic model mismatches

---

## **🚨 Session Rules**

### **Stay Focused:**
- ✅ **Fix existing code** - don't rewrite
- ✅ **One file at a time** - don't jump around
- ✅ **Test after each fix** - make sure it still runs
- ✅ **Document what we find** - understand before changing

### **Success Criteria:**
- [ ] All imports work (no ModuleNotFoundError)
- [ ] Can run `python main.py detect <url>` without errors
- [ ] Can scrape at least ONE roaster completely
- [ ] Data actually appears in Supabase
- [ ] Understand the overall data flow

### **If We Get Stuck:**
- **Option A:** Fix the specific error and move on
- **Option B:** Skip that piece and test other parts
- **Option C:** Simplify the failing function temporarily

---

## **📝 Prep for Tomorrow**

### **Before We Start:**
1. Make sure you can run `python main.py --help`
2. Have a test roaster URL ready (Blue Tokai?)
3. Supabase credentials working