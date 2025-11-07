from typing import TypedDict, List, Dict, Any, Optional
from typing import Any as _Any
from langgraph.graph import StateGraph, END, START
from uuid import uuid4
from dataclasses import replace

from app.config import settings
from app.database import Database
from app.logging_utils import JsonSqlLogger
from agents import nlp_agent, email_agent, orchestrator, supervisor, csv_agent, db_agent, report_agent, memory_agent


class AppState(TypedDict, total=False):
    run_id: str
    user_input: str
    query: str
    data: List[Dict[str, Any]]
    artifacts: Dict[str, str]
    user_id: str
    memory_messages: List[Dict[str, Any]]
    last_node: str
    last_result: Dict[str, Any]
    supervisor_ok: bool
    route: str
    status: str


def build_app(cfg=settings) -> _Any:
    db = Database(cfg.DB_PATH)
    logger = JsonSqlLogger(db, cfg.LOG_FILE)

    def memory_load_node(state: AppState) -> AppState:
        res = memory_agent.load(state, cfg, logger)
        updates: AppState = {
            "memory_messages": (res.get("data") or {}).get("messages") or [],
            "last_node": "memory_load",
            "last_result": res,
            "status": res.get("status"),
        }
        return updates

    def nlp_node(state: AppState) -> AppState:
        res = nlp_agent.run(state, cfg, logger)
        updates: AppState = {
            "query": (res.get("data") or {}).get("query"),
            "data": (res.get("data") or {}).get("rows"),
            "last_node": "nlp",
            "last_result": res,
            "status": res.get("status"),
        }
        return updates

    def csv_node(state: AppState) -> AppState:
        res = csv_agent.run(state, cfg, logger)
        artifacts = dict(state.get("artifacts") or {})
        csv_path = (res.get("data") or {}).get("csv_path")
        if csv_path:
            artifacts["csv_path"] = csv_path
        return {"artifacts": artifacts, "last_node": "csv", "last_result": res, "status": res.get("status")}

    def db_node(state: AppState) -> AppState:
        res = db_agent.run(state, cfg, logger)
        updates: AppState = {
            "data": (res.get("data") or {}).get("rows"),
            "query": (res.get("data") or {}).get("query_used") or state.get("query"),
            "last_node": "db",
            "last_result": res,
            "status": res.get("status"),
        }
        return updates

    def email_node(state: AppState) -> AppState:
        res = email_agent.run(state, cfg, logger)
        artifacts = dict(state.get("artifacts") or {})
        return {"artifacts": artifacts, "last_node": "email", "last_result": res, "status": res.get("status")}

    def report_node(state: AppState) -> AppState:
        res = report_agent.run(state, cfg, logger)
        artifacts = dict(state.get("artifacts") or {})
        pdf_path = (res.get("data") or {}).get("pdf_path")
        if pdf_path:
            artifacts["pdf_path"] = pdf_path
        return {"artifacts": artifacts, "last_node": "report", "last_result": res, "status": res.get("status")}

    def memory_save_node(state: AppState) -> AppState:
        res = memory_agent.save(state, cfg, logger)
        return {"last_node": "memory_save", "last_result": res, "status": res.get("status")}

    def supervisor_node(state: AppState) -> AppState:
        ok, reason = supervisor.check(state.get("last_node"), state.get("last_result"))
        logger.info(state["run_id"], "supervisor", "check", {"ok": ok, "reason": reason, "after": state.get("last_node")})
        route = orchestrator.decide_next(state.get("last_node"), state)
        if not ok:
            route = "end"
        return {"supervisor_ok": ok, "route": route}

    def route_after_supervisor(state: AppState):
        return state.get("route") or "end"

    graph = StateGraph(AppState)
    graph.add_node("memory_load", memory_load_node)
    graph.add_node("nlp", nlp_node)
    graph.add_node("db", db_node)
    graph.add_node("csv", csv_node)
    graph.add_node("report", report_node)
    graph.add_node("email", email_node)
    graph.add_node("memory_save", memory_save_node)
    graph.add_node("supervisor", supervisor_node)
    graph.add_edge(START, "memory_load")
    graph.add_edge("memory_load", "supervisor")
    graph.add_edge("nlp", "supervisor")
    graph.add_conditional_edges("supervisor", route_after_supervisor, {"nlp": "nlp", "db": "db", "csv": "csv", "report": "report", "email": "email", "memory_save": "memory_save", "end": END})
    graph.add_edge("db", "supervisor")
    graph.add_edge("csv", "supervisor")
    graph.add_edge("report", "supervisor")
    graph.add_edge("email", "supervisor")
    graph.add_edge("memory_save", END)
    app = graph.compile()
    return app, db, logger


def run_once(question: str, overrides: Optional[Dict[str, Any]] = None, user_id: str = "default") -> Dict[str, Any]:
    cfg = settings
    if overrides:
        try:
            cfg = replace(settings, **{k: v for k, v in overrides.items() if hasattr(settings, k)})
        except Exception:
            pass
    app, db, logger = build_app(cfg)
    run_id = str(uuid4())
    db.start_run(run_id, question)
    initial: AppState = {"run_id": run_id, "user_input": question, "artifacts": {}, "user_id": user_id}
    out = app.invoke(initial)
    status = out.get("status") or "success"
    db.finish_run(run_id, status)
    # include run_id for clients
    try:
        out["run_id"] = run_id  # type: ignore[index]
    except Exception:
        pass
    return out


if __name__ == "__main__":
    q = input("Enter question: ").strip() or "Show sample sales for last week"
    result = run_once(q)
    print({"artifacts": result.get("artifacts", {}), "status": result.get("status")})
