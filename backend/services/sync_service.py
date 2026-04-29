from concurrent.futures import ThreadPoolExecutor, as_completed

from .db import get_connection
from .etops_client import EtopsClient


class SyncService:
    def __init__(self, etops_client: EtopsClient):
        self.etops_client = etops_client

    def sync_clients(self):
        client_refs = self.etops_client.list_clients()

        profiles = []

        with ThreadPoolExecutor(max_workers=12) as pool:
            futures = {
                pool.submit(
                    self.etops_client.fetch_client_profile,
                    c["client_id"]
                ): c["client_id"]
                for c in client_refs
            }

            for future in as_completed(futures):
                profile = future.result()
                if profile:
                    profiles.append(profile)

        conn = get_connection()

        for p in profiles:
            conn.execute("""
            INSERT OR REPLACE INTO clients (
                client_id,
                name,
                free_liquidity_chf,
                last_contact_days,
                aum_chf,
                risk_class
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                p["client_id"],
                p["name"],
                p.get("free_liquidity_chf", 0),
                p.get("last_contact_days", 0),
                p.get("aum_chf", 0),
                p.get("risk_class", "")
            ))

        conn.commit()
        conn.close()

        return {
            "synced_clients": len(profiles)
        }