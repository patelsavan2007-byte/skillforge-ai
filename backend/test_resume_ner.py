import os
import sys
import logging

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.mongodb import connect_to_mongodb, close_mongodb_connection, get_resumes_collection
from app.services.resume_ner import get_ner_service
from app.services.resume_parser import parse_file_to_text
from app.services.resume_extractor import build_structured_resume, extract_academic_scores, extract_projects_from_text
from app.services.resume_service import (
    create_resume_record,
    get_latest_user_resume,
    update_latest_resume,
    delete_resume_by_id
)

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

EXPERIENCE
Software Engineering Intern
ABC Technologies
May 2025 - July 2025

PROJECTS
SkillForge AI
AI-powered career mentor application using React, FastAPI, MongoDB and machine learning.

CERTIFICATIONS
AWS Certified Cloud Practitioner

LANGUAGES
English, Hindi, Gujarati
"""

def run_tests():
    print("==================================================")
    print(" RUNNING SKILLFORGE RESUME NER & PIPELINE TESTS")
    print("==================================================")

    # 1. Test Model Loading & Entity Extraction
    print("\n--- 1. Testing Hugging Face oksomu/resume-ner Loading ---")
    ner_service = get_ner_service()
    print("NER Service initialized successfully.")

    print("\n--- 2. Testing Entity Extraction on Sample Resume ---")
    entities = ner_service.extract_entities(TEST_RESUME_TEXT)
    print(f"Extracted {len(entities)} raw NER entities:")
    for e in entities:
        print(f"  [{e['label']}] {e['text']} (score: {e['score']})")

    # 3. Test SGPA / CGPA Extraction
    print("\n--- 3. Testing Academic Score Parsing ---")
    scores1 = extract_academic_scores("CGPA: 8.7  SGPA: 8.9")
    print("Parsed scores (CGPA: 8.7 SGPA: 8.9):", scores1)
    assert scores1["cgpa"] == 8.7, f"Expected CGPA 8.7, got {scores1['cgpa']}"
    assert scores1["sgpa"] == 8.9, f"Expected SGPA 8.9, got {scores1['sgpa']}"

    # 4. Test Structured Resume Extraction
    print("\n--- 4. Testing Structured Resume Building ---")
    structured = build_structured_resume(TEST_RESUME_TEXT, entities)
    print("Personal Info:", structured["personal"])
    print("Education:", structured["education"])
    print("Skills:", structured["skills"])
    print("Experience:", structured["experience"])
    print("Projects:", structured["projects"])
    print("Certifications:", structured["certifications"])
    print("Languages:", structured["languages"])

    assert structured["personal"]["name"], "Personal name should not be empty"
    assert "Python" in structured["skills"] or len(structured["skills"]) > 0, "Skills should contain parsed items"

    # 5. Test Long Resume Chunking (>512 tokens)
    print("\n--- 5. Testing Long Resume Chunking (>512 Tokens) ---")
    long_resume_text = (TEST_RESUME_TEXT + "\n\n") * 10
    chunks = ner_service.chunk_text(long_resume_text)
    print(f"Long text divided into {len(chunks)} chunks.")
    assert len(chunks) > 1, "Long resume should be split into multiple chunks"
    long_entities = ner_service.extract_entities(long_resume_text)
    print(f"Extracted {len(long_entities)} entities across chunks without context error.")

    # 6. Test MongoDB Database Operations
    print("\n--- 6. Testing MongoDB Atlas Integration ---")
    connect_to_mongodb()
    test_user_id = "test_user_ner_verification_123"

    # Clean up previous test records if any
    resumes_col = get_resumes_collection()
    resumes_col.delete_many({"userId": test_user_id})

    # Create record
    doc = create_resume_record(
        user_id=test_user_id,
        file_name="John_Smith_Resume.pdf",
        raw_text=TEST_RESUME_TEXT
    )
    print("Inserted resume document ID:", doc["id"])
    assert doc["userId"] == test_user_id, "User ID mismatch"

    # Retrieve record
    retrieved = get_latest_user_resume(test_user_id)
    assert retrieved is not None, "Failed to retrieve resume from MongoDB"
    print("Retrieved resume name:", retrieved["profile"]["personal"]["name"])

    # Update record
    updated_profile = retrieved["profile"]
    updated_profile["skills"].append("PyTorch")
    updated = update_latest_resume(test_user_id, updated_profile)
    assert updated is not None, "Failed to update resume profile"
    assert "PyTorch" in updated["profile"]["skills"], "Updated skill not found"
    print("Updated resume skills count:", len(updated["profile"]["skills"]))

    # Delete record
    deleted = delete_resume_by_id(retrieved["id"], test_user_id)
    assert deleted, "Failed to delete test resume"
    print("Deleted test resume successfully.")

    close_mongodb_connection()
    print("\n==================================================")
    print(" ALL VERIFICATION TESTS PASSED SUCCESSFULLY! ")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
