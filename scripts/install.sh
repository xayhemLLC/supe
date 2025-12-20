#!/bin/bash
# Supe Install Script
# One-liner: curl -sSL https://raw.githubusercontent.com/your-repo/supe/main/scripts/install.sh | bash

set -e

echo "🚀 Installing Supe..."
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check Python version
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
        
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 10 ]; then
            echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"
            return 0
        fi
    fi
    
    echo -e "${RED}✗${NC} Python 3.10+ required"
    exit 1
}

# Check for uv or pip
check_installer() {
    if command -v uv &> /dev/null; then
        echo -e "${GREEN}✓${NC} uv found (recommended)"
        INSTALLER="uv"
    elif command -v pip3 &> /dev/null; then
        echo -e "${GREEN}✓${NC} pip3 found"
        INSTALLER="pip3"
    elif command -v pip &> /dev/null; then
        echo -e "${GREEN}✓${NC} pip found"
        INSTALLER="pip"
    else
        echo -e "${RED}✗${NC} No package installer found. Install uv or pip first."
        exit 1
    fi
}

# Install supe
install_supe() {
    echo ""
    echo "📦 Installing supe..."
    echo ""
    
    if [ "$INSTALLER" = "uv" ]; then
        # Check if we're in the repo
        if [ -f "pyproject.toml" ]; then
            uv pip install -e .
        else
            echo "Please run this script from the supe directory, or clone the repo first:"
            echo "  git clone https://github.com/your-repo/supe.git"
            echo "  cd supe"
            echo "  ./scripts/install.sh"
            exit 1
        fi
    else
        if [ -f "pyproject.toml" ]; then
            $INSTALLER install -e .
        else
            echo "Please run this script from the supe directory."
            exit 1
        fi
    fi
}

# Verify installation
verify_install() {
    echo ""
    if command -v supe &> /dev/null; then
        echo -e "${GREEN}✅ Supe installed successfully!${NC}"
        echo ""
        echo "Available commands:"
        echo "  supe      - Unified CLI"
        echo "  tasc      - Task management"
        echo "  t         - Shorthand for tasc"
        echo "  tascer    - Safety & validation"
        echo ""
        echo "Get started:"
        echo "  supe status"
        echo "  supe --help"
    else
        echo -e "${RED}Installation may have succeeded but 'supe' not in PATH${NC}"
        echo "Try running: source ~/.bashrc (or restart your terminal)"
    fi
}

# Main
main() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "       🔹 Supe Installation Script"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    check_python
    check_installer
    install_supe
    verify_install
}

main "$@"
