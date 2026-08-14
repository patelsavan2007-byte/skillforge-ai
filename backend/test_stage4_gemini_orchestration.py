"""Regression tests for deterministic Stage 4 Gemini orchestration."""

import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, ".")

from app.services import gemini_service
from app.services.learning_service import _sanitize_gemini_output, generate_personalized_recommendations


E5_COURSES = [{
    "title": "Real Python Course", "provider": "Catalog", "url": "https://catalog.example/python",
    "description": "A real catalog description", "skills": ["Python"], "duration": "4 weeks",
    "difficulty": "Intermediate", "similarity_score": 0.91,
}]


class TestStage4GeminiOrchestration(unittest.TestCase):
    def test_01_gemini_model_is_gemini_2_5_flash(self):
        self.assertEqual(gemini_service.GEMINI_MODEL_CANDIDATES, ["gemini-2.5-flash"])

    def test_02_prompt_receives_deterministic_skill_data(self):
        with patch.object(gemini_service, "generate_gemini_json", return_value={}) as call:
            gemini_service.generate_recommendations_with_gemini(
                {"name": "Ada"}, "Engineer", ["Python"], ["Docker"], E5_COURSES
            )
        prompt = call.call_args.args[0]
        self.assertIn("VERIFIED STRENGTHS", prompt)
        self.assertIn("Python", prompt)
        self.assertIn("VERIFIED SKILL GAPS", prompt)
        self.assertIn("Docker", prompt)

    def test_03_gemini_cannot_override_true_skill_gaps(self):
        response = {"roadmap": [{"title": "Docker", "skills": ["Docker"], "courses": []}], "true_skill_gaps": ["Fake"]}
        with patch("app.services.learning_service.rank_courses_with_e5", return_value=E5_COURSES), patch(
            "app.services.learning_service.generate_recommendations_with_gemini", return_value=response
        ):
            result = generate_personalized_recommendations({}, "Engineer", ["Docker"], user_strengths=["Python"])
        self.assertEqual(result["true_skill_gaps"], ["Docker"])

    def test_04_gemini_cannot_override_user_strengths(self):
        response = {"roadmap": [{"title": "Docker", "skills": [], "courses": []}], "user_strengths": ["Fake"]}
        with patch("app.services.learning_service.rank_courses_with_e5", return_value=E5_COURSES), patch(
            "app.services.learning_service.generate_recommendations_with_gemini", return_value=response
        ):
            result = generate_personalized_recommendations({}, "Engineer", ["Docker"], user_strengths=["Python"])
        self.assertEqual(result["user_strengths"], ["Python"])

    def test_05_e5_metadata_has_no_embeddings_in_prompt(self):
        course = dict(E5_COURSES[0], embedding=[0.1] * 768)
        with patch.object(gemini_service, "generate_gemini_json", return_value={}) as call:
            gemini_service.generate_recommendations_with_gemini({}, "Engineer", [], ["Python"], [course])
        self.assertNotIn("embedding", call.call_args.args[0])

    def test_06_e5_course_metadata_is_sent_to_gemini(self):
        with patch.object(gemini_service, "generate_gemini_json", return_value={}) as call:
            gemini_service.generate_recommendations_with_gemini({}, "Engineer", [], ["Python"], E5_COURSES)
        prompt = call.call_args.args[0]
        for value in ("Real Python Course", "https://catalog.example/python", "A real catalog description"):
            self.assertIn(value, prompt)

    def test_07_e5_course_urls_are_restored_after_gemini(self):
        result = _sanitize_gemini_output({"courses": [{"title": "Real Python Course", "url": "https://fake"}], "roadmap": []}, E5_COURSES)
        self.assertEqual(result["courses"][0]["url"], E5_COURSES[0]["url"])

    def test_08_fabricated_course_urls_are_discarded(self):
        result = _sanitize_gemini_output({"courses": [{"title": "Invented", "url": "https://fake"}], "roadmap": []}, E5_COURSES)
        self.assertEqual(result["courses"][0]["url"], "")

    def test_09_roadmap_urls_are_sanitized(self):
        result = _sanitize_gemini_output({"courses": [], "roadmap": [{"title": "Week", "courses": [{"title": "Real Python Course", "url": "bad"}]}]}, E5_COURSES)
        self.assertEqual(result["roadmap"][0]["courses"][0]["url"], E5_COURSES[0]["url"])

    def test_10_fallback_projects_relate_to_skill_gaps(self):
        with patch("app.services.learning_service.rank_courses_with_e5", return_value=None), patch(
            "app.services.learning_service.generate_recommendations_with_gemini", return_value=None
        ):
            result = generate_personalized_recommendations({}, "Engineer", ["Kubernetes"])
        self.assertTrue(result["recommendedProjects"])
        self.assertIn("Kubernetes", result["recommendedProjects"][0]["technologies"])

    def test_11_fallback_interview_prep_is_structured(self):
        with patch("app.services.learning_service.rank_courses_with_e5", return_value=None), patch(
            "app.services.learning_service.generate_recommendations_with_gemini", return_value=None
        ):
            result = generate_personalized_recommendations({}, "Engineer", ["Kubernetes"])
        self.assertTrue(all({"topic", "question", "keyConcept"} <= item.keys() for item in result["interviewPrep"]))

    def test_12_malformed_gemini_json_uses_fallback(self):
        with patch("app.services.learning_service.rank_courses_with_e5", return_value=None), patch(
            "app.services.learning_service.generate_recommendations_with_gemini", return_value=None
        ):
            result = generate_personalized_recommendations({}, "Engineer", ["Docker"])
        self.assertTrue(result["roadmap"])

    def test_13_gemini_failure_preserves_e5_courses(self):
        with patch("app.services.learning_service.rank_courses_with_e5", return_value=E5_COURSES), patch(
            "app.services.learning_service.generate_recommendations_with_gemini", return_value=None
        ):
            result = generate_personalized_recommendations({}, "Engineer", ["Python"])
        self.assertEqual(result["courses"], E5_COURSES)

    def test_14_fallback_urls_are_not_fabricated(self):
        with patch("app.services.learning_service.rank_courses_with_e5", return_value=None), patch(
            "app.services.learning_service.generate_recommendations_with_gemini", return_value=None
        ):
            result = generate_personalized_recommendations({}, "Engineer", ["Docker"])
        urls = [course["url"] for item in result["roadmap"] for course in item["courses"]]
        self.assertTrue(all(not url for url in urls))


if __name__ == "__main__":
    unittest.main(verbosity=2)
