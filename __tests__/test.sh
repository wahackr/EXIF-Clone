#!/bin/bash
# Quick test runner script for EXIF-Clone

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}EXIF-Clone Test Suite${NC}"
echo "======================="
echo ""

# Function to run tests
run_tests() {
    local test_type=$1
    local description=$2
    
    echo -e "${GREEN}Running ${description}...${NC}"
    uv run pytest __tests__/${test_type} -v
    echo ""
}

# Parse arguments
case "${1:-all}" in
    unit)
        run_tests "unit/" "Unit Tests"
        ;;
    integration)
        run_tests "integration/" "Integration Tests"
        ;;
    coverage)
        echo -e "${GREEN}Running All Tests with Coverage...${NC}"
        uv run pytest __tests__/ -v --cov=src --cov-report=term-missing --cov-report=html
        echo ""
        echo "HTML coverage report generated in htmlcov/index.html"
        ;;
    all)
        run_tests "unit/" "Unit Tests"
        run_tests "integration/" "Integration Tests"
        ;;
    *)
        echo "Usage: $0 {all|unit|integration|coverage}"
        echo ""
        echo "  all          - Run all tests (default)"
        echo "  unit         - Run unit tests only"
        echo "  integration  - Run integration tests only"
        echo "  coverage     - Run all tests with coverage report"
        exit 1
        ;;
esac

echo -e "${GREEN}✓ All tests passed!${NC}"
