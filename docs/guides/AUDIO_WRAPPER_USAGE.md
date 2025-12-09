# Claude Audio Wrapper Usage Instructions

## Important: Audio Wrapper Must Be Active From Session Start

The audio wrapper monitors Claude's output in real-time. It **must** be running from the beginning of your Claude session to detect permission requests.

## How to Start Claude with Audio Notifications

### Option 1: Use the `claude-audio` Alias (Recommended)
```bash
# Instead of running:
claude

# Run:
claude-audio
```

### Option 2: Direct Wrapper Execution
```bash
/home/anteb/thesis_project/.claude/claude-audio-wrapper.sh
```

### Option 3: Make Audio Wrapper Default (Optional)
Edit your `~/.bashrc` and uncomment the line:
```bash
alias claude='/home/anteb/thesis_project/.claude/claude-audio-wrapper.sh'
```

Then reload:
```bash
source ~/.bashrc
```

Now all `claude` commands will use the audio wrapper automatically.

## Testing ExitPlanMode Audio

1. **Start Claude with the wrapper**:
   ```bash
   claude-audio
   ```

2. **Enter plan mode**:
   - Type your request normally
   - Claude will enter plan mode

3. **When Claude uses ExitPlanMode**:
   - You should hear a notification sound (1000 Hz beep)
   - BEFORE the permission prompt appears
   - Then you can press 'y' to approve

## What the Wrapper Detects

The wrapper now monitors for these ExitPlanMode-related patterns:
- "exit plan mode" (case insensitive)
- "ExitPlanMode"
- "User has approved your plan"
- "ready to code"
- "start coding"
- Standard permission patterns ([y/N], etc.)

## Troubleshooting

### "I didn't hear the sound"
This usually means:
1. **Wrapper not active**: The current session isn't using the wrapper
2. **Pattern not matched**: The output didn't match any monitored patterns

### Check if Wrapper is Active
Look at your terminal prompt. If you started with `claude-audio`, the wrapper is active.

### Enable Debug Mode
```bash
CLAUDE_WRAPPER_DEBUG=true claude-audio
```

This will show when patterns are detected and audio is triggered.

### Check Logs
```bash
# View wrapper detection logs
tail -f /home/anteb/thesis_project/.claude/wrapper.log

# View Python monitor logs (if using Python version)
tail -f /home/anteb/thesis_project/.claude/monitor.log
```

## Key Point: Session Initialization

**Remember**: The wrapper must be running from the start of your Claude session. You cannot enable audio mid-session. If you forgot to start with `claude-audio`, you need to:
1. Exit the current Claude session
2. Start a new session with `claude-audio`