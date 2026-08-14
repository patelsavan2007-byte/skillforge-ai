"""
test_e5_course_retrieval.py
============================
Unit & Integration Tests for intfloat/e5-base-v2 Semantic Course Retrieval in SkillForge AI.
"""

import sys
import unittest
import numpy as np

sys.path.insert(0, ".")

from app.services.skill_gap_engine import compute_skill_gap
from app.services.career_service import REQUIRED_SKILLS_BY_ROLE
from app.services.embedding_service import (
    init_e5_service,
    rank_courses_with_e5,
    _construct_course_passage_text,
    compute_cosine_similarity,
)


class TestE5CourseRetrieval(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Ensure E5 service is initialized once before tests."""
        cls.initialized = init_e5_service()

    def test_01_e5_model_and_service_initialization(self):
        """Verify intfloat/e5-base-v2 model and course catalog load successfully."""
        self.assertTrue(self.initialized, "E5 service should initialize successfully")

    def test_02_passage_prefix_construction(self):
        """Verify course text constructs with required 'passage: ' prefix."""
        sample_course = {
            "title": "Machine Learning Engineering",
            "description": "Deploy models to production",
            "skills": ["MLOps", "Docker"],
            "platform": "Coursera",
            "category": "AI/ML Engineer",
        }
        passage_text = _construct_course_passage_text(sample_course)
        self.assertTrue(passage_text.startswith("passage: "))
        self.assertIn("Machine Learning Engineering", passage_text)
        self.assertIn("MLOps", passage_text)

    def test_03_cosine_similarity_computation(self):
        """Verify cosine similarity calculation produces correct dot product scores."""
        query_vec = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        doc_vecs = np.array([
            [1.0, 0.0, 0.0],   # Perfect match -> 1.0
            [0.7071, 0.7071, 0.0], # Partial match -> 0.7071
            [0.0, 1.0, 0.0],   # Orthogonal -> 0.0
        ], dtype=np.float32)

        scores = compute_cosine_similarity(query_vec, doc_vecs)
        self.assertAlmostEqual(float(scores[0]), 1.0, places=3)
        self.assertAlmostEqual(float(scores[1]), 0.7071, places=3)
        self.assertAlmostEqual(float(scores[2]), 0.0, places=3)

    def test_04_mlops_and_docker_gap_course_ranking(self):
        """
        Integration test:
        Student has Python, Machine Learning.
        Required: AI/ML Engineer (includes Deep Learning, MLOps, Docker, etc.)
        Deterministic true_skill_gaps: Deep Learning, TensorFlow, PyTorch, Model Deployment, MLOps...
        E5 should rank MLOps/Deep Learning/Docker courses highest with similarity scores.
        """
        student_skills = ["Python", "Machine Learning", "Scikit-learn", "Pandas", "NumPy", "SQL"]
        required = REQUIRED_SKILLS_BY_ROLE["AI/ML Engineer"]

        gap_result = compute_skill_gap(student_skills, required)
        true_skill_gaps = gap_result["true_skill_gaps"]

        self.assertIn("Deep Learning", true_skill_gaps)

        courses = rank_courses_with_e5(true_skill_gaps, top_k=5)
        self.assertIsNotNone(courses)
        self.assertGreaterEqual(len(courses), 3)
        self.assertLessEqual(len(courses), 5)

        # Check descending order of similarity_score
        scores = [c["similarity_score"] for c in courses]
        self.assertEqual(scores, sorted(scores, reverse=True), "Courses must be ranked descending by similarity score")

        # Verify real URLs are preserved
        for c in courses:
            self.assertTrue(c["url"].startswith("https://"), f"Course URL must be real URL: {c['url']}")
            self.assertIn("similarity_score", c)
            self.assertIsInstance(c["similarity_score"], float)

    def test_05_frontend_developer_gap_course_ranking(self):
        """
        Student has HTML, CSS, JavaScript.
        Required: Frontend Developer (includes React, TypeScript, Tailwind CSS...)
        E5 should rank React/Frontend courses highest.
        """
        student_skills = ["HTML", "CSS", "JavaScript"]
        required = REQUIRED_SKILLS_BY_ROLE["Frontend Developer"]

        gap_result = compute_skill_gap(student_skills, required)
        true_skill_gaps = gap_result["true_skill_gaps"]

        self.assertIn("React", true_skill_gaps)

        courses = rank_courses_with_e5(true_skill_gaps, top_k=3)
        self.assertIsNotNone(courses)
        self.assertGreaterEqual(len(courses), 3)

        # Top course should address React / Frontend
        top_title = courses[0]["title"]
        self.assertTrue("React" in top_title or "Frontend" in top_title or "HTML" in top_title)

    def test_06_empty_skill_gaps_handling(self):
        """Empty skill gaps list returns None cleanly without crashing."""
        courses = rank_courses_with_e5([], top_k=5)
        self.assertIsNone(courses)


if __name__ == "__main__":
    unittest.main(verbosity=2)
