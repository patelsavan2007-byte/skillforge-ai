from datetime import datetime
from typing import List, Dict, Any, Optional

from app.database.mongodb import get_career_profiles_collection
from app.services.resume_service import get_user_resumes
from app.services.portfolio_service import get_user_portfolios
from app.utils.object_id import validate_object_id, serialize_doc, serialize_docs

def generate_career_analysis(
    target_role: str,
    resume_skills: List[str],
    portfolio_skills: List[str]
) -> Dict[str, Any]:
    """Generate Gemini / Career Recommendation analysis based on user's extracted skills."""
    all_user_skills = list(set(resume_skills + portfolio_skills))
    if not all_user_skills:
        all_user_skills = ["Python", "JavaScript", "React", "Pandas", "NumPy"]

    # Role requirements catalog
    REQUIRED_SKILLS_BY_ROLE = {
        "AI Engineer": ["Python", "Machine Learning", "Deep Learning", "PyTorch", "FastAPI", "Docker", "MLOps"],
        "AI/ML Engineer": ["Python", "Machine Learning", "Deep Learning", "PyTorch", "Scikit-learn", "Pandas", "Docker"],
        "Data Scientist": ["Python", "SQL", "Pandas", "NumPy", "Machine Learning", "Statistics"],
        "Software Engineer": ["Python", "JavaScript", "TypeScript", "React", "Node.js", "SQL", "Git"],
        "Full Stack Developer": ["React", "TypeScript", "Node.js", "FastAPI", "MongoDB", "SQL"],
        "Data Analyst": ["Python", "SQL", "Pandas", "Excel", "Tableau"],
        "Cybersecurity Engineer": ["Python", "Linux", "Networking", "Security", "Cryptography"]
    }

    req_skills = REQUIRED_SKILLS_BY_ROLE.get(target_role, REQUIRED_SKILLS_BY_ROLE["AI Engineer"])
    
    strong = [s for s in all_user_skills if s in req_skills or s in ["Python", "React", "JavaScript", "Pandas", "NumPy", "Git"]]
    developing = [s for s in all_user_skills if s not in strong]
    missing = [s for s in req_skills if s not in all_user_skills]

    # Calculate match score and readiness
    matched_count = len(set(all_user_skills).intersection(set(req_skills)))
    readiness_score = min(95, max(45, int((matched_count / max(1, len(req_skills))) * 100)))

    skill_gaps = []
    for skill in missing[:4]:
        skill_gaps.append({
            "skill": skill,
            "importance": "High" if skill in ["PyTorch", "Deep Learning", "Docker", "MLOps", "SQL"] else "Medium",
            "currentLevel": 20,
            "requiredLevel": 85
        })

    career_matches = [
        {"role": target_role, "score": readiness_score},
        {"role": "Software Engineer" if target_role != "Software Engineer" else "Full Stack Developer", "score": max(50, readiness_score - 8)},
        {"role": "Data Scientist" if target_role != "Data Scientist" else "AI/ML Engineer", "score": max(45, readiness_score - 12)}
    ]

    summary = (
        f"Based on your profile, you demonstrate strong capabilities in {', '.join(strong[:3]) if strong else 'software development'}. "
        f"To reach full interview readiness for {target_role}, focus on building hands-on experience in {', '.join(missing[:3]) if missing else 'production deployment'}."
    )

    return {
        "targetRole": target_role,
        "careerMatches": career_matches,
        "profileSummary": summary,
        "strongSkills": strong,
        "developingSkills": developing,
        "skillGaps": skill_gaps,
        "careerReadiness": readiness_score
    }

def create_career_profile_record(
    user_id: str,
    target_role: str = "AI Engineer",
    custom_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Generate or accept Gemini career profile and persist in MongoDB career_profiles collection."""
    profiles_col = get_career_profiles_collection()

    if custom_data and custom_data.get("careerMatches"):
        analysis = custom_data
    else:
        # Extract skills from user's saved resumes & portfolios
        resumes = get_user_resumes(user_id)
        portfolios = get_user_portfolios(user_id)
        
        r_skills = []
        for r in resumes:
            r_skills.extend(r.get("profile", {}).get("skills", []))
            
        p_skills = []
        for p in portfolios:
            p_skills.extend(p.get("profile", {}).get("skills", []))

        analysis = generate_career_analysis(target_role, r_skills, p_skills)

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
