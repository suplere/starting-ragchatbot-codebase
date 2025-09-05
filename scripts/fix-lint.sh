#!/bin/bash

# Auto-fix common linting issues script

set -e

echo "🔧 Auto-fixing linting issues..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Remove unused imports using autoflake
echo "🧹 Removing unused imports..."
if command -v autoflake &> /dev/null; then
    autoflake --remove-all-unused-imports --recursive --in-place backend/ main.py
    print_status "Unused imports removed"
else
    print_warning "autoflake not installed, skipping unused import removal"
fi

# Format with Black (handles some line length issues)
echo "📝 Formatting with Black..."
black backend/ main.py
print_status "Code formatted"

# Sort imports
echo "📋 Sorting imports..."
isort backend/ main.py --profile black
print_status "Imports sorted"

echo -e "\n${GREEN}🎉 Auto-fix completed! Run ./scripts/quality.sh to check remaining issues.${NC}"