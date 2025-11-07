from typing import Dict, Any, List
import re
from app.logging_utils import JsonSqlLogger
from app.config import settings as _settings


def _extract_sql(text: str) -> str:
    if not text:
        return ""
    m = re.search(r"```(?:sql)?\s*(.*?)```", text, re.IGNORECASE | re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(r"select\b[\s\S]*", text, re.IGNORECASE)
    if m:
        sql = m.group(0)
        semi = sql.find(";")
        if semi != -1:
            sql = sql[:semi]
        return sql.strip()
    return text.strip()


def _heuristic_groupby_query(table: str, columns: List[Dict[str, Any]], user_input: str) -> str:
    if not table:
        return ""
    lowered = user_input.lower()
    keywords = ["employment", "job", "type", "category", "segment", "region", "status"]
    target = None
    for c in columns:
        name = str(c.get("name", ""))
        lname = name.lower()
        if any(k in lname for k in keywords):
            target = name
            break
    if not target and columns:
        for c in columns:
            name = str(c.get("name", ""))
            if name and name.isidentifier():
                target = name
                break
    if target:
        return f"SELECT {target} AS value, COUNT(*) AS count FROM {table} GROUP BY {target} ORDER BY count DESC LIMIT 20"
    return f"SELECT * FROM {table} LIMIT 50"


def run(state: Dict[str, Any], settings, logger: JsonSqlLogger) -> Dict[str, Any]:
    run_id = state.get("run_id", "")
    user_input = state.get("user_input", "")
    query = None
    used = "mock"
    schema_cols: List[Dict[str, Any]] = []
    memory_msgs: List[Dict[str, Any]] = state.get("memory_messages") or []
    table = getattr(settings, "DATA_TABLE", "")
    try:
        if getattr(settings, "DATA_DB_TYPE", "") and table:
            try:
                from utils import db_utils
                schema_cols = db_utils.get_table_columns(settings, table)
            except Exception as e:
                logger.error(run_id, "nlp", "schema_fetch_failed", {"error": str(e)})
        if getattr(settings, "OPENAI_API_KEY", ""):
            try:
                from openai import OpenAI
                from utils import db_utils
                client = OpenAI(api_key=settings.OPENAI_API_KEY)
                cols_str = ", ".join([f"{c.get('name')} ({c.get('type')})" for c in schema_cols]) or ""
                mem_str = "; ".join([f"{m.get('role')}: {m.get('content')}" for m in memory_msgs[-5:]]) if memory_msgs else ""
                prompt = (
                    f"You are a senior data SQL assistant. Given a table name `{table}` and its columns [{cols_str}], "
                    f"and considering recent context/preferences [{mem_str}], "
                    f"write a single safe SELECT query that best answers the question: '{user_input}'. "
                    f"Rules: only SELECT; no CTE unless needed; avoid DDL/DML; prefer GROUP BY or ORDER BY as appropriate; "
                    f"if aggregating categories use COUNT(*) and return top categories; always include LIMIT 500 or fewer. "
                    f"Return only the SQL without explanations or backticks."
                )
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                )
                content = resp.choices[0].message.content if resp and resp.choices else ""
                sql = _extract_sql(content)
                if sql and table and table not in sql:
                    sql = sql.replace("FROM ", f"FROM {table} ")
                if sql:
                    from utils import db_utils
                    if not db_utils.is_safe_select(sql):
                        sql = _heuristic_groupby_query(table, schema_cols, user_input)
                    sql = db_utils.ensure_limit(sql, 500)
                query = sql
                used = "openai"
            except Exception as e:
                query = None
                used = "mock"
        if not query:
            query = _heuristic_groupby_query(table, schema_cols, user_input) if table else "SELECT 1"
        logger.info(run_id, "nlp", "nlp_done", {"used": used, "query": query, "schema_cols": len(schema_cols)})
        return {"status": "success", "data": {"query": query}, "log": {"used": used}}
    except Exception as e:
        logger.exception(run_id, "nlp", "nlp_error", {"error": str(e)})
        return {"status": "error", "data": {}, "log": {"error": str(e)}}
