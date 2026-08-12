from typing import Dict, List, Optional, Any
from pydantic import BaseModel

class CompletedItem(BaseModel):
    id: Optional[str] = ""
    completedAt: Optional[str] = None

class ProgressUpdate(BaseModel):
    skills: Optional[Dict[str, int]] = None
    completedCourses: Optional[List[Any]] = None
    completedProjects: Optional[List[Any]] = None
    roadmapProgress: Optional[int] = None
    interviewScore: Optional[int] = None
    careerReadiness: Optional[int] = None

class ProgressResponse(BaseModel):
    id: str
    userId: str
    skills: Dict[str, int] = {}
    completedCourses: List[Any] = []
    completedProjects: List[Any] = []
    roadmapProgress: int = 0
    interviewScore: int = 0
    careerReadiness: int = 0
    updatedAt: Optional[str] = None
