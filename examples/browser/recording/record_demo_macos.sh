#!/bin/bash
# macOS Screen Recording Helper
# Uses built-in screencapture instead of ffmpeg

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
OUTPUT_FILE="$HOME/Desktop/cdp_browser_demo_$(date +%Y%m%d_%H%M%S).mov"

echo "=================================================="
echo "CDP Browser Demo - macOS Screen Recording"
echo "=================================================="
echo ""
echo "Instructions:"
echo ""
echo "1. This will use macOS built-in screen recording"
echo "2. Press Cmd+Shift+5 NOW"
echo "3. Select 'Record Entire Screen' or 'Record Selected Portion'"
echo "4. Click the 'Record' button"
echo "5. Then come back here and press ENTER"
echo ""
read -p "Press ENTER when recording has started..."

echo ""
echo "Starting demo in 3 seconds..."
sleep 1
echo "3..."
sleep 1
echo "2..."
sleep 1
echo "1..."
sleep 1

# Run the demo
cd "$PROJECT_ROOT"
source .venv/bin/activate
python "$SCRIPT_DIR/cdp_browser_demo_30s.py"

echo ""
echo "=================================================="
echo "✓ Demo Complete!"
echo "=================================================="
echo ""
echo "Stop your recording now:"
echo "  1. Click the stop button in menu bar (■)"
echo "  2. Video will save to ~/Desktop/"
echo ""
echo "To convert MOV to MP4:"
echo "  ffmpeg -i input.mov -c:v libx264 -preset fast -crf 23 -c:a aac output.mp4"
echo ""
