from typing import Dict, List, Optional, Any
from pydantic import BaseModel

class CompletedItem(BaseModel):
    id: Optional[str] = ""
    completedAt: Optional[str] = None


class SkillProgressItem(BaseModel):
    skill: str
    status: str = "not_started"
    progress: int = 0
    completed: bool = False


class RoadmapCheckpointUpdate(BaseModel):
    week: int
    completed: bool
    learningPathId: Optional[str] = None

class ProgressUpdate(BaseModel):
    skills: Optional[Dict[str, int]] = None
    completedCourses: Optional[List[Any]] = None
    completedProjects: Optional[List[Any]] = None
    roadmapProgress: Optional[int] = None
    interviewScore: Optional[int] = None
    careerReadiness: Optional[int] = None
    # Fields linking progress to real career analysis
    targetRole: Optional[str] = None
    skillGapItems: Optional[List[str]] = None
    skillProgress: Optional[List[SkillProgressItem]] = None
    totalRoadmapItems: Optional[int] = None
    completedRoadmapItems: Optional[int] = None

class ProgressResponse(BaseModel):
    id: str
    userId: str
    skills: Dict[str, int] = {}
    completedCourses: List[Any] = []
    completedProjects: List[Any] = []
    roadmapProgress: int = 0
    interviewScore: int = 0
    careerReadiness: int = 0
    # Fields linking progress to real career analysis
    targetRole: Optional[str] = None
    skillGapItems: List[str] = []
    skillProgress: List[SkillProgressItem] = []
    totalRoadmapItems: int = 0
    completedRoadmapItems: int = 0
    updatedAt: Optional[str] = None
