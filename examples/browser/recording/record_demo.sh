#!/bin/bash
# Automatic CDP Browser Demo Recording Script
# Records screen, runs demo, outputs MP4

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="$HOME/Desktop"
OUTPUT_FILE="$OUTPUT_DIR/cdp_browser_demo_$(date +%Y%m%d_%H%M%S).mp4"
DEMO_SCRIPT="$SCRIPT_DIR/cdp_browser_demo_30s.py"

echo "=================================================="
echo "CDP Browser Demo - Automatic Recording"
echo "=================================================="
echo ""
echo "Output will be saved to:"
echo "  $OUTPUT_FILE"
echo ""
echo "Starting in 3 seconds..."
echo "  (Position your windows now!)"
echo ""
sleep 3

# Get screen info for macOS
SCREEN_SIZE=$(system_profiler SPDisplaysDataType | grep Resolution | head -1 | awk '{print $2"x"$4}')
echo "Recording screen: $SCREEN_SIZE"
echo ""

# Start screen recording with ffmpeg (macOS AVFoundation)
echo "→ Starting screen recording..."
ffmpeg -f avfoundation \
    -capture_cursor 1 \
    -capture_mouse_clicks 1 \
    -video_size "$SCREEN_SIZE" \
    -framerate 30 \
    -i "1:none" \
    -c:v libx264 \
    -preset ultrafast \
    -pix_fmt yuv420p \
    -y \
    "$OUTPUT_FILE" \
    > /tmp/ffmpeg_recording.log 2>&1 &

FFMPEG_PID=$!
echo "  Recording started (PID: $FFMPEG_PID)"
echo ""

# Wait for ffmpeg to initialize
sleep 2

# Run the demo
echo "→ Running CDP Browser demo..."
echo ""
cd "$PROJECT_ROOT"
source .venv/bin/activate
python "$DEMO_SCRIPT"

# Wait a moment before stopping
sleep 2

# Stop recording
echo ""
echo "→ Stopping recording..."
kill -INT $FFMPEG_PID 2>/dev/null || true
wait $FFMPEG_PID 2>/dev/null || true

# Wait for ffmpeg to finish encoding
sleep 2

# Check if file exists and show info
if [ -f "$OUTPUT_FILE" ]; then
    FILE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
    echo ""
    echo "=================================================="
    echo "✓ Recording Complete!"
    echo "=================================================="
    echo ""
    echo "Video saved to:"
    echo "  $OUTPUT_FILE"
    echo ""
    echo "File size: $FILE_SIZE"
    echo ""
    echo "To play:"
    echo "  open \"$OUTPUT_FILE\""
    echo ""
    echo "To share:"
    echo "  - Upload to YouTube/Vimeo"
    echo "  - Share via Dropbox/Google Drive"
    echo "  - Convert to GIF: ffmpeg -i \"$OUTPUT_FILE\" -vf \"fps=10,scale=800:-1\" output.gif"
    echo ""
    echo "=================================================="

    # Optionally open the video
    read -p "Open video now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open "$OUTPUT_FILE"
    fi
else
    echo ""
    echo "❌ Error: Video file not created"
    echo "Check logs: /tmp/ffmpeg_recording.log"
fi
