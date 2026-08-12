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

def generate_gemini_json(prompt: str, system_instruction: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Call Gemini API to generate structured JSON. Returns None if API key missing or call fails."""
    client = _get_genai_client()
    if not client:
        return None

    try:
        # Use gemini-2.5-flash as default model
        config = {
            "response_mime_type": "application/json",
            "temperature": 0.2,
        }
        if system_instruction:
            config["system_instruction"] = system_instruction

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=config,
        )
        if response and response.text:
            return _clean_json_response(response.text)
    except Exception as e:
        logger.error(f"Gemini API generation error: {e}")
        print(f"[Gemini Service] API call failed: {e}")

    return None

# PROMPT HELPERS

def analyze_resume_with_gemini(raw_text: str) -> Optional[Dict[str, Any]]:
    """Send raw resume text to Gemini for structured extraction."""
    system_instruction = (
        "You are an expert resume parser. Extract candidate information from raw resume text. "
        "Return ONLY a JSON object matching this schema:\n"
        "{\n"
        '  "name": "Candidate Full Name",\n'
        '  "email": "email@example.com",\n'
        '  "phone": "+1234567890",\n'
        '  "location": "City, Country",\n'
        '  "education": [{"degree": "", "field": "", "institution": "", "startDate": "", "endDate": "", "cgpa": null}],\n'
        '  "experience": [{"company": "", "title": "", "startDate": "", "endDate": "", "description": ""}],\n'
        '  "skills": ["Skill1", "Skill2"],\n'
        '  "projects": [{"name": "", "description": "", "technologies": ["Tech1", "Tech2"], "url": ""}],\n'
        '  "certifications": ["Cert1"],\n'
        '  "technologies": ["Tech1", "Tech2"],\n'
        '  "achievements": ["Achievement1"]\n'
        "}"
    )
    prompt = f"Resume Content:\n{raw_text[:8000]}"
    return generate_gemini_json(prompt, system_instruction=system_instruction)

def analyze_portfolio_with_gemini(url: str, html_text: str) -> Optional[Dict[str, Any]]:
    """Send portfolio page content to Gemini for structured extraction."""
    system_instruction = (
        "You are a developer portfolio analyzer. Extract candidate portfolio details from webpage text. "
        "Return ONLY a JSON object matching this schema:\n"
        "{\n"
        '  "name": "Developer Name",\n'
        '  "bio": "Short summary or bio from portfolio",\n'
        '  "skills": ["Skill1", "Skill2"],\n'
        '  "projects": [{"name": "", "description": "", "technologies": ["Tech1"], "github": "", "url": ""}],\n'
        '  "technologies": ["Tech1", "Tech2"],\n'
        '  "certifications": ["Cert1"],\n'
        '  "experience": [{"company": "", "title": "", "description": ""}],\n'
        '  "education": [{"degree": "", "field": "", "institution": ""}]\n'
        "}"
    )
    prompt = f"Portfolio URL: {url}\nPage Text:\n{html_text[:8000]}"
    return generate_gemini_json(prompt, system_instruction=system_instruction)

def merge_profiles_with_gemini(resume_profile: Dict[str, Any], portfolio_profile: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Send resume and portfolio profiles to Gemini to intelligently merge and resolve duplicates."""
    system_instruction = (
        "You are an expert career profiler. Unify candidate details from both Resume and Portfolio sources. "
        "Deduplicate skills, combine projects keeping the most detailed description, preserve resume work history, "
        "and return a single Unified Profile JSON matching this schema:\n"
        "{\n"
        '  "name": "Full Name",\n'
        '  "bio": "Combined bio summary",\n'
        '  "education": [...],\n'
        '  "experience": [...],\n'
        '  "skills": ["Skill1", "Skill2"],\n'
        '  "projects": [{"name": "", "description": "", "technologies": [], "url": ""}],\n'
        '  "certifications": [...],\n'
        '  "technologies": [...],\n'
        '  "achievements": [...]\n'
        "}"
    )
    prompt = (
        f"RESUME PROFILE:\n{json.dumps(resume_profile, indent=2)}\n\n"
        f"PORTFOLIO PROFILE:\n{json.dumps(portfolio_profile, indent=2)}"
    )
    return generate_gemini_json(prompt, system_instruction=system_instruction)

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
    skill_gaps: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """Generate personalized roadmap, courses, projects, certifications, interview questions, and advice."""
    system_instruction = (
        f"You are an AI Career Mentor creating a personalized career plan for role: '{target_role}'. "
        "All recommendations MUST be directly tailored to address the identified skill gaps. "
        "Return ONLY a JSON object matching this schema:\n"
        "{\n"
        '  "durationWeeks": 8,\n'
        '  "roadmap": [\n'
        '    {"week": 1, "title": "Phase Title", "skills": ["Skill1"], "courses": [{"title": "", "provider": "", "url": "", "duration": "", "difficulty": ""}], "project": {"title": "", "description": "", "skills": []}, "completed": false}\n'
        '  ],\n'
        '  "courses": [{"title": "", "provider": "", "url": "", "duration": "", "difficulty": "", "skillAddressed": ""}],\n'
        '  "recommendedProjects": [{"title": "", "description": "", "technologies": [], "difficulty": ""}],\n'
        '  "certifications": [{"name": "", "provider": "", "priority": "High/Medium"}],\n'
        '  "interviewPrep": [{"topic": "", "question": "", "keyConcept": ""}],\n'
        '  "careerAdvice": ["Advice bullet 1", "Advice bullet 2"]\n'
        "}"
    )
    prompt = (
        f"Target Role: {target_role}\n"
        f"Skill Gaps: {json.dumps(skill_gaps, indent=2)}\n"
        f"Candidate Profile: {json.dumps(unified_profile, indent=2)}"
    )
    return generate_gemini_json(prompt, system_instruction=system_instruction)
