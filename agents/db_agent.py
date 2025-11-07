from typing import Dict, Any, List
from app.logging_utils import JsonSqlLogger
from utils import db_utils


def run(state: Dict[str, Any], settings, logger: JsonSqlLogger) -> Dict[str, Any]:
    run_id = state.get("run_id", "")
    nlp_query = state.get("query") or ""
    # Try NLP query first if present; on failure, fall back to SELECT * FROM DATA_TABLE
    tried_queries: List[str] = []
    def _exec(q: str) -> List[Dict[str, Any]]:
        return db_utils.execute_select(settings, q, limit=500)
    try:
        # MongoDB path: sample documents (basic support)
        if str(getattr(settings, "DATA_DB_TYPE", "")).strip().lower() == "mongodb":
            try:
                from utils import mongo_utils
                rows = mongo_utils.sample_rows(settings, limit=500)
                logger.info(run_id, "db", "mongo_sampled", {"rows": len(rows)})
                return {"status": "success", "data": {"rows": rows, "query_used": "mongodb_sample"}, "log": {"rows": len(rows)}}
            except Exception as e:
                logger.exception(run_id, "db", "mongo_error", {"error": str(e)})
                return {"status": "error", "data": {}, "log": {"error": str(e)}}
        if nlp_query:
            tried_queries.append(nlp_query)
            try:
                rows = _exec(nlp_query)
                logger.info(run_id, "db", "db_query_executed", {"rows": len(rows)})
                return {"status": "success", "data": {"rows": rows, "query_used": nlp_query}, "log": {"rows": len(rows)}}
            except Exception as e:
                logger.error(run_id, "db", "db_nlp_query_failed", {"error": str(e), "query": nlp_query})
        table = getattr(settings, "DATA_TABLE", "")
        if not table:
            return {"status": "error", "data": {}, "log": {"error": "No DATA_TABLE configured and NLP query failed/absent"}}
        fallback = f"SELECT * FROM {table}"
        tried_queries.append(fallback)
        rows = _exec(fallback)
        logger.info(run_id, "db", "db_query_executed_fallback", {"rows": len(rows)})
        return {"status": "success", "data": {"rows": rows, "query_used": fallback}, "log": {"rows": len(rows)}}
    except Exception as e:
        logger.exception(run_id, "db", "db_error", {"error": str(e), "tried": tried_queries})
        return {"status": "error", "data": {}, "log": {"error": str(e)}}
