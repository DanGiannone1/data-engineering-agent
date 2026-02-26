import json
import logging
from datetime import datetime

import azure.functions as func
import azure.durable_functions as df

from activities.change_detection import run_change_detection
from activities.profiling import run_profiling, revise_pseudocode as revise_pseudocode_impl
from activities.code_generation import generate_pyspark, fix_pyspark
from activities.spark_execution import execute_spark_job
from activities.integrity_checks import run_integrity_checks
from activities.audit import log_agent_message, log_auditor_message, get_thread_messages
from tools.github_code import save_approved_code
from models.approved_code import ApprovedCodeMetadata
from orchestrator.transform import orchestrator_function

logger = logging.getLogger(__name__)

# DFApp (not FunctionApp) — required for orchestration_trigger, activity_trigger, durable_client_input
app = df.DFApp(http_auth_level=func.AuthLevel.ANONYMOUS)


# ──────────────────────────────────────────
# HTTP Triggers
# ──────────────────────────────────────────

@app.route(route="health", methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse('{"status": "healthy"}', mimetype="application/json")


@app.route(route="transform", methods=["POST"])
@app.durable_client_input(client_name="client")
async def start_transform(req: func.HttpRequest, client) -> func.HttpResponse:
    """POST /api/transform — start a new transformation orchestration."""
    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse('{"error": "Invalid JSON"}', status_code=400, mimetype="application/json")

    required = ["client_id", "mapping_path", "data_path"]
    missing = [f for f in required if f not in body]
    if missing:
        return func.HttpResponse(
            json.dumps({"error": f"Missing fields: {missing}"}),
            status_code=400,
            mimetype="application/json",
        )

    instance_id = await client.start_new("transform_orchestrator", client_input=body)

    return func.HttpResponse(
        json.dumps({"instance_id": instance_id, "client_id": body["client_id"]}),
        status_code=202,
        mimetype="application/json",
    )


@app.route(route="transform/{instanceId}/status", methods=["GET"])
@app.durable_client_input(client_name="client")
async def get_transform_status(req: func.HttpRequest, client) -> func.HttpResponse:
    """GET /api/transform/{id}/status — current phase + pending review data."""
    instance_id = req.route_params.get("instanceId")
    status = await client.get_status(instance_id)

    if status is None:
        return func.HttpResponse('{"error": "Not found"}', status_code=404, mimetype="application/json")

    result = {
        "instance_id": instance_id,
        "runtime_status": status.runtime_status.value if status.runtime_status else None,
        "custom_status": status.custom_status,
        "output": status.output,
        "created_time": status.created_time.isoformat() if status.created_time else None,
        "last_updated_time": status.last_updated_time.isoformat() if status.last_updated_time else None,
    }
    return func.HttpResponse(json.dumps(result, default=str), mimetype="application/json")


@app.route(route="transform/{instanceId}/review", methods=["POST"])
@app.durable_client_input(client_name="client")
async def submit_review(req: func.HttpRequest, client) -> func.HttpResponse:
    """POST /api/transform/{id}/review — approve/reject with feedback."""
    instance_id = req.route_params.get("instanceId")
    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse('{"error": "Invalid JSON"}', status_code=400, mimetype="application/json")

    if "approved" not in body:
        return func.HttpResponse('{"error": "Missing approved field"}', status_code=400, mimetype="application/json")

    # Pass dict directly — no json.dumps (avoid double-serialization)
    await client.raise_event(instance_id, "review", body)

    return func.HttpResponse(
        json.dumps({"status": "review submitted", "approved": body["approved"]}),
        mimetype="application/json",
    )


@app.route(route="transform/{instanceId}/messages", methods=["GET"])
def get_messages(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/transform/{id}/messages — conversation history for chat UI."""
    instance_id = req.route_params.get("instanceId")
    messages = get_thread_messages(instance_id)
    return func.HttpResponse(json.dumps(messages, default=str), mimetype="application/json")


# ──────────────────────────────────────────
# Durable Functions Orchestrator
# ──────────────────────────────────────────

@app.orchestration_trigger(context_name="context")
def transform_orchestrator(context: df.DurableOrchestrationContext):
    yield from orchestrator_function(context)


# ──────────────────────────────────────────
# Activity Functions
# ──────────────────────────────────────────

@app.activity_trigger(input_name="input")
def change_detection(input: dict) -> dict:
    return run_change_detection(input["client_id"], input["mapping_path"], input["data_path"])


@app.activity_trigger(input_name="input")
def profiling(input: dict) -> str:
    return run_profiling(input["client_id"], input["mapping_path"], input["data_path"])


@app.activity_trigger(input_name="input")
def revise_pseudocode(input: dict) -> str:
    return revise_pseudocode_impl(input["pseudocode"], input["feedback"])


@app.activity_trigger(input_name="input")
def code_generation(input: dict) -> str:
    return generate_pyspark(
        input["client_id"], input["pseudocode"],
        input["input_path"], input["output_path"],
        data_path=input.get("data_path", ""),
    )


@app.activity_trigger(input_name="input")
def fix_code(input: dict) -> str:
    return fix_pyspark(input["pyspark_code"], input["error_log"])


@app.activity_trigger(input_name="input")
def spark_execution(input: dict) -> dict:
    return execute_spark_job(input["pyspark_code"], input["client_id"])


@app.activity_trigger(input_name="input")
def integrity_checks(input: dict) -> dict:
    report = run_integrity_checks(input["output_path"])
    return report.model_dump()


@app.activity_trigger(input_name="input")
def log_message(input: dict) -> dict:
    if input["role"] == "agent":
        log_agent_message(input["thread_id"], input["client_id"], input["phase"], input["content"])
    else:
        log_auditor_message(input["thread_id"], input["client_id"], input["phase"], input["content"])
    return {"logged": True}


@app.activity_trigger(input_name="input")
def save_code(input: dict) -> dict:
    metadata = ApprovedCodeMetadata(
        client_id=input["client_id"],
        approved_by="auditor",
        approved_at=datetime.utcnow(),
    )
    save_approved_code(input["client_id"], input["pseudocode"], input["pyspark_code"], metadata)
    return {"saved": True}
