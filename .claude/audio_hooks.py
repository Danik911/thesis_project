#!/usr/bin/env uv run python
"""
Claude Code Audio Hooks Handler
Comprehensive audio notification system with multiple fallback methods
Based on haihai.ai tutorial, adapted for WSL2/Linux environments

Author: Claude Code Assistant
Date: 2025-07-22
"""

import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Configure logging with UTF-8 encoding for Windows compatibility
LOG_FILE = Path(__file__).parent / "hooks.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AudioManager:
    """Manages audio playback with multiple fallback methods"""

    def __init__(self, sounds_dir: Path):
        self.sounds_dir = sounds_dir
        self.powershell_path = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
        self.powershell_script = str(sounds_dir.parent / "play_sound.ps1")
        # Prioritize actual audio file playback over system beeps
        self.audio_methods = [
            self._try_windows_media_player,  # Windows native audio player
            self._try_vlc,           # Best quality audio playback
            self._try_mpg123,        # Good for MP3 files
            self._try_paplay,        # Linux audio (fallback)
            self._try_aplay,         # ALSA audio (fallback)
            self._try_windows_powershell,  # PowerShell with custom sound mapping
            self._try_system_beep,   # System beeps (lower priority)
            self._try_terminal_bell, # Terminal bell (lower priority)
            self._try_visual_notification  # Final fallback
        ]

    def play_sound(self, sound_file: str) -> bool:
        """Try to play sound using multiple methods, return True if successful"""
        if not sound_file:
            logger.warning("No sound file specified")
            return False

        sound_path = self.sounds_dir / sound_file

        # If sound file doesn't exist, try with .wav and .mp3 extensions
        if not sound_path.exists():
            for ext in [".wav", ".mp3"]:
                test_path = self.sounds_dir / f"{sound_file.replace('.wav', '').replace('.mp3', '')}{ext}"
                if test_path.exists():
                    sound_path = test_path
                    break

        if not sound_path.exists():
            logger.warning(f"Sound file not found: {sound_path}")
            # Fall back to PowerShell system sounds first
            if self._try_windows_powershell(sound_file):
                return True
            # Then visual notification as final fallback
            return self._try_visual_notification(sound_file)

        # Try each audio method until one succeeds
        for method in self.audio_methods:
            try:
                if method(str(sound_path)):
                    logger.info(f"Audio played successfully using {method.__name__}")
                    return True
            except Exception as e:
                logger.debug(f"Audio method {method.__name__} failed: {e}")
                continue

        logger.error("All audio methods failed")
        return False

    def _try_windows_powershell(self, sound_path: str) -> bool:
        """Try Windows PowerShell system sounds (primary method for WSL2)"""
        try:
            # First try the enhanced PowerShell script with audio session management
            if self._try_enhanced_powershell_script(sound_path):
                return True

            # Fallback to original direct PowerShell commands
            return self._try_direct_powershell_commands(sound_path)

        except Exception as e:
            logger.debug(f"Windows PowerShell method failed: {e}")
            return False

    def _try_enhanced_powershell_script(self, sound_path: str) -> bool:
        """Try enhanced PowerShell script with STA threading and audio session management"""
        try:
            enhanced_script = str(self.sounds_dir.parent / "enhanced_play_sound.ps1")
            if not Path(enhanced_script).exists():
                logger.debug("Enhanced PowerShell script not found, using fallback")
                return False

            # Get sound type from path
            sound_type = self._get_sound_type_from_path(sound_path)

            # Execute enhanced script with proper arguments and WSL2 audio permissions
            cmd = [
                self.powershell_path,
                "-WindowStyle", "Hidden",
                "-ExecutionPolicy", "Bypass",
                "-File", enhanced_script,
                "-SoundType", sound_type,
                "-Message", f"Claude Code Hook Audio - {sound_type}"
            ]

            logger.debug(f"Executing enhanced PowerShell script: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=False, capture_output=True, timeout=10, text=True)

            if result.returncode == 0 and "SUCCESS:" in result.stdout:
                logger.info(f"Enhanced PowerShell audio successful: {sound_type}")
                return True
            logger.debug(f"Enhanced PowerShell script failed: {result.stderr}")
            logger.debug(f"Enhanced PowerShell stdout: {result.stdout}")
            return False

        except Exception as e:
            logger.debug(f"Enhanced PowerShell script method failed: {e}")
            return False

    def _try_direct_powershell_commands(self, sound_path: str) -> bool:
        """Fallback to direct PowerShell commands (original implementation)"""
        try:
            # Map sound files to PowerShell system sounds
            sound_command = self._get_powershell_sound_command(sound_path)

            # Try with different PowerShell execution modes - prioritize working WSL2 audio approach
            cmd_variations = [
                # WSL2 audio working approach - WindowStyle Hidden + ExecutionPolicy Bypass
                [self.powershell_path, "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-Command", sound_command],
                # Alternative working approach
                [self.powershell_path, "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-Command", sound_command],
                # Standard fallbacks
                [self.powershell_path, "-ExecutionPolicy", "Bypass", "-Command", sound_command],
                [self.powershell_path, "-NoProfile", "-WindowStyle", "Hidden", "-Command", sound_command]
            ]

            for cmd in cmd_variations:
                try:
                    result = subprocess.run(cmd, check=False, capture_output=True, timeout=5, text=True,
                                          creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0)

                    if result.returncode == 0:
                        logger.info(f"Direct PowerShell audio successful: {sound_command}")
                        return True
                    logger.debug(f"PowerShell cmd failed: {' '.join(cmd)}, error: {result.stderr}")
                except Exception as inner_e:
                    logger.debug(f"PowerShell cmd exception: {inner_e}")
                    continue

            return False

        except Exception as e:
            logger.debug(f"Direct PowerShell commands failed: {e}")
            return False

    def _get_powershell_sound_command(self, sound_path: str) -> str:
        """Map sound file to direct PowerShell SystemSounds command"""
        filename = Path(sound_path).stem.lower()

        # Map to Windows SystemSounds API calls
        mapping = {
            "edit": "[System.Media.SystemSounds]::Question.Play()",
            "write": "[System.Media.SystemSounds]::Exclamation.Play()",
            "bash": "[System.Media.SystemSounds]::Hand.Play()",
            "todo": "[System.Media.SystemSounds]::Asterisk.Play()",
            "test": "[System.Media.SystemSounds]::Question.Play()",
            "error": "[System.Media.SystemSounds]::Hand.Play()",
            "notification": "[System.Media.SystemSounds]::Exclamation.Play()",
            "prompt": "[System.Media.SystemSounds]::Beep.Play()",
            "completion": "[System.Media.SystemSounds]::Asterisk.Play()"
        }

        for key, command in mapping.items():
            if key in filename:
                return command

        return "[System.Media.SystemSounds]::Beep.Play()"  # default

    def _get_sound_type_from_path(self, sound_path: str) -> str:
        """Extract sound type from file path for enhanced PowerShell script"""
        filename = Path(sound_path).stem.lower()

        # Map common sound file patterns to sound types
        sound_types = ["edit", "write", "bash", "todo", "test", "error", "notification", "prompt", "completion"]

        for sound_type in sound_types:
            if sound_type in filename:
                return sound_type

        # Check if it's a raw sound type (when called directly)
        if filename in sound_types:
            return filename

        return "default"

    def _try_windows_media_player(self, sound_path: str) -> bool:
        """Try Windows Media Player for audio file playback"""
        try:
            # Use PowerShell to play audio files with Windows Media Player
            cmd = [
                self.powershell_path,
                "-WindowStyle", "Hidden",
                "-ExecutionPolicy", "Bypass",
                "-Command",
                f"Add-Type -AssemblyName presentationCore; "
                f"$mediaPlayer = New-Object system.windows.media.mediaplayer; "
                f"$mediaPlayer.open([uri]'{sound_path}'); "
                f"$mediaPlayer.Play(); "
                f"Start-Sleep -Milliseconds 2000; "
                f"$mediaPlayer.Stop(); "
                f"$mediaPlayer.Close()"
            ]
            
            result = subprocess.run(cmd, check=False, capture_output=True, timeout=10, text=True)
            if result.returncode == 0:
                logger.info(f"Windows Media Player successfully played: {sound_path}")
                return True
            else:
                logger.debug(f"Windows Media Player failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.debug(f"Windows Media Player method failed: {e}")
            return False

    def _try_vlc(self, sound_path: str) -> bool:
        """Try VLC media player (quietest, most reliable)"""
        cmd = ["vlc", "--intf", "dummy", "--play-and-exit", sound_path]
        result = subprocess.run(cmd, check=False, capture_output=True, timeout=5)
        return result.returncode == 0

    def _try_mpg123(self, sound_path: str) -> bool:
        """Try mpg123 for MP3 files"""
        if not sound_path.lower().endswith(".mp3"):
            return False
        cmd = ["mpg123", "-q", sound_path]
        result = subprocess.run(cmd, check=False, capture_output=True, timeout=5)
        return result.returncode == 0

    def _try_paplay(self, sound_path: str) -> bool:
        """Try PulseAudio paplay"""
        cmd = ["paplay", sound_path]
        result = subprocess.run(cmd, check=False, capture_output=True, timeout=5)
        return result.returncode == 0

    def _try_aplay(self, sound_path: str) -> bool:
        """Try ALSA aplay"""
        if not sound_path.lower().endswith(".wav"):
            return False
        cmd = ["aplay", "-q", sound_path]
        result = subprocess.run(cmd, check=False, capture_output=True, timeout=5)
        return result.returncode == 0

    def _try_system_beep(self, sound_path: str) -> bool:
        """Try system beep as fallback"""
        try:
            # Different beep patterns for different sounds
            beep_pattern = self._get_beep_pattern(sound_path)
            for freq, duration in beep_pattern:
                subprocess.run(["beep", "-f", str(freq), "-l", str(duration)],
                             check=False, capture_output=True, timeout=2)
            return True
        except:
            return False

    def _try_terminal_bell(self, sound_path: str) -> bool:
        """Try terminal bell"""
        try:
            # Multiple bells for emphasis
            bell_count = self._get_bell_count(sound_path)
            for _ in range(bell_count):
                print("\a", end="", flush=True)
            return True
        except:
            return False

    def _try_visual_notification(self, sound_path: str) -> bool:
        """Visual notification as final fallback"""
        emoji = self._get_emoji_for_sound(sound_path)
        message = f"🔔 AUDIO: {emoji} {Path(sound_path).stem}"
        print(f"\n{message}\n", flush=True)
        logger.info(f"Visual notification: {message}")
        return True

    def _get_beep_pattern(self, sound_path: str) -> list:
        """Get beep pattern based on sound file"""
        patterns = {
            "edit": [(800, 200)],
            "write": [(1000, 150), (800, 150)],
            "bash": [(600, 300)],
            "todo": [(1200, 100), (1000, 100), (800, 100)],
            "error": [(400, 500)],
            "test": [(1000, 200)]
        }

        filename = Path(sound_path).stem.lower()
        for key, pattern in patterns.items():
            if key in filename:
                return pattern
        return [(800, 200)]  # default

    def _get_bell_count(self, sound_path: str) -> int:
        """Get bell count based on sound file"""
        counts = {
            "edit": 1,
            "write": 2,
            "bash": 1,
            "todo": 3,
            "error": 4,
            "test": 1
        }

        filename = Path(sound_path).stem.lower()
        for key, count in counts.items():
            if key in filename:
                return count
        return 1

    def _get_emoji_for_sound(self, sound_path: str) -> str:
        """Get emoji based on sound file"""
        emojis = {
            "edit": "📝",
            "write": "✍️",
            "bash": "💻",
            "todo": "✅",
            "error": "❌",
            "test": "🔊"
        }

        filename = Path(sound_path).stem.lower()
        for key, emoji in emojis.items():
            if key in filename:
                return emoji
        return "🔔"

class ClaudeHooksHandler:
    """Main handler for Claude Code hooks with audio support"""

    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.sounds_dir = self.base_dir / "sounds"
        self.audio_manager = AudioManager(self.sounds_dir)

        # Sound mapping based on haihai.ai tutorial
        self.sound_map = {
            # Tool events
            "Edit": "edit.wav",
            "Write": "write.wav",
            "MultiEdit": "edit.wav",
            "Bash": "bash.wav",
            "TodoWrite": "todo.wav",

            # System events
            "startup": "test.wav",
            "completion": "todo.wav",
            "error": "error.wav",

            # Hook events
            "Notification": "notification.wav",
            "UserPromptSubmit": "prompt.wav",
            "Stop": "todo.wav",

            # Default fallback
            "default": "test.wav"
        }

        logger.info("Claude Hooks Handler initialized")
        logger.info(f"Sounds directory: {self.sounds_dir}")
        logger.info(f"Available audio methods: {len(self.audio_manager.audio_methods)}")

    def handle_hook(self, hook_data: dict[str, Any]) -> dict[str, Any]:
        """Main hook handler - processes hook events and plays audio"""
        try:
            # Log the full hook event
            self.log_hook_data(hook_data)

            # Get sound file for this event
            sound_file = self.get_sound_for_event(hook_data)

            # SELECTIVE FILTERING: Only play audio if sound_file is not None
            if sound_file is None:
                # Skip audio for filtered events
                return {
                    "allow": True,
                    "message": f"Hook processed (filtered): {hook_data.get('hook_event_name', 'unknown')}"
                }

            # Play the sound
            success = self.audio_manager.play_sound(sound_file)

            # Return appropriate response
            return {
                "allow": True,
                "message": f"🔔 Hook processed: {hook_data.get('hook_event_name', 'unknown')} - Audio: {'✅' if success else '❌'}"
            }

        except Exception as e:
            logger.error(f"Hook handler error: {e}")
            return {
                "allow": True,
                "message": f"❌ Hook error: {e!s}"
            }

    def get_sound_for_event(self, hook_data: dict[str, Any]) -> str:
        """Determine appropriate sound file based on hook event - SELECTIVE MODE"""
        tool_name = hook_data.get("tool_name", "")
        hook_event = hook_data.get("hook_event_name", "")

        # SELECTIVE FILTERING: Only process specific events
        # 1. Stop events (task completion)
        if hook_event == "Stop":
            logger.info("Task completion detected")
            return self.get_context_aware_stop_sound(hook_data)

        # 2. Notification events (permission requests)
        if hook_event == "Notification":
            logger.info("Permission request notification detected")
            return "notification"

        # IGNORE all other events (PreToolUse, PostToolUse, UserPromptSubmit)
        # This eliminates notifications for routine tool operations
        logger.debug(f"Ignoring hook event: {hook_event} for tool: {tool_name}")
        return None  # Return None to skip audio

    def get_bash_sound(self, hook_data: dict[str, Any]) -> str:
        """Get sound for bash commands based on command content"""
        tool_input = hook_data.get("tool_input", {})
        command = tool_input.get("command", "").lower()

        # Command patterns (expandable)
        if any(word in command for word in ["git", "commit", "push"]):
            return "todo.wav"  # Success sound for git operations
        if any(word in command for word in ["test", "pytest", "npm test"]):
            return "test.wav"
        if any(word in command for word in ["error", "failed"]):
            return "error.wav"
        return "bash.wav"  # Default bash sound

    def log_hook_data(self, hook_data: dict[str, Any]):
        """Log hook event data for debugging"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "hook_event": hook_data.get("hook_event_name", "unknown"),
            "tool_name": hook_data.get("tool_name", "unknown"),
            "summary": self.get_event_summary(hook_data)
        }

        logger.info(f"Hook Event: {log_entry['summary']}")

        # Also write to JSON log file for detailed analysis
        json_log_file = self.base_dir / "hooks_detailed.log"
        try:
            with open(json_log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.warning(f"Failed to write JSON log: {e}")

    def get_event_summary(self, hook_data: dict[str, Any]) -> str:
        """Create human-readable summary of hook event"""
        tool_name = hook_data.get("tool_name", "Unknown")
        hook_event = hook_data.get("hook_event_name", "")

        # Handle system hook events
        if hook_event == "PreToolUse":
            return f"🚨 PRE-PERMISSION: About to request {tool_name} usage"
        if hook_event == "PostToolUse":
            return f"✅ POST-EXECUTION: {tool_name} completed"
        if hook_event == "Notification":
            return "🔔 Permission request notification"
        if hook_event == "UserPromptSubmit":
            return "📤 User prompt submitted"
        if hook_event == "Stop":
            return self.get_enhanced_stop_summary(hook_data)

        # Handle tool events
        if tool_name == "Edit":
            file_path = hook_data.get("tool_input", {}).get("file_path", "")
            filename = Path(file_path).name if file_path else "file"
            return f"📝 Editing {filename}"

        if tool_name == "Write":
            file_path = hook_data.get("tool_input", {}).get("file_path", "")
            filename = Path(file_path).name if file_path else "file"
            return f"✍️ Writing {filename}"

        if tool_name == "Bash":
            command = hook_data.get("tool_input", {}).get("command", "")[:50]
            return f"💻 Bash: {command}..."

        if tool_name == "TodoWrite":
            todos_count = len(hook_data.get("tool_input", {}).get("todos", []))
            return f"✅ Todo update: {todos_count} items"

        return f"🔔 {tool_name} - {hook_event}"

    def get_enhanced_stop_summary(self, hook_data: dict[str, Any]) -> str:
        """Enhanced Stop event analysis - Limited to available hook data only"""
        try:
            # Since Claude Code only provides hook_event_name, tool_name, and tool_input,
            # we need alternative approaches for planning mode detection

            # For now, use simple detection based on timing patterns or manual triggers
            # This is a limitation of the Claude Code hooks system

            return "✅ Task completed"

        except Exception as e:
            logger.error(f"Enhanced stop analysis error: {e}")
            return "✅ Task completed"

    def get_context_aware_stop_sound(self, hook_data: dict[str, Any]) -> str:
        """Return different sounds based on Stop event context"""
        try:
            # Since Claude Code hooks have limited data, use a simple approach:
            # Check for a planning mode flag file as a manual override
            planning_flag_file = self.base_dir / "planning_mode_flag.txt"

            if planning_flag_file.exists():
                # Planning mode detected - use different sound
                try:
                    planning_flag_file.unlink()  # Remove the flag file after use
                    logger.info("Planning mode flag detected - using planning completion sound")
                    return "planning"  # Use planning sound type for enhanced script
                except:
                    pass

            # Default task completion sound
            return self.sound_map["Stop"]

        except Exception as e:
            logger.debug(f"Context-aware stop sound error: {e}")
            return self.sound_map["Stop"]

def main():
    """Main entry point for Claude Code hooks"""
    try:
        # Initialize handler
        handler = ClaudeHooksHandler()

        # Read hook data from stdin (Claude Code provides this)
        if len(sys.argv) > 1:
            # If arguments provided, treat as test mode
            test_event = {
                "hook_event_name": "PreToolUse",
                "tool_name": sys.argv[1] if len(sys.argv) > 1 else "Test",
                "tool_input": {"command": "test audio"}
            }
            result = handler.handle_hook(test_event)
            print(json.dumps(result, indent=2))
        else:
            # Read from stdin (normal hook operation)
            hook_data = json.loads(sys.stdin.read())
            result = handler.handle_hook(hook_data)
            print(json.dumps(result))

    except Exception as e:
        logger.error(f"Main error: {e}")
        print(json.dumps({"allow": True, "message": f"Hook error: {e!s}"}))

if __name__ == "__main__":
    main()
