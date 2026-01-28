#!/bin/bash
# Database Migration Management Script
# Manages Alembic migrations, seed data, and database operations

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

function print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

function print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

function print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

function print_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# Load environment variables
function load_environment() {
    local env="${ENV:-dev}"
    local env_file=".env.${env}"
    
    if [ -f "$env_file" ]; then
        print_debug "Loading environment from $env_file"
        # Export variables from .env file, handling Python-style format (KEY = 'value')
        # Remove spaces around = and quotes, then export
        while IFS= read -r line || [ -n "$line" ]; do
            # Skip comments and empty lines
            [[ "$line" =~ ^[[:space:]]*# ]] && continue
            [[ -z "${line// }" ]] && continue
            
            # Extract key and value, removing spaces and quotes
            if [[ "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=[[:space:]]*(.+)[[:space:]]*$ ]]; then
                key="${BASH_REMATCH[1]}"
                value="${BASH_REMATCH[2]}"
                # Remove surrounding quotes if present
                value="${value#\'}"
                value="${value%\'}"
                value="${value#\"}"
                value="${value%\"}"
                # Remove trailing spaces
                value="${value%"${value##*[![:space:]]}"}"
                export "$key=$value"
            fi
        done < "$env_file"
    else
        print_warn "Environment file $env_file not found, using defaults"
    fi
}

# Activate virtual environment if it exists
function activate_venv() {
    if [ -d "venv" ]; then
        print_debug "Activating virtual environment"
        source venv/bin/activate
        # Verify python and alembic are available
        if ! command -v python &> /dev/null; then
            print_error "Python not found in virtual environment"
            exit 1
        fi
        if ! python -m alembic --version &> /dev/null; then
            print_error "Alembic not found in virtual environment"
            print_error "Please install alembic: pip install alembic"
            exit 1
        fi
    elif [ -d ".venv" ]; then
        print_debug "Activating virtual environment"
        source .venv/bin/activate
        # Verify python and alembic are available
        if ! command -v python &> /dev/null; then
            print_error "Python not found in virtual environment"
            exit 1
        fi
        if ! python -m alembic --version &> /dev/null; then
            print_error "Alembic not found in virtual environment"
            print_error "Please install alembic: pip install alembic"
            exit 1
        fi
    else
        print_debug "No virtual environment found, using system Python"
        # Check if python and alembic are available
        if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
            print_error "Python not found"
            exit 1
        fi
        if ! python -m alembic --version &> /dev/null; then
            print_error "Alembic not found"
            print_error "Please install alembic: pip install alembic"
            exit 1
        fi
    fi
}

function show_help() {
    cat << EOF
${GREEN}Database Migration Management Tool${NC}

${BLUE}Usage:${NC}
    ./scripts/db_migrate.sh <command> [options]

${BLUE}Commands:${NC}
    ${GREEN}create${NC} <message>      Create a new migration script
                            Example: ./scripts/db_migrate.sh create "Add user avatar field"
    
    ${GREEN}upgrade${NC} [revision]    Apply migrations up to specified revision (default: head)
                            Example: ./scripts/db_migrate.sh upgrade
                            Example: ./scripts/db_migrate.sh upgrade abc123
    
    ${GREEN}downgrade${NC} [steps]     Rollback migrations by specified steps (default: -1)
                            Example: ./scripts/db_migrate.sh downgrade -1
                            Example: ./scripts/db_migrate.sh downgrade -2
    
    ${GREEN}current${NC}               Display current database revision
    
    ${GREEN}history${NC}               Display migration history with details
    
    ${GREEN}reset${NC}                 Reset database to initial state (drops all tables and re-runs migrations)
                            ${YELLOW}WARNING: This will delete all data!${NC}
    
    ${GREEN}stamp${NC} <revision>      Mark database as being at a specific revision without running migrations
                            Example: ./scripts/db_migrate.sh stamp head
                            Example: ./scripts/db_migrate.sh stamp abc123
    
    ${GREEN}data-migrate${NC} [range]  Run data migration scripts for specified revision range
                            Example: ./scripts/db_migrate.sh data-migrate
                            Example: ./scripts/db_migrate.sh data-migrate abc123:def456
    
    ${GREEN}repair${NC}                Repair corrupted migration history
                            Use when alembic_version table is out of sync
    
    ${GREEN}help${NC}                  Show this help message

${BLUE}Environment Variables:${NC}
    ENV                     Environment to use (dev, prod, staging) - default: dev
                            Example: ENV=prod ./scripts/db_migrate.sh upgrade

${BLUE}Examples:${NC}
    # Create a new migration
    ./scripts/db_migrate.sh create "Add user avatar field"
    
    # Apply all pending migrations
    ./scripts/db_migrate.sh upgrade
    
    # Rollback last migration
    ./scripts/db_migrate.sh downgrade -1
    
    # Check current database version
    ./scripts/db_migrate.sh current
    
    # View migration history
    ./scripts/db_migrate.sh history
    
    # Reset database (development only)
    ./scripts/db_migrate.sh reset
    
    # Stamp database at current code revision (for existing databases)
    ./scripts/db_migrate.sh stamp head
    
    # Run data migrations
    ./scripts/db_migrate.sh data-migrate
    
    # Repair migration history
    ./scripts/db_migrate.sh repair

${BLUE}Notes:${NC}
    - All commands automatically load environment variables from .env.\${ENV} files
    - Virtual environment is automatically activated if present
    - Destructive operations (reset, downgrade) require confirmation
    - For production use, always test migrations in staging first

EOF
}

function create_migration() {
    local message="$1"
    if [ -z "$message" ]; then
        print_error "Migration message is required"
        echo "Usage: ./scripts/db_migrate.sh create \"migration description\""
        exit 1
    fi
    
    print_info "Creating migration: $message"
    if python -m alembic revision --autogenerate -m "$message"; then
        print_info "✅ Migration script created successfully"
        print_info "Please review the generated migration in alembic/versions/ directory"
    else
        print_error "Failed to create migration"
        exit 1
    fi
}

function upgrade_db() {
    local revision="${1:-head}"
    print_info "Applying migrations to: $revision"
    
    if python -m alembic upgrade "$revision"; then
        print_info "✅ Migrations applied successfully"
    else
        print_error "Migration failed"
        print_error "Database may be in an inconsistent state"
        print_error "Check the error message above and fix the issue"
        exit 1
    fi
}

function downgrade_db() {
    local steps="${1:--1}"
    print_warn "⚠️  Rolling back migrations: $steps"
    print_warn "This operation may result in data loss"
    read -p "Are you sure you want to continue? (yes/no): " -r
    echo
    
    if [[ $REPLY == "yes" ]]; then
        if python -m alembic downgrade "$steps"; then
            print_info "✅ Rollback completed successfully"
        else
            print_error "Rollback failed"
            exit 1
        fi
    else
        print_info "Operation cancelled"
        exit 0
    fi
}

function show_current() {
    print_info "Current database revision:"
    if python -m alembic current; then
        :
    else
        print_error "Failed to get current revision"
        print_error "Database may not be initialized or alembic_version table may be missing"
        exit 1
    fi
}

function show_history() {
    print_info "Migration history:"
    if python -m alembic history --verbose; then
        :
    else
        print_error "Failed to retrieve migration history"
        exit 1
    fi
}

function reset_db() {
    print_warn "⚠️  WARNING: This will drop all tables and re-initialize the database"
    print_warn "⚠️  ALL DATA WILL BE LOST!"
    echo
    read -p "Type 'yes' to confirm database reset: " -r
    echo
    
    if [[ $REPLY == "yes" ]]; then
        print_info "Step 1/3: Rolling back to base..."
        if python -m alembic downgrade base; then
            print_info "✅ Rollback to base completed"
        else
            print_error "Failed to rollback to base"
            exit 1
        fi
        
        print_info "Step 2/3: Applying all migrations..."
        if python -m alembic upgrade head; then
            print_info "✅ Migrations applied"
        else
            print_error "Failed to apply migrations"
            exit 1
        fi
        
        print_info "Step 3/3: Seeding initial data..."
        if python scripts/seed_data.py --env "${ENV:-dev}"; then
            print_info "✅ Seed data loaded"
        else
            print_warn "Seed data loading failed or not available"
        fi
        
        print_info "✅ Database reset completed successfully"
    else
        print_info "Operation cancelled"
        exit 0
    fi
}

function stamp_db() {
    local revision="$1"
    if [ -z "$revision" ]; then
        print_error "Revision is required"
        echo "Usage: ./scripts/db_migrate.sh stamp <revision>"
        echo "Example: ./scripts/db_migrate.sh stamp head"
        exit 1
    fi
    
    print_info "Stamping database at revision: $revision"
    print_warn "This will mark the database as being at the specified revision"
    print_warn "without actually running any migrations"
    echo
    read -p "Are you sure? (yes/no): " -r
    echo
    
    if [[ $REPLY == "yes" ]]; then
        if python -m alembic stamp "$revision"; then
            print_info "✅ Database stamped successfully at revision: $revision"
        else
            print_error "Failed to stamp database"
            exit 1
        fi
    else
        print_info "Operation cancelled"
        exit 0
    fi
}

function data_migrate() {
    local range="${1:-}"
    
    print_info "Running data migrations..."
    
    if [ -f "scripts/data_migrate.py" ]; then
        if [ -n "$range" ]; then
            print_info "Running data migrations for range: $range"
            if python scripts/data_migrate.py --range "$range"; then
                print_info "✅ Data migrations completed successfully"
            else
                print_error "Data migration failed"
                exit 1
            fi
        else
            print_info "Running all pending data migrations"
            if python scripts/data_migrate.py; then
                print_info "✅ Data migrations completed successfully"
            else
                print_error "Data migration failed"
                exit 1
            fi
        fi
    else
        print_warn "Data migration script not found at scripts/data_migrate.py"
        print_info "No data migrations to run"
    fi
}

function repair_db() {
    print_warn "⚠️  Database migration history repair"
    print_info "This command will attempt to fix corrupted migration history"
    echo
    print_info "Current database state:"
    python -m alembic current 2>&1 || true
    echo
    
    print_info "Available repair options:"
    echo "  1. Stamp database at head (mark as up-to-date)"
    echo "  2. Stamp database at specific revision"
    echo "  3. Show migration history for manual inspection"
    echo "  4. Cancel"
    echo
    read -p "Select option (1-4): " -r
    echo
    
    case $REPLY in
        1)
            print_info "Stamping database at head..."
            if python -m alembic stamp head; then
                print_info "✅ Database stamped at head"
                python -m alembic current
            else
                print_error "Failed to stamp database"
                exit 1
            fi
            ;;
        2)
            read -p "Enter revision ID: " -r revision
            if [ -n "$revision" ]; then
                if python -m alembic stamp "$revision"; then
                    print_info "✅ Database stamped at revision: $revision"
                    python -m alembic current
                else
                    print_error "Failed to stamp database"
                    exit 1
                fi
            else
                print_error "Revision ID is required"
                exit 1
            fi
            ;;
        3)
            print_info "Migration history:"
            python -m alembic history --verbose
            ;;
        4)
            print_info "Operation cancelled"
            exit 0
            ;;
        *)
            print_error "Invalid option"
            exit 1
            ;;
    esac
}

# Initialize environment
load_environment
activate_venv

# Validate command
if [ $# -eq 0 ]; then
    print_error "No command specified"
    echo
    show_help
    exit 1
fi

# Main command dispatcher
case "${1}" in
    create)
        create_migration "$2"
        ;;
    upgrade)
        upgrade_db "$2"
        ;;
    downgrade)
        downgrade_db "$2"
        ;;
    current)
        show_current
        ;;
    history)
        show_history
        ;;
    reset)
        reset_db
        ;;
    stamp)
        stamp_db "$2"
        ;;
    data-migrate)
        data_migrate "$2"
        ;;
    repair)
        repair_db
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: ${1}"
        echo
        show_help
        exit 1
        ;;
esac

exit 0
