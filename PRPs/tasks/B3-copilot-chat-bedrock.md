# Task B3 — Copilot Chat with AWS Bedrock

**Phase:** 3 (AI Copilot) | **Day:** 3 (highest risk)
**Dependencies:** B2 (Filters + Virtual Scroll)
**Branch:** `feature/mes-agentic-bi`
**Status:** NOT STARTED
**Estimated effort:** 1 day

---

## Objective

Integrate AWS Bedrock Converse API with Claude Sonnet 4.6 for the copilot chat. The copilot receives the data schema as context and has 5 tools (apply_filter, remove_filter, search_data, summarize_column, answer_question). Implement the agentic loop: user message -> Bedrock with tools -> execute pandas operations -> feed results back -> natural language summary. Frontend: bottom expandable chat drawer with suggestion chips.

**Kill criterion:** If Bedrock model access not available, switch to OpenRouter (same tool definitions, different client). `LIMS_OPENROUTER_API_KEY` is already in .env.local.

---

## Files to Create

| File | Purpose |
|------|---------|
| `main/src/bi/copilot.py` | `BICopilot` class. System prompt builder (column schema, types, sample values, active filters, row counts). 5 tool definitions for Bedrock Converse `toolConfig`. Agentic loop: send message -> process `toolUse` blocks -> execute FilterEngine operations -> send `toolResult` back -> get summary. Chat history per session. Langfuse `@observe` tracing. |
| `main/frontend/components/bi/ChatDrawer.tsx` | Bottom drawer (Framer Motion height animation). Collapsed: just "Chat Assistant" bar + input field. Expanded: message history + suggestion chips ("Show summary table", "Generate a detailed report", "Filter and download as Excel") + input. Filter action badges when copilot applies filters. Follow `main/frontend/components/ChatInterface.tsx` patterns. |

## Files to Modify

| File | Change |
|------|--------|
| `main/api/bi_router.py` | Add `POST /bi/chat/{session_id}`. Request: `{ message }`. Response: `{ response, tool_calls, filters_changed, active_filters, filtered_row_count }`. |
| `main/frontend/pages/agentic-bi.tsx` | Integrate ChatDrawer. When `filters_changed=true` in chat response, re-fetch grid data and update sidebar filter state. |

---

## Implementation Details

### 1. copilot.py — Bedrock Converse with Tool Use

```python
import boto3
import json
from langfuse.decorators import observe

class BICopilot:
    def __init__(self, session_id: str, config: BIConfig):
        self.client = boto3.client('bedrock-runtime', region_name=config.bedrock_region)
        self.model_id = config.bedrock_model_id  # us.anthropic.claude-sonnet-4-6
        self.filter_engine = FilterEngine(session_id)
        self.session_id = session_id

    def _build_system_prompt(self, session: BISession) -> str:
        # Include: column names, types, sample values, active filters, total/filtered rows
        # Tell LLM to use tools for data operations, not guess answers

    def _get_tool_config(self) -> dict:
        return {"tools": [
            {"toolSpec": {"name": "apply_filter", "description": "Apply a filter to narrow data",
                "inputSchema": {"json": {"type": "object", "properties": {
                    "column": {"type": "string"}, "operator": {"type": "string",
                        "enum": ["equals","not_equals","contains","greater_than","less_than","between","in"]},
                    "value": {}}, "required": ["column","operator","value"]}}}},
            {"toolSpec": {"name": "remove_filter", ...}},
            {"toolSpec": {"name": "search_data", ...}},
            {"toolSpec": {"name": "summarize_column", ...}},
            {"toolSpec": {"name": "answer_question", ...}},
        ]}

    @observe(name="bi-copilot-chat")
    def chat(self, user_message: str) -> dict:
        session = get_session(self.session_id)
        system_prompt = self._build_system_prompt(session)
        messages = session.chat_history + [{"role": "user", "content": [{"text": user_message}]}]

        response = self.client.converse(
            modelId=self.model_id,
            messages=messages,
            system=[{"text": system_prompt}],
            toolConfig=self._get_tool_config(),
        )

        # Process response content blocks
        assistant_content = response["output"]["message"]["content"]
        tool_calls = []
        filters_changed = False

        for block in assistant_content:
            if "toolUse" in block:
                tool_name = block["toolUse"]["name"]
                tool_input = block["toolUse"]["input"]
                result = self._execute_tool(tool_name, tool_input)
                if tool_name in ("apply_filter", "remove_filter"):
                    filters_changed = True
                tool_calls.append({"tool": tool_name, "input": tool_input, "result": result})

        # If tools were called, feed results back for natural language summary
        if tool_calls:
            messages.append({"role": "assistant", "content": assistant_content})
            tool_results = [{"role": "user", "content": [
                {"toolResult": {"toolUseId": block["toolUse"]["toolUseId"],
                    "content": [{"json": result}]}}
                for block in assistant_content if "toolUse" in block
                for result in [self._execute_tool(block["toolUse"]["name"], block["toolUse"]["input"])]
            ]}]
            # Second Bedrock call for summary
            follow_up = self.client.converse(modelId=self.model_id, messages=messages + tool_results,
                system=[{"text": system_prompt}])
            response_text = follow_up["output"]["message"]["content"][0]["text"]
        else:
            response_text = assistant_content[0]["text"]

        return {"response": response_text, "tool_calls": tool_calls,
                "filters_changed": filters_changed,
                "active_filters": self.filter_engine.get_active_filters(),
                "filtered_row_count": self.filter_engine.filtered_count()}
```

### 2. ChatDrawer.tsx — Bottom Drawer

Follow `ChatInterface.tsx` pattern: message bubbles, auto-scroll, loading dots. Additional features:
- Framer Motion `animate={{ height }}` for expand/collapse
- Suggestion chips: "Show summary table", "Generate a detailed report", "Filter and download as Excel"
- Filter action badges: when `tool_calls` includes `apply_filter`, show badge "Filter applied: Country = India"
- Input with Enter key handler + send button

---

## Environment Variables

```bash
# Already in .env.local from pre-requisites:
BI_BEDROCK_REGION=us-east-1
BI_BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-6
```

---

## Testing Strategy

```bash
# 1. Verify Bedrock connectivity
python -c "
import boto3
client = boto3.client('bedrock-runtime', region_name='us-east-1')
r = client.converse(modelId='us.anthropic.claude-sonnet-4-6',
    messages=[{'role':'user','content':[{'text':'Say hello'}]}])
print(r['output']['message']['content'][0]['text'])
"

# 2. Test chat endpoint
curl -X POST http://localhost:8080/bi/chat/{session_id} \
  -H "Content-Type: application/json" \
  -d '{"message": "Show data where Country Name is India"}'
# Expect: { response: "...", filters_changed: true, active_filters: [...] }

# 3. Test summarize
curl -X POST http://localhost:8080/bi/chat/{session_id} \
  -H "Content-Type: application/json" \
  -d '{"message": "How many unique countries are in this dataset?"}'
# Expect: { response: "There are X unique countries..." }

# 4. Frontend: type in chat drawer -> see response + filter applied
```

---

## Gate Criteria (Pass/Fail)

- [ ] Bedrock Converse API responds within 5 seconds
- [ ] Chat "Show data where Country = India" -> apply_filter tool called -> filters_changed=true
- [ ] Chat "How many records have Death Rate > 100?" -> answer_question tool -> correct count
- [ ] Chat "Summarize the Year column" -> summarize_column tool -> statistics returned
- [ ] Chat "Remove all filters" -> remove_filter with __all__ -> filters cleared
- [ ] Filter changes from chat sync to sidebar filter state
- [ ] Suggestion chips trigger correct chat messages
- [ ] Chat drawer expands/collapses with animation
- [ ] Langfuse trace shows tool calls for chat interaction
