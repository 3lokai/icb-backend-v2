import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from pydantic import BaseModel, HttpUrl

from common import pydantic_utils


# Minimal Pydantic model for testing
def make_test_model():
    class TestModel(BaseModel):
        name: str
        url: HttpUrl = "https://example.com"
        value: int = 42
        optional: str | None = None

    return TestModel


# Test model_to_dict basic usage
def test_model_to_dict_basic():
    TestModel = make_test_model()
    model = TestModel(name="Coffee")
    result = pydantic_utils.model_to_dict(model)
    assert result["name"] == "Coffee"
    assert result["url"] == "https://example.com"
    assert result["value"] == 42
    assert "optional" not in result  # exclude_none=True by default


# Test model_to_dict with exclude_none=False
def test_model_to_dict_exclude_none_false():
    TestModel = make_test_model()
    model = TestModel(name="Coffee")
    result = pydantic_utils.model_to_dict(model, exclude_none=False)
    assert "optional" in result
    assert result["optional"] is None


# Test dict_to_pydantic_model basic usage
def test_dict_to_pydantic_model_basic():
    TestModel = make_test_model()
    data = {"name": "Test", "url": "https://test.com", "value": 100}
    model = pydantic_utils.dict_to_pydantic_model(data, TestModel)
    assert isinstance(model, TestModel)
    assert model.name == "Test"
    assert str(model.url) == "https://test.com/"
    assert model.value == 100


# Test dict_to_pydantic_model with missing required field
def test_dict_to_pydantic_model_missing_required():
    TestModel = make_test_model()
    data = {"url": "https://test.com"}
    model = pydantic_utils.dict_to_pydantic_model(data, TestModel)
    assert model is None


# Test dict_to_pydantic_model with field_map
def test_dict_to_pydantic_model_field_map():
    TestModel = make_test_model()
    data = {"the_name": "Test", "url": "https://test.com", "value": 99}
    model = pydantic_utils.dict_to_pydantic_model(data, TestModel, field_map={"the_name": "name"})
    assert model.name == "Test"
    assert model.value == 99


# Test preprocess_roaster_data and preprocess_coffee_data just run (smoke test)
def test_preprocess_roaster_data_smoke():
    data = {"name": "Roaster", "website_url": "https://roaster.com"}
    out = pydantic_utils.preprocess_roaster_data(data)
    assert isinstance(out, dict)
    assert out["name"] == "Roaster"


def test_preprocess_coffee_data_smoke():
    data = {"name": "Coffee", "direct_buy_url": "https://buy.com"}
    out = pydantic_utils.preprocess_coffee_data(data)
    assert isinstance(out, dict)
    assert out["name"] == "Coffee"
