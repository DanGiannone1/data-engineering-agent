"""End-to-end integration test scenarios.

These tests require a running Function App (local or deployed) and Azure services.
Run with: pytest tests/test_e2e/ --base-url http://localhost:7071

Scenarios:
1. New client — full 6-phase pipeline
2. Repeat run — LLM determines no change, reuses code
3. Rejection loop — reject pseudocode with feedback, verify revision
"""

import json
import time
import pytest
import requests


def start_transform(base_url: str, client_id: str) -> str:
    resp = requests.post(f"{base_url}/api/transform", json={
        "client_id": client_id,
        "mapping_path": f"{client_id}/mapping.xlsm",
        "data_path": f"{client_id}/transactions.xlsx",
    })
    resp.raise_for_status()
    return resp.json()["instance_id"]


def wait_for_agent_message(base_url: str, instance_id: str, phase: str, timeout: int = 300) -> list:
    """Poll until the agent posts a message in the given phase."""
    for _ in range(timeout // 5):
        resp = requests.get(f"{base_url}/api/transform/{instance_id}/messages")
        messages = resp.json()
        agent_msgs = [m for m in messages if m["role"] == "agent" and m["phase"] == phase]
        if agent_msgs:
            return messages
        time.sleep(5)
    pytest.fail(f"Timed out waiting for agent message in phase '{phase}'")


def submit_review(base_url: str, instance_id: str, approved: bool, feedback: str = ""):
    resp = requests.post(f"{base_url}/api/transform/{instance_id}/review", json={
        "approved": approved,
        "feedback": feedback,
    })
    resp.raise_for_status()


def get_status(base_url: str, instance_id: str) -> dict:
    resp = requests.get(f"{base_url}/api/transform/{instance_id}/status")
    resp.raise_for_status()
    return resp.json()


@pytest.mark.e2e
def test_new_client_full_pipeline(base_url):
    """Scenario 1: New client — full 6-phase pipeline with approvals."""
    instance_id = start_transform(base_url, "E2E_NEW_CLIENT")

    # Wait for pseudocode
    messages = wait_for_agent_message(base_url, instance_id, "pseudocode_review")
    pseudocode_msg = [m for m in messages if m["phase"] == "pseudocode_review" and m["role"] == "agent"][-1]
    assert len(pseudocode_msg["content"]) > 50  # Should have substantial pseudocode

    # Approve pseudocode
    submit_review(base_url, instance_id, approved=True)

    # Wait for output review
    messages = wait_for_agent_message(base_url, instance_id, "output_review", timeout=600)

    # Approve output
    submit_review(base_url, instance_id, approved=True)

    # Wait for completion
    for _ in range(60):
        status = get_status(base_url, instance_id)
        if status["runtime_status"] != "Running":
            break
        time.sleep(5)

    assert status["runtime_status"] == "Completed"


@pytest.mark.e2e
def test_repeat_run_reuse(base_url):
    """Scenario 2: Repeat run — should detect no change and reuse code."""
    # Requires that E2E_NEW_CLIENT already has approved code from test 1
    instance_id = start_transform(base_url, "E2E_NEW_CLIENT")

    # Wait for change detection message
    messages = wait_for_agent_message(base_url, instance_id, "change_detection")
    detection_msg = [m for m in messages if m["phase"] == "change_detection"][-1]

    # Should indicate reuse
    assert "reuse" in detection_msg["content"].lower() or "no change" in detection_msg["content"].lower()


@pytest.mark.e2e
def test_rejection_loop(base_url):
    """Scenario 3: Reject pseudocode with feedback, verify revision."""
    instance_id = start_transform(base_url, "E2E_REJECT_CLIENT")

    # Wait for pseudocode
    messages = wait_for_agent_message(base_url, instance_id, "pseudocode_review")
    first_pseudocode = [m for m in messages if m["phase"] == "pseudocode_review" and m["role"] == "agent"][-1]

    # Reject with feedback
    submit_review(base_url, instance_id, approved=False, feedback="Please add a step to filter out void transactions")

    # Wait for revised pseudocode
    time.sleep(10)
    messages = wait_for_agent_message(base_url, instance_id, "pseudocode_review")
    agent_msgs = [m for m in messages if m["phase"] == "pseudocode_review" and m["role"] == "agent"]

    # Should have at least 2 agent messages in pseudocode_review phase (original + revision)
    assert len(agent_msgs) >= 2

    revised = agent_msgs[-1]["content"]
    assert revised != first_pseudocode["content"]  # Should be different
