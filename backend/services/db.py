# import sqlite3
# from pathlib import Path

# DB_PATH = Path(__file__).resolve().parent.parent / "apollo.db"


# def get_connection():
#     conn = sqlite3.connect(DB_PATH)
#     conn.row_factory = sqlite3.Row
#     return conn


# def init_db():
#     conn = get_connection()

#     conn.execute("""
#     CREATE TABLE IF NOT EXISTS clients (
#         client_id TEXT PRIMARY KEY,
#         name TEXT,
#         free_liquidity_chf REAL,
#         last_contact_days INTEGER,
#         aum_chf REAL,
#         risk_class TEXT,
#         synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#     )
#     """)

#     conn.commit()
#     conn.close()




import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "apollo.db"


def get_connection():
    """Returns a database connection with row_factory set to Row (dict-like access)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Creates the clients table with indexes if it doesn't exist."""
    conn = get_connection()

    # Create clients table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        client_id TEXT PRIMARY KEY,
        name TEXT,
        free_liquidity_chf REAL,
        last_contact_days INTEGER,
        aum_chf REAL,
        risk_class TEXT,
        synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create indexes for fast query performance
    conn.execute("CREATE INDEX IF NOT EXISTS idx_liquidity ON clients(free_liquidity_chf DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_contact_days ON clients(last_contact_days)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_risk_aum ON clients(risk_class, aum_chf DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_client_id ON clients(client_id)")

    conn.commit()
    conn.close()
    print("✅ Database initialized with indexes")


def sync_clients_from_mock():
    """
    Syncs all clients from mock_etops into SQLite.
    This replaces the O(N) fanout with a single batch write.
    Call this every 5 minutes in production.
    """
    from .mock_etops import get_all_clients  # Import here to avoid circular import
    
    clients = get_all_clients()  # Your mock data source
    
    if not clients:
        print("⚠️ No clients found in mock data")
        return 0
    
    conn = get_connection()
    updated_count = 0
    
    for client in clients:
        # Handle both possible key names (client_id vs id)
        client_id = client.get("client_id") or client.get("id")
        if not client_id:
            continue
            
        conn.execute("""
            INSERT OR REPLACE INTO clients 
            (client_id, name, free_liquidity_chf, last_contact_days, aum_chf, risk_class, synced_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            str(client_id),
            client.get("name", f"Client {client_id}"),
            float(client.get("free_liquidity_chf") or client.get("free_liquidity", 0)),
            int(client.get("last_contact_days", 0)),
            float(client.get("aum_chf", 0)),
            client.get("risk_class", "standard"),
        ))
        updated_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"🔄 Synced {updated_count} clients to database")
    return updated_count


def get_sync_status() -> Dict[str, Any]:
    """Returns the last sync time and record count."""
    conn = get_connection()
    
    # Get latest sync timestamp
    cursor = conn.execute("""
        SELECT MAX(synced_at) as last_sync, COUNT(*) as total_clients
        FROM clients
    """)
    row = cursor.fetchone()
    conn.close()
    
    return {
        "last_sync": row["last_sync"] if row else None,
        "total_clients": row["total_clients"] if row else 0,
    }


def query_clients_sql(
    limit: int = 10,
    min_last_contact_days: Optional[int] = None,
    sort_by: str = "free_liquidity_chf",
    order: str = "DESC",
    client_ids: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Reusable SQL query function for clients.
    This is what replaces ALL _get_all_client_profiles() calls.
    """
    conn = get_connection()
    
    # Base query
    query = "SELECT * FROM clients WHERE 1=1"
    params = []
    
    # Filter by client IDs (for clients_without_recent_contact)
    if client_ids:
        placeholders = ','.join(['?' for _ in client_ids])
        query += f" AND client_id IN ({placeholders})"
        params.extend(client_ids)
    
    # Filter by last contact days
    if min_last_contact_days is not None:
        query += " AND last_contact_days >= ?"
        params.append(min_last_contact_days)
    
    # Validate sort column to prevent SQL injection
    allowed_sort_columns = {
        "free_liquidity_chf", "last_contact_days", "name", 
        "aum_chf", "risk_class", "client_id"
    }
    if sort_by not in allowed_sort_columns:
        sort_by = "free_liquidity_chf"
    
    # Add ordering and limit
    order_dir = "DESC" if order.upper() == "DESC" else "ASC"
    query += f" ORDER BY {sort_by} {order_dir} LIMIT ?"
    params.append(max(1, min(limit, 100)))  # Clamp between 1 and 100
    
    cursor = conn.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return results


def get_clients_by_ids(client_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch specific clients by their IDs.
    Used by clients_without_recent_contact function.
    """
    if not client_ids:
        return []
    
    conn = get_connection()
    placeholders = ','.join(['?' for _ in client_ids])
    cursor = conn.execute(f"""
        SELECT *
        FROM clients
        WHERE client_id IN ({placeholders})
        ORDER BY free_liquidity_chf DESC
    """, client_ids)
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results