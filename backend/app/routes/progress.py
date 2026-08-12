from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Body
from app.routes.auth import get_current_user_id
from app.schemas.progress import ProgressUpdate
from app.services.progress_service import (
    get_user_progress,
    update_user_progress,
)

router = APIRouter(prefix="/api/progress", tags=["progress"])

@router.get("", response_model=Dict[str, Any])
async def get_progress(user_id: str = Depends(get_current_user_id)):
    """Retrieve user's unique progress record from MongoDB progress collection."""
    progress_doc = get_user_progress(user_id)
    return {"success": True, "data": progress_doc}

@router.put("", response_model=Dict[str, Any])
async def replace_progress(
    payload: ProgressUpdate = Body(...),
    user_id: str = Depends(get_current_user_id)
):
    """Replace/Upsert progress document for authenticated user."""
    updates = payload.model_dump(exclude_none=True)
    updated_doc = update_user_progress(user_id, updates)
    return {"success": True, "data": updated_doc}

@router.patch("", response_model=Dict[str, Any])
async def patch_progress(
    payload: ProgressUpdate = Body(...),
    user_id: str = Depends(get_current_user_id)
):
    """Patch progress document for authenticated user."""
    updates = payload.model_dump(exclude_none=True)
    updated_doc = update_user_progress(user_id, updates)
    return {"success": True, "data": updated_doc}
