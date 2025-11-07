from typing import Dict, Any, List
from app.logging_utils import JsonSqlLogger
from utils import chart_utils, pdf_utils


def run(state: Dict[str, Any], settings, logger: JsonSqlLogger) -> Dict[str, Any]:
    run_id = state.get("run_id", "")
    rows: List[Dict[str, Any]] = state.get("data") or []
    chart_path = None
    try:
        try:
            chart_path = chart_utils.make_bar_chart_from_rows(rows, top_k=10, title="Top categories")
        except Exception:
            chart_path = None
        pdf_path = pdf_utils.create_pdf_summary(state.get("user_input", ""), rows, chart_path=chart_path)
        artifacts = dict(state.get("artifacts") or {})
        artifacts["pdf_path"] = pdf_path
        logger.info(run_id, "report", "pdf_created", {"path": pdf_path, "chart": chart_path})
        return {"status": "success", "data": {"pdf_path": pdf_path, "chart_path": chart_path}, "log": {"event": "pdf_created"}}
    except Exception as e:
        logger.exception(run_id, "report", "pdf_error", {"error": str(e)})
        return {"status": "error", "data": {}, "log": {"error": str(e)}}
