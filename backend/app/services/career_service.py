import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.database.mongodb import get_career_profiles_collection
from app.services.gemini_service import analyze_career_gap_with_gemini
from app.utils.object_id import validate_object_id, serialize_doc, serialize_docs

logger = logging.getLogger("skillforge.career_service")

REQUIRED_SKILLS_BY_ROLE = {
    "AI Engineer": ["Python", "Machine Learning", "Deep Learning", "PyTorch", "FastAPI", "Docker", "MLOps"],
    "AI/ML Engineer": ["Python", "Machine Learning", "Deep Learning", "PyTorch", "Scikit-learn", "Pandas", "Docker"],
    "Data Scientist": ["Python", "SQL", "Pandas", "NumPy", "Machine Learning", "Statistics", "Data Visualization"],
    "Software Engineer": ["Python", "JavaScript", "TypeScript", "React", "Node.js", "SQL", "Git"],
    "Full Stack Developer": ["React", "TypeScript", "Node.js", "FastAPI", "MongoDB", "SQL", "Tailwind CSS"],
    "Data Analyst": ["Python", "SQL", "Pandas", "Excel", "Tableau", "Power BI", "Statistics"],
    "Cybersecurity Engineer": ["Python", "Linux", "Networking", "Security", "Cryptography", "Wireshark"]
}

def generate_career_analysis(
    target_role: str,
    unified_profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate skill gap analysis comparing UNIFIED STUDENT PROFILE vs TARGET ROLE REQUIREMENTS.
    Combines deterministic heuristic matching + Gemini AI reasoning.
    """
    user_skills = [s.strip() for s in unified_profile.get("skills", []) if isinstance(s, str)]
    user_skills_lower = set(s.lower() for s in user_skills)

    req_skills = REQUIRED_SKILLS_BY_ROLE.get(target_role, REQUIRED_SKILLS_BY_ROLE["AI/ML Engineer"])
    
    # 1. Deterministic Heuristic Match
    matched_skills = [s for s in req_skills if s.lower() in user_skills_lower]
    missing_skills = [s for s in req_skills if s.lower() not in user_skills_lower]

    strong = [s for s in user_skills if any(s.lower() == r.lower() for r in req_skills) or s in ["Python", "JavaScript", "React", "Git", "SQL"]]
    developing = [s for s in user_skills if s not in strong]
    
    if not strong and user_skills:
        strong = user_skills[:3]

    matched_ratio = len(matched_skills) / max(1, len(req_skills))
    heuristic_score = min(95, max(35, int(matched_ratio * 100)))

    # 2. Try Gemini AI reasoning for career gap analysis
    gemini_gap = analyze_career_gap_with_gemini(unified_profile, target_role)
    if gemini_gap:
        return {
            "targetRole": target_role,
            "careerMatches": [
                {"role": target_role, "score": gemini_gap.get("careerReadiness", heuristic_score)},
                {"role": "Software Engineer" if target_role != "Software Engineer" else "Full Stack Developer", "score": max(45, gemini_gap.get("careerReadiness", heuristic_score) - 10)},
                {"role": "Data Scientist" if target_role != "Data Scientist" else "AI/ML Engineer", "score": max(40, gemini_gap.get("careerReadiness", heuristic_score) - 15)}
            ],
            "profileSummary": gemini_gap.get("profileSummary") or f"Profile evaluated for {target_role}.",
            "strongSkills": gemini_gap.get("strongSkills") or strong,
            "developingSkills": gemini_gap.get("developingSkills") or developing,
            "skillGaps": gemini_gap.get("skillGaps") or [
                {"skill": s, "importance": "High" if idx < 2 else "Medium", "currentLevel": 20, "requiredLevel": 85}
                for idx, s in enumerate(missing_skills[:5])
            ],
            "careerReadiness": gemini_gap.get("careerReadiness", heuristic_score),
            "missingTechnologies": gemini_gap.get("missingTechnologies") or missing_skills,
            "missingProjectExperience": gemini_gap.get("missingProjectExperience") or [f"Hands-on {target_role} production project"],
            "recommendedNextSkills": gemini_gap.get("recommendedNextSkills") or missing_skills[:3]
        }

    # HEURISTIC FALLBACK
    skill_gaps = [
        {
            "skill": skill,
            "importance": "High" if skill in ["PyTorch", "Deep Learning", "Docker", "MLOps", "SQL", "React"] else "Medium",
            "currentLevel": 25,
            "requiredLevel": 85
        }
        for skill in missing_skills[:5]
    ]

    career_matches = [
        {"role": target_role, "score": heuristic_score},
        {"role": "Software Engineer" if target_role != "Software Engineer" else "Full Stack Developer", "score": max(45, heuristic_score - 8)},
        {"role": "Data Scientist" if target_role != "Data Scientist" else "AI/ML Engineer", "score": max(40, heuristic_score - 12)}
    ]

    summary = (
        f"Based on your profile, you demonstrate strong foundational capabilities in {', '.join(strong[:3]) if strong else 'software development'}. "
        f"To reach full interview readiness for {target_role}, focus on filling key gaps in {', '.join(missing_skills[:3]) if missing_skills else 'production deployment'}."
    )

    return {
        "targetRole": target_role,
        "careerMatches": career_matches,
        "profileSummary": summary,
        "strongSkills": strong,
        "developingSkills": developing,
        "skillGaps": skill_gaps,
        "careerReadiness": heuristic_score,
        "missingTechnologies": missing_skills,
        "missingProjectExperience": [f"Full-stack/AI production project targeting {target_role}"],
        "recommendedNextSkills": missing_skills[:3]
    }

def create_career_profile_record(
    user_id: str,
    target_role: str = "AI Engineer",
    unified_profile: Optional[Dict[str, Any]] = None,
    custom_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Persist structured career profile analysis in MongoDB career_profiles collection."""
    profiles_col = get_career_profiles_collection()

    if custom_data and custom_data.get("careerMatches"):
        analysis = custom_data
    else:
        profile_obj = unified_profile or {"skills": ["Python", "JavaScript", "React"]}
        analysis = generate_career_analysis(target_role, profile_obj)

    now = datetime.utcnow()
    doc = {
        "userId": user_id,
        "targetRole": analysis.get("targetRole", target_role),
        "careerMatches": analysis.get("careerMatches", []),
        "profileSummary": analysis.get("profileSummary", ""),
        "strongSkills": analysis.get("strongSkills", []),
        "developingSkills": analysis.get("developingSkills", []),
        "skillGaps": analysis.get("skillGaps", []),
        "careerReadiness": analysis.get("careerReadiness", 70),
        "missingTechnologies": analysis.get("missingTechnologies", []),
        "missingProjectExperience": analysis.get("missingProjectExperience", []),
        "recommendedNextSkills": analysis.get("recommendedNextSkills", []),
        "createdAt": now,
        "updatedAt": now,
    }

    result = profiles_col.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    doc["id"] = str(result.inserted_id)
    return serialize_doc(doc)

def get_user_career_profiles(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve user career profiles sorted by creation date."""
    profiles_col = get_career_profiles_collection()
    docs = list(profiles_col.find({"userId": user_id}).sort("createdAt", -1))
    return serialize_docs(docs)

def get_career_profile_by_id(profile_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve single career profile strictly isolated by userId."""
    profiles_col = get_career_profiles_collection()
    oid = validate_object_id(profile_id)
    doc = profiles_col.find_one({"_id": oid, "userId": user_id})
    return serialize_doc(doc)
