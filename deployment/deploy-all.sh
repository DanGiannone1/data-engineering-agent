#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../.env"

echo "============================================"
echo " Data Engineering Agent — POC Deployment"
echo "============================================"
echo ""
echo "Resource Group: $RESOURCE_GROUP"
echo "Location:       $LOCATION"
echo "Subscription:   $SUBSCRIPTION_ID"
echo ""

# Verify Azure CLI is logged in
if ! az account show &>/dev/null; then
  echo "ERROR: Not logged in to Azure CLI. Run 'az login' first."
  exit 1
fi

# Set subscription
az account set --subscription "$SUBSCRIPTION_ID"
echo "Subscription set to $SUBSCRIPTION_ID"
echo ""

# Create resource group if it doesn't exist
echo "Ensuring resource group '$RESOURCE_GROUP' exists..."
az group create \
  --name "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --only-show-errors
echo ""

# Run deployment scripts in order
for script in 01-storage.sh 02-cosmos.sh 03-monitoring.sh 04-function-app.sh 05-databricks.sh 06-rbac.sh; do
  echo ""
  echo ">>> Running $script ..."
  echo ""
  bash "$SCRIPT_DIR/$script"
done

echo ""
echo "============================================"
echo " Deployment Complete — Resource Summary"
echo "============================================"
echo ""
az resource list --resource-group "$RESOURCE_GROUP" --output table
