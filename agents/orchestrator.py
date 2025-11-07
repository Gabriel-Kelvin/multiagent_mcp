from typing import Any, Dict


def decide_next(last_node: str, state: Dict[str, Any]) -> str:
    if last_node == "memory_load":
        return "nlp"
    if last_node == "nlp":
        # DB is mandatory
        return "db"
    if last_node == "db":
        return "csv"
    if last_node == "csv":
        return "report"
    if last_node == "report":
        return "email"
    if last_node == "email":
        return "memory_save"
    return "end"
