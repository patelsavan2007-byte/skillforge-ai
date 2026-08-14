"""
embedding_service.py
====================
Dedicated E5 Semantic Retrieval and Ranking Service for SkillForge AI.
Optimized for Low-Memory Deployment (Render Free 512MB RAM).

Model: intfloat/e5-base-v2 (lazy-loaded on demand when memory permits)
Fallback: Fast, deterministic, memory-safe catalog ranking (<1MB RAM)
"""

import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
from app.config import settings

logger = logging.getLogger("skillforge.embedding_service")

# Global singleton storage
_E5_MODEL = None
_COURSE_CATALOG: List[Dict[str, Any]] = []
_COURSE_EMBEDDINGS: Optional[np.ndarray] = None
_CACHED_FALLBACK_CATALOG: Optional[List[Dict[str, Any]]] = None
_IS_INITIALIZED = False
_INITIALIZATION_FAILED = False


def get_e5_model():
    """Load E5 lazily for query encoding if memory permits; never block startup."""
    global _E5_MODEL, _INITIALIZATION_FAILED
    if _E5_MODEL is not None:
        return _E5_MODEL
    if _INITIALIZATION_FAILED:
        return None

    # In low-memory mode or when heavy models are disabled, bypass E5 entirely
    if getattr(settings, "LOW_MEMORY_MODE", False) or not getattr(settings, "ENABLE_HEAVY_MODELS", True):
        logger.info("Low memory mode active: Skipping E5 model load to stay within 512MB RAM.")
        _INITIALIZATION_FAILED = True
        return None

    try:
        from sentence_transformers import SentenceTransformer
        logger.info("Initializing intfloat/e5-base-v2 for query encoding...")
        _E5_MODEL = SentenceTransformer("intfloat/e5-base-v2", local_files_only=True)
        return _E5_MODEL
    except (ImportError, MemoryError, OSError, Exception) as exc:
        logger.warning("E5 model unavailable or memory constrained (%s). Using deterministic catalog fallback.", exc)
        _INITIALIZATION_FAILED = True
        return None


def _get_course_catalog_path() -> Path:
    """Resolve path to course_catalog.json."""
    base_dir = Path(__file__).resolve().parent.parent
    return base_dir / "data" / "course_catalog.json"


def _construct_course_passage_text(course: Dict[str, Any]) -> str:
    """Construct semantic text representation for a course with 'passage: ' prefix."""
    title = course.get("title", "")
    desc = course.get("description", "")
    skills = course.get("skills", [])
    skills_str = ", ".join(skills) if isinstance(skills, list) else str(skills)
    platform = course.get("platform", "")
    category = course.get("category", "")

    content = f"{title}. {desc} Target Skills: {skills_str}. Platform: {platform}. Category: {category}."
    return f"passage: {content.strip()}"


def init_e5_service() -> bool:
    """Initialize the E5 embedding service if heavy models are enabled and memory permits."""
    global _E5_MODEL, _COURSE_CATALOG, _COURSE_EMBEDDINGS, _IS_INITIALIZED, _INITIALIZATION_FAILED

    if _IS_INITIALIZED:
        return True
    if _INITIALIZATION_FAILED:
        return False

    if getattr(settings, "LOW_MEMORY_MODE", False) or not getattr(settings, "ENABLE_HEAVY_MODELS", True):
        return False

    try:
        _E5_MODEL = get_e5_model()
        if _E5_MODEL is None:
            return False

        catalog_path = _get_course_catalog_path()
        if not catalog_path.exists():
            _INITIALIZATION_FAILED = True
            return False

        with open(catalog_path, "r", encoding="utf-8") as f:
            _COURSE_CATALOG = json.load(f)

        if not _COURSE_CATALOG:
            _INITIALIZATION_FAILED = True
            return False

        passages = [_construct_course_passage_text(c) for c in _COURSE_CATALOG]
        embeddings = _E5_MODEL.encode(passages, normalize_embeddings=True)
        _COURSE_EMBEDDINGS = np.array(embeddings, dtype=np.float32)

        _IS_INITIALIZED = True
        logger.info("E5 embedding service initialized successfully.")
        return True

    except (MemoryError, Exception) as e:
        logger.warning("Failed to initialize E5 model/embeddings (%s). Using catalog fallback.", e)
        _INITIALIZATION_FAILED = True
        return False


def _map_chroma_course(course: Dict[str, Any], skill_gaps: List[str]) -> Dict[str, Any]:
    raw_skills = course.get("skills", "[]")
    try:
        skills = json.loads(raw_skills) if isinstance(raw_skills, str) else raw_skills
    except (TypeError, json.JSONDecodeError):
        skills = []
    return {
        "title": course.get("title", ""),
        "provider": course.get("provider", ""),
        "url": course.get("url", ""),
        "duration": course.get("duration", ""),
        "difficulty": course.get("difficulty", "All Levels"),
        "skillAddressed": (skills or skill_gaps[:1] or ["General"])[0],
        "similarity_score": float(course.get("similarity_score", 0.0)),
        "description": course.get("description", ""),
        "skills": skills if isinstance(skills, list) else [],
    }


def _rerank_chroma_courses(courses: List[Dict[str, Any]], skill_gaps: List[str], top_k: int) -> List[Dict[str, Any]]:
    """Prefer results explicitly tagged/titled for deterministic gaps over broad prose matches."""
    gaps = {gap.casefold() for gap in skill_gaps}

    def relevance(course: Dict[str, Any]) -> tuple[int, int, float]:
        try:
            skills = json.loads(course.get("skills", "[]"))
        except (TypeError, json.JSONDecodeError):
            skills = []
        tagged_matches = sum(str(skill).casefold() in gaps for skill in skills)
        title = str(course.get("title", "")).casefold()
        title_matches = sum(gap in title for gap in gaps)
        return title_matches, tagged_matches, float(course.get("similarity_score", 0.0))

    return sorted(courses, key=relevance, reverse=True)[:top_k]


def compute_cosine_similarity(query_vec: np.ndarray, doc_vecs: np.ndarray) -> np.ndarray:
    """Compute cosine similarity between normalized query vector and document vectors."""
    if query_vec.ndim == 1:
        query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-9)
    else:
        query_norm = query_vec[0] / (np.linalg.norm(query_vec[0]) + 1e-9)

    doc_norms = doc_vecs / (np.linalg.norm(doc_vecs, axis=1, keepdims=True) + 1e-9)
    scores = np.dot(doc_norms, query_norm)
    return np.clip(scores, -1.0, 1.0)


def rank_courses_with_e5(
    true_skill_gaps: List[str],
    top_k: int = 5
) -> Optional[List[Dict[str, Any]]]:
    """
    Rank courses from catalog based on student true_skill_gaps.
    Seamlessly uses deterministic URL-safe catalog fallback in low-memory environments.
    """
    if not true_skill_gaps:
        logger.info("No true_skill_gaps provided for course ranking.")
        return None

    # Immediate fast path for low memory mode (Render Free 512MB RAM)
    if getattr(settings, "LOW_MEMORY_MODE", False) or not getattr(settings, "ENABLE_HEAVY_MODELS", True):
        return _fallback_catalog_courses(true_skill_gaps, top_k)

    try:
        model = get_e5_model()
        if model is None:
            return _fallback_catalog_courses(true_skill_gaps, top_k)

        skills_str = ", ".join(true_skill_gaps)
        query_text = f"query: {skills_str}"
        query_embedding = model.encode(query_text, normalize_embeddings=True)
        query_vec = np.array(query_embedding, dtype=np.float32)

        # Optional ChromaDB path
        try:
            from app.services.chromadb_service import query_courses
            chroma_courses = query_courses(query_vec.tolist(), top_k=max(25, top_k * 10))
            if chroma_courses:
                ranked_courses = _rerank_chroma_courses(chroma_courses, true_skill_gaps, top_k)
                return [_map_chroma_course(course, true_skill_gaps) for course in ranked_courses]
        except (ImportError, MemoryError, Exception) as ce:
            logger.debug("ChromaDB query skipped: %s", ce)

        if not init_e5_service():
            return _fallback_catalog_courses(true_skill_gaps, top_k)

        scores = compute_cosine_similarity(query_vec, _COURSE_EMBEDDINGS)
        ranked_indices = np.argsort(scores)[::-1]

        top_courses = []
        k = max(3, min(top_k, len(_COURSE_CATALOG)))

        for idx in ranked_indices[:k]:
            course = dict(_COURSE_CATALOG[idx])
            sim_score = float(scores[idx])
            top_courses.append({
                "title": course.get("title"),
                "provider": course.get("platform"),
                "url": course.get("url"),
                "duration": course.get("duration", "4 weeks"),
                "difficulty": course.get("difficulty", "Intermediate"),
                "skillAddressed": course.get("skillAddressed") or (true_skill_gaps[0] if true_skill_gaps else "General"),
                "similarity_score": round(sim_score, 2),
                "description": course.get("description", ""),
                "skills": course.get("skills", []),
            })

        return top_courses

    except (MemoryError, Exception) as e:
        logger.warning("E5 ranking encountered %s. Falling back to deterministic catalog matching.", e)
        return _fallback_catalog_courses(true_skill_gaps, top_k)


def _load_cached_catalog() -> List[Dict[str, Any]]:
    """Load and cache course_catalog.json in memory (<200KB) once."""
    global _CACHED_FALLBACK_CATALOG
    if _CACHED_FALLBACK_CATALOG is not None:
        return _CACHED_FALLBACK_CATALOG
    try:
        with open(_get_course_catalog_path(), "r", encoding="utf-8") as source:
            _CACHED_FALLBACK_CATALOG = json.load(source)
            return _CACHED_FALLBACK_CATALOG
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("Course catalog fallback unavailable: %s", exc)
        return []


def _fallback_catalog_courses(true_skill_gaps: List[str], top_k: int = 5) -> Optional[List[Dict[str, Any]]]:
    """
    Deterministic, zero-PyTorch, URL-safe fallback for Render Free 512MB RAM.
    Directly matches skill gaps against curated course catalog and returns ranked results with real URLs.
    """
    catalog = _load_cached_catalog()
    if not catalog:
        return None

    gap_keys = [skill.casefold().strip() for skill in true_skill_gaps if skill.strip()]
    ranked = []
    
    for course in catalog:
        c_title = str(course.get("title", "")).casefold()
        c_desc = str(course.get("description", "")).casefold()
        c_skills = [str(s).casefold() for s in course.get("skills", [])]
        c_category = str(course.get("category", "")).casefold()
        
        # Weighted scoring: exact skill tag match (3 pts), title match (2 pts), description/category (1 pt)
        score = 0
        matched_gaps = []
        for gap in gap_keys:
            if any(gap == s or gap in s for s in c_skills):
                score += 3
                matched_gaps.append(gap)
            elif gap in c_title:
                score += 2
                matched_gaps.append(gap)
            elif gap in c_desc or gap in c_category:
                score += 1
                matched_gaps.append(gap)
                
        if score > 0:
            ranked.append((score, course, matched_gaps))

    # Sort descending by score, then title
    ranked.sort(key=lambda item: (-item[0], str(item[1].get("title", ""))))

    # If no exact matches found, return top general core courses
    if not ranked and catalog:
        ranked = [(1, c, [gap_keys[0] if gap_keys else "General"]) for c in catalog[:top_k]]

    result = []
    target_count = max(3, min(top_k, len(ranked)))
    
    for score, course, matched_gaps in ranked[:target_count]:
        primary_skill = matched_gaps[0].title() if matched_gaps else (true_skill_gaps[0] if true_skill_gaps else "Core Engineering")
        result.append({
            "title": course.get("title", "Software Engineering Course"),
            "provider": course.get("platform") or course.get("provider", "Coursera"),
            "url": course.get("url", ""),
            "duration": course.get("duration", "4 weeks"),
            "difficulty": course.get("difficulty", "Intermediate"),
            "skillAddressed": primary_skill,
            "similarity_score": round(min(0.95, 0.70 + (score * 0.05)), 2),
            "description": course.get("description", ""),
            "skills": course.get("skills", [primary_skill]),
            "why_recommended": f"Targeted course to close skill gap in {primary_skill}."
        })

    return result or None
