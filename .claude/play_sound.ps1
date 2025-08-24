# Enhanced PowerShell script for audio notifications
param(
    [string]$SoundType = "default",
    [string]$Message = "Claude Code Event"
)

# Try multiple Windows audio methods
try {
    # Method 1: System Sounds
    switch ($SoundType) {
        "edit" { 
            [System.Media.SystemSounds]::Question.Play()
            Write-Host "Edit sound played"
        }
        "write" { 
            [System.Media.SystemSounds]::Exclamation.Play()
            Write-Host "Write sound played"
        }
        "bash" { 
            [System.Media.SystemSounds]::Hand.Play()
            Write-Host "Bash sound played"
        }
        "todo" { 
            [System.Media.SystemSounds]::Asterisk.Play()
            Write-Host "Todo sound played"
        }
        default { 
            [System.Media.SystemSounds]::Beep.Play()
            Write-Host "Default sound played"
        }
    }
    
    # Method 2: Console Beep as backup
    [console]::beep(800,200)
    
    Write-Host "Audio notification successful"
    exit 0
    
} catch {
    Write-Host "Audio failed"
    exit 1
}