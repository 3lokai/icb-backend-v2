import hashlib

import aiohttp
from aiohttp import ClientTimeout
from bs4 import BeautifulSoup


class PlatformDetector:
    def __init__(self):
        self._cache = {}  # Simple in-memory cache

    async def detect(self, url):
        cache_key = self._get_cache_key(url)
        if cache_key in self._cache:
            return self._cache[cache_key]
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=ClientTimeout(total=10)) as resp:
                    html = await resp.text()
            soup = BeautifulSoup(html, "html.parser")

            results = [
                self._detect_shopify(html, soup, url),
                self._detect_woocommerce(html, soup, url),
                self._detect_magento(html, soup, url),
                self._detect_wordpress(html, soup, url),
                self._detect_webflow(html, soup, url),
            ]
            # Pick the platform with the highest confidence
            platform, confidence = max(results, key=lambda x: x[1])
            if confidence < 40:
                platform, confidence = "unknown", confidence
            self._cache[cache_key] = (platform, confidence)
            return platform, confidence
        except Exception as e:
            print(f"[PlatformDetector] Error for {url}: {e}")
            return "unknown", 0

    def _get_cache_key(self, url):
        return hashlib.sha256(url.encode()).hexdigest()

    def _detect_shopify(self, html, soup, url):
        score = 0
        if soup.find("script", src=lambda x: x and "cdn.shopify.com" in x):
            score += 40
        if soup.find(attrs={"data-shopify": True}):
            score += 30
        if "/cdn/shop/" in url:
            score += 10
        if "Shopify.theme" in html:
            score += 20
        return ("shopify", min(score, 100))

    def _detect_woocommerce(self, html, soup, url):
        score = 0
        if soup.find("body", class_=lambda c: c and "woocommerce" in c):
            score += 40
        if soup.find("link", href=lambda x: x and "woocommerce" in x):
            score += 20
        if "woocommerce" in html.lower():
            score += 20
        if soup.select('.woocommerce, [class*="woocommerce"]'):
            score += 20
        return ("woocommerce", min(score, 100))

    def _detect_magento(self, html, soup, url):
        score = 0
        # Classic meta tag
        if soup.find("meta", attrs={"name": "generator", "content": lambda x: x and "Magento" in x}):
            score += 60
        # Magento JS/CSS static assets
        if "/pub/static/frontend/" in html:
            score += 30
        # <script type="text/x-magento-init">
        if soup.find("script", attrs={"type": "text/x-magento-init"}):
            score += 30
        # data-mage-init attribute
        if soup.find(attrs={"data-mage-init": True}):
            score += 20
        # JS var require with baseUrl containing /pub/static/frontend/
        if "var require = {" in html and "baseUrl" in html and "/pub/static/frontend/" in html:
            score += 20
        # Fallback: mage- classes or IDs
        if "mage-" in html:
            score += 10
        return ("magento", min(score, 100))

    def _detect_wordpress(self, html, soup, url):
        score = 0
        wp_meta = soup.find("meta", attrs={"name": "generator", "content": lambda x: x and "WordPress" in x})
        wp_paths = "/wp-content/" in html or "/wp-includes/" in html
        if wp_meta:
            score += 40
        if wp_paths:
            score += 30
        return ("wordpress", min(score, 100))

    def _detect_webflow(self, html, soup, url):
        score = 0
        if soup.find("meta", attrs={"name": "generator", "content": lambda x: x and "Webflow" in x}):
            score += 60
        if "Webflow.require" in html:
            score += 30
        return ("webflow", min(score, 100))
