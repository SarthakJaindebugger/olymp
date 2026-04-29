
# Apollo Query Layer

A natural language query layer for the Etops CRM API – built for the Olymp AG case study.

**Stack:** Flask + React(TypeScript) + SQLite + OpenAI GPT-3.5 Turbo/ Ollama(gpt 120b oss cloud)

---

## Architecture

```
User Question → React Frontend → Flask Backend → LLM (Tool Call) → SQLite Query → Ranked Results
                                                                           ↓
                                                              Tool Trace (Audit)
```

**How it works:**
1. **Background sync** – Fetches 50 mock clients into SQLite (every 5 min)
2. **LLM orchestrates** – Converts natural language → deterministic tool call
3. **SQL query** – Executes indexed query (<50ms)
4. **Tool trace** – Shows exact SQL for FINMA audit compliance

**NOT RAG** – LLM never retrieves or guesses data. Backend computes everything.

---

## Quick Start

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Backend runs on `http://localhost:5000`

### 2. Frontend

```bash
cd react_frontend
npm install
npm start
```

Frontend runs on `http://localhost:3000`

### 3. Environment (Optional)

Create `backend/.env` for OpenAI:

## Inorder to change the API key, navigate to the below path and change line number 184
```
olymp/backend/services/llm.py
```

Or use Ollama locally (no key needed).

---

## Project Structure

```
olymp/
├── backend/
│   ├── app.py              # Flask server, /chat endpoint
│   ├── services/           # Core logic (aggregation, db, llm)
│   ├── mock_data.json      # 50 mock clients
│   ├── apollo.db           # SQLite database (auto-created)
│   └── requirements.txt
├── react_frontend/
│   ├── src/                # React components
│   └── package.json
└── README.md
```

---

## Example Query

**Ask:** *"Which clients have highest liquidity and no contact in the last 90 days?"*

**Response:** Ranked table of 10 clients with tool trace for audit.

---

## Key Design

| Problem | Solution |
|---------|----------|
| O(N) fanout (250 API calls per query) | Local SQLite with background sync |
| LLM hallucination | Deterministic tool calling (NOT RAG) |
| FINMA audit requirements | Tool trace shows exact SQL |
| Privacy concerns | Dual LLM support (OpenAI or Ollama) |

---

## Notes

- Mock data only (no live Etops credentials needed)
- SQLite indexes on `free_liquidity_chf` and `last_contact_days`
- Streaming status messages in chat
- Collapsible tool trace for compliance

```

---

## What This README Includes

| Section | Content |
|---------|---------|
| Architecture | One-line flow diagram |
| Quick Start | Backend + frontend commands |
| Project Structure | Matches your screenshot exactly |
| Example Query | The user story question |
| Key Design | O(N) → SQLite, NOT RAG, audit |
| Notes | Mock data, indexes, streaming |

