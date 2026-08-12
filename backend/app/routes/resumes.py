from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Body, Request

from app.routes.auth import get_current_user_id
from app.schemas.resume import ResumeCreate, ResumeUpdate, ResumeResponse
from app.services.resume_service import (
    create_resume_record,
    get_user_resumes,
    get_latest_user_resume,
    get_resume_by_id,
    update_resume_by_id,
    update_latest_resume,
    delete_resume_by_id,
)

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


@router.post("/upload", response_model=Dict[str, Any])
@router.post("", response_model=Dict[str, Any])
async def upload_resume(
    file: Optional[UploadFile] = File(None),
    payload: Optional[ResumeCreate] = Body(None),
    user_id: str = Depends(get_current_user_id)
):
    """Upload resume file (PDF/DOCX/TXT), run Hugging Face oksomu/resume-ner, extract structured profile, and store in MongoDB."""
    file_bytes = None
    file_name = "resume.pdf"
    custom_profile = None

    if file:
        file_bytes = await file.read()
        file_name = file.filename or "resume.pdf"

    if payload:
        if payload.fileName:
            file_name = payload.fileName
        if payload.profile:
            custom_profile = payload.profile.model_dump()

    try:
        doc = create_resume_record(
            user_id=user_id,
            file_name=file_name,
            file_bytes=file_bytes,
            raw_text=payload.rawText if payload else None,
            custom_profile=custom_profile
        )
        return {
            "success": True,
            "message": "Resume processed and stored successfully",
            "data": doc,
            "resume": doc
        }
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")


@router.get("", response_model=Dict[str, Any])
async def get_resume(user_id: str = Depends(get_current_user_id)):
    """Retrieve current active extracted resume profile for authenticated user."""
    latest = get_latest_user_resume(user_id)
    if not latest:
        resumes = get_user_resumes(user_id)
        if resumes:
            latest = resumes[0]

    if not latest:
        return {
            "success": True,
            "message": "No resume uploaded yet",
            "data": None,
            "resume": None
        }

    return {
        "success": True,
        "data": latest,
        "resume": latest
    }


@router.get("/{resume_id}", response_model=Dict[str, Any])
async def get_resume_by_identifier(resume_id: str, user_id: str = Depends(get_current_user_id)):
    """Retrieve specific resume by ID with strict user isolation."""
    resume = get_resume_by_id(resume_id, user_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found or unauthorized access.")
    return {"success": True, "data": resume, "resume": resume}


@router.put("/{resume_id}", response_model=Dict[str, Any])
@router.put("", response_model=Dict[str, Any])
async def update_resume(
    resume_id: Optional[str] = None,
    payload: ResumeUpdate = Body(...),
    user_id: str = Depends(get_current_user_id)
):
    """Allows user to manually edit and update extracted resume profile in MongoDB."""
    profile_dict = payload.profile.model_dump()
    
    if resume_id and resume_id != "active":
        updated = update_resume_by_id(
            resume_id=resume_id,
            user_id=user_id,
            updated_profile=profile_dict,
            category=payload.resumeCategory
        )
    else:
        updated = update_latest_resume(
            user_id=user_id,
            updated_profile=profile_dict,
            category=payload.resumeCategory
        )

    if not updated:
        raise HTTPException(status_code=404, detail="Resume not found to update.")

    return {
        "success": True,
        "message": "Resume profile updated successfully",
        "data": updated,
        "resume": updated
    }


@router.delete("/{resume_id}", response_model=Dict[str, Any])
@router.delete("", response_model=Dict[str, Any])
async def delete_resume(
    resume_id: Optional[str] = None,
    user_id: str = Depends(get_current_user_id)
):
    """Delete specific resume or active user resume from MongoDB."""
    if not resume_id or resume_id == "active":
        latest = get_latest_user_resume(user_id)
        if not latest:
            raise HTTPException(status_code=404, detail="No resume found to delete.")
        resume_id = latest["id"]

    deleted = delete_resume_by_id(resume_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Resume not found or unauthorized.")
    return {"success": True, "message": "Resume deleted successfully"}
