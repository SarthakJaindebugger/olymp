import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


class EtopsClient:
    """Adapter around Etops CRM API with a mock fallback.

    The real API branch is intentionally lightweight because candidate credentials
    are unavailable for this take-home. If ETOPS_TOKEN and ETOPS_BASE_URL are set,
    this client can be pointed to live endpoints.
    """

    def __init__(self) -> None:
        self.base_url = os.getenv("ETOPS_BASE_URL", "").rstrip("/")
        self.token = os.getenv("ETOPS_TOKEN", "")
        mock_path = Path(__file__).resolve().parent.parent / "mock_data.json"
        self._mock_clients: List[Dict[str, Any]] = json.loads(mock_path.read_text())

    @property
    def is_live_mode(self) -> bool:
        return bool(self.base_url and self.token)

    def list_clients(self) -> List[Dict[str, Any]]:
        if not self.is_live_mode:
            time.sleep(0.05)
            return [{"client_id": c["client_id"], "name": c["name"]} for c in self._mock_clients]

        url = f"{self.base_url}/clients"
        response = requests.get(url, headers=self._headers(), timeout=8)
        response.raise_for_status()
        return response.json()

    def fetch_client_profile(self, client_id: str) -> Optional[Dict[str, Any]]:
        if not self.is_live_mode:
            time.sleep(0.03)
            return next((c for c in self._mock_clients if c["client_id"] == client_id), None)

        url = f"{self.base_url}/clients/{client_id}"
        response = requests.get(url, headers=self._headers(), timeout=8)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token}", "Accept": "application/json"}
