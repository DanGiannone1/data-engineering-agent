"""Unit tests for integrity checks."""

from unittest.mock import patch
from activities.integrity_checks import run_integrity_checks


@patch("activities.integrity_checks.read_spark_output")
def test_integrity_pass(mock_read):
    mock_read.return_value = {
        "columns": ["id", "name", "amount"],
        "dtypes": {"id": "int64", "name": "object", "amount": "float64"},
        "row_count": 100,
        "sample_rows": [
            {"id": 1, "name": "Alice", "amount": 100.0},
            {"id": 2, "name": "Bob", "amount": 200.0},
        ],
    }

    report = run_integrity_checks("output/test.parquet", expected_columns=["id", "name", "amount"])
    assert report.overall_pass is True


@patch("activities.integrity_checks.read_spark_output")
def test_integrity_fail_empty(mock_read):
    mock_read.return_value = {
        "columns": ["id"],
        "dtypes": {"id": "int64"},
        "row_count": 0,
        "sample_rows": [],
    }

    report = run_integrity_checks("output/test.parquet")
    assert report.overall_pass is False
    assert any("0 rows" in c.message for c in report.checks)


@patch("activities.integrity_checks.read_spark_output")
def test_integrity_fail_missing_columns(mock_read):
    mock_read.return_value = {
        "columns": ["id"],
        "dtypes": {"id": "int64"},
        "row_count": 10,
        "sample_rows": [{"id": 1}],
    }

    report = run_integrity_checks("output/test.parquet", expected_columns=["id", "name"])
    assert report.overall_pass is False
    assert any("Missing" in c.message for c in report.checks)
