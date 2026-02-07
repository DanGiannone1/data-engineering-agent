# Agent Runtime Setup & Decision Log

**Date:** February 6, 2026
**Status:** Pivoting to Microsoft Agent Framework

---

## Decision: GitHub Copilot SDK → Microsoft Agent Framework

### Context

In January 2026, we validated the GitHub Copilot SDK as a viable agentic harness for this project. The SDK worked well in testing (see historical validation below). However, after evaluating production timeline risks, we are pivoting to the **Microsoft Agent Framework** as our agent runtime.

### Why We're Moving Away from Copilot SDK

| Factor | Copilot SDK | Agent Framework |
|--------|-------------|-----------------|
| **GA Status** | Still in preview (no confirmed GA date) | Azure AI Foundry Agent Service: **GA since May 2025**; SDK: GA targeted Q1 2026 |
| **Production Risk** | Customer cannot go live on a preview SDK | 10,000+ orgs already using Foundry Agent Service in production |
| **Pricing** | $39/month flat subscription per seat | $0 platform fee — pure per-token consumption |
| **Cost at 100 runs/month** | $39/month (fixed) | ~$7/month (consumption) — **82% cheaper** |
| **Human-in-the-Loop** | Custom implementation needed | Built-in workflow checkpointing |
| **State Persistence** | Custom implementation needed | Built-in `ChatMessageStore` with Cosmos DB support |
| **Observability** | Custom logging | Built-in OpenTelemetry tracing |
| **Migration Path** | N/A | Can wrap Copilot SDK as `GitHubCopilotAgent` if it reaches GA later |

### Decision

**Use Microsoft Agent Framework with `AzureOpenAIResponsesClient` as the primary LLM backend.**

This gives us:
- Direct Azure OpenAI access via Managed Identity (no API keys)
- Consumption-based pricing (pay only for tokens used)
- Production-grade workflow orchestration with checkpointing
- Built-in MCP support for custom tools
- OpenTelemetry tracing for audit compliance
- Path to wrap Copilot SDK later if it reaches GA

---

## Microsoft Agent Framework Setup

### Installation

```bash
# Install Agent Framework (preview — use --pre flag until GA)
pip install agent-framework --pre

# Or install specific sub-packages
pip install agent-framework-core --pre
pip install agent-framework-azure-ai --pre
```

**Requirements:**
- Python >= 3.10
- Azure OpenAI resource deployed with GPT-4o and/or GPT-4o-mini
- Azure Managed Identity (for Container Apps deployment) or Azure CLI credential (for local dev)

### Basic Agent Setup

```python
from agent_framework.azure import AzureOpenAIResponsesClient
from agent_framework import ChatAgent, MCPStdioTool
from azure.identity import DefaultAzureCredential

# Initialize Azure OpenAI client (uses Managed Identity in production)
client = AzureOpenAIResponsesClient(
    credential=DefaultAzureCredential(),
    azure_endpoint="https://<resource>.openai.azure.com",
    model="gpt-4o",
)

# Create agent
agent = client.as_agent(
    name="DataEngineeringAgent",
    instructions="You are a data engineering agent that profiles data, "
                 "generates transformation pseudocode, and creates PySpark code.",
)

# Run with MCP tools
async with (
    MCPStdioTool(name="adls-tools", command="python", args=["mcp_adls_server.py"]) as adls,
    agent,
):
    result = await agent.run(
        "Profile the source data and analyze the mapping spreadsheet.",
        tools=[adls],
    )
```

### Workflow with Human-in-the-Loop Checkpointing

```python
from agent_framework.workflows import Workflow, checkpoint
from agent_framework.workflows.storage import FileCheckpointStorage

class TransformationWorkflow(Workflow):
    async def run(self, client_id: str, mapping_path: str):
        # Phase 2: Profile data + generate pseudocode
        pseudocode = await self.agent.run(
            f"Profile data and generate pseudocode for {client_id}"
        )

        # Phase 3: Checkpoint — pause for human review
        approval = await checkpoint("pseudocode_review", {
            "pseudocode": pseudocode,
            "client_id": client_id,
        })

        if not approval.approved:
            pseudocode = await self.agent.run(
                f"Revise pseudocode based on feedback: {approval.feedback}"
            )

        # Phase 4: Generate PySpark + execute
        pyspark = await self.agent.run(
            f"Generate PySpark from approved pseudocode: {pseudocode}"
        )

        # Phase 5: Agent integrity checks
        check_result = await self.agent.run(
            f"Run integrity checks on the output: row counts, schema, nulls"
        )

        # Phase 6: Final human review (only if checks pass)
        if check_result.passed:
            final = await checkpoint("final_review", {
                "integrity_report": check_result,
                "sample_output": sample_rows,
            })
```

---

## Historical: GitHub Copilot SDK Validation (January 2026)

> **Note:** This section preserved for reference. The Copilot SDK validation was successful and the technology works. We are moving away due to GA timeline risk, not technical issues.

### What Was Validated
- SDK version: `github-copilot-sdk==0.1.18`
- Copilot CLI: `v0.0.394`
- All event types working (PENDING_MESSAGES_MODIFIED, USER_MESSAGE, ASSISTANT_TURN_START/END, SESSION_USAGE_INFO, ASSISTANT_MESSAGE, ASSISTANT_REASONING, SESSION_IDLE)
- Multi-model routing confirmed (GPT-4, Claude, etc.)
- Session persistence and event-driven streaming operational
- MCP tool integration ready
- Windows-specific: must specify CLI path to `copilot.cmd` explicitly

### Test Script
`test_copilot_sdk.py` — demonstrates client init, session creation, message send, event handling. Still present in repo for reference.

### Why It Worked
The Copilot SDK provides a production-grade agentic harness with built-in planning, tool invocation, context management, and error recovery. It reduces the typical 4-6 month DIY development effort to hours.

### Why We're Not Using It (For Now)
- **Preview status**: No confirmed GA date as of February 2026
- **Customer timeline**: Production deployment cannot depend on a preview SDK
- **Agent Framework compatibility**: If Copilot SDK reaches GA, it can be used as a backend agent type (`GitHubCopilotAgent`) within the Agent Framework — so this isn't a permanent departure

---

## Next Steps

1. Set up Azure OpenAI resource with GPT-4o deployment
2. Build MCP tool servers for ADLS data access and Databricks job submission
3. Implement `TransformationWorkflow` with checkpointing and 3-try retry logic
4. Test end-to-end: profiling → pseudocode → auditor review → PySpark → integrity checks → auditor final review
5. Deploy to customer's existing compute (AKS or Azure Durable Functions) with Managed Identity
   - **Note:** Customer CTO org requires using existing tech stack (AKS, Durable Functions). Container Apps is a future roadmap option.
