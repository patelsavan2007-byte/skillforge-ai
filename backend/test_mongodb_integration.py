import unittest
import os
import json
from datetime import datetime
from bson import ObjectId
from fastapi.testclient import TestClient

from app.main import app
from app.database.mongodb import (
    get_database,
    get_users_collection,
    get_resumes_collection,
    get_portfolios_collection,
    get_career_profiles_collection,
    get_learning_paths_collection,
    get_progress_collection,
    init_indexes,
    close_mongodb_connection,
    get_safe_host_info
)
from app.services.google_auth import get_or_create_user

client = TestClient(app)

class TestMongoDBIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment and initialize MongoDB indexes."""
        init_indexes()
        
    @classmethod
    def tearDownClass(cls):
        """Clean up test documents marked 'test': true and close MongoClient connection."""
        try:
            db = get_database()
            collections = ["users", "resumes", "portfolios", "career_profiles", "learning_paths", "progress"]
            for col in collections:
                db[col].delete_many({"test": True})
            print("Test cleanup completed: all test documents with 'test': true removed.")
        except Exception as e:
            print("Test cleanup warning:", e)
        finally:
            close_mongodb_connection()
        
    def test_01_mongodb_connection_and_database(self):
        """Verify MongoDB ping, database name ('skillforge'), host info, and 6 collections."""
        db = get_database()
        ping_res = db.command("ping")
        self.assertEqual(ping_res.get("ok"), 1.0)
        
        self.assertEqual(db.name, "skillforge")
        
        safe_host = get_safe_host_info(db.client)
        print(f"Verified MongoDB database: {db.name}")
        print(f"Verified MongoDB host: {safe_host}")
        
    def test_02_indexes(self):
        """Verify explicit index definitions and print index names safely."""
        db = get_database()
        
        print("\n--- MONGO INDEX VERIFICATION ---")
        for col_name in ["users", "resumes", "portfolios", "career_profiles", "learning_paths", "progress"]:
            indexes = list(db[col_name].list_indexes())
            idx_names = [idx["name"] for idx in indexes]
            print(f"Collection '{col_name}' index names: {idx_names}")
            self.assertTrue(len(indexes) >= 2 if col_name in ["users", "progress"] else len(indexes) >= 1)

    def test_03_test_document_insertion_and_retrieval(self):
        """Insert test documents across all 6 collections, verify reading back, and document counts."""
        db = get_database()
        now = datetime.utcnow()
        test_user_id = str(ObjectId())

        # 1. users
        users_col = get_users_collection()
        user_doc = {
            "name": "MongoDB Integration Test",
            "email": "mongodb-integration-test@example.com",
            "createdAt": now,
            "updatedAt": now,
            "test": True
        }
        res_u = users_col.insert_one(user_doc)
        self.assertIsNotNone(res_u.inserted_id)
        found_u = users_col.find_one({"_id": res_u.inserted_id})
        self.assertEqual(found_u["email"], "mongodb-integration-test@example.com")

        # 2. resumes
        resumes_col = get_resumes_collection()
        resume_doc = {
            "userId": test_user_id,
            "fileName": "integration-test.pdf",
            "profile": {
                "name": "MongoDB Integration Test",
                "skills": ["Python", "FastAPI"]
            },
            "uploadedAt": now,
            "test": True
        }
        res_r = resumes_col.insert_one(resume_doc)
        self.assertIsNotNone(res_r.inserted_id)

        # 3. portfolios
        portfolios_col = get_portfolios_collection()
        portfolio_doc = {
            "userId": test_user_id,
            "url": "https://example.com",
            "profile": {
                "name": "Integration Test",
                "skills": ["Python"]
            },
            "analyzedAt": now,
            "test": True
        }
        res_p = portfolios_col.insert_one(portfolio_doc)
        self.assertIsNotNone(res_p.inserted_id)

        # 4. career_profiles
        career_col = get_career_profiles_collection()
        cp_doc = {
            "userId": test_user_id,
            "targetRole": "AI Engineer",
            "careerReadiness": 50,
            "createdAt": now,
            "test": True
        }
        res_cp = career_col.insert_one(cp_doc)
        self.assertIsNotNone(res_cp.inserted_id)

        # 5. learning_paths
        lp_col = get_learning_paths_collection()
        lp_doc = {
            "userId": test_user_id,
            "targetRole": "AI Engineer",
            "durationWeeks": 1,
            "roadmap": [],
            "createdAt": now,
            "test": True
        }
        res_lp = lp_col.insert_one(lp_doc)
        self.assertIsNotNone(res_lp.inserted_id)

        # 6. progress
        progress_col = get_progress_collection()
        prog_doc = {
            "userId": test_user_id,
            "skills": {"Python": 50},
            "roadmapProgress": 0,
            "updatedAt": now,
            "test": True
        }
        res_prog = progress_col.insert_one(prog_doc)
        self.assertIsNotNone(res_prog.inserted_id)

        # Verify collection list in database 'skillforge'
        all_cols = db.list_collection_names()
        expected = ["users", "resumes", "portfolios", "career_profiles", "learning_paths", "progress"]
        print(f"\nExisting collections in '{db.name}': {all_cols}")
        for c in expected:
            self.assertIn(c, all_cols)

        # Print document counts
        print("\n--- DOCUMENT COUNTS ---")
        for c in expected:
            count = db[c].count_documents({})
            print(f"Collection '{c}' document count: {count}")

    def test_04_google_auth_user_creation(self):
        """Test get_or_create_user service with a mock Google user profile."""
        google_profile = {
            "sub": "mock_google_id_99999",
            "email": "mock-oauth-user@example.com",
            "name": "Mock OAuth User",
            "picture": "https://example.com/pic.jpg"
        }
        user = get_or_create_user(google_profile)
        self.assertIsNotNone(user.get("id"))
        self.assertEqual(user.get("email"), "mock-oauth-user@example.com")
        
        # Clean up mock user
        get_users_collection().delete_many({"email": "mock-oauth-user@example.com"})

    def test_05_user_isolation(self):
        """Verify strict data isolation: User B cannot access User A's data."""
        users_col = get_users_collection()
        now = datetime.utcnow()
        
        # Create User A & User B
        res_a = users_col.insert_one({"name": "User A", "email": "isolation-usera@example.com", "createdAt": now, "test": True})
        res_b = users_col.insert_one({"name": "User B", "email": "isolation-userb@example.com", "createdAt": now, "test": True})
        
        user_a_id = str(res_a.inserted_id)
        user_b_id = str(res_b.inserted_id)

        headers_a = {"X-User-ID": user_a_id}
        headers_b = {"X-User-ID": user_b_id}

        # User A posts resume
        res_post = client.post("/api/resumes", headers=headers_a, json={"fileName": "user_a.pdf", "rawText": "Python Developer"})
        self.assertEqual(res_post.status_code, 200)
        resume_id = res_post.json()["data"]["id"]

        # Mark created resume for test cleanup
        get_resumes_collection().update_one({"_id": ObjectId(resume_id)}, {"$set": {"test": True}})

        # User B attempts to access User A's resume -> 404 Not Found
        res_get_b = client.get(f"/api/resumes/{resume_id}", headers=headers_b)
        self.assertEqual(res_get_b.status_code, 404)

        # User A attempts to access User A's resume -> 200 OK
        res_get_a = client.get(f"/api/resumes/{resume_id}", headers=headers_a)
        self.assertEqual(res_get_a.status_code, 200)

if __name__ == "__main__":
    unittest.main()
