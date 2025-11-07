import os
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def write_csv_rows(rows: List[Dict[str, Any]], file_path: Optional[str] = None) -> str:
    _ensure_dir("artifacts")
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    out_path = file_path or os.path.join("artifacts", f"data-{ts}.csv")
    fieldnames = set()
    for r in rows:
        fieldnames.update(r.keys())
    headers = list(fieldnames)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    return out_path
