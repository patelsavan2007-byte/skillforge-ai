"""
test_skill_gap_engine.py
========================
Deterministic unit tests for SkillForge AI Skill Gap Engine.

Tests 1-10 match the specification in the master prompt exactly.
"""

import sys
import unittest

sys.path.insert(0, ".")
from app.services.skill_gap_engine import (
    compute_skill_gap,
    normalize_skill,
    normalize_skill_list,
    SKILL_ALIASES,
)
from app.services.career_service import REQUIRED_SKILLS_BY_ROLE


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FRONTEND_ROLES = [
    "AI/ML Engineer",
    "Data Scientist",
    "Data Analyst",
    "Data Engineer",
    "Software Engineer",
    "Frontend Developer",
    "Backend Developer",
    "Full Stack Developer",
    "Mobile App Developer",
    "DevOps Engineer",
    "Cloud Engineer",
    "Cybersecurity Engineer",
    "UI/UX Designer",
    "Product Manager",
    "QA Automation Engineer",
    "Blockchain Developer",
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestNormalization(unittest.TestCase):
    """Basic normalization and alias resolution."""

    def test_lowercase(self):
        self.assertEqual(normalize_skill("PYTHON"), "python")
        self.assertEqual(normalize_skill("Python"), "python")
        self.assertEqual(normalize_skill("python"), "python")

    def test_strip_whitespace(self):
        self.assertEqual(normalize_skill("  Python  "), "python")

    def test_react_alias(self):
        self.assertEqual(normalize_skill("React.js"), "react")
        self.assertEqual(normalize_skill("ReactJS"), "react")
        self.assertEqual(normalize_skill("react js"), "react")

    def test_sklearn_alias(self):
        self.assertEqual(normalize_skill("sklearn"), "scikit-learn")
        self.assertEqual(normalize_skill("scikit learn"), "scikit-learn")

    def test_nodejs_alias(self):
        self.assertEqual(normalize_skill("NodeJS"), "node.js")
        self.assertEqual(normalize_skill("node"), "node.js")

    def test_numpy_alias(self):
        # np -> numpy; but "numpy" itself
        self.assertEqual(normalize_skill("np"), "numpy")
        self.assertEqual(normalize_skill("NumPy"), "numpy")

    def test_tensorflow_alias(self):
        self.assertEqual(normalize_skill("TensorFlow"), "tensorflow")
        self.assertEqual(normalize_skill("tf"), "tensorflow")

    def test_pytorch_alias(self):
        self.assertEqual(normalize_skill("torch"), "pytorch")
        self.assertEqual(normalize_skill("PyTorch"), "pytorch")

    def test_java_is_not_javascript(self):
        """Java must NOT normalize to javascript."""
        self.assertNotEqual(normalize_skill("Java"), normalize_skill("JavaScript"))
        self.assertEqual(normalize_skill("Java"), "java")
        self.assertEqual(normalize_skill("JavaScript"), "javascript")

    def test_react_is_not_react_native(self):
        """React must NOT normalize to react native."""
        self.assertNotEqual(normalize_skill("React"), normalize_skill("React Native"))
        self.assertEqual(normalize_skill("React"), "react")
        self.assertEqual(normalize_skill("React Native"), "react native")

    def test_aws_is_not_azure(self):
        self.assertNotEqual(normalize_skill("AWS"), normalize_skill("Azure"))

    def test_sql_is_not_postgresql(self):
        self.assertNotEqual(normalize_skill("SQL"), normalize_skill("PostgreSQL"))

    def test_non_string_returns_empty(self):
        self.assertEqual(normalize_skill(None), "")  # type: ignore
        self.assertEqual(normalize_skill(123), "")   # type: ignore

    def test_empty_string(self):
        self.assertEqual(normalize_skill(""), "")


class TestNormalizeSkillList(unittest.TestCase):
    """Deduplication in normalize_skill_list."""

    def test_deduplication_case_insensitive(self):
        """TEST 6: Python, Python, python -> only one entry."""
        result = normalize_skill_list(["Python", "Python", "python"])
        self.assertEqual(result, ["python"])

    def test_dedup_via_alias(self):
        """React.js and React are the same after normalization."""
        result = normalize_skill_list(["React.js", "React", "reactjs"])
        self.assertEqual(result, ["react"])

    def test_empty_list(self):
        self.assertEqual(normalize_skill_list([]), [])

    def test_filters_empty_strings(self):
        result = normalize_skill_list(["", "  ", "Python"])
        self.assertEqual(result, ["python"])


class TestComputeSkillGap(unittest.TestCase):
    """Core engine compute_skill_gap tests matching specification Tests 1-10."""

    # ─── Test 1 ────────────────────────────────────────────────────────────
    def test_1_known_skills_are_strengths_not_gaps(self):
        """
        Student: Python, Pandas, NumPy | Role: Data Scientist
        Expected: Python, Pandas, NumPy are strengths — NOT gaps.
        """
        student = ["Python", "Pandas", "NumPy"]
        required = REQUIRED_SKILLS_BY_ROLE["Data Scientist"]
        result = compute_skill_gap(student, required)

        strengths_lower = [s.lower() for s in result["user_strengths"]]
        gaps_lower = [s.lower() for s in result["true_skill_gaps"]]

        self.assertIn("python", strengths_lower, "Python must be a strength")
        self.assertIn("pandas", strengths_lower, "Pandas must be a strength")
        self.assertIn("numpy", strengths_lower, "NumPy must be a strength")

        self.assertNotIn("python", gaps_lower, "Python must NOT be a gap")
        self.assertNotIn("pandas", gaps_lower, "Pandas must NOT be a gap")
        self.assertNotIn("numpy", gaps_lower, "NumPy must NOT be a gap")

    # ─── Test 2 ────────────────────────────────────────────────────────────
    def test_2_gaps_include_missing_skills(self):
        """
        Student: Python, Pandas, NumPy | Role: Data Scientist
        Expected: gaps include skills student actually lacks (SQL, Machine Learning, etc.)
        """
        student = ["Python", "Pandas", "NumPy"]
        required = REQUIRED_SKILLS_BY_ROLE["Data Scientist"]
        result = compute_skill_gap(student, required)

        gaps_lower = [s.lower() for s in result["true_skill_gaps"]]

        # Required skills that the student does NOT have
        self.assertIn("sql", gaps_lower)
        self.assertIn("machine learning", gaps_lower)
        self.assertIn("statistics", gaps_lower)
        self.assertIn("scikit-learn", gaps_lower)

    # ─── Test 3 ────────────────────────────────────────────────────────────
    def test_3_react_js_alias_is_strength_not_gap(self):
        """
        Student: React.js | Required: React
        Expected: strength=React, React must NOT be in gaps.
        """
        result = compute_skill_gap(["React.js"], ["React"])
        strengths_lower = [s.lower() for s in result["user_strengths"]]
        gaps_lower = [s.lower() for s in result["true_skill_gaps"]]

        self.assertIn("react", strengths_lower, "React.js should resolve to React strength")
        self.assertNotIn("react", gaps_lower, "React must NOT be in gaps")

    # ─── Test 4 ────────────────────────────────────────────────────────────
    def test_4_sklearn_alias_is_strength_not_gap(self):
        """
        Student: sklearn | Required: Scikit-learn
        Expected: strength=Scikit-learn, must NOT be in gaps.
        """
        result = compute_skill_gap(["sklearn"], ["Scikit-learn"])
        strengths_lower = [s.lower() for s in result["user_strengths"]]
        gaps_lower = [s.lower() for s in result["true_skill_gaps"]]

        self.assertIn("scikit-learn", strengths_lower)
        self.assertNotIn("scikit-learn", gaps_lower)

    # ─── Test 5 ────────────────────────────────────────────────────────────
    def test_5_java_is_not_javascript(self):
        """
        Student: Java | Required: JavaScript
        Expected: JavaScript remains a gap; Java does NOT satisfy JavaScript.
        """
        result = compute_skill_gap(["Java"], ["JavaScript"])
        gaps_lower = [s.lower() for s in result["true_skill_gaps"]]
        strengths_lower = [s.lower() for s in result["user_strengths"]]

        self.assertIn("javascript", gaps_lower, "JavaScript must remain a gap")
        self.assertNotIn("javascript", strengths_lower, "Java must not satisfy JavaScript")

    # ─── Test 6 ────────────────────────────────────────────────────────────
    def test_6_duplicate_student_skills_deduped(self):
        """
        Student: Python, Python, python
        Expected: only one normalized Python skill; no errors.
        """
        result = compute_skill_gap(["Python", "Python", "python"], ["Python"])
        # Should get exactly one match
        self.assertEqual(len(result["user_strengths"]), 1)
        self.assertEqual(result["user_strengths"][0].lower(), "python")
        self.assertEqual(len(result["true_skill_gaps"]), 0)

    # ─── Test 7 ────────────────────────────────────────────────────────────
    def test_7_empty_student_skills(self):
        """
        Student has no skills.
        Expected: user_strengths=[], true_skill_gaps=all required skills.
        """
        required = REQUIRED_SKILLS_BY_ROLE["Data Scientist"]
        result = compute_skill_gap([], required)

        self.assertEqual(result["user_strengths"], [])
        self.assertEqual(len(result["true_skill_gaps"]), len(required))

    # ─── Test 8 ────────────────────────────────────────────────────────────
    def test_8_student_has_all_required_skills(self):
        """
        Student has all required skills.
        Expected: true_skill_gaps=[].
        """
        required = ["Python", "SQL", "Machine Learning"]
        result = compute_skill_gap(required, required)

        self.assertEqual(result["true_skill_gaps"], [])
        self.assertEqual(len(result["user_strengths"]), len(required))

    # ─── Test 9 ────────────────────────────────────────────────────────────
    def test_9_all_16_roles_have_non_empty_required_skills(self):
        """
        Every role in the 16-role taxonomy must have a non-empty required skill set.
        """
        for role in FRONTEND_ROLES:
            required = REQUIRED_SKILLS_BY_ROLE.get(role)
            self.assertIsNotNone(required, f"Role not found in taxonomy: {role}")
            self.assertGreater(
                len(required), 0,
                f"Role '{role}' has empty required skills"
            )

    # ─── Test 10 ───────────────────────────────────────────────────────────
    def test_10_strengths_and_gaps_never_overlap(self):
        """
        For ALL 16 roles with various student skill sets:
        set(user_strengths) ∩ set(true_skill_gaps) must always be empty.
        """
        test_cases = [
            ["Python", "SQL", "React", "Docker"],
            ["Java", "Kotlin", "Android", "iOS"],
            ["Figma", "UI Design", "Wireframing"],
            ["Blockchain", "Solidity", "Web3", "JavaScript"],
            [],
        ]

        for role in FRONTEND_ROLES:
            required = REQUIRED_SKILLS_BY_ROLE[role]
            for student_skills in test_cases:
                result = compute_skill_gap(student_skills, required)
                strengths_set = set(s.lower() for s in result["user_strengths"])
                gaps_set = set(s.lower() for s in result["true_skill_gaps"])
                overlap = strengths_set & gaps_set
                self.assertEqual(
                    overlap, set(),
                    f"Role '{role}' with student {student_skills}: "
                    f"overlap detected: {overlap}"
                )


class TestRoleSpecificGaps(unittest.TestCase):
    """Spot-checks for specific role taxonomies."""

    def test_devops_has_kubernetes_and_cicd(self):
        req = REQUIRED_SKILLS_BY_ROLE["DevOps Engineer"]
        req_lower = [r.lower() for r in req]
        self.assertIn("kubernetes", req_lower)
        self.assertIn("ci/cd", req_lower)
        self.assertIn("docker", req_lower)

    def test_frontend_has_html_css_react(self):
        req = REQUIRED_SKILLS_BY_ROLE["Frontend Developer"]
        req_lower = [r.lower() for r in req]
        self.assertIn("html", req_lower)
        self.assertIn("css", req_lower)
        self.assertIn("react", req_lower)

    def test_mobile_has_flutter_and_react_native(self):
        req = REQUIRED_SKILLS_BY_ROLE["Mobile App Developer"]
        req_lower = [r.lower() for r in req]
        self.assertIn("flutter", req_lower)
        self.assertIn("react native", req_lower)

    def test_blockchain_has_solidity_and_web3(self):
        req = REQUIRED_SKILLS_BY_ROLE["Blockchain Developer"]
        req_lower = [r.lower() for r in req]
        self.assertIn("solidity", req_lower)
        self.assertIn("web3", req_lower)
        self.assertIn("smart contracts", req_lower)

    def test_uiux_has_figma_and_wireframing(self):
        req = REQUIRED_SKILLS_BY_ROLE["UI/UX Designer"]
        req_lower = [r.lower() for r in req]
        self.assertIn("figma", req_lower)
        self.assertIn("wireframing", req_lower)

    def test_product_manager_has_agile_and_scrum(self):
        req = REQUIRED_SKILLS_BY_ROLE["Product Manager"]
        req_lower = [r.lower() for r in req]
        self.assertIn("agile", req_lower)
        self.assertIn("scrum", req_lower)

    def test_qa_has_selenium_playwright_cypress(self):
        req = REQUIRED_SKILLS_BY_ROLE["QA Automation Engineer"]
        req_lower = [r.lower() for r in req]
        self.assertIn("selenium", req_lower)
        self.assertIn("playwright", req_lower)
        self.assertIn("cypress", req_lower)

    def test_cybersec_has_penetration_testing_and_owasp(self):
        req = REQUIRED_SKILLS_BY_ROLE["Cybersecurity Engineer"]
        req_lower = [r.lower() for r in req]
        self.assertIn("penetration testing", req_lower)
        self.assertIn("owasp", req_lower)

    def test_cloud_has_aws_azure_gcp(self):
        req = REQUIRED_SKILLS_BY_ROLE["Cloud Engineer"]
        req_lower = [r.lower() for r in req]
        self.assertIn("aws", req_lower)
        self.assertIn("azure", req_lower)
        self.assertIn("google cloud", req_lower)

    def test_nodejs_alias_in_backend_developer_check(self):
        """Student writes 'NodeJS' -> should satisfy 'Node.js' requirement."""
        result = compute_skill_gap(
            ["NodeJS", "Python", "SQL"],
            REQUIRED_SKILLS_BY_ROLE["Backend Developer"],
        )
        strengths_lower = [s.lower() for s in result["user_strengths"]]
        gaps_lower = [s.lower() for s in result["true_skill_gaps"]]
        self.assertIn("node.js", strengths_lower)
        self.assertNotIn("node.js", gaps_lower)


class TestSafeAliasRules(unittest.TestCase):
    """Verify SKILL_ALIASES does not contain unsafe mappings."""

    def test_no_java_to_javascript_mapping(self):
        self.assertNotIn("java", SKILL_ALIASES)

    def test_no_react_to_react_native_mapping(self):
        # 'react' by itself must not alias to 'react native'
        if "react" in SKILL_ALIASES:
            self.assertNotEqual(SKILL_ALIASES["react"], "react native")

    def test_no_sql_to_postgresql_mapping(self):
        if "sql" in SKILL_ALIASES:
            self.assertNotEqual(SKILL_ALIASES["sql"], "postgresql")

    def test_no_python_to_pytorch_mapping(self):
        if "python" in SKILL_ALIASES:
            self.assertNotEqual(SKILL_ALIASES["python"], "pytorch")

    def test_no_ml_to_deep_learning_mapping(self):
        if "ml" in SKILL_ALIASES:
            self.assertNotEqual(SKILL_ALIASES["ml"], "deep learning")


if __name__ == "__main__":
    unittest.main(verbosity=2)
