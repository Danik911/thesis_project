#!/usr/bin/env uv run python
"""
Claude Code Audio Monitor - Advanced real-time permission detection
Monitors Claude output and triggers audio notifications BEFORE permission prompts
"""

import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path


class ClaudeAudioMonitor:
    def __init__(self):
        # Base directory
        self.base_dir = Path(__file__).parent

        # Permission patterns to detect (case-insensitive)
        self.patterns = [
            r"Do you want to allow",
            r"Allow\s+once\s+Allow\s+all",
            r"Permission.*request",
            r"Claude needs your permission",
            r"Allow.*execute",
            r"Would you like to.*proceed",
            r"Confirm.*action",
            r"Press.*to.*allow",
            r"tool use.*rejected",
            r"wants to.*permission",
            r"approve.*tool",
            r"\[y/N\]",
            r"\[Y/n\]",
            r"yes/no",
            r"Press.*yes",
            r"ExitPlanMode.*permission",
            r"permission.*required",
            r"authorization.*needed",
            r"exit.*plan.*mode",
            r"ExitPlanMode",
            r"User has approved your plan",
            r"ready to.*code",
            r"start.*coding"
        ]

        # Compile regex pattern
        self.pattern_regex = re.compile("|".join(self.patterns), re.IGNORECASE)

        # Audio script path
        self.audio_script = self.base_dir / "enhanced_play_sound.ps1"

        # Log file
        self.log_file = self.base_dir / "monitor.log"

        # Debug mode
        self.debug = os.environ.get("CLAUDE_MONITOR_DEBUG", "false").lower() == "true"

        # Track last audio play time to avoid rapid repeats
        self.last_audio_time = 0
        self.audio_cooldown = 0.5  # seconds

    def log(self, message):
        """Log message to file and optionally to stderr"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - {message}"

        # Write to log file
        with open(self.log_file, "a") as f:
            f.write(log_entry + "\n")

        # Debug output
        if self.debug:
            print(f"[MONITOR] {log_entry}", file=sys.stderr)

    def play_audio(self, context="Permission Request"):
        """Trigger audio notification in background thread"""
        current_time = time.time()

        # Check cooldown to avoid rapid repeats
        if current_time - self.last_audio_time < self.audio_cooldown:
            self.log(f"Audio cooldown active, skipping: {context}")
            return

        self.last_audio_time = current_time

        def _play():
            try:
                # Use enhanced PowerShell script
                cmd = [
                    "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
                    "-WindowStyle", "Hidden",
                    "-ExecutionPolicy", "Bypass",
                    "-File", str(self.audio_script),
                    "-SoundType", "notification",
                    "-Message", f"Claude Monitor: {context}"
                ]

                subprocess.run(cmd, check=False, capture_output=True, timeout=2)
                self.log(f"Audio triggered for: {context}")

            except Exception as e:
                self.log(f"Audio error: {e!s}")

        # Play in background to not block output
        threading.Thread(target=_play, daemon=True).start()

    def monitor_line(self, line):
        """Check line for permission patterns"""
        # Strip ANSI escape codes for cleaner matching
        clean_line = re.sub(r"\x1b\[[0-9;]*m", "", line)

        match = self.pattern_regex.search(clean_line)
        if match:
            self.log(f"Pattern detected: '{match.group()}' in line: {clean_line.strip()}")
            self.play_audio(f"Pattern: {match.group()}")
            return True
        return False

    def run(self, claude_args):
        """Run Claude with monitoring"""
        self.log(f"Starting monitor with args: {claude_args}")

        # Build command
        cmd = ["claude"] + claude_args

        # Start Claude process with unbuffered output
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=sys.stdin,
            text=True,
            bufsize=1,  # Line buffered
            env=env
        )

        # Monitor output in real-time
        try:
            for line in process.stdout:
                # Print line immediately with flush
                print(line, end="", flush=True)

                # Check for permission patterns
                if line.strip():  # Only check non-empty lines
                    self.monitor_line(line)

        except KeyboardInterrupt:
            self.log("Monitor interrupted by user")
            process.terminate()
        except Exception as e:
            self.log(f"Monitor error: {e!s}")
            process.terminate()

        # Wait for process to complete
        return_code = process.wait()
        self.log(f"Claude exited with code: {return_code}")

        return return_code

def main():
    """Main entry point"""
    monitor = ClaudeAudioMonitor()

    # Show startup message in debug mode
    if monitor.debug:
        print("[MONITOR] Claude Audio Monitor Started", file=sys.stderr)
        print(f"[MONITOR] Monitoring {len(monitor.patterns)} patterns", file=sys.stderr)
        print(f"[MONITOR] Log file: {monitor.log_file}", file=sys.stderr)

    # Run with command line arguments
    sys.exit(monitor.run(sys.argv[1:]))

if __name__ == "__main__":
    main()
