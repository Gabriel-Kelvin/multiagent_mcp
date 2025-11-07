from typing import Any, Dict, List, Optional
from pymongo import MongoClient
from bson import ObjectId


def _obj_to_str(doc: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            out[k] = str(v)
        else:
            out[k] = v
    return out


def connect(settings) -> MongoClient:
    host = getattr(settings, "DATA_HOST", "localhost") or "localhost"
    port = int(getattr(settings, "DATA_PORT", 27017) or 27017)
    user = getattr(settings, "DATA_USER", "")
    password = getattr(settings, "DATA_PASSWORD", "")
    if user:
        uri = f"mongodb://{user}:{password}@{host}:{port}"
    else:
        uri = f"mongodb://{host}:{port}"
    return MongoClient(uri)


def sample_rows(settings, limit: int = 5) -> List[Dict[str, Any]]:
    client = connect(settings)
    try:
        dbname = getattr(settings, "DATA_NAME", "")
        collname = getattr(settings, "DATA_TABLE", "")
        if not (dbname and collname):
            raise ValueError("DATA_NAME (database) and DATA_TABLE (collection) are required for MongoDB")
        coll = client[dbname][collname]
        docs = list(coll.find({}, limit=limit))
        return [_obj_to_str(d) for d in docs]
    finally:
        client.close()
