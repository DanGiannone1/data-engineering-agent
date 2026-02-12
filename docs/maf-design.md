# Data Engineering Agent - MAF Design

**Date:** 2026-02-11
**Status:** Draft

---

## Overview

Refactor the data engineering agent to use Microsoft Agent Framework (MAF), aligning with the original design document. The agent should run as pure Python locally before deploying to Azure Functions.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Workflow (Graph-based)                       │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐     │
│  │ Change   │──▶│ Profiler │──▶│ Pseudocode│──▶│   Code   │     │
│  │ Detector │   │  Agent   │   │  Review   │   │Generator │     │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘     │
│                                     │              │            │
│                              [HITL Checkpoint]     │            │
│                                     ▼              ▼            │
│                              ┌──────────┐   ┌──────────┐        │
│                              │ Feedback │   │  Spark   │        │
│                              │  Loop    │   │ Executor │        │
│                              └──────────┘   └──────────┘        │
│                                                    │            │
│                                                    ▼            │
│                                             ┌──────────┐        │
│                                             │Integrity │        │
│                                             │ Checker  │        │
│                                             └──────────┘        │
│                                                    │            │
│                                             [HITL Checkpoint]   │
│                                                    ▼            │
│                                             ┌──────────┐        │
│                                             │  Output  │        │
│                                             │  Review  │        │
│                                             └──────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

## Installation

```bash
pip install agent-framework --pre
```

## Components

### 1. Agent Client Setup

```python
# src/agent/client.py
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import DefaultAzureCredential
import os

def get_agent_client() -> AzureOpenAIResponsesClient:
    """Get MAF client configured for Azure OpenAI."""
    return AzureOpenAIResponsesClient(
        endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        deployment_name=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        credential=DefaultAzureCredential(process_timeout=30),
    )
```

### 2. Tools (as Python Functions)

Tools are plain Python functions with type annotations. MAF auto-generates the schema.

```python
# src/tools/adls_tools.py
from typing import Annotated
from pydantic import Field

def read_mapping_spreadsheet(
    path: Annotated[str, Field(description="Path within mappings container, e.g. 'CLIENT_001/mapping.xlsx'")]
) -> dict:
    """Parse Excel mapping file from ADLS and return column mappings."""
    from clients.adls import download_file
    import openpyxl
    import io

    data = download_file("mappings", path)
    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    # ... parse and return
    return {"sheets": [...]}

def sample_source_data(
    path: Annotated[str, Field(description="Path within data container")],
    n_rows: Annotated[int, Field(description="Number of rows to sample")] = 100
) -> dict:
    """Read first N rows from source file on ADLS for profiling."""
    # ... implementation
    return {"columns": [...], "sample_rows": [...]}
```

### 3. Structured Output Models

```python
# src/models/agent_outputs.py
from pydantic import BaseModel, Field
from typing import Annotated

class ChangeDetectionResult(BaseModel):
    """Result of change detection phase."""
    needs_regeneration: bool
    reason: str
    existing_code: dict | None = None

class DataProfile(BaseModel):
    """Profiling results for a dataset."""
    columns: dict[str, dict]  # column_name -> {dtype, null_rate, unique_count, ...}
    row_count: int
    anomalies: list[str]

class Pseudocode(BaseModel):
    """Plain-English transformation plan."""
    summary: str
    steps: list[str]
    input_columns: list[str]
    output_columns: list[str]

class PySparkCode(BaseModel):
    """Generated PySpark transformation code."""
    code: str
    input_path: str
    output_path: str
```

### 4. Agents (Specialized by Phase)

```python
# src/agents/profiler.py
from agent_framework.azure import AzureOpenAIResponsesClient
from tools.adls_tools import read_mapping_spreadsheet, sample_source_data
from tools.profiling import profile_data
from models.agent_outputs import Pseudocode

PROFILER_INSTRUCTIONS = """You are a data engineering agent that:
1. Analyzes mapping spreadsheets to understand transformation rules
2. Profiles source data to identify types, patterns, and anomalies
3. Generates plain-English pseudocode transformation plans

Your pseudocode should be readable by non-technical auditors.
Structure it as numbered steps covering:
- Data reading and validation
- Column mapping and renaming
- Calculations and derived columns
- Filtering and business rules
- Output format
"""

def create_profiler_agent(client: AzureOpenAIResponsesClient):
    return client.as_agent(
        name="DataProfiler",
        instructions=PROFILER_INSTRUCTIONS,
        tools=[read_mapping_spreadsheet, sample_source_data, profile_data],
        response_format=Pseudocode,
    )
```

```python
# src/agents/code_generator.py
CODEGEN_INSTRUCTIONS = """You are a data engineering agent that converts
approved pseudocode into production PySpark code.

Requirements:
- Use PySpark DataFrame API (not RDDs)
- Read from abfss:// paths provided
- Write output as parquet
- Include proper error handling
- The code runs on Databricks - spark session is already available

Return ONLY valid Python code, no explanations.
"""

def create_codegen_agent(client: AzureOpenAIResponsesClient):
    return client.as_agent(
        name="CodeGenerator",
        instructions=CODEGEN_INSTRUCTIONS,
        response_format=PySparkCode,
    )
```

### 5. Executors (Workflow Nodes)

```python
# src/workflow/executors.py
from agent_framework import Executor, handler
from agent_framework.types import WorkflowContext

class ProfilerExecutor(Executor):
    """Profiles data and generates pseudocode."""

    def __init__(self, agent):
        super().__init__(id="profiler")
        self.agent = agent

    @handler
    async def handle(self, input: dict, ctx: WorkflowContext):
        client_id = input["client_id"]
        mapping_path = input["mapping_path"]
        data_path = input["data_path"]

        result = await self.agent.run(
            f"Profile the data at {data_path} using the mapping at {mapping_path} "
            f"for client {client_id}. Generate transformation pseudocode."
        )

        # Emit pseudocode for review
        await ctx.emit(result.value)  # Pseudocode model


class CodeGeneratorExecutor(Executor):
    """Generates PySpark from approved pseudocode."""

    def __init__(self, agent):
        super().__init__(id="code_generator")
        self.agent = agent

    @handler
    async def handle(self, pseudocode: Pseudocode, ctx: WorkflowContext):
        input_path = ctx.get_state("input_path")
        output_path = ctx.get_state("output_path")

        result = await self.agent.run(
            f"Generate PySpark code from this pseudocode:\n\n"
            f"{pseudocode.model_dump_json()}\n\n"
            f"Input: {input_path}\nOutput: {output_path}"
        )

        await ctx.emit(result.value)  # PySparkCode model
```

### 6. Workflow Definition

```python
# src/workflow/transform_workflow.py
from agent_framework import WorkflowBuilder, InMemoryCheckpointStorage
from agent_framework.orchestrations import SequentialBuilder
from workflow.executors import ProfilerExecutor, CodeGeneratorExecutor, SparkExecutor

def create_transform_workflow(client):
    """Create the transformation workflow with checkpointing."""

    # Create agents
    profiler_agent = create_profiler_agent(client)
    codegen_agent = create_codegen_agent(client)

    # Create executors
    profiler = ProfilerExecutor(profiler_agent)
    code_generator = CodeGeneratorExecutor(codegen_agent)
    spark_executor = SparkExecutor()
    integrity_checker = IntegrityCheckerExecutor()

    # Build workflow with checkpointing
    checkpoint_storage = InMemoryCheckpointStorage()  # Use CosmosCheckpointStorage for prod

    builder = WorkflowBuilder(
        start_executor=profiler,
        checkpoint_storage=checkpoint_storage
    )

    # Profiler -> [HITL Review] -> Code Generator
    builder.add_edge(profiler, code_generator)

    # Code Generator -> Spark Execution -> Integrity Checks
    builder.add_edge(code_generator, spark_executor)
    builder.add_edge(spark_executor, integrity_checker)

    # Integrity Checker -> [HITL Review] -> Done
    # (with retry loop back to code_generator on failure)

    return builder.build()
```

### 7. Local Runner (Pure Python)

```python
# run_local.py
"""
Run the data engineering agent locally as pure Python.
No Azure Functions required.
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from agent.client import get_agent_client
from workflow.transform_workflow import create_transform_workflow

async def main():
    # Create MAF client
    client = get_agent_client()

    # Create workflow
    workflow = create_transform_workflow(client)

    # Run with sample input
    input_data = {
        "client_id": "TEST_CLIENT",
        "mapping_path": "TEST_CLIENT/mapping.xlsx",
        "data_path": "TEST_CLIENT/transactions.csv",
    }

    print("Starting transformation workflow...")

    async for event in workflow.run_streaming(input_data):
        if hasattr(event, 'checkpoint'):
            print(f"Checkpoint: {event.checkpoint.checkpoint_id}")
        elif hasattr(event, 'data'):
            print(f"Output: {event.data}")
        elif hasattr(event, 'request'):
            # Human-in-the-loop request
            print(f"\n=== REVIEW REQUIRED ===")
            print(event.request.data)

            # For local testing, auto-approve or get input
            user_input = input("Approve? (y/n/feedback): ")
            if user_input.lower() == 'y':
                await event.respond(AgentRequestInfoResponse.approve())
            else:
                await event.respond(AgentRequestInfoResponse.from_strings([user_input]))

if __name__ == "__main__":
    asyncio.run(main())
```

## Migration Path

### Phase 1: Setup & Simple Agent
1. Install `agent-framework --pre`
2. Create `AzureOpenAIResponsesClient` wrapper
3. Port one agent (profiler) with tools
4. Test locally with `run_local.py`

### Phase 2: Structured Outputs
1. Define Pydantic models for each phase output
2. Add `response_format` to agents
3. Validate typed outputs

### Phase 3: Workflow
1. Create executors for each phase
2. Wire up workflow with `WorkflowBuilder`
3. Add checkpointing with `InMemoryCheckpointStorage`
4. Test full pipeline locally

### Phase 4: Human-in-the-Loop
1. Add HITL checkpoints at review points
2. Implement request/response handling
3. Test approval/feedback loops

### Phase 5: Production
1. Replace `InMemoryCheckpointStorage` with Cosmos-backed storage
2. Wrap workflow in Azure Durable Functions
3. Deploy and test

## Key Differences from Current Implementation

| Aspect | Current | MAF |
|--------|---------|-----|
| LLM calls | Raw `openai` SDK | `AzureOpenAIResponsesClient` |
| Tools | Manual prompt injection | `FunctionTool` with auto-schema |
| Orchestration | Durable Functions only | Workflow graph + Durable Functions |
| Outputs | String parsing | Typed Pydantic models |
| State | Manual Cosmos writes | Built-in checkpointing |
| HITL | External events | Native request/response |

## Sources

- [Agent Framework Overview](https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview)
- [Workflows Documentation](https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/overview)
- [Checkpoints](https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/checkpoints)
- [Human-in-the-Loop](https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/orchestrations/human-in-the-loop)
- [Azure OpenAI Responses Agent](https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-types/azure-openai-responses-agent)
- [GitHub Repository](https://github.com/microsoft/agent-framework)
- [Samples Repository](https://github.com/microsoft/Agent-Framework-Samples)
