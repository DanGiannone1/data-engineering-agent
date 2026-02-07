#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../.env"

echo "=== Creating Log Analytics Workspace ==="

az monitor log-analytics workspace create \
  --workspace-name "$LOG_ANALYTICS_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --sku PerGB2018 \
  --only-show-errors

echo "Log Analytics workspace '$LOG_ANALYTICS_NAME' created."

LOG_ANALYTICS_ID=$(az monitor log-analytics workspace show \
  --workspace-name "$LOG_ANALYTICS_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query id -o tsv)

echo "=== Creating Application Insights ==="

az monitor app-insights component create \
  --app "$APP_INSIGHTS_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --workspace "$LOG_ANALYTICS_ID" \
  --kind web \
  --only-show-errors

echo "Application Insights '$APP_INSIGHTS_NAME' created."

echo "=== Monitoring setup complete ==="
