#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../.env"

echo "=== Creating Databricks Workspace (Standard Tier) ==="

az databricks workspace create \
  --name "$DATABRICKS_WORKSPACE_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --sku standard \
  --only-show-errors

echo "Databricks workspace '$DATABRICKS_WORKSPACE_NAME' created."

DATABRICKS_URL=$(az databricks workspace show \
  --name "$DATABRICKS_WORKSPACE_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query workspaceUrl -o tsv)

echo "Workspace URL: https://$DATABRICKS_URL"

echo "=== Databricks setup complete ==="
