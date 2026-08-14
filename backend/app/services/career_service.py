import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.database.mongodb import get_career_profiles_collection
from app.services.gemini_service import analyze_career_gap_with_gemini
from app.services.skill_gap_engine import compute_skill_gap
from app.utils.object_id import validate_object_id, serialize_doc, serialize_docs

logger = logging.getLogger("skillforge.career_service")

REQUIRED_SKILLS_BY_ROLE = {
    # ── 1. AI/ML Engineer ──────────────────────────────────────────────────
    "AI/ML Engineer": [
        "Python", "NumPy", "Pandas", "Scikit-learn", "Machine Learning",
        "Deep Learning", "TensorFlow", "PyTorch", "Neural Networks",
        "Natural Language Processing", "Computer Vision", "SQL", "Git",
        "Data Preprocessing", "Model Evaluation", "Feature Engineering",
        "Model Deployment", "REST APIs",
    ],
    # Legacy alias kept for backward compat with any stored records
    "AI Engineer": [
        "Python", "Machine Learning", "Deep Learning", "PyTorch",
        "Scikit-learn", "Pandas", "Docker", "FastAPI", "MLOps",
    ],

    # ── 2. Data Scientist ──────────────────────────────────────────────────
    "Data Scientist": [
        "Python", "NumPy", "Pandas", "Scikit-learn", "Statistics",
        "Probability", "Machine Learning", "Data Analysis",
        "Data Visualization", "SQL", "Matplotlib", "Seaborn",
        "Feature Engineering", "Model Evaluation", "Jupyter", "Git",
        "Hypothesis Testing",
    ],

    # ── 3. Data Analyst ────────────────────────────────────────────────────
    "Data Analyst": [
        "SQL", "Python", "Pandas", "NumPy", "Statistics", "Data Analysis",
        "Data Visualization", "Excel", "Power BI", "Tableau", "Matplotlib",
        "Seaborn", "Data Cleaning", "Reporting", "Dashboarding",
    ],

    # ── 4. Data Engineer ───────────────────────────────────────────────────
    "Data Engineer": [
        "Python", "SQL", "PostgreSQL", "MySQL", "MongoDB", "ETL",
        "Data Pipelines", "Apache Spark", "Apache Airflow",
        "Data Warehousing", "Hadoop", "Kafka", "AWS", "Docker", "Git",
        "Linux",
    ],

    # ── 5. Software Engineer ───────────────────────────────────────────────
    "Software Engineer": [
        "Python", "Java", "JavaScript", "TypeScript", "Data Structures",
        "Algorithms", "Object-Oriented Programming", "SQL", "Git",
        "REST APIs", "Testing", "Debugging", "Software Development",
        "Database Fundamentals",
    ],

    # ── 6. Frontend Developer ──────────────────────────────────────────────
    "Frontend Developer": [
        "HTML", "CSS", "JavaScript", "TypeScript", "React", "Vite",
        "Responsive Design", "Tailwind CSS", "REST APIs", "Git",
        "UI Development", "Web Accessibility", "State Management",
        "Browser DevTools",
    ],

    # ── 7. Backend Developer ───────────────────────────────────────────────
    "Backend Developer": [
        "Python", "Node.js", "Java", "REST APIs", "FastAPI", "Express.js",
        "SQL", "PostgreSQL", "MongoDB", "Authentication", "JWT",
        "API Security", "Git", "Docker", "Linux", "Testing",
    ],

    # ── 8. Full Stack Developer ────────────────────────────────────────────
    "Full Stack Developer": [
        "HTML", "CSS", "JavaScript", "TypeScript", "React", "Node.js",
        "Python", "REST APIs", "SQL", "MongoDB", "PostgreSQL", "Git",
        "Authentication", "Responsive Design", "Backend Development",
        "Frontend Development", "Docker",
    ],

    # ── 9. Mobile App Developer ────────────────────────────────────────────
    "Mobile App Developer": [
        "Java", "Kotlin", "Swift", "Dart", "Flutter", "React Native",
        "Android", "iOS", "Mobile UI", "REST APIs", "JSON", "Git",
        "Mobile App Development", "State Management", "Firebase",
    ],

    # ── 10. DevOps Engineer ────────────────────────────────────────────────
    "DevOps Engineer": [
        "Linux", "Git", "Docker", "Kubernetes", "CI/CD", "Jenkins",
        "GitHub Actions", "AWS", "Azure", "Terraform", "Ansible", "Bash",
        "Networking", "Monitoring", "Logging", "Infrastructure as Code",
    ],

    # ── 11. Cloud Engineer ─────────────────────────────────────────────────
    "Cloud Engineer": [
        "AWS", "Azure", "Google Cloud", "Cloud Computing", "Linux",
        "Networking", "Docker", "Kubernetes", "Terraform", "IAM", "CI/CD",
        "Infrastructure as Code", "Monitoring", "Security", "Git",
    ],

    # ── 12. Cybersecurity Engineer ─────────────────────────────────────────
    "Cybersecurity Engineer": [
        "Cybersecurity", "Network Security", "Linux", "Python", "SQL",
        "Cryptography", "Authentication", "Authorization",
        "Vulnerability Assessment", "Penetration Testing", "OWASP",
        "SIEM", "Firewalls", "Incident Response", "Security Monitoring",
        "Risk Management",
    ],

    # ── 13. UI/UX Designer ─────────────────────────────────────────────────
    "UI/UX Designer": [
        "UI Design", "UX Design", "User Research", "Wireframing",
        "Prototyping", "Figma", "Design Systems", "Interaction Design",
        "Visual Design", "Usability Testing", "Information Architecture",
        "Responsive Design", "Accessibility",
    ],

    # ── 14. Product Manager ────────────────────────────────────────────────
    "Product Manager": [
        "Product Management", "Product Strategy", "Product Roadmapping",
        "Market Research", "User Research", "Requirements Analysis",
        "Agile", "Scrum", "Stakeholder Management", "Product Analytics",
        "A/B Testing", "Communication", "Documentation", "Prioritization",
    ],

    # ── 15. QA Automation Engineer ─────────────────────────────────────────
    "QA Automation Engineer": [
        "Software Testing", "Test Automation", "Python", "Java",
        "JavaScript", "Selenium", "Playwright", "Cypress", "API Testing",
        "Postman", "SQL", "Git", "CI/CD", "Regression Testing",
        "Integration Testing", "Unit Testing", "Bug Tracking",
    ],

    # ── 16. Blockchain Developer ───────────────────────────────────────────
    "Blockchain Developer": [
        "Blockchain", "Solidity", "Ethereum", "Smart Contracts", "Web3",
        "JavaScript", "TypeScript", "Node.js", "Cryptography",
        "Wallet Integration", "Distributed Systems", "Git", "Hardhat",
        "Ethers.js", "Security",
    ],
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

    req_skills = REQUIRED_SKILLS_BY_ROLE.get(target_role, REQUIRED_SKILLS_BY_ROLE["AI/ML Engineer"])

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
    user_skills_lower = set(s.lower() for s in user_skills)
    req_lower = set(r.lower() for r in req_skills)
    developing = [s for s in user_skills if s.lower() not in req_lower]

    # ------------------------------------------------------------------ #
    # STEP 2 — Optional Gemini enrichment for display fields only.        #
    # Gemini output MUST NOT overwrite user_strengths / true_skill_gaps.  #
    # ------------------------------------------------------------------ #
    gemini_gap = analyze_career_gap_with_gemini(unified_profile, target_role)
    if gemini_gap:
        # Gemini provides: profileSummary, careerReadiness, skillGaps detail,
        # missingTechnologies, missingProjectExperience, recommendedNextSkills.
        # We keep the deterministic strengths/gaps as the authoritative fields.
        skill_gaps_display = gemini_gap.get("skillGaps") or [
            {"skill": s, "importance": "High" if idx < 2 else "Medium",
             "currentLevel": 20, "requiredLevel": 85}
            for idx, s in enumerate(true_skill_gaps[:5])
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
            # Candidate skills remain deterministic facts; Gemini only enriches
            # qualitative explanations and must not invent strengths.
            "strongSkills": user_strengths,
            "developingSkills": developing,
            "skillGaps": skill_gaps_display,
            "careerReadiness": gemini_gap.get("careerReadiness", heuristic_score),
            "missingTechnologies": gemini_gap.get("missingTechnologies") or true_skill_gaps,
            "missingProjectExperience": gemini_gap.get("missingProjectExperience") or [f"Hands-on {target_role} production project"],
            "recommendedNextSkills": gemini_gap.get("recommendedNextSkills") or true_skill_gaps[:3],
            # --- DETERMINISTIC FIELDS (always authoritative, never overridden) ---
            "user_strengths": user_strengths,
            "true_skill_gaps": true_skill_gaps,
        }

    # ------------------------------------------------------------------ #
    # STEP 3 — Heuristic fallback (no Gemini)                             #
    # ------------------------------------------------------------------ #
    skill_gaps_display = [
        {
            "skill": skill,
            "importance": "High" if skill in ["PyTorch", "Deep Learning", "Docker", "MLOps", "SQL", "React"] else "Medium",
            "currentLevel": 25,
            "requiredLevel": 85,
        }
        for skill in true_skill_gaps[:5]
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
        f"{', '.join(true_skill_gaps[:3]) if true_skill_gaps else 'production deployment'}."
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
        "recommendedNextSkills": true_skill_gaps[:3],
        # --- DETERMINISTIC FIELDS (always authoritative, never overridden) ---
        "user_strengths": user_strengths,
        "true_skill_gaps": true_skill_gaps,
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
