#!/bin/bash
# Docker entrypoint script for RuoYi-FastAPI backend
# Handles database initialization before starting the application

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
    if python scripts/wait_for_db.py; then
        echo "Database is ready!"
    else
        echo "ERROR: Database connection failed"
        exit 1
    fi

    # Step 2: Run Alembic migrations
    echo ""
    echo "[2/3] Running database migrations..."
    if python -m alembic upgrade head; then
        echo "Migrations completed successfully"
    else
        echo "ERROR: Migration failed"
        exit 1
    fi

    # Step 3: Seed initial data
    echo ""
    echo "[3/3] Seeding initial data..."
    if python scripts/seed_data.py --env "${APP_ENV:-prod}"; then
        echo "Seed data loaded successfully"
    else
        echo "WARNING: Seed data loading failed (may already exist)"
        # Don't exit on seed failure - data might already exist
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
