#!/bin/bash
# Build standalone executables for Supe
# Usage: ./scripts/build.sh [platform]
#   platform: windows, macos, linux, all (default: current platform)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Activate venv if exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}       🔹 Supe Build Script${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check for pyinstaller
if ! command -v pyinstaller &> /dev/null; then
    echo -e "${RED}PyInstaller not found. Installing...${NC}"
    python3 -m pip install pyinstaller
fi

# Detect platform
detect_platform() {
    case "$(uname -s)" in
        Darwin*) echo "macos" ;;
        Linux*)  echo "linux" ;;
        MINGW*|MSYS*|CYGWIN*) echo "windows" ;;
        *) echo "unknown" ;;
    esac
}

PLATFORM="${1:-$(detect_platform)}"
BUILD_DIR="$PROJECT_DIR/dist"
mkdir -p "$BUILD_DIR"

echo -e "Building for: ${GREEN}$PLATFORM${NC}"
echo ""

# Build function
build_executable() {
    local platform=$1
    
    echo -e "${CYAN}▶ Building supe executable...${NC}"
    
    # Clean previous builds
    rm -rf build/ dist/supe dist/supe.exe dist/Supe.app 2>/dev/null || true
    
    # Build with PyInstaller
    pyinstaller supe.spec --clean --noconfirm
    
    # Platform-specific post-processing
    case $platform in
        macos)
            if [ -d "dist/Supe.app" ]; then
                echo -e "${GREEN}✅ Built: dist/Supe.app${NC}"
            fi
            if [ -f "dist/supe" ]; then
                chmod +x dist/supe
                echo -e "${GREEN}✅ Built: dist/supe${NC}"
            fi
            ;;
        windows)
            if [ -f "dist/supe.exe" ]; then
                echo -e "${GREEN}✅ Built: dist/supe.exe${NC}"
            fi
            ;;
        linux)
            if [ -f "dist/supe" ]; then
                chmod +x dist/supe
                echo -e "${GREEN}✅ Built: dist/supe${NC}"
            fi
            ;;
    esac
}

# Create installer packages
create_installer() {
    local platform=$1
    
    echo ""
    echo -e "${CYAN}▶ Creating installer package...${NC}"
    
    case $platform in
        macos)
            # Create DMG
            if command -v create-dmg &> /dev/null && [ -d "dist/Supe.app" ]; then
                create-dmg \
                    --volname "Supe Installer" \
                    --window-pos 200 120 \
                    --window-size 600 400 \
                    --icon-size 100 \
                    --app-drop-link 450 185 \
                    "dist/Supe-Installer.dmg" \
                    "dist/Supe.app"
                echo -e "${GREEN}✅ Created: dist/Supe-Installer.dmg${NC}"
            else
                # Create zip
                cd dist && zip -r supe-macos.zip supe && cd ..
                echo -e "${GREEN}✅ Created: dist/supe-macos.zip${NC}"
            fi
            ;;
        windows)
            # Create zip
            if [ -f "dist/supe.exe" ]; then
                cd dist && zip supe-windows.zip supe.exe && cd ..
                echo -e "${GREEN}✅ Created: dist/supe-windows.zip${NC}"
            fi
            ;;
        linux)
            # Create tar.gz
            if [ -f "dist/supe" ]; then
                cd dist && tar -czvf supe-linux.tar.gz supe && cd ..
                echo -e "${GREEN}✅ Created: dist/supe-linux.tar.gz${NC}"
            fi
            ;;
    esac
}

# Main
case $PLATFORM in
    all)
        echo "Cross-platform builds require running on each platform."
        echo "Use GitHub Actions for automated cross-platform builds."
        exit 1
        ;;
    macos|linux|windows)
        build_executable $PLATFORM
        create_installer $PLATFORM
        ;;
    *)
        echo -e "${RED}Unknown platform: $PLATFORM${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}       Build Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Output in: $BUILD_DIR"
ls -la "$BUILD_DIR"
