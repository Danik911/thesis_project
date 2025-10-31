# 🧹 Comprehensive Cleanup Analysis
**Date**: 2025-10-31
**Status**: Ready for execution (NOT started yet)

## 📊 Current State Summary

- **Total Size**: ~900MB
- **Main Folder**: 601MB (67% of project)
- **Redundant Files**: ~80% of main/*.py files
- **Cleanup Plan Found**: `/main/docs/guides/PROJECT_CORE_FILES_SCHEME.md`
- **Cleanup Executed**: ❌ NO - All redundant files still present

---

## 🔍 TOP-LEVEL ANALYSIS (Folder by Folder)

### 📁 ROOT FILES

| File | Size | Status | Recommendation |
|------|------|--------|----------------|
| `=2.0.0` | 27K | ❓ Unknown | **DELETE** - Appears to be a corrupt/misnamed file |
| `.claude.json` | 121K | ✅ Config | **KEEP** - Claude Code configuration |
| `.env.example` | 1.9K | ✅ Config | **KEEP** - Environment template |
| `.env.oss_testing` | 6.1K | 🟡 Testing | **REVIEW** - May be redundant with .env.example |
| `.gitignore` | 4.5K | ✅ Config | **KEEP** - Git configuration |
| `.mcp.json` | 1.8K | ✅ Config | **KEEP** - MCP configuration |
| `.python-version` | 4B | ✅ Config | **KEEP** - Python version |
| `CLAUDE.md` | 8.4K | ✅ Docs | **KEEP** - Project instructions |
| `CONSULTATION_BYPASS_FIX_SUMMARY.md` | 4.6K | 🟡 Docs | **MOVE** to `docs_archive/` - Historical |
| `LICENSE` | 12K | ✅ Legal | **KEEP** - Required |
| `README.md` | 18K | ✅ Docs | **KEEP** - Essential |
| `TECHNICAL_ARCHITECTURE_REPORT.md` | 23K | 🟡 Docs | **MOVE** to `main/docs/` |
| `check_current_state.py` | 1.9K | 🔴 Debug | **DELETE** - Utility script |
| `generate_compliance_dashboard.py` | 29K | 🟡 Tool | **MOVE** to `main/tools/` or DELETE if unused |
| `generate_compliance_dashboard_simple.py` | 28K | 🔴 Duplicate | **DELETE** - Duplicate of above |
| `install_phoenix_deps.sh` | 1.1K | 🟡 Setup | **MOVE** to `main/scripts/` |
| `package.json` | 56B | ❓ Empty | **DELETE** - Nearly empty, not used |
| `package-lock.json` | 39K | ❓ Node | **DELETE** - Not a Node.js project |
| `phoenix_launcher.py` | 1.9K | 🟡 Tool | **MOVE** to `main/tools/` |
| `phoenix_main.html` | 2.7K | 🟡 Viz | **MOVE** to `test_visualizations/` |
| `phoenix_trace_analyzer.py` | 31K | 🟡 Tool | **MOVE** to `main/tools/` |
| `phoenix_traces.json` | 113B | 🔴 Data | **DELETE** - Generated file |
| `pyproject.toml` | 3.2K | ✅ Config | **KEEP** - Python project config |
| `requirements.txt` | 431B | 🟡 Config | **KEEP** (but prefer uv.lock) |
| `requirements_compatible.txt` | 957B | 🔴 Redundant | **DELETE** - Use uv.lock |
| `uv.lock` | 678K | ✅ Config | **KEEP** - Main dependency lock |

**Summary**:
- ✅ KEEP: 10 files
- 🟡 MOVE/REVIEW: 9 files
- 🔴 DELETE: 6 files

---

### 📁 ROOT DIRECTORIES

#### `.claude/`
**Status**: ✅ **KEEP**
**Purpose**: Claude Code agent configurations
**Action**: None

#### `.git/`
**Status**: ✅ **KEEP**
**Purpose**: Git version control
**Action**: None

#### `.serena/`
**Status**: ✅ **KEEP**
**Purpose**: Serena MCP memory
**Action**: None

#### `.taskmaster/`
**Status**: ✅ **KEEP**
**Purpose**: Task-Master AI project management
**Action**: None

---

#### `PRPs/` (33K)
**Status**: 🟡 **REVIEW**
**Purpose**: Problem Requirements Prompts
**Analysis Needed**: Check if still referenced
**Recommendation**: MOVE to `archive/PRPs/` if not actively used

#### `THESIS_EVIDENCE_PACKAGE/` (107MB)
**Status**: ✅ **KEEP**
**Purpose**: Final thesis submission evidence
**Action**: None - Critical for thesis

#### `archive/` (9.9MB)
**Status**: ✅ **KEEP**
**Purpose**: Historical records
**Action**: Good organization, keep as-is

#### `augmentation/` (15K)
**Status**: 🔴 **DELETE** or REVIEW
**Purpose**: Unknown
**Recommendation**: Check contents, likely deletable

#### `chroma_db/` (60MB)
**Status**: ✅ **KEEP**
**Purpose**: Vector database for RAG
**Action**: None - Required for system

#### `compliance/` (35K)
**Status**: 🟡 **REVIEW**
**Purpose**: Compliance files
**Recommendation**: Check if duplicated in THESIS_EVIDENCE_PACKAGE

#### `datasets/` (292K)
**Status**: ✅ **KEEP**
**Purpose**: URS corpus for testing
**Action**: None - Required for validation

#### `docs_archive/` (177K)
**Status**: ✅ **KEEP**
**Purpose**: Archived documentation
**Action**: Good organization

#### `logs/` (92K)
**Status**: 🔴 **CLEANUP**
**Purpose**: Runtime logs
**Recommendation**: DELETE old logs, keep only recent

#### `main/` (601MB) 🚨
**Status**: 🔴 **CRITICAL CLEANUP NEEDED**
**Purpose**: Main application code
**Action**: See detailed analysis below

#### `output/` (308K)
**Status**: 🟡 **CLEANUP**
**Purpose**: Generated outputs
**Recommendation**: DELETE old runs, keep only latest validation results

#### `run/` (594K)
**Status**: 🔴 **DELETE**
**Purpose**: Runtime files
**Recommendation**: Generated files, should be in .gitignore

#### `test_visualizations/` (8.9MB)
**Status**: 🟡 **REVIEW**
**Purpose**: Test visualization outputs
**Recommendation**: Keep representative samples, delete rest

#### `thesis_visualizations/` (108MB)
**Status**: ✅ **KEEP**
**Purpose**: Final thesis figures
**Action**: None - Critical for thesis

#### `viva_preparation/` (28K)
**Status**: ✅ **KEEP**
**Purpose**: Thesis defense preparation
**Action**: None

---

## 🚨 CRITICAL: main/ FOLDER CLEANUP (601MB)

### Current State in main/:
- **110 Python files** total
- **67 files** are debug/test/utility scripts (61%!)
- **Target**: Reduce to ~20 core files + organized tests

### Files to DELETE from main/:

#### Debug Files (All DELETE):
```bash
debug_*.py              # All debug scripts (10+ files)
test_*.py               # All test scripts in root (20+ files)
analyze_*.py            # All analysis scripts
create_sample_*.py      # All sample creation scripts
minimal_*.py            # All minimal test scripts
focused_*.py            # All focused test scripts
```

#### Other Redundant Files:
- `main.py.backup` (if exists)
- `ingest_chromadb.backup.py` (if exists)
- Any `*.pyc` files
- Any `__pycache__/` directories

### main/src/ Cleanup:

#### Files to DELETE:
```
src/core/
├── unified_workflow_backup.py      ❌ DELETE
├── unified_workflow_original.py    ❌ DELETE
└── categorization_workflow.py      ❌ DELETE

src/agents/oq_generator/
├── generator_v2.py                 ❌ DELETE (use generator.py)
├── chunked_generator.py            ❌ DELETE
└── workflow.py                     ❌ DELETE

src/agents/parallel/
├── context_provider.py.backup      ❌ DELETE
└── agent_factory.py                ❌ DELETE

src/agents/planner/                 ❌ DELETE ENTIRE FOLDER
├── agent.py
├── coordination.py
├── gamp_strategies.py
├── strategy_generator.py
└── workflow.py

src/monitoring/
├── phoenix_enhanced.py             ❌ DELETE
├── phoenix_enhanced_broken.py      ❌ DELETE
├── phoenix_enhanced_old.py         ❌ DELETE
├── phoenix_event_handler.py        ❌ DELETE
├── pharmaceutical_event_handler.py ❌ DELETE
├── simple_tracer.py                ❌ DELETE
└── trace_config.py                 ❌ DELETE

src/config/
├── agent_llm_config.py             ❌ DELETE
└── timeout_config.py               ❌ DELETE

src/llms/
├── openrouter_llm.py               ❌ DELETE
├── cerebras_provider.py            ❌ DELETE
└── oss_provider_factory.py         ❌ DELETE

src/document_processing/            ❌ DELETE ENTIRE FOLDER
src/rag/                            ❌ DELETE ENTIRE FOLDER (empty)
src/security/                       ❌ DELETE ENTIRE FOLDER (empty)
src/validation/                     ❌ DELETE ENTIRE FOLDER (empty)
```

#### Directories to DELETE:
- `examples/` - Example files not needed

### Files to KEEP in main/:
```
main/
├── main.py                         ✅ KEEP - Entry point
├── ingest_chromadb.py              ✅ KEEP - Required setup
└── src/
    ├── core/
    │   ├── unified_workflow.py     ✅ KEEP - Master orchestrator
    │   ├── events.py               ✅ KEEP - Event definitions
    │   ├── human_consultation.py   ✅ KEEP - HITL
    │   └── event_logger.py         ✅ KEEP - Audit logging
    ├── agents/
    │   ├── categorization/
    │   │   └── agent.py            ✅ KEEP
    │   ├── oq_generator/
    │   │   ├── generator.py        ✅ KEEP (NOT generator_v2)
    │   │   ├── models.py           ✅ KEEP
    │   │   ├── templates.py        ✅ KEEP
    │   │   └── yaml_parser.py      ✅ KEEP
    │   └── parallel/
    │       ├── context_provider.py ✅ KEEP
    │       ├── research_agent.py   ✅ KEEP
    │       └── sme_agent.py        ✅ KEEP
    ├── config/
    │   └── llm_config.py           ✅ KEEP
    ├── llms/
    │   └── openrouter_compat.py    ✅ KEEP
    └── monitoring/
        ├── phoenix_config.py       ✅ KEEP
        └── custom_span_exporter.py ✅ KEEP
```

---

## 📋 CLEANUP EXECUTION PLAN

### Phase 1: Backup (CRITICAL - Do this first!)
```bash
# Create backup with timestamp
cd /home/user/thesis_project
tar -czf backup_before_cleanup_$(date +%Y%m%d_%H%M%S).tar.gz main/
mv backup_*.tar.gz ../
```

### Phase 2: Remove Root Level Files
```bash
cd /home/user/thesis_project

# Delete clearly redundant files
rm =2.0.0
rm package.json package-lock.json
rm requirements_compatible.txt
rm phoenix_traces.json
rm check_current_state.py
rm generate_compliance_dashboard_simple.py

# Move files to appropriate locations
mkdir -p main/tools main/scripts
mv generate_compliance_dashboard.py main/tools/
mv phoenix_launcher.py main/tools/
mv phoenix_trace_analyzer.py main/tools/
mv install_phoenix_deps.sh main/scripts/
mv TECHNICAL_ARCHITECTURE_REPORT.md main/docs/
mv CONSULTATION_BYPASS_FIX_SUMMARY.md docs_archive/
mv phoenix_main.html test_visualizations/
```

### Phase 3: Clean main/ Root
```bash
cd main

# Remove all debug/test/utility files
rm -f debug_*.py test_*.py analyze_*.py create_sample_*.py minimal_*.py focused_*.py

# Remove backup files
find . -name "*.backup" -delete
find . -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
```

### Phase 4: Clean main/src/
```bash
cd src

# Remove backup files
rm -f core/unified_workflow_backup.py
rm -f core/unified_workflow_original.py
rm -f core/categorization_workflow.py

# Remove old generator versions
rm -f agents/oq_generator/generator_v2.py
rm -f agents/oq_generator/chunked_generator.py
rm -f agents/oq_generator/workflow.py

# Remove parallel agent backups
rm -f agents/parallel/context_provider.py.backup
rm -f agents/parallel/agent_factory.py

# Remove entire planner folder (not used)
rm -rf agents/planner

# Remove old monitoring files
rm -f monitoring/phoenix_enhanced*.py
rm -f monitoring/phoenix_event_handler.py
rm -f monitoring/pharmaceutical_event_handler.py
rm -f monitoring/simple_tracer.py
rm -f monitoring/trace_config.py

# Remove old config files
rm -f config/agent_llm_config.py
rm -f config/timeout_config.py

# Remove old LLM files
rm -f llms/openrouter_llm.py
rm -f llms/cerebras_provider.py
rm -f llms/oss_provider_factory.py

# Remove entire unused folders
rm -rf document_processing rag security validation

# Remove examples
rm -rf examples
```

### Phase 5: Clean Empty Directories
```bash
cd /home/user/thesis_project
find . -type d -empty -delete
```

### Phase 6: Clean Runtime/Generated Files
```bash
# Clean old logs (keep last 7 days)
find logs/ -name "*.log" -mtime +7 -delete

# Clean old output (keep only latest)
# MANUAL REVIEW RECOMMENDED - don't auto-delete
```

### Phase 7: Review Questionable Folders
```bash
# These need manual review:
# - augmentation/ - Check if used
# - compliance/ - Check for duplicates with THESIS_EVIDENCE_PACKAGE
# - run/ - Should be in .gitignore
```

---

## 🎯 EXPECTED RESULTS

### Before Cleanup:
- **Total files**: ~500+
- **Python files in main/**: 110
- **Redundant files**: ~80%
- **Size**: 900MB

### After Cleanup:
- **Total files**: ~100-150 (core + thesis package)
- **Python files in main/**: ~25 (20 core + 5 utilities)
- **Redundant files**: 0%
- **Size**: ~700MB (mostly thesis evidence + databases)

### Benefits:
1. ✅ **Clarity**: Easy to understand project structure
2. ✅ **Maintainability**: Clear which files are production vs. archive
3. ✅ **Thesis Documentation**: Clean codebase for submission
4. ✅ **Compliance**: Clear separation of code versions

---

## ⚠️ WARNINGS

1. **BACKUP FIRST**: Always create backup before deleting
2. **Test After**: Run tests after cleanup to ensure nothing broke
3. **Git Status**: Check git status - don't delete tracked files you need
4. **Manual Review**: Some files may have unexpected dependencies
5. **Incremental**: Do cleanup in phases, test between phases

---

## 🔍 VALIDATION CHECKLIST

After cleanup, verify:

- [ ] `main.py` still runs successfully
- [ ] Tests pass: `cd main && pytest tests/ -v`
- [ ] Git status clean (no accidental deletions)
- [ ] Documentation updated
- [ ] Backup created and verified
- [ ] Can regenerate OQ tests
- [ ] Phoenix monitoring works
- [ ] ChromaDB ingestion works

---

## 📝 NOTES

- Original cleanup plan: `/main/docs/guides/PROJECT_CORE_FILES_SCHEME.md`
- This analysis created: 2025-10-31
- **STATUS**: Ready for execution, awaiting user confirmation
- **RISK LEVEL**: Medium (with proper backup: Low)

