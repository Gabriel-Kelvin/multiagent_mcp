#!/usr/bin/env python3
"""
Migrate existing SQLite data (logs, runs, memory_messages) to Supabase Postgres.

Usage:
  python scripts/migrate_sqlite_to_supabase.py \
      --sqlite-path logs/app.db \
      [--dry-run]

Connection picks from environment:
  - SUPABASE_POOLER_DSN or SUPABASE_DIRECT_DSN, else
  - PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD (sslmode=require is used)

Safe to run multiple times. 'runs' rows are upserted on run_id; logs and memory_messages are appended.
"""
import os
import sqlite3
import argparse
import json
from typing import Any, Dict, List
from dotenv import load_dotenv
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

# Load environment variables from repo root .env explicitly
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH, override=True)
print(f"dotenv: loaded={_ENV_PATH.exists()} path={_ENV_PATH}")


DDL_STATEMENTS = [
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


def build_dsn() -> str:
    if os.getenv("SUPABASE_POOLER_DSN"):
        return os.getenv("SUPABASE_POOLER_DSN")
    if os.getenv("SUPABASE_DIRECT_DSN"):
        return os.getenv("SUPABASE_DIRECT_DSN")
    host = os.getenv("PGHOST", "localhost")
    port = os.getenv("PGPORT", "5432")
    db = os.getenv("PGDATABASE", "postgres")
    user = os.getenv("PGUSER", "postgres")
    pwd = os.getenv("PGPASSWORD", "")
    # Quick visibility in case of connection issues
    print(f"Using PG params host={host} port={port} db={db} user={user}")
    return f"host={host} port={port} dbname={db} user={user} password={pwd} sslmode=require"


def ensure_schema(conn) -> None:
    with conn.cursor() as cur:
        for stmt in DDL_STATEMENTS:
            cur.execute(stmt)


def fetch_sqlite_rows(sqlite_path: str, query: str, params: tuple = ()) -> List[sqlite3.Row]:
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        return cur.fetchall()
    finally:
        conn.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sqlite-path", default=os.getenv("DB_PATH", "logs/app.db"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    sqlite_path = args.sqlite_path
    if not os.path.exists(sqlite_path):
        raise SystemExit(f"SQLite file not found: {sqlite_path}")

    dsn = build_dsn()
    pg = psycopg2.connect(dsn)
    pg.autocommit = True

    try:
        ensure_schema(pg)

        # Fetch
        logs = fetch_sqlite_rows(sqlite_path, "SELECT run_id, timestamp, level, node, event, data FROM logs ORDER BY id")
        runs = fetch_sqlite_rows(sqlite_path, "SELECT run_id, user_input, status, started_at, finished_at FROM runs ORDER BY id")
        mem = fetch_sqlite_rows(sqlite_path, "SELECT user_id, run_id, timestamp, role, content FROM memory_messages ORDER BY id")

        print(f"Found: logs={len(logs)} runs={len(runs)} memory_messages={len(mem)}")
        if args.dry_run:
            return

        with pg.cursor() as cur:
            # Insert runs with upsert on run_id
            if runs:
                execute_values(
                    cur,
                    """
                    INSERT INTO runs (run_id, user_input, status, started_at, finished_at)
                    VALUES %s
                    ON CONFLICT (run_id) DO UPDATE SET
                      user_input = EXCLUDED.user_input,
                      status = EXCLUDED.status,
                      started_at = EXCLUDED.started_at,
                      finished_at = EXCLUDED.finished_at
                    """,
                    [(r["run_id"], r["user_input"], r["status"], r["started_at"], r["finished_at"]) for r in runs],
                )
            # Insert logs
            if logs:
                execute_values(
                    cur,
                    "INSERT INTO logs (run_id, timestamp, level, node, event, data) VALUES %s",
                    [(r["run_id"], r["timestamp"], r["level"], r["node"], r["event"], r["data"]) for r in logs],
                )
            # Insert memory
            if mem:
                execute_values(
                    cur,
                    "INSERT INTO memory_messages (user_id, run_id, timestamp, role, content) VALUES %s",
                    [(r["user_id"], r["run_id"], r["timestamp"], r["role"], r["content"]) for r in mem],
                )
        print("Migration complete ✅")
    finally:
        pg.close()


if __name__ == "__main__":
    main()
