from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, File, UploadFile, Form
from pydantic import BaseModel

from app.routes.auth import get_current_user_id
from app.schemas.career_profile import CareerProfileCreate
from app.services.resume_service import create_resume_record
from app.services.portfolio_service import analyze_portfolio_url, create_portfolio_record
from app.services.profile_merge_service import merge_student_profiles
from app.services.career_service import (
    create_career_profile_record,
    get_user_career_profiles,
    get_career_profile_by_id,
    generate_career_analysis
)
from app.services.learning_service import create_learning_path_record
from app.services.progress_service import initialize_progress_from_career_analysis
from app.services.progress_service import get_user_progress
from app.database.mongodb import get_learning_paths_collection, get_portfolios_collection, get_resumes_collection
from app.utils.object_id import serialize_doc

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
    # Deliberately do not load a historical resume here.  This endpoint is an
    # "analyze current inputs" action: only an uploaded file participates.

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

    # Generate personalized recommendations & roadmap with dynamic duration
    learning_doc = create_learning_path_record(
        user_id=user_id,
        target_role=target,
        duration_weeks=None,
        unified_profile=unified_profile,
        skill_gaps=career_doc.get("true_skill_gaps", []),
        user_strengths=career_doc.get("user_strengths", [])
    )

    # Seed progress from the real deterministic output — never from hardcoded defaults
    true_skill_gaps = career_doc.get("true_skill_gaps") or []
    roadmap = learning_doc.get("roadmap") or []
    career_readiness = int(career_doc.get("careerReadiness", 0))
    progress_doc = initialize_progress_from_career_analysis(
        user_id=user_id,
        target_role=target,
        true_skill_gaps=true_skill_gaps,
        roadmap=roadmap,
        career_readiness=career_readiness,
    )

    return {
        "success": True,
        "message": "Personalized career analysis completed successfully",
        "data": {
            "targetRole": target,
            "unifiedProfile": unified_profile,
            "careerProfile": career_doc,
            "learningPath": learning_doc,
            "progress": progress_doc,
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


@router.get("/latest-analysis", response_model=Dict[str, Any])
async def get_latest_analysis(user_id: str = Depends(get_current_user_id)):
    """Rehydrate the most recent persisted analysis for the authenticated user."""
    profiles = get_user_career_profiles(user_id)
    if not profiles:
        return {"success": True, "data": None}

    career_profile = profiles[0]
    paths_col = get_learning_paths_collection()
    resumes_col = get_resumes_collection()
    portfolios_col = get_portfolios_collection()
    learning_path = paths_col.find_one({"userId": user_id}, sort=[("createdAt", -1)])
    resume = resumes_col.find_one({"userId": user_id}, sort=[("uploadedAt", -1)])
    portfolio = portfolios_col.find_one({"userId": user_id}, sort=[("analyzedAt", -1)])
    unified_profile = career_profile.get("unifiedProfile") or merge_student_profiles(
        resume.get("profile") if resume else None,
        portfolio.get("profile") if portfolio else None,
    )
    return {
        "success": True,
        "data": {
            "role": career_profile.get("targetRole", "AI/ML Engineer"),
            "unifiedProfile": unified_profile,
            "careerProfile": career_profile,
            "learningPath": serialize_doc(learning_path) if learning_path else None,
            "progress": get_user_progress(user_id),
            "resumeId": str(resume["_id"]) if resume else None,
            "portfolioId": str(portfolio["_id"]) if portfolio else None,
        },
    }

@router.get("/{profile_id}", response_model=Dict[str, Any])
async def get_career_profile(profile_id: str, user_id: str = Depends(get_current_user_id)):
    """Retrieve specific career profile by ID with strict user isolation."""
    profile = get_career_profile_by_id(profile_id, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Career profile not found")
    return {"success": True, "data": profile}
