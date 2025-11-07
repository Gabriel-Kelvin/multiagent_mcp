from typing import Dict, Any, List
from app.logging_utils import JsonSqlLogger


def load(state: Dict[str, Any], settings, logger: JsonSqlLogger) -> Dict[str, Any]:
    run_id = state.get("run_id", "")
    user_id = state.get("user_id", "default")
    try:
        db = logger.db
        msgs: List[Dict[str, Any]] = db.get_recent_memory(user_id=user_id, limit=10)
        logger.info(run_id, "memory", "loaded", {"count": len(msgs)})
        return {"status": "success", "data": {"messages": msgs}, "log": {"count": len(msgs)}}
    except Exception as e:
        logger.exception(run_id, "memory", "load_error", {"error": str(e)})
        return {"status": "error", "data": {}, "log": {"error": str(e)}}


def save(state: Dict[str, Any], settings, logger: JsonSqlLogger) -> Dict[str, Any]:
    run_id = state.get("run_id", "")
    user_id = state.get("user_id", "default")
    question = state.get("user_input", "")
    # Summary message: include query_used and simple stat
    last = state.get("last_result") or {}
    query_used = None
    if isinstance(last.get("data"), dict):
        query_used = last.get("data", {}).get("query_used") or state.get("query")
    try:
        db = logger.db
        if question:
            db.add_memory_message(user_id=user_id, run_id=run_id, role="user", content=question)
        if query_used:
            db.add_memory_message(user_id=user_id, run_id=run_id, role="assistant", content=f"query_used: {query_used}")
        logger.info(run_id, "memory", "saved", {"has_question": bool(question), "has_query": bool(query_used)})
        return {"status": "success", "data": {}, "log": {"saved": True}}
    except Exception as e:
        logger.exception(run_id, "memory", "save_error", {"error": str(e)})
        return {"status": "error", "data": {}, "log": {"error": str(e)}}
