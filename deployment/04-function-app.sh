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

echo "=== Creating Function App (Flex Consumption) ==="

az functionapp create \
  --name "$FUNCTION_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --storage-account "$FUNC_STORAGE_NAME" \
  --flexconsumption-location "$LOCATION" \
  --runtime python \
  --runtime-version 3.11 \
  --assign-identity '[system]' \
  --only-show-errors

echo "Function App '$FUNCTION_APP_NAME' created (Flex Consumption, Managed Identity)."

echo "Configuring runtime app settings..."
az functionapp config appsettings set \
  --name "$FUNCTION_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --settings \
    AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
    AZURE_OPENAI_DEPLOYMENT="$AZURE_OPENAI_DEPLOYMENT" \
    COSMOS_ENDPOINT="https://${COSMOS_ACCOUNT_NAME}.documents.azure.com:443/" \
    COSMOS_DATABASE="agent-db" \
    ADLS_ACCOUNT_NAME="$STORAGE_ACCOUNT_NAME" \
  --only-show-errors

echo "=== Function App setup complete ==="
