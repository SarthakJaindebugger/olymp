import json
import os
from typing import Any, Callable, Dict, List

import requests


class OllamaToolAgent:
    def __init__(self, tool_registry: Dict[str, Callable[..., Any]]) -> None:
        self.tool_registry = tool_registry
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "gpt oss 120b cloud")

    def chat_with_tools(self, user_text: str) -> Dict[str, Any]:
        system_prompt = (
            "You are Apollo Assistant. Always use tools for numeric/client ranking questions. "
            "Never invent results. Summarize tool output concisely and include client_id references."
        )

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ]

        tool_trace: List[Dict[str, Any]] = []

        for _ in range(4):
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "tools": self._tool_schema(),
            }
            response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=45)
            response.raise_for_status()
            body = response.json()
            assistant_message = body.get("message", {})
            messages.append(assistant_message)

            tool_calls = assistant_message.get("tool_calls") or []
            if not tool_calls:
                return {
                    "answer": assistant_message.get("content", "No response generated."),
                    "tool_trace": tool_trace,
                }

            for call in tool_calls:
                tool_name = call["function"]["name"]
                raw_args = call["function"].get("arguments", {})
                args = raw_args if isinstance(raw_args, dict) else json.loads(raw_args or "{}")

                result = self.tool_registry[tool_name](**args)
                tool_trace.append({"tool": tool_name, "args": args, "result_preview": str(result)[:280]})

                messages.append(
                    {
                        "role": "tool",
                        "name": tool_name,
                        "content": json.dumps(result),
                    }
                )

        return {
            "answer": "Reached tool-calling iteration limit. Please refine the question.",
            "tool_trace": tool_trace,
        }

    def _tool_schema(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "query_liquidity_and_stale_contacts",
                    "description": "Find top clients by free liquidity and return subset with no contact in N days.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer", "description": "Top N clients by liquidity", "default": 5},
                            "inactivity_days": {
                                "type": "integer",
                                "description": "Days since last contact threshold",
                                "default": 90,
                            },
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_top_liquidity_clients",
                    "description": "Return top N clients sorted by free liquidity.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer", "default": 5},
                        },
                    },
                },
            },
        ]
