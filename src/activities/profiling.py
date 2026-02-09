"""Phase 2: Data profiling and pseudocode generation."""

import json
import logging
from agent.runner import run_agent
from agent.prompts import PROFILING_AND_PSEUDOCODE, PSEUDOCODE_REVISION
from tools.adls import read_mapping_spreadsheet, sample_source_data
from tools.profiling import profile_data

logger = logging.getLogger(__name__)


def run_profiling(client_id: str, mapping_path: str, data_path: str) -> str:
    """Phase 2: Profile data and generate pseudocode.

    Returns:
        Pseudocode string (plain English transformation plan).
    """
    mapping = read_mapping_spreadsheet(mapping_path)
    sample = sample_source_data(data_path)
    profile = profile_data(sample)

    user_message = json.dumps({
        "client_id": client_id,
        "mapping": mapping,
        "data_profile": profile,
        "sample_rows": sample["sample_rows"][:20],
    }, default=str)

    pseudocode = run_agent(PROFILING_AND_PSEUDOCODE, user_message)
    logger.info("Generated pseudocode for %s (%d chars)", client_id, len(pseudocode))
    return pseudocode


def revise_pseudocode(pseudocode: str, feedback: str) -> str:
    """Revise pseudocode based on auditor feedback.

    Returns:
        Revised pseudocode string.
    """
    prompt = PSEUDOCODE_REVISION.format(feedback=feedback, pseudocode=pseudocode)
    revised = run_agent(prompt, "Please provide the revised pseudocode.")
    logger.info("Revised pseudocode (%d chars)", len(revised))
    return revised
