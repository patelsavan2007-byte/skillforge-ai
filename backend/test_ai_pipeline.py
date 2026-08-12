import unittest
import uuid
import httpx

BASE_URL = "http://localhost:8000"

class TestAIPipeline(unittest.TestCase):
    def setUp(self):
        self.client = httpx.Client(base_url=BASE_URL, timeout=15.0)
        # Unique user per test so the analyze endpoint's "latest resume" fallback
        # never leaks state between test cases (idempotent / repeatable runs).
        self.user_id = f"test_user_pipeline_{uuid.uuid4().hex[:12]}"

    def tearDown(self):
        self.client.close()

    def test_01_health_endpoint(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "ok")

    def test_02_google_oauth_login_redirect(self):
        resp = self.client.get("/api/auth/google/login", follow_redirects=False)
        self.assertEqual(resp.status_code, 307)
        self.assertIn("accounts.google.com", resp.headers["location"])
        self.assertIn("client_id=", resp.headers["location"])

    def test_03_neither_resume_nor_portfolio_error(self):
        headers = {"X-User-ID": self.user_id}
        resp = self.client.post(
            "/api/career-profiles/analyze",
            data={"target_role": "AI/ML Engineer"},
            headers=headers
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("At least one profile source", resp.json()["detail"])

    def test_04_portfolio_only_analysis(self):
        headers = {"X-User-ID": self.user_id}
        resp = self.client.post(
            "/api/career-profiles/analyze",
            data={
                "portfolio_url": "https://github.com/torvalds",
                "target_role": "Software Engineer"
            },
            headers=headers
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        unified = data["data"]["unifiedProfile"]
        self.assertTrue(unified["source"]["portfolio"])
        self.assertFalse(unified["source"]["resume"])
        self.assertIn("skills", unified)
        self.assertIn("careerProfile", data["data"])
        self.assertIn("learningPath", data["data"])

    def test_05_resume_only_analysis(self):
        headers = {"X-User-ID": self.user_id}
        resume_content = (
            "Alex Mercer\nalex@example.com\n"
            "Education: BS Computer Science, Stanford University, CGPA: 3.9\n"
            "Experience: Software Engineer Intern at Google (Python, FastAPI, Docker)\n"
            "Skills: Python, React, PyTorch, SQL, Git\n"
            "Projects: AI Career Assistant (Python, React, FastAPI)"
        ).encode("utf-8")

        files = {"file": ("resume.txt", resume_content, "text/plain")}
        data = {"target_role": "AI/ML Engineer"}

        resp = self.client.post(
            "/api/career-profiles/analyze",
            files=files,
            data=data,
            headers=headers
        )
        self.assertEqual(resp.status_code, 200)
        res = resp.json()
        self.assertTrue(res["success"])
        unified = res["data"]["unifiedProfile"]
        self.assertTrue(unified["source"]["resume"])
        self.assertIn("skills", unified)

    def test_06_merged_resume_and_portfolio(self):
        headers = {"X-User-ID": self.user_id}
        resume_content = (
            "Jordan Lee\njordan@example.com\n"
            "Skills: Python, FastAPI, PyTorch, MongoDB\n"
            "Projects: Resume Parser (Python, FastAPI)"
        ).encode("utf-8")

        files = {"file": ("resume.txt", resume_content, "text/plain")}
        data = {
            "portfolio_url": "https://github.com/pallets/flask",
            "target_role": "Full Stack Developer"
        }

        resp = self.client.post(
            "/api/career-profiles/analyze",
            files=files,
            data=data,
            headers=headers
        )
        self.assertEqual(resp.status_code, 200)
        res = resp.json()
        self.assertTrue(res["success"])
        unified = res["data"]["unifiedProfile"]
        self.assertTrue(unified["source"]["resume"])
        self.assertTrue(unified["source"]["portfolio"])
        # Verify deduplicated skills list exists
        self.assertIsInstance(unified["skills"], list)
        self.assertIn("careerProfile", res["data"])
        self.assertIn("learningPath", res["data"])

if __name__ == "__main__":
    unittest.main()
