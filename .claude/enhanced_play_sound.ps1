# Enhanced PowerShell Audio Script for Claude Code Hooks
# Implements audio session management for reliable WSL2 audio execution
# Version: 2.0 - Enhanced for subprocess execution context
# Date: 2025-07-23

param(
    [Parameter(Mandatory=$true)]
    [string]$SoundType,
    
    [Parameter(Mandatory=$false)]
    [string]$Message = ""
)

# Configure error handling
$ErrorActionPreference = "Continue"
$VerbosePreference = "Continue"

# Log function for debugging
function Write-AudioLog {
    param([string]$LogMessage)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss,fff"
    $logFile = Join-Path $PSScriptRoot "enhanced_audio.log"
    "$timestamp - INFO - $LogMessage" | Out-File -FilePath $logFile -Append -Encoding UTF8
    Write-Verbose $LogMessage
}

Write-AudioLog "Enhanced PowerShell audio script started - SoundType: $SoundType"

try {
    # CRITICAL: Set Single Threaded Apartment (STA) mode for audio context
    # This is essential for Windows audio APIs to work properly in subprocess execution
    Write-AudioLog "Setting thread apartment state to STA"
    [System.Threading.Thread]::CurrentThread.SetApartmentState([System.Threading.ApartmentState]::STA)
    
    # Initialize audio context without requiring additional assemblies
    # Use the built-in SystemSounds that are available by default
    Write-AudioLog "Initializing audio context using built-in Windows capabilities"
    
    # Map sound types to Windows SystemSounds with enhanced reliability
    $soundMapping = @{
        'edit' = 'Question'
        'write' = 'Exclamation'
        'bash' = 'Hand'  
        'todo' = 'Asterisk'
        'test' = 'Question'
        'error' = 'Hand'
        'notification' = 'Exclamation'
        'prompt' = 'Beep'
        'completion' = 'Asterisk'
        'planning' = 'Question'  # Special sound for planning mode
        'default' = 'Beep'
    }
    
    # Determine the appropriate system sound
    $systemSound = 'Beep'  # default fallback
    foreach ($key in $soundMapping.Keys) {
        if ($SoundType.ToLower().Contains($key)) {
            $systemSound = $soundMapping[$key]
            break
        }
    }
    
    Write-AudioLog "Mapped sound type '$SoundType' to Windows SystemSound '$systemSound'"
    
    # Execute the system sound with enhanced error handling
    # Multiple execution attempts with different approaches
    $audioSuccess = $false
    
    # Method 1: Console beep (WSL2 subprocess compatible - no elevation required)
    try {
        Write-AudioLog "Attempt 1: Console beep method (WSL2 compatible)"
        $beepParams = @{
            'Question' = @(800, 300)
            'Exclamation' = @(1000, 250)
            'Hand' = @(400, 400)
            'Asterisk' = @(1200, 200)
            'Beep' = @(800, 150)
            'edit' = @(800, 300)
            'write' = @(1000, 250)
            'bash' = @(400, 400)
            'todo' = @(1200, 200)
            'planning' = @(800, 300)
            'default' = @(800, 150)
        }
        
        # Try direct sound type first, then mapped system sound
        $freq = 800
        $duration = 200
        
        if ($beepParams.ContainsKey($SoundType.ToLower())) {
            $freq, $duration = $beepParams[$SoundType.ToLower()]
            Write-AudioLog "Using direct sound type mapping: $SoundType -> $freq Hz, $duration ms"
        }
        elseif ($beepParams.ContainsKey($systemSound)) {
            $freq, $duration = $beepParams[$systemSound]
            Write-AudioLog "Using system sound mapping: $systemSound -> $freq Hz, $duration ms"
        }
        else {
            Write-AudioLog "Using default beep: $freq Hz, $duration ms"
        }
        
        [Console]::Beep($freq, $duration)
        Start-Sleep -Milliseconds 100  # Allow sound to complete
        Write-AudioLog "Audio method 1 (console beep) succeeded: $freq Hz, $duration ms"
        $audioSuccess = $true
    }
    catch {
        Write-AudioLog "Audio method 1 failed: $($_.Exception.Message)"
        
        # Method 2: SystemSounds fallback (may require elevation)
        try {
            Write-AudioLog "Attempt 2: SystemSounds fallback (may require elevation)"
            $command = "[System.Media.SystemSounds]::$systemSound.Play()"
            Invoke-Expression $command
            Start-Sleep -Milliseconds 150
            Write-AudioLog "Audio method 2 (SystemSounds) succeeded for sound '$systemSound'"
            $audioSuccess = $true
        }
        catch {
            Write-AudioLog "Audio method 2 failed: $($_.Exception.Message)"
        }
    }
    
    if ($audioSuccess) {
        Write-AudioLog "Enhanced PowerShell audio successful: $systemSound"
        if ($Message) {
            Write-AudioLog "Audio context: $Message"
        }
        
        # Return success indicator for calling script
        Write-Output "SUCCESS: Enhanced audio played - $systemSound"
        exit 0
    }
    else {
        Write-AudioLog "All enhanced audio methods failed for sound: $systemSound"
        Write-Output "FAILURE: Enhanced audio failed - $systemSound"
        exit 1
    }
}
catch {
    $errorMsg = "Enhanced PowerShell audio script error: $($_.Exception.Message)"
    Write-AudioLog $errorMsg
    Write-Error $errorMsg
    Write-Output "ERROR: $errorMsg"
    exit 1
}
finally {
    Write-AudioLog "Enhanced PowerShell audio script completed"
}