from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Body
from app.routes.auth import get_current_user_id
from app.schemas.resume import ResumeCreate, ResumeResponse
from app.services.resume_service import (
    create_resume_record,
    get_user_resumes,
    get_resume_by_id,
    delete_resume_by_id,
)

router = APIRouter(prefix="/api/resumes", tags=["resumes"])

@router.post("", response_model=Dict[str, Any])
async def upload_resume(
    file: Optional[UploadFile] = File(None),
    payload: Optional[ResumeCreate] = Body(None),
    user_id: str = Depends(get_current_user_id)
):
    """Upload resume file or profile payload, run NER extraction, and persist to MongoDB resumes collection."""
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

    doc = create_resume_record(
        user_id=user_id,
        file_name=file_name,
        file_bytes=file_bytes,
        raw_text=payload.rawText if payload else None,
        custom_profile=custom_profile
    )
    return {"success": True, "data": doc}

@router.get("", response_model=Dict[str, Any])
async def list_resumes(user_id: str = Depends(get_current_user_id)):
    """Retrieve all resumes uploaded by authenticated user."""
    resumes = get_user_resumes(user_id)
    return {"success": True, "count": len(resumes), "data": resumes}

@router.get("/{resume_id}", response_model=Dict[str, Any])
async def get_resume(resume_id: str, user_id: str = Depends(get_current_user_id)):
    """Retrieve specific resume by ID with strict user isolation."""
    resume = get_resume_by_id(resume_id, user_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return {"success": True, "data": resume}

@router.delete("/{resume_id}", response_model=Dict[str, Any])
async def delete_resume(resume_id: str, user_id: str = Depends(get_current_user_id)):
    """Delete specific resume by ID with strict user isolation."""
    deleted = delete_resume_by_id(resume_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Resume not found or unauthorized")
    return {"success": True, "message": "Resume deleted successfully"}
