"""Trigger a test transformation and exercise the review endpoints.

Usage:
    python scripts/trigger_test_run.py [--base-url http://localhost:7071]

This script:
1. Starts a new transformation via POST /api/transform
2. Polls status until pseudocode review is pending
3. Approves the pseudocode
4. Polls until output review is pending
5. Approves the output
6. Verifies completion
"""

import argparse
import json
import time
import requests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:7071")
    parser.add_argument("--client-id", default="CLIENT_001")
    parser.add_argument("--mapping-path", default="mappings/CLIENT_001/mapping.xlsm")
    parser.add_argument("--data-path", default="data/CLIENT_001/transactions.xlsx")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")

    # 1. Start transformation
    print(f"Starting transformation for {args.client_id}...")
    resp = requests.post(f"{base}/api/transform", json={
        "client_id": args.client_id,
        "mapping_path": args.mapping_path,
        "data_path": args.data_path,
    })
    resp.raise_for_status()
    instance = resp.json()
    instance_id = instance["instance_id"]
    print(f"  Instance ID: {instance_id}")

    # 2. Poll until review is pending
    print("\nWaiting for pseudocode review...")
    wait_for_review(base, instance_id)

    # 3. Get messages
    messages = get_messages(base, instance_id)
    print(f"\n  Latest agent message ({len(messages)} total):")
    if messages:
        print(f"  {messages[-1]['content'][:200]}...")

    # 4. Approve pseudocode
    print("\nApproving pseudocode...")
    resp = requests.post(f"{base}/api/transform/{instance_id}/review", json={
        "approved": True,
    })
    resp.raise_for_status()
    print("  Approved.")

    # 5. Poll until output review or completion
    print("\nWaiting for output review or completion...")
    wait_for_review(base, instance_id, max_wait=600)

    # 6. Check status
    status = get_status(base, instance_id)
    if status["runtime_status"] == "Completed":
        print(f"\nTransformation completed! Output: {status.get('output', {})}")
        return

    # 7. Approve output
    print("\nApproving output...")
    resp = requests.post(f"{base}/api/transform/{instance_id}/review", json={
        "approved": True,
    })
    resp.raise_for_status()

    # 8. Wait for completion
    print("\nWaiting for completion...")
    for _ in range(60):
        status = get_status(base, instance_id)
        if status["runtime_status"] != "Running":
            break
        time.sleep(5)

    print(f"\nFinal status: {status['runtime_status']}")
    print(f"Output: {json.dumps(status.get('output'), indent=2)}")


def get_status(base: str, instance_id: str) -> dict:
    resp = requests.get(f"{base}/api/transform/{instance_id}/status")
    resp.raise_for_status()
    return resp.json()


def get_messages(base: str, instance_id: str) -> list:
    resp = requests.get(f"{base}/api/transform/{instance_id}/messages")
    resp.raise_for_status()
    return resp.json()


def wait_for_review(base: str, instance_id: str, max_wait: int = 300):
    """Poll until the orchestration is waiting for an external event (review)."""
    for i in range(max_wait // 5):
        status = get_status(base, instance_id)
        runtime = status["runtime_status"]

        if runtime != "Running":
            print(f"  Status: {runtime}")
            return

        # Check if messages indicate review pending
        messages = get_messages(base, instance_id)
        if messages and messages[-1]["role"] == "agent":
            phase = messages[-1].get("phase", "")
            if phase in ("pseudocode_review", "output_review"):
                print(f"  Review pending (phase: {phase})")
                return

        if i % 6 == 0:
            print(f"  Still processing... ({i * 5}s)")
        time.sleep(5)

    print("  Timed out waiting for review.")


if __name__ == "__main__":
    main()
