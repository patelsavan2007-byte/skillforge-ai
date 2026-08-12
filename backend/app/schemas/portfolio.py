from typing import List, Optional, Any
from pydantic import BaseModel, HttpUrl

class PortfolioProject(BaseModel):
    name: Optional[str] = ""
    description: Optional[str] = ""
    technologies: List[str] = []
    github: Optional[str] = ""
    url: Optional[str] = ""

class PortfolioProfile(BaseModel):
    name: Optional[str] = ""
    bio: Optional[str] = ""
    skills: List[str] = []
    projects: List[PortfolioProject] = []
    experience: List[Any] = []
    certifications: List[Any] = []

class PortfolioCreate(BaseModel):
    url: str
    profile: Optional[PortfolioProfile] = None

class PortfolioResponse(BaseModel):
    id: str
    userId: str
    url: str
    profile: PortfolioProfile
    analyzedAt: Optional[str] = None
    updatedAt: Optional[str] = None
