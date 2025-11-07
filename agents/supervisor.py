from typing import Any, Dict
import os


def check(node_name: str, last_result: Dict[str, Any]):
    if not last_result:
        return False, "no_result"
    status = last_result.get("status")
    if status not in ("success", "skipped"):
        return False, "node_failed"
    if node_name == "nlp":
        data = last_result.get("data") or {}
        query = data.get("query") or ""
        if not query:
            return False, "no_query"
    if node_name == "db":
        data = last_result.get("data") or {}
        rows = data.get("rows") or []
        if rows is None or len(rows) == 0:
            return False, "no_rows_from_db"
    if node_name == "csv":
        data = last_result.get("data") or {}
        path = (data or {}).get("csv_path") or (data.get("path") if isinstance(data, dict) else None)
        if path and not os.path.exists(path):
            return False, "missing_csv"
    if node_name == "report":
        data = last_result.get("data") or {}
        pdf_path = data.get("pdf_path")
        if not (pdf_path and os.path.exists(pdf_path)):
            return False, "missing_pdf"
    if node_name == "email":
        # Allow gracefully skipped email
        status = last_result.get("status")
        if status == "skipped":
            return True, "email_skipped"
        if status != "success":
            return False, "email_not_sent"
    return True, "ok"
