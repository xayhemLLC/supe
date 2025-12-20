#!/bin/bash
# Supe Uninstall Script

set -e

echo "🗑️  Uninstalling Supe..."
echo ""

# Try pip first
if command -v pip3 &> /dev/null; then
    pip3 uninstall supe -y 2>/dev/null || true
elif command -v pip &> /dev/null; then
    pip uninstall supe -y 2>/dev/null || true
fi

# Also try uv
if command -v uv &> /dev/null; then
    uv pip uninstall supe 2>/dev/null || true
fi

echo ""
echo "✅ Supe uninstalled"
echo ""
echo "The following may remain:"
echo "  - ~/.tascer/ directory (local data)"
echo "  - tasc.sqlite files (task databases)"
echo ""
echo "To remove all data: rm -rf ~/.tascer tasc.sqlite"
