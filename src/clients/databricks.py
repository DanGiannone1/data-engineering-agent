import base64
import os
import uuid

import requests
from azure.identity import DefaultAzureCredential


DATABRICKS_RESOURCE_ID = "2ff814a6-3304-4ab8-85cb-cd0e6f879c1d"  # Azure Databricks resource ID


def _get_databricks_token() -> str:
    credential = DefaultAzureCredential()
    token = credential.get_token(f"{DATABRICKS_RESOURCE_ID}/.default")
    return token.token


def _get_host() -> str:
    return os.environ["DATABRICKS_HOST"].rstrip("/")


def submit_run(pyspark_code: str, client_id: str = "", cluster_config: dict | None = None) -> str:
    """Submit a PySpark job via Jobs API 2.1. Returns run_id."""
    host = _get_host()
    token = _get_databricks_token()
    headers = {"Authorization": f"Bearer {token}"}

    if cluster_config is None:
        storage_account = os.environ["ADLS_ACCOUNT_NAME"]
        sp_client_id = os.environ["DATABRICKS_SP_CLIENT_ID"]
        sp_secret = os.environ["DATABRICKS_SP_SECRET"]
        sp_tenant = os.environ.get("DATABRICKS_SP_TENANT", "4e278620-67ad-411e-89a5-0f82836e52c5")
        cluster_config = {
            "spark_version": "14.3.x-scala2.12",
            "node_type_id": "Standard_D4s_v3",
            "num_workers": 1,
            "spark_conf": {
                f"fs.azure.account.auth.type.{storage_account}.dfs.core.windows.net": "OAuth",
                f"fs.azure.account.oauth.provider.type.{storage_account}.dfs.core.windows.net":
                    "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider",
                f"fs.azure.account.oauth2.client.id.{storage_account}.dfs.core.windows.net": sp_client_id,
                f"fs.azure.account.oauth2.client.secret.{storage_account}.dfs.core.windows.net": sp_secret,
                f"fs.azure.account.oauth2.client.endpoint.{storage_account}.dfs.core.windows.net":
                    f"https://login.microsoftonline.com/{sp_tenant}/oauth2/token",
            },
        }

    # Upload PySpark code as a Databricks notebook via Workspace API
    job_id = uuid.uuid4().hex[:12]
    notebook_path = f"/Shared/dea_transform_{job_id}"

    resp = requests.post(
        f"{host}/api/2.0/workspace/import",
        headers=headers,
        json={
            "path": notebook_path,
            "format": "SOURCE",
            "language": "PYTHON",
            "content": base64.b64encode(pyspark_code.encode()).decode(),
            "overwrite": True,
        },
        timeout=30,
    )
    resp.raise_for_status()

    payload = {
        "run_name": f"dea-transform-{client_id}" if client_id else "dea-transform",
        "new_cluster": cluster_config,
        "notebook_task": {
            "notebook_path": notebook_path,
        },
        "libraries": [
            {"pypi": {"package": "openpyxl"}},
        ],
    }

    resp = requests.post(
        f"{host}/api/2.1/jobs/runs/submit",
        headers=headers,
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return str(resp.json()["run_id"])


def get_run_status(run_id: str) -> dict:
    """Get run status. Returns {state, error_log}."""
    host = _get_host()
    token = _get_databricks_token()
    headers = {"Authorization": f"Bearer {token}"}

    resp = requests.get(
        f"{host}/api/2.1/jobs/runs/get",
        headers=headers,
        params={"run_id": run_id},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    state = data["state"]["life_cycle_state"]
    result_state = data["state"].get("result_state", "")
    error_log = data["state"].get("state_message", "")

    done = state in ("TERMINATED", "SKIPPED", "INTERNAL_ERROR")
    success = result_state == "SUCCESS"

    # Fetch notebook output for better error details on failure
    if done and not success:
        try:
            out_resp = requests.get(
                f"{host}/api/2.1/jobs/runs/get-output",
                headers=headers,
                params={"run_id": run_id},
                timeout=30,
            )
            out_resp.raise_for_status()
            out_data = out_resp.json()
            notebook_error = out_data.get("error", "")
            notebook_trace = out_data.get("error_trace", "")
            if notebook_trace:
                error_log = notebook_trace[-3000:]  # Last 3000 chars of traceback
            elif notebook_error:
                error_log = notebook_error
        except Exception:
            pass  # Fall back to state_message

    return {
        "life_cycle_state": state,
        "result_state": result_state,
        "error_log": error_log,
        "done": done,
        "success": success,
    }
