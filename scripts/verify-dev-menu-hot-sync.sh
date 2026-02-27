#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "[dev-menu-hot-sync] backend verification..."
"$ROOT_DIR/ruoyi-fastapi-backend/venv/bin/pytest" \
  "$ROOT_DIR/ruoyi-fastapi-backend/modules/system/tests/test_dev_menu_hot_sync_e2e.py" \
  "$ROOT_DIR/ruoyi-fastapi-backend/modules/system/tests/test_dev_menu_sync_runtime.py" \
  "$ROOT_DIR/ruoyi-fastapi-backend/modules/system/tests/test_dev_menu_reconcile_service.py" \
  "$ROOT_DIR/ruoyi-fastapi-backend/modules/system/tests/test_dev_menu_signature_service.py" \
  "$ROOT_DIR/ruoyi-fastapi-backend/modules/system/tests/test_dev_menu_sync_controller.py" \
  "$ROOT_DIR/ruoyi-fastapi-backend/tests/test_menu_seed_scope.py" \
  "$ROOT_DIR/ruoyi-fastapi-backend/tests/unit/modules/test_registry.py" \
  -q --no-cov

echo "[dev-menu-hot-sync] frontend verification..."
(
  cd "$ROOT_DIR/ruoyi-fastapi-frontend"
  yarn test:run \
    tests/unit/config/devMenuSync.test.ts \
    tests/unit/stores/permission.test.ts \
    tests/unit/plugins/devMenuHotSync.test.ts
)

echo "[dev-menu-hot-sync] verification passed."
