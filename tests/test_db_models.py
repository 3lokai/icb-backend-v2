import os
import sys
from datetime import datetime

import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db import models


def test_roastlevel_enum():
    assert "light" in models.RoastLevel.ALL
    assert models.RoastLevel.LIGHT == "light"


def test_beantype_enum():
    assert "arabica" in models.BeanType.ALL
    assert models.BeanType.ARABICA == "arabica"


def test_processingmethod_enum():
    assert "washed" in models.ProcessingMethod.ALL
    assert models.ProcessingMethod.WASHED == "washed"


def test_roaster_model_valid():
    r = models.Roaster(name="Test Roaster", slug="test-roaster", website_url="https://test.com")
    assert r.name == "Test Roaster"
    assert str(r.website_url) == "https://test.com/"


def test_roaster_model_invalid_url():
    with pytest.raises(ValidationError):
        models.Roaster(name="Test Roaster", slug="test-roaster", website_url="not-a-url")


def test_coffee_model_valid():
    c = models.Coffee(name="Test Coffee", slug="test-coffee", roaster_id="r1", direct_buy_url="https://buy.com")
    assert c.name == "Test Coffee"
    assert str(c.direct_buy_url) == "https://buy.com/"


def test_coffee_model_missing_required():
    with pytest.raises(ValidationError):
        models.Coffee(
            name="Test Coffee",
            slug="test-coffee",
            # missing roaster_id
            direct_buy_url="https://buy.com",
        )


def test_coffeeprice_and_externallink():
    price = models.CoffeePrice(size_grams=250, price=500)
    assert price.size_grams == 250
    link = models.ExternalLink(provider="Amazon", url="https://amz.com")
    assert link.provider == "Amazon"
    assert str(link.url) == "https://amz.com/"


def test_scrapingstate_model():
    now = datetime.now()
    state = models.ScrapingState(
        url="https://site.com",
        last_scraped=now,
        status="done",
        field_timestamps={"foo": now},
        field_confidence={"foo": 100},
    )
    assert state.url == "https://site.com"
    assert state.status == "done"
    assert state.field_timestamps["foo"] == now
    assert state.field_confidence["foo"] == 100
