@echo off
echo Closing any existing Chrome instances...
taskkill /F /IM chrome.exe 2>nul
timeout /t 2 >nul

echo Starting Chrome with debugging enabled...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%TEMP%\chrome-debug" --new-window "http://localhost:6006/projects/UHJvamVjdDox/traces"

echo Chrome should now be running with debugging on port 9222
echo Navigate to http://localhost:6006/projects/UHJvamVjdDox/traces if not already there
pause