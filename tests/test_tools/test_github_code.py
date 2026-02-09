"""Unit tests for GitHub code storage tools."""

import json
import tempfile
from pathlib import Path
from datetime import datetime

# Override REPO_ROOT before importing
import os

_tmpdir = tempfile.mkdtemp()
os.environ["REPO_ROOT"] = _tmpdir

from tools.github_code import get_approved_code, save_approved_code
from models.approved_code import ApprovedCodeMetadata


def test_get_approved_code_not_found():
    result = get_approved_code("NONEXISTENT_CLIENT")
    assert result is None


def test_save_and_get_approved_code():
    client_id = "TEST_CLIENT"
    pseudocode = "1. Read the data\n2. Transform it\n3. Write output"
    pyspark_code = "from pyspark.sql import SparkSession\n# test"
    metadata = ApprovedCodeMetadata(
        client_id=client_id,
        approved_by="test@example.com",
        approved_at=datetime(2026, 1, 1),
    )

    save_approved_code(client_id, pseudocode, pyspark_code, metadata)

    result = get_approved_code(client_id)
    assert result is not None
    assert result["pseudocode"] == pseudocode
    assert result["pyspark_code"] == pyspark_code
    assert result["metadata"]["client_id"] == client_id
    assert result["metadata"]["approved_by"] == "test@example.com"
