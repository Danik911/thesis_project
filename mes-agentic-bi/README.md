# MES Agentic BI

Standalone data copilot service for manufacturing execution system (MES) analytics.

## Quick Start

### Local Development (no Docker)

**Backend:**
```bash
uv sync
uv run uvicorn api.app:app --port 8080 --reload
curl http://localhost:8080/health
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000/agentic-bi
```

### Docker Compose

```bash
cp .env.example .env.local
# Edit .env.local with your API keys
docker compose up -d
# API: http://localhost:8080
# UI:  http://localhost:3000/agentic-bi
```

## Architecture

```
mes-agentic-bi/
  api/           # FastAPI routers + app entry
  src/bi/        # Business logic (copilot, filters, charts, exporters)
  frontend/      # Next.js pages + TanStack Table grid
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/bi/upload` | Upload CSV/XLSX |
| GET | `/bi/data/{session_id}` | Paginated data |
| GET | `/bi/schema/{session_id}` | Session schema |
| POST | `/bi/filter/{session_id}` | Apply filters |
| POST | `/bi/chat/{session_id}` | Copilot chat |
| GET | `/bi/export/excel/{session_id}` | Excel export |
| GET | `/bi/export/pdf/{session_id}` | PDF export |
| GET | `/bi/charts/recommend/{session_id}` | Chart recommendations |
| POST | `/bi/charts/data/{session_id}` | Chart data |
| POST | `/bi/snowflake/tables` | List Snowflake tables |
| POST | `/bi/snowflake/load/table` | Load Snowflake table |
| POST | `/bi/voice/session/{session_id}` | Start voice session |
| POST | `/bi/voice/tts/{session_id}` | Text-to-speech |

## Environment Variables

See `.env.example` for all configuration options.
