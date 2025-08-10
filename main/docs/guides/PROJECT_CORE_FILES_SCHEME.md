# Project Core Files Scheme - Clean Architecture

## 🎯 CORE FILES (Essential for Production)

### 1. **Entry Points**
```
main/
├── main.py                           # ✅ PRIMARY ENTRY POINT - launches workflow
├── ingest_chromadb.py               # ✅ REQUIRED - ingests regulatory documents
└── src/
```

### 2. **Core Workflow Orchestration**
```
main/src/core/
├── unified_workflow.py              # ✅ MASTER ORCHESTRATOR - coordinates all agents
├── events.py                        # ✅ Event definitions for workflow communication
├── human_consultation.py            # ✅ Human-in-the-loop handling
└── event_logger.py                  # ✅ Audit trail logging
```

### 3. **Agent Implementations (All Essential)**
```
main/src/agents/
├── categorization/
│   └── agent.py                     # ✅ GAMP-5 categorization logic
├── oq_generator/
│   ├── generator.py                 # ✅ Main OQ test generator
│   ├── models.py                    # ✅ Pydantic models for validation
│   ├── templates.py                 # ✅ Prompt templates
│   └── yaml_parser.py               # ✅ YAML parsing with field fixes
├── parallel/
│   ├── context_provider.py         # ✅ ChromaDB integration
│   ├── research_agent.py           # ✅ Research capabilities
│   └── sme_agent.py                # ✅ SME validation
```

### 4. **Configuration**
```
main/src/config/
└── llm_config.py                    # ✅ DeepSeek V3 configuration
```

### 5. **LLM Integration**
```
main/src/llms/
└── openrouter_compat.py            # ✅ OpenRouter/DeepSeek integration
```

### 6. **Monitoring**
```
main/src/monitoring/
├── phoenix_config.py                # ✅ Phoenix setup
└── custom_span_exporter.py         # ✅ Custom span export for ChromaDB
```

---

## 🗑️ REDUNDANT/BACKUP FILES (Can be Removed)

### 1. **Duplicate Workflows**
```
main/src/core/
├── unified_workflow_backup.py      # ❌ REDUNDANT - old backup
├── unified_workflow_original.py    # ❌ REDUNDANT - original version
└── categorization_workflow.py      # ❌ REDUNDANT - merged into unified
```

### 2. **Old Implementations**
```
main/src/agents/oq_generator/
├── generator_v2.py                 # ❌ REDUNDANT - old version
├── chunked_generator.py            # ❌ REDUNDANT - not used
└── workflow.py                     # ❌ REDUNDANT - old workflow pattern

main/src/agents/parallel/
├── context_provider.py.backup      # ❌ REDUNDANT - backup file
└── agent_factory.py                # ❌ REDUNDANT - not used

main/src/agents/planner/            # ❌ ENTIRE FOLDER - planner not used
├── agent.py
├── coordination.py
├── gamp_strategies.py
├── strategy_generator.py
└── workflow.py
```

### 3. **Deprecated Monitoring**
```
main/src/monitoring/
├── phoenix_enhanced.py             # ❌ REDUNDANT - old version
├── phoenix_enhanced_broken.py      # ❌ REDUNDANT - broken version
├── phoenix_enhanced_old.py         # ❌ REDUNDANT - old version
├── phoenix_event_handler.py        # ❌ REDUNDANT - replaced by custom exporter
├── pharmaceutical_event_handler.py # ❌ REDUNDANT - not used
├── simple_tracer.py               # ❌ REDUNDANT - replaced
└── trace_config.py                # ❌ REDUNDANT - consolidated
```

### 4. **Unused Utilities**
```
main/src/
├── document_processing/            # ❌ ENTIRE FOLDER - not used in production
├── rag/                           # ❌ EMPTY FOLDER
├── security/                      # ❌ EMPTY FOLDER
├── validation/                    # ❌ EMPTY FOLDER
├── shared/                        # ❌ MOSTLY REDUNDANT (except utils.py)
```

### 5. **Test/Debug Files in Main**
```
main/
├── debug_*.py                     # ❌ ALL debug files - 10+ files
├── test_*.py                      # ❌ ALL test files in main - 20+ files
├── analyze_*.py                   # ❌ Analysis scripts
├── create_sample_*.py             # ❌ Sample creation scripts
├── minimal_*.py                   # ❌ Minimal test scripts
├── focused_*.py                   # ❌ Focused test scripts
└── examples/                      # ❌ ENTIRE FOLDER - examples
```

### 6. **Old Configurations**
```
main/src/config/
├── agent_llm_config.py           # ❌ REDUNDANT - old agent-specific config
└── timeout_config.py              # ❌ REDUNDANT - timeouts in main config

main/src/llms/
├── openrouter_llm.py             # ❌ REDUNDANT - old implementation
├── cerebras_provider.py          # ❌ REDUNDANT - not used
└── oss_provider_factory.py       # ❌ REDUNDANT - not used
```

---

## 📁 CLEAN PROJECT STRUCTURE (After Cleanup)

```
thesis_project/
├── main/
│   ├── main.py                          # Entry point
│   ├── ingest_chromadb.py              # ChromaDB ingestion
│   ├── src/
│   │   ├── core/
│   │   │   ├── unified_workflow.py     # Master orchestrator
│   │   │   ├── events.py               # Event definitions
│   │   │   ├── human_consultation.py   # Human oversight
│   │   │   └── event_logger.py         # Audit logging
│   │   ├── agents/
│   │   │   ├── categorization/
│   │   │   │   └── agent.py            # GAMP-5 categorizer
│   │   │   ├── oq_generator/
│   │   │   │   ├── generator.py        # OQ generator
│   │   │   │   ├── models.py           # Data models
│   │   │   │   ├── templates.py        # Prompts
│   │   │   │   └── yaml_parser.py      # YAML parsing
│   │   │   └── parallel/
│   │   │       ├── context_provider.py # ChromaDB RAG
│   │   │       ├── research_agent.py   # Research
│   │   │       └── sme_agent.py        # SME validation
│   │   ├── config/
│   │   │   └── llm_config.py          # DeepSeek V3 config
│   │   ├── llms/
│   │   │   └── openrouter_compat.py   # OpenRouter integration
│   │   └── monitoring/
│   │       ├── phoenix_config.py       # Phoenix setup
│   │       └── custom_span_exporter.py # Span export
│   ├── tests/                          # Test files (keep separate)
│   ├── output/                         # Generated outputs
│   └── chroma_db/                      # Vector database
├── docs/                               # Documentation
└── .env                                # API keys
```

---

## 🔧 CLEANUP COMMANDS

To clean up redundant files safely:

```bash
# 1. Backup first
cp -r main main_backup_$(date +%Y%m%d)

# 2. Remove debug/test files from main
cd main
rm -f debug_*.py test_*.py analyze_*.py create_sample_*.py minimal_*.py focused_*.py

# 3. Remove backup files
find . -name "*.backup" -delete
find . -name "*_backup.py" -delete
find . -name "*_original.py" -delete
find . -name "*_old.py" -delete
find . -name "*_broken.py" -delete

# 4. Remove empty directories
find . -type d -empty -delete

# 5. Remove entire unused directories
rm -rf src/document_processing
rm -rf src/agents/planner
rm -rf src/rag src/security src/validation
rm -rf examples
```

---

## ✅ FILES TO DEFINITELY KEEP

1. **main.py** - Entry point
2. **ingest_chromadb.py** - Required for setup
3. **src/core/unified_workflow.py** - Main orchestrator
4. **src/agents/categorization/agent.py** - GAMP categorization
5. **src/agents/oq_generator/generator.py** - Test generation
6. **src/agents/oq_generator/yaml_parser.py** - YAML parsing fixes
7. **src/agents/parallel/context_provider.py** - ChromaDB RAG
8. **src/config/llm_config.py** - DeepSeek configuration
9. **src/llms/openrouter_compat.py** - OpenRouter integration
10. **src/monitoring/custom_span_exporter.py** - Phoenix monitoring

---

## 📊 Impact Analysis

**Current State**: ~100+ Python files with many duplicates
**After Cleanup**: ~20 core files + test suite
**Size Reduction**: ~80% fewer files
**Clarity Improvement**: 100% - clear single-purpose files

This cleanup will make the codebase much clearer for thesis documentation and future maintenance.