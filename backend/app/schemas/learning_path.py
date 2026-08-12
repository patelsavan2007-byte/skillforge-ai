from typing import List, Optional, Any, Dict
from pydantic import BaseModel

class CourseItem(BaseModel):
    title: str
    provider: Optional[str] = ""
    url: Optional[str] = ""
    duration: Optional[str] = ""
    difficulty: Optional[str] = ""

class ProjectTask(BaseModel):
    title: str
    description: Optional[str] = ""
    skills: List[str] = []

class RoadmapWeek(BaseModel):
    week: int
    title: str
    skills: List[str] = []
    courses: List[CourseItem] = []
    project: Optional[ProjectTask] = None
    completed: bool = False

class LearningPathCreate(BaseModel):
    targetRole: str = "AI Engineer"
    durationWeeks: int = 8
    roadmap: List[RoadmapWeek] = []

class LearningPathUpdate(BaseModel):
    roadmap: Optional[List[RoadmapWeek]] = None
    durationWeeks: Optional[int] = None

class LearningPathResponse(BaseModel):
    id: str
    userId: str
    targetRole: str
    durationWeeks: int
    roadmap: List[RoadmapWeek]
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
