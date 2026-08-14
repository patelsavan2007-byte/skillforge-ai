"""Offline, idempotent ingestion of verified courses into Stage 3 ChromaDB."""

import csv
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.services.chromadb_service import get_course_collection, get_collection_stats
from app.services.embedding_service import _construct_course_passage_text, get_e5_model
from app.services.career_service import REQUIRED_SKILLS_BY_ROLE

logger = logging.getLogger("skillforge.ingest_courses")
BATCH_SIZE = 64


def _skill_catalog() -> List[str]:
    return list(dict.fromkeys(skill for values in REQUIRED_SKILLS_BY_ROLE.values() for skill in values))


def _tag_course(title: str, description: str) -> tuple[List[str], str]:
    text = f"{title} {description}".casefold()
    skills = [skill for skill in _skill_catalog() if re.search(rf"(?<!\w){re.escape(skill.casefold())}(?!\w)", text)]
    role_scores = {
        role: sum(skill in required for skill in skills)
        for role, required in REQUIRED_SKILLS_BY_ROLE.items()
    }
    category = max(role_scores, key=role_scores.get) if skills and max(role_scores.values()) else "General"
    return skills, category


def _difficulty(text: str) -> str:
    lower = text.casefold()
    if any(word in lower for word in ("advanced", "professional", "expert", "specialization")):
        return "Advanced"
    if any(word in lower for word in ("beginner", "introduction", "fundamentals", "from scratch")):
        return "Beginner"
    return "Intermediate" if lower else "All Levels"


def _duration(hours: str) -> str:
    try:
        value = float(hours)
    except (TypeError, ValueError):
        return ""
    return f"{int(value)} hours" if value < 40 else f"{max(1, round(value / 20))} weeks"


def _records() -> Iterable[Dict[str, Any]]:
    with (PROJECT_DIR / "all_courses.csv").open(encoding="utf-8", newline="") as source:
        for row in csv.DictReader(source):
            title = row["course_name"].strip()
            description = (row.get("description") or "").strip() or title
            url = (row.get("url") or "").strip()
            if not title or not re.match(r"^https://", url, re.I):
                continue
            skills, category = _tag_course(title, description)
            yield {
                "id": f"kaggle_{row['id']}",
                "document": _construct_course_passage_text({"title": title, "description": description, "skills": skills, "platform": row["provider"], "category": category}),
                "metadata": {"raw_id": str(row["id"]), "title": title, "provider": row["provider"].strip(), "description": description, "url": url, "pricing": row.get("pricing", ""), "duration": _duration(row.get("duration_in_hours", "")), "difficulty": _difficulty(f"{title} {description}"), "skills": json.dumps(skills), "category": category},
            }


def main() -> int:
    collection = get_course_collection(create=True)
    model = get_e5_model()
    if collection is None or model is None:
        print("Ingestion aborted: ChromaDB or intfloat/e5-base-v2 is unavailable.")
        return 1
    records = list(_records())
    for offset in range(0, len(records), BATCH_SIZE):
        batch = records[offset:offset + BATCH_SIZE]
        embeddings = model.encode([item["document"] for item in batch], normalize_embeddings=True).tolist()
        collection.upsert(ids=[item["id"] for item in batch], documents=[item["document"] for item in batch], metadatas=[item["metadata"] for item in batch], embeddings=embeddings)
        print(f"Indexed {min(offset + len(batch), len(records))}/{len(records)} courses")
    print(json.dumps(get_collection_stats(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
