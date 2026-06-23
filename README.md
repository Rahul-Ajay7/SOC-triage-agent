# 🛡️ SOC Triage Agent

An **autonomous Security Operations Center (SOC) triage agent**. It ingests raw
security alerts (SSH/auth logs), investigates them like a junior analyst using a
**LangGraph reasoning loop + tools**, and produces a verdict
(`benign` / `suspicious` / `critical`) with a **full step-by-step reasoning trace**.

The star feature is that trace — you can watch the agent *think*:

> checked IP → unknown → searched history → 20 failed + 1 success → **CRITICAL**

## Why it's "agentic" (not just one LLM call)

The agent loops. After gathering evidence it **assesses its own confidence**.
If confidence is low, it **loops back to gather more evidence** before deciding:

```
START → ingest → extract_iocs → enrich ⇄ assess → classify → summarize → END
                                    └────────┘
                          loop back while confidence is LOW
```

## Architecture

| Layer | What it does |
|-------|--------------|
| `app/parsers/` | Turn raw logs into structured alerts (`auth_log.py`) |
| `app/tools/` | What the agent can DO: `ioc_extractor`, `ip_reputation`, `geo_lookup`, `mitre_mapper`, `log_search` |
| `app/agent/` | The brain — LangGraph `state` + `nodes` + `graph`, `prompts`, and the reused `llm` fallback chain |
| `app/services/` | Orchestration: alert → agent → persist incident + trace |
| `app/api/` | REST: push alerts, pull queue, get trace, approve/reject |
| `frontend/` | Next.js (App Router + TypeScript + Tailwind) dashboard with the **AgentTrace** view |

## Free-first design

Runs with an **empty `.env`** — every external dependency degrades to
deterministic heuristics:

- **LLM** — fallback chain **Groq → Gemini → Ollama** (free tiers); heuristics if none set.
- **IP reputation** — AbuseIPDB free tier; heuristic (internal/known-bad/unknown) otherwise.
- **Geo / impossible travel** — ip-api.com (free, no key); offline map for demo IPs.
- **MITRE ATT&CK** — local JSON, no network.

## Quick start

**1. Backend** (port 8001):

```bash
cd backend
py -3.11 -m venv .venv
.venv\Scripts\activate          # macOS/Linux: . .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env          # optional — works empty too
uvicorn main:app --reload --port 8001
```

**2. Frontend** (port 3000, new terminal):

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000/** and click **“Load demo alerts”**.

- API docs: http://localhost:8001/docs
- Backend tests: `pytest` (from `backend/`)
- Frontend talks to the backend via `NEXT_PUBLIC_API_BASE` (see `frontend/.env.local`).

### Or with Docker

```bash
cp .env.example backend/.env
docker compose up --build
```

## Demo scenarios (`POST /api/seed`)

1. **Benign login** — internal publickey login → `benign`, high confidence, no loop.
2. **Brute force** — thin alert (2 failures, unknown IP) → low confidence →
   **loops back**, log search finds 20 failures + 1 success → `critical`.
3. **Impossible travel** — same user logs in from Singapore then Moscow minutes
   apart → `critical`, mapped to MITRE **T1078 Valid Accounts**.

## API

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/alerts` | Push an alert → stored **and** triaged; returns verdict + trace |
| `GET`  | `/api/alerts` | Alert queue |
| `GET`  | `/api/incidents` | Verdicts queue |
| `GET`  | `/api/incidents/{id}` | Incident + full trace |
| `GET`  | `/api/incidents/{id}/trace` | Just the reasoning trace |
| `POST` | `/api/incidents/{id}/action` | Human approve/reject |
| `POST` | `/api/seed` | Load + triage the 3 demo alerts |
