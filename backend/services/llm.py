
# --------CODE WITH OLLAMA LOCAL SETUP-----------------

# import json
# import os
# from typing import Any, Callable, Dict, List

# import requests


# class OllamaToolAgent:
#     def __init__(self, tool_registry: Dict[str, Callable[..., Any]]) -> None:
#         self.tool_registry = tool_registry
#         self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
#         self.model = os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")
#         self.fallback_model = os.getenv("OLLAMA_FALLBACK_MODEL", "llama3.1:8b")

#     def chat_with_tools(self, user_text: str) -> Dict[str, Any]:
#         system_prompt = (
#             "You are Apollo Assistant. Use tools for ranking/filtering questions and return plain readable text. "
#             "Do not use markdown tables, **bold markers**, or code fences in final answers. "
#             "Always include client_id references when returning client rows."
#         )

#         messages: List[Dict[str, Any]] = [
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": user_text},
#         ]

#         tool_trace: List[Dict[str, Any]] = []
#         model_in_use = self.model

#         for _ in range(4):
#             payload = {
#                 "model": model_in_use,
#                 "messages": messages,
#                 "stream": False,
#                 "tools": self._tool_schema(),
#             }

#             try:
#                 body = self._request_chat(payload)
#             except RuntimeError as error:
#                 if model_in_use != self.fallback_model and self.fallback_model:
#                     model_in_use = self.fallback_model
#                     body = self._request_chat({**payload, "model": model_in_use})
#                 else:
#                     return self._heuristic_fallback(user_text, str(error))

#             assistant_message = body.get("message", {})
#             messages.append(assistant_message)

#             tool_calls = assistant_message.get("tool_calls") or []
#             if not tool_calls:
#                 clean = assistant_message.get("content", "No response generated.")
#                 clean = clean.replace("**", "")
#                 return {"answer": clean, "tool_trace": tool_trace}

#             for call in tool_calls:
#                 tool_name = call["function"]["name"]
#                 raw_args = call["function"].get("arguments", {})
#                 args = raw_args if isinstance(raw_args, dict) else json.loads(raw_args or "{}")

#                 result = self.tool_registry[tool_name](**args)
#                 tool_trace.append(
#                     {
#                         "tool": tool_name,
#                         "args": args,
#                         "result_preview": str(result)[:280],
#                         "model": model_in_use,
#                     }
#                 )

#                 messages.append(
#                     {
#                         "role": "tool",
#                         "name": tool_name,
#                         "content": json.dumps(result),
#                     }
#                 )

#         return {
#             "answer": "Reached tool-calling iteration limit. Please refine the question.",
#             "tool_trace": tool_trace,
#         }

#     def _request_chat(self, payload: Dict[str, Any]) -> Dict[str, Any]:
#         response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=45)
#         if response.status_code >= 400:
#             detail = response.text.strip()
#             raise RuntimeError(f"Ollama request failed ({response.status_code}): {detail}")
#         return response.json()

#     def _heuristic_fallback(self, user_text: str, error_message: str) -> Dict[str, Any]:
#         text = user_text.lower()
#         if "liquidity" in text and ("contact" in text or "90" in text):
#             result = self.tool_registry["query_liquidity_and_stale_contacts"](limit=5, inactivity_days=90)
#             answer = (
#                 "Ollama was unavailable, so deterministic backend tools were used directly. "
#                 "Returned top liquidity clients and the subset with no contact in 90 days."
#             )
#             return {
#                 "answer": answer,
#                 "tool_trace": [
#                     {
#                         "tool": "query_liquidity_and_stale_contacts",
#                         "args": {"limit": 5, "inactivity_days": 90},
#                         "result_preview": str(result)[:280],
#                         "fallback_reason": error_message,
#                     }
#                 ],
#             }

#         return {
#             "answer": f"LLM call failed and no deterministic fallback matched this prompt. {error_message}",
#             "tool_trace": [],
#         }

#     def _tool_schema(self) -> List[Dict[str, Any]]:
#         return [
#             {
#                 "type": "function",
#                 "function": {
#                     "name": "query_liquidity_and_stale_contacts",
#                     "description": "Find top clients by free liquidity and return subset with no contact in N days.",
#                     "parameters": {
#                         "type": "object",
#                         "properties": {
#                             "limit": {"type": "integer", "description": "Top N clients by liquidity", "default": 5},
#                             "inactivity_days": {
#                                 "type": "integer",
#                                 "description": "Days since last contact threshold",
#                                 "default": 90,
#                             },
#                         },
#                     },
#                 },
#             },
#             {
#                 "type": "function",
#                 "function": {
#                     "name": "get_top_liquidity_clients",
#                     "description": "Return top N clients sorted by free liquidity.",
#                     "parameters": {
#                         "type": "object",
#                         "properties": {
#                             "limit": {"type": "integer", "default": 5},
#                         },
#                     },
#                 },
#             },
#             {
#                 "type": "function",
#                 "function": {
#                     "name": "query_clients",
#                     "description": "Generic client query with sorting/filtering. Supports sort_by: free_liquidity_chf, last_contact_days, name, first_name.",
#                     "parameters": {
#                         "type": "object",
#                         "properties": {
#                             "limit": {"type": "integer", "default": 5},
#                             "sort_by": {"type": "string", "default": "free_liquidity_chf"},
#                             "order": {"type": "string", "enum": ["asc", "desc"], "default": "desc"},
#                             "min_last_contact_days": {"type": "integer"},
#                         },
#                     },
#                 },
#             },
#         ]



# --------CODE WITH OPENAI API KEY PROVIDED-----------------

import json
import os
from typing import Any, Callable, Dict, List

import requests


class OpenAIToolAgent:
    def __init__(self, tool_registry: Dict[str, Callable[..., Any]]) -> None:
        self.tool_registry = tool_registry
        self.api_key = os.getenv("OPENAI_API_KEY", "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")
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")  # Use gpt-3.5-turbo for cost efficiency
        self.fallback_model = os.getenv("OPENAI_FALLBACK_MODEL", "gpt-3.5-turbo")  # Same fallback

    def chat_with_tools(self, user_text: str) -> Dict[str, Any]:
        system_prompt = (
            "You are Apollo Assistant. Use tools for ranking/filtering questions and return plain readable text. "
            "Do not use markdown tables, **bold markers**, or code fences in final answers. "
            "Always include client_id references when returning client rows."
        )

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ]

        tool_trace: List[Dict[str, Any]] = []
        model_in_use = self.model

        for _ in range(4):
            payload = {
                "model": model_in_use,
                "messages": messages,
                "tools": self._tool_schema(),
                "tool_choice": "auto",  # Let the model decide when to use tools
            }

            try:
                body = self._request_chat(payload)
            except RuntimeError as error:
                if model_in_use != self.fallback_model and self.fallback_model:
                    model_in_use = self.fallback_model
                    body = self._request_chat({**payload, "model": model_in_use})
                else:
                    return self._heuristic_fallback(user_text, str(error))

            assistant_message = body.get("choices", [{}])[0].get("message", {})
            messages.append(assistant_message)

            tool_calls = assistant_message.get("tool_calls") or []
            if not tool_calls:
                clean = assistant_message.get("content", "No response generated.")
                clean = clean.replace("**", "")
                return {"answer": clean, "tool_trace": tool_trace}

            for call in tool_calls:
                tool_name = call["function"]["name"]
                raw_args = call["function"].get("arguments", {})
                args = raw_args if isinstance(raw_args, dict) else json.loads(raw_args or "{}")

                result = self.tool_registry[tool_name](**args)
                tool_trace.append(
                    {
                        "tool": tool_name,
                        "args": args,
                        "result_preview": str(result)[:280],
                        "model": model_in_use,
                    }
                )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call["id"],  # Required by OpenAI API
                        "name": tool_name,
                        "content": json.dumps(result),
                    }
                )

        return {
            "answer": "Reached tool-calling iteration limit. Please refine the question.",
            "tool_trace": tool_trace,
        }

    def _request_chat(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Remove 'stream' if present, OpenAI handles it differently
        payload.pop("stream", None)
        
        response = requests.post(self.base_url, json=payload, headers=headers, timeout=45)
        
        if response.status_code >= 400:
            detail = response.text.strip()
            raise RuntimeError(f"OpenAI API request failed ({response.status_code}): {detail}")
        
        resp_json = response.json()
        
        # Check for OpenAI specific error format
        if "error" in resp_json:
            raise RuntimeError(f"OpenAI API error: {resp_json['error']}")
            
        return resp_json

    def _heuristic_fallback(self, user_text: str, error_message: str) -> Dict[str, Any]:
        text = user_text.lower()
        if "liquidity" in text and ("contact" in text or "90" in text):
            result = self.tool_registry["query_liquidity_and_stale_contacts"](limit=5, inactivity_days=90)
            answer = (
                "OpenAI was unavailable, so deterministic backend tools were used directly. "
                "Returned top liquidity clients and the subset with no contact in 90 days."
            )
            return {
                "answer": answer,
                "tool_trace": [
                    {
                        "tool": "query_liquidity_and_stale_contacts",
                        "args": {"limit": 5, "inactivity_days": 90},
                        "result_preview": str(result)[:280],
                        "fallback_reason": error_message,
                    }
                ],
            }

        return {
            "answer": f"LLM call failed and no deterministic fallback matched this prompt. {error_message}",
            "tool_trace": [],
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
            {
                "type": "function",
                "function": {
                    "name": "query_clients",
                    "description": "Generic client query with sorting/filtering. Supports sort_by: free_liquidity_chf, last_contact_days, name, first_name.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer", "default": 5},
                            "sort_by": {"type": "string", "default": "free_liquidity_chf"},
                            "order": {"type": "string", "enum": ["asc", "desc"], "default": "desc"},
                            "min_last_contact_days": {"type": "integer"},
                        },
                    },
                },
            },
        ]


# Simple test function
def test_openai_agent():
    # Mock tool functions for testing
    def mock_query_liquidity_and_stale_contacts(limit=5, inactivity_days=90):
        return {
            "top_clients": [{"client_id": 1, "name": "Client A", "liquidity": 50000}],
            "stale_clients": [{"client_id": 2, "name": "Client B", "last_contact": 95}]
        }
    
    def mock_get_top_liquidity_clients(limit=5):
        return [{"client_id": i, "liquidity": 100000 - i * 10000} for i in range(1, limit+1)]
    
    def mock_query_clients(limit=5, sort_by="free_liquidity_chf", order="desc", min_last_contact_days=None):
        return [{"client_id": i, "name": f"Client {i}", "liquidity": 50000 - i * 5000} for i in range(1, limit+1)]
    
    tool_registry = {
        "query_liquidity_and_stale_contacts": mock_query_liquidity_and_stale_contacts,
        "get_top_liquidity_clients": mock_get_top_liquidity_clients,
        "query_clients": mock_query_clients,
    }
    
    agent = OpenAIToolAgent(tool_registry)
    
    # Test the agent
    result = agent.chat_with_tools("Show me top 3 clients by liquidity")
    print("Answer:", result["answer"])
    print("Tool trace:", result["tool_trace"])


if __name__ == "__main__":
    test_openai_agent()