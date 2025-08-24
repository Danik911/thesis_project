# Kill Chrome and start with debugging - FIXED VERSION
Write-Host "Stopping all Chrome processes..." -ForegroundColor Yellow
Get-Process chrome -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3

Write-Host "Starting Chrome with debugging..." -ForegroundColor Green

# Use full path and create temp profile
$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$tempProfile = "$env:TEMP\chrome-debug-profile"

# Create temp profile directory
New-Item -ItemType Directory -Force -Path $tempProfile | Out-Null

# Start Chrome with explicit parameters
$args = @(
    "--remote-debugging-port=9222",
    "--user-data-dir=$tempProfile",
    "--no-first-run",
    "--no-default-browser-check",
    "http://localhost:6006"
)

Start-Process -FilePath $chromePath -ArgumentList $args

Write-Host "Waiting for Chrome to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Test connection
Write-Host "Testing debug connection..." -ForegroundColor Cyan
try {
    $test = Invoke-RestMethod -Uri "http://127.0.0.1:9222/json/version" -TimeoutSec 5
    Write-Host "✅ SUCCESS! Chrome debugging is active!" -ForegroundColor Green
    Write-Host "Browser: $($test.Browser)" -ForegroundColor Cyan
    Write-Host "Now login to Phoenix and navigate to traces" -ForegroundColor Yellow
} catch {
    Write-Host "❌ FAILED! Debugging not accessible" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    
    # Check if port is in use
    $portCheck = netstat -an | Select-String ":9222"
    if ($portCheck) {
        Write-Host "Port 9222 is in use:" -ForegroundColor Yellow
        $portCheck
    }
}