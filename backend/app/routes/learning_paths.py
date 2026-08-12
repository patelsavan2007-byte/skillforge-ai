from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from app.routes.auth import get_current_user_id
from app.schemas.learning_path import LearningPathCreate, LearningPathUpdate
from app.services.learning_service import (
    create_learning_path_record,
    get_user_learning_paths,
    get_learning_path_by_id,
    update_learning_path_by_id,
)

router = APIRouter(prefix="/api/learning-paths", tags=["learning_paths"])

@router.post("", response_model=Dict[str, Any])
async def create_learning_path(
    payload: Optional[LearningPathCreate] = Body(None),
    user_id: str = Depends(get_current_user_id)
):
    """Generate Gemini learning roadmap and persist to MongoDB learning_paths collection."""
    target_role = payload.targetRole if payload else "AI Engineer"
    duration_weeks = payload.durationWeeks if payload else 8
    custom_roadmap = [w.model_dump() for w in payload.roadmap] if payload and payload.roadmap else None

    doc = create_learning_path_record(
        user_id=user_id,
        target_role=target_role,
        duration_weeks=duration_weeks,
        custom_roadmap=custom_roadmap
    )
    return {"success": True, "data": doc}

@router.get("", response_model=Dict[str, Any])
async def list_learning_paths(user_id: str = Depends(get_current_user_id)):
    """Retrieve all learning paths for authenticated user."""
    paths = get_user_learning_paths(user_id)
    return {"success": True, "count": len(paths), "data": paths}

@router.get("/{path_id}", response_model=Dict[str, Any])
async def get_learning_path(path_id: str, user_id: str = Depends(get_current_user_id)):
    """Retrieve learning path by ID with strict user isolation."""
    path_doc = get_learning_path_by_id(path_id, user_id)
    if not path_doc:
        raise HTTPException(status_code=404, detail="Learning path not found")
    return {"success": True, "data": path_doc}

@router.patch("/{path_id}", response_model=Dict[str, Any])
async def update_learning_path(
    path_id: str,
    payload: LearningPathUpdate = Body(...),
    user_id: str = Depends(get_current_user_id)
):
    """Patch learning roadmap or weeks with strict user isolation."""
    roadmap_dicts = [w.model_dump() for w in payload.roadmap] if payload.roadmap is not None else None
    
    updated = update_learning_path_by_id(
        path_id=path_id,
        user_id=user_id,
        roadmap=roadmap_dicts,
        duration_weeks=payload.durationWeeks
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Learning path not found or unauthorized")
    return {"success": True, "data": updated}
