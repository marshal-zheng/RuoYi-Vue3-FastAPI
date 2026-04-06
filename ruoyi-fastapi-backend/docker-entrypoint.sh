#!/bin/bash
# Docker entrypoint script for RuoYi-FastAPI backend
# Handles the unified formal deploy chain before starting the application

set -e

echo "=========================================="
echo "RuoYi-FastAPI Backend Initialization"
echo "=========================================="
echo "Environment: ${APP_ENV:-prod}"
echo "Skip DB Init: ${SKIP_DB_INIT:-false}"
echo ""

# Skip database initialization if requested
if [ "${SKIP_DB_INIT}" = "true" ]; then
    echo "SKIP_DB_INIT=true, skipping database initialization"
else
    # Step 1: Wait for database
    echo "[1/3] Waiting for database..."
    if python scripts/db.py wait-db; then
        echo "Database is ready!"
    else
        echo "ERROR: Database connection failed"
        exit 1
    fi

    # Step 2: Run the formal deploy chain
    echo ""
    echo "[2/3] Running formal database deploy chain..."
    echo "Docker/shared/test/staging/prod/customer upgrades use deploy --revision head only"
    if python scripts/db.py deploy --revision head; then
        echo "Formal deploy chain completed successfully"
    else
        echo "ERROR: Formal deploy chain failed"
        exit 1
    fi

    # Step 3: Seed bootstrap-only data after baseline bundles are deployed
    echo ""
    echo "[3/3] Seeding bootstrap-only data..."
    echo "Fresh install order: schema migration -> baseline bundles -> bootstrap seed"
    if python scripts/db.py bootstrap-seed --env "${APP_ENV:-prod}"; then
        echo "Bootstrap seed loaded successfully"
    else
        echo "ERROR: Bootstrap seed loading failed"
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "Database initialization complete"
echo "Starting application..."
echo "=========================================="
echo ""

# Execute the main command (passed as arguments)
exec "$@"
