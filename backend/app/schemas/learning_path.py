from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

class CourseItem(BaseModel):
    title: str
    provider: Optional[str] = ""
    url: Optional[str] = ""
    duration: Optional[str] = ""
    difficulty: Optional[str] = ""
    skillAddressed: Optional[str] = ""
    why_recommended: Optional[str] = ""

class CertificationItem(BaseModel):
    name: str
    provider: Optional[str] = ""
    skill: Optional[str] = ""
    why_recommended: Optional[str] = ""
    priority: Optional[str] = "High"
    url: Optional[str] = ""

class InterviewPrepItem(BaseModel):
    topic: str
    question: str
    keyConcept: Optional[str] = ""
    url: Optional[str] = ""
    resourceTitle: Optional[str] = ""

class ProjectTask(BaseModel):
    title: str
    description: Optional[str] = ""
    skills: List[str] = []
    difficulty: Optional[str] = "Intermediate"
    estimated_hours: Optional[int] = 8
    why_recommended: Optional[str] = ""
    suggested_stack: List[str] = []
    expected_resume_impact: Optional[str] = ""
    url: Optional[str] = ""

class RoadmapSubTask(BaseModel):
    title: str
    duration: Optional[str] = "2h"
    description: Optional[str] = ""

class RoadmapWeek(BaseModel):
    week: int
    title: str
    skill: Optional[str] = ""
    skills: List[str] = []
    current_level: Optional[str] = "Beginner"
    target_level: Optional[str] = "Intermediate"
    gap_level: Optional[str] = "Medium"
    estimated_hours: Optional[int] = 8
    estimated_days: Optional[int] = 2
    difficulty: Optional[str] = "Intermediate"
    objective: Optional[str] = ""
    why_this_matters: Optional[str] = ""
    why_this_week: Optional[str] = ""
    tasks: List[RoadmapSubTask] = []
    checkpoint: Optional[str] = ""
    courses: List[CourseItem] = []
    project: Optional[ProjectTask] = None
    status: Optional[str] = "not_started"
    completed: bool = False
    completed_at: Optional[str] = None
    actual_hours: Optional[int] = None

class LearningPathCreate(BaseModel):
    targetRole: str = "AI Engineer"
    durationWeeks: Optional[int] = None
    roadmap: List[RoadmapWeek] = []

class LearningPathUpdate(BaseModel):
    roadmap: Optional[List[RoadmapWeek]] = None
    durationWeeks: Optional[int] = None

class LearningPathResponse(BaseModel):
    id: str
    userId: str
    targetRole: str
    durationWeeks: int
    estimatedCompletionHours: Optional[int] = 0
    estimatedCompletionDays: Optional[int] = 0
    initialReadiness: Optional[int] = 50
    careerReadiness: Optional[int] = 50
    roadmap: List[RoadmapWeek]
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
