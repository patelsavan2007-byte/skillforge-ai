import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from bson import ObjectId

from app.database.mongodb import get_resumes_collection
from app.utils.object_id import validate_object_id, serialize_doc, serialize_docs

from app.services.resume_parser import parse_file_to_text
from app.services.resume_ner import get_ner_service
from app.services.resume_extractor import build_structured_resume

logger = logging.getLogger("skillforge.resume_service")


def process_resume_and_extract(
    file_name: str,
    file_bytes: Optional[bytes] = None,
    raw_text: Optional[str] = None
) -> Dict[str, Any]:
    """Execute text extraction -> Gemini / Hugging Face NER -> structured profile extraction."""
    text = raw_text or ""
    if file_bytes and not text:
        text = parse_file_to_text(file_name, file_bytes)

    if not text.strip():
        raise ValueError("Resume text is empty or could not be extracted.")

    # 1. Try Gemini Resume Parser
    from app.services.gemini_service import analyze_resume_with_gemini
    gemini_profile = analyze_resume_with_gemini(text)
    if gemini_profile and (gemini_profile.get("skills") or gemini_profile.get("education") or gemini_profile.get("experience")):
        return gemini_profile

    # 2. Fallback to Hugging Face oksomu/resume-ner + heuristic extractor
    ner_service = get_ner_service()
    ner_entities = ner_service.extract_entities(text)
    structured_profile = build_structured_resume(text, ner_entities)
    return structured_profile


def create_resume_record(
    user_id: str,
    file_name: str,
    file_bytes: Optional[bytes] = None,
    raw_text: Optional[str] = None,
    custom_profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Extract resume NER profile and persist in PyMongo resumes collection."""
    resumes_col = get_resumes_collection()
    
    if custom_profile:
        profile_data = custom_profile
    else:
        profile_data = process_resume_and_extract(
            file_name=file_name,
            file_bytes=file_bytes,
            raw_text=raw_text
        )

    now = datetime.utcnow()
    doc = {
        "userId": user_id,
        "fileName": file_name,
        "profile": profile_data,
        "resumeCategory": "Information-Technology",
        "uploadedAt": now,
        "updatedAt": now,
    }

    result = resumes_col.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    doc["id"] = str(result.inserted_id)
    return serialize_doc(doc)


def get_user_resumes(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve all stored resumes for an authenticated user."""
    resumes_col = get_resumes_collection()
    docs = list(resumes_col.find({"userId": user_id}).sort("uploadedAt", -1))
    return serialize_docs(docs)


def get_latest_user_resume(user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve active/latest uploaded resume profile for authenticated user."""
    resumes_col = get_resumes_collection()
    doc = resumes_col.find_one({"userId": user_id}, sort=[("uploadedAt", -1)])
    return serialize_doc(doc) if doc else None


def get_resume_by_id(resume_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve specific resume strictly isolated by userId."""
    resumes_col = get_resumes_collection()
    oid = validate_object_id(resume_id)
    doc = resumes_col.find_one({"_id": oid, "userId": user_id})
    return serialize_doc(doc)


def update_resume_by_id(
    resume_id: str,
    user_id: str,
    updated_profile: Dict[str, Any],
    category: Optional[str] = "Information-Technology"
) -> Optional[Dict[str, Any]]:
    """Update profile data for a specific user resume document."""
    resumes_col = get_resumes_collection()
    oid = validate_object_id(resume_id)

    now = datetime.utcnow()
    result = resumes_col.update_one(
        {"_id": oid, "userId": user_id},
        {"$set": {"profile": updated_profile, "resumeCategory": category, "updatedAt": now}}
    )

    if result.matched_count == 0:
        return None

    updated_doc = resumes_col.find_one({"_id": oid, "userId": user_id})
    return serialize_doc(updated_doc)


def update_latest_resume(
    user_id: str,
    updated_profile: Dict[str, Any],
    category: Optional[str] = "Information-Technology"
) -> Optional[Dict[str, Any]]:
    """Update profile data for user's latest active resume."""
    latest = get_latest_user_resume(user_id)
    if not latest:
        # Create a new record if none exists
        return create_resume_record(
            user_id=user_id,
            file_name="resume.pdf",
            custom_profile=updated_profile
        )
    return update_resume_by_id(latest["id"], user_id, updated_profile, category)


def delete_resume_by_id(resume_id: str, user_id: str) -> bool:
    """Delete a resume document strictly isolated by userId."""
    resumes_col = get_resumes_collection()
    oid = validate_object_id(resume_id)
    result = resumes_col.delete_one({"_id": oid, "userId": user_id})
    return result.deleted_count > 0
