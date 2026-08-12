from typing import List, Optional, Any
from pydantic import BaseModel

class CareerMatch(BaseModel):
    role: str
    score: int

class SkillGapItem(BaseModel):
    skill: str
    importance: Optional[str] = "Medium"
    currentLevel: int = 0
    requiredLevel: int = 80

class CareerProfileCreate(BaseModel):
    targetRole: str = "AI Engineer"
    careerMatches: List[CareerMatch] = []
    profileSummary: Optional[str] = ""
    strongSkills: List[str] = []
    developingSkills: List[str] = []
    skillGaps: List[SkillGapItem] = []
    careerReadiness: int = 70

class CareerProfileResponse(BaseModel):
    id: str
    userId: str
    targetRole: str
    careerMatches: List[CareerMatch]
    profileSummary: str
    strongSkills: List[str]
    developingSkills: List[str]
    skillGaps: List[SkillGapItem]
    careerReadiness: int
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
