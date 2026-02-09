"""Test connectivity to all deployed Azure services.

Usage:
    ADLS_ACCOUNT_NAME=deagentstorage \
    COSMOS_ENDPOINT=https://de-agent-cosmos.documents.azure.com:443/ \
    COSMOS_DATABASE=agent-db \
    DATABRICKS_HOST=https://adb-7405605163173611.11.azuredatabricks.net \
    AZURE_OPENAI_ENDPOINT=https://test-foundry-djg.cognitiveservices.azure.com \
    AZURE_OPENAI_DEPLOYMENT=gpt-4.1 \
    python scripts/test_connectivity.py
"""

import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

PASS = "PASS"
FAIL = "FAIL"
results = []


def test(name, fn):
    try:
        result = fn()
        results.append((name, PASS, result))
        print(f"  [{PASS}] {name}: {result}")
    except Exception as e:
        results.append((name, FAIL, str(e)))
        print(f"  [{FAIL}] {name}: {e}")


def test_adls():
    from clients.adls import get_adls_client
    client = get_adls_client()
    fs = client.get_file_system_client("mappings")
    props = fs.get_file_system_properties()
    return f"Container 'mappings' exists, last_modified={props['last_modified']}"


def test_adls_list_containers():
    from clients.adls import get_adls_client
    client = get_adls_client()
    containers = [fs.name for fs in client.list_file_systems()]
    return f"Containers: {containers}"


def test_cosmos():
    from clients.cosmos import get_conversations_container
    container = get_conversations_container()
    # Write a test message
    test_id = f"test-{uuid.uuid4().hex[:8]}"
    msg = {
        "id": test_id,
        "thread_id": "connectivity-test",
        "content": "connectivity test",
        "role": "agent",
    }
    container.upsert_item(msg)
    # Read it back
    item = container.read_item(test_id, partition_key="connectivity-test")
    # Clean up
    container.delete_item(test_id, partition_key="connectivity-test")
    return f"Write/read/delete OK (id={test_id})"


def test_databricks():
    from clients.databricks import _get_databricks_token, _get_host
    token = _get_databricks_token()
    host = _get_host()
    import requests
    resp = requests.get(
        f"{host}/api/2.0/clusters/list",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    resp.raise_for_status()
    clusters = resp.json().get("clusters", [])
    return f"API reachable, {len(clusters)} clusters found"


def test_openai():
    from agent.client import get_openai_client
    client = get_openai_client()
    deployment = os.environ["AZURE_OPENAI_DEPLOYMENT"]
    resp = client.chat.completions.create(
        model=deployment,
        messages=[{"role": "user", "content": "Say 'hello' and nothing else."}],
        max_tokens=10,
    )
    return f"Response: {resp.choices[0].message.content}"


def main():
    print("=== Azure Service Connectivity Tests ===\n")

    print("1. ADLS Gen2:")
    test("  Container access", test_adls)
    test("  List containers", test_adls_list_containers)

    print("\n2. Cosmos DB:")
    test("  CRUD operations", test_cosmos)

    print("\n3. Databricks:")
    test("  API + auth", test_databricks)

    print("\n4. Azure OpenAI:")
    test("  Chat completion", test_openai)

    print("\n=== Summary ===")
    passed = sum(1 for _, s, _ in results if s == PASS)
    failed = sum(1 for _, s, _ in results if s == FAIL)
    print(f"  {passed} passed, {failed} failed out of {len(results)} tests")

    if failed > 0:
        print("\nFailed tests:")
        for name, status, detail in results:
            if status == FAIL:
                print(f"  {name}: {detail}")
        sys.exit(1)


if __name__ == "__main__":
    main()
