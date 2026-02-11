#!/bin/bash
# Money Scout Daemon Setup
# Run this to install the daemon to run 24/7

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DAEMON_SCRIPT="$SCRIPT_DIR/money_scout_daemon.py"
VENV_PYTHON="$SCRIPT_DIR/../.venv/bin/python"
LOG_DIR="$HOME/.supe/logs"
PLIST_PATH="$HOME/Library/LaunchAgents/com.supe.moneyscout.plist"

# Create log directory
mkdir -p "$LOG_DIR"

echo "========================================"
echo "Money Scout Daemon Setup"
echo "========================================"
echo ""

# Check Python
if [ ! -f "$VENV_PYTHON" ]; then
    echo "Error: Python venv not found at $VENV_PYTHON"
    echo "Run: cd $SCRIPT_DIR/.. && uv venv && source .venv/bin/activate && uv pip install -e ."
    exit 1
fi

echo "Choose how to run the daemon:"
echo ""
echo "1. Screen (interactive, survives logout)"
echo "2. tmux (interactive, survives logout)"
echo "3. launchd (macOS service, starts on boot)"
echo "4. nohup (simple background, stops on logout)"
echo ""
read -p "Enter choice [1-4]: " choice

case $choice in
    1)
        echo ""
        echo "Starting with screen..."
        echo "To detach: Ctrl+A, then D"
        echo "To reattach: screen -r scout"
        echo ""
        screen -S scout "$VENV_PYTHON" "$DAEMON_SCRIPT" --profile "Python developer"
        ;;
    2)
        echo ""
        echo "Starting with tmux..."
        echo "To detach: Ctrl+B, then D"
        echo "To reattach: tmux attach -t scout"
        echo ""
        tmux new-session -d -s scout "$VENV_PYTHON $DAEMON_SCRIPT --profile 'Python developer'"
        echo "Started in tmux session 'scout'"
        echo "Attach with: tmux attach -t scout"
        ;;
    3)
        echo ""
        echo "Installing launchd service..."

        # Create plist
        cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.supe.moneyscout</string>
    <key>ProgramArguments</key>
    <array>
        <string>$VENV_PYTHON</string>
        <string>$DAEMON_SCRIPT</string>
        <string>--profile</string>
        <string>Python developer</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/scout.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/scout.err</string>
    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR/..</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
EOF

        # Load the service
        launchctl unload "$PLIST_PATH" 2>/dev/null || true
        launchctl load "$PLIST_PATH"

        echo "Service installed and started!"
        echo ""
        echo "Commands:"
        echo "  View logs:    tail -f $LOG_DIR/scout.log"
        echo "  Stop:         launchctl unload $PLIST_PATH"
        echo "  Start:        launchctl load $PLIST_PATH"
        echo "  Uninstall:    rm $PLIST_PATH && launchctl unload $PLIST_PATH"
        ;;
    4)
        echo ""
        echo "Starting with nohup..."
        nohup "$VENV_PYTHON" "$DAEMON_SCRIPT" --profile "Python developer" > "$LOG_DIR/scout.log" 2>&1 &
        echo "Started! PID: $!"
        echo "View logs: tail -f $LOG_DIR/scout.log"
        echo "Stop: kill $!"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "========================================"
echo "Setup complete!"
echo ""
echo "Check findings anytime:"
echo "  python $DAEMON_SCRIPT --report"
echo "  cat ~/.supe/scout_findings.json"
echo "  supe memory search 'opportunity'"
echo "========================================"
