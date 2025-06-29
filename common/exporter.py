"""
Standardized data export utilities for the Coffee Scraper system.
Supports CSV and JSON export with configurable options.
"""

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional


def export_to_csv(
    data: List[Dict[str, Any]],
    output_path: str,
    fieldnames: Optional[List[str]] = None,
    field_mapping: Optional[Dict[str, str]] = None,
    extras_action: Literal["ignore", "raise"] = "ignore",
    encoding: str = "utf-8-sig",
) -> None:
    """
    Export a list of dictionaries to a CSV file with configurable field mapping.
    Args:
        data: List of dictionaries to export.
        output_path: Path to the output CSV file.
        fieldnames: List of field names (columns) to export. If None, inferred from data.
        field_mapping: Optional mapping from data keys to CSV column names.
        extras_action: How to handle extra fields ('ignore', 'raise').
        encoding: Encoding for the output file (default: utf-8-sig for Excel compatibility).
    """
    if not data:
        raise ValueError("No data provided for CSV export.")

    # Determine fieldnames
    if fieldnames is None:
        fieldnames = list(data[0].keys())
    if field_mapping:
        csv_fieldnames = [field_mapping.get(fn, fn) for fn in fieldnames]
    else:
        csv_fieldnames = fieldnames

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding=encoding) as f:
        writer = csv.DictWriter(f, fieldnames=csv_fieldnames, extrasaction=extras_action)
        writer.writeheader()
        for row in data:
            if field_mapping:
                csv_row = {field_mapping.get(k, k): v for k, v in row.items() if k in fieldnames}
            else:
                csv_row = {k: v for k, v in row.items() if k in fieldnames}
            writer.writerow(csv_row)


def export_to_json(
    data: Any, output_path: str, indent: Optional[int] = 2, sort_keys: bool = False, encoding: str = "utf-8"
) -> None:
    """
    Export data to a JSON file with formatting options.
    Args:
        data: Data to export (list, dict, etc.).
        output_path: Path to the output JSON file.
        indent: Indentation for pretty-printing (None for compact).
        sort_keys: Whether to sort keys in output.
        encoding: Encoding for the output file.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding=encoding) as f:
        json.dump(data, f, indent=indent, sort_keys=sort_keys, ensure_ascii=False)
