#!/bin/bash
# Script to run frontend tests with coverage

set -e

echo "🧪 Running RuoYi-FastAPI Frontend Tests"
echo "======================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Change to frontend directory
cd "$(dirname "$0")/.."

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  Dependencies not installed. Installing...${NC}"
    yarn install
fi

# Create coverage directory
mkdir -p tests/coverage

# Run tests based on arguments
if [ "$1" == "quick" ]; then
    # Quick test run without coverage
    echo -e "${GREEN}✓${NC} Running quick tests..."
    yarn test:run --reporter=verbose
elif [ "$1" == "unit" ]; then
    # Run only unit tests
    echo -e "${GREEN}✓${NC} Running unit tests..."
    yarn test:run tests/unit --coverage
elif [ "$1" == "integration" ]; then
    # Run only integration tests
    echo -e "${GREEN}✓${NC} Running integration tests..."
    yarn test:run tests/integration
elif [ "$1" == "watch" ]; then
    # Watch mode for development
    echo -e "${GREEN}✓${NC} Running tests in watch mode..."
    yarn test
else
    # Full test run with coverage
    echo -e "${GREEN}✓${NC} Running all tests with coverage..."
    yarn test:run --coverage
fi

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    
    # Show coverage report location
    if [ -d "tests/coverage" ]; then
        echo "📊 Coverage report: tests/coverage/index.html"
        
        # Extract coverage percentage if available
        if [ -f "tests/coverage/coverage-summary.json" ]; then
            COVERAGE=$(node -e "const c=require('./tests/coverage/coverage-summary.json'); console.log(c.total.lines.pct)")
            echo -e "📈 Total coverage: ${GREEN}${COVERAGE}%${NC}"
        fi
    fi
else
    echo ""
    echo -e "${RED}❌ Tests failed!${NC}"
    exit 1
fi

echo ""
echo "Done! 🎉"
