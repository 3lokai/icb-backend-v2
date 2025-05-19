import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common import exporter

def test_export_to_csv_and_json(tmp_path):
    # Dummy data
    data = [
        {"name": "Coffee1", "price": 100},
        {"name": "Coffee2", "price": 200},
    ]
    csv_path = tmp_path / "test.csv"
    json_path = tmp_path / "test.json"

    # Test export_to_csv
    exporter.export_to_csv(data, str(csv_path))
    assert os.path.exists(csv_path)
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()
        assert "name" in lines[0] and "price" in lines[0]
        assert "Coffee1" in lines[1]
        assert "Coffee2" in lines[2]

    # Test export_to_json
    exporter.export_to_json(data, str(json_path))
    assert os.path.exists(json_path)
    import json as pyjson
    with open(json_path, "r", encoding="utf-8") as f:
        loaded = pyjson.load(f)
        assert loaded == data
