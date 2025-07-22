# Claude Code Overview

Claude Code is an AI-powered development tool that helps you code faster through natural language commands.

## Key Capabilities

### Development Acceleration
- Edit files and fix bugs across your codebase
- Answer questions about code architecture and logic  
- Execute and fix tests, linting, and other commands
- Search through git history, resolve merge conflicts, and create commits and PRs
- Browse documentation and resources from the internet using web search

### Security and Privacy
- Direct API connection to Anthropic's API
- Works directly in your terminal
- Maintains awareness of your entire project structure
- Performs real operations like editing files and creating commits

## Essential Commands

| Command | Description | Example |
|---------|-------------|---------|
| `claude` | Start interactive mode | `claude` |
| `claude "task"` | Run a one-time task | `claude "fix the build error"` |
| `claude -p "query"` | Run query and exit | `claude -p "explain this function"` |
| `claude -c` | Continue recent conversation | `claude -c` |
| `claude -r` | Resume previous conversation | `claude -r` |
| `claude commit` | Create a Git commit | `claude commit` |

## Interactive Session Commands

| Command | Purpose |
|---------|---------|
| `/clear` | Clear conversation history |
| `/help` | Show available commands |
| `/init` | Initialize project with CLAUDE.md guide |
| `/config` | View/modify configuration |
| `/memory` | Edit CLAUDE.md memory files |
| `/review` | Request code review |
| `/cost` | Show token usage statistics |

## Best Practices

### Be Specific
- Instead of "fix the bug", say "fix the login bug where users see a blank screen after entering wrong credentials"

### Use Step-by-Step Instructions
- Break complex tasks into steps
- Let Claude explore and understand your code first

### Leverage Context
- Claude reads files as needed - no manual context addition required
- Ask questions about architecture before making changes

## Working with PRPs

When using Claude Code with the PRP framework:

1. **Context is King**: Include comprehensive documentation and examples in PRPs
2. **Validation Loops**: Provide executable commands for testing
3. **Progressive Success**: Start simple, validate, then enhance
4. **Use Slash Commands**: Leverage custom commands for PRP workflows

## Tools Available

Claude Code has access to various tools for:
- File operations (read, write, edit)
- Code search and analysis
- Git operations
- Web browsing and search
- Command execution
- Test running and debugging