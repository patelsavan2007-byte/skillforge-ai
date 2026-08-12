import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.database.mongodb import get_learning_paths_collection
from app.services.gemini_service import generate_recommendations_with_gemini
from app.utils.object_id import validate_object_id, serialize_doc, serialize_docs

logger = logging.getLogger("skillforge.learning_service")

def generate_personalized_recommendations(
    unified_profile: Dict[str, Any],
    target_role: str,
    skill_gaps: List[Dict[str, Any]],
    duration_weeks: int = 8
) -> Dict[str, Any]:
    """
    Generate personalized roadmap, courses, projects, certifications, interview questions, and advice
    directly linked to identified candidate skill gaps.
    Combines Gemini recommendations + fallback heuristics.
    """
    # 1. Try Gemini Recommendation Engine
    gemini_recs = generate_recommendations_with_gemini(unified_profile, target_role, skill_gaps)
    if gemini_recs and gemini_recs.get("roadmap"):
        return gemini_recs

    # HEURISTIC FALLBACK TAILORED TO SKILL GAPS
    gap_names = [g.get("skill", "") for g in skill_gaps if g.get("skill")]
    primary_gap = gap_names[0] if gap_names else "Machine Learning"
    secondary_gap = gap_names[1] if len(gap_names) > 1 else "Deep Learning"

    roadmap = [
        {
            "week": 1,
            "title": f"Fundamentals of {primary_gap}",
            "skills": [primary_gap, "Core Principles"],
            "courses": [
                {
                    "title": f"Mastering {primary_gap}",
                    "provider": "Coursera",
                    "url": "https://coursera.org",
                    "duration": "10 hours",
                    "difficulty": "Intermediate"
                }
            ],
            "project": {
                "title": f"{primary_gap} Hands-on Implementation",
                "description": f"Build a practical project focusing on {primary_gap}.",
                "skills": [primary_gap]
            },
            "completed": True
        },
        {
            "week": 2,
            "title": f"Advanced {secondary_gap} & Architecture",
            "skills": [secondary_gap, "System Design"],
            "courses": [
                {
                    "title": f"{secondary_gap} Specialization",
                    "provider": "DeepLearning.AI",
                    "url": "https://coursera.org",
                    "duration": "15 hours",
                    "difficulty": "Advanced"
                }
            ],
            "project": {
                "title": f"{secondary_gap} Production Pipeline",
                "description": f"Develop an end-to-end pipeline implementing {secondary_gap}.",
                "skills": [secondary_gap]
            },
            "completed": False
        },
        {
            "week": 3,
            "title": "API Integration & Docker Deployment",
            "skills": ["FastAPI", "Docker", "REST API"],
            "courses": [
                {
                    "title": "FastAPI & Docker Microservices",
                    "provider": "Udemy",
                    "url": "https://udemy.com",
                    "duration": "12 hours",
                    "difficulty": "Intermediate"
                }
            ],
            "project": {
                "title": f"Dockerized {target_role} API",
                "description": "Serve predictions via REST endpoints packaged in Docker.",
                "skills": ["Docker", "FastAPI"]
            },
            "completed": False
        },
        {
            "week": 4,
            "title": "Industry Capstone & Portfolio Publishing",
            "skills": ["Git", "CI/CD", "Documentation"],
            "courses": [
                {
                    "title": f"{target_role} Production Best Practices",
                    "provider": "SkillForge AI",
                    "url": "https://skillforge.ai",
                    "duration": "20 hours",
                    "difficulty": "Advanced"
                }
            ],
            "project": {
                "title": f"Production {target_role} System",
                "description": "Deploy complete system with documentation, monitoring, and live demo link.",
                "skills": [primary_gap, secondary_gap, "Docker", "FastAPI"]
            },
            "completed": False
        }
    ]

    courses = [
        {
            "title": f"{primary_gap} Masterclass",
            "provider": "Coursera",
            "url": "https://coursera.org",
            "duration": "12 hours",
            "difficulty": "Intermediate",
            "skillAddressed": primary_gap
        },
        {
            "title": f"{secondary_gap} in Production",
            "provider": "Udemy",
            "url": "https://udemy.com",
            "duration": "15 hours",
            "difficulty": "Advanced",
            "skillAddressed": secondary_gap
        }
    ]

    recommended_projects = [
        {
            "title": f"Real-world {primary_gap} System",
            "description": f"Implement a complete system demonstrating mastery of {primary_gap}.",
            "technologies": [primary_gap, "Python", "FastAPI"],
            "difficulty": "Advanced"
        },
        {
            "title": f"End-to-End {target_role} Platform",
            "description": f"Build and deploy a full-stack platform for {target_role} portfolio.",
            "technologies": [primary_gap, secondary_gap, "Docker", "MongoDB"],
            "difficulty": "Advanced"
        }
    ]

    certifications = [
        {"name": f"Professional {target_role} Certificate", "provider": "Google / AWS", "priority": "High"},
        {"name": f"Advanced {primary_gap} Developer", "provider": "DeepLearning.AI", "priority": "High"}
    ]

    interview_prep = [
        {
            "topic": primary_gap,
            "question": f"Explain key architectural trade-offs in {primary_gap} and how you optimize performance.",
            "keyConcept": f"Core mechanics and production considerations of {primary_gap}."
        },
        {
            "topic": "System Design",
            "question": f"How would you design a scalable system for {target_role}?",
            "keyConcept": "API design, load balancing, model caching, and database indexing."
        }
    ]

    career_advice = [
        f"Highlight hands-on projects featuring {primary_gap} prominently on your GitHub repository.",
        f"Tailor your resume headline specifically for '{target_role}' positions.",
        "Add architecture diagrams and live demo links to all portfolio projects."
    ]

    return {
        "durationWeeks": duration_weeks,
        "roadmap": roadmap[:duration_weeks],
        "courses": courses,
        "recommendedProjects": recommended_projects,
        "certifications": certifications,
        "interviewPrep": interview_prep,
        "careerAdvice": career_advice
    }

def create_learning_path_record(
    user_id: str,
    target_role: str = "AI Engineer",
    duration_weeks: int = 8,
    unified_profile: Optional[Dict[str, Any]] = None,
    skill_gaps: Optional[List[Dict[str, Any]]] = None,
    custom_roadmap: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Generate and persist personalized learning roadmap into MongoDB learning_paths collection."""
    paths_col = get_learning_paths_collection()
    
    if custom_roadmap:
        recs = {"roadmap": custom_roadmap, "durationWeeks": len(custom_roadmap)}
    else:
        profile_obj = unified_profile or {}
        gaps_obj = skill_gaps or []
        recs = generate_personalized_recommendations(profile_obj, target_role, gaps_obj, duration_weeks)

    now = datetime.utcnow()
    doc = {
        "userId": user_id,
        "targetRole": target_role,
        "durationWeeks": recs.get("durationWeeks", duration_weeks),
        "roadmap": recs.get("roadmap", []),
        "courses": recs.get("courses", []),
        "recommendedProjects": recs.get("recommendedProjects", []),
        "certifications": recs.get("certifications", []),
        "interviewPrep": recs.get("interviewPrep", []),
        "careerAdvice": recs.get("careerAdvice", []),
        "createdAt": now,
        "updatedAt": now,
    }

    result = paths_col.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    doc["id"] = str(result.inserted_id)
    return serialize_doc(doc)

def get_user_learning_paths(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve user learning paths sorted by creation date."""
    paths_col = get_learning_paths_collection()
    docs = list(paths_col.find({"userId": user_id}).sort("createdAt", -1))
    return serialize_docs(docs)

def get_learning_path_by_id(path_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve single learning path strictly isolated by userId."""
    paths_col = get_learning_paths_collection()
    oid = validate_object_id(path_id)
    doc = paths_col.find_one({"_id": oid, "userId": user_id})
    return serialize_doc(doc)

def update_learning_path_by_id(
    path_id: str,
    user_id: str,
    roadmap: Optional[List[Dict[str, Any]]] = None,
    duration_weeks: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """Update/patch learning roadmap strictly isolated by userId."""
    paths_col = get_learning_paths_collection()
    oid = validate_object_id(path_id)
    
    update_data: Dict[str, Any] = {"updatedAt": datetime.utcnow()}
    if roadmap is not None:
        update_data["roadmap"] = roadmap
    if duration_weeks is not None:
        update_data["durationWeeks"] = duration_weeks

    result = paths_col.find_one_and_update(
        {"_id": oid, "userId": user_id},
        {"$set": update_data},
        return_document=True
    )
    return serialize_doc(result)
