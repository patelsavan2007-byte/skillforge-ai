"""Stage 1 Architecture Verification Tests"""
import asyncio
from app.services.resume_ner import get_ner_service
from app.services.resume_extractor import build_structured_resume
from app.services.profile_merge_service import merge_student_profiles
from app.services.portfolio_service import analyze_portfolio_url

def test_structured_resume_fallback():
    """Test that build_structured_resume produces valid output even with empty NER entities."""
    print("=== Test 1: Structured resume with empty NER entities (deterministic fallback) ===")
    test_text = """John Smith
john@example.com
Ahmedabad, Gujarat

EDUCATION
B.Tech in Computer Science
Gujarat Technological University
2022 - 2026
CGPA: 8.7

SKILLS
Python, Java, React, FastAPI, MongoDB, TensorFlow

EXPERIENCE
Software Engineering Intern
ABC Technologies
May 2025 - July 2025

PROJECTS
SkillForge AI
AI-powered career mentor application using React, FastAPI, MongoDB and machine learning.

CERTIFICATIONS
AWS Certified Cloud Practitioner

LANGUAGES
English, Hindi, Gujarati
"""
    # Empty entities - tests deterministic fallback in resume_extractor
    profile = build_structured_resume(test_text, [])
    print(f"Resume skills (fallback): {profile['skills']}")
    print(f"Resume personal: {profile['personal']}")
    print(f"Resume education count: {len(profile['education'])}")
    print(f"Resume experience count: {len(profile['experience'])}")
    print(f"Resume projects count: {len(profile['projects'])}")
    assert profile["personal"]["name"], "Name should not be empty"
    assert profile["personal"]["email"], "Email should be extracted via regex fallback"
    assert len(profile["education"]) > 0, "Education should be extracted"
    # Note: experience has no regex fallback in existing code when NER is empty - that's existing behavior
    assert len(profile["projects"]) > 0, "Projects should be extracted"
    print("PASSED")

def test_structured_resume_with_ner_entities():
    """Test build_structured_resume with actual NER-like entities."""
    print("\n=== Test 2: Structured resume with NER-like entities ===")
    test_text = """John Smith
john@example.com
Ahmedabad, Gujarat

EDUCATION
B.Tech in Computer Science
Gujarat Technological University
2022 - 2026
CGPA: 8.7

SKILLS
Python, Java, React, FastAPI, MongoDB, TensorFlow

EXPERIENCE
Software Engineering Intern
ABC Technologies
May 2025 - July 2025

PROJECTS
SkillForge AI
AI-powered career mentor application using React, FastAPI, MongoDB and machine learning.

CERTIFICATIONS
AWS Certified Cloud Practitioner

LANGUAGES
English, Hindi, Gujarati
"""
    # Simulate NER entities (same format as oksomu/resume-ner output)
    entities = [
        {"text": "John Smith", "label": "NAME", "score": 0.98},
        {"text": "john@example.com", "label": "EMAIL", "score": 0.99},
        {"text": "Ahmedabad", "label": "LOCATION", "score": 0.95},
        {"text": "B.Tech", "label": "DEGREE", "score": 0.92},
        {"text": "Computer Science", "label": "FIELD", "score": 0.90},
        {"text": "Gujarat Technological University", "label": "INSTITUTION", "score": 0.93},
        {"text": "ABC Technologies", "label": "COMPANY", "score": 0.94},
        {"text": "Software Engineering Intern", "label": "TITLE", "score": 0.91},
        {"text": "Python", "label": "SKILL", "score": 0.97},
        {"text": "Java", "label": "SKILL", "score": 0.96},
        {"text": "React", "label": "SKILL", "score": 0.95},
        {"text": "FastAPI", "label": "SKILL", "score": 0.94},
        {"text": "MongoDB", "label": "SKILL", "score": 0.93},
        {"text": "TensorFlow", "label": "SKILL", "score": 0.92},
        {"text": "AWS Certified Cloud Practitioner", "label": "CERT", "score": 0.89},
        {"text": "English", "label": "LANGUAGE", "score": 0.88},
        {"text": "Hindi", "label": "LANGUAGE", "score": 0.87},
        {"text": "Gujarati", "label": "LANGUAGE", "score": 0.86},
    ]
    profile = build_structured_resume(test_text, entities)
    print(f"Resume skills: {profile['skills']}")
    print(f"Resume personal: {profile['personal']}")
    print(f"Resume education count: {len(profile['education'])}")
    print(f"Resume experience count: {len(profile['experience'])}")
    print(f"Resume projects count: {len(profile['projects'])}")
    print(f"Resume certifications: {profile['certifications']}")
    print(f"Resume languages: {profile['languages']}")
    assert "Python" in profile["skills"], "Python should be in skills"
    assert "React" in profile["skills"], "React should be in skills"
    assert profile["personal"]["name"] == "John Smith", "Name should be from NER"
    assert profile["personal"]["email"] == "john@example.com", "Email should be from NER"
    assert len(profile["education"]) > 0, "Education should exist"
    assert len(profile["experience"]) > 0, "Experience should exist"
    print("PASSED")

def test_deterministic_profile_merge():
    print("\n=== Test 3: Deterministic profile merge ===")
    resume_profile = {
        "personal": {"name": "John Smith"},
        "skills": ["Python", "React", "FastAPI"],
        "projects": [{"name": "SkillForge AI", "description": "AI app", "technologies": ["Python", "FastAPI"]}],
        "education": [{"degree": "B.Tech"}],
        "experience": [{"company": "ABC Technologies"}]
    }
    portfolio_profile = {
        "name": "John Smith",
        "bio": "Developer",
        "skills": ["Python", "React", "MongoDB"],
        "projects": [{"name": "SkillForge AI", "description": "AI career mentor", "technologies": ["React", "FastAPI", "MongoDB"]}]
    }
    merged = merge_student_profiles(resume_profile, portfolio_profile)
    print(f"Merged skills: {merged['skills']}")
    print(f"Merged projects count: {len(merged['projects'])}")
    print(f"Merged source: {merged['source']}")
    assert "Python" in merged["skills"], "Python should be in merged skills"
    assert "React" in merged["skills"], "React should be in merged skills"
    assert "MongoDB" in merged["skills"], "MongoDB should be in merged skills"
    assert "FastAPI" in merged["skills"], "FastAPI should be in merged skills"
    assert len(merged["skills"]) == 4, f"Should have 4 unique skills, got {len(merged['skills'])}"
    assert merged["source"]["resume"] is True
    assert merged["source"]["portfolio"] is True
    print("PASSED")

def test_portfolio_deterministic_analysis():
    print("\n=== Test 4: Portfolio deterministic analysis ===")
    result = asyncio.run(analyze_portfolio_url("https://example.com"))
    print(f"Portfolio skills: {result['skills']}")
    print(f"Portfolio projects count: {len(result['projects'])}")
    assert "skills" in result, "Portfolio should have skills"
    assert len(result["projects"]) > 0, "Portfolio should have at least one project"
    print("PASSED")

def test_profile_merge_resume_only():
    print("\n=== Test 5: Profile merge resume only ===")
    resume_profile = {
        "personal": {"name": "Jane Doe"},
        "skills": ["Python", "SQL"],
        "projects": [{"name": "Data Project", "description": "Data analysis", "technologies": ["Python", "SQL"]}]
    }
    merged = merge_student_profiles(resume_profile=resume_profile)
    assert merged["source"]["resume"] is True
    assert merged["source"]["portfolio"] is False
    assert "Python" in merged["skills"]
    assert "SQL" in merged["skills"]
    print("PASSED")

def test_profile_merge_portfolio_only():
    print("\n=== Test 6: Profile merge portfolio only ===")
    portfolio_profile = {
        "name": "Jane Doe",
        "bio": "Developer",
        "skills": ["JavaScript", "React"],
        "projects": [{"name": "Web App", "technologies": ["JavaScript", "React"]}]
    }
    merged = merge_student_profiles(portfolio_profile=portfolio_profile)
    assert merged["source"]["resume"] is False
    assert merged["source"]["portfolio"] is True
    assert "JavaScript" in merged["skills"]
    assert "React" in merged["skills"]
    print("PASSED")

def test_profile_merge_neither_raises():
    print("\n=== Test 7: Profile merge neither raises ValueError ===")
    try:
        merge_student_profiles(resume_profile=None, portfolio_profile=None)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "At least one profile source" in str(e)
        print("PASSED")

def test_gemini_not_called_in_stage1():
    """Verify Gemini is not imported in the modified Stage 1 files."""
    print("\n=== Test 8: Gemini not imported in Stage 1 services ===")
    import ast
    
    files_to_check = [
        "app/services/resume_service.py",
        "app/services/portfolio_service.py",
        "app/services/profile_merge_service.py",
    ]
    
    for filepath in files_to_check:
        with open(filepath, "r") as f:
            content = f.read()
        tree = ast.parse(content)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and "gemini" in node.module:
                    imports.append(f"from {node.module} import ...")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if "gemini" in alias.name:
                        imports.append(f"import {alias.name}")
        
        if imports:
            print(f"FAIL: {filepath} still imports Gemini: {imports}")
            assert False, f"{filepath} still imports Gemini"
        else:
            print(f"OK: {filepath} does not import Gemini")
    
    print("PASSED")

if __name__ == "__main__":
    test_structured_resume_fallback()
    test_structured_resume_with_ner_entities()
    test_deterministic_profile_merge()
    test_portfolio_deterministic_analysis()
    test_profile_merge_resume_only()
    test_profile_merge_portfolio_only()
    test_profile_merge_neither_raises()
    test_gemini_not_called_in_stage1()
    print("\n=== ALL STAGE 1 ARCHITECTURE TESTS PASSED ===")
