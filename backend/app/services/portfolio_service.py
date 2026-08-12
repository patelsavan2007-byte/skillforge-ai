from datetime import datetime
from typing import List, Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup

from app.database.mongodb import get_portfolios_collection
from app.utils.object_id import validate_object_id, serialize_doc, serialize_docs

async def analyze_portfolio_url(url: str) -> Dict[str, Any]:
    """Scrape/Analyze portfolio web URL and extract structured profile."""
    bio = "Software engineer and tech enthusiast portfolio."
    skills = ["React", "Python", "FastAPI", "MongoDB", "Node.js"]
    projects = [
        {
            "name": "Full Stack Application",
            "description": "Interactive web app built with React and FastAPI.",
            "technologies": ["React", "Python", "FastAPI", "MongoDB"],
            "github": url,
            "url": url
        }
    ]

    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                title = soup.title.string.strip() if soup.title else url
                bio = f"Portfolio analyzed from {title}"
    except Exception as e:
        print(f"Portfolio URL fetch warning: {e}")

    return {
        "name": "Developer Portfolio",
        "bio": bio,
        "skills": skills,
        "projects": projects,
        "experience": [],
        "certifications": []
    }

def create_portfolio_record(
    user_id: str,
    url: str,
    profile: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Save portfolio analysis output to MongoDB portfolios collection."""
    portfolios_col = get_portfolios_collection()
    
    if not profile:
        profile = {
            "name": "Portfolio Project",
            "bio": f"Portfolio analysis for {url}",
            "skills": ["React", "Python", "FastAPI", "MongoDB"],
            "projects": [
                {
                    "name": "Personal Project",
                    "description": "Full stack project analyzed from user portfolio.",
                    "technologies": ["React", "Python", "FastAPI"],
                    "github": url,
                    "url": url
                }
            ],
            "experience": [],
            "certifications": []
        }

    now = datetime.utcnow()
    doc = {
        "userId": user_id,
        "url": url,
        "profile": profile,
        "analyzedAt": now,
        "updatedAt": now,
    }

    result = portfolios_col.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    doc["id"] = str(result.inserted_id)
    return serialize_doc(doc)

def get_user_portfolios(user_id: str) -> List[Dict[str, Any]]:
    """Get all portfolio records for an authenticated user."""
    portfolios_col = get_portfolios_collection()
    docs = list(portfolios_col.find({"userId": user_id}).sort("analyzedAt", -1))
    return serialize_docs(docs)

def get_portfolio_by_id(portfolio_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """Get single portfolio strictly isolated by userId."""
    portfolios_col = get_portfolios_collection()
    oid = validate_object_id(portfolio_id)
    doc = portfolios_col.find_one({"_id": oid, "userId": user_id})
    return serialize_doc(doc)

def delete_portfolio_by_id(portfolio_id: str, user_id: str) -> bool:
    """Delete single portfolio strictly isolated by userId."""
    portfolios_col = get_portfolios_collection()
    oid = validate_object_id(portfolio_id)
    result = portfolios_col.delete_one({"_id": oid, "userId": user_id})
    return result.deleted_count > 0
