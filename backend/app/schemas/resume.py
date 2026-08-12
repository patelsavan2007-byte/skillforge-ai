from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

class EducationItem(BaseModel):
    degree: Optional[str] = ""
    field: Optional[str] = ""
    institution: Optional[str] = ""
    startDate: Optional[str] = ""
    endDate: Optional[str] = ""

class ExperienceItem(BaseModel):
    company: Optional[str] = ""
    title: Optional[str] = ""
    duration: Optional[str] = ""
    description: Optional[str] = ""

class ProjectItem(BaseModel):
    name: Optional[str] = ""
    description: Optional[str] = ""
    technologies: List[str] = []
    url: Optional[str] = ""

class ResumeProfile(BaseModel):
    name: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""
    location: Optional[str] = ""
    education: List[EducationItem] = []
    skills: List[str] = []
    experience: List[ExperienceItem] = []
    certifications: List[str] = []
    projects: List[ProjectItem] = []

class ResumeCreate(BaseModel):
    fileName: str = "resume.pdf"
    profile: Optional[ResumeProfile] = None
    rawText: Optional[str] = ""
    resumeCategory: Optional[str] = "Information-Technology"

class ResumeResponse(BaseModel):
    id: str
    userId: str
    fileName: str
    profile: ResumeProfile
    resumeCategory: Optional[str] = "Information-Technology"
    uploadedAt: Optional[str] = None
    updatedAt: Optional[str] = None
