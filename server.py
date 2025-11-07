from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from uuid import uuid4

from main import run_once
from app.database import Database
from app.config import settings
from utils import db_utils
from agents.scheduler_agent import SchedulerService

app = FastAPI(title="Multi-Agent Data Assistant")

# CORS for local React dev and general access; adjust for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve artifacts (CSV/PDF) statically for downloads from the frontend
try:
    app.mount("/artifacts", StaticFiles(directory="artifacts"), name="artifacts")
except Exception:
    pass


class RunRequest(BaseModel):
    question: str
    user_id: Optional[str] = "default"
    db_type: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    name: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    table: Optional[str] = None
    dsn: Optional[str] = None
    sslmode: Optional[str] = None
    email_from: Optional[str] = None
    email_to: Optional[str] = None
    email_key: Optional[str] = None
    use_env: Optional[bool] = False


def _mk_overrides(req: RunRequest) -> Dict[str, Any]:
    o: Dict[str, Any] = {}
    if getattr(req, "use_env", False):
        # Prefer DSN from env, then discrete PG params
        if getattr(settings, "DATA_DB_TYPE", ""):
            o["DATA_DB_TYPE"] = settings.DATA_DB_TYPE
        dsn = getattr(settings, "DATA_DSN", "") or getattr(settings, "SUPABASE_POOLER_DSN", "") or getattr(settings, "SUPABASE_DIRECT_DSN", "")
        if dsn:
            o["DATA_DSN"] = dsn
        else:
            if getattr(settings, "PGHOST", ""): o["DATA_HOST"] = settings.PGHOST
            if getattr(settings, "PGPORT", ""): o["DATA_PORT"] = str(settings.PGPORT)
            if getattr(settings, "PGDATABASE", ""): o["DATA_NAME"] = settings.PGDATABASE
            if getattr(settings, "PGUSER", ""): o["DATA_USER"] = settings.PGUSER
            if getattr(settings, "PGPASSWORD", ""): o["DATA_PASSWORD"] = settings.PGPASSWORD
            o["DATA_SSLMODE"] = getattr(settings, "DATA_SSLMODE", "require") or "require"
    if req.db_type:
        o["DATA_DB_TYPE"] = req.db_type
    if req.host is not None:
        o["DATA_HOST"] = req.host
    if req.port is not None:
        o["DATA_PORT"] = str(req.port)
    if req.name is not None:
        o["DATA_NAME"] = req.name
    if req.user is not None:
        o["DATA_USER"] = req.user
    if req.password is not None:
        o["DATA_PASSWORD"] = req.password
    if req.table is not None:
        o["DATA_TABLE"] = req.table
    if getattr(req, "dsn", None) is not None:
        o["DATA_DSN"] = req.dsn
    if getattr(req, "sslmode", None) is not None:
        o["DATA_SSLMODE"] = req.sslmode
    if getattr(req, "email_from", None):
        o["EMAIL_FROM"] = req.email_from
    if getattr(req, "email_to", None):
        o["EMAIL_TO"] = req.email_to
    if getattr(req, "email_key", None):
        o["SENDGRID_API_KEY"] = req.email_key
    return o


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok"}


@app.post("/run")
def run_flow(req: RunRequest) -> Dict[str, Any]:
    overrides = _mk_overrides(req)
    result = run_once(req.question, overrides=overrides, user_id=req.user_id or "default")
    preview: List[Dict[str, Any]] = []
    data = result.get("data") or []
    if isinstance(data, list):
        preview = data[:5]
    return {
        "status": result.get("status"),
        "artifacts": result.get("artifacts", {}),
        "preview": preview,
        "run_id": result.get("run_id"),
    }


class DbTestRequest(BaseModel):
    db_type: str
    host: Optional[str] = None
    port: Optional[int] = None
    name: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    table: Optional[str] = None
    dsn: Optional[str] = None
    sslmode: Optional[str] = None
    use_env: Optional[bool] = False


@app.post("/db/test")
def db_test(req: DbTestRequest) -> Dict[str, Any]:
    # Build a transient settings-like object
    class X:
        pass
    x = X()
    setattr(x, "DATA_DB_TYPE", req.db_type)
    if req.use_env:
        # Use server environment for connection
        setattr(x, "DATA_HOST", getattr(settings, "DATA_HOST", ""))
        setattr(x, "DATA_PORT", getattr(settings, "DATA_PORT", "5432"))
        setattr(x, "DATA_NAME", getattr(settings, "DATA_NAME", ""))
        setattr(x, "DATA_USER", getattr(settings, "DATA_USER", ""))
        setattr(x, "DATA_PASSWORD", getattr(settings, "DATA_PASSWORD", ""))
        setattr(x, "DATA_DSN", getattr(settings, "DATA_DSN", ""))
        setattr(x, "DATA_SSLMODE", getattr(settings, "DATA_SSLMODE", ""))
        setattr(x, "DATA_TABLE", req.table or getattr(settings, "DATA_TABLE", ""))
    else:
        setattr(x, "DATA_HOST", req.host or "localhost")
        setattr(x, "DATA_PORT", str(req.port or (3306 if req.db_type == "mysql" else 5432)))
        setattr(x, "DATA_NAME", req.name or "")
        setattr(x, "DATA_USER", req.user or "")
        setattr(x, "DATA_PASSWORD", req.password or "")
        setattr(x, "DATA_DSN", req.dsn or "")
        setattr(x, "DATA_SSLMODE", req.sslmode or ("require" if (req.host or "").endswith("supabase.com") else ""))
        setattr(x, "DATA_TABLE", req.table or "")
    try:
        if req.db_type in ("mysql", "postgres", "postgresql", "sqlite"):
            table = getattr(x, "DATA_TABLE", "")
            if not table:
                return {"status": "error", "error": "DATA_TABLE required"}
            rows = db_utils.execute_select(x, f"SELECT * FROM {table}", limit=5)
            return {"status": "success", "rows": rows}
        elif req.db_type == "mongodb":
            from utils import mongo_utils
            rows = mongo_utils.sample_rows(x, limit=5)
            return {"status": "success", "rows": rows}
        else:
            return {"status": "error", "error": "Unsupported db_type"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/logs")
def get_logs(limit: int = 200) -> Dict[str, Any]:
    db = Database(settings.DB_PATH)
    logs = db.get_logs(limit=limit)
    return {"status": "success", "logs": logs}


# Scheduler endpoints for React frontend
class ScheduleJobRequest(BaseModel):
    question: str
    frequency: str  # daily | weekly | monthly
    time: str       # HH:MM
    user_id: Optional[str] = "scheduler"
    # Optional overrides
    dsn: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    name: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    table: Optional[str] = None
    sslmode: Optional[str] = None


def _mk_overrides_from_schedule(req: ScheduleJobRequest) -> Dict[str, Any]:
    o: Dict[str, Any] = {"DATA_DB_TYPE": "postgres"}
    if getattr(req, "use_env", False):
        dsn = getattr(settings, "DATA_DSN", "") or getattr(settings, "SUPABASE_POOLER_DSN", "") or getattr(settings, "SUPABASE_DIRECT_DSN", "")
        if dsn:
            o["DATA_DSN"] = dsn
        else:
            if getattr(settings, "PGHOST", ""): o["DATA_HOST"] = settings.PGHOST
            if getattr(settings, "PGPORT", ""): o["DATA_PORT"] = str(settings.PGPORT)
            if getattr(settings, "PGDATABASE", ""): o["DATA_NAME"] = settings.PGDATABASE
            if getattr(settings, "PGUSER", ""): o["DATA_USER"] = settings.PGUSER
            if getattr(settings, "PGPASSWORD", ""): o["DATA_PASSWORD"] = settings.PGPASSWORD
            o["DATA_SSLMODE"] = getattr(settings, "DATA_SSLMODE", "require") or "require"
    if req.dsn:
        o["DATA_DSN"] = req.dsn
    if req.host is not None:
        o["DATA_HOST"] = req.host
    if req.port is not None:
        o["DATA_PORT"] = str(req.port)
    if req.name is not None:
        o["DATA_NAME"] = req.name
    if req.user is not None:
        o["DATA_USER"] = req.user
    if req.password is not None:
        o["DATA_PASSWORD"] = req.password
    if req.table is not None:
        o["DATA_TABLE"] = req.table
    if req.sslmode is not None:
        o["DATA_SSLMODE"] = req.sslmode
    return o


@app.post("/scheduler/add")
def scheduler_add(req: ScheduleJobRequest) -> Dict[str, Any]:
    job_id = f"scheduled_{uuid4().hex[:8]}"
    overrides = _mk_overrides_from_schedule(req)
    SchedulerService.add_job(job_id, req.question, req.frequency, req.time, overrides, run_once)
    return {"status": "success", "job_id": job_id}


@app.get("/scheduler/list")
def scheduler_list() -> Dict[str, Any]:
    jobs = SchedulerService.list_jobs()
    return {"status": "success", "jobs": jobs}


@app.delete("/scheduler/{job_id}")
def scheduler_delete(job_id: str) -> Dict[str, Any]:
    ok = SchedulerService.remove_job(job_id)
    return {"status": "success" if ok else "error", "deleted": ok}
