#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../.env"

FUNC_STORAGE_NAME="${STORAGE_ACCOUNT_NAME}func"

echo "============================================"
echo " Data Engineering Agent — POC Teardown"
echo "============================================"
echo ""
echo "This will DELETE the following resources in '$RESOURCE_GROUP':"
echo "  - Databricks workspace: $DATABRICKS_WORKSPACE_NAME"
echo "  - Function App:         $FUNCTION_APP_NAME"
echo "  - Function storage:     $FUNC_STORAGE_NAME"
echo "  - App Insights:         $APP_INSIGHTS_NAME"
echo "  - Log Analytics:        $LOG_ANALYTICS_NAME"
echo "  - Cosmos DB:            $COSMOS_ACCOUNT_NAME"
echo "  - Storage account:      $STORAGE_ACCOUNT_NAME"
echo ""
read -rp "Are you sure? (y/N): " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
  echo "Aborted."
  exit 0
fi

echo ""

echo "Deleting Databricks workspace..."
az databricks workspace delete \
  --name "$DATABRICKS_WORKSPACE_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --yes --no-wait \
  --only-show-errors 2>/dev/null || echo "  (not found or already deleted)"

echo "Deleting Function App..."
az functionapp delete \
  --name "$FUNCTION_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --only-show-errors 2>/dev/null || echo "  (not found or already deleted)"

echo "Deleting Function storage account..."
az storage account delete \
  --name "$FUNC_STORAGE_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --yes \
  --only-show-errors 2>/dev/null || echo "  (not found or already deleted)"

echo "Deleting Application Insights..."
az monitor app-insights component delete \
  --app "$APP_INSIGHTS_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --only-show-errors 2>/dev/null || echo "  (not found or already deleted)"

echo "Deleting Log Analytics workspace..."
az monitor log-analytics workspace delete \
  --workspace-name "$LOG_ANALYTICS_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --yes --force \
  --only-show-errors 2>/dev/null || echo "  (not found or already deleted)"

echo "Deleting Cosmos DB account..."
az cosmosdb delete \
  --name "$COSMOS_ACCOUNT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --yes \
  --only-show-errors 2>/dev/null || echo "  (not found or already deleted)"

echo "Deleting Storage account..."
az storage account delete \
  --name "$STORAGE_ACCOUNT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --yes \
  --only-show-errors 2>/dev/null || echo "  (not found or already deleted)"

echo ""
echo "============================================"
echo " Teardown complete"
echo "============================================"
echo ""
echo "Remaining resources in '$RESOURCE_GROUP':"
az resource list --resource-group "$RESOURCE_GROUP" --output table 2>/dev/null || echo "(none)"
