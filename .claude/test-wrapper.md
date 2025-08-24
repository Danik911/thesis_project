# Testing Claude Audio Wrapper

## Quick Test Instructions

### 1. Test with Simulation Script
```bash
# Source your bashrc to get the alias
source ~/.bashrc

# Run the test simulation through the wrapper
/home/anteb/thesis_project/.claude/claude-audio-wrapper.sh /home/anteb/thesis_project/.claude/test-permission-output.sh
```

You should hear a notification sound (1000 Hz, 250 ms beep) when the line "Claude needs your permission" appears, BEFORE you're prompted to press [y/N].

### 2. Test with Real Claude (using alias)
```bash
# Use the claude-audio alias
claude-audio --help
```

### 3. Test with Python Monitor (more advanced)
```bash
# Run with debug mode
CLAUDE_MONITOR_DEBUG=true /home/anteb/thesis_project/.claude/claude-monitor.py --help
```

### 4. Enable for All Claude Commands (optional)
To make ALL claude commands use audio notifications:
```bash
# Edit ~/.bashrc and uncomment the line:
# alias claude='/home/anteb/thesis_project/.claude/claude-audio-wrapper.sh'

# Then reload:
source ~/.bashrc
```

## What You Should Experience

1. When running any command through the wrapper
2. As soon as a permission request text appears on screen
3. You'll hear a notification sound (1000 Hz beep for 250ms)
4. BEFORE you need to press any key
5. Then you can respond to the prompt normally

## Debug Mode

Enable debug output:
```bash
CLAUDE_WRAPPER_DEBUG=true claude-audio <command>
```

Check logs:
```bash
tail -f /home/anteb/thesis_project/.claude/wrapper.log
tail -f /home/anteb/thesis_project/.claude/monitor.log
```

## Pattern Customization

The wrapper monitors for these patterns:
- "Do you want to allow"
- "Permission request"
- "Claude needs your permission"
- "[y/N]" or "[Y/n]"
- "Press yes"
- And more...

You can modify patterns in:
- `/home/anteb/thesis_project/.claude/claude-audio-wrapper.sh` (bash version)
- `/home/anteb/thesis_project/.claude/claude-monitor.py` (Python version)