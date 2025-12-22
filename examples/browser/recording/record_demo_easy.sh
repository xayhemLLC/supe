#!/bin/bash
# Easy CDP Browser Demo Recording
# Uses macOS built-in screen recorder

cd "$(dirname "$0")"

clear
echo "╔════════════════════════════════════════════════════════╗"
echo "║  CDP Browser Demo - Easy Recording                    ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "This will help you record the demo using macOS built-in"
echo "screen recording (no permission issues!)."
echo ""
echo "──────────────────────────────────────────────────────────"
echo "STEP 1: Start Screen Recording"
echo "──────────────────────────────────────────────────────────"
echo ""
echo "  1. Press: Cmd + Shift + 5"
echo "  2. Click: 'Record Entire Screen'"
echo "  3. Click: Red 'Record' button"
echo "  4. Come back here"
echo ""
read -p "Press ENTER when recording has started..."

clear
echo "╔════════════════════════════════════════════════════════╗"
echo "║  Starting Demo in 3 seconds...                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
sleep 1
echo "  3..."
sleep 1
echo "  2..."
sleep 1
echo "  1..."
sleep 1

echo ""
echo "▶ Running demo..."
echo ""

# Run the demo
source .venv/bin/activate
python examples/cdp_browser_demo_30s.py

echo ""
echo "──────────────────────────────────────────────────────────"
echo "STEP 2: Stop Recording"
echo "──────────────────────────────────────────────────────────"
echo ""
echo "  1. Click the Stop button (■) in your menu bar"
echo "  2. Video will save to: ~/Desktop/"
echo ""
echo "──────────────────────────────────────────────────────────"
echo "STEP 3: Convert to MP4 (Optional)"
echo "──────────────────────────────────────────────────────────"
echo ""
echo "After you stop recording, run:"
echo ""
echo "  cd ~/Desktop"
echo "  ffmpeg -i 'Screen Recording*.mov' -c:v libx264 \\"
echo "         -preset fast -crf 23 cdp_browser_demo.mp4"
echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  ✓ Demo Complete!                                     ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
