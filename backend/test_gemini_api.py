"""
test_gemini_api.py
==================
Backend test script to verify Gemini 2.5 Flash API connectivity and response parsing.

IMPORTANT: NEVER print or log the actual GEMINI_API_KEY secret.
"""

import sys
import unittest

sys.path.insert(0, ".")

from app.config import settings
from app.services.gemini_service import GEMINI_MODEL_CANDIDATES, _get_genai_client, generate_gemini_json


class TestGeminiAPI(unittest.TestCase):
    def test_00_only_supported_model_is_configured(self):
        self.assertEqual(GEMINI_MODEL_CANDIDATES, ["gemini-2.5-flash"])

    def test_01_gemini_api_key_loaded(self):
        """Verify GEMINI_API_KEY is present in environment/config."""
        self.assertTrue(bool(settings.GEMINI_API_KEY), "GEMINI_API_KEY should be set in backend/.env")
        print("GEMINI_API_KEY loaded: YES")

    def test_02_gemini_client_initialization(self):
        """Verify Google GenAI client initializes successfully."""
        client = _get_genai_client()
        self.assertIsNotNone(client, "Google GenAI client should initialize")
        print("Gemini client: OK")

    def test_03_gemini_2_5_flash_model_response(self):
        """Verify gemini-2.5-flash model responds with valid structured JSON."""
        print("Model: gemini-2.5-flash")
        prompt = "Provide a sample JSON response with key 'status' set to 'ok' and key 'message' set to 'Gemini 2.5 Flash operational'."
        result = generate_gemini_json(prompt)
        
        self.assertIsNotNone(result, "gemini-2.5-flash API call should return parsed JSON")
        self.assertIsInstance(result, dict, "Result should be a dictionary")
        self.assertIn("status", result)
        print("Gemini API: OK")


if __name__ == "__main__":
    unittest.main(verbosity=2)
