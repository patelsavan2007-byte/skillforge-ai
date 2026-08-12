from datetime import datetime
from typing import Dict, Any, Optional

from app.database.mongodb import get_progress_collection
from app.utils.object_id import serialize_doc

def get_user_progress(user_id: str) -> Dict[str, Any]:
    """Retrieve unique progress document for an authenticated user.
    If none exists, initializes default progress record.
    """
    progress_col = get_progress_collection()
    doc = progress_col.find_one({"userId": user_id})
    
    if not doc:
        now = datetime.utcnow()
        default_doc = {
            "userId": user_id,
            "skills": {
                "Python": 90,
                "Machine Learning": 60,
                "PyTorch": 25,
                "MLOps": 10,
                "SQL": 45
            },
            "completedCourses": [
                {"courseId": "course_python_101", "completedAt": now.isoformat()}
            ],
            "completedProjects": [
                {"projectId": "proj_ml_dashboard", "completedAt": now.isoformat()}
            ],
            "roadmapProgress": 33,
            "interviewScore": 75,
            "careerReadiness": 68,
            "updatedAt": now
        }
        try:
            res = progress_col.insert_one(default_doc)
            default_doc["_id"] = str(res.inserted_id)
            default_doc["id"] = str(res.inserted_id)
            return serialize_doc(default_doc)
        except Exception:
            # Handle potential race condition on unique index
            doc = progress_col.find_one({"userId": user_id})

    return serialize_doc(doc)

def update_user_progress(user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Upsert progress document for an authenticated user."""
    progress_col = get_progress_collection()
    now = datetime.utcnow()
    
    set_fields = {"updatedAt": now}
    for key, value in updates.items():
        if value is not None:
            set_fields[key] = value

    res = progress_col.find_one_and_update(
        {"userId": user_id},
        {"$set": set_fields},
        upsert=True,
        return_document=True
    )
    return serialize_doc(res)
