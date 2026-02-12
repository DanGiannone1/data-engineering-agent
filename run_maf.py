"""
MAF Prototype - Test the agentic loop with existing tools.

This uses Microsoft Agent Framework to create a data engineering agent
that can read mappings, sample data, generate code, and execute Spark jobs.
"""

import asyncio
import json
import os
import sys
from typing import Annotated

from dotenv import load_dotenv

load_dotenv()

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from agent_framework import Agent, tool
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential


# =============================================================================
# Tools - Wrapped versions of existing tools with MAF-compatible signatures
# =============================================================================

@tool
def read_mapping_spreadsheet(
    path: Annotated[str, "Path within 'mappings' container, e.g. 'CLIENT_001/mapping.xlsx'"]
) -> str:
    """Download Excel mapping from ADLS and return structured column mappings."""
    from tools.adls import read_mapping_spreadsheet as _read
    result = _read(path)
    return json.dumps(result, indent=2, default=str)


@tool
def sample_source_data(
    path: Annotated[str, "Path within 'data' container, e.g. 'CLIENT_001/transactions.csv'"],
    n_rows: Annotated[int, "Number of rows to sample"] = 100
) -> str:
    """Read first N rows from source data file in ADLS for profiling."""
    from tools.adls import sample_source_data as _sample
    result = _sample(path, n_rows)
    return json.dumps(result, indent=2, default=str)


@tool
def read_spark_output(
    path: Annotated[str, "Path within 'output' container, e.g. 'CLIENT_001/20260211'"],
    n_rows: Annotated[int, "Number of rows to read"] = 50
) -> str:
    """Read Spark output from ADLS for validation."""
    from tools.adls import read_spark_output as _read_output
    result = _read_output(path, n_rows)
    return json.dumps(result, indent=2, default=str)


@tool
def submit_spark_job(
    pyspark_code: Annotated[str, "Complete PySpark code to execute"],
    client_id: Annotated[str, "Client identifier for job naming"]
) -> str:
    """Submit a PySpark transformation job to Databricks. Returns run_id."""
    from tools.databricks import submit_spark_job as _submit
    run_id = _submit(pyspark_code, client_id)
    return json.dumps({"run_id": run_id, "status": "submitted"})


@tool
def check_spark_job_status(
    run_id: Annotated[str, "Databricks run ID to check"]
) -> str:
    """Check Spark job status. Returns done, success, error_log."""
    from tools.databricks import check_spark_job_status as _check
    result = _check(run_id)
    return json.dumps(result, indent=2)


@tool
def wait_for_spark_job(
    run_id: Annotated[str, "Databricks run ID to wait for"],
    poll_interval: Annotated[int, "Seconds between status checks"] = 15,
    timeout: Annotated[int, "Maximum seconds to wait"] = 1800
) -> str:
    """Poll until Spark job completes or times out."""
    from tools.databricks import wait_for_spark_job as _wait
    result = _wait(run_id, poll_interval, timeout)
    return json.dumps(result, indent=2)


# =============================================================================
# Agent Setup
# =============================================================================

AGENT_INSTRUCTIONS = """You are a data engineering agent that transforms data according to mapping specifications.

Your workflow:
1. Read the mapping spreadsheet to understand the transformation rules
2. Sample the source data to understand its structure and types
3. Generate PySpark code that implements the transformation
4. Submit the Spark job and wait for completion
5. Read the output to verify the transformation worked correctly

When generating PySpark code:
- Use DataFrame API (not RDDs)
- Read from abfss://{container}@{storage_account}.dfs.core.windows.net/{path}
- Write output as parquet
- The code runs on Databricks - spark session is already available as 'spark'
- Include error handling for common issues

Storage account: deagentstorage2026
Containers: 'data' for input, 'output' for results

Think step by step and use tools to gather information before generating code.
"""


def get_chat_client() -> AzureOpenAIChatClient:
    """Create Azure OpenAI chat client."""
    return AzureOpenAIChatClient(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        deployment_name=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        credential=AzureCliCredential(process_timeout=60),
        api_version="2025-01-01-preview",
    )


def create_agent() -> Agent:
    """Create the data engineering agent with tools."""
    client = get_chat_client()

    # Tools decorated with @tool are already FunctionTool instances
    tools = [
        read_mapping_spreadsheet,
        sample_source_data,
        read_spark_output,
        submit_spark_job,
        check_spark_job_status,
        wait_for_spark_job,
    ]

    return Agent(
        client=client,
        name="DataEngineer",
        instructions=AGENT_INSTRUCTIONS,
        tools=tools,
    )


# =============================================================================
# Main Runner
# =============================================================================

async def run_transform(client_id: str, mapping_path: str, data_path: str, output_path: str):
    """Run the transformation workflow."""
    agent = create_agent()

    user_request = f"""Transform data for client {client_id}.

Mapping file: {mapping_path}
Source data: {data_path}
Output path: {output_path}

Please:
1. Read the mapping to understand the transformation rules
2. Sample the source data to understand its structure
3. Generate and execute PySpark code to transform the data
4. Verify the output looks correct
"""

    print("=" * 60)
    print("Starting MAF Agent")
    print("=" * 60)
    print(f"Request: Transform {data_path} using {mapping_path}")
    print("=" * 60)

    # Run agent without streaming for simpler output
    thread = agent.get_new_thread()

    print("\nCalling agent.run()...")
    response = await agent.run(user_request, thread=thread)

    print("\n" + "=" * 60)
    print("Agent completed")

    # Print the full text response
    if hasattr(response, 'text') and response.text:
        print("\n--- AGENT RESPONSE ---")
        print(response.text)
        print("--- END RESPONSE ---")

    # Check for messages (tool calls happen in messages)
    if hasattr(response, 'messages') and response.messages:
        print(f"\n--- TOOL CALLS ({len(response.messages)} messages) ---")
        for i, msg in enumerate(response.messages):
            role = getattr(msg, 'role', 'unknown')
            if hasattr(msg, 'contents') and msg.contents:
                for content in msg.contents:
                    content_type = type(content).__name__
                    # Show tool calls
                    if hasattr(content, 'name') and content.name:
                        print(f"  [{role}] Tool: {content.name}")
                        if hasattr(content, 'arguments') and content.arguments:
                            args = str(content.arguments)[:150]
                            print(f"         Args: {args}...")
                    # Show tool results (abbreviated)
                    elif content_type == 'FunctionCallResultContent':
                        if hasattr(content, 'result'):
                            result = str(content.result)[:100]
                            print(f"  [result] {result}...")

    print("=" * 60)


async def main():
    """Main entry point."""
    # Default test values
    client_id = "TEST_CLIENT"
    mapping_path = "TEST_CLIENT/mapping.xlsx"
    data_path = "TEST_CLIENT/transactions.csv"
    output_path = "TEST_CLIENT/output_maf"

    # Allow override from command line
    if len(sys.argv) > 1:
        client_id = sys.argv[1]
    if len(sys.argv) > 2:
        mapping_path = sys.argv[2]
    if len(sys.argv) > 3:
        data_path = sys.argv[3]
    if len(sys.argv) > 4:
        output_path = sys.argv[4]

    await run_transform(client_id, mapping_path, data_path, output_path)


if __name__ == "__main__":
    asyncio.run(main())
