#!/bin/bash
# Script to run backend tests with coverage

set -e

echo "🧪 Running RuoYi-FastAPI Backend Tests"
echo "======================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Change to backend directory
cd "$(dirname "$0")/.."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${GREEN}✓${NC} Activating virtual environment..."
source venv/bin/activate

# Install test dependencies
echo -e "${GREEN}✓${NC} Installing test dependencies..."
pip install -q -r requirements-dev.txt

# Create coverage directory
mkdir -p tests/coverage

# Run tests
echo ""
echo -e "${GREEN}✓${NC} Running tests..."
echo ""

# Run with different options based on arguments
if [ "$1" == "quick" ]; then
    # Quick test run without coverage
    pytest tests/ -v --tb=short
elif [ "$1" == "unit" ]; then
    # Run only unit tests
    pytest tests/unit/ -v --cov=module_admin --cov=utils --cov-report=term-missing
elif [ "$1" == "integration" ]; then
    # Run only integration tests
    pytest tests/integration/ -v
elif [ "$1" == "watch" ]; then
    # Watch mode for development
    pytest-watch tests/ -- -v --tb=short
else
    # Full test run with coverage
    pytest tests/ \
        -v \
        --cov=module_admin \
        --cov=utils \
        --cov=config \
        --cov-report=html:tests/coverage/html \
        --cov-report=term-missing \
        --cov-report=json:tests/coverage/coverage.json \
        --cov-fail-under=70 \
        -n auto
fi

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "📊 Coverage report generated at: tests/coverage/html/index.html"
    echo ""
    
    # Extract coverage percentage
    if [ -f "tests/coverage/coverage.json" ]; then
        COVERAGE=$(python3 -c "import json; print(json.load(open('tests/coverage/coverage.json'))['totals']['percent_covered'])")
        echo -e "📈 Total coverage: ${GREEN}${COVERAGE}%${NC}"
    fi
else
    echo ""
    echo -e "${RED}❌ Tests failed!${NC}"
    exit 1
fi

# Deactivate virtual environment
deactivate

echo ""
echo "Done! 🎉"
