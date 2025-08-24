# Serena MCP - Semantic Code Intelligence Tool

## Overview
Serena is a powerful semantic code intelligence MCP server available in this project that provides advanced code analysis and manipulation capabilities beyond standard text-based tools.

## Key Capabilities

### 1. Symbol-Based Operations
- **find_symbol**: Locate classes, methods, functions by name path without knowing file locations
- **replace_symbol_body**: Replace entire method/class bodies precisely
- **insert_before_symbol/insert_after_symbol**: Add code at semantically correct locations
- **get_symbols_overview**: Understand file/directory structure at symbol level

### 2. Code Intelligence
- **find_referencing_symbols**: Track where symbols are used (critical for multi-agent dependencies)
- **search_for_pattern**: Flexible regex search across codebase with context lines
- **Relationship mapping**: Understand how agents communicate through events and shared state

### 3. Project Memory System
- **write_memory**: Store persistent knowledge about project patterns, decisions, compliance rules
- **read_memory**: Retrieve stored insights across sessions
- **list_memories**: See available project knowledge base

## Practical Usage for Pharmaceutical Test Generation Project

### Task 1 - Fix Categorization Agent Fallbacks
```python
# Find fallback logic
mcp__serena__search_for_pattern --substring_pattern="score.*0\.[789]|default.*category|fallback" --relative_path="main/src/agents/categorization"

# Replace symbol body to remove fallbacks
mcp__serena__replace_symbol_body --name_path="CategorationAgent/categorize" --relative_path="main/src/agents/categorization/agent.py" --body="<new implementation>"
```

### Multi-Agent System Analysis
```python
# Understand agent event flow
mcp__serena__find_referencing_symbols --name_path="emit_event" --relative_path="main/src/core/unified_workflow.py"

# Get agent structure overview
mcp__serena__get_symbols_overview --relative_path="main/src/agents"
```

### Compliance Pattern Storage
```python
# Store GAMP-5 patterns
mcp__serena__write_memory --memory_name="gamp5_implementation_patterns" --content="<patterns>"

# Store validation rules
mcp__serena__write_memory --memory_name="pharmaceutical_validation_rules" --content="<rules>"
```

## Advantages Over Standard Tools

1. **Semantic Understanding**: Understands code structure (classes, methods, inheritance) not just text
2. **Precise Modifications**: Edit at symbol level without complex regex patterns
3. **Dependency Tracking**: Automatically find all references when modifying interfaces
4. **Persistent Knowledge**: Build project-specific intelligence over time
5. **Efficient Navigation**: Jump directly to relevant code without reading entire files

## Best Practices

### DO:
- Use symbol tools for structural changes (adding/modifying methods, classes)
- Store critical project insights in memory for future reference
- Use find_referencing_symbols before modifying public interfaces
- Leverage get_symbols_overview to understand new code areas

### DON'T:
- Read entire files when only specific symbols are needed
- Use regex for complex structural changes (use symbol tools instead)
- Forget to check references before breaking changes
- Re-read the same content with different tools

## Integration with Task-Master AI Workflow

1. **Before task**: Read relevant memories about implementation patterns
2. **Research phase**: Use get_symbols_overview to understand affected code
3. **Implementation**: Use symbol-based editing for precise changes
4. **Validation**: Use find_referencing_symbols to ensure no breaks
5. **Completion**: Write new insights to memory for future tasks

## Critical for Regulatory Compliance

Serena's precise symbol tracking is essential for:
- Ensuring no fallback logic exists (regulatory requirement)
- Tracking all error handling paths
- Validating agent communication patterns
- Maintaining GAMP-5 categorization integrity
- Documenting compliance decisions in memory

Remember: Serena provides semantic understanding crucial for maintaining pharmaceutical validation standards and regulatory compliance in this multi-agent system.