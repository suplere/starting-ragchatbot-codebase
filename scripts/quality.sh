#!/bin/bash

# Code Quality Tools Script
# This script runs various code quality checks

set -e

echo "🔧 Running code quality checks..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Format code with Black
echo "📝 Formatting code with Black..."
if black backend/ main.py --check --quiet; then
    print_status "Code formatting is consistent"
else
    print_warning "Applying Black formatting..."
    black backend/ main.py
    print_status "Code formatted with Black"
fi

# Sort imports with isort
echo "📋 Sorting imports with isort..."
if isort backend/ main.py --profile black --check-only --quiet; then
    print_status "Import sorting is consistent"
else
    print_warning "Sorting imports..."
    isort backend/ main.py --profile black
    print_status "Imports sorted with isort"
fi

# Run flake8 for linting
echo "🔍 Running flake8 linting..."
if flake8 backend/ main.py --max-line-length=88 --extend-ignore=E203,W503; then
    print_status "Flake8 linting passed"
else
    print_error "Flake8 linting failed"
    exit 1
fi

# Run tests if available
echo "🧪 Running tests..."
if [ -d "backend/tests" ]; then
    if python -m pytest backend/tests/ -v; then
        print_status "All tests passed"
    else
        print_error "Some tests failed"
        exit 1
    fi
else
    print_warning "No tests directory found, skipping tests"
fi

echo -e "\n${GREEN}🎉 All quality checks completed successfully!${NC}"