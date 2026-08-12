from datetime import datetime
from typing import List, Dict, Any, Optional

from app.database.mongodb import get_learning_paths_collection
from app.services.career_service import get_user_career_profiles
from app.utils.object_id import validate_object_id, serialize_doc, serialize_docs

def generate_learning_roadmap(target_role: str = "AI Engineer", duration_weeks: int = 8) -> List[Dict[str, Any]]:
    """Generate week-by-week Gemini learning roadmap."""
    weeks = [
        {
            "week": 1,
            "title": "Python & Advanced Data Structures",
            "skills": ["OOP", "Generators", "Asyncio", "Testing"],
            "courses": [
                {
                    "title": "Complete Python Developer",
                    "provider": "Coursera / Udemy",
                    "url": "https://coursera.org",
                    "duration": "10 hours",
                    "difficulty": "Intermediate"
                }
            ],
            "project": {
                "title": "High-Performance Data Pipeline",
                "description": "Build an asynchronous data extraction pipeline.",
                "skills": ["Python", "Asyncio"]
            },
            "completed": True
        },
        {
            "week": 2,
            "title": "Machine Learning & Model Evaluation",
            "skills": ["Regression", "Classification", "Cross Validation"],
            "courses": [
                {
                    "title": "Machine Learning Specialization",
                    "provider": "Coursera · DeepLearning.AI",
                    "url": "https://coursera.org",
                    "duration": "15 hours",
                    "difficulty": "Intermediate"
                }
            ],
            "project": {
                "title": "Customer Churn Predictor",
                "description": "Train and evaluate a gradient boosted decision tree model.",
                "skills": ["Python", "Scikit-learn", "Pandas"]
            },
            "completed": False
        },
        {
            "week": 3,
            "title": "Deep Learning & Neural Networks",
            "skills": ["CNN", "PyTorch", "Transfer Learning"],
            "courses": [
                {
                    "title": "Deep Learning Specialization",
                    "provider": "Coursera · DeepLearning.AI",
                    "url": "https://coursera.org",
                    "duration": "20 hours",
                    "difficulty": "Advanced"
                }
            ],
            "project": {
                "title": "Image Classifier with PyTorch",
                "description": "Fine-tune a ResNet model for custom image classification.",
                "skills": ["PyTorch", "Computer Vision"]
            },
            "completed": False
        },
        {
            "week": 4,
            "title": "SQL Data Warehousing",
            "skills": ["Window Functions", "Joins", "Indexing"],
            "courses": [
                {
                    "title": "SQL for Data Science",
                    "provider": "Coursera · UC Davis",
                    "url": "https://coursera.org",
                    "duration": "8 hours",
                    "difficulty": "Intermediate"
                }
            ],
            "project": {
                "title": "Analytics Data Warehouse",
                "description": "Design relational tables and optimize analytical SQL queries.",
                "skills": ["SQL", "Data Modeling"]
            },
            "completed": False
        },
        {
            "week": 5,
            "title": "FastAPI & REST Service Architecture",
            "skills": ["FastAPI", "Pydantic", "Async Endpoints"],
            "courses": [
                {
                    "title": "FastAPI Microservices",
                    "provider": "Udemy",
                    "url": "https://udemy.com",
                    "duration": "12 hours",
                    "difficulty": "Intermediate"
                }
            ],
            "project": {
                "title": "ML Model Inference Server",
                "description": "Serve PyTorch model predictions via scalable REST APIs.",
                "skills": ["FastAPI", "Python", "REST"]
            },
            "completed": False
        },
        {
            "week": 6,
            "title": "Containerization & Docker",
            "skills": ["Docker", "Docker Compose", "Multi-stage builds"],
            "courses": [
                {
                    "title": "Docker & Kubernetes Mastery",
                    "provider": "Udemy",
                    "url": "https://udemy.com",
                    "duration": "14 hours",
                    "difficulty": "Intermediate"
                }
            ],
            "project": {
                "title": "Dockerized ML API",
                "description": "Package model server into production Docker image.",
                "skills": ["Docker", "FastAPI"]
            },
            "completed": False
        },
        {
            "week": 7,
            "title": "MLOps & CI/CD Pipelines",
            "skills": ["GitHub Actions", "Model Registry", "Monitoring"],
            "courses": [
                {
                    "title": "MLOps Specialization",
                    "provider": "Coursera · DeepLearning.AI",
                    "url": "https://coursera.org",
                    "duration": "16 hours",
                    "difficulty": "Advanced"
                }
            ],
            "project": {
                "title": "Automated Model Deployment Pipeline",
                "description": "Setup CI/CD pipeline to test and deploy ML API.",
                "skills": ["MLOps", "CI/CD", "Docker"]
            },
            "completed": False
        },
        {
            "week": 8,
            "title": "Capstone Industry Project",
            "skills": ["System Design", "Documentation", "Deployment"],
            "courses": [
                {
                    "title": "Machine Learning Engineering Capstone",
                    "provider": "SkillForge AI",
                    "url": "https://skillforge.ai",
                    "duration": "25 hours",
                    "difficulty": "Advanced"
                }
            ],
            "project": {
                "title": "End-to-End AI Application",
                "description": "Deploy a complete web AI system with full production capabilities.",
                "skills": ["Python", "React", "FastAPI", "MongoDB", "Docker"]
            },
            "completed": False
        }
    ]
    return weeks[:duration_weeks]

def create_learning_path_record(
    user_id: str,
    target_role: str = "AI Engineer",
    duration_weeks: int = 8,
    custom_roadmap: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Generate or persist Gemini learning roadmap into MongoDB learning_paths collection."""
    paths_col = get_learning_paths_collection()
    
    if custom_roadmap:
        roadmap = custom_roadmap
    else:
        roadmap = generate_learning_roadmap(target_role, duration_weeks)

    now = datetime.utcnow()
    doc = {
        "userId": user_id,
        "targetRole": target_role,
        "durationWeeks": len(roadmap) if len(roadmap) > 0 else duration_weeks,
        "roadmap": roadmap,
        "createdAt": now,
        "updatedAt": now,
    }

    result = paths_col.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    doc["id"] = str(result.inserted_id)
    return serialize_doc(doc)

def get_user_learning_paths(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve user learning paths sorted by creation date."""
    paths_col = get_learning_paths_collection()
    docs = list(paths_col.find({"userId": user_id}).sort("createdAt", -1))
    return serialize_docs(docs)

def get_learning_path_by_id(path_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve single learning path strictly isolated by userId."""
    paths_col = get_learning_paths_collection()
    oid = validate_object_id(path_id)
    doc = paths_col.find_one({"_id": oid, "userId": user_id})
    return serialize_doc(doc)

def update_learning_path_by_id(
    path_id: str,
    user_id: str,
    roadmap: Optional[List[Dict[str, Any]]] = None,
    duration_weeks: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """Update/patch learning roadmap strictly isolated by userId."""
    paths_col = get_learning_paths_collection()
    oid = validate_object_id(path_id)
    
    update_data: Dict[str, Any] = {"updatedAt": datetime.utcnow()}
    if roadmap is not None:
        update_data["roadmap"] = roadmap
    if duration_weeks is not None:
        update_data["durationWeeks"] = duration_weeks

    result = paths_col.find_one_and_update(
        {"_id": oid, "userId": user_id},
        {"$set": update_data},
        return_document=True
    )
    return serialize_doc(result)
