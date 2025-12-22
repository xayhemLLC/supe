#!/bin/bash
# Record Terminal Demo with asciinema

cd "$(dirname "$0")"

clear
cat << "EOF"
╔════════════════════════════════════════════════════════╗
║  CDP Browser - Terminal Recording                     ║
╚════════════════════════════════════════════════════════╝

This records your terminal session with beautiful output!

Choose a recording method:
  [1] asciinema (recommended - shareable terminal recording)
  [2] ttyrec (alternative terminal recorder)
  [3] screen recording → GIF (using ffmpeg)
  [4] Just run the demo (I'll record manually)

EOF

read -p "Choice [1-4]: " choice

case $choice in
  1)
    # asciinema method
    echo ""
    echo "Using asciinema..."
    echo ""

    # Check if installed
    if ! command -v asciinema &> /dev/null; then
      echo "Installing asciinema..."
      pip install asciinema
    fi

    OUTPUT="cdp_terminal_demo_$(date +%Y%m%d_%H%M%S).cast"

    echo "Recording to: $OUTPUT"
    echo ""
    echo "Press Ctrl+D when done to stop recording"
    echo ""
    sleep 2

    # Record with asciinema
    asciinema rec "$OUTPUT" -c "source .venv/bin/activate && python examples/cdp_browser_terminal_demo.py"

    echo ""
    echo "✓ Recording saved to: $OUTPUT"
    echo ""
    echo "To replay:"
    echo "  asciinema play $OUTPUT"
    echo ""
    echo "To upload and share:"
    echo "  asciinema upload $OUTPUT"
    echo ""
    echo "To convert to GIF:"
    echo "  # First install agg:"
    echo "  cargo install --git https://github.com/asciinema/agg"
    echo "  # Then convert:"
    echo "  agg $OUTPUT cdp_demo.gif"
    echo ""
    ;;

  2)
    # ttyrec method
    echo ""
    echo "Using ttyrec..."

    if ! command -v ttyrec &> /dev/null; then
      echo "Installing ttyrec..."
      brew install ttyrec
    fi

    OUTPUT="cdp_terminal_demo_$(date +%Y%m%d_%H%M%S).tty"

    echo "Recording to: $OUTPUT"
    echo "Press Ctrl+D to stop"
    sleep 2

    ttyrec "$OUTPUT"
    source .venv/bin/activate
    python examples/cdp_browser_terminal_demo.py
    exit

    echo ""
    echo "To replay:"
    echo "  ttyplay $OUTPUT"
    ;;

  3)
    # Screen recording to GIF
    echo ""
    echo "Screen Recording → GIF"
    echo ""
    echo "This will:"
    echo "  1. Use macOS screen recording"
    echo "  2. Convert to GIF with ffmpeg"
    echo ""
    read -p "Press ENTER to continue..."

    echo ""
    echo "Press Cmd+Shift+5 NOW and start recording"
    read -p "Press ENTER when recording started..."

    sleep 2
    source .venv/bin/activate
    python examples/cdp_browser_terminal_demo.py

    echo ""
    echo "Stop your recording now!"
    echo ""
    echo "To convert to GIF:"
    echo "  cd ~/Desktop"
    echo "  ffmpeg -i 'Screen Recording*.mov' -vf 'fps=10,scale=800:-1:flags=lanczos,palettegen' palette.png"
    echo "  ffmpeg -i 'Screen Recording*.mov' -i palette.png -filter_complex 'fps=10,scale=800:-1:flags=lanczos[x];[x][1:v]paletteuse' cdp_demo.gif"
    echo ""
    ;;

  4)
    # Just run the demo
    echo ""
    echo "Running demo..."
    echo "(Record manually with your preferred tool)"
    echo ""
    sleep 2

    source .venv/bin/activate
    python examples/cdp_browser_terminal_demo.py
    ;;

  *)
    echo "Invalid choice"
    exit 1
    ;;
esac

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  ✓ Done!                                              ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
