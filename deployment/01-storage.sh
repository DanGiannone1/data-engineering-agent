#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../.env"

echo "=== Creating ADLS Gen2 Storage Account ==="

az storage account create \
  --name "$STORAGE_ACCOUNT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --sku Standard_LRS \
  --kind StorageV2 \
  --hns true \
  --access-tier Hot \
  --only-show-errors

echo "Storage account '$STORAGE_ACCOUNT_NAME' created."

for CONTAINER in mappings data output audit-trail; do
  echo "Creating container: $CONTAINER"
  az storage container create \
    --name "$CONTAINER" \
    --account-name "$STORAGE_ACCOUNT_NAME" \
    --auth-mode login \
    --only-show-errors
done

echo "=== Storage setup complete ==="
