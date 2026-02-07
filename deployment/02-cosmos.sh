#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../.env"

echo "=== Creating Cosmos DB Account (Free Tier) ==="

az cosmosdb create \
  --name "$COSMOS_ACCOUNT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --enable-free-tier true \
  --default-consistency-level Session \
  --only-show-errors

echo "Cosmos DB account '$COSMOS_ACCOUNT_NAME' created."

echo "Creating database: agent-db"
az cosmosdb sql database create \
  --account-name "$COSMOS_ACCOUNT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --name agent-db \
  --only-show-errors

echo "Creating container: approved-code (partition key: /client_id)"
az cosmosdb sql container create \
  --account-name "$COSMOS_ACCOUNT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --database-name agent-db \
  --name approved-code \
  --partition-key-path "/client_id" \
  --only-show-errors

echo "Creating container: agent-state (partition key: /thread_id)"
az cosmosdb sql container create \
  --account-name "$COSMOS_ACCOUNT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --database-name agent-db \
  --name agent-state \
  --partition-key-path "/thread_id" \
  --only-show-errors

echo "Creating container: audit-trail (partition key: /client_id)"
az cosmosdb sql container create \
  --account-name "$COSMOS_ACCOUNT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --database-name agent-db \
  --name audit-trail \
  --partition-key-path "/client_id" \
  --only-show-errors

echo "=== Cosmos DB setup complete ==="
