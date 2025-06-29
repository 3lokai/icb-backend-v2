import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scrapers.roasters_crawl4ai import schemas


def test_contact_schema_structure():
    schema = schemas.CONTACT_SCHEMA
    assert schema["name"] == "RoasterContact"
    assert any(f["name"] == "email" for f in schema["fields"])
    assert any(f["name"] == "address" for f in schema["fields"])
    assert any(f["name"] == "instagram" for f in schema["fields"])


def test_address_schema_structure():
    schema = schemas.ADDRESS_SCHEMA
    assert schema["name"] == "AddressInfo"
    assert any(f["name"] == "address" for f in schema["fields"])
    assert any(f["name"] == "footer_text" for f in schema["fields"])


def test_about_schema_structure():
    schema = schemas.ABOUT_SCHEMA
    assert schema["name"] == "RoasterAbout"
    assert any(f["name"] == "meta_description" for f in schema["fields"])
    assert any(f["name"] == "about_text" for f in schema["fields"])


def test_roaster_llm_schema_keys():
    schema = schemas.ROASTER_LLM_SCHEMA
    for key in ["description", "founded_year", "has_subscription", "city", "address"]:
        assert key in schema
    assert schema["founded_year"]["type"] == "integer"
    assert schema["description"]["type"] == "string"


def test_roaster_llm_instructions_content():
    instr = schemas.ROASTER_LLM_INSTRUCTIONS
    assert "description" in instr
    assert "founded_year" in instr
    assert "address" in instr
    assert "Return values as a JSON object" in instr
