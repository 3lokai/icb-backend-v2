import pytest
from pydantic import BaseModel, HttpUrl

from db.supabase import SupabaseClient


class NestedModel(BaseModel):
    url: HttpUrl
    name: str


class ExampleModel(BaseModel):
    homepage: HttpUrl
    links: list[HttpUrl]
    nested: NestedModel
    nested_list: list[NestedModel]
    plain: str
    optional_url: HttpUrl | None = None
    dict_field: dict[str, HttpUrl]


@pytest.mark.parametrize(
    "model,expected",
    [
        (
            ExampleModel(
                homepage="https://example.com",
                links=["https://foo.com", "https://bar.com"],
                nested=NestedModel(url="https://nested.com", name="nested"),
                nested_list=[
                    NestedModel(url="https://n1.com", name="n1"),
                    NestedModel(url="https://n2.com", name="n2"),
                ],
                plain="plain value",
                dict_field={"a": "https://a.com", "b": "https://b.com"},
            ),
            {
                "homepage": "https://example.com",
                "links": ["https://foo.com", "https://bar.com"],
                "nested": {"url": "https://nested.com", "name": "nested"},
                "nested_list": [{"url": "https://n1.com", "name": "n1"}, {"url": "https://n2.com", "name": "n2"}],
                "plain": "plain value",
                "optional_url": None,
                "dict_field": {"a": "https://a.com", "b": "https://b.com"},
            },
        ),
    ],
)
def test_model_to_dict_serialization(model, expected):
    result = SupabaseClient.model_to_dict(model)
    assert result == expected


def test_model_to_dict_handles_non_url_types():
    class Model(BaseModel):
        number: int
        flag: bool
        none_val: None = None

    m = Model(number=5, flag=True)
    result = SupabaseClient.model_to_dict(m)
    assert result == {"number": 5, "flag": True, "none_val": None}


def test_model_to_dict_handles_nested_none():
    class Model(BaseModel):
        url: HttpUrl | None = None
        nested: NestedModel | None = None

    m = Model()
    result = SupabaseClient.model_to_dict(m)
    assert result == {"url": None, "nested": None}
