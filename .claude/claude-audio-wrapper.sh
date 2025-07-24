#!/bin/bash
# Claude Code Audio Wrapper - Smart permission detection with distinct sounds and cooldown
# This script monitors Claude's output and plays different sounds for different tool types

# Cooldown tracking
LAST_AUDIO_TIME=0
COOLDOWN_SECONDS=2

# Smart audio trigger function with sound type detection
play_permission_sound() {
    local line="$1"
    local current_time=$(date +%s)
    
    # Check cooldown to prevent spam
    if [ $((current_time - LAST_AUDIO_TIME)) -lt $COOLDOWN_SECONDS ]; then
        if [ "$DEBUG_MODE" = "true" ]; then
            echo "[WRAPPER] Audio skipped due to cooldown" >&2
        fi
        return
    fi
    
    # Determine sound type based on context
    local sound_type="notification"
    local message="Permission Request"
    
    # Detect tool type from the line
    if [[ "$line" =~ [Bb]ash|[Cc]ommand|[Ee]xecute ]]; then
        sound_type="bash"
        message="Bash Command Permission"
    elif [[ "$line" =~ [Ww]rite|[Cc]reate|[Ss]ave ]]; then
        sound_type="write"
        message="File Write Permission"
    elif [[ "$line" =~ [Ee]dit|[Mm]odify|[Cc]hange ]]; then
        sound_type="edit"
        message="File Edit Permission"
    elif [[ "$line" =~ [Rr]ead|[Vv]iew ]]; then
        sound_type="notification"
        message="File Read Permission"
    fi
    
    # Play the appropriate sound
    /mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe \
        -WindowStyle Hidden -ExecutionPolicy Bypass \
        -File /home/anteb/thesis_project/.claude/enhanced_play_sound.ps1 \
        -SoundType "$sound_type" -Message "$message" &
    
    # Update last audio time
    LAST_AUDIO_TIME=$current_time
    
    if [ "$DEBUG_MODE" = "true" ]; then
        echo "[WRAPPER] Audio played: $sound_type for $message" >&2
    fi
}

# Log function for debugging
log_detection() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Permission pattern detected: $1" >> /home/anteb/thesis_project/.claude/wrapper.log
}

# Critical permission patterns - ONLY for NEW permission requests
# Excludes already-allowed actions (todos, file edits, MCP calls)
PATTERNS=(
    "Do you want to allow.*first time"
    "Claude needs your permission.*new"
    "Allow.*execute.*new"
    "first time.*permission"
    "Permission.*required.*new"
)

# Create pattern regex
PATTERN_REGEX=$(IFS='|'; echo "${PATTERNS[*]}")

# Debug mode flag
DEBUG_MODE=${CLAUDE_WRAPPER_DEBUG:-false}

if [ "$DEBUG_MODE" = "true" ]; then
    echo "Claude Audio Wrapper - Debug Mode Enabled" >&2
    echo "Monitoring for patterns: $PATTERN_REGEX" >&2
fi

# Run Claude with real-time output monitoring
# Using stdbuf to ensure line-buffered output for immediate processing
stdbuf -oL -eL claude "$@" 2>&1 | while IFS= read -r line; do
    # Output line immediately (no buffering)
    echo "$line"
    
    # Check for permission patterns (case-insensitive)
    if [[ "$line" =~ ($PATTERN_REGEX) ]]; then
        # Log the detection
        log_detection "$line"
        
        # Trigger smart audio with context detection
        play_permission_sound "$line"
    fi
done

# Exit with Claude's exit code
exit ${PIPESTATUS[0]}