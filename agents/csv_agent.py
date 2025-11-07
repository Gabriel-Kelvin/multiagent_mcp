from typing import Dict, Any, List
from app.logging_utils import JsonSqlLogger
from utils import csv_utils


def run(state: Dict[str, Any], settings, logger: JsonSqlLogger) -> Dict[str, Any]:
    run_id = state.get("run_id", "")
    rows: List[Dict[str, Any]] = state.get("data") or []
    try:
        csv_path = csv_utils.write_csv_rows(rows)
        logger.info(run_id, "csv", "csv_created", {"path": csv_path})
        return {"status": "success", "data": {"csv_path": csv_path}, "log": {"event": "csv_created"}}
    except Exception as e:
        logger.exception(run_id, "csv", "csv_error", {"error": str(e)})
        return {"status": "error", "data": {}, "log": {"error": str(e)}}
