"""Focused deterministic tests for Stage 5 progress tracking."""

import sys
import unittest
from datetime import datetime
from unittest.mock import patch

sys.path.insert(0, ".")

from app.services.progress_service import initialize_progress_from_career_analysis, toggle_roadmap_checkpoint


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = docs or []

    def find_one(self, query, sort=None):
        for doc in self.docs:
            if all(doc.get(key) == value for key, value in query.items()):
                return doc
        return None

    def find_one_and_update(self, query, update, upsert=False, return_document=True):
        doc = self.find_one(query)
        if doc is None and upsert:
            doc = {"_id": f"progress-{len(self.docs)}", **query}
            self.docs.append(doc)
        doc.update(update.get("$set", {}))
        return doc

    def update_one(self, query, update):
        doc = self.find_one(query)
        if doc:
            doc.update(update.get("$set", {}))


class TestProgressTracking(unittest.TestCase):
    def setUp(self):
        self.roadmap = [
            {"week": 1, "skills": ["Docker"], "completed": False},
            {"week": 2, "skills": ["Kubernetes"], "completed": False},
            {"week": 3, "skills": ["Docker"], "completed": False},
            {"week": 4, "skills": ["Kubernetes"], "completed": False},
        ]
        self.paths = FakeCollection([{"_id": "path-a", "userId": "user-a", "roadmap": self.roadmap, "createdAt": datetime.utcnow()}])
        self.progress = FakeCollection()
        self.patches = (
            patch("app.services.progress_service.get_learning_paths_collection", return_value=self.paths),
            patch("app.services.progress_service.get_progress_collection", return_value=self.progress),
        )
        for patcher in self.patches:
            patcher.start()

    def tearDown(self):
        for patcher in self.patches:
            patcher.stop()

    def test_01_initialization_uses_true_skill_gaps(self):
        result = initialize_progress_from_career_analysis("user-a", "DevOps", ["Docker", "Kubernetes"], self.roadmap, 20)
        self.assertEqual([item["skill"] for item in result["skillProgress"]], ["Docker", "Kubernetes"])
        self.assertEqual(result["skills"], {})

    def test_02_progress_starts_at_zero(self):
        result = initialize_progress_from_career_analysis("user-a", "DevOps", ["Docker"], self.roadmap)
        self.assertEqual((result["completedRoadmapItems"], result["roadmapProgress"]), (0, 0))

    def test_03_checking_checkpoint_recalculates_progress(self):
        initialize_progress_from_career_analysis("user-a", "DevOps", ["Docker", "Kubernetes"], self.roadmap)
        result = toggle_roadmap_checkpoint("user-a", 1, True)
        self.assertEqual((result["completedRoadmapItems"], result["roadmapProgress"]), (1, 25))

    def test_04_unchecking_checkpoint_restores_progress(self):
        initialize_progress_from_career_analysis("user-a", "DevOps", ["Docker"], self.roadmap)
        toggle_roadmap_checkpoint("user-a", 1, True)
        result = toggle_roadmap_checkpoint("user-a", 1, False)
        self.assertEqual((result["completedRoadmapItems"], result["roadmapProgress"]), (0, 0))

    def test_05_exact_percentage_is_integer_formula(self):
        ten = [{"week": index, "skills": [], "completed": index <= 4} for index in range(1, 11)]
        result = initialize_progress_from_career_analysis("user-a", "Role", [], ten)
        self.assertEqual(result["roadmapProgress"], 40)

    def test_06_user_isolation_prevents_other_user_mutation(self):
        initialize_progress_from_career_analysis("user-a", "DevOps", ["Docker"], self.roadmap)
        with self.assertRaises(ValueError):
            toggle_roadmap_checkpoint("user-b", 1, True)
        self.assertFalse(self.roadmap[0]["completed"])

    def test_07_reinitializing_replaces_items_without_defaults(self):
        initialize_progress_from_career_analysis("user-a", "DevOps", ["Docker"], self.roadmap)
        result = initialize_progress_from_career_analysis("user-a", "Frontend", ["React"], self.roadmap)
        self.assertEqual(result["skillGapItems"], ["React"])
        self.assertEqual(result["skillProgress"], [{"skill": "React", "status": "not_started", "progress": 0, "completed": False}])


if __name__ == "__main__":
    unittest.main(verbosity=2)
