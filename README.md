# Data Engineering Agent

AI agent that automates data transformations for audit engagements. Auditors upload source data and a column mapping; the agent profiles the data, generates pseudocode for review, produces PySpark code, executes it on Databricks, validates the output, and saves the approved transformation for reuse.

## Architecture

- **Agent Runtime:** Azure Durable Functions (Flex Consumption) with a 6-phase orchestrator
- **C# Backend:** .NET 8 isolated worker (primary) — `src-dotnet/`
- **Python Backend:** Python 3.11 (alternative) — `src-python/`
- **LLM:** Azure OpenAI (`gpt-4.1`) via `DefaultAzureCredential`
- **Spark:** Azure Databricks (Jobs Compute via REST API)
- **Storage:** ADLS Gen2 (mappings, source data, output)
- **State:** Cosmos DB Serverless (conversation history)
- **Approved Code:** Git repo (`approved-code/{client_id}/`)
- **Frontend:** Next.js (chat UI with approval controls)

### Agent Workflow

1. **Change detection** — LLM compares current inputs against stored pseudocode to decide if a new transform is needed or cached code can be reused
2. **Data profiling** — samples source data, generates pseudocode describing the transformation
3. **Auditor review** — conversational review of pseudocode (orchestrator waits for external event)
4. **Code generation + Spark execution** — generates PySpark, uploads notebook to Databricks, runs it (up to 5 retries with error log passback)
5. **Integrity checks** — deterministic validation (row count, schema, nulls, duplicates)
6. **Final review** — auditor approves output or loops back to step 3

## Prerequisites

- **Azure CLI** >= 2.60 (`az --version`)
- **Azure Functions Core Tools** v4 (`func --version`)
- **.NET 8 SDK** (`dotnet --version`) — for C# backend
- **Python** 3.11 — for Python backend
- **Node.js** >= 18 — for frontend
- An Azure subscription with permissions to create resources
- An **Azure OpenAI** resource with a `gpt-4.1` model deployment (create this manually in Azure AI Foundry — not automated by the deployment scripts)

## Infrastructure Setup

### 1. Configure environment variables

```bash
cp deployment/.env.example .env
```

Edit `.env` with your values. The deployment scripts source this file.

**Storage account names must be globally unique and 3-24 lowercase alphanumeric characters only** (no hyphens). Pick names that won't collide.

### 2. Log in to Azure

```bash
az login
az account set --subscription <your-subscription-id>
```

The deploying user needs **Owner** or **Contributor + User Access Administrator** on the subscription (the RBAC script creates role assignments).

The storage script uses `--auth-mode login` for container creation, so the deploying user also needs **Storage Blob Data Contributor** on the new storage account. If your subscription enforces `allowSharedKeyAccess = false`, this is the only auth path that works.

### 3. Deploy all resources

```bash
bash deployment/deploy-all.sh
```

This runs the scripts in order:

| Script | Creates |
|--------|---------|
| `01-storage.sh` | ADLS Gen2 storage account + containers (mappings, data, output, audit-trail) |
| `02-cosmos.sh` | Cosmos DB Serverless account + `agent-db` database + `conversations` container |
| `03-monitoring.sh` | Log Analytics workspace + Application Insights |
| `04-function-app.sh` | Function App (Flex Consumption, system-assigned Managed Identity) + app settings |
| `05-databricks.sh` | Databricks workspace (Standard tier) |
| `06-rbac.sh` | RBAC role assignments for Function App's Managed Identity + sets DATABRICKS_HOST app setting |

### 4. Create the Databricks Service Principal

The Databricks cluster needs a service principal to write output to ADLS. This is **not automated** by the deployment scripts.

1. In **Entra ID > App registrations**, create a new registration (e.g., `dea-databricks-sp`)
2. Under **Certificates & secrets**, create a client secret and save the value
3. Grant the SP **Storage Blob Data Contributor** on your ADLS storage account:
   ```bash
   # Get the SP's object ID
   SP_OBJECT_ID=$(az ad sp show --id <sp-client-id> --query id -o tsv)

   # Get storage account resource ID
   STORAGE_ID=$(az storage account show --name <storage-account> --resource-group <rg> --query id -o tsv)

   az role assignment create \
     --assignee "$SP_OBJECT_ID" \
     --role "Storage Blob Data Contributor" \
     --scope "$STORAGE_ID"
   ```
4. Add the SP credentials as Function App settings:
   ```bash
   az functionapp config appsettings set \
     --name <function-app-name> \
     --resource-group <rg> \
     --settings \
       DATABRICKS_SP_CLIENT_ID=<sp-client-id> \
       DATABRICKS_SP_SECRET=<sp-client-secret> \
       DATABRICKS_SP_TENANT=<your-tenant-id>
   ```

### 5. Upload sample data (optional)

```bash
python scripts/upload_sample_data.py
```

This uploads test mapping + source data files to the `mappings` and `data` containers in ADLS.

## Local Development

### C# Backend (primary)

```bash
cd src-dotnet
dotnet build
cd src/DataEngineeringAgent.Functions
func start
```

Create `src-dotnet/src/DataEngineeringAgent.Functions/local.settings.json`:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage__accountName": "<function-storage-account>",
    "FUNCTIONS_WORKER_RUNTIME": "dotnet-isolated",
    "AZURE_OPENAI_ENDPOINT": "https://<your-resource>.cognitiveservices.azure.com",
    "AZURE_OPENAI_DEPLOYMENT": "gpt-4.1",
    "COSMOS_ENDPOINT": "https://<cosmos-account>.documents.azure.com:443/",
    "COSMOS_DATABASE": "agent-db",
    "ADLS_ACCOUNT_NAME": "<storage-account>",
    "DATABRICKS_HOST": "https://<workspace-url>.azuredatabricks.net",
    "DATABRICKS_SP_CLIENT_ID": "<sp-client-id>",
    "DATABRICKS_SP_SECRET": "<sp-client-secret>",
    "DATABRICKS_SP_TENANT": "<tenant-id>"
  }
}
```

### Python Backend (alternative)

```bash
cd src-python
pip install -r requirements.txt
func start
```

Create `src-python/local.settings.json` with the same keys (use `"FUNCTIONS_WORKER_RUNTIME": "python"`).

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs at `http://localhost:3001`. Set `NEXT_PUBLIC_API_URL=http://localhost:7071/api` in `frontend/.env.local` to point at the local backend.

The dashboard accepts a **Client ID** (e.g., `CLIENT_001`) and derives the mapping/data paths automatically.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/transform` | Start a new transformation (`client_id`, `mapping_path`, `data_path`) |
| `GET` | `/api/transform/{id}/status` | Get orchestration status and current phase |
| `POST` | `/api/transform/{id}/review` | Submit review (`approved: true/false`, optional `feedback`) |
| `GET` | `/api/transform/{id}/messages` | Get conversation history for chat UI |

### Example: trigger a transform

```bash
curl -X POST http://localhost:7071/api/transform \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "CLIENT_001",
    "mapping_path": "mappings/CLIENT_001/mapping.xlsm",
    "data_path": "data/CLIENT_001/transactions.xlsx"
  }'
```

## Project Structure

```
src-dotnet/                # C# backend (.NET 8 isolated worker)
  src/
    DataEngineeringAgent.Functions/   # Azure Functions entry point
    DataEngineeringAgent.Core/        # Business logic, services, models
  tests/                              # Unit + integration tests
src-python/                # Python backend (Azure Functions)
  function_app.py          # HTTP triggers + orchestrator + activity registration
  orchestrator/transform.py # 6-phase durable orchestrator
  activities/              # Phase implementations
  agent/                   # OpenAI client, prompts, runner
  clients/                 # Azure SDK wrappers (ADLS, Cosmos, Databricks)
  models/                  # Pydantic schemas
  tools/                   # Direct function tools
  tests/                   # Unit + E2E tests
frontend/                  # Next.js UI (chat + approval controls)
deployment/                # Azure CLI deployment scripts
scripts/                   # Test/utility scripts
approved-code/             # Persisted approved transforms per client
docs/                      # Design docs, cost analysis, requirements
```

## Teardown

```bash
bash deployment/teardown.sh
```

Deletes all deployed resources. Prompts for confirmation before proceeding.
