"""
Single-table storage layer, deliberately shaped like a DynamoDB table
(pk, sk, entity_type, data-as-JSON) so it can later be swapped for
real DynamoDB via boto3 with minimal code change elsewhere in the app.

Key patterns used by this app:
    PATIENT#<id> | METADATA        -> patient profile
    PATIENT#<id> | EVAL#<iso-ts>   -> a stored DischargeReadinessEvaluation
    PATIENT#<id> | TASK#<task_id>  -> a discharge task
    PATIENT#<id> | AUDIT#<iso-ts>  -> an audit log entry
    PATIENT#<id> | SIGNOFF         -> current signoff status object
"""
import sqlite3
import json
import os
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

DB_PATH = os.getenv("DB_PATH", "discharge.db")


def init_db(db_path: Optional[str] = None) -> None:
    """Create the table if it doesn't exist. Safe to call on every startup."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS records (
            pk TEXT NOT NULL,
            sk TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            data TEXT NOT NULL,
            PRIMARY KEY (pk, sk)
        )
        """
    )
    # Index on sk lets us look up a task by its id alone, without knowing
    # its parent patient's pk -- the local stand-in for a DynamoDB GSI.
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sk ON records(sk)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_entity_type ON records(entity_type)")
    conn.commit()
    conn.close()


@contextmanager
def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def _row_to_item(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "pk": row["pk"],
        "sk": row["sk"],
        "entity_type": row["entity_type"],
        "data": json.loads(row["data"]),
    }


def put_item(pk: str, sk: str, entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Upsert. Overwrites any existing item at the same (pk, sk)."""
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO records (pk, sk, entity_type, data) VALUES (?, ?, ?, ?)
            ON CONFLICT(pk, sk) DO UPDATE SET
                entity_type = excluded.entity_type,
                data = excluded.data
            """,
            (pk, sk, entity_type, json.dumps(data)),
        )
        conn.commit()
    return {"pk": pk, "sk": sk, "entity_type": entity_type, "data": data}


def get_item(pk: str, sk: str) -> Optional[Dict[str, Any]]:
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM records WHERE pk = ? AND sk = ?", (pk, sk)
        ).fetchone()
        return _row_to_item(row) if row else None


def query_by_pk(pk: str) -> List[Dict[str, Any]]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM records WHERE pk = ? ORDER BY sk ASC", (pk,)
        ).fetchall()
        return [_row_to_item(r) for r in rows]


def query_by_pk_prefix(pk: str, sk_prefix: str) -> List[Dict[str, Any]]:
    """Ordered ascending by sk. Since we use ISO-8601 timestamps in sk,
    ascending order also means chronological order -- last item = most recent."""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM records WHERE pk = ? AND sk LIKE ? ORDER BY sk ASC",
            (pk, f"{sk_prefix}%"),
        ).fetchall()
        return [_row_to_item(r) for r in rows]


def scan_by_sk(sk: str) -> List[Dict[str, Any]]:
    """Find item(s) with this exact sk regardless of pk. Used to resolve a
    task by task_id alone, since the caller doesn't know the parent patient."""
    with _conn() as conn:
        rows = conn.execute("SELECT * FROM records WHERE sk = ?", (sk,)).fetchall()
        return [_row_to_item(r) for r in rows]


def scan_by_entity_type(entity_type: str) -> List[Dict[str, Any]]:
    """Full scan by entity_type, e.g. list every patient's METADATA row."""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM records WHERE entity_type = ?", (entity_type,)
        ).fetchall()
        return [_row_to_item(r) for r in rows]


def delete_item(pk: str, sk: str) -> None:
    with _conn() as conn:
        conn.execute("DELETE FROM records WHERE pk = ? AND sk = ?", (pk, sk))
        conn.commit()
