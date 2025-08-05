# PowerShell script to start Chrome with debugging
Write-Host "Starting Chrome with debugging on port 9222..." -ForegroundColor Green

# Kill any existing Chrome processes
Stop-Process -Name chrome -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Start Chrome with debugging
Start-Process -FilePath "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList "--remote-debugging-port=9222", "--new-window", "http://localhost:6006/projects/UHJvamVjdDox/traces"

Write-Host "Chrome started with debugging enabled!" -ForegroundColor Green
Write-Host "Phoenix traces page should open automatically" -ForegroundColor Cyan