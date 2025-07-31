# PowerShell wrapper for Claude Code hooks on Windows
# This script ensures proper Python execution and error handling

param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

try {
    $pythonPath = "python"
    $scriptPath = "C:\Users\anteb\Desktop\Courses\Projects\thesis_project\.claude\audio_hooks.py"
    
    # Execute the Python script with all arguments
    if ($Arguments) {
        & $pythonPath $scriptPath $Arguments
    } else {
        & $pythonPath $scriptPath
    }
    
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        Write-Error "Hook script failed with exit code: $exitCode"
        exit $exitCode
    }
} catch {
    Write-Error "PowerShell hook wrapper failed: $($_.Exception.Message)"
    exit 1
}