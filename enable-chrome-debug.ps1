# PowerShell script to enable Chrome debugging
Write-Host "Closing any existing Chrome instances..." -ForegroundColor Yellow
Stop-Process -Name chrome -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

Write-Host "Starting Chrome with debugging enabled..." -ForegroundColor Green
$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$arguments = @(
    "--remote-debugging-port=9222",
    "--user-data-dir=$env:TEMP\chrome-debug",
    "--new-window",
    "http://localhost:6006/projects/UHJvamVjdDox/traces"
)

Start-Process -FilePath $chromePath -ArgumentList $arguments

Write-Host "Chrome should now be running with debugging on port 9222" -ForegroundColor Green
Write-Host "Phoenix traces page should open automatically" -ForegroundColor Cyan

# Wait a moment for Chrome to start
Start-Sleep -Seconds 3

# Test if debugging port is accessible
try {
    $response = Invoke-WebRequest -Uri "http://localhost:9222/json/version" -TimeoutSec 5
    Write-Host "`nChrome debugging is ACTIVE!" -ForegroundColor Green
    Write-Host "You can now run the monitor-agent" -ForegroundColor Cyan
} catch {
    Write-Host "`nWarning: Could not verify Chrome debugging port" -ForegroundColor Red
    Write-Host "Make sure Chrome opened successfully" -ForegroundColor Yellow
}