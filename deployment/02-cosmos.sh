#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../.env"

echo "=== Creating Cosmos DB Account (Serverless) ==="

az cosmosdb create \
  --name "$COSMOS_ACCOUNT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --locations regionName="$LOCATION" failoverPriority=0 \
  --capabilities EnableServerless \
  --default-consistency-level Session \
  --only-show-errors

echo "Cosmos DB account '$COSMOS_ACCOUNT_NAME' created."

echo "Creating database: agent-db"
az cosmosdb sql database create \
  --account-name "$COSMOS_ACCOUNT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --name agent-db \
  --only-show-errors

echo "Creating container: conversations (partition key: /thread_id)"
az cosmosdb sql container create \
  --account-name "$COSMOS_ACCOUNT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --database-name agent-db \
  --name conversations \
  --partition-key-path "/thread_id" \
  --only-show-errors

echo "=== Cosmos DB setup complete ==="
