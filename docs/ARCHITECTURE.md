# System Architecture

Multi-agent LLM system for pharmaceutical test generation with GAMP-5 compliance.

## High-Level Architecture

```mermaid
graph TD
    URS[URS Document] --> CAT[GAMP-5 Categorization Agent]
    CAT --> CTX[Context Provider Agent]
    CAT --> RES[Research Agent]
    CAT --> SME[SME Agent]
    CTX --> OQ[OQ Generator Agent]
    RES --> OQ
    SME --> OQ
    OQ --> TS[Test Suite]
    TS --> LF[LangFuse Cloud Tracing]
```

## Core Agents

### GAMP-5 Categorization Agent

Determines software category per ISPE GAMP-5 guidelines:

```python
# main/src/agents/categorization/agent.py
class GAMPCategorizationWorkflow(Workflow):
    @step
    @observe(name="gamp_categorization")
    async def categorize(self, ctx: Context, ev: StartEvent) -> StopEvent:
        indicators = self._extract_gamp_indicators(ev.urs_content)
        response = await self.llm.astructured_predict(
            output_cls=GAMPCategoryOutput,
            prompt=self._build_categorization_prompt(indicators),
            temperature=0.1
        )

        # NO FALLBACKS - explicit failure on low confidence
        if response.confidence < 0.8:
            raise HumanConsultationRequiredEvent(
                reason=f"Low confidence: {response.confidence}",
                suggested_category=response.category
            )
        return StopEvent(result=response)
```

### Context Provider (ChromaDB RAG)

Retrieves regulatory context from 26 indexed pharmaceutical documents:

```python
# main/src/agents/parallel/context_provider.py
class ContextProviderAgent:
    def __init__(self):
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.chroma_client.get_collection("pharmaceutical_regulations")

    async def get_regulatory_context(
        self, urs_content: str, gamp_category: GAMPCategory
    ) -> RegulatoryContext:
        query_embedding = self.embed_model.get_text_embedding(urs_content)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=10,
            where={"category": gamp_category.value}
        )
        return RegulatoryContext(
            gamp_requirements=self._extract_gamp_requirements(results),
            cfr_requirements=self._extract_cfr_requirements(results),
            alcoa_principles=self._map_alcoa_principles(results)
        )
```

### OQ Test Generator

Generates test suites using DeepSeek V3 via OpenRouter:

```python
# main/src/agents/oq_generator/generator.py
class OQTestGenerator:
    def __init__(self, llm: LLM):
        self.llm = llm  # DeepSeek V3 via OpenRouter
        self.yaml_parser = EnhancedYAMLParser()

    @observe(name="oq_test_generation")
    async def generate_oq_test_suite(
        self, gamp_category: GAMPCategory,
        urs_content: str, context_data: Dict, config: OQGenerationConfig
    ) -> OQTestSuite:
        prompt = self._build_generation_prompt(
            urs_content=urs_content,
            gamp_category=gamp_category,
            regulatory_context=context_data.get("regulatory_context"),
            target_count=config.target_test_count
        )
        response = await self.llm.acomplete(prompt, temperature=0.1, max_tokens=30000)
        test_suite = self.yaml_parser.parse_and_validate(response.text)
        self._validate_alcoa_compliance(test_suite)
        return test_suite
```

---

## Compliance Implementation

### ALCOA+ Validation

```python
# main/src/validation/alcoa_validator.py
class ALCOAPlusValidator:
    PRINCIPLES = {
        "Attributable": self._validate_attribution,
        "Legible": self._validate_legibility,
        "Contemporaneous": self._validate_contemporaneous,
        "Original": self._validate_originality,
        "Accurate": self._validate_accuracy,
        "Complete": self._validate_completeness,
        "Consistent": self._validate_consistency,
        "Enduring": self._validate_enduring,
        "Available": self._validate_availability
    }

    @observe(name="alcoa_validation")
    def validate_test_suite(self, suite: OQTestSuite) -> ValidationResult:
        for principle, validator in self.PRINCIPLES.items():
            result = validator(suite)
            if not result.passed:
                raise ALCOAViolationError(principle=principle, details=result.details)
        return ValidationResult(passed=True, principles=results)
```

### Traceability Matrix

```python
# main/src/validation/traceability.py
class TraceabilityMatrix:
    def build_matrix(
        self, urs_requirements: List[Requirement], test_cases: List[OQTestCase]
    ) -> pd.DataFrame:
        matrix = pd.DataFrame(
            index=[req.id for req in urs_requirements],
            columns=[test.test_id for test in test_cases]
        )
        for req in urs_requirements:
            for test in test_cases:
                similarity = self._calculate_similarity(req.description, test.objective)
                if similarity > 0.85:
                    matrix.loc[req.id, test.test_id] = 1
        return matrix
```

---

## Security Implementation

### OWASP LLM Top 10 Validation

```python
# main/src/security/owasp_validator.py
class OWASPLLMValidator:
    def validate_generated_tests(self, test_suite: OQTestSuite) -> SecurityReport:
        vulnerabilities = []

        # LLM01: Prompt Injection Prevention
        if self._detect_prompt_injection(test_suite):
            vulnerabilities.append(VulnerabilityReport(risk="LLM01", severity="HIGH"))

        # LLM06: Insecure Output Handling
        for test in test_suite.test_cases:
            insecure_patterns = self._scan_insecure_patterns(test.test_steps)
            if insecure_patterns:
                vulnerabilities.append(VulnerabilityReport(risk="LLM06", severity="MEDIUM"))

        return SecurityReport(vulnerabilities=vulnerabilities)
```

---

## LangFuse Observability

### Automatic Tracing

```python
# main/api/observability.py
from langfuse import Langfuse
from langfuse.decorators import observe, langfuse_context

langfuse_client = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
)

@observe(name="unified_workflow_execution")
async def execute_unified_workflow(urs_content: str, job_id: str):
    langfuse_context.update_current_trace(
        name="pharmaceutical_test_generation",
        user_id=job_id,
        tags=["pharmaceutical", "gamp5", "oq_generation"],
        metadata={"framework": "GAMP-5", "regulatory_standard": "21 CFR Part 11"}
    )
    workflow = UnifiedTestGenerationWorkflow()
    return await workflow.run(urs_content=urs_content)
```

### Audit Trail Generation

```python
# main/src/compliance/audit_trail.py
@observe(name="audit_trail_generation")
def generate_alcoa_audit_trail(job_id: str, workflow_result: dict) -> dict:
    return {
        "job_id": job_id,
        "timestamp": datetime.now().isoformat(),
        "trace_id": langfuse_context.get_current_trace_id(),
        "compliance_metadata": {
            "gamp_category": workflow_result.get("gamp_category"),
            "alcoa_validated": True,
            "cfr_part11_compliant": True
        }
    }
```

---

## AI4LIMS PoC Architecture

**Branch**: `prjoject_p_protatype` | **Routes**: `/lims/*` | **Collection**: `mda_templates`

AI4LIMS is a proof-of-concept LIMS integration that demonstrates automated Master Data Assurance (MDA) generation from PDF equipment documentation. The system implements a human-in-the-loop (HITL) workflow with mandatory approval before export.

### State Machine

The AI4LIMS workflow follows a strict linear state progression:

```
IDLE → EXTRACTING → GENERATING → PENDING_REVIEW → APPROVED → EXPORTED
           ↓             ↓              ↓            ↓
         FAILED       FAILED         FAILED       FAILED
```

**State Definitions:**

| State | Description | Next States |
|-------|-------------|-------------|
| `IDLE` | Initial state, no job active | `EXTRACTING` |
| `EXTRACTING` | LlamaExtract processing PDF | `GENERATING`, `FAILED` |
| `GENERATING` | RAG-enhanced MDA generation | `PENDING_REVIEW`, `FAILED` |
| `PENDING_REVIEW` | Human review required (HITL gate) | `APPROVED`, `FAILED` |
| `APPROVED` | Human approved MDA | `EXPORTED` |
| `EXPORTED` | XLSX file downloaded | `IDLE` |
| `FAILED` | Error occurred at any stage | `IDLE` |

**No bypass path exists** — human approval via `PENDING_REVIEW` is mandatory before export.

### Backend Components

#### 1. PDF Extraction (LlamaExtract)

```python
# main/src/lims/extractor.py
class LlamaExtractClient:
    def __init__(self):
        self.client = LlamaExtract(api_key=os.getenv("LLAMA_CLOUD_API_KEY"))
        self.schema = MDAExtractionSchema()  # 28 fields

    @observe(name="llamaextract_pdf_extraction")
    async def extract_from_pdf(self, pdf_path: str, job_id: str) -> ExtractedData:
        extraction_schema = self.schema.to_llamaextract_schema()
        result = await self.client.aextract(
            schema=extraction_schema,
            files=[pdf_path]
        )
        # NO FALLBACKS - fail if extraction confidence < 0.7
        if result.confidence < 0.7:
            raise ExtractionConfidenceError(
                f"Low extraction confidence: {result.confidence}"
            )
        return ExtractedData(
            equipment_name=result.equipment_name,
            manufacturer=result.manufacturer,
            model_number=result.model_number,
            # ... 25 more fields
        )
```

#### 2. RAG-Enhanced MDA Generation

```python
# main/src/lims/mda_generator.py
class MDAGenerator:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="openai/gpt-5",  # via OpenRouter
            api_key=os.getenv("OPENROUTER_API_KEY"),
            temperature=0.1
        )
        self.rag_engine = self._init_chromadb_rag()

    def _init_chromadb_rag(self):
        chroma_client = chromadb.PersistentClient(path="./chroma_db")
        collection = chroma_client.get_collection("mda_templates")
        return ChromaVectorStore(chroma_collection=collection)

    @observe(name="lims_mda_generation")
    async def generate_mda(
        self, extracted_data: ExtractedData, job_id: str
    ) -> MDARecord:
        # RAG: Retrieve top 5 similar templates
        query_embedding = self._embed(extracted_data.equipment_name)
        template_docs = self.rag_engine.query(
            query_embeddings=[query_embedding],
            n_results=5
        )

        # Generate MDA using GPT-5 with RAG context
        prompt = self._build_mda_prompt(extracted_data, template_docs)
        response = await self.llm.agenerate(prompt)

        return MDARecord(
            equipment_id=self._generate_equipment_id(),
            equipment_name=extracted_data.equipment_name,
            test_cases=self._parse_test_cases(response.text),
            # ... 90 total fields across 4 sheets
        )
```

#### 3. Chat Agent for HITL Refinement

```python
# main/src/lims/chat_agent.py
class LIMSChatAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="anthropic/claude-opus-4.6",  # via OpenRouter
            temperature=0.2
        )
        self.job_store = JobStore()

    @observe(name="lims_chat_interaction")
    async def handle_chat_message(
        self, job_id: str, user_message: str
    ) -> ChatResponse:
        job = self.job_store.get_job(job_id)
        if job.state != JobState.PENDING_REVIEW:
            raise InvalidStateError("Chat only available during review")

        mda_context = job.result.get("mda_record")
        prompt = self._build_chat_prompt(user_message, mda_context)
        response = await self.llm.agenerate(prompt)

        # Parse response for edits
        edits = self._extract_cell_edits(response.text)
        if edits:
            # Store suggested edits in job metadata
            job.metadata["suggested_edits"] = edits

        return ChatResponse(
            message=response.text,
            suggested_edits=edits
        )

    def apply_chat_edit(
        self, job_id: str, edit_id: str, action: Literal["apply", "reject"]
    ):
        job = self.job_store.get_job(job_id)
        if action == "apply":
            # Apply edit to MDA record
            self._update_mda_cell(job, edit_id)
        # Track edit decision in audit trail
        job.metadata["edit_history"].append({
            "edit_id": edit_id,
            "action": action,
            "timestamp": datetime.now().isoformat()
        })
```

#### 4. XLSX Export (4-Sheet Format)

```python
# main/src/lims/xlsx_exporter.py
class XLSXExporter:
    SHEETS = ["Equipment Info", "Test Cases", "Validation Matrix", "Audit Trail"]

    @observe(name="lims_xlsx_export")
    def export_mda_to_xlsx(self, mda_record: MDARecord, job_id: str) -> BytesIO:
        wb = openpyxl.Workbook()

        # Sheet 1: Equipment Info (28 fields)
        self._write_equipment_info(wb, mda_record)

        # Sheet 2: Test Cases (62 fields)
        self._write_test_cases(wb, mda_record.test_cases)

        # Sheet 3: Validation Matrix (traceability)
        self._write_validation_matrix(wb, mda_record)

        # Sheet 4: Audit Trail (ALCOA+ compliance)
        self._write_audit_trail(wb, job_id)

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer
```

#### 5. Job State Management

```python
# main/src/lims/job_store.py
class JobStore:
    def __init__(self):
        self.jobs: Dict[str, LIMSJob] = {}

    def create_job(self, file_path: str) -> str:
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = LIMSJob(
            id=job_id,
            state=JobState.IDLE,
            file_path=file_path,
            created_at=datetime.now()
        )
        return job_id

    def transition_state(self, job_id: str, new_state: JobState):
        job = self.jobs[job_id]
        # Validate state transition
        if not self._is_valid_transition(job.state, new_state):
            raise InvalidStateTransitionError(
                f"Cannot transition from {job.state} to {new_state}"
            )
        job.state = new_state
        job.updated_at = datetime.now()

    def get_job(self, job_id: str) -> LIMSJob:
        if job_id not in self.jobs:
            raise JobNotFoundError(f"Job {job_id} not found")
        return self.jobs[job_id]
```

### Frontend Components

#### 1. LIMSStepIndicator

Visual pipeline stage indicator component:

```tsx
// main/frontend/components/lims/LIMSStepIndicator.tsx
const STEPS = [
  { key: "EXTRACTING", label: "Extracting" },
  { key: "GENERATING", label: "Generating" },
  { key: "PENDING_REVIEW", label: "Review" },
  { key: "APPROVED", label: "Approved" },
  { key: "EXPORTED", label: "Exported" }
];

export default function LIMSStepIndicator({ currentState }) {
  const currentIndex = STEPS.findIndex(s => s.key === currentState);

  return (
    <div className="flex items-center gap-2">
      {STEPS.map((step, idx) => (
        <div key={step.key} className="flex items-center">
          <div className={cn(
            "w-8 h-8 rounded-full flex items-center justify-center",
            idx <= currentIndex ? "bg-blue-500 text-white" : "bg-gray-300"
          )}>
            {idx < currentIndex ? "✓" : idx + 1}
          </div>
          {idx < STEPS.length - 1 && (
            <div className={cn(
              "w-12 h-1",
              idx < currentIndex ? "bg-blue-500" : "bg-gray-300"
            )} />
          )}
        </div>
      ))}
    </div>
  );
}
```

#### 2. ChatInterface

HITL chat panel for MDA refinement:

```tsx
// main/frontend/components/lims/ChatInterface.tsx
export default function ChatInterface({ jobId, onEditAction }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");

  const sendMessage = async () => {
    const response = await fetch("/lims/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_id: jobId, message: input })
    });
    const data = await response.json();

    setMessages([
      ...messages,
      { role: "user", content: input },
      {
        role: "assistant",
        content: data.message,
        suggested_edits: data.suggested_edits  // Cell-level edit proposals
      }
    ]);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Message history */}
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map((msg, idx) => (
          <div key={idx} className={msg.role === "user" ? "text-right" : ""}>
            <div className="inline-block bg-gray-100 p-2 rounded">
              {msg.content}
            </div>
            {/* Edit badges */}
            {msg.suggested_edits?.map(edit => (
              <div key={edit.id} className="mt-2 flex gap-2">
                <span className="text-sm">
                  Edit: {edit.sheet}.{edit.cell} → {edit.new_value}
                </span>
                <button onClick={() => onEditAction(edit.id, "apply")}>
                  Apply
                </button>
                <button onClick={() => onEditAction(edit.id, "reject")}>
                  Reject
                </button>
              </div>
            ))}
          </div>
        ))}
      </div>
      {/* Input */}
      <div className="border-t p-4">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyPress={e => e.key === "Enter" && sendMessage()}
          placeholder="Ask for changes to MDA..."
        />
      </div>
    </div>
  );
}
```

#### 3. MDAViewer (Enhanced)

Table viewer with cell-level edit highlighting:

```tsx
// main/frontend/components/lims/MDAViewer.tsx
export default function MDAViewer({ mdaRecord, appliedEdits }) {
  const isCellEdited = (sheet: string, cell: string) => {
    return appliedEdits.some(
      e => e.sheet === sheet && e.cell === cell && e.status === "applied"
    );
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr>
            <th>Field</th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(mdaRecord).map(([key, value]) => (
            <tr key={key}>
              <td className="border p-2">{key}</td>
              <td
                className={cn(
                  "border p-2",
                  isCellEdited("Equipment Info", key) && "bg-green-100"
                )}
              >
                {value}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

#### 4. LIMS Page (lims.tsx)

Full state machine orchestration with Framer Motion transitions:

```tsx
// main/frontend/pages/lims.tsx
export default function LIMSPage() {
  const [state, setState] = useState<JobState>("IDLE");
  const [jobId, setJobId] = useState<string | null>(null);
  const [mdaRecord, setMdaRecord] = useState(null);

  // Upload and start pipeline
  const handleUpload = async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch("/lims/upload", {
      method: "POST",
      body: formData
    });
    const { job_id } = await res.json();
    setJobId(job_id);
    setState("EXTRACTING");
    pollJobStatus(job_id);
  };

  // Status polling (defensive, 3s interval)
  const pollJobStatus = async (jobId: string) => {
    const interval = setInterval(async () => {
      const res = await fetch(`/lims/status/${jobId}`);
      const data = await res.json();
      setState(data.state);

      if (data.state === "PENDING_REVIEW") {
        setMdaRecord(data.result.mda_record);
        clearInterval(interval);
      } else if (data.state === "FAILED") {
        clearInterval(interval);
      }
    }, 3000);
  };

  // Human approval
  const handleApprove = async () => {
    await fetch(`/lims/approve/${jobId}`, { method: "POST" });
    setState("APPROVED");
  };

  // Export (triggers browser download)
  const handleExport = () => {
    window.open(`/lims/export/${jobId}`, "_blank");
    setState("EXPORTED");
  };

  // Chat edit actions
  const handleEditAction = async (editId: string, action: "apply" | "reject") => {
    await fetch(`/lims/edit/${jobId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ edit_id: editId, action })
    });
    // Refresh MDA record
    const res = await fetch(`/lims/status/${jobId}`);
    const data = await res.json();
    setMdaRecord(data.result.mda_record);
  };

  return (
    <div className="p-8">
      {/* Step indicator */}
      <LIMSStepIndicator currentState={state} />

      {/* View transitions (Framer Motion) */}
      <AnimatePresence mode="wait">
        {state === "IDLE" && (
          <motion.div key="upload" {...fadeTransition}>
            <FileUpload onUpload={handleUpload} />
          </motion.div>
        )}

        {state === "EXTRACTING" && (
          <motion.div key="extracting" {...fadeTransition}>
            <Spinner /> Extracting PDF data...
          </motion.div>
        )}

        {state === "GENERATING" && (
          <motion.div key="generating" {...fadeTransition}>
            <Spinner /> Generating MDA...
          </motion.div>
        )}

        {state === "PENDING_REVIEW" && (
          <motion.div key="review" {...fadeTransition}>
            {/* Two-column layout: MDA table (3/5) + Chat (2/5) */}
            <div className="grid grid-cols-5 gap-4">
              <div className="col-span-3">
                <MDAViewer
                  mdaRecord={mdaRecord}
                  appliedEdits={/* track from chat */}
                />
                <button onClick={handleApprove}>Approve MDA</button>
              </div>
              <div className="col-span-2">
                <ChatInterface
                  jobId={jobId}
                  onEditAction={handleEditAction}
                />
              </div>
            </div>
          </motion.div>
        )}

        {state === "APPROVED" && (
          <motion.div key="approved" {...fadeTransition}>
            <button onClick={handleExport}>Download XLSX</button>
          </motion.div>
        )}

        {state === "EXPORTED" && (
          <motion.div key="exported" {...fadeTransition}>
            Export complete! <button onClick={() => setState("IDLE")}>
              Upload another
            </button>
          </motion.div>
        )}

        {state === "FAILED" && (
          <motion.div key="failed" {...fadeTransition}>
            <ErrorDisplay />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
```

### API Endpoints

| Endpoint | Method | Purpose | State Transition |
|----------|--------|---------|------------------|
| `/lims/extract` | POST | Upload PDF, trigger two-layer pipeline | `IDLE` → `EXTRACTING` |
| `/lims/classify` | POST | Test type classification only | N/A (read-only) |
| `/lims/template/{type}` | GET | Get curated template skeleton | N/A (read-only) |
| `/lims/status/{job_id}` | GET | Job status + current MDA state | N/A (read-only) |
| `/lims/chat` | POST | HITL refinement chat | N/A (metadata update) |
| `/lims/approve/{job_id}` | POST | Human approval | `PENDING_REVIEW` → `APPROVED` |
| `/lims/export/{job_id}` | GET | XLSX export (APPROVED only) | `APPROVED` → `EXPORTED` |

**Authentication**: None (feature-flagged off via `NEXT_PUBLIC_AUTH_ENABLED=false`)

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **PDF Extraction** | LlamaExtract (LlamaIndex Cloud) | Structured 28-field data extraction |
| **Chat LLM** | GPT-5 / Claude Opus 4.6 via OpenRouter | HITL refinement |
| **RAG Vector Store** | ChromaDB (`mda_templates` collection) | Template retrieval |
| **Export Format** | openpyxl | 4-sheet XLSX generation |
| **Frontend Transitions** | Framer Motion | AnimatePresence view transitions |
| **State Polling** | 3-second interval fetch | Defensive status updates |

### Key Design Decisions

1. **No Auth Required**: Clerk authentication disabled (`NEXT_PUBLIC_AUTH_ENABLED=false`) to simplify PoC testing. Uses plain `fetch`, not `authenticatedFetch`.

2. **Mandatory HITL Gate**: No bypass path exists. Export is blocked until human approval via `PENDING_REVIEW → APPROVED` transition.

3. **Cell-Level Edit Tracking**: Chat edits are tracked with audit trail:
   ```json
   {
     "edit_id": "edit_001",
     "sheet": "Equipment Info",
     "cell": "B5",
     "old_value": "Manual Inspection",
     "new_value": "Automated Optical Inspection",
     "action": "applied",
     "timestamp": "2026-02-17T10:30:00Z"
   }
   ```

4. **Defensive Status Polling**: Frontend polls `/lims/status/:job_id` every 3 seconds to avoid stale state issues during long-running extraction/generation.

5. **Browser-Native Export**: Uses `window.open()` to trigger XLSX download via browser's native download mechanism (no custom download handler).

6. **Merger Analysis Name Protection**: Template LIMS identifiers (e.g., `SITE_IDENTITY`) are never overwritten by extraction names during overlay. The merger uses `protected_keys={"name"}` so canonical names are preserved; conflicts are recorded for SME review. Extraction `analysis` refs in components, calc_variables, and calculations are rewritten to template names before overlay using exact match + word-subset matching (minimum 3 tokens, unambiguous). This prevents dangling cross-sheet references caused by truncated or alternate names returned by LlamaExtract. Analysis type inference from name keywords is applied when the extracted type is `NULL`, enabling analysis matching even when the extraction omits the type field.

7. **Template-Locked Merge Mode**: When the test type is known (i.e., classified as any `TestType` value other than `TestType.OTHER`), the merger operates in template-locked mode. In this mode, `_overlay_extracted_items()` is called with `template_locked=True`, which causes unmatched extracted entities to be logged at WARNING level and rejected rather than appended to the template. The template defines the exact structure; unmatched items from extraction are treated as noise. `merge_layers()` computes `template_locked = test_type is not None and test_type != TestType.OTHER`. Rejection counts are tracked in `MergeResult.stats["TEMPLATE_LOCKED_REJECTED"]`. When `test_type` is `None` or `TestType.OTHER`, the merger falls back to the original unlocked behavior (backward compatible).

### Langfuse End-to-End Tracing

All LIMS pipeline stages are instrumented with `@observe` decorators (Langfuse v3 API: `from langfuse import get_client, observe`). A single parent trace on `TwoLayerPipeline.run()` wraps the entire pipeline; all child `@observe` decorators auto-nest beneath it.

**Full trace tree:**

```
lims-two-layer-pipeline (parent trace)
├── lims-classify
├── lims-focused-extract
├── lims-augment
│   └── rag-standards-query (auto-nested)
├── lims-merge
└── lims-chat (when user interacts)
    └── rag-mda-templates-query (auto-nested)
```

**Traced functions:**

| File | Function | Span Name |
|------|----------|-----------|
| `pipeline.py` | `TwoLayerPipeline.run()` | `lims-two-layer-pipeline` (parent) |
| `classifier.py` | `TestTypeClassifier.classify()` | `lims-classify` |
| `focused_extractor.py` | `focused_extract()` | `lims-focused-extract` |
| `pipeline.py` | `_augment_gaps()` | `lims-augment` |
| `merger.py` | `merge_layers()` | `lims-merge` |
| `chat_agent.py` | `ChatSession.chat()` | `lims-chat` |
| `mda_generator.py` | `generate_mda()` | `lims-mda-generate` |
| `rag_loader.py` | `query_similar_templates()` | `rag-mda-templates-query` |
| `standards_loader.py` | `query_standards()` | `rag-standards-query` |

**API response**: `lims_router.py` captures `trace_id` and `trace_url` after the pipeline completes and includes them in the `/lims/extract` JSON response. Langfuse is flushed after each pipeline run to ensure trace delivery.

**Key implementation details:**
- Parent trace uses `capture_input=False, capture_output=False` to avoid serializing PDF bytes
- `get_client().get_current_trace_id()` retrieves the active trace ID for API responses
- Pre-existing `@observe` decorators on `query_standards()` and `query_similar_templates()` auto-nest under the parent without modification

---

## MES Agentic BI Architecture

**Branch**: `feature/mes-agentic-bi` | **Routes**: `/bi/*` | **PRP**: `PRPs/data-copilot-poc.md`

MES Agentic BI is a proof-of-concept data copilot for the Plant Performance Reporting System (PPRS). The currently validated implementation covers B2 (filters + virtual scroll), B3 (copilot chat), and B4 (PDF/Excel export): users upload XLSX/CSV files, backend parses and stores data in an in-memory session, server-side filters are applied via pandas, an AI copilot can query and filter the data via an agentic tool-use loop, and frontend renders schema + expandable per-field filters + column visibility + virtualized table rendering + bottom chat drawer.

### Current Implemented Flow (B2 + B3 + B4)

```
User Uploads XLSX/CSV
        |
        v
   data_parser.py (pandas)
        |
        v
   session_store.py (in-memory)
  |
  +--------------------------+---------------------------+
  |                          |                           |
  v                          v                           v
  /bi/schema/{session_id}    /bi/data/{session_id}      /bi/chat/{session_id}
  |                          |                           |
  +------------+-------------+                      copilot.py
         v                                         (agentic loop)
     agentic-bi.tsx + Sidebar.tsx + DataGrid.tsx + ExportButtons.tsx + ChatDrawer.tsx
       |
       v
    /bi/export/pdf/{session_id} + /bi/export/excel/{session_id}
```

### Copilot Chat Backend (B3)

The copilot is implemented in `main/src/bi/copilot.py` as a single `chat()` function with an agentic tool-use loop. It uses the OpenAI SDK pointed at the OpenRouter base URL (`https://openrouter.ai/api/v1`), model `anthropic/claude-sonnet-4`.

**Note**: AWS Bedrock was the original target provider. It was abandoned after `IAM AccessDeniedException` errors confirmed the Bedrock kill criterion. OpenRouter with an OpenAI-compatible API is the replacement.

#### Agentic Loop

```python
# main/src/bi/copilot.py
@observe(name="bi-copilot-chat")
def chat(session_id: str, user_message: str) -> dict[str, Any]:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
    # Rebuild system prompt each call with current schema + filter state
    system_prompt = _build_system_prompt(session_id)
    messages = [{"role": "system", "content": system_prompt}, *history]

    # Agentic loop — max 5 iterations
    for iteration in range(5):
        response = client.chat.completions.create(
            model=config.copilot_model,  # "anthropic/claude-sonnet-4"
            messages=messages,
            tools=TOOLS,
        )
        if finish_reason == "stop" or not assistant_message.tool_calls:
            break
        # Dispatch tool calls, append results, continue loop
```

**Loop contract**: The LLM calls tools until it has enough data to answer, then emits a `stop` finish reason. If the loop reaches 5 iterations without stopping, the last assistant text is returned and a warning is logged. No exception is raised — failure is surfaced to the caller via the response content.

#### Tools

Five OpenAI function-calling tools are registered:

| Tool | Description |
|------|-------------|
| `apply_filter` | Apply or replace a filter on a column (supports 11 operators: equals, not_equals, contains, greater_than, less_than, greater_equal, less_equal, between, in, is_null, is_not_null). Returns updated row count. |
| `remove_filter` | Remove a filter from one column or clear all filters (pass `__all__`). |
| `search_data` | Full-text search across one or more columns in the filtered dataset. Returns up to 50 matching rows. |
| `summarize_column` | Descriptive statistics for a column: count/mean/std/min/max/quartiles for numeric; top-20 value counts for categorical. |
| `answer_question` | Structured analytical operations (count, group_by, trend, outliers, comparison, general) on the filtered DataFrame. |

#### System Prompt Design

The system prompt is rebuilt on every call using `_build_system_prompt(session_id)`. It includes:
- Dataset filename, total rows, filtered rows, column count
- Per-column metadata: dtype, unique count, null count, 5 sample values
- Currently active filter list

This ensures the LLM always has current dataset state without stale context from earlier turns.

#### Per-Session Chat History

Chat history is stored in a module-level dict (`_chat_histories: dict[str, list]`) keyed by `session_id`. The system prompt is excluded from the stored history — it is prepended fresh on each call so filter state is always accurate.

### Copilot Chat Frontend (B3)

The `ChatDrawer` component (`main/frontend/components/bi/ChatDrawer.tsx`) is a bottom-anchored expandable drawer rendered on the `agentic-bi.tsx` page.

```tsx
// main/frontend/components/bi/ChatDrawer.tsx
// Bottom drawer: collapsed=64px, expanded=420px, spring animation via Framer Motion
export default function ChatDrawer({ sessionId, onFiltersChanged }) {
  const [expanded, setExpanded] = useState(false);

  // Auto-expand on first message send
  const handleSend = async (text) => {
    setExpanded(true);
    const data: BIChatResponse = await fetch(`/bi/chat/${sessionId}`, { ... });

    // Render filter action badges for apply_filter / remove_filter tool calls
    // If data.filters_changed, call onFiltersChanged() to sync grid state
  };

  return (
    <motion.div
      animate={{ height: expanded ? 420 : 64 }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
    >
      {/* 3 suggestion chips when no messages present */}
      {/* Message list with filter action badges */}
    </motion.div>
  );
}
```

**Key behaviors:**
- Collapsed (64 px) by default; auto-expands to 420 px when the first message is sent
- Three suggestion chips are shown when the message list is empty
- Filter action badges are rendered for `apply_filter` and `remove_filter` tool calls, displaying the column and operator applied
- When the backend reports `filters_changed: true`, the drawer calls `onFiltersChanged()` to trigger a grid data refresh in the parent page

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Data Ingestion** | pandas | XLSX/CSV parsing (~15K rows) |
| **Data Grid** | TanStack Table v8 | Paginated grid rendering |
| **Copilot LLM** | `anthropic/claude-sonnet-4` via OpenRouter | Agentic tool-use chat loop |
| **Copilot SDK** | OpenAI Python SDK (OpenRouter-compatible) | Function calling API |
| **Copilot Tracing** | Langfuse `@observe` | Per-call trace: `bi-copilot-chat` |
| **Backend** | FastAPI (`/bi/*` routes) | Upload, session, schema, data, chat endpoints |
| **Frontend** | Next.js 14 (Pages Router, `agentic-bi.tsx`) | Upload, sidebar, grid, pagination, chat drawer |
| **Docker Compose** | `docker-compose.bi.yml` | Planned in later phase |
| **Authentication** | None (PoC) | No auth required |
| **Color Accent** | Cyan/Teal | UI theme (vs blue for thesis, emerald for LIMS) |

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/bi/upload` | POST | XLSX/CSV upload + parse into session |
| `/bi/data/{session_id}` | GET | Paginated filtered rows for selected session |
| `/bi/schema/{session_id}` | GET | Column metadata for sidebar |
| `/bi/filter/{session_id}` | POST | Apply/update active server-side filters |
| `/bi/chat/{session_id}` | POST | Copilot agentic chat turn (OpenRouter, tool-use loop) |
| `/bi/export/pdf/{session_id}` | GET | Filtered PDF export (landscape A4, max 1000 rows) |
| `/bi/export/excel/{session_id}` | GET | Filtered Excel export with "Filters Applied" metadata |

### Planned Next Flow (B5)

- **B2**: filter engine + sidebar filter controls + virtual scrolling (validated).
- **B3**: copilot chat (`/bi/chat/{session_id}`) via OpenRouter, agentic tool-use loop (validated).
- **B4**: PDF/Excel export endpoints + top-bar export controls (validated).
- **B5**: polish, compose stack, deployment updates.

### Key Design Decisions

1. **No Auth Required**: PoC only — no Clerk integration. Uses plain `fetch`.

2. **In-Memory Session Store**: Uploaded data held in `session_store.py` (keyed by `session_id`). No database needed for PoC scale.

3. **Additive Delivery by phase**: B1 implemented and validated first; B2-B5 are layered without impacting thesis/LIMS routes.

4. **Pagination-first strategy**: B1 uses server-side pagination (100 rows/page) before introducing virtual scroll in B2.

5. **Additive Architecture**: `bi_router.py` is mounted separately from thesis routes and LIMS routes. Zero impact on existing code.

6. **OpenRouter instead of Bedrock**: AWS Bedrock was the originally planned copilot LLM provider. After confirmed `IAM AccessDeniedException` errors (kill criterion), the copilot was switched to OpenRouter using the OpenAI-compatible API. `config.py` field renamed from `bedrock_model_id` to `copilot_model`. No other BI files required changes.

7. **Dynamic system prompt**: The copilot system prompt is rebuilt on every chat call with current dataset schema and active filter state. It is never stored in chat history, preventing stale schema/filter information across turns.

---

## Docker Stack

### Thesis Project Stack (docker-compose.dev.yml)

5-service Docker Compose architecture (LOCAL DEVELOPMENT):

| Service | Purpose | Technology |
|---------|---------|------------|
| **postgres** | Job queue metadata (dev only) | PostgreSQL 15 + pgvector |
| **localstack** | AWS SQS emulation | LocalStack 3.9.0 |
| **api** | REST API endpoints | FastAPI + uvicorn |
| **worker** | Async workflow executor | Python asyncio |
| **frontend** | Job submission UI | Next.js 14 |

**Note**: Production AWS deployment uses a stateless architecture. PostgreSQL is for local development only; production stores ChromaDB in S3 (downloaded at container startup).

### AI4LIMS PoC Stack (docker-compose.lims.yml)

Minimal 2-service architecture for LIMS PoC:

| Service | Purpose | Technology |
|---------|---------|------------|
| **api** | LIMS API endpoints (`/lims/*`) | FastAPI + uvicorn |
| **frontend** | LIMS HITL interface (`/lims.tsx`) | Next.js 14 |

**Note**: No PostgreSQL, LocalStack, or worker service. AI4LIMS uses in-memory job store for simplicity. ChromaDB `mda_templates` collection is locally persisted.

```yaml
# docker-compose.dev.yml (key services)
services:
  postgres:
    image: ankane/pgvector:v0.8.1
    environment:
      POSTGRES_DB: pharma_tests
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]

  api:
    build:
      dockerfile: Dockerfile.api
    ports:
      - "8080:8080"
    environment:
      LANGFUSE_HOST: https://cloud.langfuse.com
      LLM_MODEL: deepseek/deepseek-chat
    depends_on:
      postgres:
        condition: service_healthy

  worker:
    build:
      dockerfile: Dockerfile.api
    command: python main/api/worker.py
    depends_on:
      postgres:
        condition: service_healthy

  frontend:
    build:
      context: ./frontend
    ports:
      - "3000:3000"
```

**Job Queue Flow:**
```
API → PostgreSQL → SQS → Worker → LangFuse traces
```

---

## Technology Stack

### Thesis Project (Main)

| Component | Technology |
|-----------|------------|
| LLM (Production) | DeepSeek V3.1 via OpenRouter |
| LLM (Development) | Gemini 2.5 Flash Lite |
| Observability | LangFuse Cloud (EU) |
| Vector Store | ChromaDB (`pharmaceutical_regulations` collection) |
| Authentication | Clerk |
| Backend | FastAPI |
| Frontend | Next.js 14 (Pages Router) |
| Queue | AWS SQS (LocalStack for dev) |
| Database | PostgreSQL + pgvector (local dev only) |
| IaC | Terraform |

### AI4LIMS PoC (Branch: prjoject_p_protatype)

| Component | Technology |
|-----------|------------|
| PDF Extraction | LlamaExtract via LlamaIndex Cloud |
| Chat LLM | GPT-5 / Claude Opus 4.6 via OpenRouter |
| RAG Vector Store | ChromaDB (`mda_templates` collection) |
| Export Format | openpyxl (4-sheet XLSX) |
| UI Transitions | Framer Motion |
| Authentication | Clerk (disabled via `NEXT_PUBLIC_AUTH_ENABLED=false`) |
| Backend | FastAPI (`/lims/*` routes) |
| Frontend | Next.js 14 (Pages Router, `/lims.tsx`) |
| Docker Compose | `docker-compose.lims.yml` (minimal: frontend + API only) |

### MES Agentic BI (Branch: feature/mes-agentic-bi)

| Component | Technology |
|-----------|------------|
| Data Ingestion | pandas (XLSX/CSV, ~15K rows) |
| Data Grid | TanStack Table v8 + @tanstack/react-virtual |
| Copilot LLM | `anthropic/claude-sonnet-4` via OpenRouter |
| Copilot SDK | OpenAI Python SDK (OpenRouter-compatible base URL) |
| Data Processing | pandas DataFrame (in-memory sessions) |
| PDF Export | fpdf2 |
| Excel Export | openpyxl |
| Observability | Langfuse `@observe` (`bi-copilot-chat` span) |
| Authentication | None (PoC: `NEXT_PUBLIC_AUTH_ENABLED=false`) |
| Backend | FastAPI (`/bi/*` routes) |
| Frontend | Next.js 14 (Pages Router, `/agentic-bi.tsx`) |
| Docker Compose | `docker-compose.bi.yml` (minimal: frontend + API only) |

---

## Environment Configuration

```bash
# .env.local
# LLM
OPENROUTER_API_KEY=sk-or-v1-...
LLM_MODEL=deepseek/deepseek-chat
EMBEDDING_MODEL=text-embedding-3-small

# LangFuse
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

# Clerk
CLERK_SECRET_KEY=sk_test_...
CLERK_PEM_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----..."
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...

# Database
DATABASE_URL=postgresql://postgres:password@postgres:5432/pharma_tests

# RAG
RAG_VECTOR_STORE_PATH=/app/chroma_db
RAG_COLLECTION_NAME=pharmaceutical_regulations
```

---

## Code Structure

### Thesis Project (Main)

```
thesis_project/
├── main/
│   ├── src/
│   │   ├── core/unified_workflow.py      # Master orchestrator
│   │   ├── agents/
│   │   │   ├── categorization/           # GAMP-5 categorizer
│   │   │   ├── oq_generator/             # Test generator
│   │   │   └── parallel/                 # Context, Research, SME
│   │   ├── validation/
│   │   │   ├── alcoa_validator.py        # ALCOA+ implementation
│   │   │   └── traceability.py           # Requirements mapping
│   │   └── security/owasp_validator.py   # Security controls
│   ├── api/
│   │   ├── app.py                        # FastAPI application
│   │   └── worker.py                     # Background job processor
│   └── tests/
├── frontend/                             # Next.js dashboard
├── aws/terraform/                        # AWS infrastructure
└── docker-compose.dev.yml
```

### AI4LIMS PoC (Branch: prjoject_p_protatype)

```
thesis_project/
├── main/
│   ├── src/
│   │   └── lims/
│   │       ├── mda_schema.py             # 28-field extraction schema
│   │       ├── extractor.py              # LlamaExtract client
│   │       ├── mda_generator.py          # RAG-enhanced MDA generation
│   │       ├── chat_agent.py             # HITL chat for refinement
│   │       ├── xlsx_exporter.py          # 4-sheet XLSX export
│   │       └── job_store.py              # In-memory state management
│   ├── api/
│   │   └── lims_router.py                # LIMS API endpoints (/lims/*)
│   └── tests/
│       └── lims/
├── frontend/
│   ├── pages/
│   │   └── lims.tsx                      # LIMS HITL page
│   └── components/
│       └── lims/
│           ├── LIMSStepIndicator.tsx     # Pipeline stage indicator
│           ├── ChatInterface.tsx         # Chat panel with edit badges
│           └── MDAViewer.tsx             # Enhanced table with highlights
├── docs/
│   └── project_p/
│       ├── AI4LIMS_PoC_Plan.md           # PoC overview
│       ├── LIMS-001-pdf-extraction-setup.md
│       ├── LIMS-002-mda-generation-rag-xlsx.md
│       └── LIMS-003-chat-agent-hitl-router.md
├── chroma_db/
│   └── mda_templates/                    # RAG collection
└── docker-compose.lims.yml               # LIMS PoC compose file
```
