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
        '  "profileSummary": "Detailed 2-3 sentence career evaluation",\n'
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
    e5_courses: Optional[List[Dict[str, Any]]] = None
) -> Optional[Dict[str, Any]]:
    """Generate an explanatory roadmap from deterministic data and E5 metadata only."""
    system_instruction = (
        f"You are an AI Career Mentor creating a personalized career plan for role: '{target_role}'. "
        "VERIFIED STRENGTHS and VERIFIED SKILL GAPS are deterministic facts; do not modify, "
        "replace, or invent them. All recommendations MUST address the verified skill gaps. "
        "E5 RETRIEVED COURSES are the only permitted source of course titles, providers, and URLs. "
        "Do NOT invent courses, providers, or URLs. A course not present in E5 RETRIEVED COURSES "
        "must have an empty URL. "
        "Return ONLY a JSON object matching this schema:\n"
        "{\n"
        '  "durationWeeks": 8,\n'
        '  "roadmap": [\n'
        '    {"week": 1, "title": "Phase Title", "milestone_title": "Phase Title", "objective": "", "skills": ["Skill1"], "skills_addressed": ["Skill1"], "learning_tasks": [""], "estimated_duration": "", "courses": [{"title": "", "provider": "", "url": "", "duration": "", "difficulty": ""}], "related_courses": [{"title": "", "url": ""}], "project": {"title": "", "description": "", "skills": []}, "checkpoint": "", "completed": false}\n'
        '  ],\n'
        '  "courses": [{"title": "", "provider": "", "url": "", "duration": "", "difficulty": "", "skillAddressed": ""}],\n'
        '  "recommendedProjects": [{"title": "", "description": "", "technologies": [], "difficulty": ""}],\n'
        '  "certifications": [{"name": "", "provider": "", "priority": "High/Medium"}],\n'
        '  "interviewPrep": [{"topic": "", "question": "", "keyConcept": ""}],\n'
        '  "careerAdvice": ["Advice bullet 1", "Advice bullet 2"]\n'
        "}"
    )
    # E5 returns metadata only. Deliberately do not add embedding vectors here.
    e5_metadata = [
        {
            key: course.get(key)
            for key in ("title", "provider", "url", "description", "skills", "duration", "difficulty", "similarity_score")
        }
        for course in (e5_courses or [])
        if isinstance(course, dict)
    ]
    prompt = (
        f"PROFILE:\n{json.dumps(unified_profile, indent=2)}\n\n"
        f"TARGET ROLE: {target_role}\n\n"
        f"VERIFIED STRENGTHS:\n{json.dumps(user_strengths, indent=2)}\n\n"
        f"VERIFIED SKILL GAPS:\n{json.dumps(true_skill_gaps, indent=2)}\n\n"
        f"E5 RETRIEVED COURSES:\n{json.dumps(e5_metadata, indent=2)}"
    )
    return generate_gemini_json(prompt, system_instruction=system_instruction)

