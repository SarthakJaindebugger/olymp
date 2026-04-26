# Phase 1 — Concept & Architecture (Apollo case)

## Problem statement
Etops CRM exposes per-client REST resources but no cross-client aggregation endpoint. The business need is to answer multi-client questions (e.g., *top free liquidity + stale contact*) in <10s with auditable references.

## Proposed approach
Build a **query and aggregation tier** between chat UX and Etops API:

1. **Natural-language orchestration**
   - LLM is only an intent/router layer.
   - It can call deterministic backend tools (no RAG for computed answers).
2. **Deterministic aggregation service**
   - Fetch client list once, fan out profile fetches concurrently.
   - Compute ranking/filtering server-side in typed Python logic.
3. **Auditable output contract**
   - Return structured rows with `client_id` references and filter metadata.
   - LLM summarizes but does not invent numbers.

## Architecture (logical)
- **Frontend (React single page):** chat input, result panel, tool trace.
- **Flask API:**
  - `POST /api/chat`: calls LLM with tool schema.
  - `GET /api/aggregation/liquidity`: deterministic endpoint for direct checks.
- **Aggregation service:**
  - Concurrency via thread pool for per-client fan-out.
  - Short TTL cache (30s) to reduce repeated fan-out.
- **Etops adapter:**
  - Supports live mode (token + base URL) and mock mode (JSON fixture).
- **Ollama local LLM:** function/tool calling loop over backend tools.

## Key trade-offs
- **Why tools over free-form prompting:** reproducibility and compliance traceability.
- **Why short TTL cache:** balances data freshness vs latency for interactive chat.
- **Why thread pool (prototype):** simple to implement in Flask context; could evolve to async workers or materialized snapshot service.

## Limitations (explicit)
- No auth/multi-tenant boundaries in prototype.
- In-memory cache only (single-process); production should externalize cache.
- Tool calling quality depends on model function-calling reliability.
- Mock schema approximates Etops fields; live payload mapping may require adapters.

## Phase-3 production path (if continued)
- Add scheduled snapshot/index table for O(1) query-time ranking.
- Add robust retries/circuit breakers around Etops calls.
- Add structured observability (tool-call logs + latency + correctness checks).
- Add policy guardrails (allowed tools, max row counts, PII-safe logging).
