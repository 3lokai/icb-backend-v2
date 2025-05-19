import os
import sys
import pytest
import tempfile
import shutil
import csv
from click.testing import CliRunner

# Patch sys.path for local imports if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import main

def test_setup_logging_creates_log_dir(tmp_path):
    log_dir = tmp_path / "logs"
    if log_dir.exists():
        shutil.rmtree(log_dir)
    logger = main.setup_logging(log_dir_override=log_dir)
    assert log_dir.exists(), "Log directory should be created by setup_logging()"


def test_detect_platform(monkeypatch):
    runner = CliRunner()
    # Patch detect_platform to return a known value
    monkeypatch.setattr(main, "detect_platform", lambda url: ("shopify", 0.99))
    result = runner.invoke(main.detect, ["https://example.com"])
    assert result.exit_code == 0
    assert "shopify" in result.output


def test_scrape_roaster_single(monkeypatch):
    runner = CliRunner()
    fake_roaster = {"name": "Test Roaster", "website_url": "https://roaster.com", "id": "test-id"}
    class DummyScraper:
        async def extract_roaster(self, name, url):
            return fake_roaster
    monkeypatch.setattr(main, "RoasterScraper", DummyScraper)
    monkeypatch.setattr(main.supabase, "upsert_roaster", lambda r: None)
    result = runner.invoke(main.scrape_roaster, ["Test Roaster,https://roaster.com"])
    assert result.exit_code == 0
    assert "Successfully scraped roaster" in result.output


def test_scrape_roaster_batch(tmp_path, monkeypatch):
    runner = CliRunner()
    fake_roaster = {"name": "Batch Roaster", "website_url": "https://batch.com", "id": "batch-id"}
    class DummyScraper:
        async def extract_roaster(self, name, url):
            return fake_roaster
    monkeypatch.setattr(main, "RoasterScraper", DummyScraper)
    monkeypatch.setattr(main.supabase, "upsert_roaster", lambda r: None)
    # Create a fake CSV
    csv_path = tmp_path / "roasters.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "url"])
        writer.writeheader()
        writer.writerow({"name": "Batch Roaster", "url": "https://batch.com"})
    result = runner.invoke(main.scrape_roaster, [str(csv_path), "--csv"])
    assert result.exit_code == 0
    assert "Scraped 1 roasters" in result.output


def test_scrape_roaster_batch_handles_missing(monkeypatch, tmp_path):
    runner = CliRunner()
    class DummyScraper:
        async def extract_roaster(self, name, url):
            if not name or not url:
                raise ValueError("Missing name or URL")
            return {"name": name, "website_url": url, "id": "id"}
    monkeypatch.setattr(main, "RoasterScraper", DummyScraper)
    monkeypatch.setattr(main.supabase, "upsert_roaster", lambda r: None)
    csv_path = tmp_path / "bad.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "url"])
        writer.writeheader()
        writer.writerow({"name": "", "url": "https://bad.com"})
    result = runner.invoke(main.scrape_roaster, [str(csv_path), "--csv"])
    assert result.exit_code == 0
    assert "Input Errors" in result.output


def test_scrape_roaster_single_invalid(monkeypatch):
    runner = CliRunner()
    result = runner.invoke(main.scrape_roaster, ["badinput"])
    assert result.exit_code == 0
    assert "Error: For single roaster, provide input as 'name,url'" in result.output


def test_scrape_products_command(monkeypatch):
    runner = CliRunner()
    fake_coffee = type("Coffee", (), {"name": "Test Coffee"})
    class DummyProductScraper:
        def __init__(self, *a, **k): pass
        async def scrape_roaster_products(self, roaster):
            return [fake_coffee]
    monkeypatch.setattr(main, "ProductScraper", DummyProductScraper)
    monkeypatch.setattr(main.supabase, "upsert_coffee", lambda c: None)
    result = runner.invoke(main.scrape_products, ["Test Roaster,https://roaster.com"])
    assert result.exit_code == 0
    assert "Successfully scraped" in result.output
