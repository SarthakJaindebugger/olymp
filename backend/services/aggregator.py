import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Sequence

from .etops_client import EtopsClient

from .db import get_connection


class AggregationService:
    def __init__(self, etops_client: EtopsClient, cache_ttl_seconds: int = 30) -> None:
        self.etops_client = etops_client
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: Dict[str, Any] = {"expires_at": 0.0, "clients": []}

    # def _get_all_client_profiles(self) -> List[Dict[str, Any]]:
    #     now = time.time()
    #     if now < self._cache["expires_at"]:
    #         return list(self._cache["clients"])

    #     client_refs = self.etops_client.list_clients()
    #     profiles: List[Dict[str, Any]] = []

    #     with ThreadPoolExecutor(max_workers=12) as pool:
    #         futures = {
    #             pool.submit(self.etops_client.fetch_client_profile, c["client_id"]): c["client_id"]
    #             for c in client_refs
    #         }
    #         for future in as_completed(futures):
    #             profile = future.result()
    #             if profile:
    #                 profiles.append(profile)

    #     self._cache = {
    #         "expires_at": now + self.cache_ttl_seconds,
    #         "clients": profiles,
    #     }
    #     return profiles

    # def top_liquidity_clients(self, limit: int = 5) -> List[Dict[str, Any]]:
    #     clients = self._get_all_client_profiles()
    #     ranked = sorted(clients, key=lambda c: c.get("free_liquidity_chf", 0), reverse=True)
    #     return ranked[: max(1, min(limit, 50))]

    def top_liquidity_clients(self, limit=5):

        conn = get_connection()

        rows = conn.execute("""
        SELECT *
        FROM clients
        ORDER BY free_liquidity_chf DESC
        LIMIT ?
        """, (limit,)).fetchall()

        conn.close()

        return [dict(r) for r in rows]

    # def clients_without_recent_contact(
    #     self, client_ids: Sequence[str], days: int = 90
    # ) -> List[Dict[str, Any]]:
    #     candidates = self._get_all_client_profiles()
    #     candidate_map = {c["client_id"]: c for c in candidates}
    #     result = []
    #     for client_id in client_ids:
    #         c = candidate_map.get(client_id)
    #         if c and c.get("last_contact_days", 0) > days:
    #             result.append(c)
    #     return sorted(result, key=lambda c: c.get("free_liquidity_chf", 0), reverse=True)


    def clients_without_recent_contact(
        self, client_ids: Sequence[str], days: int = 90
    ) -> List[Dict[str, Any]]:
        """Uses SQLite – NO _get_all_client_profiles() call."""
        from .db import get_clients_by_ids
        
        if not client_ids:
            return []
        
        # Get ALL requested clients from DB
        all_clients = get_clients_by_ids(list(client_ids))
        
        # Filter and sort (still efficient because DB already indexed)
        filtered = [c for c in all_clients if c.get("last_contact_days", 0) > days]
        return sorted(filtered, key=lambda c: c.get("free_liquidity_chf", 0), reverse=True)

    # def liquidity_and_stale_contacts(self, limit: int = 5, inactivity_days: int = 90) -> Dict[str, Any]:
    #     top = self.top_liquidity_clients(limit=limit)
    #     stale = self.clients_without_recent_contact(
    #         client_ids=[c["client_id"] for c in top], days=inactivity_days
    #     )
    #     return {
    #         "top_liquidity_clients": top,
    #         "stale_contact_subset": stale,
    #         "filters": {"limit": limit, "inactivity_days": inactivity_days},
    #     }


    def liquidity_and_stale_contacts(
        self,
        limit=5,
        inactivity_days=90
    ):

        conn = get_connection()

        rows = conn.execute("""
        SELECT *
        FROM clients
        WHERE last_contact_days > ?
        ORDER BY free_liquidity_chf DESC
        LIMIT ?
        """, (inactivity_days, limit)).fetchall()

        conn.close()

        return {
            "top_liquidity_clients": [dict(r) for r in rows],
            "filters": {
                "limit": limit,
                "inactivity_days": inactivity_days,
            },
        }



    # def query_clients(
    #     self,
    #     limit: int = 5,
    #     sort_by: str = "free_liquidity_chf",
    #     order: str = "desc",
    #     min_last_contact_days: Optional[int] = None,
    # ) -> Dict[str, Any]:
    #     clients = self._get_all_client_profiles()

    #     if min_last_contact_days is not None:
    #         clients = [c for c in clients if c.get("last_contact_days", 0) >= min_last_contact_days]

    #     sort_by = sort_by.lower()
    #     if sort_by == "first_name":
    #         key_fn = lambda c: c.get("name", "").split(" ")[0].lower()
    #     else:
    #         key_fn = lambda c: c.get(sort_by, 0)

    #     reverse = order.lower() == "desc"
    #     sorted_clients = sorted(clients, key=key_fn, reverse=reverse)

    #     return {
    #         "rows": sorted_clients[: max(1, min(limit, 100))],
    #         "filters": {
    #             "limit": limit,
    #             "sort_by": sort_by,
    #             "order": order,
    #             "min_last_contact_days": min_last_contact_days,
    #         },
    #     }

    def query_clients(
        self,
        limit: int = 10,
        sort_by: str = "free_liquidity_chf",
        order: str = "desc",
        min_last_contact_days: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Uses SQLite – single query, no Python sorting."""
        from .db import query_clients_sql
        
        rows = query_clients_sql(
            limit=limit,
            min_last_contact_days=min_last_contact_days,
            sort_by=sort_by if sort_by != "first_name" else "name",
            order=order,
        )
        
        return {
            "rows": rows,
            "filters": {
                "limit": limit,
                "sort_by": sort_by,
                "order": order,
                "min_last_contact_days": min_last_contact_days,
            },
        }

