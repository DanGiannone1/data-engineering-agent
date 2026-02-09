"""GitHub-based approved code storage.

Reads/writes approved PySpark code, pseudocode, and metadata from the
approved-code/{client_id}/ directory in the repo.
"""

import json
import os
from pathlib import Path

from models.approved_code import ApprovedCodeMetadata

# Repo root — in Azure Functions, this would be the deployed code directory.
# For local dev, it's the repo root.
REPO_ROOT = Path(os.environ.get("REPO_ROOT", Path(__file__).resolve().parents[2]))
APPROVED_CODE_DIR = REPO_ROOT / "approved-code"


def get_approved_code(client_id: str) -> dict | None:
    """Read approved code for a client from the repo.

    Returns:
        Dict with pseudocode, pyspark_code, metadata, or None if not found.
    """
    client_dir = APPROVED_CODE_DIR / client_id

    if not client_dir.exists():
        return None

    pseudocode_path = client_dir / "pseudocode.md"
    transform_path = client_dir / "transform.py"
    metadata_path = client_dir / "metadata.json"

    # All three files must exist for a valid approved-code entry
    if not (pseudocode_path.exists() and transform_path.exists() and metadata_path.exists()):
        return None

    return {
        "pseudocode": pseudocode_path.read_text(),
        "pyspark_code": transform_path.read_text(),
        "metadata": json.loads(metadata_path.read_text()),
    }


def save_approved_code(
    client_id: str,
    pseudocode: str,
    pyspark_code: str,
    metadata: ApprovedCodeMetadata,
) -> None:
    """Write approved code files to the repo.

    Creates approved-code/{client_id}/ with pseudocode.md, transform.py, metadata.json.
    """
    client_dir = APPROVED_CODE_DIR / client_id
    client_dir.mkdir(parents=True, exist_ok=True)

    (client_dir / "pseudocode.md").write_text(pseudocode)
    (client_dir / "transform.py").write_text(pyspark_code)
    (client_dir / "metadata.json").write_text(
        metadata.model_dump_json(indent=2)
    )
