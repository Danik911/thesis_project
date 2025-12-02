# Best Practices Checklist

## Content & Structure

### DO

1. **Keep SKILL.md under 500 lines**
   - Context window shared across system prompts, conversation, and skills
   - Use progressive disclosure for additional content

2. **Write descriptions in third person with triggers**
   - "Extracts text from PDFs. Use when working with PDF files or document extraction."
   - NOT "I can help you process Excel files" (wrong perspective)
   - NOT "Helps with documents" (too vague)

3. **Use consistent terminology throughout**
   - Pick one term and stick to it (e.g., always "API endpoint" not URL/route/path)

4. **Provide concrete examples with input/output pairs**
   - Demonstrates desired style and detail level
   - Especially critical for code/content generation

5. **Implement validation loops for quality**
   - Pattern: Create -> Validate -> Fix -> Repeat
   - Example: Generate JSON -> Validate schema -> Execute

6. **Structure long reference files with table of contents**
   - Files over 100 lines need navigation

7. **Use checklists for complex multi-step tasks**
   ```markdown
   Task Progress:
   - [ ] Step 1: [Action with command]
   - [ ] Step 2: [Validation step]
   - [ ] Step 3: [Next action]
   ```

8. **Appropriate degrees of freedom**
   - High freedom (text): Multiple valid approaches
   - Medium freedom (pseudocode): Preferred patterns with variations
   - Low freedom (scripts): Exact sequences for fragile operations

---

## Code & Scripts

### DO

1. **Solve problems, don't punt to Claude**
   - Handle error conditions explicitly
   - Provide alternatives for common issues
   - Scripts should be production-ready

2. **Justify all constants and magic numbers**
   - `TIMEOUT = 47  # Most failures resolve by second retry`
   - NOT `TIMEOUT = 47` (why 47?)

3. **List required packages explicitly**
   ```bash
   pip install pypdf pydantic
   ```

4. **Create verifiable intermediate outputs**
   - Pattern: Create plan file -> Validate -> Execute
   - Catches errors before destructive changes

5. **Provide default approach with escape hatches**
   - "Use pdfplumber for text extraction. For scanned PDFs, use pdf2image with pytesseract."
   - NOT listing multiple equal options without guidance

---

## Progressive Disclosure Patterns

### Pattern 1: High-Level Guide with References
```markdown
# Main Skill

## Quick Start
[Basic instructions]

## Common Operations
[Frequent use cases]

For advanced features, see reference/advanced.md
For API reference, see reference/api.md
```

### Pattern 2: Conditional Details
```markdown
## Basic Usage
[Standard approach]

<details>
<summary>Advanced: Handling Edge Cases</summary>
[Special case handling - collapsed by default]
</details>
```

**Critical**: Keep references **one level deep** from SKILL.md.

---

## Anti-Patterns

### DON'T

1. **Reference time-sensitive information**
   - Use "current method" vs. "legacy" sections
   - NOT "As of January 2025..."

2. **Use Windows-style paths**
   - `scripts/helper.py`
   - NOT `scripts\helper.py`

3. **Assume tools are pre-installed**
   - Always show explicit installation steps

4. **Use vague MCP tool references**
   - `ServerName:tool_name` (e.g., `BigQuery:bigquery_schema`)
   - NOT `tool_name`

5. **Provide too many equal options**
   - Causes decision paralysis
   - Provide default + alternatives for specific scenarios

6. **Create deeply nested references**
   - SKILL.md -> File1.md (OK)
   - SKILL.md -> File1.md -> File2.md (BAD)

7. **Inspect DOM before network stabilization (web testing)**
   - Wait for `networkidle` state before inspection

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
- [ ] Scripts have clear documentation
- [ ] No Windows paths (always forward slashes)
- [ ] Validation steps for critical operations
- [ ] Feedback loops for quality tasks

### Cross-Model Testing
- [ ] Tested with Haiku (cost optimization)
- [ ] Tested with Sonnet (standard model)
- [ ] Tested with Opus (complex tasks)
- [ ] Tested with real usage scenarios
- [ ] Team feedback incorporated
