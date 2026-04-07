#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/ruoyi-fastapi-backend"
FRONTEND_DIR="$ROOT_DIR/ruoyi-fastapi-frontend"

resolve_backend_python() {
    if [ -x "$BACKEND_DIR/.venv/bin/python" ]; then
        echo "$BACKEND_DIR/.venv/bin/python"
        return
    fi
    if [ -x "$BACKEND_DIR/venv/bin/python" ]; then
        echo "$BACKEND_DIR/venv/bin/python"
        return
    fi
    if command -v python3 >/dev/null 2>&1; then
        echo "python3"
        return
    fi
    echo "python"
}

BACKEND_PYTHON="$(resolve_backend_python)"
BACKEND_TESTS=(
    "$BACKEND_DIR/tests/unit/config/test_env.py"
    "$BACKEND_DIR/tests/unit/middlewares/test_request_logging_middleware.py"
    "$BACKEND_DIR/tests/unit/scripts/test_start_script.py"
    "$BACKEND_DIR/tests/unit/scripts/test_managed_data_fast_reconcile_service.py"
    "$BACKEND_DIR/tests/unit/scripts/test_db_workflow.py"
    "$BACKEND_DIR/tests/unit/scripts/test_workflow_verify_service.py"
    "$BACKEND_DIR/tests/unit/modules/test_registry.py"
    "$BACKEND_DIR/modules/system/tests/test_dev_menu_hot_sync_e2e.py"
    "$BACKEND_DIR/modules/system/tests/test_dev_menu_sync_runtime.py"
    "$BACKEND_DIR/modules/system/tests/test_dev_menu_event_broker.py"
    "$BACKEND_DIR/modules/system/tests/test_dev_menu_signature_service.py"
    "$BACKEND_DIR/modules/system/tests/test_dev_menu_sync_controller.py"
)
FRONTEND_TESTS=(
    "tests/unit/config/devMenuSync.test.ts"
    "tests/unit/stores/permission.test.ts"
    "tests/unit/plugins/devMenuHotSync.test.ts"
    "src/plugins/dev-menu-hot-sync.test.ts"
)

echo "[dev-menu-hot-sync] backend verification..."
"$BACKEND_PYTHON" -m pytest "${BACKEND_TESTS[@]}" -q --no-cov

echo "[dev-menu-hot-sync] frontend verification..."
(
  cd "$FRONTEND_DIR"
  yarn test:run "${FRONTEND_TESTS[@]}"
)

echo "[dev-menu-hot-sync] verification passed."
