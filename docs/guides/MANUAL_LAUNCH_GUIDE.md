# Manual Launch Guide - Pharmaceutical Test Generation System

**Created**: 2025-08-28  
**Purpose**: Step-by-step instructions for manually launching the test generation workflow and ChromaDB ingestion

---

## 🚀 Quick Launch (5 minutes)

### Prerequisites Check
```bash
# 1. Navigate to main directory
cd C:\Users\anteb\Desktop\Courses\Projects\thesis_project\main

# 2. Verify Phoenix is running
docker ps | grep phoenix
# Expected: phoenix-server container running on port 6006

# 3. Check API keys are loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv('../.env'); print('APIs ready:', bool(os.getenv('OPENAI_API_KEY')) and bool(os.getenv('OPENROUTER_API_KEY')))"
```

### Launch Workflow
```bash
# Set encoding for Windows
set PYTHONIOENCODING=utf-8

# Run the clean demo script (with 8-minute timeout)
python run_demo_clean.py

# OR run main.py directly with specific file
python main.py "C:\Users\anteb\Desktop\Courses\Projects\thesis_project\datasets\urs_corpus\category_3\URS-001.md" --verbose

# OR for quick categorization-only test (5 seconds)
python main.py datasets\urs_corpus\category_3\URS-001.md --categorization-only
```

---

## 📍 WHERE TO FIND ALL TRACES AND LOGS

### 1. **Phoenix Traces** (Primary Observability)
```
main\logs\traces\
├── all_spans_YYYYMMDD_HHMMSS.jsonl        # Complete span data (60-200 spans)
├── chromadb_spans_YYYYMMDD_HHMMSS.jsonl   # Vector DB operations (20-30 spans)
├── trace_YYYYMMDD_HHMMSS.jsonl            # Workflow events
└── backup_YYYYMMDD\                       # Previous runs backup
```

**Phoenix UI Access**: http://localhost:6006
- Real-time trace visualization
- Performance metrics dashboard
- Span search and filtering

### 2. **Audit Logs** (Regulatory Compliance)
```
main\logs\audit\
├── gamp5_audit_YYYYMMDD_001.jsonl         # GAMP-5 compliance trail
└── backup_YYYYMMDD.jsonl                  # Previous audit backups
```

**Contains**:
- GAMP categorization decisions
- Regulatory compliance checkpoints
- Data integrity hashes (ALCOA+)
- 21 CFR Part 11 signatures

### 3. **Comprehensive Audit** (Detailed Tracking)
```
main\logs\comprehensive_audit\
└── comprehensive_audit_YYYYMMDD_*.jsonl   # Detailed workflow audits
```

### 4. **Event Logs** (System Events)
```
main\logs\events\
├── pharma_events.log                      # Application events
└── streams\                               # Event streams directory
```

### 5. **Test Output** (Generated Results)
```
main\output\test_suites\
└── test_suite_OQ-SUITE-XXXX_YYYYMMDD_HHMMSS.json
```

**Test Suite Contains**:
- 10-30 OQ test cases
- GAMP category classification
- Test metadata and requirements
- Regulatory compliance flags

### 6. **UI Export Traces** (Phoenix Export)
```
logs\traces\demonstration.csv              # UI-exported trace data
```

---

## 💾 CHROMADB INGESTION GUIDE

### Check Existing ChromaDB Content
```python
# Python script to check ChromaDB
import chromadb
from pathlib import Path

# Connect to ChromaDB
persist_dir = Path("C:/Users/anteb/Desktop/Courses/Projects/thesis_project/main/chroma_db")
client = chromadb.PersistentClient(path=str(persist_dir))

# List collections
collections = client.list_collections()
print(f"Collections: {[c.name for c in collections]}")

# Check document count
for collection in collections:
    col = client.get_collection(collection.name)
    count = col.count()
    print(f"{collection.name}: {count} documents")
```

### Manual Document Ingestion
```python
# Run ingestion script
cd C:\Users\anteb\Desktop\Courses\Projects\thesis_project\main

# Ingest regulatory documents
python run_ingestion.py

# OR use the ingestion module directly
python -m src.rag.ingestion_pipeline
```

### Ingestion Input Documents
```
main\test_generation\examples\thesis_text\
├── ISPE - GAMP 5_ A Risk-Based Approach to Compliant GxP Computerized_short.md
├── FDA Part-11--Electronic-Records--Electronic-Signatures---Scope-and-Application-(PDF).md
└── [other regulatory documents]
```

### Verify Ingestion Success
```bash
# Check ChromaDB directory size
dir C:\Users\anteb\Desktop\Courses\Projects\thesis_project\main\chroma_db

# Expected: 15-20 chunks for standard documents
# Collection: pharmaceutical_regulations
```

---

## 🔍 TRACE ANALYSIS COMMANDS

### Count Spans in Trace Files
```bash
# PowerShell command
Get-Content main\logs\traces\all_spans_*.jsonl | Measure-Object -Line

# Or using Python
python -c "sum(1 for _ in open('main/logs/traces/all_spans_20250828_124456.jsonl'))"
```

### Extract Key Metrics
```python
import json

# Read trace file
with open('main/logs/traces/all_spans_20250828_124456.jsonl', 'r') as f:
    spans = [json.loads(line) for line in f]

# Analyze
print(f"Total spans: {len(spans)}")
print(f"Unique operations: {len(set(s.get('name', '') for s in spans))}")
print(f"Total duration: {sum(s.get('duration_ns', 0) for s in spans) / 1e9:.2f}s")
```

### Find Errors in Traces
```bash
# Search for errors
findstr /i "error fail 401" main\logs\traces\*.jsonl

# Or with grep (if available)
grep -i "error\|fail\|401" main/logs/traces/*.jsonl
```

---

## 📊 MONITORING WITH PHOENIX

### Access Phoenix UI
1. Open browser: http://localhost:6006
2. Navigate to "Traces" tab
3. Filter by date/time of your run
4. Click on traces to see span details

### Export Traces from UI
1. Select traces in Phoenix UI
2. Click "Export" button
3. Choose CSV or JSON format
4. Save to `logs\traces\` directory

### Phoenix Docker Commands
```bash
# Check Phoenix status
docker ps | grep phoenix

# View Phoenix logs
docker logs phoenix-server --tail 100

# Restart Phoenix if needed
docker restart phoenix-server

# Stop Phoenix
docker stop phoenix-server

# Start Phoenix
docker start phoenix-server
```

---

## 🎯 EXPECTED OUTPUTS

### Successful Run Metrics
- **Execution Time**: 5-8 minutes
- **Test Cases Generated**: 10-30 OQ tests
- **Spans Captured**: 60-200 traces
- **ChromaDB Operations**: 20-30 queries
- **Audit Entries**: 500+ compliance records

### Output File Sizes
- Test Suite JSON: 20-50 KB
- All Spans JSONL: 100-500 KB
- Audit Log: 50-200 KB
- ChromaDB Spans: 20-100 KB

### Key Success Indicators
✅ Test suite file created in `output\test_suites\`  
✅ Trace files in `logs\traces\` with current timestamp  
✅ No Python errors in console output  
✅ Phoenix shows new traces at http://localhost:6006  
✅ GAMP Category 3 identified for URS-001.md  

---

## 🛠️ TROUBLESHOOTING

### Issue: Unicode/Encoding Errors
```bash
# Solution: Set encoding before running
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=0
```

### Issue: OpenRouter 401 Error
```bash
# Check API key is set
echo %OPENROUTER_API_KEY%

# Verify in .env file
type ..\\.env | findstr OPENROUTER
```

### Issue: Phoenix Not Accessible
```bash
# Restart Phoenix container
docker restart phoenix-server

# Check port availability
netstat -an | findstr 6006
```

### Issue: No Test Suite Generated
1. Check timeout wasn't too short (use 8+ minutes)
2. Verify API keys are valid
3. Check logs/traces for specific errors
4. Try categorization-only mode first

### Issue: ChromaDB Empty
```bash
# Re-run ingestion
python run_ingestion.py

# Check ChromaDB persistence directory
dir main\chroma_db /s
```

---

## 📝 VALIDATION CHECKLIST

Before viva demonstration:

- [ ] Phoenix container running (`docker ps`)
- [ ] API keys loaded (`.env` file present)
- [ ] ChromaDB has 15+ chunks ingested
- [ ] Previous traces backed up or cleared
- [ ] Windows encoding set (`PYTHONIOENCODING=utf-8`)
- [ ] Test with categorization-only first
- [ ] Phoenix UI accessible at http://localhost:6006

After execution:

- [ ] Test suite generated in `output\test_suites\`
- [ ] Trace files created in `logs\traces\`
- [ ] Audit log updated in `logs\audit\`
- [ ] Phoenix shows new traces
- [ ] No critical errors in console

---

## 📞 QUICK REFERENCE

### Essential Paths
```
Project Root: C:\Users\anteb\Desktop\Courses\Projects\thesis_project\
Main App: C:\Users\anteb\Desktop\Courses\Projects\thesis_project\main\
Traces: main\logs\traces\
Test Output: main\output\test_suites\
ChromaDB: main\chroma_db\
Phoenix UI: http://localhost:6006
```

### Key Commands
```bash
# Launch workflow
python run_demo_clean.py

# Quick test
python main.py datasets\urs_corpus\category_3\URS-001.md --categorization-only

# Check traces
dir main\logs\traces\*.jsonl

# View Phoenix
start http://localhost:6006
```

### Critical Files
- Input URS: `datasets\urs_corpus\category_3\URS-001.md`
- Latest test suite: `output\test_suites\test_suite_OQ-SUITE-*_20*.json`
- Today's traces: `logs\traces\*_20250828_*.jsonl`
- Audit log: `logs\audit\gamp5_audit_20250828_001.jsonl`

---

**END OF MANUAL LAUNCH GUIDE**

For additional support, refer to:
- `main\docs\guides\QUICK_START_GUIDE.md`
- `main\docs\guides\PHOENIX_OBSERVABILITY_GUIDE.md`
- `viva_preparation\DEMO_LAUNCH_GUIDE.md`