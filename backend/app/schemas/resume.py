from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class PersonalDetails(BaseModel):
    name: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""
    location: Optional[str] = ""


class EducationItem(BaseModel):
    degree: Optional[str] = ""
    field: Optional[str] = ""
    institution: Optional[str] = ""
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    sgpa: Optional[float] = None
    cgpa: Optional[float] = None


class ExperienceItem(BaseModel):
    company: Optional[str] = ""
    title: Optional[str] = ""
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    duration: Optional[str] = ""
    description: Optional[str] = ""


class ProjectItem(BaseModel):
    name: Optional[str] = ""
    description: Optional[str] = ""
    technologies: List[str] = []
    url: Optional[str] = None


class RawEntityItem(BaseModel):
    text: str
    label: str
    score: float


class ResumeProfile(BaseModel):
    personal: Optional[PersonalDetails] = Field(default_factory=PersonalDetails)
    education: List[EducationItem] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)
    rawEntities: List[RawEntityItem] = Field(default_factory=list)


class ResumeCreate(BaseModel):
    fileName: str = "resume.pdf"
    profile: Optional[ResumeProfile] = None
    rawText: Optional[str] = ""
    resumeCategory: Optional[str] = "Information-Technology"


class ResumeUpdate(BaseModel):
    profile: ResumeProfile
    resumeCategory: Optional[str] = "Information-Technology"


class ResumeResponse(BaseModel):
    id: str
    userId: str
    fileName: str
    profile: ResumeProfile
    resumeCategory: Optional[str] = "Information-Technology"
    uploadedAt: Optional[str] = None
    updatedAt: Optional[str] = None
