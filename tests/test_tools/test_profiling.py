"""Unit tests for the profiling tool."""

from tools.profiling import profile_data


def test_profile_basic():
    data = {
        "columns": ["id", "name", "amount"],
        "sample_rows": [
            {"id": 1, "name": "Alice", "amount": 100.0},
            {"id": 2, "name": "Bob", "amount": 200.0},
            {"id": 3, "name": None, "amount": 300.0},
        ],
    }
    result = profile_data(data)

    assert result["row_count"] == 3
    assert result["total_columns"] == 3
    assert "id" in result["columns"]
    assert "name" in result["columns"]
    assert "amount" in result["columns"]

    # Check null detection
    assert result["columns"]["name"]["null_count"] == 1
    assert result["columns"]["id"]["null_count"] == 0

    # Check numeric stats
    assert result["columns"]["amount"]["min"] == 100.0
    assert result["columns"]["amount"]["max"] == 300.0


def test_profile_empty():
    data = {"columns": [], "sample_rows": []}
    result = profile_data(data)
    assert result["row_count"] == 0


def test_profile_anomaly_high_nulls():
    data = {
        "columns": ["a"],
        "sample_rows": [{"a": None}, {"a": None}, {"a": None}, {"a": 1}],
    }
    result = profile_data(data)
    assert any("nulls" in a for a in result["anomalies"])


def test_profile_anomaly_constant_column():
    data = {
        "columns": ["a"],
        "sample_rows": [{"a": "X"}, {"a": "X"}, {"a": "X"}],
    }
    result = profile_data(data)
    assert any("constant" in a for a in result["anomalies"])
