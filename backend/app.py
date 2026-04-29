# --------CODE WITH OLLAMA LOCAL SETUP-----------------

# import os
# from pathlib import Path

# from dotenv import load_dotenv
# from flask import Flask, jsonify, request, send_from_directory
# from flask_cors import CORS

# from services.aggregator import AggregationService
# from services.etops_client import EtopsClient
# from services.llm import OllamaToolAgent

# load_dotenv()

# # In local development the React TypeScript app runs via Vite (react_frontend/).
# # If `react_frontend/dist` exists, Flask can serve that built app.
# dist_path = Path(__file__).resolve().parent.parent / "react_frontend" / "dist"
# app = Flask(__name__, static_folder=str(dist_path), static_url_path="")
# CORS(app)

# etops_client = EtopsClient()
# aggregator = AggregationService(etops_client)


# def _tool_query_liquidity_and_stale_contacts(limit: int = 5, inactivity_days: int = 90):
#     return aggregator.liquidity_and_stale_contacts(limit=limit, inactivity_days=inactivity_days)


# def _tool_get_top_liquidity_clients(limit: int = 5):
#     return aggregator.top_liquidity_clients(limit=limit)


# def _tool_query_clients(limit: int = 5, sort_by: str = "free_liquidity_chf", order: str = "desc", min_last_contact_days=None):
#     return aggregator.query_clients(
#         limit=limit,
#         sort_by=sort_by,
#         order=order,
#         min_last_contact_days=min_last_contact_days,
#     )

# agent = OllamaToolAgent(
#     tool_registry={
#         "query_liquidity_and_stale_contacts": _tool_query_liquidity_and_stale_contacts,
#         "get_top_liquidity_clients": _tool_get_top_liquidity_clients,
#         "query_clients": _tool_query_clients,
#     }
# )


# @app.get("/api/health")
# def health():
#     return jsonify({"ok": True, "live_etops_mode": etops_client.is_live_mode})


# @app.get("/api/aggregation/liquidity")
# def top_liquidity():
#     limit = int(request.args.get("limit", 5))
#     return jsonify({"rows": aggregator.top_liquidity_clients(limit=limit)})




# @app.get("/api/aggregation/query")
# def query_clients():
#     limit = int(request.args.get("limit", 5))
#     sort_by = request.args.get("sort_by", "free_liquidity_chf")
#     order = request.args.get("order", "desc")
#     min_last_contact_days = request.args.get("min_last_contact_days")
#     parsed_min = int(min_last_contact_days) if min_last_contact_days is not None else None
#     return jsonify(
#         aggregator.query_clients(
#             limit=limit, sort_by=sort_by, order=order, min_last_contact_days=parsed_min
#         )
#     )

# @app.post("/api/chat")
# def chat():
#     payload = request.get_json(force=True)
#     user_message = payload.get("message", "").strip()
#     if not user_message:
#         return jsonify({"error": "message is required"}), 400

#     try:
#         result = agent.chat_with_tools(user_message)
#         return jsonify(result)
#     except Exception as exc:  # noqa: BLE001 - prototype-grade error handling
#         return jsonify({"error": str(exc)}), 500


# @app.get("/")
# def serve_frontend():
#     index_path = Path(app.static_folder) / "index.html"
#     if index_path.exists():
#         return send_from_directory(app.static_folder, "index.html")

#     return jsonify(
#         {
#             "message": "Frontend is in react_frontend/. Run `cd react_frontend && npm install && npm run dev` for local UI, or build it with `npm run build` to serve from Flask."
#         }
#     )


# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)





# --------CODE WITH OPENAI API KEY PROVIDED-----------------
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from services.aggregator import AggregationService
from services.etops_client import EtopsClient
from services.llm import OpenAIToolAgent  # Changed from OllamaToolAgent

from services.db import init_db
from services.sync_service import SyncService


load_dotenv()

# In local development the React TypeScript app runs via Vite (react_frontend/).
# If `react_frontend/dist` exists, Flask can serve that built app.
dist_path = Path(__file__).resolve().parent.parent / "react_frontend" / "dist"
app = Flask(__name__, static_folder=str(dist_path), static_url_path="")
CORS(app)

etops_client = EtopsClient()

# Added 
init_db()

sync_service = SyncService(etops_client)
sync_service.sync_clients()


aggregator = AggregationService(etops_client)


def _tool_query_liquidity_and_stale_contacts(limit: int = 5, inactivity_days: int = 90):
    return aggregator.liquidity_and_stale_contacts(limit=limit, inactivity_days=inactivity_days)


def _tool_get_top_liquidity_clients(limit: int = 5):
    return aggregator.top_liquidity_clients(limit=limit)


def _tool_query_clients(limit: int = 5, sort_by: str = "free_liquidity_chf", order: str = "desc", min_last_contact_days=None):
    return aggregator.query_clients(
        limit=limit,
        sort_by=sort_by,
        order=order,
        min_last_contact_days=min_last_contact_days,
    )

# Changed from OllamaToolAgent to OpenAIToolAgent
agent = OpenAIToolAgent(
    tool_registry={
        "query_liquidity_and_stale_contacts": _tool_query_liquidity_and_stale_contacts,
        "get_top_liquidity_clients": _tool_get_top_liquidity_clients,
        "query_clients": _tool_query_clients,
    }
)


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
        result = agent.chat_with_tools(user_message)
        return jsonify(result)
    except Exception as exc:  # noqa: BLE001 - prototype-grade error handling
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