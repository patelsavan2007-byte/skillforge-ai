import json
import logging
import re
from typing import Dict, Any, Optional, List
from app.config import settings

logger = logging.getLogger("skillforge.gemini")

def _get_genai_client():
    if not settings.GEMINI_API_KEY:
        return None
    try:
        from google import genai
        return genai.Client(api_key=settings.GEMINI_API_KEY)
    except Exception as e:
        logger.warning(f"Could not initialize Google GenAI client: {e}")
        return None

def _clean_json_response(text: str) -> Dict[str, Any]:
    """Clean markdown code fences from model response and parse JSON."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\n", "", cleaned)
        cleaned = re.sub(r"\n```$", "", cleaned)
    
    # Extract JSON object using regex if surrounding text exists
    json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if json_match:
        cleaned = json_match.group(0)
        
    return json.loads(cleaned)

GEMINI_MODEL_CANDIDATES = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]

def generate_gemini_json(prompt: str, system_instruction: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Call Gemini API to generate structured JSON. Returns None if API key missing or call fails."""
    client = _get_genai_client()
    if not client:
        return None

    config = {
        "response_mime_type": "application/json",
        "temperature": 0.2,
    }
    if system_instruction:
        config["system_instruction"] = system_instruction

    for model_name in GEMINI_MODEL_CANDIDATES:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )
            if response and response.text:
                return _clean_json_response(response.text)
        except Exception as e:
            err_str = str(e)
            if "404" in err_str or "not found" in err_str.lower() or "no longer available" in err_str.lower():
                logger.info(f"Gemini model '{model_name}' unavailable ({e}), trying next candidate...")
                continue
            logger.error(f"Gemini API generation error on model '{model_name}': {e}")
            print(f"[Gemini Service] API call failed on model '{model_name}': {e}")

    return None


# Gemini is intentionally limited to qualitative career/learning orchestration.

def analyze_career_gap_with_gemini(unified_profile: Dict[str, Any], target_role: str) -> Optional[Dict[str, Any]]:
    """Analyze unified candidate profile against target role requirements."""
    system_instruction = (
        f"You are a Senior Technical Career Counselor evaluating a candidate for the target role: '{target_role}'. "
        "Return ONLY a JSON object matching this schema:\n"
        "{\n"
        '  "profileSummary": "Detailed 2-3 sentence career evaluation based on candidate evidence",\n'
        '  "careerReadiness": 75,\n'
        '  "strongSkills": ["Skill1", "Skill2"],\n'
        '  "developingSkills": ["Skill3"],\n'
        '  "skillGaps": [{"skill": "SkillName", "importance": "High/Medium", "currentLevel": 20, "requiredLevel": 85}],\n'
        '  "missingTechnologies": ["Tech1", "Tech2"],\n'
        '  "missingProjectExperience": ["Project concept candidate should build"],\n'
        '  "recommendedNextSkills": ["Skill1", "Skill2"]\n'
        "}"
    )
    prompt = f"Target Role: {target_role}\nUnified Profile:\n{json.dumps(unified_profile, indent=2)}"
    return generate_gemini_json(prompt, system_instruction=system_instruction)

def generate_recommendations_with_gemini(
    unified_profile: Dict[str, Any],
    target_role: str,
    user_strengths: List[str],
    true_skill_gaps: List[str],
    prioritized_gaps: Optional[Dict[str, Any]] = None,
    dynamic_duration: int = 4,
    e5_courses: Optional[List[Dict[str, Any]]] = None,
    existing_projects: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    """Generate a strictly personalized career roadmap and recommendations from verified candidate evidence."""
    system_instruction = (
        f"You are an Elite Technical Career Architect designing a custom, highly personalized, task-based career plan for a candidate targeting: '{target_role}'.\n"
        "STRICT PERSONALIZATION RULES:\n"
        "1. GROUNDING IN CANDIDATE EVIDENCE: The roadmap must start at the student's CURRENT level. If the candidate already demonstrates full-stack/core skills, NEVER suggest beginner tutorials (e.g. do not teach HTML basics if they already know React/Node/Postgres).\n"
        "2. REALISTIC TIME ESTIMATION: Do not allocate 1 week per skill. Use realistic units:\n"
        "   - Very small gap: 2-4 hours (1 day)\n"
        "   - Small gap: 4-8 hours (1-2 days)\n"
        "   - Medium gap: 8-16 hours (2-4 days)\n"
        "   - Large gap: 16-30 hours (4-7 days)\n"
        "3. GROUP SMALL GAPS: Group closely related small gaps into a single cohesive milestone (e.g., 'Phase 1: REST API & Auth Architecture' covering endpoints, JWT, and error handling over 2 days).\n"
        "4. TASK-BASED BREAKDOWN: Each milestone MUST contain daily actionable subtasks (e.g. 'Day 1: Architecture (2h)', 'Day 2: Implementation (3h)') and a concrete verification Checkpoint.\n"
        "5. NO COMPLETED MILESTONES: Every milestone must have 'completed': false and 'status': 'not_started'.\n"
        "6. NO DUPLICATE BEGINNER PROJECTS: Check the candidate's existing projects. Recommend advanced production architectures, scaling, or distributed systems that target verified gaps.\n"
        "7. NO UNRELATED TECH: Do NOT recommend random technologies (e.g. PyTorch or Flutter for Full Stack) unless relevant to the role and gaps.\n"
        "8. E5 RETRIEVED COURSES: Use E5 courses as the primary reference for real titles and providers. Never invent fake URLs.\n"
        "9. CERTIFICATION & INTERVIEW WEB LINKS: Provide real, authoritative web links for certifications (e.g., official AWS, GCP, Linux Foundation, Microsoft cert URLs) and interview preparation platforms/guides (e.g., System Design Primer on GitHub, NeetCode, LeetCode, MDN Web Docs, Real Python).\n"
        "10. PROJECT-SPECIFIC INTERVIEW PREP: Include questions targeting the candidate's actual projects (e.g. 'In your project X, how did you handle Y?') in addition to architectural questions.\n"
        "11. ACTIONABLE ADVICE: Generate 3-5 distinct, concrete, non-generic career actions tailored specifically to this student's profile.\n\n"
        "Return ONLY a JSON object matching this schema:\n"
        "{\n"
        f'  "durationWeeks": {dynamic_duration},\n'
        '  "estimatedCompletionHours": 24,\n'
        '  "estimatedCompletionDays": 6,\n'
        '  "roadmap": [\n'
        '    {\n'
        '      "week": 1,\n'
        '      "title": "Phase 1: Clear Action-Oriented Milestone Title",\n'
        '      "skill": "Target Skill Name",\n'
        '      "skills": ["Skill1", "Skill2"],\n'
        '      "current_level": "Beginner / Developing",\n'
        '      "target_level": "Intermediate / Advanced",\n'
        '      "gap_level": "High / Medium / Low",\n'
        '      "estimated_hours": 8,\n'
        '      "estimated_days": 2,\n'
        '      "difficulty": "Intermediate",\n'
        '      "objective": "Specific learning outcome for this milestone",\n'
        '      "why_this_matters": "Why this specific topic is critical for target role readiness",\n'
        '      "tasks": [\n'
        '        {"title": "Day 1: Architectural Fundamentals", "duration": "3h", "description": "Core mechanics and design patterns"},\n'
        '        {"title": "Day 2: Hands-on Implementation", "duration": "5h", "description": "Build working module and integrate"}\n'
        '      ],\n'
        '      "checkpoint": "Concrete verification milestone (e.g. Build and deploy a tested REST module)",\n'
        '      "courses": [{"title": "Course Name", "provider": "Provider", "url": "", "duration": "10h", "difficulty": "Intermediate", "why_recommended": "Reason"}],\n'
        '      "project": {"title": "Project Title", "description": "Hands-on implementation targeting gap", "skills": ["Skill1"], "url": "https://github.com/..."},\n'
        '      "status": "not_started",\n'
        '      "completed": false\n'
        '    }\n'
        '  ],\n'
        '  "courses": [{"title": "Course Title", "provider": "Provider", "url": "", "duration": "15h", "difficulty": "Intermediate", "skillAddressed": "Skill", "why_recommended": "Reason"}],\n'
        '  "recommendedProjects": [\n'
        '    {\n'
        '      "title": "Project Title",\n'
        '      "description": "Production architecture and features",\n'
        '      "technologies": ["Tech1", "Tech2"],\n'
        '      "difficulty": "Advanced",\n'
        '      "skills_gained": ["Skill1"],\n'
        '      "skills_targeted": ["Skill1"],\n'
        '      "why_recommended": "Fills gap X without duplicating existing project Y",\n'
        '      "expected_resume_impact": "Demonstrates scalable backend architecture",\n'
        '      "suggested_stack": ["React", "FastAPI", "Docker"],\n'
        '      "url": "https://github.com/..."\n'
        '    }\n'
        '  ],\n'
        '  "certifications": [{"name": "Official Certification Name", "provider": "AWS / GCP / Linux Foundation", "skill": "Skill", "why_recommended": "Reason", "priority": "High/Medium", "url": "https://aws.amazon.com/certification/..."}],\n'
        '  "interviewPrep": [{"topic": "Topic", "question": "Technical or project-specific question", "keyConcept": "Core architectural or algorithmic concept", "url": "https://github.com/donnemartin/system-design-primer", "resourceTitle": "System Design Primer / LeetCode"}],\n'
        '  "careerAdvice": ["Highly specific action item 1", "Highly specific action item 2", "Highly specific action item 3"]\n'
        "}"
    )

    e5_metadata = [
        {
            key: course.get(key)
            for key in ("title", "provider", "url", "description", "skills", "duration", "difficulty", "similarity_score")
        }
        for course in (e5_courses or [])
        if isinstance(course, dict)
    ]

    p_gaps = prioritized_gaps or {"critical": true_skill_gaps, "medium": [], "low": []}
    
    prompt = (
        f"STUDENT PROFILE SUMMARY:\n{json.dumps(unified_profile, indent=2)}\n\n"
        f"EXISTING STUDENT PROJECTS:\n{json.dumps(existing_projects or unified_profile.get('projects', []), indent=2)}\n\n"
        f"TARGET ROLE: {target_role}\n\n"
        f"VERIFIED DEMONSTRATED STRENGTHS:\n{json.dumps(user_strengths, indent=2)}\n\n"
        f"PRIORITIZED SKILL GAPS:\n{json.dumps(p_gaps, indent=2)}\n\n"
        f"TARGET ROADMAP DURATION: {dynamic_duration} weeks\n\n"
        f"E5 RETRIEVED COURSES:\n{json.dumps(e5_metadata, indent=2)}"
    )
    return generate_gemini_json(prompt, system_instruction=system_instruction)

