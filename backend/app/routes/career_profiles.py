from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from app.routes.auth import get_current_user_id
from app.schemas.career_profile import CareerProfileCreate
from app.services.career_service import (
    create_career_profile_record,
    get_user_career_profiles,
    get_career_profile_by_id,
)

router = APIRouter(prefix="/api/career-profiles", tags=["career_profiles"])

@router.post("", response_model=Dict[str, Any])
async def create_career_profile(
    payload: Optional[CareerProfileCreate] = Body(None),
    user_id: str = Depends(get_current_user_id)
):
    """Run Gemini career analysis and persist structured profile to MongoDB career_profiles collection."""
    target_role = payload.targetRole if payload else "AI Engineer"
    custom_data = payload.model_dump() if payload else None

    doc = create_career_profile_record(
        user_id=user_id,
        target_role=target_role,
        custom_data=custom_data
    )
    return {"success": True, "data": doc}

@router.get("", response_model=Dict[str, Any])
async def list_career_profiles(user_id: str = Depends(get_current_user_id)):
    """Retrieve all career profiles for authenticated user."""
    profiles = get_user_career_profiles(user_id)
    return {"success": True, "count": len(profiles), "data": profiles}

@router.get("/{profile_id}", response_model=Dict[str, Any])
async def get_career_profile(profile_id: str, user_id: str = Depends(get_current_user_id)):
    """Retrieve specific career profile by ID with strict user isolation."""
    profile = get_career_profile_by_id(profile_id, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Career profile not found")
    return {"success": True, "data": profile}
