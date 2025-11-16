param(
    [string]$UserId,

    [string]$Template = "server-token",

    [string]$EnvFile = ".env.local",

    [switch]$Persist,

    [switch]$ListTemplates
)

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    throw "Python is required but was not found in PATH. Install Python 3.9+ and retry."
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$tokenScript = Join-Path $repoRoot "scripts\get_clerk_token.py"
if (-not (Test-Path $tokenScript)) {
    throw "Helper script not found at $tokenScript. Ensure the repository is intact."
}

$arguments = @($tokenScript, "--env-file", $EnvFile)

if ($ListTemplates) {
    $arguments += "--list-templates"
}
else {
    if (-not $UserId) {
        throw "-UserId is required unless --ListTemplates is specified."
    }
    $arguments += @("--user-id", $UserId, "--template", $Template)
}

$rawOutput = & $python.Path @arguments 2>&1
if ($LASTEXITCODE -ne 0) {
    $message = ($rawOutput | Out-String).Trim()
    throw "Clerk token helper failed.`n$message"
}

$normalizedOutput = if ($rawOutput -is [System.Array]) { $rawOutput -join [Environment]::NewLine } else { [string]$rawOutput }

if (-not $normalizedOutput) {
    throw "Clerk token helper returned no output."
}

if ($ListTemplates) {
    $normalizedOutput -split "`r?`n" | Where-Object { $_ } | ForEach-Object { Write-Host $_ }
    return
}

$lines = @($normalizedOutput -split "`r?`n" | Where-Object { $_ -and ($_ -notmatch "^session_id=") })
$tokenLine = if ($lines.Count) { [string]$lines[-1] } else { "" }
$token = $tokenLine.Trim()
if (-not $token) {
    throw "Unable to parse JWT from helper output."
}

$env:CLERK_TOKEN = $token
if ($Persist) {
    [Environment]::SetEnvironmentVariable("CLERK_TOKEN", $token, [EnvironmentVariableTarget]::User)
}

Write-Host "CLERK_TOKEN exported for this PowerShell session." -ForegroundColor Green
if ($Persist) {
    Write-Host "Persistent user-level CLERK_TOKEN updated." -ForegroundColor Yellow
}
