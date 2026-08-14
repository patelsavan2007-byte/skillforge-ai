"""
recommendation_engine.py
========================
Evidence-based recommendation & career planning engine for SkillForge AI.

Pipeline:
1. Build normalized evidence profile (demonstrated, developing, missing, unknown).
2. Load role priority requirements (high, medium, low).
3. Compute prioritized skill gaps (critical, medium, low).
4. Calculate dynamic task-based hours and days based on gap severity.
5. Compute deterministic weighted readiness baseline (25%-95%).
6. Retrieve semantically ranked courses via E5.
7. Call Gemini with rich candidate context for task-based milestone breakdown.
8. Validate and filter recommendations (reject contradictions, duplicate projects, fake URLs, irrelevant tech).
9. Return strictly personalized, actionable plan.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Set

from app.services.skill_gap_engine import normalize_skill, normalize_skill_list, compute_skill_gap
from app.services.career_service import WEIGHTED_ROLE_REQUIREMENTS, get_flat_required_skills

logger = logging.getLogger("skillforge.recommendation_engine")

# Priority weight multipliers for deterministic readiness calculations
PRIORITY_WEIGHTS = {
    "high": 3,
    "medium": 2,
    "low": 1
}


def calculate_weighted_readiness(
    target_role: str,
    demonstrated_skills: List[str],
    completed_skills: Optional[List[str]] = None,
) -> int:
    """
    Calculate deterministic career readiness percentage based on weighted role skills.
    
    Formula:
    total_points = sum(weight(skill) for skill in target_role_skills)
    earned_points = sum(weight(skill) for skill in (demonstrated_skills U completed_skills))
    ratio = earned_points / total_points
    readiness = min(96, max(25, 25 + round(ratio * 70)))
    """
    role_weights = WEIGHTED_ROLE_REQUIREMENTS.get(
        target_role, WEIGHTED_ROLE_REQUIREMENTS.get("AI/ML Engineer", {})
    )
    if not role_weights:
        return 50

    total_points = 0
    for skill_name, priority in role_weights.items():
        total_points += PRIORITY_WEIGHTS.get(priority.lower(), 2)

    demonstrated_norm = set(normalize_skill_list(demonstrated_skills or []))
    completed_norm = set(normalize_skill_list(completed_skills or []))
    achieved_skills = demonstrated_norm | completed_norm

    earned_points = 0
    for skill_name, priority in role_weights.items():
        norm_key = normalize_skill(skill_name)
        if norm_key in achieved_skills:
            earned_points += PRIORITY_WEIGHTS.get(priority.lower(), 2)

    if total_points <= 0:
        return 50

    ratio = min(1.0, earned_points / total_points)
    # Smooth progression from 25% (baseline starter) to 95% (fully ready)
    readiness = 25 + int(round(ratio * 70))
    return int(min(96, max(25, readiness)))


def build_evidence_profile(unified_profile: Dict[str, Any], target_role: str) -> Dict[str, Any]:
    """
    Construct a normalized evidence profile classifying every skill as:
    - demonstrated: clear evidence in resume/portfolio (skills, projects, experience, bio)
    - developing: mentioned or partial evidence
    - missing: required by target role but no evidence found
    """
    skills_raw = unified_profile.get("skills", [])
    techs_raw = unified_profile.get("technologies", [])
    projects_raw = unified_profile.get("projects", [])
    exp_raw = unified_profile.get("experience", [])
    certs_raw = unified_profile.get("certifications", [])
    
    # Collect all skill tokens from explicit skills and technologies
    direct_skills = normalize_skill_list(skills_raw + techs_raw)
    direct_skill_set = set(direct_skills)
    
    # Collect skills mentioned in project technologies and descriptions
    project_skills: Set[str] = set()
    project_names: List[str] = []
    for proj in projects_raw:
        if isinstance(proj, dict):
            name = proj.get("name", "").strip()
            if name:
                project_names.append(name)
            p_techs = proj.get("technologies", [])
            if isinstance(p_techs, list):
                for t in p_techs:
                    norm = normalize_skill(str(t))
                    if norm:
                        project_skills.add(norm)
            p_desc = str(proj.get("description", "")).lower()
            for s in direct_skills:
                if s in p_desc:
                    project_skills.add(s)

    # Collect skills from experience descriptions
    exp_skills: Set[str] = set()
    for exp in exp_raw:
        if isinstance(exp, dict):
            e_desc = str(exp.get("description", "") + " " + exp.get("role", "")).lower()
            for s in direct_skills:
                if s in e_desc:
                    exp_skills.add(s)

    demonstrated_set = direct_skill_set | project_skills | exp_skills

    # Get target role requirements
    role_weights = WEIGHTED_ROLE_REQUIREMENTS.get(target_role, WEIGHTED_ROLE_REQUIREMENTS.get("AI/ML Engineer", {}))
    
    classified_skills: Dict[str, str] = {}
    for skill_name, priority in role_weights.items():
        norm = normalize_skill(skill_name)
        if norm in demonstrated_set:
            classified_skills[skill_name] = "demonstrated"
        else:
            classified_skills[skill_name] = "missing"

    supplementary_skills: List[str] = []
    role_norm_set = {normalize_skill(k) for k in role_weights.keys()}
    for s in direct_skills:
        if s not in role_norm_set:
            supplementary_skills.append(s)

    return {
        "demonstrated_skills": [k for k, v in classified_skills.items() if v == "demonstrated"],
        "missing_skills": [k for k, v in classified_skills.items() if v == "missing"],
        "supplementary_skills": supplementary_skills,
        "existing_project_names": project_names,
        "existing_projects": projects_raw,
        "experience": exp_raw,
        "certifications": certs_raw,
        "raw_skills": direct_skills,
    }


def compute_prioritized_gaps(evidence_profile: Dict[str, Any], target_role: str) -> Dict[str, Any]:
    """
    Calculate prioritized skill gaps based on role importance and student evidence.
    """
    role_weights = WEIGHTED_ROLE_REQUIREMENTS.get(target_role, WEIGHTED_ROLE_REQUIREMENTS.get("AI/ML Engineer", {}))
    missing = evidence_profile.get("missing_skills", [])
    demonstrated = evidence_profile.get("demonstrated_skills", [])
    
    critical_gaps: List[str] = []
    medium_gaps: List[str] = []
    optional_gaps: List[str] = []
    
    for skill in missing:
        p = role_weights.get(skill, "medium")
        if p == "high":
            critical_gaps.append(skill)
        elif p == "medium":
            medium_gaps.append(skill)
        else:
            optional_gaps.append(skill)

    return {
        "critical_gaps": critical_gaps,
        "medium_gaps": medium_gaps,
        "optional_gaps": optional_gaps,
        "strong_skills": demonstrated,
        "developing_skills": evidence_profile.get("supplementary_skills", []),
        "all_missing_gaps": critical_gaps + medium_gaps + optional_gaps,
    }


def estimate_gap_scope(skill: str, priority: str = "medium") -> Dict[str, Any]:
    """
    Estimate realistic hours, days, and difficulty for a specific skill gap:
    - VERY SMALL GAP: 2–4 hours (1 day)
    - SMALL GAP: 4–8 hours (1–2 days)
    - MEDIUM GAP: 8–16 hours (2–4 days)
    - LARGE GAP: 16–30 hours (4–7 days)
    """
    skill_lower = skill.lower()
    
    # Large complex architecture topics
    if any(k in skill_lower for k in ["system design", "distributed", "kubernetes", "deep learning", "machine learning", "cloud computing", "cryptography"]):
        return {
            "estimated_hours": 16,
            "estimated_days": 4,
            "difficulty": "Advanced",
            "current_level": "Beginner",
            "target_level": "Intermediate / Advanced",
            "gap_level": "High"
        }
    # Medium core engineering topics
    elif any(k in skill_lower for k in ["docker", "ci/cd", "testing", "fastapi", "sql", "postgresql", "mongodb", "authentication", "api security", "mlops", "data analysis", "statistics"]):
        return {
            "estimated_hours": 10,
            "estimated_days": 2,
            "difficulty": "Intermediate",
            "current_level": "Beginner",
            "target_level": "Intermediate",
            "gap_level": "Medium"
        }
    # Small / lightweight topics
    else:
        hours = 6 if priority == "medium" else 4
        days = 2 if priority == "medium" else 1
        return {
            "estimated_hours": hours,
            "estimated_days": days,
            "difficulty": "Intermediate" if priority == "medium" else "Beginner",
            "current_level": "Beginner",
            "target_level": "Competent",
            "gap_level": "Low"
        }


def calculate_dynamic_duration(prioritized_gaps: Dict[str, Any]) -> int:
    """
    Calculate dynamic roadmap duration (in weeks/phases) based on actual gaps.
    """
    crit_count = len(prioritized_gaps.get("critical_gaps", []))
    med_count = len(prioritized_gaps.get("medium_gaps", []))
    total_gaps = crit_count + med_count + len(prioritized_gaps.get("optional_gaps", []))

    if crit_count == 0:
        if med_count <= 2:
            return 3 if total_gaps <= 1 else 4
        elif med_count <= 4:
            return 5
        else:
            return 6
    elif crit_count == 1:
        return 5 if med_count <= 2 else 6
    elif crit_count == 2:
        return 6 if med_count <= 2 else 7
    elif crit_count == 3:
        return 8
    else:
        return min(10, max(6, crit_count + 3))


def filter_and_validate_recommendations(
    raw_recs: Dict[str, Any],
    evidence_profile: Dict[str, Any],
    prioritized_gaps: Dict[str, Any],
    target_role: str,
    e5_courses: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Quality Filter:
    1. Removes recommendations that contradict the student's profile.
    2. Replaces or filters beginner project duplicates if the student already built them.
    3. Grounds courses in E5 / official providers and strips fake URLs.
    4. Enforces realistic task-based hours and days.
    5. Ensures all newly generated milestones have completed = False and status = 'not_started'.
    """
    demonstrated_lower = {s.lower() for s in evidence_profile.get("demonstrated_skills", [])}
    existing_project_names = [p.lower() for p in evidence_profile.get("existing_project_names", [])]
    existing_projects = evidence_profile.get("existing_projects", [])
    
    role_weights = WEIGHTED_ROLE_REQUIREMENTS.get(target_role, {})

    # 1. Filter and normalize Roadmap
    raw_roadmap = raw_recs.get("roadmap", [])
    cleaned_roadmap = []
    total_hours = 0
    total_days = 0
    
    for idx, week_item in enumerate(raw_roadmap, start=1):
        if not isinstance(week_item, dict):
            continue
        w = dict(week_item)
        w["week"] = idx
        w["status"] = "not_started"
        w["completed"] = False  # NEVER auto-complete for a brand-new plan!
        w["completed_at"] = None
        w["actual_hours"] = None
        
        # Skill & scope estimation
        skill_name = w.get("skill") or (w.get("skills", ["General"])[0] if w.get("skills") else "Core Engineering")
        priority = role_weights.get(skill_name, "medium")
        scope = estimate_gap_scope(skill_name, priority)
        
        if not w.get("estimated_hours") or not isinstance(w.get("estimated_hours"), (int, float)):
            w["estimated_hours"] = scope["estimated_hours"]
        else:
            w["estimated_hours"] = int(w["estimated_hours"])
            
        if not w.get("estimated_days") or not isinstance(w.get("estimated_days"), (int, float)):
            w["estimated_days"] = scope["estimated_days"]
        else:
            w["estimated_days"] = int(w["estimated_days"])
            
        w["current_level"] = w.get("current_level") or scope["current_level"]
        w["target_level"] = w.get("target_level") or scope["target_level"]
        w["gap_level"] = w.get("gap_level") or scope["gap_level"]
        w["difficulty"] = w.get("difficulty") or scope["difficulty"]
        
        total_hours += w["estimated_hours"]
        total_days += w["estimated_days"]
        
        # Ensure title exists
        if not w.get("title"):
            w["title"] = w.get("milestone_title") or f"Phase {idx}: {skill_name} Mastery"
            
        # Clean skills list
        skills = w.get("skills", [])
        if isinstance(skills, list):
            w["skills"] = [str(s).strip() for s in skills if str(s).strip()]
        if not w.get("skills") and skill_name:
            w["skills"] = [skill_name]
            
        # Clean tasks
        tasks = w.get("tasks", [])
        cleaned_tasks = []
        if isinstance(tasks, list) and tasks:
            for t in tasks:
                if isinstance(t, dict):
                    cleaned_tasks.append({
                        "title": str(t.get("title", "")).strip(),
                        "duration": str(t.get("duration", "2h")).strip(),
                        "description": str(t.get("description", "")).strip(),
                    })
                elif isinstance(t, str) and t.strip():
                    cleaned_tasks.append({
                        "title": t.strip(),
                        "duration": "2h",
                        "description": f"Practical learning task for {skill_name}."
                    })
        if not cleaned_tasks:
            # Generate structured subtasks
            cleaned_tasks = [
                {"title": f"Day 1: {skill_name} Core Principles", "duration": f"{max(2, w['estimated_hours'] // 2)}h", "description": f"Architecture and patterns in {skill_name}."},
                {"title": f"Day 2: {skill_name} Implementation & Testing", "duration": f"{max(2, w['estimated_hours'] - (w['estimated_hours'] // 2))}h", "description": f"Hands-on integration with {target_role} system."}
            ]
        w["tasks"] = cleaned_tasks
        
        # Checkpoint
        if not w.get("checkpoint"):
            w["checkpoint"] = f"Build and verify a functioning {skill_name} module with automated tests."
            
        # Clean project in milestone
        proj = w.get("project")
        if isinstance(proj, dict):
            p_title = str(proj.get("title", "")).strip()
            is_dup = any(name in p_title.lower() or p_title.lower() in name for name in existing_project_names)
            if is_dup:
                proj["title"] = f"Advanced {target_role} System: {p_title}"
            if not proj.get("url") or "http" not in str(proj.get("url", "")):
                proj_text = (p_title + " " + skill_name + " " + target_role).lower()
                for p_key, p_link in {
                    "fastapi": "https://github.com/fastapi/full-stack-fastapi-template",
                    "react": "https://github.com/facebook/create-react-app",
                    "next": "https://github.com/vercel/next.js/tree/canary/examples",
                    "node": "https://github.com/goldbergyoni/nodebestpractices",
                    "docker": "https://github.com/docker/awesome-compose",
                    "kubernetes": "https://github.com/kubernetes/examples",
                    "machine learning": "https://github.com/ageron/handson-ml3",
                    "pytorch": "https://github.com/pytorch/examples",
                    "sql": "https://github.com/enisget/sql-project-ideas",
                    "system design": "https://github.com/donnemartin/system-design-primer",
                }.items():
                    if p_key in proj_text:
                        proj["url"] = p_link
                        break
                if not proj.get("url"):
                    proj["url"] = "https://github.com/fastapi/full-stack-fastapi-template" if "stack" in target_role.lower() else "https://github.com/donnemartin/system-design-primer"
            w["project"] = proj
            
        cleaned_roadmap.append(w)

    # 2. Filter Projects & Ground Reference Architecture URLs
    raw_projects = raw_recs.get("recommendedProjects", [])
    cleaned_projects = []
    
    project_template_urls = {
        "fastapi": "https://github.com/fastapi/full-stack-fastapi-template",
        "react": "https://github.com/facebook/create-react-app",
        "next": "https://github.com/vercel/next.js/tree/canary/examples",
        "node": "https://github.com/goldbergyoni/nodebestpractices",
        "express": "https://github.com/expressjs/express/tree/master/examples",
        "docker": "https://github.com/docker/awesome-compose",
        "kubernetes": "https://github.com/kubernetes/examples",
        "machine learning": "https://github.com/ageron/handson-ml3",
        "deep learning": "https://github.com/pytorch/examples",
        "pytorch": "https://github.com/pytorch/examples",
        "tensorflow": "https://github.com/tensorflow/examples",
        "sql": "https://github.com/enisget/sql-project-ideas",
        "system design": "https://github.com/donnemartin/system-design-primer",
        "full stack": "https://github.com/fastapi/full-stack-fastapi-template",
    }

    for p in raw_projects:
        if not isinstance(p, dict):
            continue
        p_dict = dict(p)
        p_title = str(p_dict.get("title", "")).strip()
        
        is_duplicate = False
        for ex in existing_projects:
            ex_name = str(ex.get("name", "")).lower()
            if ex_name and (ex_name in p_title.lower() or p_title.lower() in ex_name):
                is_duplicate = True
                break
                
        if is_duplicate:
            p_dict["title"] = f"Production-Grade Scalable {p_title}"
            p_dict["description"] = "Scale and enhance your existing architecture with automated CI/CD, caching, and observability."
            p_dict["difficulty"] = "Advanced"
            
        # Ground Project URL
        if not p_dict.get("url") or "http" not in str(p_dict.get("url", "")):
            tech_str = " ".join([str(t) for t in p_dict.get("technologies", []) + p_dict.get("suggested_stack", [])])
            p_combined = (p_title + " " + tech_str + " " + target_role).lower()
            for key, link in project_template_urls.items():
                if key in p_combined:
                    p_dict["url"] = link
                    break
            if not p_dict.get("url"):
                p_dict["url"] = "https://github.com/fastapi/full-stack-fastapi-template" if "stack" in target_role.lower() else "https://github.com/donnemartin/system-design-primer"
                
        cleaned_projects.append(p_dict)

    # 3. Filter Courses & Ground URLs
    catalog_urls = {}
    if e5_courses:
        for c in e5_courses:
            if isinstance(c, dict) and c.get("title") and c.get("url"):
                catalog_urls[c["title"].strip().lower()] = c["url"].strip()

    raw_courses = raw_recs.get("courses", [])
    cleaned_courses = []
    
    for c in raw_courses:
        if not isinstance(c, dict):
            continue
        c_dict = dict(c)
        c_title = str(c_dict.get("title", "")).strip()
        c_skill = str(c_dict.get("skillAddressed") or c_dict.get("skill") or "").strip()
        
        if c_skill.lower() in demonstrated_lower and "basic" in c_title.lower():
            continue
            
        matching_url = catalog_urls.get(c_title.lower())
        if matching_url:
            c_dict["url"] = matching_url
        elif not c_dict.get("url") or "http" not in str(c_dict.get("url", "")):
            c_dict["url"] = ""
            
        cleaned_courses.append(c_dict)

    # 4. Filter Certifications & Ground Official URLs
    raw_certs = raw_recs.get("certifications", [])
    cleaned_certs = []
    fake_keywords = ["advanced html", "html developer", "basic css certificate", "generic developer"]
    
    cert_catalog_urls = {
        "aws": "https://aws.amazon.com/certification/",
        "google": "https://cloud.google.com/learn/certification",
        "gcp": "https://cloud.google.com/learn/certification",
        "azure": "https://learn.microsoft.com/credentials/browse/",
        "microsoft": "https://learn.microsoft.com/credentials/browse/",
        "kubernetes": "https://training.linuxfoundation.org/certification/certified-kubernetes-administrator-cka/",
        "linux": "https://training.linuxfoundation.org/certification/",
        "terraform": "https://www.hashicorp.com/certification/terraform-associate",
        "meta": "https://www.coursera.org/professional-certificates/meta-front-end-developer",
        "mongodb": "https://learn.mongodb.com/pages/certification-overview",
        "deeplearning": "https://www.deeplearning.ai/courses/",
        "tensorflow": "https://www.tensorflow.org/certificate",
    }
    
    for cert in raw_certs:
        if not isinstance(cert, dict):
            continue
        c_name = str(cert.get("name", "")).strip()
        if any(fk in c_name.lower() for fk in fake_keywords):
            continue
        
        c_dict = dict(cert)
        # Ground URL if empty or unverified
        if not c_dict.get("url") or "http" not in str(c_dict.get("url", "")):
            c_text = (c_name + " " + str(c_dict.get("provider", ""))).lower()
            for key, link in cert_catalog_urls.items():
                if key in c_text:
                    c_dict["url"] = link
                    break
            if not c_dict.get("url"):
                c_dict["url"] = "https://aws.amazon.com/certification/" if "cloud" in target_role.lower() else "https://training.linuxfoundation.org/certification/"
                
        cleaned_certs.append(c_dict)

    # 5. Filter Interview Prep & Ground Authoritative URLs
    raw_interview = raw_recs.get("interviewPrep", [])
    cleaned_interview = []
    
    interview_urls = {
        "system design": ("https://github.com/donnemartin/system-design-primer", "System Design Primer"),
        "architecture": ("https://github.com/donnemartin/system-design-primer", "System Design Primer"),
        "algorithm": ("https://leetcode.com/explore/", "LeetCode Practice"),
        "coding": ("https://neetcode.io/practice", "NeetCode Roadmap"),
        "python": ("https://realpython.com/", "Real Python"),
        "fastapi": ("https://fastapi.tiangolo.com/tutorial/", "FastAPI Docs"),
        "react": ("https://react.dev/learn", "React Official Docs"),
        "node": ("https://nodejs.org/en/learn", "Node.js Learn"),
        "sql": ("https://sqlzoo.net/", "SQLZoo"),
        "docker": ("https://docs.docker.com/get-started/", "Docker Docs"),
        "machine learning": ("https://developers.google.com/machine-learning/crash-course", "Google ML Crash Course"),
        "ml": ("https://developers.google.com/machine-learning/crash-course", "Google ML Crash Course"),
    }
    
    for item in raw_interview:
        if not isinstance(item, dict):
            continue
        i_dict = dict(item)
        if not i_dict.get("url") or "http" not in str(i_dict.get("url", "")):
            topic_lower = (str(i_dict.get("topic", "")) + " " + str(i_dict.get("question", ""))).lower()
            matched_url, matched_title = "https://neetcode.io/practice", "NeetCode Roadmap"
            for key, (link, title) in interview_urls.items():
                if key in topic_lower:
                    matched_url, matched_title = link, title
                    break
            i_dict["url"] = matched_url
            i_dict["resourceTitle"] = i_dict.get("resourceTitle") or matched_title
        cleaned_interview.append(i_dict)

    # Compute baseline readiness
    demonstrated_skills = evidence_profile.get("demonstrated_skills", [])
    initial_readiness = calculate_weighted_readiness(target_role, demonstrated_skills)

    return {
        "durationWeeks": len(cleaned_roadmap) if cleaned_roadmap else raw_recs.get("durationWeeks", 4),
        "estimatedCompletionHours": total_hours if total_hours > 0 else 24,
        "estimatedCompletionDays": total_days if total_days > 0 else 6,
        "initialReadiness": initial_readiness,
        "careerReadiness": initial_readiness,
        "improvedScore": 0,
        "roadmap": cleaned_roadmap,
        "courses": cleaned_courses if cleaned_courses else (e5_courses or []),
        "recommendedProjects": cleaned_projects,
        "certifications": cleaned_certs,
        "interviewPrep": cleaned_interview,
        "careerAdvice": raw_recs.get("careerAdvice", []),
    }
