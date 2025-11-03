-- AppleScript to press the return key twice with a 3-second interval
-- This handles the native certificate selection dialog on macOS

tell application "System Events"
	keystroke return
	delay 3
	keystroke return
end tell
