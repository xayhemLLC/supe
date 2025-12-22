#!/bin/bash
# Simple CDP Browser Demo Recording
# Just runs demo and tells you when to start/stop recording

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
OUTPUT_FILE="$HOME/Desktop/cdp_browser_demo.mp4"

echo "=================================================="
echo "CDP Browser Demo - Manual Recording"
echo "=================================================="
echo ""
echo "Instructions:"
echo "  1. Press Cmd+Shift+5 (macOS Screenshot)"
echo "  2. Click 'Record Selected Portion' or 'Record Entire Screen'"
echo "  3. Click 'Record' button"
echo "  4. Press ENTER here to start demo"
echo ""
read -p "Press ENTER when recording has started..."
echo ""
echo "→ Starting demo in 3 seconds..."
sleep 3

# Run the demo
cd "$PROJECT_ROOT"
source .venv/bin/activate
python "$SCRIPT_DIR/cdp_browser_demo_30s.py"

echo ""
echo "=================================================="
echo "✓ Demo Complete!"
echo "=================================================="
echo ""
echo "Now stop your recording:"
echo "  - Click the stop button in menu bar"
echo "  - Video saves to: ~/Desktop/"
echo ""
