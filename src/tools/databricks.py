"""Databricks tools for Spark job submission and monitoring."""

import time
from clients.databricks import submit_run, get_run_status


def submit_spark_job(pyspark_code: str, client_id: str) -> str:
    """Submit a PySpark transformation job to Databricks.

    Returns:
        run_id as string.
    """
    return submit_run(pyspark_code, client_id=client_id)


def check_spark_job_status(run_id: str) -> dict:
    """Check Spark job status.

    Returns:
        Dict with done, success, life_cycle_state, result_state, error_log.
    """
    return get_run_status(run_id)


def wait_for_spark_job(run_id: str, poll_interval: int = 15, timeout: int = 1800) -> dict:
    """Poll until Spark job completes or times out.

    Returns:
        Final status dict with done, success, error_log.
    """
    elapsed = 0
    while elapsed < timeout:
        status = get_run_status(run_id)
        if status["done"]:
            return status
        time.sleep(poll_interval)
        elapsed += poll_interval

    return {"done": True, "success": False, "error_log": f"Timed out after {timeout}s"}
