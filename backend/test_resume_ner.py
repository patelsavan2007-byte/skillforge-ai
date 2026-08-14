"""Self-contained tests for the runtime resume NER and deterministic extractor."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.resume_extractor import build_structured_resume, extract_academic_scores, extract_projects_from_text, extract_skills_from_text
from app.services.profile_merge_service import merge_student_profiles
from app.services.resume_ner import get_ner_service


TEST_RESUME_TEXT = """
John Smith
john@example.com
Ahmedabad, Gujarat

EDUCATION
B.Tech in Computer Science
Gujarat Technological University
2022 - 2026
CGPA: 8.7

SKILLS
Python, Java, React, FastAPI, MongoDB, TensorFlow

PROJECTS
SkillForge AI
AI-powered career mentor application using React, FastAPI, MongoDB and machine learning.
"""


class TestResumeNERPipeline(unittest.TestCase):
    def test_01_academic_scores(self):
        self.assertEqual(extract_academic_scores("CGPA: 8.7 SGPA: 8.9"), {"cgpa": 8.7, "sgpa": 8.9})

    def test_02_extractor_preserves_regex_fallbacks(self):
        profile = build_structured_resume(TEST_RESUME_TEXT, [])
        self.assertEqual(profile["personal"]["email"], "john@example.com")
        self.assertIn("Python", profile["skills"])
        self.assertEqual(profile["projects"][0]["name"], "SkillForge AI")

    def test_03_projects_use_detected_skills(self):
        projects = extract_projects_from_text(TEST_RESUME_TEXT, ["React", "FastAPI", "MongoDB"])
        self.assertIn("React", projects[0]["technologies"])

    def test_04_ner_chunks_long_resumes(self):
        service = get_ner_service()
        self.assertGreater(len(service.chunk_text((TEST_RESUME_TEXT + "\n") * 10)), 1)
        self.assertIsInstance(service.extract_entities(TEST_RESUME_TEXT), list)

    def test_05_controlled_fallback_recovers_project_technologies(self):
        text = "Built an AI model integration with Python, React, Flask, MongoDB and TensorFlow."
        self.assertEqual(
            extract_skills_from_text(text),
            ["Python", "React", "Flask", "MongoDB", "TensorFlow"],
        )

    def test_06_merge_preserves_resume_technologies_as_canonical_skills(self):
        merged = merge_student_profiles(
            {"skills": ["python", "React"], "technologies": ["Mongo", "Flask"]},
            {"skills": ["reactjs"], "technologies": ["TensorFlow"]},
        )
        self.assertEqual(merged["skills"], ["Python", "React", "MongoDB", "Flask", "TensorFlow"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
