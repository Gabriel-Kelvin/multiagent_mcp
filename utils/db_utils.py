import os
import re
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

try:
    import pymysql  # type: ignore
    from pymysql.cursors import DictCursor as MySQLDictCursor  # type: ignore
except Exception:  # pragma: no cover
    pymysql = None
    MySQLDictCursor = None  # type: ignore

try:
    import psycopg2  # type: ignore
    import psycopg2.extras as pg_extras  # type: ignore
except Exception:  # pragma: no cover
    psycopg2 = None
    pg_extras = None  # type: ignore


FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke)\b", re.IGNORECASE)
SELECT_START = re.compile(r"^\s*select\b", re.IGNORECASE)
HAS_LIMIT = re.compile(r"\blimit\b", re.IGNORECASE)


def _sqlite_connect(path: str):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def connect(settings):
    db_type = str(getattr(settings, "DATA_DB_TYPE", "")).strip().lower()
    if db_type == "mysql":
        if not pymysql:
            raise ImportError("pymysql is not installed. Add it to requirements and install.")
        host = getattr(settings, "DATA_HOST", "localhost") or "localhost"
        port = int(getattr(settings, "DATA_PORT", 3306) or 3306)
        user = getattr(settings, "DATA_USER", "")
        password = getattr(settings, "DATA_PASSWORD", "")
        db = getattr(settings, "DATA_NAME", "")
        if not (user and db):
            raise ValueError("Missing DATA_USER or DATA_NAME for MySQL")
        return pymysql.connect(host=host, port=port, user=user, password=password, database=db, cursorclass=MySQLDictCursor)
    elif db_type == "postgres" or db_type == "postgresql":
        if not psycopg2:
            raise ImportError("psycopg2-binary is not installed. Add it to requirements and install.")
        dsn = str(getattr(settings, "DATA_DSN", "") or "").strip()
        if dsn:
            return psycopg2.connect(dsn, cursor_factory=pg_extras.RealDictCursor)
        host = getattr(settings, "DATA_HOST", "localhost") or "localhost"
        port = int(getattr(settings, "DATA_PORT", 5432) or 5432)
        user = getattr(settings, "DATA_USER", "")
        password = getattr(settings, "DATA_PASSWORD", "")
        db = getattr(settings, "DATA_NAME", "")
        if not (user and db):
            raise ValueError("Missing DATA_USER or DATA_NAME for Postgres")
        sslmode = str(getattr(settings, "DATA_SSLMODE", "") or "").strip() or ("require" if "supabase" in str(host).lower() else None)
        kwargs = {"host": host, "port": port, "user": user, "password": password, "dbname": db, "cursor_factory": pg_extras.RealDictCursor}
        if sslmode:
            kwargs["sslmode"] = sslmode
        return psycopg2.connect(**kwargs)
    elif db_type == "sqlite":
        path = getattr(settings, "DATA_NAME", "")
        if not path:
            raise ValueError("For sqlite, set DATA_NAME to the database file path")
        return _sqlite_connect(path)
    else:
        raise ValueError("Unsupported DATA_DB_TYPE. Use mysql, postgres, or sqlite.")


def is_safe_select(query: str) -> bool:
    if not SELECT_START.search(query or ""):
        return False
    if FORBIDDEN.search(query or ""):
        return False
    return True


def ensure_limit(query: str, default_limit: int = 500) -> str:
    if not HAS_LIMIT.search(query or ""):
        return f"{query.rstrip().rstrip(';')} LIMIT {default_limit}"
    return query


def execute_select(settings, query: str, limit: int = 500) -> List[Dict[str, Any]]:
    if not is_safe_select(query):
        raise ValueError("Only SELECT queries are allowed")
    query = ensure_limit(query, limit)
    db_type = str(getattr(settings, "DATA_DB_TYPE", "")).strip().lower()
    if db_type == "mysql":
        conn = connect(settings)
        try:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                return list(rows)
        finally:
            conn.close()
    elif db_type in ("postgres", "postgresql"):
        conn = connect(settings)
        try:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                return [dict(r) for r in rows]
        finally:
            conn.close()
    elif db_type == "sqlite":
        conn = connect(settings)
        try:
            cur = conn.cursor()
            cur.execute(query)
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
    else:
        raise ValueError("Unsupported DATA_DB_TYPE")


def _split_schema_table(table: str) -> (str, str):
    if "." in table:
        parts = table.split(".", 1)
        return parts[0], parts[1]
    return "public", table


def get_table_columns(settings, table_name: str) -> List[Dict[str, str]]:
    db_type = str(getattr(settings, "DATA_DB_TYPE", "")).strip().lower()
    if not table_name:
        return []
    if db_type == "mysql":
        conn = connect(settings)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s ORDER BY ORDINAL_POSITION",
                    (getattr(settings, "DATA_NAME", ""), table_name),
                )
                rows = cur.fetchall()
                return [{"name": r["COLUMN_NAME"], "type": r["DATA_TYPE"]} for r in rows]
        finally:
            conn.close()
    elif db_type in ("postgres", "postgresql"):
        schema, table = _split_schema_table(table_name)
        conn = connect(settings)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = %s AND table_name = %s ORDER BY ordinal_position",
                    (schema, table),
                )
                rows = cur.fetchall()
                return [{"name": r["column_name"], "type": r["data_type"]} for r in rows]
        finally:
            conn.close()
    elif db_type == "sqlite":
        conn = connect(settings)
        try:
            cur = conn.cursor()
            cur.execute(f"PRAGMA table_info({table_name})")
            rows = cur.fetchall()
            # rows: cid, name, type, notnull, dflt_value, pk
            out: List[Dict[str, str]] = []
            for r in rows:
                # sqlite3.Row supports dict-style access
                name = r["name"] if isinstance(r, sqlite3.Row) else r[1]
                typ = r["type"] if isinstance(r, sqlite3.Row) else r[2]
                out.append({"name": name, "type": typ})
            return out
        finally:
            conn.close()
    return []
