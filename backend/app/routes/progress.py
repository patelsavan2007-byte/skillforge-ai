from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Body, HTTPException
from pydantic import BaseModel

from app.routes.auth import get_current_user_id
from app.schemas.progress import ProgressUpdate, RoadmapCheckpointUpdate
from app.services.progress_service import (
    get_user_progress,
    update_user_progress,
    initialize_progress_from_career_analysis,
    toggle_roadmap_checkpoint,
)
from app.database.mongodb import get_career_profiles_collection, get_learning_paths_collection
from app.utils.object_id import validate_object_id

router = APIRouter(prefix="/api/progress", tags=["progress"])


class ProgressInitRequest(BaseModel):
    careerProfileId: Optional[str] = None
    learningPathId: Optional[str] = None


@router.get("", response_model=Dict[str, Any])
async def get_progress(user_id: str = Depends(get_current_user_id)):
    """Retrieve user's unique progress record from MongoDB progress collection."""
    progress_doc = get_user_progress(user_id)
    return {"success": True, "data": progress_doc}


@router.post("/initialize", response_model=Dict[str, Any])
async def initialize_progress(
    payload: ProgressInitRequest = Body(...),
    user_id: str = Depends(get_current_user_id),
):
    """Seed or reset the authenticated user's progress from their real career analysis data.

    Looks up the career profile and learning path by ID (both scoped to the user),
    extracts true_skill_gaps and roadmap, then writes a fresh progress document.
    roadmapProgress is calculated deterministically from roadmap length and completion state.
    """
    career_col = get_career_profiles_collection()
    paths_col = get_learning_paths_collection()

    # Resolve career profile
    career_doc = None
    if payload.careerProfileId:
        try:
            oid = validate_object_id(payload.careerProfileId)
            career_doc = career_col.find_one({"_id": oid, "userId": user_id})
        except Exception:
            pass
    if career_doc is None:
        # Fall back to most recent profile for this user
        career_doc = career_col.find_one({"userId": user_id}, sort=[("createdAt", -1)])
    if career_doc is None:
        raise HTTPException(status_code=404, detail="No career profile found for this user. Run career analysis first.")

    # Resolve learning path
    path_doc = None
    if payload.learningPathId:
        try:
            oid = validate_object_id(payload.learningPathId)
            path_doc = paths_col.find_one({"_id": oid, "userId": user_id})
        except Exception:
            pass
    if path_doc is None:
        path_doc = paths_col.find_one({"userId": user_id}, sort=[("createdAt", -1)])
    if path_doc is None:
        raise HTTPException(status_code=404, detail="No learning path found for this user. Run career analysis first.")

    true_skill_gaps: list = career_doc.get("true_skill_gaps") or []
    target_role: str = career_doc.get("targetRole", "")
    career_readiness: int = int(career_doc.get("careerReadiness", 0))
    roadmap: list = path_doc.get("roadmap") or []

    progress_doc = initialize_progress_from_career_analysis(
        user_id=user_id,
        target_role=target_role,
        true_skill_gaps=true_skill_gaps,
        roadmap=roadmap,
        career_readiness=career_readiness,
    )
    return {"success": True, "data": progress_doc}


@router.put("", response_model=Dict[str, Any])
async def replace_progress(
    payload: ProgressUpdate = Body(...),
    user_id: str = Depends(get_current_user_id),
):
    """Replace/Upsert progress document for authenticated user."""
    updates = payload.model_dump(exclude_none=True)
    updated_doc = update_user_progress(user_id, updates)
    return {"success": True, "data": updated_doc}


@router.patch("", response_model=Dict[str, Any])
async def patch_progress(
    payload: ProgressUpdate = Body(...),
    user_id: str = Depends(get_current_user_id),
):
    """Patch progress document for authenticated user."""
    updates = payload.model_dump(exclude_none=True)
    updated_doc = update_user_progress(user_id, updates)
    return {"success": True, "data": updated_doc}


@router.patch("/checkpoint", response_model=Dict[str, Any])
async def update_roadmap_checkpoint(
    payload: RoadmapCheckpointUpdate = Body(...),
    user_id: str = Depends(get_current_user_id),
):
    """Toggle one persisted roadmap milestone and return the recalculated progress."""
    try:
        progress_doc = toggle_roadmap_checkpoint(
            user_id=user_id,
            week=payload.week,
            completed=payload.completed,
            learning_path_id=payload.learningPathId,
        )
    except (ValueError, TypeError):
        raise HTTPException(status_code=404, detail="Learning path milestone not found or unauthorized")
    return {"success": True, "data": progress_doc, "roadmap": progress_doc.get("roadmap", [])}
