# scrapers/product/extractors/attributes.py
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from common.utils import standardize_bean_type, standardize_processing_method, standardize_roast_level

logger = logging.getLogger(__name__)


def extract_roast_level(
    text: str, tags: Optional[List[str]] = None, structured_data: Optional[Dict[str, Any]] = None, confidence_tracking: bool = True
) -> Tuple[Optional[str], float]:
    """
    Extract coffee roast level using multiple strategies with confidence scoring.

    Args:
        text: Product description or full product text
        tags: List of product tags/categories (optional)
        structured_data: Structured product data if available (optional)
        confidence_tracking: Whether to track confidence scores

    Returns:
        Tuple of (roast_level, confidence_score)
    """
    if tags is None:
        tags = []

    # Strategy 1 (highest confidence): Check dedicated attribute in structured data
    if structured_data:
        for attr_key in ["roast_level", "roast", "roastLevel", "roast-level"]:
            if attr_key in structured_data:
                roast = structured_data[attr_key]
                if isinstance(roast, str) and roast.strip():
                    return standardize_roast_level(roast), 0.95  # Very high confidence

    # Strategy 2 (high confidence): Check product tags
    roast_patterns = [
        (r"\b(light)\s+roast\b", "light", 0.9),
        (r"\b(light[\s-]*medium)\s+roast\b", "light-medium", 0.9),
        (r"\b(medium)\s+roast\b", "medium", 0.9),
        (r"\b(medium[\s-]*dark)\s+roast\b", "medium-dark", 0.9),
        (r"\b(dark)\s+roast\b", "dark", 0.9),
        (r"\b(city[\s-]*plus|city\+)\b", "city-plus", 0.85),
        (r"\b(full[\s-]*city)\b", "full-city", 0.85),
        (r"\b(city)\b", "city", 0.8),
        (r"\b(french)\b", "french", 0.8),
        (r"\b(italian)\b", "italian", 0.8),
        (r"\b(espresso)\b", "espresso", 0.7),  # Lower confidence as espresso can be brew method too
        (r"\b(cinnamon)\b", "cinnamon", 0.8),
        (r"\b(filter)\b", "filter", 0.7),  # Lower confidence as filter can be brew method too
        (r"\b(omni[\s-]*roast)\b", "omniroast", 0.85),
    ]

    for tag in tags:
        tag_lower = tag.lower().strip()
        for pattern, roast, confidence in roast_patterns:
            if re.search(pattern, tag_lower):
                return roast, confidence

    # Strategy 3 (medium confidence): Parse description text for explicit declarations
    explicit_patterns = [
        (
            r"roast(?:ed)?\s*(?:level)?(?:\s*(?:is|:))?\s*(light|medium[\s-]*light|medium|medium[\s-]*dark|dark|city[\s-]*plus|city\+|full[\s-]*city|city|french|italian|espresso|cinnamon|filter|omni[\s-]*roast)",
            0.8,
        ),
        (
            r"(light|medium[\s-]*light|medium|medium[\s-]*dark|dark|city[\s-]*plus|city\+|full[\s-]*city|city|french|italian|cinnamon|omni[\s-]*roast)\s+roast(?:ed)?",
            0.75,
        ),
    ]

    for pattern, confidence in explicit_patterns:
        match = re.search(pattern, text.lower())
        if match:
            roast = match.group(1).strip()
            return standardize_roast_level(roast), confidence

    # Strategy 4 (lower confidence): Look for roast words in description
    roast_words = [
        ("light", "light", 0.6),
        ("medium-light", "medium-light", 0.6),
        ("medium light", "medium-light", 0.6),
        ("medium", "medium", 0.55),  # Lower confidence because "medium" is common word
        ("medium-dark", "medium-dark", 0.6),
        ("medium dark", "medium-dark", 0.6),
        ("dark", "dark", 0.55),  # Lower confidence because "dark" is common word
    ]

    for word, roast, confidence in roast_words:
        if re.search(r"\b" + re.escape(word) + r"\b", text.lower()):
            # Only return if it's likely describing the roast (context check)
            if re.search(r"\broast", text.lower()) or "profile" in text.lower():
                return roast, confidence

    # No roast level found
    return None, 0.0


def extract_bean_type(
    text: str, tags: Optional[List[str]] = None, structured_data: Optional[Dict[str, Any]] = None, confidence_tracking: bool = True
) -> Tuple[Optional[str], float]:
    """
    Extract coffee bean type using multiple strategies with confidence scoring.

    Args:
        text: Product description or full product text
        tags: List of product tags/categories (optional)
        structured_data: Structured product data if available (optional)
        confidence_tracking: Whether to track confidence scores

    Returns:
        Tuple of (bean_type, confidence_score)
    """
    if tags is None:
        tags = []

    # Strategy 1 (highest confidence): Check dedicated attribute in structured data
    if structured_data:
        for attr_key in ["bean_type", "beanType", "bean-type", "bean", "variety"]:
            if attr_key in structured_data:
                bean = structured_data[attr_key]
                if isinstance(bean, str) and bean.strip():
                    return standardize_bean_type(bean), 0.95  # Very high confidence

    # Strategy 2 (high confidence): Check product tags
    bean_patterns = [
        (r"\b(arabica)\b", "arabica", 0.9),
        (r"\b(robusta)\b", "robusta", 0.9),
        (r"\b(liberica)\b", "liberica", 0.9),
        (r"\b(blend)\b", "blend", 0.8),  # Slightly lower as "blend" can be used in other contexts
        (r"\b(arabica[\s-]*robusta)\b", "arabica-robusta", 0.9),
        (r"\b(mixed[\s-]*arabica)\b", "mixed-arabica", 0.9),
    ]

    for tag in tags:
        tag_lower = tag.lower().strip()
        for pattern, bean, confidence in bean_patterns:
            if re.search(pattern, tag_lower):
                return bean, confidence

    # Strategy 3 (medium confidence): Explicit bean type declarations in text
    # Check for specific combinations first
    if re.search(r"\barabica\b.*\brobusta\b", text.lower()) or re.search(r"\brobusta\b.*\barabica\b", text.lower()):
        return "arabica-robusta", 0.85

    explicit_patterns = [
        (r"(?:bean|coffee)(?:\s*(?:type|variety))?(?:\s*(?:is|:))?\s*((?:100%\s*)?arabica)", "arabica", 0.85),
        (r"(?:bean|coffee)(?:\s*(?:type|variety))?(?:\s*(?:is|:))?\s*((?:100%\s*)?robusta)", "robusta", 0.85),
        (r"(?:bean|coffee)(?:\s*(?:type|variety))?(?:\s*(?:is|:))?\s*((?:100%\s*)?liberica)", "liberica", 0.85),
        (r"(?:bean|coffee)(?:\s*(?:type|variety))?(?:\s*(?:is|:))?\s*(blend)", "blend", 0.8),
        (r"((?:100%\s*)?arabica)(?:\s*(?:bean|coffee|type|variety))?", "arabica", 0.8),
        (r"((?:100%\s*)?robusta)(?:\s*(?:bean|coffee|type|variety))?", "robusta", 0.8),
        (r"((?:100%\s*)?liberica)(?:\s*(?:bean|coffee|type|variety))?", "liberica", 0.8),
    ]

    for pattern, bean, confidence in explicit_patterns:
        if re.search(pattern, text.lower()):
            return bean, confidence

    # Strategy 4 (lower confidence): Look for varietals (these are all arabica)
    arabica_varietals = [
        "bourbon",
        "typica",
        "gesha",
        "geisha",
        "sl28",
        "sl34",
        "caturra",
        "catuai",
        "catimor",
        "pacamara",
        "maragogipe",
        "pacas",
        "villa sarchi",
        "mundo novo",
    ]

    for varietal in arabica_varietals:
        if re.search(r"\b" + re.escape(varietal) + r"\b", text.lower()):
            return "arabica", 0.75  # Lower confidence because it's inferred

    # Strategy 5 (lowest confidence): Basic keyword matching
    bean_keywords = [
        ("arabica", "arabica", 0.6),
        ("robusta", "robusta", 0.6),
        ("liberica", "liberica", 0.6),
        ("blend", "blend", 0.5),  # Lowest confidence for just the word "blend"
    ]

    for keyword, bean, confidence in bean_keywords:
        if re.search(r"\b" + re.escape(keyword) + r"\b", text.lower()):
            return bean, confidence

    # No bean type found
    return None, 0.0


def extract_processing_method(
    text: str, tags: Optional[List[str]] = None, structured_data: Optional[Dict[str, Any]] = None, confidence_tracking: bool = True
) -> Tuple[Optional[str], float]:
    """
    Extract coffee processing method using multiple strategies with confidence scoring.

    Args:
        text: Product description or full product text
        tags: List of product tags/categories (optional)
        structured_data: Structured product data if available (optional)
        confidence_tracking: Whether to track confidence scores

    Returns:
        Tuple of (processing_method, confidence_score)
    """
    if tags is None:
        tags = []

    # Strategy 1 (highest confidence): Check dedicated attribute in structured data
    if structured_data:
        for attr_key in ["processing_method", "process", "processing", "process_method"]:
            if attr_key in structured_data:
                process = structured_data[attr_key]
                if isinstance(process, str) and process.strip():
                    return standardize_processing_method(process), 0.95  # Very high confidence

    # Strategy 2 (high confidence): Check product tags
    process_patterns = [
        (r"\b(washed|wet[\s-]*process)\b", "washed", 0.9),
        (r"\b(natural|dry[\s-]*process)\b", "natural", 0.9),
        (r"\b(honey|pulped[\s-]*natural)\b", "honey", 0.9),
        (r"\b(anaerobic)\b", "anaerobic", 0.9),
        (r"\b(monsooned|monsoon[\s-]*process)\b", "monsooned", 0.9),
        (r"\b(wet[\s-]*hulled)\b", "wet-hulled", 0.9),
        (r"\b(carbonic[\s-]*maceration)\b", "carbonic-maceration", 0.9),
        (r"\b(double[\s-]*fermented)\b", "double-fermented", 0.9),
    ]

    for tag in tags:
        tag_lower = tag.lower().strip()
        for pattern, process, confidence in process_patterns:
            if re.search(pattern, tag_lower):
                return process, confidence

    # Strategy 3 (medium confidence): Explicit process declarations in text
    explicit_patterns = [
        (
            r"process(?:ing)?(?:\s*(?:method|type))?(?:\s*(?:is|:))?\s*(washed|natural|honey|anaerobic|monsooned|wet[\s-]*hulled|carbonic[\s-]*maceration|double[\s-]*fermented)",
            0.8,
        ),
        (
            r"(washed|natural|honey|anaerobic|monsooned|wet[\s-]*hulled|carbonic[\s-]*maceration|double[\s-]*fermented)(?:\s*(?:process|processing|processed))",
            0.8,
        ),
    ]

    for pattern, confidence in explicit_patterns:
        match = re.search(pattern, text.lower())
        if match:
            process = match.group(1).strip()
            return standardize_processing_method(process), confidence

    # Strategy 4 (lower confidence): General keyword matching
    process_keywords = [
        ("washed", "washed", 0.7),
        ("wet process", "washed", 0.7),
        ("natural", "natural", 0.65),  # Lower as "natural" is a common word
        ("dry process", "natural", 0.7),
        ("honey", "honey", 0.65),  # Lower as "honey" could be flavor note
        ("pulped natural", "pulped-natural", 0.7),
        ("anaerobic", "anaerobic", 0.7),
        ("monsooned", "monsooned", 0.7),
        ("monsoon malabar", "monsooned", 0.7),
        ("wet hulled", "wet-hulled", 0.7),
        ("carbonic maceration", "carbonic-maceration", 0.7),
        ("double fermented", "double-fermented", 0.7),
    ]

    for keyword, process, confidence in process_keywords:
        if re.search(r"\b" + re.escape(keyword) + r"\b", text.lower()):
            return process, confidence

    # No processing method found
    return None, 0.0


def extract_flavor_profiles(
    text: str, tags: Optional[List[str]] = None, structured_data: Optional[Dict[str, Any]] = None, confidence_tracking: bool = True
) -> Tuple[Optional[List[str]], float]:
    """
    Extract coffee flavor profiles using multiple strategies with confidence scoring.

    Args:
        text: Product description or full product text
        tags: List of product tags/categories (optional)
        structured_data: Structured product data if available (optional)
        confidence_tracking: Whether to track confidence scores

    Returns:
        Tuple of (flavor_profiles, confidence_score)
    """
    if tags is None:
        tags = []

    # Common flavor profiles in coffee
    known_flavors = [
        "chocolate",
        "cocoa",
        "nutty",
        "nuts",
        "almond",
        "hazelnut",
        "caramel",
        "toffee",
        "butterscotch",
        "fruity",
        "berry",
        "blueberry",
        "strawberry",
        "cherry",
        "citrus",
        "lemon",
        "orange",
        "lime",
        "floral",
        "jasmine",
        "rose",
        "spice",
        "cinnamon",
        "vanilla",
        "earthy",
        "woody",
        "tobacco",
        "cedar",
        "honey",
        "maple",
        "malt",
        "molasses",
        "stone fruit",
        "peach",
        "apricot",
        "plum",
        "tropical",
        "pineapple",
        "mango",
        "coconut",
        "apple",
        "pear",
        "wine",
        "winey",
        "grapes",
        "blackcurrant",
        "melon",
        "herbal",
        "roasted",
    ]

    # Strategy 1 (highest confidence): Check dedicated attribute in structured data
    if structured_data:
        for attr_key in ["flavor_profiles", "flavor_notes", "tasting_notes", "flavors"]:
            if attr_key in structured_data:
                flavors = structured_data[attr_key]
                if isinstance(flavors, list) and flavors:
                    # Keep only known flavors
                    valid_flavors = [f.lower() for f in flavors if any(kf in f.lower() for kf in known_flavors)]
                    if valid_flavors:
                        return valid_flavors, 0.95  # Very high confidence

    # Strategy 2 (high confidence): Check product tags for flavor keywords
    tag_flavors = []
    for tag in tags:
        tag_lower = tag.lower().strip()
        for flavor in known_flavors:
            if flavor in tag_lower:
                tag_flavors.append(flavor)

    if tag_flavors:
        return list(set(tag_flavors)), 0.9  # High confidence

    # Strategy 3 (medium confidence): Look for "notes of" or "flavors of" patterns
    notes_match = re.search(r"(?:notes|flavors|flavours|aromas|tasting\s*profile)\s+of\s+([\w\s,&+]+)", text.lower())
    if notes_match:
        notes_text = notes_match.group(1).lower()
        extracted = []
        for flavor in known_flavors:
            if flavor in notes_text:
                extracted.append(flavor)

        if extracted:
            return list(set(extracted)), 0.85  # Good confidence

    # Need to handle explicitly labeled flavor sections:
    # "FLAVOUR NOTES: Long-lasting, pleasant taste with..."
    # "Taste Notes - Juicy Mango, Mixed berries"
    flavor_section_patterns = [r"(?:FLAVOUR|FLAVOR)\s+NOTES:\s*(.*?)(?:\.|$)", r"Taste\s+Notes\s*[-:]\s*(.*?)(?:\.|$)"]
    for pattern in flavor_section_patterns:
        section_match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if section_match:
            section_text = section_match.group(1).lower()
            extracted = []
            for flavor in known_flavors:
                if flavor in section_text:
                    extracted.append(flavor)
            if extracted:
                return list(set(extracted)), 0.80

    # Strategy 4 (lower confidence): Look for flavor words in description
    text_flavors = []
    for flavor in known_flavors:
        if re.search(r"\b" + re.escape(flavor) + r"\b", text.lower()):
            text_flavors.append(flavor)

    if text_flavors:
        return list(set(text_flavors)), 0.7  # Lower confidence

    # No flavor profiles found
    return None, 0.0


def detect_is_single_origin(
    name: str, text: str, tags: Optional[List[str]] = None, confidence_tracking: bool = True
) -> Tuple[bool, float]:
    """
    Detect if a coffee product is single origin as opposed to a blend.

    Args:
        name: Product name
        text: Product description
        tags: List of product tags/categories (optional)
        confidence_tracking: Whether to track confidence scores

    Returns:
        Tuple of (is_single_origin, confidence_score)
    """
    if tags is None:
        tags = []

    # Strategy 1: Check for explicit "single origin" text
    if re.search(r"\bsingle[\s-]*origin\b", name.lower()) or re.search(r"\bsingle[\s-]*origin\b", text.lower()):
        return True, 0.95  # Very high confidence

    # Strategy 2: Look in tags
    for tag in tags:
        if re.search(r"\bsingle[\s-]*origin\b", tag.lower()):
            return True, 0.9
        elif re.search(r"\bblend\b", tag.lower()):
            return False, 0.9

    # Strategy 3: Check if name contains an origin/region name
    origin_indicators = [
        "estate",
        "farm",
        "ethiopia",
        "colombian",
        "kenya",
        "sumatra",
        "guatemala",
        "brazil",
        "costa rica",
        "honduras",
        "rwanda",
        "burundi",
        "el salvador",
        "nicaragua",
        "panama",
        "indonesia",
        "india",
        "vietnam",
        "mexico",
        "peru",
        "jamaica",
        "hawaii",
        "kona",
    ]

    # Check name for origin indicators (high confidence)
    for origin in origin_indicators:
        if re.search(r"\b" + re.escape(origin) + r"\b", name.lower()):
            return True, 0.85

    # Strategy 4: Check for blend keywords in name (high confidence)
    if re.search(r"\bblend\b", name.lower()) or re.search(r"\bmix\b", name.lower()):
        return False, 0.85

    # Strategy 5: Check description for single origin indicators
    if re.search(r"\bsingle\s+farm\b", text.lower()) or re.search(r"\bone\s+farm\b", text.lower()):
        return True, 0.8

    # Look for origin descriptions in text (medium confidence)
    for origin in origin_indicators:
        if re.search(r"\b" + re.escape(origin) + r"\b", text.lower()):
            # Only return if it seems to be describing the coffee's origin
            if "from" in text.lower() or "origin" in text.lower() or "region" in text.lower():
                return True, 0.75

    # Strategy 6: Default case - check for absence of blend indicators
    if not re.search(r"\bblend\b", text.lower()) and not re.search(r"\bmix\b", text.lower()):
        # In the absence of blend indicators, slightly lean toward single origin
        return True, 0.6  # Low confidence

    # Inconclusive
    return False, 0.0


def detect_is_seasonal(
    name: str, text: str, tags: Optional[List[str]] = None, confidence_tracking: bool = True
) -> Tuple[bool, float]:
    """
    Detect if a coffee product is seasonal.

    Args:
        name: Product name
        text: Product description
        tags: List of product tags/categories (optional)
        confidence_tracking: Whether to track confidence scores

    Returns:
        Tuple of (is_seasonal, confidence_score)
    """
    if tags is None:
        tags = []

    # Strategy 1: Check tags for seasonal indicators
    for tag in tags:
        if re.search(r"\bseasonal\b", tag.lower()) or re.search(r"\blimited\b", tag.lower()):
            return True, 0.9

    # Strategy 2: Check name for seasonal indicators
    if re.search(r"\bseasonal\b", name.lower()) or re.search(r"\blimited\b", name.lower()):
        return True, 0.85

    # Strategy 3: Check description for seasonal language
    seasonal_patterns = [
        r"\bseasonal\b",
        r"\blimited\s+(?:time|edition|release|availability)\b",
        r"\bavailable\s+(?:only|just)\s+for\b",
        r"\bspecial\s+harvest\b",
        r"\bshort\s+time\b",
        r"\btemporal\b",
        r"\bwhile\s+supplies\s+last\b",
    ]

    for pattern in seasonal_patterns:
        if re.search(pattern, text.lower()):
            return True, 0.8

    # Strategy 4: Check for seasonal or temporary language
    season_words = ["summer", "winter", "spring", "autumn", "fall", "holiday", "christmas", "festival"]

    for season in season_words:
        if re.search(r"\b" + re.escape(season) + r"\b", name.lower()):
            return True, 0.8
        elif re.search(r"\b" + re.escape(season) + r"\b", text.lower()):
            return True, 0.7

    # Inconclusive
    return False, 0.0


def extract_all_attributes(
    coffee: Dict[str, Any],
    text: str,
    tags: Optional[List[str]] = None,
    structured_data: Optional[Dict[str, Any]] = None,
    name: Optional[str] = None,
    confidence_tracking: bool = True,
) -> Dict[str, Any]:
    """
    Extract all coffee attributes and update the coffee dict.

    Args:
        coffee: Coffee product dict to update
        text: Product description or full product text
        tags: List of product tags/categories (optional)
        structured_data: Structured product data if available (optional)
        name: Product name (optional)
        confidence_tracking: Whether to track confidence scores

    Returns:
        Updated coffee dict with extracted attributes
    """
    if tags is None:
        tags = []

    if name is None:
        name = coffee.get("name", "")
    if name is None:
        name = ""

    # Initialize confidence tracking
    if confidence_tracking and "confidence_scores" not in coffee:
        coffee["confidence_scores"] = {}

    # Extract roast level
    roast_level, confidence = extract_roast_level(text, tags, structured_data, confidence_tracking)
    if roast_level:
        coffee["roast_level"] = roast_level
        if confidence_tracking:
            coffee["confidence_scores"]["roast_level"] = confidence

    # Extract bean type
    bean_type, confidence = extract_bean_type(text, tags, structured_data, confidence_tracking)
    if bean_type:
        coffee["bean_type"] = bean_type
        if confidence_tracking:
            coffee["confidence_scores"]["bean_type"] = confidence

    # Extract processing method
    processing_method, confidence = extract_processing_method(text, tags, structured_data, confidence_tracking)
    if processing_method:
        coffee["processing_method"] = processing_method
        if confidence_tracking:
            coffee["confidence_scores"]["processing_method"] = confidence

    # Extract flavor profiles
    flavor_profiles, confidence = extract_flavor_profiles(text, tags, structured_data, confidence_tracking)
    if flavor_profiles:
        coffee["flavor_profiles"] = flavor_profiles
        if confidence_tracking:
            coffee["confidence_scores"]["flavor_profiles"] = confidence

    # Detect if single origin
    is_single_origin, confidence = detect_is_single_origin(name, text, tags, confidence_tracking)
    if is_single_origin is not None:
        coffee["is_single_origin"] = is_single_origin
        if confidence_tracking:
            coffee["confidence_scores"]["is_single_origin"] = confidence

    # Detect if seasonal
    is_seasonal, confidence = detect_is_seasonal(name, text, tags, confidence_tracking)
    if is_seasonal is not None:
        coffee["is_seasonal"] = is_seasonal
        if confidence_tracking:
            coffee["confidence_scores"]["is_seasonal"] = confidence

    # Check if it's a blend based on bean_type, is_single_origin, or name patterns
    blend_detected = False

    # Check if name contains percentage indicators (e.g., "50% Arabica - 50% Robusta")
    percentage_match = re.search(r"(\d+)%\s*([a-zA-Z]+).*?(\d+)%\s*([a-zA-Z]+)", name.lower())
    if percentage_match:
        blend_detected = True
        # If we didn't already determine bean type, set it based on percentages
        if "bean_type" not in coffee:
            bean1 = percentage_match.group(2).lower()
            bean2 = percentage_match.group(4).lower()
            if ("arabica" in bean1 and "robusta" in bean2) or ("robusta" in bean1 and "arabica" in bean2):
                coffee["bean_type"] = "arabica-robusta"
                if confidence_tracking:
                    coffee["confidence_scores"]["bean_type"] = 0.9  # High confidence for explicit percentages

    # Set is_blend flag based on all available information
    if "bean_type" in coffee and coffee["bean_type"] == "blend":
        blend_detected = True
    elif "is_single_origin" in coffee and coffee["is_single_origin"] == False:
        blend_detected = True
    elif "blend" in name.lower():
        blend_detected = True

    if blend_detected:
        coffee["is_blend"] = True
        if "is_single_origin" not in coffee:
            coffee["is_single_origin"] = False

    return coffee
