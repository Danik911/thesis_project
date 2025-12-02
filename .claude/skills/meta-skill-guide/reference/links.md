# External References & Links

## Official Documentation

- **Skills Overview**: https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview
- **Best Practices**: https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices
- **Claude Code Skills**: https://docs.claude.com/en/docs/claude-code/skills
- **Release Notes**: https://docs.claude.com/en/release-notes/overview

---

## GitHub Repositories

- **Anthropic Skills**: https://github.com/anthropics/skills
- **Claude Cookbooks**: https://github.com/anthropics/claude-cookbooks/tree/main/skills
- **Custom Skills Examples**: https://github.com/anthropics/claude-cookbooks/tree/main/skills/custom_skills

---

## Skill Examples by Complexity

### Simple Skills
- **Algorithmic Art**: https://github.com/anthropics/skills/tree/main/algorithmic-art

### Moderate Skills
- **XLSX**: https://github.com/anthropics/skills/tree/main/document-skills/xlsx
- **PDF**: https://github.com/anthropics/skills/tree/main/document-skills/pdf

### Advanced Skills
- **MCP Builder**: https://github.com/anthropics/skills/tree/main/mcp-builder
- **Webapp Testing**: https://github.com/anthropics/skills/tree/main/webapp-testing

### Enterprise Skills
- **Brand Guidelines**: https://github.com/anthropics/skills/tree/main/brand-guidelines
- **Internal Comms**: https://github.com/anthropics/skills/tree/main/internal-comms

### Workflow Skills
- **Worktree Manager**: https://github.com/disler/claude-code-hooks-multi-agent-observability/tree/main/.claude/skills

---

## Subagent Resources

- **Official Guide**: https://docs.claude.com/en/docs/claude-code/sub-agents
- **Community Collection**: https://github.com/VoltAgent/awesome-claude-code-subagents
- **Practical Integration**: https://jewelhuq.medium.com/practical-guide-to-mastering-claude-codes-main-agent-and-sub-agents-fd52952dcf00
- **Parallelization Guide**: https://zachwills.net/how-to-use-claude-code-subagents-to-parallelize-development/
- **Best Practices**: https://www.anthropic.com/engineering/claude-code-best-practices

---

## API Version Headers

```python
# For programmatic skill creation via API
headers = {
    "anthropic-beta": "skills-2025-10-02",
    "anthropic-beta": "code-execution-2025-08-25",
    "anthropic-beta": "files-api-2025-04-14"
}
```

---

## Versioning & Updates

**This Guide Version**: 1.2.0 (December 2025)
- **v1.2.0**: Refactored to progressive disclosure pattern
- **v1.1.0**: Added subagent integration patterns
- **v1.0.0**: Initial release

**Update Policy:**
- When official documentation changes skill specifications
- When new skill patterns emerge from Anthropic
- When API versions update (check headers above)
- Review quarterly against official docs
