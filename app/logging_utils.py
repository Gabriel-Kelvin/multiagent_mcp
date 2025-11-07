import os
import json
from datetime import datetime
from typing import Optional, Dict, Any

from app.database import Database
from app.config import settings


def _ensure_dir_for_file(path: str) -> None:
    dirn = os.path.dirname(path)
    if dirn:
        os.makedirs(dirn, exist_ok=True)


class JsonSqlLogger:
    def __init__(self, database: Database, jsonl_file: Optional[str] = None):
        self.db = database
        self.jsonl_file = jsonl_file or settings.LOG_FILE
        _ensure_dir_for_file(self.jsonl_file)

    def _write_jsonl(self, record: Dict[str, Any]) -> None:
        with open(self.jsonl_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def log(self, run_id: str, level: str, node: str, event: str, data: Optional[Dict[str, Any]] = None) -> None:
        record = {
            "run_id": run_id,
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "node": node,
            "event": event,
            "data": data or {},
        }
        self._write_jsonl(record)
        self.db.insert_log(run_id, level, node, event, data or {})

    def info(self, run_id: str, node: str, event: str, data: Optional[Dict[str, Any]] = None) -> None:
        self.log(run_id, "INFO", node, event, data)

    def error(self, run_id: str, node: str, event: str, data: Optional[Dict[str, Any]] = None) -> None:
        self.log(run_id, "ERROR", node, event, data)

    def exception(self, run_id: str, node: str, event: str, data: Optional[Dict[str, Any]] = None) -> None:
        self.log(run_id, "EXCEPTION", node, event, data)
