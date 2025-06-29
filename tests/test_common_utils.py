import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from common import utils


# Test create_slug
@pytest.mark.parametrize(
    "name,expected",
    [
        ("Coffee Shop", "coffee-shop"),
        ("Special!@# Name", "special-name"),
        ("  spaced   out  ", "spaced-out"),
        ("", ""),
    ],
)
def test_create_slug(name, expected):
    assert utils.create_slug(name) == expected


# Test normalize_phone_number
@pytest.mark.parametrize(
    "phone,expected", [("+91-9876543210", "+919876543210"), ("98765 43210", "+919876543210"), ("", "")]
)
def test_normalize_phone_number(phone, expected):
    assert utils.normalize_phone_number(phone) == expected


# Test clean_html
@pytest.mark.parametrize(
    "html,expected",
    [("<div>Hello <b>World</b></div>", "Hello World"), ("<p>Test</p>", "Test"), ("No tags", "No tags"), ("", "")],
)
def test_clean_html(html, expected):
    assert utils.clean_html(html) == expected


# Test clean_description
@pytest.mark.parametrize(
    "desc,expected", [("  This is a test.  ", "This is a test."), ("\nNew\tLine\r", "New Line"), ("", "")]
)
def test_clean_description(desc, expected):
    assert utils.clean_description(desc) == expected


# Test get_domain_from_url
@pytest.mark.parametrize(
    "url,expected", [("https://example.com/page", "example.com"), ("http://test.org", "test.org"), ("", "")]
)
def test_get_domain_from_url(url, expected):
    assert utils.get_domain_from_url(url) == expected


# Test normalize_url
@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://www.example.com/", "https://example.com"),
        ("http://example.com/page/", "http://example.com/page"),
        ("", ""),
    ],
)
def test_normalize_url(url, expected):
    assert utils.normalize_url(url) == expected
