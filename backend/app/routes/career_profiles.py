from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, File, UploadFile, Form
from pydantic import BaseModel

from app.routes.auth import get_current_user_id
from app.schemas.career_profile import CareerProfileCreate
from app.services.resume_service import create_resume_record, get_latest_user_resume, get_resume_by_id
from app.services.portfolio_service import analyze_portfolio_url, create_portfolio_record
from app.services.profile_merge_service import merge_student_profiles
from app.services.career_service import (
    create_career_profile_record,
    get_user_career_profiles,
    get_career_profile_by_id,
    generate_career_analysis
)
from app.services.learning_service import create_learning_path_record

router = APIRouter(prefix="/api/career-profiles", tags=["career_profiles"])

class AnalyzeRequestJSON(BaseModel):
    resumeId: Optional[str] = None
    portfolioUrl: Optional[str] = None
    targetRole: Optional[str] = "AI/ML Engineer"

@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_career_pipeline(
    file: Optional[UploadFile] = File(None),
    portfolio_url: Optional[str] = Form(None),
    target_role: Optional[str] = Form("AI/ML Engineer"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Unified personalized career analysis pipeline handling 4 cases:
    1. Resume only
    2. Portfolio only
    3. Resume + Portfolio (Merged unified profile)
    4. Target role comparison + skill gap + personalized roadmap recommendations
    """
    target = (target_role or "AI/ML Engineer").strip()
    resume_doc = None
    portfolio_doc = None

    # Case 1: Handle uploaded resume file
    if file and file.filename:
        file_bytes = await file.read()
        try:
            resume_doc = create_resume_record(
                user_id=user_id,
                file_name=file.filename,
                file_bytes=file_bytes
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to process resume file: {str(e)}")
    else:
        # Fall back to latest uploaded resume for this user if available
        resume_doc = get_latest_user_resume(user_id)

    # Case 2: Handle portfolio URL
    p_url = (portfolio_url or "").strip()
    if p_url:
        try:
            p_profile = await analyze_portfolio_url(p_url)
            portfolio_doc = create_portfolio_record(
                user_id=user_id,
                url=p_url,
                profile=p_profile
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to analyze portfolio URL: {str(e)}")

    resume_profile = resume_doc.get("profile") if resume_doc else None
    portfolio_profile = portfolio_doc.get("profile") if portfolio_doc else None

    # Case 3: Merge profiles
    try:
        unified_profile = merge_student_profiles(resume_profile, portfolio_profile)
    except ValueError as ve:
        raise HTTPException(
            status_code=400,
            detail=str(ve)
        )

    # Case 4: Target role skill gap analysis
    career_doc = create_career_profile_record(
        user_id=user_id,
        target_role=target,
        unified_profile=unified_profile
    )

    # Generate personalized recommendations & roadmap
    learning_doc = create_learning_path_record(
        user_id=user_id,
        target_role=target,
        duration_weeks=8,
        unified_profile=unified_profile,
        skill_gaps=career_doc.get("skillGaps", [])
    )

    return {
        "success": True,
        "message": "Personalized career analysis completed successfully",
        "data": {
            "targetRole": target,
            "unifiedProfile": unified_profile,
            "careerProfile": career_doc,
            "learningPath": learning_doc,
            "resumeId": resume_doc.get("id") if resume_doc else None,
            "portfolioId": portfolio_doc.get("id") if portfolio_doc else None
        }
    }

@router.post("", response_model=Dict[str, Any])
async def create_career_profile(
    payload: Optional[CareerProfileCreate] = Body(None),
    user_id: str = Depends(get_current_user_id)
):
    """Run career analysis and persist structured profile to MongoDB career_profiles collection."""
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
