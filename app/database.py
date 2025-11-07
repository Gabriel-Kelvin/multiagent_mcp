import os
import json
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List

import psycopg2
import psycopg2.extras as pg_extras

from app.config import settings


def _pg_dsn_from_settings() -> str:
    """Build a Postgres DSN string from Settings."""
    if settings.SUPABASE_POOLER_DSN:
        return settings.SUPABASE_POOLER_DSN
    if settings.SUPABASE_DIRECT_DSN:
        return settings.SUPABASE_DIRECT_DSN
    host = settings.PGHOST or "localhost"
    port = settings.PGPORT or "5432"
    db = settings.PGDATABASE or "postgres"
    user = settings.PGUSER or "postgres"
    pwd = settings.PGPASSWORD or ""
    return f"host={host} port={port} dbname={db} user={user} password={pwd} sslmode=require"


class Database:
    def __init__(self, db_path: Optional[str] = None):
        # db_path kept for backward compatibility; not used for Postgres
        self._lock = threading.Lock()
        self._dsn = _pg_dsn_from_settings()
        self.init_db()

    def _connect(self):
        conn = psycopg2.connect(self._dsn)
        conn.autocommit = True
        return conn

    def init_db(self) -> None:
        sqls = [
            """
            CREATE TABLE IF NOT EXISTS logs (
                id BIGSERIAL PRIMARY KEY,
                run_id TEXT,
                timestamp TEXT,
                level TEXT,
                node TEXT,
                event TEXT,
                data TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS runs (
                id BIGSERIAL PRIMARY KEY,
                run_id TEXT UNIQUE,
                user_input TEXT,
                status TEXT,
                started_at TEXT,
                finished_at TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS memory_messages (
                id BIGSERIAL PRIMARY KEY,
                user_id TEXT,
                run_id TEXT,
                timestamp TEXT,
                role TEXT,
                content TEXT
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_logs_run_id ON logs(run_id)",
            "CREATE INDEX IF NOT EXISTS idx_mem_user_id ON memory_messages(user_id)",
        ]
        with self._lock:
            conn = self._connect()
            try:
                with conn.cursor() as cur:
                    for s in sqls:
                        cur.execute(s)
            finally:
                conn.close()

    def insert_log(self, run_id: str, level: str, node: str, event: str, data: Optional[Dict[str, Any]] = None) -> None:
        payload = json.dumps(data or {}, ensure_ascii=False)
        ts = datetime.utcnow().isoformat()
        with self._lock:
            conn = self._connect()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO logs (run_id, timestamp, level, node, event, data) VALUES (%s, %s, %s, %s, %s, %s)",
                        (run_id, ts, level, node, event, payload),
                    )
            finally:
                conn.close()

    def start_run(self, run_id: str, user_input: str) -> None:
        ts = datetime.utcnow().isoformat()
        with self._lock:
            conn = self._connect()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO runs (run_id, user_input, status, started_at, finished_at)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (run_id) DO UPDATE SET
                          user_input = EXCLUDED.user_input,
                          status = EXCLUDED.status,
                          started_at = EXCLUDED.started_at,
                          finished_at = EXCLUDED.finished_at
                        """,
                        (run_id, user_input, "running", ts, None),
                    )
            finally:
                conn.close()

    def finish_run(self, run_id: str, status: str) -> None:
        ts = datetime.utcnow().isoformat()
        with self._lock:
            conn = self._connect()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE runs SET status = %s, finished_at = %s WHERE run_id = %s",
                        (status, ts, run_id),
                    )
            finally:
                conn.close()

    # Conversational memory helpers
    def add_memory_message(self, user_id: str, run_id: str, role: str, content: str) -> None:
        ts = datetime.utcnow().isoformat()
        with self._lock:
            conn = self._connect()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO memory_messages (user_id, run_id, timestamp, role, content) VALUES (%s, %s, %s, %s, %s)",
                        (user_id, run_id, ts, role, content),
                    )
            finally:
                conn.close()

    def get_recent_memory(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._connect()
            try:
                with conn.cursor(cursor_factory=pg_extras.RealDictCursor) as cur:
                    cur.execute(
                        "SELECT user_id, run_id, timestamp, role, content FROM memory_messages WHERE user_id = %s ORDER BY id DESC LIMIT %s",
                        (user_id, limit),
                    )
                    rows = cur.fetchall()
                    out = [dict(r) for r in rows]
                    return list(reversed(out))
            finally:
                conn.close()

    def get_logs(self, limit: int = 200) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._connect()
            try:
                with conn.cursor(cursor_factory=pg_extras.RealDictCursor) as cur:
                    cur.execute(
                        "SELECT run_id, timestamp, level, node, event, data FROM logs ORDER BY id DESC LIMIT %s",
                        (limit,),
                    )
                    rows = cur.fetchall()
                    return [dict(r) for r in rows]
            finally:
                conn.close()
