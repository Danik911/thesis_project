# Test if Chrome debugging is active
try {
    $response = Invoke-WebRequest -Uri "http://localhost:9222/json/version" -TimeoutSec 3
    Write-Host "✅ Chrome debugging is ACTIVE!" -ForegroundColor Green
    $version = $response.Content | ConvertFrom-Json
    Write-Host "Browser: $($version.Browser)" -ForegroundColor Cyan
    Write-Host "You can run monitor-agent now" -ForegroundColor Yellow
} catch {
    Write-Host "❌ Chrome debugging is NOT active" -ForegroundColor Red
    Write-Host "Please run: .\start-chrome-debug.ps1" -ForegroundColor Yellow
}