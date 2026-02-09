"""6-phase Durable Functions orchestrator for data transformation.

Phases:
1. Change detection (LLM-based)
2. Data profiling + pseudocode generation
3. Auditor review of pseudocode (wait for external event)
4. PySpark code generation + Spark execution (3-try retry)
5. Deterministic integrity checks
6. Auditor review of output (wait for external event)
"""

import json
import logging
import os
import re

logger = logging.getLogger(__name__)

MAX_CODE_RETRIES = 5


def orchestrator_function(context):
    """Main orchestrator — receives TransformRequest as input."""
    input_data = context.get_input()
    client_id = input_data["client_id"]
    mapping_path = input_data["mapping_path"]
    data_path = input_data["data_path"]
    thread_id = context.instance_id

    # Use replay-safe clock (not datetime.utcnow which is non-deterministic)
    output_path = f"{client_id}/{context.current_utc_datetime.strftime('%Y%m%d_%H%M%S')}"

    pseudocode = None
    pyspark_code = None

    # --- Phase 1: Change Detection ---
    yield context.call_activity("log_message", {
        "thread_id": thread_id, "client_id": client_id,
        "phase": "change_detection", "role": "agent",
        "content": "Checking if existing transformation can be reused...",
    })

    detection = yield context.call_activity("change_detection", {
        "client_id": client_id,
        "mapping_path": mapping_path,
        "data_path": data_path,
    })

    if not detection["needs_regeneration"] and detection.get("existing_code"):
        yield context.call_activity("log_message", {
            "thread_id": thread_id, "client_id": client_id,
            "phase": "change_detection", "role": "agent",
            "content": f"Reusing existing transformation. Reason: {detection['reason']}",
        })
        pyspark_code = detection["existing_code"]["pyspark_code"]
        pseudocode = detection["existing_code"].get("pseudocode", "")

        # Update output path in reused code to point to this run's output
        storage_account = os.environ["ADLS_ACCOUNT_NAME"]
        new_output = f"abfss://output@{storage_account}.dfs.core.windows.net/{output_path}"
        old_pattern = rf'abfss://output@{re.escape(storage_account)}\.dfs\.core\.windows\.net/[^"\x27)\s]+'
        pyspark_code = re.sub(old_pattern, new_output, pyspark_code)
    else:
        yield context.call_activity("log_message", {
            "thread_id": thread_id, "client_id": client_id,
            "phase": "change_detection", "role": "agent",
            "content": f"Regeneration needed. Reason: {detection['reason']}",
        })

    # --- Phases 2-6 loop (output rejection loops back here) ---
    while True:
        # --- Phase 2: Profiling + Pseudocode ---
        if pyspark_code is None:
            pseudocode = yield context.call_activity("profiling", {
                "client_id": client_id,
                "mapping_path": mapping_path,
                "data_path": data_path,
            })

            yield context.call_activity("log_message", {
                "thread_id": thread_id, "client_id": client_id,
                "phase": "pseudocode_review", "role": "agent",
                "content": pseudocode,
            })

            # --- Phase 3: Auditor Review (loop) ---
            while True:
                review = yield context.wait_for_external_event("review")
                if isinstance(review, str):
                    review = json.loads(review)

                yield context.call_activity("log_message", {
                    "thread_id": thread_id, "client_id": client_id,
                    "phase": "pseudocode_review", "role": "auditor",
                    "content": f"{'Approved' if review['approved'] else 'Feedback: ' + review.get('feedback', '')}",
                })

                if review["approved"]:
                    break

                # Revise pseudocode with feedback
                pseudocode = yield context.call_activity("revise_pseudocode", {
                    "pseudocode": pseudocode,
                    "feedback": review["feedback"],
                })

                yield context.call_activity("log_message", {
                    "thread_id": thread_id, "client_id": client_id,
                    "phase": "pseudocode_review", "role": "agent",
                    "content": pseudocode,
                })

            # --- Phase 4a: Code Generation ---
            pyspark_code = yield context.call_activity("code_generation", {
                "client_id": client_id,
                "pseudocode": pseudocode,
                "input_path": f"abfss://data@{os.environ['ADLS_ACCOUNT_NAME']}.dfs.core.windows.net/{data_path}",
                "output_path": f"abfss://output@{os.environ['ADLS_ACCOUNT_NAME']}.dfs.core.windows.net/{output_path}",
                "data_path": data_path,
            })

        # --- Phase 4b + 5: Execution + Integrity (3-try retry) ---
        execution_succeeded = False
        for attempt in range(1, MAX_CODE_RETRIES + 1):
            yield context.call_activity("log_message", {
                "thread_id": thread_id, "client_id": client_id,
                "phase": "code_generation", "role": "agent",
                "content": f"Executing transformation (attempt {attempt}/{MAX_CODE_RETRIES})...",
            })

            spark_result = yield context.call_activity("spark_execution", {
                "pyspark_code": pyspark_code,
                "client_id": client_id,
            })

            if not spark_result["success"]:
                if attempt < MAX_CODE_RETRIES:
                    pyspark_code = yield context.call_activity("fix_code", {
                        "pyspark_code": pyspark_code,
                        "error_log": spark_result["error_log"],
                    })
                    continue
                else:
                    yield context.call_activity("log_message", {
                        "thread_id": thread_id, "client_id": client_id,
                        "phase": "code_generation", "role": "agent",
                        "content": f"Transformation failed after {MAX_CODE_RETRIES} attempts. Error: {spark_result['error_log']}",
                    })
                    return {"status": "failed", "error": spark_result["error_log"]}

            # Phase 5: Integrity Checks
            integrity = yield context.call_activity("integrity_checks", {
                "output_path": output_path,
            })

            if integrity["overall_pass"]:
                execution_succeeded = True
                break

            if attempt < MAX_CODE_RETRIES:
                error_context = "; ".join(integrity["errors"])
                pyspark_code = yield context.call_activity("fix_code", {
                    "pyspark_code": pyspark_code,
                    "error_log": f"Integrity check failures: {error_context}",
                })
            else:
                yield context.call_activity("log_message", {
                    "thread_id": thread_id, "client_id": client_id,
                    "phase": "code_generation", "role": "agent",
                    "content": f"Integrity checks failed after {MAX_CODE_RETRIES} attempts: {integrity['errors']}",
                })
                return {"status": "failed", "error": f"Integrity failures: {integrity['errors']}"}

        if not execution_succeeded:
            return {"status": "failed", "error": "Execution did not succeed"}

        # --- Phase 6: Auditor Review of Output ---
        yield context.call_activity("log_message", {
            "thread_id": thread_id, "client_id": client_id,
            "phase": "output_review", "role": "agent",
            "content": f"Transformation complete. Output at: {output_path}\nIntegrity checks: PASSED\nPlease review the output.",
        })

        review = yield context.wait_for_external_event("review")
        if isinstance(review, str):
            review = json.loads(review)

        yield context.call_activity("log_message", {
            "thread_id": thread_id, "client_id": client_id,
            "phase": "output_review", "role": "auditor",
            "content": f"{'Approved' if review['approved'] else 'Rejected: ' + review.get('feedback', '')}",
        })

        if review["approved"]:
            break  # Exit the while loop — proceed to save

        # Output rejected — loop back to Phase 2
        yield context.call_activity("log_message", {
            "thread_id": thread_id, "client_id": client_id,
            "phase": "output_review", "role": "agent",
            "content": "Output rejected. Returning to pseudocode revision...",
        })
        pyspark_code = None  # Force regeneration

    # --- Save approved code ---
    yield context.call_activity("save_code", {
        "client_id": client_id,
        "pseudocode": pseudocode or "",
        "pyspark_code": pyspark_code,
    })

    return {"status": "completed", "output_path": output_path}
