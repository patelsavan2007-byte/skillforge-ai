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

from app.services.recommendation_engine import (
    build_evidence_profile,
    compute_prioritized_gaps,
    calculate_dynamic_duration,
    filter_and_validate_recommendations,
)

def generate_personalized_recommendations(
    unified_profile: Dict[str, Any],
    target_role: str,
    skill_gaps: List[Any],
    duration_weeks: Optional[int] = None,
    user_strengths: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Generate personalized roadmap, courses, projects, certifications, interview questions, and advice.
    E5 intfloat/e5-base-v2 is used for semantic course retrieval/ranking based on true skill gaps.
    Combines E5 semantic retrieval + Gemini recommendations + fallback heuristics + quality filter.
    """
    # Extract string names of true_skill_gaps
    gap_names = _normalize_skill_names(skill_gaps)
    deterministic_strengths = [s.strip() for s in (user_strengths or []) if isinstance(s, str) and s.strip()]

    # Fallback gap names if empty
    if not gap_names and unified_profile.get("true_skill_gaps"):
        gap_names = [s for s in unified_profile.get("true_skill_gaps", []) if isinstance(s, str)]

    # 1. Build evidence profile & compute prioritized gaps
    evidence = build_evidence_profile(unified_profile, target_role)
    prioritized_gaps = compute_prioritized_gaps(evidence, target_role)
    
    # Calculate dynamic duration unless explicitly overridden
    dyn_duration = duration_weeks if (duration_weeks and duration_weeks > 0) else calculate_dynamic_duration(prioritized_gaps)

    # 2. Perform E5 Semantic Course Retrieval & Cosine Similarity Ranking
    e5_ranked_courses = rank_courses_with_e5(gap_names, top_k=5)

    # 3. Try Gemini Recommendation Engine with E5 context
    gemini_recs = generate_recommendations_with_gemini(
        unified_profile,
        target_role,
        deterministic_strengths,
        gap_names,
        prioritized_gaps=prioritized_gaps,
        dynamic_duration=dyn_duration,
        e5_courses=e5_ranked_courses,
        existing_projects=evidence.get("existing_projects", []),
    )
    
    if gemini_recs and gemini_recs.get("roadmap"):
        gemini_recs = _sanitize_gemini_output(gemini_recs, e5_ranked_courses)
        filtered = filter_and_validate_recommendations(
            gemini_recs, evidence, prioritized_gaps, target_role, e5_courses=e5_ranked_courses
        )
        filtered["user_strengths"] = deterministic_strengths
        filtered["true_skill_gaps"] = gap_names
        filtered["prioritized_gaps"] = prioritized_gaps
        return filtered

    # 4. EVIDENCE-BASED HEURISTIC FALLBACK (no Gemini available)
    # Build milestones dynamically from the actual gaps
    roadmap = []
    gaps_to_cover = gap_names if gap_names else ["Production Architecture", "System Design", "Cloud Deployment"]
    
    for w_idx in range(1, dyn_duration + 1):
        if w_idx <= len(gaps_to_cover):
            focus_gap = gaps_to_cover[w_idx - 1]
            title = f"Mastering {focus_gap}"
            skills = [focus_gap]
        else:
            focus_gap = gaps_to_cover[(w_idx - 1) % len(gaps_to_cover)]
            title = f"Advanced {focus_gap} & Architecture"
            skills = [focus_gap, "System Integration"]
            
        roadmap.append({
            "week": w_idx,
            "title": title,
            "objective": f"Develop deep practical proficiency in {focus_gap} for {target_role} readiness.",
            "why_this_week": f"Directly addresses verified {target_role} skill gap in {focus_gap}.",
            "estimated_hours": "10-12 hours",
            "skills": skills,
            "courses": [
                {
                    "title": f"{focus_gap} for {target_role}s",
                    "provider": "Coursera / Udemy",
                    "url": "",
                    "duration": "10 hours",
                    "difficulty": "Intermediate"
                }
            ],
            "project": {
                "title": f"Hands-on {focus_gap} System",
                "description": f"Build and deploy an end-to-end module demonstrating {focus_gap}.",
                "skills": skills
            },
            "completed": False  # CRITICAL: Always False for new plans
        })

    courses = e5_ranked_courses if e5_ranked_courses else [
        {
            "title": f"{g} Masterclass" if idx == 0 else f"Advanced {g} in Production",
            "provider": "Coursera",
            "url": "",
            "duration": "12 hours",
            "difficulty": "Intermediate",
            "skillAddressed": g,
            "why_recommended": f"Targeted course to close skill gap in {g}"
        }
        for idx, g in enumerate(gap_names[:4])
    ]

    # Dynamic recommended projects targeting gaps
    primary_gap = gap_names[0] if gap_names else "Full-Stack System"
    secondary_gap = gap_names[1] if len(gap_names) > 1 else "Cloud Deployment"
    
    recommended_projects = [
        {
            "title": f"Production {target_role} Architecture: {primary_gap}",
            "description": f"End-to-end production system implementing {primary_gap} with automated testing and deployment.",
            "technologies": [primary_gap] + (deterministic_strengths[:2] if deterministic_strengths else ["FastAPI"]),
            "difficulty": "Advanced",
            "skills_gained": [primary_gap],
            "skills_targeted": [primary_gap],
            "why_recommended": f"Builds portfolio evidence for {primary_gap} required for {target_role}.",
            "expected_resume_impact": f"Proves production readiness in {primary_gap}.",
            "suggested_stack": [primary_gap, "Docker", "PostgreSQL"],
            "url": "https://github.com/fastapi/full-stack-fastapi-template" if "stack" in target_role.lower() else "https://github.com/donnemartin/system-design-primer"
        },
        {
            "title": f"Scalable {secondary_gap} Platform",
            "description": f"Deploy a distributed platform demonstrating {secondary_gap} and scalable system design.",
            "technologies": [secondary_gap, primary_gap],
            "difficulty": "Advanced",
            "skills_gained": [secondary_gap],
            "skills_targeted": [secondary_gap],
            "why_recommended": f"Addresses secondary critical gap in {secondary_gap}.",
            "expected_resume_impact": f"Demonstrates end-to-end architectural mastery in {secondary_gap}.",
            "suggested_stack": [secondary_gap, "Docker", "CI/CD"],
            "url": "https://github.com/donnemartin/system-design-primer"
        }
    ]

    certifications = [
        {
            "name": f"Certified {target_role} Practitioner",
            "provider": "AWS / Google Cloud / Linux Foundation",
            "skill": primary_gap,
            "why_recommended": f"Industry-recognized credential validating {target_role} core competencies.",
            "priority": "High",
            "url": "https://aws.amazon.com/certification/" if "cloud" in target_role.lower() else "https://training.linuxfoundation.org/certification/"
        }
    ] if gap_names else []

    interview_prep = [
        {
            "topic": primary_gap,
            "question": f"How do you design and optimize production systems leveraging {primary_gap} for high availability?",
            "keyConcept": f"Core architecture, bottleneck identification, and optimization in {primary_gap}.",
            "url": "https://github.com/donnemartin/system-design-primer",
            "resourceTitle": "System Design Primer"
        },
        {
            "topic": f"{target_role} Architecture",
            "question": f"Walk through the architectural trade-offs you made in your projects when scaling data flow and persistence.",
            "keyConcept": "System design trade-offs, caching layers, and database indexing.",
            "url": "https://neetcode.io/practice",
            "resourceTitle": "NeetCode Roadmap"
        }
    ]

    career_advice = [
        f"Prominently feature your {primary_gap} implementations in your GitHub portfolio READMEs.",
        f"Tailor your technical project bullet points to highlight {target_role} metrics and architecture decisions.",
        f"Focus next on closing your {secondary_gap} gap to achieve full interview readiness."
    ]

    raw_result = {
        "durationWeeks": len(roadmap),
        "roadmap": roadmap,
        "courses": courses,
        "recommendedProjects": recommended_projects,
        "certifications": certifications,
        "interviewPrep": interview_prep,
        "careerAdvice": career_advice,
        "user_strengths": deterministic_strengths,
        "true_skill_gaps": gap_names,
        "prioritized_gaps": prioritized_gaps,
    }
    
    return filter_and_validate_recommendations(
        raw_result, evidence, prioritized_gaps, target_role, e5_courses=e5_ranked_courses
    )

def create_learning_path_record(
    user_id: str,
    target_role: str = "AI Engineer",
    duration_weeks: Optional[int] = None,
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
        "durationWeeks": recs.get("durationWeeks", duration_weeks or 4),
        "estimatedCompletionHours": recs.get("estimatedCompletionHours", 24),
        "estimatedCompletionDays": recs.get("estimatedCompletionDays", 6),
        "initialReadiness": recs.get("initialReadiness", 50),
        "careerReadiness": recs.get("careerReadiness", 50),
        "improvedScore": 0,
        "roadmap": recs.get("roadmap", []),
        "courses": recs.get("courses", []),
        "recommendedProjects": recs.get("recommendedProjects", []),
        "certifications": recs.get("certifications", []),
        "interviewPrep": recs.get("interviewPrep", []),
        "careerAdvice": recs.get("careerAdvice", []),
        "user_strengths": recs.get("user_strengths", []),
        "true_skill_gaps": recs.get("true_skill_gaps", []),
        "prioritized_gaps": recs.get("prioritized_gaps", {}),
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
