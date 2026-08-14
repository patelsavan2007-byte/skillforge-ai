import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup

from app.database.mongodb import get_portfolios_collection
from app.utils.object_id import validate_object_id, serialize_doc, serialize_docs

logger = logging.getLogger("skillforge.portfolio")

COMMON_SKILL_KEYWORDS = [
    "Python", "JavaScript", "TypeScript", "React", "Next.js", "Vue", "Angular",
    "Node.js", "Express", "FastAPI", "Django", "Flask", "PyTorch", "TensorFlow",
    "Keras", "Scikit-learn", "Pandas", "NumPy", "SQL", "PostgreSQL", "MongoDB",
    "Docker", "Kubernetes", "AWS", "GCP", "Azure", "Git", "GitHub", "CI/CD",
    "GraphQL", "REST API", "Tailwind CSS", "Linux", "C++", "Java", "Go", "Rust"
]

async def analyze_portfolio_url(url: str) -> Dict[str, Any]:
    """
    Fetch and analyze public portfolio/GitHub URL.
    Parses visible text and metadata with BeautifulSoup and uses deterministic heuristics for structured profile extraction.
    Handles timeouts, HTTP errors, non-HTML responses, and invalid URLs gracefully.
    """
    cleaned_url = url.strip()
    if not cleaned_url.startswith(("http://", "https://")):
        cleaned_url = "https://" + cleaned_url

    page_text = ""
    title = ""
    headings = []

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SkillForgeAI/2.0 PortfolioAnalyzer"
        }
        async with httpx.AsyncClient(timeout=6.0, follow_redirects=True, headers=headers) as client:
            resp = await client.get(cleaned_url)
            if resp.status_code == 200:
                content_type = resp.headers.get("content-type", "")
                if "html" in content_type.lower() or "text" in content_type.lower():
                    soup = BeautifulSoup(resp.text, "html.parser")
                    
                    # Remove non-content tags
                    for element in soup(["script", "style", "nav", "footer", "noscript", "svg"]):
                        element.decompose()

                    title = soup.title.string.strip() if soup.title and soup.title.string else cleaned_url
                    
                    # Extract headings & visible paragraphs
                    headings = [h.get_text().strip() for h in soup.find_all(["h1", "h2", "h3"]) if h.get_text().strip()]
                    paragraphs = [p.get_text().strip() for p in soup.find_all(["p", "li"]) if len(p.get_text().strip()) > 10]
                    
                    page_text = f"Title: {title}\nHeadings: {' | '.join(headings[:10])}\nContent:\n" + "\n".join(paragraphs[:30])
                else:
                    page_text = f"Non-HTML content analyzed from {cleaned_url}"
            else:
                page_text = f"URL returned HTTP {resp.status_code}"
    except httpx.TimeoutException:
        logger.warning(f"Portfolio URL timeout for {cleaned_url}")
        page_text = f"Portfolio request timed out for {cleaned_url}"
    except Exception as e:
        logger.warning(f"Portfolio URL fetch error for {cleaned_url}: {e}")
        page_text = f"Analysis of portfolio URL: {cleaned_url}"

    # PRIMARY: Deterministic heuristic extraction from scraped content
    detected_skills = [skill for skill in COMMON_SKILL_KEYWORDS if skill.lower() in page_text.lower()]
    # An empty scrape is not evidence of skills. Do not synthesize a profile.

    extracted_projects = []
    for idx, heading in enumerate(headings[:4]):
        if any(kw in heading.lower() for kw in ["project", "app", "system", "portfolio", "forge", "bot", "model", "tool"]):
            extracted_projects.append({
                "name": heading,
                "description": f"Featured project from candidate portfolio ({cleaned_url}).",
                "technologies": detected_skills[:3],
                "github": cleaned_url,
                "url": cleaned_url
            })

    return {
        "name": title if title and len(title) < 40 else "",
        "bio": f"Portfolio analyzed from {cleaned_url}." if page_text else "",
        "skills": detected_skills,
        "projects": extracted_projects,
        "technologies": detected_skills,
        "experience": [],
        "education": [],
        "certifications": []
    }

def create_portfolio_record(
    user_id: str,
    url: str,
    profile: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Save portfolio analysis output to MongoDB portfolios collection."""
    portfolios_col = get_portfolios_collection()
    now = datetime.utcnow()
    doc = {
        "userId": user_id,
        "url": url,
        "profile": profile or {},
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
