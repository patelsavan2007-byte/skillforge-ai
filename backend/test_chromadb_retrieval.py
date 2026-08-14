"""Stage 3 ChromaDB persistence tests; no model download is required."""

import os
import sys
import unittest
from unittest.mock import Mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.services import chromadb_service


class TestChromaCourseRetrieval(unittest.TestCase):
    def setUp(self):
        self.original_dir = settings.CHROMADB_DIR
        self.original_name = settings.CHROMA_COLLECTION_NAME
        settings.CHROMA_COLLECTION_NAME = "test_skillforge_courses"
        self.collection = Mock()
        self.collection.count.return_value = 1
        self.collection.query.return_value = {
            "metadatas": [[{"title": "Python Course", "provider": "Example", "url": "https://example.test/course", "skills": '["Python"]'}]],
            "distances": [[0.0]],
        }
        self.client = Mock()
        self.client.get_or_create_collection.return_value = self.collection
        self.client.get_collection.return_value = self.collection
        chromadb_service._CLIENT = self.client

    def tearDown(self):
        chromadb_service._CLIENT = None
        settings.CHROMADB_DIR = self.original_dir
        settings.CHROMA_COLLECTION_NAME = self.original_name

    def test_persistent_collection_uses_cosine_and_upsert_is_idempotent(self):
        collection = chromadb_service.get_course_collection(create=True)
        collection.upsert(
            ids=["kaggle_1"],
            documents=["passage: Python course updated"],
            embeddings=[[1.0, 0.0]],
            metadatas=[{"title": "Python Course", "provider": "Example", "url": "https://example.test/course", "skills": '["Python"]'}],
        )
        self.assertEqual(collection.count(), 1)
        matches = chromadb_service.query_courses([1.0, 0.0], top_k=5)
        self.assertEqual(matches[0]["title"], "Python Course")
        self.assertAlmostEqual(matches[0]["similarity_score"], 1.0, places=4)
        self.assertEqual(chromadb_service.get_collection_stats()["count"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
