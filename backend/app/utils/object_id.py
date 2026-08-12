from typing import Any, Dict, List, Optional, Union
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException

def validate_object_id(id_str: str) -> ObjectId:
    """Validate and convert a string into a BSON ObjectId.
    Raises HTTP 400 Bad Request if invalid.
    """
    if not id_str or not isinstance(id_str, str):
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")
    try:
        return ObjectId(id_str)
    except (InvalidId, TypeError, ValueError):
        raise HTTPException(status_code=400, detail=f"Invalid ObjectId string: '{id_str}'")

def serialize_doc(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Convert MongoDB BSON objects (ObjectId, datetime) in a document into JSON-serializable types."""
    if doc is None:
        return None
    
    res = {}
    for key, value in doc.items():
        if key == "_id":
            res["id"] = str(value)
            res["_id"] = str(value)
        elif isinstance(value, ObjectId):
            res[key] = str(value)
        elif hasattr(value, "isoformat"):  # datetime objects
            res[key] = value.isoformat()
        elif isinstance(value, dict):
            res[key] = serialize_doc(value)
        elif isinstance(value, list):
            res[key] = [serialize_doc(item) if isinstance(item, dict) else (str(item) if isinstance(item, ObjectId) else item) for item in value]
        else:
            res[key] = value
    return res

def serialize_docs(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Serialize a list of MongoDB documents."""
    return [serialize_doc(d) for d in docs if d is not None]
