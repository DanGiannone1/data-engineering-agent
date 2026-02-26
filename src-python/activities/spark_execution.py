"""Phase 4b: Submit PySpark to Databricks and wait for completion."""

import logging
from tools.databricks import submit_spark_job, wait_for_spark_job

logger = logging.getLogger(__name__)


def execute_spark_job(pyspark_code: str, client_id: str) -> dict:
    """Submit Spark job and wait for completion.

    Returns:
        {success: bool, run_id: str, error_log: str}
    """
    logger.info("Submitting Spark job for %s", client_id)
    run_id = submit_spark_job(pyspark_code, client_id)
    logger.info("Spark job submitted: run_id=%s", run_id)

    status = wait_for_spark_job(run_id)

    if status["success"]:
        logger.info("Spark job %s succeeded", run_id)
    else:
        logger.warning("Spark job %s failed: %s", run_id, status.get("error_log", ""))

    return {
        "success": status["success"],
        "run_id": run_id,
        "error_log": status.get("error_log", ""),
    }
