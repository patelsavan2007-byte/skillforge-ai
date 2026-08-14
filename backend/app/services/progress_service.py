from datetime import datetime
from typing import Dict, Any, Optional, List

from app.database.mongodb import get_learning_paths_collection, get_progress_collection
from app.utils.object_id import serialize_doc, validate_object_id
from app.services.recommendation_engine import calculate_weighted_readiness


def _skill_progress_items(true_skill_gaps: List[str], roadmap: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Derive per-gap status solely from the current roadmap completion state."""
    items: List[Dict[str, Any]] = []
    for skill in dict.fromkeys(s for s in true_skill_gaps if isinstance(s, str) and s.strip()):
        matching = [
            milestone for milestone in roadmap
            if skill.casefold() in {str(value).casefold() for value in milestone.get("skills", [])}
            or skill.casefold() == str(milestone.get("skill", "")).casefold()
        ]
        completed = sum(1 for milestone in matching if milestone.get("completed", False))
        if matching and completed == len(matching):
            status, progress, is_completed = "completed", 100, True
        elif completed:
            status, progress, is_completed = "in_progress", int((completed / len(matching)) * 100), False
        else:
            status, progress, is_completed = "not_started", 0, False
        items.append({"skill": skill, "status": status, "progress": progress, "completed": is_completed})
    return items


def _roadmap_tracking(roadmap: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "week": item.get("week"),
            "title": item.get("title", ""),
            "skill": item.get("skill", ""),
            "status": "completed" if item.get("completed", False) else "not_started",
            "completed": bool(item.get("completed", False)),
            "skills": item.get("skills", [])
        }
        for item in roadmap if isinstance(item, dict)
    ]


def get_user_progress(user_id: str) -> Dict[str, Any]:
    """Retrieve unique progress document for an authenticated user.
    If none exists, returns a clean empty-initialized progress record
    with no hardcoded skills or scores.
    """
    progress_col = get_progress_collection()
    doc = progress_col.find_one({"userId": user_id})

    if not doc:
        now = datetime.utcnow()
        empty_doc = {
            "userId": user_id,
            "skills": {},
            "completedCourses": [],
            "completedProjects": [],
            "roadmapProgress": 0,
            "interviewScore": 0,
            "initialReadiness": 0,
            "careerReadiness": 0,
            "improvedScore": 0,
            "completedGaps": [],
            "remainingGaps": [],
            # Career-analysis-linked fields
            "targetRole": None,
            "skillGapItems": [],
            "skillProgress": [],
            "roadmapItems": [],
            "totalRoadmapItems": 0,
            "completedRoadmapItems": 0,
            "updatedAt": now,
        }
        try:
            res = progress_col.insert_one(empty_doc)
            empty_doc["_id"] = str(res.inserted_id)
            empty_doc["id"] = str(res.inserted_id)
            return serialize_doc(empty_doc)
        except Exception:
            # Handle potential race condition on unique index
            doc = progress_col.find_one({"userId": user_id})

    return serialize_doc(doc)


def initialize_progress_from_career_analysis(
    user_id: str,
    target_role: str,
    true_skill_gaps: List[str],
    roadmap: List[Dict[str, Any]],
    career_readiness: int = 0,
) -> Dict[str, Any]:
    """Seed or reset the user's progress document from the real career analysis output."""
    progress_col = get_progress_collection()
    now = datetime.utcnow()

    roadmap = [item for item in roadmap if isinstance(item, dict)]
    total = len(roadmap)
    completed = sum(1 for item in roadmap if item.get("completed", False))
    progress_pct = int((completed / total * 100)) if total > 0 else 0

    set_fields = {
        "targetRole": target_role,
        "skillGapItems": list(true_skill_gaps),
        "skillProgress": _skill_progress_items(true_skill_gaps, roadmap),
        "roadmapItems": _roadmap_tracking(roadmap),
        "totalRoadmapItems": total,
        "completedRoadmapItems": completed,
        "roadmapProgress": progress_pct,
        "initialReadiness": career_readiness,
        "careerReadiness": career_readiness,
        "improvedScore": 0,
        "completedGaps": [],
        "remainingGaps": list(true_skill_gaps),
        "completedCourses": [],
        "completedProjects": [],
        "skills": {},
        "updatedAt": now,
    }

    res = progress_col.find_one_and_update(
        {"userId": user_id},
        {"$set": set_fields},
        upsert=True,
        return_document=True,
    )
    return serialize_doc(res)


def toggle_roadmap_checkpoint(
    user_id: str,
    week: int,
    completed: bool,
    learning_path_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Persist one user's roadmap checkpoint and deterministically recalculate progress & career readiness."""
    paths_col = get_learning_paths_collection()
    progress_col = get_progress_collection()

    path_filter: Dict[str, Any] = {"userId": user_id}
    if learning_path_id:
        path_filter["_id"] = validate_object_id(learning_path_id)
        path_doc = paths_col.find_one(path_filter)
    else:
        path_doc = paths_col.find_one(path_filter, sort=[("createdAt", -1)])
    if not path_doc:
        raise ValueError("Learning path not found or unauthorized")

    roadmap = path_doc.get("roadmap") or []
    found = False
    for milestone in roadmap:
        if isinstance(milestone, dict) and milestone.get("week") == week:
            milestone["completed"] = completed
            milestone["status"] = "completed" if completed else "not_started"
            if completed:
                milestone["completed_at"] = datetime.utcnow().isoformat()
            else:
                milestone["completed_at"] = None
            found = True
            break
    if not found:
        raise ValueError("Roadmap milestone not found")

    now = datetime.utcnow()
    paths_col.update_one({"_id": path_doc["_id"], "userId": user_id}, {"$set": {"roadmap": roadmap, "updatedAt": now}})

    existing = progress_col.find_one({"userId": user_id}) or {}
    gaps = existing.get("skillGapItems") or path_doc.get("true_skill_gaps") or []
    target_role = existing.get("targetRole") or path_doc.get("targetRole") or "Full Stack Developer"
    user_strengths = path_doc.get("user_strengths") or []
    initial_readiness = existing.get("initialReadiness") or path_doc.get("initialReadiness") or existing.get("careerReadiness", 50)

    total = len(roadmap)
    completed_count = sum(1 for item in roadmap if isinstance(item, dict) and item.get("completed", False))
    progress_pct = int((completed_count / total) * 100) if total else 0

    # Determine which skill gaps have been completed
    completed_skills_covered = set()
    for item in roadmap:
        if isinstance(item, dict) and item.get("completed", False):
            for s in item.get("skills", []):
                completed_skills_covered.add(str(s).strip().lower())
            if item.get("skill"):
                completed_skills_covered.add(str(item.get("skill")).strip().lower())

    completed_gaps = [
        g for g in gaps
        if g.strip().lower() in completed_skills_covered
    ]
    remaining_gaps = [
        g for g in gaps
        if g.strip().lower() not in completed_skills_covered
    ]

    # Recalculate dynamic career readiness
    current_readiness = calculate_weighted_readiness(
        target_role=target_role,
        demonstrated_skills=user_strengths,
        completed_skills=completed_gaps,
    )
    improved_score = max(0, current_readiness - initial_readiness)

    set_fields = {
        "totalRoadmapItems": total,
        "completedRoadmapItems": completed_count,
        "roadmapProgress": progress_pct,
        "roadmapItems": _roadmap_tracking(roadmap),
        "skillProgress": _skill_progress_items(gaps, roadmap),
        "initialReadiness": initial_readiness,
        "careerReadiness": current_readiness,
        "improvedScore": improved_score,
        "completedGaps": completed_gaps,
        "remainingGaps": remaining_gaps,
        "updatedAt": now,
    }
    progress_doc = progress_col.find_one_and_update(
        {"userId": user_id}, {"$set": set_fields}, upsert=True, return_document=True
    )
    result = serialize_doc(progress_doc)
    result["roadmap"] = roadmap
    result["learningPathId"] = str(path_doc["_id"])
    return result


def update_user_progress(user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Upsert progress document for an authenticated user.

    If completedRoadmapItems and totalRoadmapItems are both present,
    roadmapProgress is recalculated deterministically rather than
    accepting a caller-supplied value.
    """
    progress_col = get_progress_collection()
    now = datetime.utcnow()

    # These fields are derived from career analysis and persisted roadmap checkpoints,
    # never from arbitrary client input.
    deterministic_fields = {
        "skills", "skillGapItems", "skillProgress", "roadmapItems",
        "roadmapProgress", "totalRoadmapItems", "completedRoadmapItems",
    }
    set_fields: Dict[str, Any] = {"updatedAt": now}
    for key, value in updates.items():
        if value is not None and key not in deterministic_fields:
            set_fields[key] = value

    # Deterministic progress recalculation
    # Use supplied values if present; otherwise look up the existing document
    existing = progress_col.find_one({"userId": user_id}) or {}
    completed = existing.get("completedRoadmapItems", 0)
    total = existing.get("totalRoadmapItems", 0)

    if total > 0:
        set_fields["roadmapProgress"] = int((completed / total) * 100)
    else:
        set_fields["roadmapProgress"] = 0

    res = progress_col.find_one_and_update(
        {"userId": user_id},
        {"$set": set_fields},
        upsert=True,
        return_document=True,
    )
    return serialize_doc(res)
