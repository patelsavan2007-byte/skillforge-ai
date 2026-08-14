import unittest
from app.services.recommendation_engine import (
    build_evidence_profile,
    compute_prioritized_gaps,
    calculate_dynamic_duration,
    filter_and_validate_recommendations,
)
from app.services.career_service import generate_career_analysis
from app.services.learning_service import generate_personalized_recommendations


class TestRecommendationEngine(unittest.TestCase):

    def test_profile_a_full_stack_developer(self):
        """
        TEST A: React + Next.js + Node + PostgreSQL + Docker
        Target: Full Stack Developer
        Expected: Advanced full-stack gaps, NOT beginner HTML/CSS.
        """
        profile = {
            "name": "Alex FullStack",
            "skills": ["React", "Next.js", "JavaScript", "TypeScript", "Node.js", "REST APIs", "PostgreSQL", "MongoDB", "Docker", "Git"],
            "projects": [
                {
                    "name": "CodeTurtle",
                    "description": "Full-stack code execution platform using React, Node.js, Docker, and PostgreSQL.",
                    "technologies": ["React", "Node.js", "Docker", "PostgreSQL"]
                }
            ],
            "experience": [
                {
                    "role": "Full Stack Developer",
                    "company": "Tech Corp",
                    "description": "Developed web applications with Next.js, Node.js, and REST APIs."
                }
            ]
        }

        # 1. Career Analysis
        analysis = generate_career_analysis("Full Stack Developer", profile)
        user_strengths = [s.lower() for s in analysis["user_strengths"]]
        true_gaps = [s.lower() for s in analysis["true_skill_gaps"]]

        # React, Node.js, PostgreSQL, Docker, Git MUST be recognized as demonstrated strengths
        self.assertIn("react", user_strengths)
        self.assertIn("node.js", user_strengths)
        self.assertIn("postgresql", user_strengths)
        self.assertIn("docker", user_strengths)
        self.assertIn("git", user_strengths)

        # HTML and CSS should NOT be critical gaps (they are low priority for experienced Full Stack devs)
        crit_gaps = analysis.get("prioritized_gaps", {}).get("critical", [])
        self.assertNotIn("HTML", crit_gaps)
        self.assertNotIn("CSS", crit_gaps)

        # 2. Personalized Plan Generation
        recs = generate_personalized_recommendations(profile, "Full Stack Developer", analysis["true_skill_gaps"], user_strengths=analysis["user_strengths"])
        
        # Verify brand new roadmap has all completed = False
        for step in recs["roadmap"]:
            self.assertFalse(step.get("completed", False))

        # Verify no beginner HTML courses
        for course in recs.get("courses", []):
            self.assertNotIn("html fundamentals", course.get("title", "").lower())
            self.assertNotIn("figma", course.get("title", "").lower())
            self.assertNotIn("pytorch", course.get("title", "").lower())

    def test_profile_b_ai_ml_engineer(self):
        """
        TEST B: Python + Pandas + ML + TensorFlow
        Target: AI/ML Engineer
        Expected: Deep Learning / PyTorch / MLOps / Model Deployment gaps.
        """
        profile = {
            "name": "Sarah ML",
            "skills": ["Python", "Pandas", "NumPy", "Scikit-learn", "Machine Learning", "TensorFlow", "Git"],
            "projects": [
                {
                    "name": "House Price Predictor",
                    "description": "Machine learning model predicting real estate prices with Pandas and Scikit-learn.",
                    "technologies": ["Python", "Pandas", "Scikit-learn"]
                }
            ]
        }

        analysis = generate_career_analysis("AI/ML Engineer", profile)
        user_strengths = [s.lower() for s in analysis["user_strengths"]]
        true_gaps = [s.lower() for s in analysis["true_skill_gaps"]]

        self.assertIn("python", user_strengths)
        self.assertIn("machine learning", user_strengths)
        self.assertIn("scikit-learn", user_strengths)

        # PyTorch or Deep Learning or Model Deployment should be in gaps
        self.assertTrue(
            "pytorch" in true_gaps or "deep learning" in true_gaps or "model deployment" in true_gaps
        )

        recs = generate_personalized_recommendations(profile, "AI/ML Engineer", analysis["true_skill_gaps"], user_strengths=analysis["user_strengths"])
        self.assertTrue(len(recs["roadmap"]) >= 3)
        for step in recs["roadmap"]:
            self.assertFalse(step.get("completed", False))

    def test_profile_c_data_analyst(self):
        """
        TEST C: SQL + Excel + Power BI
        Target: Data Analyst
        Expected: Analytics/SQL/BI plan with Statistics / Data Cleaning.
        """
        profile = {
            "name": "David Analyst",
            "skills": ["SQL", "Excel", "Power BI", "Data Analysis", "Reporting", "Dashboarding"],
            "projects": [
                {
                    "name": "Sales Performance Dashboard",
                    "description": "Executive dashboards created in Power BI with SQL data warehouse backend.",
                    "technologies": ["SQL", "Power BI", "Excel"]
                }
            ]
        }

        analysis = generate_career_analysis("Data Analyst", profile)
        user_strengths = [s.lower() for s in analysis["user_strengths"]]

        self.assertIn("sql", user_strengths)
        self.assertIn("excel", user_strengths)
        self.assertIn("power bi", user_strengths)

        recs = generate_personalized_recommendations(profile, "Data Analyst", analysis["true_skill_gaps"], user_strengths=analysis["user_strengths"])
        self.assertTrue(len(recs["roadmap"]) >= 3)
        # Should not recommend web development or mobile dev
        for proj in recs.get("recommendedProjects", []):
            self.assertNotIn("react", [t.lower() for t in proj.get("technologies", [])])

    def test_profile_d_react_node_targeting_data_scientist(self):
        """
        TEST D: React + Node
        Target: Data Scientist
        Expected: Large skill gap because target role differs substantially.
        """
        profile = {
            "name": "Emily Transition",
            "skills": ["React", "Node.js", "JavaScript", "HTML", "CSS"],
            "projects": [
                {
                    "name": "E-Commerce App",
                    "description": "Frontend and backend store built with React and Node.js.",
                    "technologies": ["React", "Node.js"]
                }
            ]
        }

        analysis = generate_career_analysis("Data Scientist", profile)
        true_gaps = analysis["true_skill_gaps"]

        # Data Science core skills should all be missing
        gaps_lower = [g.lower() for g in true_gaps]
        self.assertIn("python", gaps_lower)
        self.assertIn("statistics", gaps_lower)
        self.assertIn("machine learning", gaps_lower)

        # Dynamic duration should be larger because of large gaps (>= 6 weeks)
        evidence = build_evidence_profile(profile, "Data Scientist")
        prioritized = compute_prioritized_gaps(evidence, "Data Scientist")
        duration = calculate_dynamic_duration(prioritized)
        self.assertGreaterEqual(duration, 6)

    def test_newly_generated_roadmap_has_zero_completed(self):
        """Verify that newly generated roadmaps never have pre-completed milestones."""
        profile = {
            "skills": ["Python", "FastAPI"],
            "projects": []
        }
        analysis = generate_career_analysis("Backend Developer", profile)
        recs = generate_personalized_recommendations(profile, "Backend Developer", analysis["true_skill_gaps"], user_strengths=analysis["user_strengths"])
        
        completed_count = sum(1 for step in recs["roadmap"] if step.get("completed", False))
        self.assertEqual(completed_count, 0)

    def test_weighted_readiness_calculation_and_progression(self):
        """Verify deterministic weighted readiness scoring and progression upon gap completion."""
        from app.services.recommendation_engine import calculate_weighted_readiness
        
        # Initial demonstrated skills for Full Stack Developer
        initial_skills = ["React", "Node.js", "JavaScript", "TypeScript"]
        base_readiness = calculate_weighted_readiness("Full Stack Developer", initial_skills)
        self.assertGreaterEqual(base_readiness, 35)
        self.assertLessEqual(base_readiness, 55)

        # After completing high-priority gaps "SQL" & "Authentication"
        after_sql = calculate_weighted_readiness("Full Stack Developer", initial_skills, completed_skills=["SQL", "Authentication"])
        self.assertGreater(after_sql, base_readiness)

        # After completing all core roadmap milestones
        after_all = calculate_weighted_readiness("Full Stack Developer", initial_skills, completed_skills=[
            "SQL", "Authentication", "Docker", "Testing", "REST APIs", "Git", "System Design", "MongoDB", "PostgreSQL", "CI/CD", "Cloud Deployment"
        ])
        self.assertGreater(after_all, after_sql)
        self.assertGreaterEqual(after_all, 85)

    def test_task_based_milestone_breakdown_properties(self):
        """Verify that generated roadmap milestones include tasks, checkpoint, hours, and days."""
        profile = {
            "skills": ["Python", "Pandas"],
            "projects": []
        }
        analysis = generate_career_analysis("AI/ML Engineer", profile)
        recs = generate_personalized_recommendations(profile, "AI/ML Engineer", analysis["true_skill_gaps"], user_strengths=analysis["user_strengths"])
        
        self.assertGreater(len(recs["roadmap"]), 0)
        for milestone in recs["roadmap"]:
            self.assertIn("estimated_hours", milestone)
            self.assertIn("estimated_days", milestone)
            self.assertIn("tasks", milestone)
            self.assertIn("checkpoint", milestone)
            self.assertGreater(len(milestone["tasks"]), 0)
            self.assertTrue(isinstance(milestone["estimated_hours"], (int, float)))
            self.assertTrue(isinstance(milestone["estimated_days"], (int, float)))


if __name__ == "__main__":
    unittest.main()
