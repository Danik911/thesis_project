# Skill Quality & Evaluation

## Build Evaluations First

**Process:**
1. **Identify gaps**: Run Claude WITHOUT skill on real tasks
2. **Create test scenarios**: Minimum 3 representative cases
3. **Establish baseline**: Document current performance
4. **Write minimal instructions**: Pass evaluations with least documentation
5. **Iterate**: Refine based on results

**Rationale**: Ensures solving real problems, not imagined ones.

---

## Iterative Development with Claude

### Two-Claude Method

**Setup:**
- **Claude A**: Skill author/developer
- **Claude B**: Skill user/tester

**Cycle:**
1. Complete task with Claude A, noting repeated context
2. Ask Claude A to create skill from pattern
3. Test with Claude B on real tasks
4. Observe where Claude B struggles
5. Return to Claude A for refinements
6. Repeat based on observations

**Key**: Iterate based on real behavior, not assumptions.

---

## Testing Checklist

### Core Quality
- [ ] Description is specific with key terms and triggers
- [ ] SKILL.md body under 500 lines
- [ ] Additional details in separate files (one level deep)
- [ ] No time-sensitive information
- [ ] Consistent terminology throughout
- [ ] Examples are concrete with input/output
- [ ] Progressive disclosure used appropriately

### Code & Scripts
- [ ] Scripts solve problems, not punt to Claude
- [ ] Error handling is explicit
- [ ] All constants justified with comments
- [ ] Required packages listed and verified
- [ ] No Windows paths (always forward slashes)
- [ ] Validation steps for critical operations

### Cross-Model Testing
- [ ] Tested with Haiku (cost optimization)
- [ ] Tested with Sonnet (standard model)
- [ ] Tested with Opus (complex tasks)
- [ ] Tested with real usage scenarios
- [ ] Team feedback incorporated

---

## Distribution Notes

**Skills don't sync** across surfaces:
- claude.ai skills stay in claude.ai
- API skills stay in API context
- Claude Code skills are filesystem-based

**Claude Code locations:**
- Personal: `~/.claude/skills/`
- Project: `.claude/skills/`

**Sharing:**
- Git for team project skills
- Semantic versioning for stability
- Review quarterly against official docs

---

## Security Considerations

1. **Only trusted sources**: You created or Anthropic official
2. **Input validation**: Pydantic/Zod for structured validation
3. **Educational errors**: Helpful, actionable messages
4. **Tool hints**: `readOnlyHint`, `destructiveHint`, `idempotentHint`
