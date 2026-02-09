"""Phase 4a: PySpark code generation from approved pseudocode."""

import logging
from agent.runner import run_agent_code
from agent.prompts import CODE_GENERATION, CODE_FIX
from tools.adls import sample_source_data

logger = logging.getLogger(__name__)


def generate_pyspark(
    client_id: str,
    pseudocode: str,
    input_path: str,
    output_path: str,
    data_path: str = "",
) -> str:
    """Phase 4a: Generate PySpark code from approved pseudocode.

    Returns:
        PySpark code as string.
    """
    # Get actual source column names to help LLM generate correct code
    source_columns = ""
    if data_path:
        try:
            sample = sample_source_data(data_path, n_rows=5)
            source_columns = ", ".join(sample["columns"])
        except Exception as e:
            logger.warning("Could not sample source data for column names: %s", e)

    prompt = CODE_GENERATION.format(
        input_path=input_path,
        output_path=output_path,
        client_id=client_id,
        pseudocode=pseudocode,
        source_columns=source_columns,
    )
    code = run_agent_code(prompt, "Generate the PySpark transformation code.")
    logger.info("Generated PySpark code for %s (%d chars)", client_id, len(code))
    return code


def fix_pyspark(pyspark_code: str, error_log: str) -> str:
    """Fix PySpark code based on Spark error log.

    Returns:
        Fixed PySpark code as string.
    """
    prompt = CODE_FIX.format(error_log=error_log, pyspark_code=pyspark_code)
    code = run_agent_code(prompt, "Fix the code and return the complete corrected script.")
    logger.info("Fixed PySpark code (%d chars)", len(code))
    return code
