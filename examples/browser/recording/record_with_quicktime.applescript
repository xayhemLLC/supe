-- Automate QuickTime Screen Recording for CDP Browser Demo
-- This avoids permission issues by using QuickTime Player

on run
	set outputPath to (path to desktop as text) & "cdp_browser_demo.mov"

	-- Start QuickTime and begin recording
	tell application "QuickTime Player"
		activate
		delay 1

		-- Start new screen recording
		tell application "System Events"
			tell process "QuickTime Player"
				click menu item "New Screen Recording" of menu "File" of menu bar 1
				delay 2

				-- Click the record button (center of screen recording window)
				click button 1 of window 1
				delay 1
			end tell
		end tell
	end tell

	-- Give time to start recording
	delay 2

	-- Run the demo
	do shell script "cd /Users/chriscabral/Desktop/super/supe && source .venv/bin/activate && python examples/cdp_browser_demo_30s.py"

	-- Wait a moment after demo
	delay 2

	-- Stop recording
	tell application "System Events"
		tell process "QuickTime Player"
			-- Press Cmd+Control+Esc to stop recording
			keystroke "c" using {command down, control down}
		end tell
	end tell

	delay 1

	-- Save the recording
	tell application "QuickTime Player"
		tell front document
			save in file outputPath
			close
		end tell
	end tell

	display dialog "Recording saved to Desktop!" buttons {"OK"} default button 1
end run
