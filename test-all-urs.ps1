# Test All URS Documents - PowerShell Script
# Comprehensive test of pharmaceutical test generation with all 8 URS documents

Write-Host "=== Pharmaceutical Test Generation - Batch URS Test ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Verify health
Write-Host "[1/5] Checking API health..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8080/health"
    Write-Host "  ✓ API Status: $($health.status)" -ForegroundColor Green
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

# Step 3: Find all URS files
Write-Host "[3/5] Finding URS documents..." -ForegroundColor Yellow
$ursFiles = Get-ChildItem -Path "datasets\urs_corpus_v2" -Recurse -Filter "URS-*.md" | Sort-Object Name
Write-Host "  ✓ Found $($ursFiles.Count) URS documents" -ForegroundColor Green

foreach ($file in $ursFiles) {
    $category = $file.Directory.Name
    Write-Host "    - $($file.Name) ($category)" -ForegroundColor Gray
}

Write-Host ""

# Step 4: Submit all jobs
Write-Host "[4/5] Submitting test generation jobs..." -ForegroundColor Yellow

$jobs = @()
$headers = @{
    "Authorization" = "Bearer $env:CLERK_TOKEN"
}

foreach ($ursFile in $ursFiles) {
    try {
        $category = $ursFile.Directory.Name
        Write-Host "  Submitting: $($ursFile.Name) [$category]..." -ForegroundColor Cyan

        $response = Invoke-RestMethod -Uri "http://localhost:8080/jobs" `
            -Method Post `
            -Headers $headers `
            -Form @{ file = $ursFile }

        $jobs += @{
            JobId = $response.job_id
            File = $ursFile.Name
            Category = $category
            Status = $response.status
            SubmittedAt = $response.submitted_at
        }

        Write-Host "    ✓ Job ID: $($response.job_id)" -ForegroundColor Green

        # Small delay to avoid overwhelming the queue
        Start-Sleep -Milliseconds 500

    } catch {
        Write-Host "    ✗ Failed: $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "  ✓ Submitted $($jobs.Count) jobs" -ForegroundColor Green
Write-Host ""

# Step 5: Monitor all jobs
Write-Host "[5/5] Monitoring job progress..." -ForegroundColor Yellow
Write-Host "  (Press Ctrl+C to stop monitoring)" -ForegroundColor Gray
Write-Host ""

$maxAttempts = 120  # 4 minutes max
$attempt = 0
$completedJobs = @()
$failedJobs = @()

while ($attempt -lt $maxAttempts) {
    Clear-Host
    Write-Host "=== Job Status Monitor ===" -ForegroundColor Cyan
    Write-Host "Time: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Gray
    Write-Host "Elapsed: $($attempt * 2) seconds" -ForegroundColor Gray
    Write-Host ""

    $completed = 0
    $failed = 0
    $processing = 0
    $pending = 0

    foreach ($job in $jobs) {
        try {
            $status = Invoke-RestMethod -Uri "http://localhost:8080/jobs/$($job.JobId)"

            $statusColor = switch ($status.status) {
                "completed" { "Green"; $completed++; break }
                "failed" { "Red"; $failed++; break }
                "processing" { "Yellow"; $processing++; break }
                "pending" { "Cyan"; $pending++; break }
                default { "Gray" }
            }

            $statusText = $status.status.ToUpper().PadRight(10)
            Write-Host "  [$statusText] $($job.File) [$($job.Category)]" -ForegroundColor $statusColor

            # Track completed/failed
            if ($status.status -eq "completed" -and $job.JobId -notin $completedJobs) {
                $completedJobs += $job.JobId
            } elseif ($status.status -eq "failed" -and $job.JobId -notin $failedJobs) {
                $failedJobs += $job.JobId
            }

        } catch {
            Write-Host "  [ERROR    ] $($job.File) - $_" -ForegroundColor Red
        }
    }

    Write-Host ""
    Write-Host "Summary:" -ForegroundColor Cyan
    Write-Host "  ✓ Completed: $completed" -ForegroundColor Green
    Write-Host "  ⚙ Processing: $processing" -ForegroundColor Yellow
    Write-Host "  ⏳ Pending: $pending" -ForegroundColor Cyan
    Write-Host "  ✗ Failed: $failed" -ForegroundColor Red

    # Exit if all done
    if ($completed + $failed -eq $jobs.Count) {
        Write-Host ""
        Write-Host "=== All jobs completed! ===" -ForegroundColor Green
        break
    }

    $attempt++
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host "=== Final Results ===" -ForegroundColor Cyan
Write-Host ""

foreach ($job in $jobs) {
    try {
        $status = Invoke-RestMethod -Uri "http://localhost:8080/jobs/$($job.JobId)"

        Write-Host "File: $($job.File) [$($job.Category)]" -ForegroundColor White
        Write-Host "  Job ID: $($job.JobId)"
        Write-Host "  Status: $($status.status)"
        Write-Host "  Submitted: $($job.SubmittedAt)"
        if ($status.updated_at) {
            Write-Host "  Updated: $($status.updated_at)"
        }
        Write-Host ""

    } catch {
        Write-Host "File: $($job.File)" -ForegroundColor White
        Write-Host "  Error: $_" -ForegroundColor Red
        Write-Host ""
    }
}

Write-Host "=== Test Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Check worker logs: docker-compose -f docker-compose.dev.yml logs worker"
Write-Host "  2. View output files: docker exec pharma-api-dev ls -lRh /app/output/"
Write-Host "  3. Check database: docker exec pharma-postgres-dev psql -U postgres -d testgen -c 'SELECT job_id, status, created_at FROM jobs ORDER BY created_at DESC LIMIT 10;'"
Write-Host "  4. View LangFuse traces: https://cloud.langfuse.com"
Write-Host ""
