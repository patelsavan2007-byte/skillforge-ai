import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.database.mongodb import get_career_profiles_collection
from app.services.gemini_service import analyze_career_gap_with_gemini
from app.services.skill_gap_engine import compute_skill_gap
from app.utils.object_id import validate_object_id, serialize_doc, serialize_docs

logger = logging.getLogger("skillforge.career_service")

# ---------------------------------------------------------------------------
# Priority-Weighted Role Requirements
# Each skill has a priority: "high", "medium", or "low"
# "high"   = core requirement — gap here is critical
# "medium" = important but secondary — gap is notable
# "low"    = nice-to-have / optional — gap is minor
# ---------------------------------------------------------------------------
WEIGHTED_ROLE_REQUIREMENTS: Dict[str, Dict[str, str]] = {
    # ── 1. AI/ML Engineer ──────────────────────────────────────────────────
    "AI/ML Engineer": {
        "Python": "high", "NumPy": "high", "Pandas": "high",
        "Scikit-learn": "high", "Machine Learning": "high",
        "Deep Learning": "high", "TensorFlow": "medium", "PyTorch": "medium",
        "Neural Networks": "medium", "Natural Language Processing": "medium",
        "Computer Vision": "medium", "SQL": "medium", "Git": "medium",
        "Data Preprocessing": "medium", "Model Evaluation": "medium",
        "Feature Engineering": "medium", "Model Deployment": "high",
        "REST APIs": "low", "Docker": "low", "MLOps": "medium",
    },
    "AI Engineer": {
        "Python": "high", "Machine Learning": "high", "Deep Learning": "high",
        "PyTorch": "high", "Scikit-learn": "medium", "Pandas": "medium",
        "Docker": "medium", "FastAPI": "medium", "MLOps": "high",
    },

    # ── 2. Data Scientist ──────────────────────────────────────────────────
    "Data Scientist": {
        "Python": "high", "NumPy": "high", "Pandas": "high",
        "Scikit-learn": "high", "Statistics": "high", "Probability": "medium",
        "Machine Learning": "high", "Data Analysis": "high",
        "Data Visualization": "medium", "SQL": "high", "Matplotlib": "medium",
        "Seaborn": "low", "Feature Engineering": "medium",
        "Model Evaluation": "medium", "Jupyter": "low", "Git": "medium",
        "Hypothesis Testing": "medium",
    },

    # ── 3. Data Analyst ────────────────────────────────────────────────────
    "Data Analyst": {
        "SQL": "high", "Python": "medium", "Pandas": "medium",
        "NumPy": "low", "Statistics": "high", "Data Analysis": "high",
        "Data Visualization": "high", "Excel": "high", "Power BI": "medium",
        "Tableau": "medium", "Matplotlib": "low", "Seaborn": "low",
        "Data Cleaning": "medium", "Reporting": "medium", "Dashboarding": "medium",
    },

    # ── 4. Data Engineer ───────────────────────────────────────────────────
    "Data Engineer": {
        "Python": "high", "SQL": "high", "PostgreSQL": "high",
        "MySQL": "medium", "MongoDB": "medium", "ETL": "high",
        "Data Pipelines": "high", "Apache Spark": "medium",
        "Apache Airflow": "medium", "Data Warehousing": "medium",
        "Hadoop": "low", "Kafka": "medium", "AWS": "medium",
        "Docker": "medium", "Git": "medium", "Linux": "low",
    },

    # ── 5. Software Engineer ───────────────────────────────────────────────
    "Software Engineer": {
        "Python": "medium", "Java": "medium", "JavaScript": "high",
        "TypeScript": "medium", "Data Structures": "high",
        "Algorithms": "high", "Object-Oriented Programming": "high",
        "SQL": "medium", "Git": "high", "REST APIs": "high",
        "Testing": "high", "Debugging": "medium",
        "Software Development": "medium", "Database Fundamentals": "medium",
        "System Design": "medium",
    },

    # ── 6. Frontend Developer ──────────────────────────────────────────────
    "Frontend Developer": {
        "HTML": "high", "CSS": "high", "JavaScript": "high",
        "TypeScript": "medium", "React": "high", "Vite": "low",
        "Responsive Design": "high", "Tailwind CSS": "medium",
        "REST APIs": "medium", "Git": "high", "UI Development": "medium",
        "Web Accessibility": "medium", "State Management": "medium",
        "Browser DevTools": "low",
    },

    # ── 7. Backend Developer ───────────────────────────────────────────────
    "Backend Developer": {
        "Python": "high", "Node.js": "high", "Java": "medium",
        "REST APIs": "high", "FastAPI": "medium", "Express.js": "medium",
        "SQL": "high", "PostgreSQL": "high", "MongoDB": "medium",
        "Authentication": "high", "JWT": "medium", "API Security": "medium",
        "Git": "high", "Docker": "medium", "Linux": "low", "Testing": "high",
    },

    # ── 8. Full Stack Developer ────────────────────────────────────────────
    "Full Stack Developer": {
        "JavaScript": "high", "TypeScript": "high", "React": "high",
        "Node.js": "high", "REST APIs": "high", "SQL": "high",
        "MongoDB": "medium", "PostgreSQL": "medium", "Git": "high",
        "Authentication": "high", "Docker": "medium",
        "Testing": "high", "System Design": "medium",
        "CI/CD": "medium", "Cloud Deployment": "medium",
        "HTML": "low", "CSS": "low", "Python": "low",
        "Responsive Design": "low", "Backend Development": "low",
        "Frontend Development": "low",
    },

    # ── 9. Mobile App Developer ────────────────────────────────────────────
    "Mobile App Developer": {
        "Java": "medium", "Kotlin": "high", "Swift": "high",
        "Dart": "medium", "Flutter": "medium", "React Native": "medium",
        "Android": "high", "iOS": "high", "Mobile UI": "high",
        "REST APIs": "medium", "JSON": "low", "Git": "high",
        "Mobile App Development": "high", "State Management": "medium",
        "Firebase": "medium",
    },

    # ── 10. DevOps Engineer ────────────────────────────────────────────────
    "DevOps Engineer": {
        "Linux": "high", "Git": "high", "Docker": "high",
        "Kubernetes": "high", "CI/CD": "high", "Jenkins": "medium",
        "GitHub Actions": "medium", "AWS": "high", "Azure": "medium",
        "Terraform": "high", "Ansible": "medium", "Bash": "medium",
        "Networking": "medium", "Monitoring": "medium", "Logging": "medium",
        "Infrastructure as Code": "high",
    },

    # ── 11. Cloud Engineer ─────────────────────────────────────────────────
    "Cloud Engineer": {
        "AWS": "high", "Azure": "high", "Google Cloud": "medium",
        "Cloud Computing": "high", "Linux": "high", "Networking": "medium",
        "Docker": "high", "Kubernetes": "high", "Terraform": "high",
        "IAM": "medium", "CI/CD": "medium",
        "Infrastructure as Code": "high", "Monitoring": "medium",
        "Security": "medium", "Git": "medium",
    },

    # ── 12. Cybersecurity Engineer ─────────────────────────────────────────
    "Cybersecurity Engineer": {
        "Cybersecurity": "high", "Network Security": "high", "Linux": "high",
        "Python": "medium", "SQL": "medium", "Cryptography": "high",
        "Authentication": "medium", "Authorization": "medium",
        "Vulnerability Assessment": "high", "Penetration Testing": "high",
        "OWASP": "high", "SIEM": "medium", "Firewalls": "medium",
        "Incident Response": "medium", "Security Monitoring": "medium",
        "Risk Management": "medium",
    },

    # ── 13. UI/UX Designer ─────────────────────────────────────────────────
    "UI/UX Designer": {
        "UI Design": "high", "UX Design": "high", "User Research": "high",
        "Wireframing": "high", "Prototyping": "high", "Figma": "high",
        "Design Systems": "medium", "Interaction Design": "medium",
        "Visual Design": "medium", "Usability Testing": "medium",
        "Information Architecture": "medium", "Responsive Design": "medium",
        "Accessibility": "low",
    },

    # ── 14. Product Manager ────────────────────────────────────────────────
    "Product Manager": {
        "Product Management": "high", "Product Strategy": "high",
        "Product Roadmapping": "high", "Market Research": "medium",
        "User Research": "high", "Requirements Analysis": "high",
        "Agile": "high", "Scrum": "medium",
        "Stakeholder Management": "medium", "Product Analytics": "medium",
        "A/B Testing": "low", "Communication": "medium",
        "Documentation": "low", "Prioritization": "medium",
    },

    # ── 15. QA Automation Engineer ─────────────────────────────────────────
    "QA Automation Engineer": {
        "Software Testing": "high", "Test Automation": "high",
        "Python": "medium", "Java": "medium", "JavaScript": "medium",
        "Selenium": "high", "Playwright": "medium", "Cypress": "medium",
        "API Testing": "high", "Postman": "medium", "SQL": "medium",
        "Git": "high", "CI/CD": "medium", "Regression Testing": "medium",
        "Integration Testing": "medium", "Unit Testing": "high",
        "Bug Tracking": "low",
    },

    # ── 16. Blockchain Developer ───────────────────────────────────────────
    "Blockchain Developer": {
        "Blockchain": "high", "Solidity": "high", "Ethereum": "high",
        "Smart Contracts": "high", "Web3": "high", "JavaScript": "medium",
        "TypeScript": "medium", "Node.js": "medium", "Cryptography": "medium",
        "Wallet Integration": "medium", "Distributed Systems": "medium",
        "Git": "medium", "Hardhat": "medium", "Ethers.js": "medium",
        "Security": "medium",
    },
}


def get_flat_required_skills(role: str) -> List[str]:
    """Extract a flat list of required skills for backward compatibility with compute_skill_gap()."""
    weighted = WEIGHTED_ROLE_REQUIREMENTS.get(role)
    if not weighted:
        # Fallback to AI/ML Engineer if role not found
        weighted = WEIGHTED_ROLE_REQUIREMENTS.get("AI/ML Engineer", {})
    return list(weighted.keys())


def get_weighted_requirements(role: str) -> Dict[str, Dict[str, List[str]]]:
    """Return role requirements grouped by priority: high, medium, low."""
    weighted = WEIGHTED_ROLE_REQUIREMENTS.get(role)
    if not weighted:
        weighted = WEIGHTED_ROLE_REQUIREMENTS.get("AI/ML Engineer", {})
    result: Dict[str, List[str]] = {"high": [], "medium": [], "low": []}
    for skill, priority in weighted.items():
        result.setdefault(priority, []).append(skill)
    return {"priorities": result, "all_skills": list(weighted.keys())}


# Legacy flat dict for backward compat (used by some test modules)
REQUIRED_SKILLS_BY_ROLE: Dict[str, List[str]] = {
    role: list(skills.keys())
    for role, skills in WEIGHTED_ROLE_REQUIREMENTS.items()
}


def generate_career_analysis(
    target_role: str,
    unified_profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate skill gap analysis comparing UNIFIED STUDENT PROFILE vs TARGET ROLE REQUIREMENTS.

    Steps:
    1. DETERMINISTIC SKILL GAP ENGINE (always runs first, never overridden).
       Produces user_strengths and true_skill_gaps via pure set arithmetic.
    2. Try Gemini AI reasoning for richer display fields (summary, readiness score).
    3. Heuristic fallback if Gemini is unavailable.

    The deterministic user_strengths / true_skill_gaps fields are injected
    into the final result regardless of which display path is taken.
    """
    user_skills = [s.strip() for s in unified_profile.get("skills", []) if isinstance(s, str)]

    req_skills = get_flat_required_skills(target_role)

    # ------------------------------------------------------------------ #
    # STEP 1 — DETERMINISTIC SKILL GAP ENGINE (source of truth)           #
    # No LLM involved. Pure set arithmetic with normalization.            #
    # ------------------------------------------------------------------ #
    gap_result = compute_skill_gap(student_skills=user_skills, required_skills=req_skills)
    user_strengths = gap_result["user_strengths"]       # intersection
    true_skill_gaps = gap_result["true_skill_gaps"]     # difference

    matched_ratio = len(user_strengths) / max(1, len(req_skills))
    heuristic_score = min(95, max(35, int(matched_ratio * 100)))

    # Developing skills: student has them but they are not in the required set
    req_lower = set(r.lower() for r in req_skills)
    developing = [s for s in user_skills if s.lower() not in req_lower]

    # ------------------------------------------------------------------ #
    # Compute prioritized skill gaps using weighted role requirements      #
    # ------------------------------------------------------------------ #
    role_weights = WEIGHTED_ROLE_REQUIREMENTS.get(target_role, {})
    critical_gaps = []
    medium_gaps = []
    low_gaps = []
    for gap_skill in true_skill_gaps:
        priority = role_weights.get(gap_skill, "medium")
        if priority == "high":
            critical_gaps.append(gap_skill)
        elif priority == "medium":
            medium_gaps.append(gap_skill)
        else:
            low_gaps.append(gap_skill)

    prioritized_gaps = {
        "critical": critical_gaps,
        "medium": medium_gaps,
        "low": low_gaps,
    }

    # ------------------------------------------------------------------ #
    # STEP 2 — Optional Gemini enrichment for display fields only.        #
    # Gemini output MUST NOT overwrite user_strengths / true_skill_gaps.  #
    # ------------------------------------------------------------------ #
    gemini_gap = analyze_career_gap_with_gemini(unified_profile, target_role)
    if gemini_gap:
        skill_gaps_display = gemini_gap.get("skillGaps") or [
            {"skill": s,
             "importance": "High" if role_weights.get(s) == "high" else "Medium",
             "currentLevel": 20, "requiredLevel": 85}
            for s in true_skill_gaps[:5]
        ]
        return {
            "targetRole": target_role,
            "careerMatches": [
                {"role": target_role, "score": gemini_gap.get("careerReadiness", heuristic_score)},
                {"role": "Software Engineer" if target_role != "Software Engineer" else "Full Stack Developer",
                 "score": max(45, gemini_gap.get("careerReadiness", heuristic_score) - 10)},
                {"role": "Data Scientist" if target_role != "Data Scientist" else "AI/ML Engineer",
                 "score": max(40, gemini_gap.get("careerReadiness", heuristic_score) - 15)},
            ],
            "profileSummary": gemini_gap.get("profileSummary") or f"Profile evaluated for {target_role}.",
            "strongSkills": user_strengths,
            "developingSkills": developing,
            "skillGaps": skill_gaps_display,
            "careerReadiness": gemini_gap.get("careerReadiness", heuristic_score),
            "missingTechnologies": gemini_gap.get("missingTechnologies") or true_skill_gaps,
            "missingProjectExperience": gemini_gap.get("missingProjectExperience") or [f"Hands-on {target_role} production project"],
            "recommendedNextSkills": gemini_gap.get("recommendedNextSkills") or (critical_gaps[:3] or true_skill_gaps[:3]),
            # --- DETERMINISTIC FIELDS (always authoritative, never overridden) ---
            "user_strengths": user_strengths,
            "true_skill_gaps": true_skill_gaps,
            "prioritized_gaps": prioritized_gaps,
        }

    # ------------------------------------------------------------------ #
    # STEP 3 — Heuristic fallback (no Gemini)                             #
    # ------------------------------------------------------------------ #
    skill_gaps_display = [
        {
            "skill": skill,
            "importance": "High" if role_weights.get(skill) == "high" else "Medium",
            "currentLevel": 25,
            "requiredLevel": 85,
        }
        for skill in (critical_gaps + medium_gaps + low_gaps)[:5]
    ]

    career_matches = [
        {"role": target_role, "score": heuristic_score},
        {"role": "Software Engineer" if target_role != "Software Engineer" else "Full Stack Developer",
         "score": max(45, heuristic_score - 8)},
        {"role": "Data Scientist" if target_role != "Data Scientist" else "AI/ML Engineer",
         "score": max(40, heuristic_score - 12)},
    ]

    summary = (
        f"Based on your profile, you demonstrate strong foundational capabilities in "
        f"{', '.join(user_strengths[:3]) if user_strengths else 'software development'}. "
        f"To reach full interview readiness for {target_role}, focus on filling key gaps in "
        f"{', '.join((critical_gaps or true_skill_gaps)[:3]) if (critical_gaps or true_skill_gaps) else 'production deployment'}."
    )

    return {
        "targetRole": target_role,
        "careerMatches": career_matches,
        "profileSummary": summary,
        "strongSkills": user_strengths,
        "developingSkills": developing,
        "skillGaps": skill_gaps_display,
        "careerReadiness": heuristic_score,
        "missingTechnologies": true_skill_gaps,
        "missingProjectExperience": [f"Full-stack/AI production project targeting {target_role}"],
        "recommendedNextSkills": (critical_gaps[:3] or true_skill_gaps[:3]),
        # --- DETERMINISTIC FIELDS (always authoritative, never overridden) ---
        "user_strengths": user_strengths,
        "true_skill_gaps": true_skill_gaps,
        "prioritized_gaps": prioritized_gaps,
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
        profile_obj = unified_profile or {"skills": []}
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
        # Deterministic skill gap fields — always present
        "user_strengths": analysis.get("user_strengths", []),
        "true_skill_gaps": analysis.get("true_skill_gaps", []),
        "unifiedProfile": unified_profile or {},
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
