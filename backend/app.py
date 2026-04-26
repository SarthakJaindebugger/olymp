import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from services.aggregator import AggregationService
from services.etops_client import EtopsClient
from services.llm import OllamaToolAgent

load_dotenv()

# In local development the React TypeScript app runs via Vite (react_frontend/).
# If `react_frontend/dist` exists, Flask can serve that built app.
dist_path = Path(__file__).resolve().parent.parent / "react_frontend" / "dist"
app = Flask(__name__, static_folder=str(dist_path), static_url_path="")
CORS(app)

etops_client = EtopsClient()
aggregator = AggregationService(etops_client)


def _tool_query_liquidity_and_stale_contacts(limit: int = 5, inactivity_days: int = 90):
    return aggregator.liquidity_and_stale_contacts(limit=limit, inactivity_days=inactivity_days)


def _tool_get_top_liquidity_clients(limit: int = 5):
    return aggregator.top_liquidity_clients(limit=limit)


agent = OllamaToolAgent(
    tool_registry={
        "query_liquidity_and_stale_contacts": _tool_query_liquidity_and_stale_contacts,
        "get_top_liquidity_clients": _tool_get_top_liquidity_clients,
    }
)


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "live_etops_mode": etops_client.is_live_mode})


@app.get("/api/aggregation/liquidity")
def top_liquidity():
    limit = int(request.args.get("limit", 5))
    return jsonify({"rows": aggregator.top_liquidity_clients(limit=limit)})


@app.post("/api/chat")
def chat():
    payload = request.get_json(force=True)
    user_message = payload.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "message is required"}), 400

    try:
        result = agent.chat_with_tools(user_message)
        return jsonify(result)
    except Exception as exc:  # noqa: BLE001 - prototype-grade error handling
        return jsonify({"error": str(exc)}), 500


@app.get("/")
def serve_frontend():
    index_path = Path(app.static_folder) / "index.html"
    if index_path.exists():
        return send_from_directory(app.static_folder, "index.html")

    return jsonify(
        {
            "message": "Frontend is in react_frontend/. Run `cd react_frontend && npm install && npm run dev` for local UI, or build it with `npm run build` to serve from Flask."
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
