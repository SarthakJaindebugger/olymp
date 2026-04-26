# Phase 1 — Concept & Architecture (Apollo Query Layer)

## 1) Problem statement
Etops CRM is built as a per-client API. It is good for reading one client profile at a time, but it does not provide native cross-client queries such as:

- “Which clients have the highest free liquidity?”
- “Of those, which have not had a contact event in the last 90 days?”

In practice, this forces relationship managers into slow CSV exports and ad-hoc analysis. Apollo needs a query layer that answers these portfolio-wide questions quickly, correctly, and with auditable references.

---

## 2) Proposed approach
Build a **deterministic aggregation tier** between the chat UI and Etops API.

### A. LLM role (intent router, not calculator)
- Use the LLM only to interpret user intent and call backend tools.
- Do **not** let the LLM invent rankings or computed values.
- All numeric answers must come from deterministic backend functions.

### B. Aggregation service role (source of truth)
- Fetch client identifiers from Etops.
- Fan out profile/detail requests concurrently.
- Compute ranking/filtering in Python logic (e.g., top liquidity + inactivity threshold).
- Return structured JSON with client IDs so results are traceable.

### C. UX role
- Chat box for natural language question.
- Show intermediate progress/tool activity where possible.
- Show final ranked output in a table with client references.

---

## 3) High-level architecture
1. **Frontend** (lightweight React page)
   - Sends user question to backend chat endpoint.
   - Renders final answer + deterministic rows.

2. **Flask backend**
   - `/api/chat`: LLM orchestration with tool/function calling.
   - `/api/aggregation/*`: deterministic computation endpoints.

3. **Etops adapter**
   - Encapsulates Etops-specific request/response mapping.
   - Allows mock mode for local development without credentials.

4. **Performance layer**
   - Concurrent fan-out for per-client calls.
   - Short-lived cache to reduce repeated query latency.

---

## 4) Why this design
- **Auditability:** deterministic functions produce reproducible results.
- **Compliance fit:** easier to explain and verify than free-form LLM answers.
- **Incremental evolution:** can start with live fan-out and move to snapshots/indexing later.
- **Developer clarity:** clear separation between orchestration (LLM) and computation (backend).

---

## 5) Limitations (current phase)
- No multi-tenant isolation/auth in prototype scope.
- In-memory cache only (single-process, non-persistent).
- Depends on Etops API latency and rate limits.
- Tool-call quality varies by model; guardrails are still required.

---

## 6) Next steps toward production
- Add periodic materialized snapshots for faster aggregation.
- Add retries, rate-limit handling, and circuit breaking around Etops calls.
- Add observability (query latency, tool traces, error metrics).
- Add policy guardrails (tool allowlists, row limits, safe logging).

This design keeps the LLM useful for language while keeping all business-critical answers deterministic and defensible.
