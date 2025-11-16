# Test Single URS Document - PowerShell Script
# Tests pharmaceutical test generation with URS-025 (Category 5 - Custom Application)

Write-Host "=== Pharmaceutical Test Generation - Single URS Test ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Verify health
Write-Host "[1/5] Checking API health..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8080/health"
    Write-Host "  ✓ API Status: $($health.status)" -ForegroundColor Green
    Write-Host "  ✓ Service: $($health.service)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Health check failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 2: Check Clerk token
Write-Host "[2/5] Verifying Clerk authentication..." -ForegroundColor Yellow
if (-not $env:CLERK_TOKEN) {
    Write-Host "  ! CLERK_TOKEN not set. Running Set-ClerkToken.ps1..." -ForegroundColor Yellow
    .\scripts\Set-ClerkToken.ps1
}

if (-not $env:CLERK_TOKEN) {
    Write-Host "  ✗ Failed to get Clerk token" -ForegroundColor Red
    exit 1
}

Write-Host "  ✓ Clerk token loaded" -ForegroundColor Green
Write-Host ""

# Step 3: Select URS file
Write-Host "[3/5] Selecting URS document..." -ForegroundColor Yellow
$ursFile = Get-Item "datasets\urs_corpus_v2\category_5\URS-025.md"
Write-Host "  ✓ URS File: $($ursFile.Name)" -ForegroundColor Green
Write-Host "  ✓ Size: $([math]::Round($ursFile.Length / 1KB, 2)) KB" -ForegroundColor Green
Write-Host ""

# Step 4: Submit job
Write-Host "[4/5] Submitting test generation job..." -ForegroundColor Yellow
try {
    $headers = @{
        "Authorization" = "Bearer $env:CLERK_TOKEN"
    }

    $response = Invoke-RestMethod -Uri "http://localhost:8080/jobs" `
        -Method Post `
        -Headers $headers `
        -Form @{ file = $ursFile }

    $jobId = $response.job_id
    Write-Host "  ✓ Job submitted successfully!" -ForegroundColor Green
    Write-Host "  ✓ Job ID: $jobId" -ForegroundColor Green
    Write-Host "  ✓ Status: $($response.status)" -ForegroundColor Green
    Write-Host "  ✓ Submitted at: $($response.submitted_at)" -ForegroundColor Green

} catch {
    Write-Host "  ✗ Job submission failed: $_" -ForegroundColor Red
    Write-Host "  Error details: $($_.Exception.Response)" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 5: Monitor job progress
Write-Host "[5/5] Monitoring job progress..." -ForegroundColor Yellow
Write-Host "  (Press Ctrl+C to stop monitoring)" -ForegroundColor Gray
Write-Host ""

$maxAttempts = 60  # 2 minutes max (60 attempts × 2 seconds)
$attempt = 0

while ($attempt -lt $maxAttempts) {
    try {
        $status = Invoke-RestMethod -Uri "http://localhost:8080/jobs/$jobId"

        $timestamp = Get-Date -Format "HH:mm:ss"
        $elapsed = $attempt * 2
        $statusText = "  [$timestamp] Status: $($status.status) - $elapsed seconds elapsed"

        Write-Host $statusText -ForegroundColor Cyan

        if ($status.status -eq "completed") {
            Write-Host ""
            Write-Host "  🎉 Job completed successfully!" -ForegroundColor Green
            Write-Host ""
            Write-Host "=== Final Job Details ===" -ForegroundColor Cyan
            $status | ConvertTo-Json | Write-Host
            Write-Host ""
            Write-Host "=== Next Steps ===" -ForegroundColor Yellow
            Write-Host "  1. Check worker logs: docker-compose -f docker-compose.dev.yml logs worker --tail=100"
            Write-Host "  2. View output files: docker exec pharma-api-dev ls -lah /app/output/"
            Write-Host "  3. Check database: docker exec pharma-postgres-dev psql -U postgres -d testgen -c 'SELECT * FROM jobs WHERE job_id = ''$jobId'';'"
            break
        } elseif ($status.status -eq "failed") {
            Write-Host ""
            Write-Host "  ✗ Job failed!" -ForegroundColor Red
            Write-Host ""
            Write-Host "=== Error Details ===" -ForegroundColor Red
            $status | ConvertTo-Json | Write-Host
            Write-Host ""
            Write-Host "=== Check Logs ===" -ForegroundColor Yellow
            Write-Host "  docker-compose -f docker-compose.dev.yml logs worker --tail=100"
            exit 1
        } elseif ($status.status -eq "processing") {
            # Show more detail during processing
            if ($status.PSObject.Properties['progress']) {
                Write-Host "    Progress: $($status.progress)" -ForegroundColor Gray
            }
        }

        $attempt++
        Start-Sleep -Seconds 2

    } catch {
        Write-Host "  ! Error checking status: $_" -ForegroundColor Red
        $attempt++
        Start-Sleep -Seconds 2
    }
}

if ($attempt -eq $maxAttempts) {
    Write-Host ""
    Write-Host "  ⚠ Job monitoring timed out after $($maxAttempts * 2) seconds" -ForegroundColor Yellow
    Write-Host "  Job may still be processing. Check status manually:" -ForegroundColor Yellow
    Write-Host "    Invoke-RestMethod -Uri 'http://localhost:8080/jobs/$jobId'" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== Test Complete ===" -ForegroundColor Cyan
