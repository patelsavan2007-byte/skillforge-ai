import logging
from typing import Dict, Any, List, Optional
from app.services.resume_extractor import normalize_skills

logger = logging.getLogger("skillforge.profile_merge")

def _normalize_list(items: List[Any]) -> List[str]:
    """Canonical, case-insensitive de-duplication shared with extraction."""
    return normalize_skills(items)

def _merge_projects(r_projects: List[Dict[str, Any]], p_projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge project arrays from resume and portfolio without duplicating."""
    merged = []
    seen_names = set()

    # Process portfolio projects first (portfolio projects often have URLs/GitHub links)
    for proj in p_projects:
        name = proj.get("name", "").strip()
        if not name:
            continue
        key = name.lower()
        seen_names.add(key)
        merged.append({
            "name": name,
            "description": proj.get("description", ""),
            "technologies": _normalize_list(proj.get("technologies", [])),
            "url": proj.get("url") or proj.get("github") or None,
            "source": "portfolio"
        })

    # Add resume projects or merge detailed description
    for proj in r_projects:
        name = proj.get("name", "").strip()
        if not name:
            continue
        key = name.lower()
        if key in seen_names:
            # Find existing entry and combine technologies/details
            for existing in merged:
                if existing["name"].lower() == key:
                    if len(proj.get("description", "")) > len(existing.get("description", "")):
                        existing["description"] = proj.get("description")
                    existing["technologies"] = _normalize_list(
                        existing.get("technologies", []) + proj.get("technologies", [])
                    )
                    existing["source"] = "both"
                    break
        else:
            seen_names.add(key)
            merged.append({
                "name": name,
                "description": proj.get("description", ""),
                "technologies": _normalize_list(proj.get("technologies", [])),
                "url": proj.get("url") or None,
                "source": "resume"
            })

    return merged

def merge_student_profiles(
    resume_profile: Optional[Dict[str, Any]] = None,
    portfolio_profile: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Merge Resume Profile and Portfolio Profile into a Unified Student Profile.
    Works with:
    - Resume only
    - Portfolio only
    - Both
    - Raises ValueError if neither exists
    """
    has_resume = bool(resume_profile and (resume_profile.get("skills") or resume_profile.get("technologies") or resume_profile.get("personal") or resume_profile.get("projects")))
    has_portfolio = bool(portfolio_profile and (portfolio_profile.get("skills") or portfolio_profile.get("technologies") or portfolio_profile.get("projects") or portfolio_profile.get("bio")))

    if not has_resume and not has_portfolio:
        raise ValueError("At least one profile source (Resume or Portfolio) is required to run analysis.")

    # PRIMARY: Deterministic merge of resume and portfolio profiles
    r_prof = resume_profile or {}
    p_prof = portfolio_profile or {}

    # Extract name/personal details (prefer resume, fallback to portfolio)
    r_personal = r_prof.get("personal", {}) if isinstance(r_prof.get("personal"), dict) else {}
    name = r_personal.get("name") or r_prof.get("name") or p_prof.get("name") or "Student Candidate"

    # Extract & deduplicate skills and technologies
    r_techs = r_prof.get("technologies", [])
    p_techs = p_prof.get("technologies", [])
    r_skills = r_prof.get("skills", [])
    p_skills = p_prof.get("skills", [])
    # `skills` is the canonical candidate capability field.  Include legacy
    # `technologies` too so older MongoDB documents cannot lose evidence.
    all_skills = _normalize_list(r_skills + r_techs + p_skills + p_techs)
    all_techs = list(all_skills)

    # Education & Experience (prefer resume as primary source)
    education = r_prof.get("education") or p_prof.get("education") or []
    experience = r_prof.get("experience") or p_prof.get("experience") or []

    # Certifications & Achievements
    certifications = _normalize_list(r_prof.get("certifications", []) + p_prof.get("certifications", []))
    achievements = _normalize_list(r_prof.get("achievements", []))

    # Merged projects
    r_projects = r_prof.get("projects", [])
    p_projects = p_prof.get("projects", [])
    merged_projects = _merge_projects(r_projects, p_projects)

    unified = {
        "name": name,
        "bio": p_prof.get("bio") or (f"Candidate with background in {', '.join(all_skills[:3])}" if all_skills else ""),
        "education": education,
        "experience": experience,
        "skills": all_skills,
        "projects": merged_projects,
        "certifications": certifications,
        "technologies": all_techs,
        "achievements": achievements,
        "source": {
            "resume": has_resume,
            "portfolio": has_portfolio
        }
    }

    return unified
