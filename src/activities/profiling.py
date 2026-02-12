"""Phase 2: Data profiling and pseudocode generation."""

import json
import logging
import re
from agent.runner import run_agent
from agent.prompts import PROFILING_AND_PSEUDOCODE, PSEUDOCODE_REVISION
from tools.adls import read_mapping_spreadsheet, sample_source_data
from tools.profiling import profile_data

logger = logging.getLogger(__name__)


def _extract_json(text: str) -> str:
    """Extract JSON from LLM response, handling markdown code blocks."""
    # Remove markdown code blocks if present
    text = text.strip()
    if text.startswith("```"):
        # Remove opening ```json or ```
        text = re.sub(r'^```\w*\n?', '', text)
        # Remove closing ```
        text = re.sub(r'\n?```$', '', text)
    return text.strip()


def _validate_pseudocode(pseudocode_json: str) -> dict:
    """Parse and validate structured pseudocode JSON."""
    try:
        data = json.loads(pseudocode_json)
        # Ensure required fields exist
        if "version" not in data:
            data["version"] = 1
        if "summary" not in data:
            data["summary"] = "Data transformation"
        if "steps" not in data:
            data["steps"] = []
        return data
    except json.JSONDecodeError as e:
        logger.warning("Failed to parse pseudocode JSON: %s", e)
        # Return fallback structure with raw text
        return {
            "version": 1,
            "summary": "Data transformation (parse error - see raw_text)",
            "steps": [],
            "raw_text": pseudocode_json
        }


def _enrich_with_samples(pseudocode: dict, sample_data: dict) -> dict:
    """Add sample data examples to lookup steps for auditor context."""
    if not sample_data or "sample_rows" not in sample_data:
        return pseudocode

    sample_rows = sample_data.get("sample_rows", [])
    if not sample_rows:
        return pseudocode

    for step in pseudocode.get("steps", []):
        if step.get("type") == "lookup_join":
            source_key = step.get("join_key", {}).get("source", "")
            if source_key:
                # Get unique sample values from the source column
                values = set()
                for row in sample_rows[:50]:
                    if source_key in row and row[source_key]:
                        values.add(str(row[source_key]))
                if values:
                    step["sample_values"] = list(values)[:5]

    return pseudocode


def run_profiling(client_id: str, mapping_path: str, data_path: str) -> str:
    """Phase 2: Profile data and generate structured pseudocode.

    Returns:
        Structured pseudocode as JSON string.
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

    raw_response = run_agent(PROFILING_AND_PSEUDOCODE, user_message)

    # Extract and validate JSON
    json_str = _extract_json(raw_response)
    pseudocode = _validate_pseudocode(json_str)

    # Enrich with sample data
    pseudocode = _enrich_with_samples(pseudocode, sample)

    result = json.dumps(pseudocode)
    logger.info("Generated structured pseudocode for %s (version %d, %d steps)",
                client_id, pseudocode.get("version", 1), len(pseudocode.get("steps", [])))
    return result


def revise_pseudocode(pseudocode: str, feedback: str) -> str:
    """Revise pseudocode based on auditor feedback.

    Returns:
        Revised structured pseudocode as JSON string.
    """
    prompt = PSEUDOCODE_REVISION.format(feedback=feedback, pseudocode=pseudocode)
    raw_response = run_agent(prompt, "Please provide the revised pseudocode JSON.")

    # Extract and validate JSON
    json_str = _extract_json(raw_response)
    revised = _validate_pseudocode(json_str)

    result = json.dumps(revised)
    logger.info("Revised pseudocode (version %d, %d steps)",
                revised.get("version", 1), len(revised.get("steps", [])))
    return result
