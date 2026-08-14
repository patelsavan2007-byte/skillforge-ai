import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.database.mongodb import get_learning_paths_collection
from app.services.gemini_service import generate_recommendations_with_gemini
from app.services.embedding_service import rank_courses_with_e5
from app.utils.object_id import validate_object_id, serialize_doc, serialize_docs

logger = logging.getLogger("skillforge.learning_service")


def _normalize_skill_names(skill_gaps: Optional[List[Any]]) -> List[str]:
    """Accept legacy display objects at the boundary, then keep only skill names."""
    names: List[str] = []
    for item in skill_gaps or []:
        value = item if isinstance(item, str) else item.get("skill") if isinstance(item, dict) else None
        if isinstance(value, str) and value.strip():
            names.append(value.strip())
    return list(dict.fromkeys(names))


def _sanitize_gemini_output(gemini_recs: Dict[str, Any], e5_courses: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Validate Gemini's shape and make E5 the sole authority for course URLs."""
    sanitized = dict(gemini_recs) if isinstance(gemini_recs, dict) else {}
    catalog = {
        str(course.get("title", "")).strip().casefold(): course
        for course in (e5_courses or [])
        if isinstance(course, dict) and str(course.get("title", "")).strip()
    }

    def sanitize_courses(courses: Any) -> List[Dict[str, Any]]:
        if not isinstance(courses, list):
            return []
        safe_courses: List[Dict[str, Any]] = []
        for course in courses:
            if not isinstance(course, dict):
                continue
            safe_course = dict(course)
            catalog_course = catalog.get(str(safe_course.get("title", "")).strip().casefold())
            # A matching E5 title always gets its catalog URL; unknown titles can never keep a URL.
            safe_course["url"] = catalog_course.get("url", "") if catalog_course else ""
            safe_courses.append(safe_course)
        return safe_courses

    sanitized["courses"] = sanitize_courses(sanitized.get("courses"))
    roadmap = sanitized.get("roadmap")
    sanitized_roadmap: List[Dict[str, Any]] = []
    if isinstance(roadmap, list):
        for index, milestone in enumerate(roadmap, start=1):
            if not isinstance(milestone, dict):
                continue
            safe_milestone = dict(milestone)
            safe_milestone["week"] = safe_milestone.get("week", index)
            safe_milestone["title"] = safe_milestone.get("title") or safe_milestone.get("milestone_title", "")
            safe_milestone["skills"] = safe_milestone.get("skills") if isinstance(safe_milestone.get("skills"), list) else []
            safe_milestone["courses"] = sanitize_courses(safe_milestone.get("courses"))
            related = safe_milestone.get("related_courses")
            if isinstance(related, list):
                safe_milestone["related_courses"] = sanitize_courses(related)
            sanitized_roadmap.append(safe_milestone)
    sanitized["roadmap"] = sanitized_roadmap
    # Keep the public response structurally valid even when Gemini omits optional sections.
    sanitized["durationWeeks"] = sanitized.get("durationWeeks") if isinstance(sanitized.get("durationWeeks"), int) else len(sanitized_roadmap)
    for key in ("recommendedProjects", "certifications", "interviewPrep", "careerAdvice"):
        sanitized[key] = sanitized.get(key) if isinstance(sanitized.get(key), list) else []
    return sanitized

def generate_personalized_recommendations(
    unified_profile: Dict[str, Any],
    target_role: str,
    skill_gaps: List[Any],
    duration_weeks: int = 8,
    user_strengths: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Generate personalized roadmap, courses, projects, certifications, interview questions, and advice.
    E5 intfloat/e5-base-v2 is used for semantic course retrieval/ranking based on true skill gaps.
    Combines E5 semantic retrieval + Gemini recommendations + fallback heuristics.
    """
    # Extract string names of true_skill_gaps
    gap_names = _normalize_skill_names(skill_gaps)
    deterministic_strengths = [s.strip() for s in (user_strengths or []) if isinstance(s, str) and s.strip()]

    # Fallback gap names if empty
    if not gap_names and unified_profile.get("true_skill_gaps"):
        gap_names = [s for s in unified_profile.get("true_skill_gaps", []) if isinstance(s, str)]

    # 1. Perform E5 Semantic Course Retrieval & Cosine Similarity Ranking
    e5_ranked_courses = rank_courses_with_e5(gap_names, top_k=5)

    # 2. Try Gemini Recommendation Engine with E5 context
    gemini_recs = generate_recommendations_with_gemini(
        unified_profile, target_role, deterministic_strengths, gap_names, e5_courses=e5_ranked_courses
    )
    if gemini_recs and gemini_recs.get("roadmap"):
        gemini_recs = _sanitize_gemini_output(gemini_recs, e5_ranked_courses)
        # Ensure E5 semantically ranked courses with real URLs take precedence
        if e5_ranked_courses:
            gemini_recs["courses"] = e5_ranked_courses
        gemini_recs["user_strengths"] = deterministic_strengths
        gemini_recs["true_skill_gaps"] = gap_names
        return gemini_recs

    # HEURISTIC FALLBACK TAILORED TO SKILL GAPS
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
                    "url": "",
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
                    "url": "",
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
                    "url": "",
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
                    "url": "",
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

    courses = e5_ranked_courses if e5_ranked_courses else [
        {
            "title": f"{primary_gap} Masterclass",
            "provider": "Coursera",
            "url": "",
            "duration": "12 hours",
            "difficulty": "Intermediate",
            "skillAddressed": primary_gap
        },
        {
            "title": f"{secondary_gap} in Production",
            "provider": "Udemy",
            "url": "",
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
        "careerAdvice": career_advice,
        "user_strengths": deterministic_strengths,
        "true_skill_gaps": gap_names,
    }

def create_learning_path_record(
    user_id: str,
    target_role: str = "AI Engineer",
    duration_weeks: int = 8,
    unified_profile: Optional[Dict[str, Any]] = None,
    skill_gaps: Optional[List[Any]] = None,
    custom_roadmap: Optional[List[Dict[str, Any]]] = None,
    user_strengths: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Generate and persist personalized learning roadmap into MongoDB learning_paths collection."""
    paths_col = get_learning_paths_collection()
    
    if custom_roadmap:
        recs = {"roadmap": custom_roadmap, "durationWeeks": len(custom_roadmap)}
    else:
        profile_obj = unified_profile or {}
        gaps_obj = skill_gaps or []
        recs = generate_personalized_recommendations(
            profile_obj, target_role, gaps_obj, duration_weeks, user_strengths=user_strengths
        )

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
        "user_strengths": recs.get("user_strengths", []),
        "true_skill_gaps": recs.get("true_skill_gaps", []),
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
