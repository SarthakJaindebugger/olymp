# Apollo Case Study Prototype (Phase 1 + Phase 2)

This repository contains a working prototype for the Olymp AG Apollo case study:

- **Phase 1:** concept/architecture document in `docs/phase1_architecture.md`
- **Phase 2:** Flask backend + React TypeScript frontend + Ollama local LLM tool-calling integration

## What is implemented

- Deterministic aggregation tools over mocked Etops-like client data
- Flask API endpoints:
  - `POST /api/chat` (LLM + tool calling)
  - `GET /api/aggregation/liquidity?limit=5` (deterministic check)
  - `GET /api/health`
- React + TypeScript frontend (`react_frontend/`) with:
  - chat box
  - assistant response
  - tool trace
  - top-liquidity table

## Tech choices

- Backend: Python + Flask
- Frontend: React + TypeScript (Vite)
- LLM runtime: **Ollama local server** (default model `gpt oss 120b cloud`)
- Data source: mock JSON fixture with live Etops adapter scaffold

## Run locally

### 1) Start Ollama

Install Ollama and pull a model that supports tool calling:

```bash
ollama pull "gpt oss 120b cloud"
ollama serve
```

### 2) Setup backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

### 3) Run React frontend

```bash
cd react_frontend
npm install
npm run dev
```

Vite runs at `http://localhost:5173` and proxies `/api` to `http://localhost:5000`.

### Optional: serve built frontend from Flask

```bash
cd react_frontend
npm run build
```

Then Flask `/` serves `react_frontend/dist/index.html`.

## Environment variables

Optional:

- `OLLAMA_BASE_URL` (default: `http://localhost:11434`)
- `OLLAMA_MODEL` (default: `gpt oss 120b cloud`)
- `ETOPS_BASE_URL` and `ETOPS_TOKEN` (if testing against real Etops API)

## Suggested demo prompt

> Which clients currently have the highest free liquidity, and which of those have not had a contact event in the last 90 days?

## Notes on incompleteness / next steps

- No production auth/tenancy or persistent cache
- Limited test coverage (prototype focus)
- Streaming tool updates not implemented yet (would be next UX upgrade)

## AI assistance disclosure

AI assistance was used to accelerate scaffolding and documentation; architecture and trade-offs were reviewed and edited manually.
