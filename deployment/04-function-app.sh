#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../.env"

FUNC_STORAGE_NAME="${STORAGE_ACCOUNT_NAME}func"

echo "=== Creating Function App Storage Account ==="

az storage account create \
  --name "$FUNC_STORAGE_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --sku Standard_LRS \
  --kind StorageV2 \
  --only-show-errors

echo "Function App storage account '$FUNC_STORAGE_NAME' created."

APP_INSIGHTS_KEY=$(az monitor app-insights component show \
  --app "$APP_INSIGHTS_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query instrumentationKey -o tsv)

echo "=== Creating Function App (Consumption Plan) ==="

az functionapp create \
  --name "$FUNCTION_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --storage-account "$FUNC_STORAGE_NAME" \
  --consumption-plan-location "$LOCATION" \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --os-type Linux \
  --app-insights "$APP_INSIGHTS_NAME" \
  --app-insights-key "$APP_INSIGHTS_KEY" \
  --only-show-errors

echo "Function App '$FUNCTION_APP_NAME' created."

echo "Enabling system-assigned Managed Identity..."
az functionapp identity assign \
  --name "$FUNCTION_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --only-show-errors

echo "=== Function App setup complete ==="
