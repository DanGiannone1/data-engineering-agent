#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../.env"

echo "=== Assigning Managed Identity RBAC Roles ==="

# Get Function App's Managed Identity principal ID
PRINCIPAL_ID=$(az functionapp identity show \
  --name "$FUNCTION_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query principalId -o tsv)

echo "Function App principal ID: $PRINCIPAL_ID"

# Storage Blob Data Contributor on ADLS Gen2
STORAGE_ID=$(az storage account show \
  --name "$STORAGE_ACCOUNT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query id -o tsv)

echo "Assigning Storage Blob Data Contributor..."
az role assignment create \
  --assignee "$PRINCIPAL_ID" \
  --role "Storage Blob Data Contributor" \
  --scope "$STORAGE_ID" \
  --only-show-errors

# Cosmos DB Built-in Data Contributor
COSMOS_ID=$(az cosmosdb show \
  --name "$COSMOS_ACCOUNT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query id -o tsv)

echo "Assigning Cosmos DB Built-in Data Contributor..."
az cosmosdb sql role assignment create \
  --account-name "$COSMOS_ACCOUNT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --principal-id "$PRINCIPAL_ID" \
  --role-definition-id "00000000-0000-0000-0000-000000000002" \
  --scope "$COSMOS_ID" \
  --only-show-errors

# Contributor on Databricks workspace
DATABRICKS_ID=$(az databricks workspace show \
  --name "$DATABRICKS_WORKSPACE_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query id -o tsv)

echo "Assigning Contributor on Databricks workspace..."
az role assignment create \
  --assignee "$PRINCIPAL_ID" \
  --role "Contributor" \
  --scope "$DATABRICKS_ID" \
  --only-show-errors

# Cognitive Services OpenAI User — scope to subscription (OpenAI resource may be in different RG)
echo "Assigning Cognitive Services OpenAI User..."
az role assignment create \
  --assignee "$PRINCIPAL_ID" \
  --role "Cognitive Services OpenAI User" \
  --scope "/subscriptions/$SUBSCRIPTION_ID" \
  --only-show-errors

# Set Databricks host URL as Function App setting (Databricks created in 05)
DATABRICKS_URL=$(az databricks workspace show \
  --name "$DATABRICKS_WORKSPACE_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query workspaceUrl -o tsv)

echo "Setting DATABRICKS_HOST app setting..."
az functionapp config appsettings set \
  --name "$FUNCTION_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --settings DATABRICKS_HOST="https://$DATABRICKS_URL" \
  --only-show-errors

echo "=== RBAC setup complete ==="
