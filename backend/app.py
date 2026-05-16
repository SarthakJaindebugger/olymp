import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from services.aggregator import AggregationService
from services.db import init_db
from services.etops_client import EtopsClient
from services.orchestrator import ConversationalQueryOrchestrator
from services.sync_service import SyncService

load_dotenv()

dist_path = Path(__file__).resolve().parent.parent / "react_frontend" / "dist"
app = Flask(__name__, static_folder=str(dist_path), static_url_path="")
CORS(app)

etops_client = EtopsClient()
init_db()

sync_service = SyncService(etops_client)
sync_service.sync_clients()

aggregator = AggregationService(etops_client)
orchestrator = ConversationalQueryOrchestrator(aggregator)


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "live_etops_mode": etops_client.is_live_mode})


@app.get("/api/aggregation/liquidity")
def top_liquidity():
    limit = int(request.args.get("limit", 5))
    return jsonify({"rows": aggregator.top_liquidity_clients(limit=limit)})


@app.get("/api/aggregation/query")
def query_clients():
    limit = int(request.args.get("limit", 5))
    sort_by = request.args.get("sort_by", "free_liquidity_chf")
    order = request.args.get("order", "desc")
    min_last_contact_days = request.args.get("min_last_contact_days")
    parsed_min = int(min_last_contact_days) if min_last_contact_days is not None else None
    return jsonify(
        aggregator.query_clients(
            limit=limit, sort_by=sort_by, order=order, min_last_contact_days=parsed_min
        )
    )


@app.post("/api/chat")
def chat():
    payload = request.get_json(force=True)
    user_message = payload.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "message is required"}), 400

    try:
        result = orchestrator.execute(user_message)
        return jsonify(result)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 500


@app.post("/api/sync")
def sync():
    result = sync_service.sync_clients()
    return jsonify(result)


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
