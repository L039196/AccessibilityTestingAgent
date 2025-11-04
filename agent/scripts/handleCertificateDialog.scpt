-- AppleScript to automatically handle certificate dialog
-- Presses Return key twice with appropriate delays for certificate acceptance

tell application "System Events"
    -- First Return press to accept the certificate
    keystroke return
    
    -- Wait 3 seconds for dialog processing
    delay 3
    
    -- Second Return press to confirm (if needed)
    keystroke return
    
    -- Additional short delay to ensure completion
    delay 1
end tell
