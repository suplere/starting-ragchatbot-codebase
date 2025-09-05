#!/bin/bash

# Code Formatting Script
# This script formats code and sorts imports

set -e

echo "🎨 Formatting code..."

# Colors for output
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Format with Black
echo "📝 Running Black formatter..."
black backend/ main.py
print_status "Code formatted with Black"

# Sort imports with isort
echo "📋 Sorting imports with isort..."
isort backend/ main.py --profile black
print_status "Imports sorted with isort"

echo -e "\n${GREEN}🎉 Code formatting completed!${NC}"