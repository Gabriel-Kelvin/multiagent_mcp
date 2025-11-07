import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt


def _pick_categorical_column(rows: List[Dict[str, Any]]) -> Optional[str]:
    if not rows:
        return None
    # prefer string-like columns or those with few unique values
    sample = rows[:500]
    candidates = {}
    for k in rows[0].keys():
        vals = [str(r.get(k, "")) for r in sample]
        uniq = len(set(vals))
        candidates[k] = uniq
    # pick column with smallest unique count but > 1
    sorted_cols = sorted(candidates.items(), key=lambda kv: kv[1])
    for col, uniq in sorted_cols:
        if 1 < uniq <= max(50, len(sample) // 2):
            return col
    # fallback: first column
    return list(rows[0].keys())[0]


essential_colors = [
    "#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
    "#edc949", "#af7aa1", "#ff9da7", "#9c755f", "#bab0ab",
]


def make_bar_chart_from_rows(rows: List[Dict[str, Any]], column: Optional[str] = None, top_k: int = 10, title: Optional[str] = None) -> Optional[str]:
    if not rows:
        return None
    os.makedirs("artifacts", exist_ok=True)
    col = column or _pick_categorical_column(rows)
    if not col:
        return None
    counts = {}
    for r in rows:
        key = str(r.get(col, ""))
        counts[key] = counts.get(key, 0) + 1
    items = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:top_k]
    labels = [k for k, _ in items]
    values = [v for _, v in items]
    if not items:
        return None
    plt.figure(figsize=(8, 4.5), dpi=150)
    bars = plt.bar(labels, values, color=essential_colors[: len(labels)])
    plt.xticks(rotation=30, ha="right")
    plt.ylabel("Count")
    plt.title(title or f"Top {top_k} by {col}")
    # annotate
    for b in bars:
        h = b.get_height()
        plt.text(b.get_x() + b.get_width() / 2, h, f"{int(h)}", ha="center", va="bottom", fontsize=8)
    plt.tight_layout()
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    out_path = os.path.join("artifacts", f"chart-{ts}.png")
    plt.savefig(out_path)
    plt.close()
    return out_path
