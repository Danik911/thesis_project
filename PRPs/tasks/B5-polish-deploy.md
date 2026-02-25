# Task B5 — Polish + Deploy

**Phase:** 5 (Polish) | **Day:** 5
**Dependencies:** B1-B4 (all features complete)
**Branch:** `feature/mes-agentic-bi`
**Status:** NOT STARTED
**Estimated effort:** 1 day

---

## Objective

Apply bold frontend design (Space Grotesk headings, cyan/teal accent, Framer Motion transitions, loading skeletons), create Docker compose file for containerized deployment, run E2E testing, and finalize documentation.

---

## Files to Create

| File | Purpose |
|------|---------|
| `docker-compose.bi.yml` | 2-service compose: API + Frontend. Follow `docker-compose.lims.yml` pattern. env_file: .env.local, volumes: ./main:/app/main:ro, network: bi-dev. |

## Files to Modify

| File | Change |
|------|--------|
| `main/frontend/pages/agentic-bi.tsx` | Bold design pass: Space Grotesk headings via `font-display`, cyan-400/500/600 accent colors, AnimatePresence with FADE transitions between states (idle/loaded), loading skeletons during upload, error state with retry. |
| `main/frontend/components/bi/Sidebar.tsx` | Design polish: glass-panel effect, field list with hover highlights, filter section with smooth expand animation. |
| `main/frontend/components/bi/DataGrid.tsx` | Design polish: sticky header with `bg-slate-800/90 backdrop-blur`, hover row highlighting `hover:bg-slate-700/30`, cyan column headers. |
| `main/frontend/components/bi/ChatDrawer.tsx` | Design polish: smooth Framer Motion expand/collapse, suggestion chip hover effects, typing indicator animation. |
| `main/frontend/components/bi/ExportButtons.tsx` | Design polish: icon buttons matching screenshot, hover glow effect. |

---

## Implementation Details

### 1. docker-compose.bi.yml

```yaml
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: bi-api
    env_file: .env.local
    environment:
      ENVIRONMENT: development
    ports:
      - "8080:8080"
    volumes:
      - ./main:/app/main:ro
    networks:
      - bi-dev

  frontend:
    build:
      context: ./main/frontend
      dockerfile: ../../Dockerfile.frontend
      target: base
      args:
        NEXT_PUBLIC_API_BASE_URL: http://localhost:8080
    container_name: bi-frontend
    env_file: .env.local
    ports:
      - "3000:3000"
    volumes:
      - ./main/frontend:/app
      - /app/node_modules
      - /app/.next
    command: ["npm", "run", "dev", "--", "--hostname", "0.0.0.0", "--port", "3000"]
    depends_on:
      - api
    networks:
      - bi-dev

networks:
  bi-dev:
    driver: bridge
```

### 2. Bold Design Checklist

- [ ] Font: Space Grotesk for headings (`font-display` class), Instrument Sans for body
- [ ] Colors: `cyan-400` text/icons, `cyan-600` buttons, `cyan-500/10` backgrounds
- [ ] Title gradient: `bg-gradient-to-r from-cyan-400 to-blue-300 bg-clip-text text-transparent`
- [ ] Panels: `rounded-xl bg-slate-800/50 border border-slate-700/50`
- [ ] Animations: AnimatePresence for state transitions, staggered entrance
- [ ] Loading: skeleton placeholders during upload/filter operations
- [ ] Empty state: database icon + "No data loaded" + upload prompt
- [ ] Error state: red error message with retry button

---

## Testing Strategy

```bash
# 1. Docker compose
docker compose -f docker-compose.bi.yml up -d
curl http://localhost:8080/bi/upload -F "file=@sample_data.xlsx"
# Navigate to http://localhost:3000/agentic-bi

# 2. Full E2E flow
# Upload -> Filter via sidebar -> Chat "Show India data" -> Export Excel -> Export PDF

# 3. Edge cases
# - Empty file upload (should error gracefully)
# - CSV with special characters (commas in values)
# - 15K row file (virtual scroll + export performance)
# - Chat with no data loaded (should return helpful message)
```

---

## Gate Criteria (Pass/Fail)

- [ ] Docker compose starts both services without errors
- [ ] Full E2E: Upload -> Filter -> Chat -> Export works in Docker
- [ ] Bold design: cyan accent visible, Space Grotesk headings, dark theme consistent
- [ ] Loading states: skeleton during upload, spinner during chat
- [ ] Error states: graceful error messages for bad files, Bedrock errors
- [ ] Empty state matches screenshot (database icon + upload prompt)
- [ ] Thesis and LIMS pages still work at `/generate`, `/history`, `/lims`
