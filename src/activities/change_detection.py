"""Phase 1: LLM-based change detection.

Compares current mapping + data sample against stored pseudocode to decide
whether regeneration is needed.
"""

import json
import logging
from agent.runner import run_agent_json
from agent.prompts import CHANGE_DETECTION
from tools.adls import read_mapping_spreadsheet, sample_source_data
from tools.github_code import get_approved_code

logger = logging.getLogger(__name__)


def run_change_detection(client_id: str, mapping_path: str, data_path: str) -> dict:
    """Phase 1: Determine if transformation needs regeneration.

    Returns:
        {needs_regeneration: bool, reason: str, existing_code: dict|None}
    """
    # Check if we have existing approved code
    existing = get_approved_code(client_id)
    if existing is None:
        logger.info("No existing code for %s — needs full generation", client_id)
        return {"needs_regeneration": True, "reason": "No existing approved code", "existing_code": None}

    # Read current inputs
    mapping = read_mapping_spreadsheet(mapping_path)
    sample = sample_source_data(data_path)

    # Ask LLM to compare
    user_message = json.dumps({
        "current_mapping": mapping,
        "current_data_sample": {
            "columns": sample["columns"],
            "dtypes": sample["dtypes"],
            "row_count": sample["row_count"],
            "sample_rows": sample["sample_rows"][:10],  # Limit for token budget
        },
        "stored_pseudocode": existing["pseudocode"],
    }, default=str)

    result = run_agent_json(CHANGE_DETECTION, user_message)

    return {
        "needs_regeneration": result["needs_regeneration"],
        "reason": result["reason"],
        "existing_code": existing if not result["needs_regeneration"] else None,
    }
