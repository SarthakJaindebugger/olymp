# Apollo Query Layer – Design Document

## Problem Statement
The Etops CRM API provides per‑client endpoints (list clients, fetch one client’s details). There is no native cross‑client aggregation. 

A relationship manager at an EAM needs to ask: *“Which clients have the highest free liquidity and have not had a contact event in the last 90 days?”* 

Currently this takes 30+ minutes to 1 day of manual Excel work. The goal is to answer it in seconds via natural language, with deterministic, auditable results.

## Proposed Architecture

( 
    User (React chat) → Flask (/chat) → Ollama (local LLM) → Tool call parsing → Aggregation Layer → Mock Etops API → Ranked results → Frontend (React)
)

# Two core components:

### 1. Aggregation Layer (Python)
- **Concurrent fan‑out** – Use `asyncio` + `aiohttp` or `ThreadPoolExecutor` to fetch all 250 clients in parallel (bounded concurrency of 20 simultaneous requests).
- **In‑memory caching** – Cache individual client profiles for 5 minutes (TTL). Reduces load on repeated queries.
- **Post‑query filtering** – Fetch all required fields (free liquidity, last contact date) for every client, then filter/sort in‑memory. For 250 clients this is fine; for 5000 we would pre‑index.

### 2. LLM Tool Use with Ollama
Ollama does not natively support OpenAI‑style function calling on all models. **Solution**: Use a model that supports tools (e.g., `llama3.1:8b` or `mistral:7b‑v0.3`). Define a tool schema in the system prompt and instruct the LLM to output **JSON** that matches a `tool_call` object. The Flask backend then parses this JSON and executes the corresponding Python function.

**Tool definition** (embedded in system prompt):
```json
{
  "name": "rank_clients_by_liquidity_and_contact_days",
  "description": "Return clients sorted by free liquidity (descending) with optional filter for clients with no contact in last N days.",
  "parameters": {
    "min_liquidity_chf": {"type": "number", "description": "Optional minimum liquidity in CHF"},
    "max_last_contact_days": {"type": "integer", "description": "Only include clients with last contact older than this many days (e.g., 90)"},
    "limit": {"type": "integer", "description": "Maximum number of clients to return"}
  }
}