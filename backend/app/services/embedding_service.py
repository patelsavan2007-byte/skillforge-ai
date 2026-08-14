"""
embedding_service.py
====================
Dedicated E5 Semantic Retrieval and Ranking Service for SkillForge AI.

Model: intfloat/e5-base-v2

Architecture:
    true_skill_gaps (from deterministic engine)
            ↓
    "query: {skill_gaps}"
            ↓
    E5 768-d query embedding
            ↓
    Cosine similarity vs precomputed cached "passage: {course_text}" embeddings
            ↓
    Top 3–5 semantically ranked courses with real URLs preserved.
"""

import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
from app.services.chromadb_service import query_courses

logger = logging.getLogger("skillforge.embedding_service")

# Global singleton storage
_E5_MODEL = None
_COURSE_CATALOG: List[Dict[str, Any]] = []
_COURSE_EMBEDDINGS: Optional[np.ndarray] = None
_IS_INITIALIZED = False
_INITIALIZATION_FAILED = False


def get_e5_model():
    """Load E5 once for query encoding; ingestion owns corpus encoding."""
    global _E5_MODEL, _INITIALIZATION_FAILED
    if _E5_MODEL is not None:
        return _E5_MODEL
    if _INITIALIZATION_FAILED:
        return None
    try:
        from sentence_transformers import SentenceTransformer
        logger.info("Initializing intfloat/e5-base-v2 for query encoding...")
        # The model is provisioned explicitly by the offline ingestion setup.
        # Runtime must use that local cache and never block API requests on a
        # Hugging Face availability check.
        _E5_MODEL = SentenceTransformer("intfloat/e5-base-v2", local_files_only=True)
        return _E5_MODEL
    except Exception as exc:
        logger.error("Failed to initialize intfloat/e5-base-v2: %s", exc)
        _INITIALIZATION_FAILED = True
        return None


def _get_course_catalog_path() -> Path:
    """Resolve path to course_catalog.json."""
    base_dir = Path(__file__).resolve().parent.parent
    return base_dir / "data" / "course_catalog.json"


def _construct_course_passage_text(course: Dict[str, Any]) -> str:
    """
    Construct semantic text representation for a course with 'passage: ' prefix.
    E5 model requires 'passage: ' prefix for document embeddings.
    """
    title = course.get("title", "")
    desc = course.get("description", "")
    skills = course.get("skills", [])
    skills_str = ", ".join(skills) if isinstance(skills, list) else str(skills)
    platform = course.get("platform", "")
    category = course.get("category", "")

    content = f"{title}. {desc} Target Skills: {skills_str}. Platform: {platform}. Category: {category}."
    return f"passage: {content.strip()}"


def init_e5_service() -> bool:
    """
    Initialize the E5 embedding service:
    1. Load intfloat/e5-base-v2 model ONCE.
    2. Load course_catalog.json ONCE.
    3. Generate course passage embeddings ONCE and cache in memory.

    Returns True if initialized successfully, False if fallback mode should be used.
    """
    global _E5_MODEL, _COURSE_CATALOG, _COURSE_EMBEDDINGS, _IS_INITIALIZED, _INITIALIZATION_FAILED

    if _IS_INITIALIZED:
        return True
    if _INITIALIZATION_FAILED:
        return False

    try:
        _E5_MODEL = get_e5_model()
        if _E5_MODEL is None:
            return False

        # Load course dataset
        catalog_path = _get_course_catalog_path()
        if not catalog_path.exists():
            logger.error(f"Course catalog file not found at: {catalog_path}")
            _INITIALIZATION_FAILED = True
            return False

        with open(catalog_path, "r", encoding="utf-8") as f:
            _COURSE_CATALOG = json.load(f)

        if not _COURSE_CATALOG:
            logger.error("Course catalog is empty.")
            _INITIALIZATION_FAILED = True
            return False

        # Construct passage texts and generate embeddings once
        passages = [_construct_course_passage_text(c) for c in _COURSE_CATALOG]
        logger.info(f"Generating E5 embeddings for {len(passages)} course passages...")
        
        # normalize_embeddings=True allows direct dot product for cosine similarity
        embeddings = _E5_MODEL.encode(passages, normalize_embeddings=True)
        _COURSE_EMBEDDINGS = np.array(embeddings, dtype=np.float32)

        _IS_INITIALIZED = True
        logger.info("E5 embedding service initialized successfully.")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize intfloat/e5-base-v2 model or course catalog: {e}")
        _INITIALIZATION_FAILED = True
        return False


def _map_chroma_course(course: Dict[str, Any], skill_gaps: List[str]) -> Dict[str, Any]:
    raw_skills = course.get("skills", "[]")
    try:
        skills = json.loads(raw_skills) if isinstance(raw_skills, str) else raw_skills
    except json.JSONDecodeError:
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
    """
    Compute cosine similarity between normalized 1D query vector and 2D matrix of normalized document vectors.
    Returns 1D array of similarity scores in [-1.0, 1.0].
    """
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
    Rank courses from catalog semantically based on student true_skill_gaps.

    Parameters
    ----------
    true_skill_gaps : List[str]
        List of missing skills derived deterministically by compute_skill_gap.
    top_k : int
        Number of top relevant courses to return (default 5, min 3).

    Returns
    -------
    List of course dictionaries ranked by descending semantic similarity score,
    or None if E5 service is unavailable (triggering fallback).
    """
    if not true_skill_gaps:
        logger.info("No true_skill_gaps provided for E5 course ranking.")
        return None

    try:
        # Construct E5 query text with required "query: " prefix
        skills_str = ", ".join(true_skill_gaps)
        query_text = f"query: {skills_str}"

        # Generate query embedding
        model = get_e5_model()
        if model is None:
            return _fallback_catalog_courses(true_skill_gaps, top_k)
        query_embedding = model.encode(query_text, normalize_embeddings=True)
        query_vec = np.array(query_embedding, dtype=np.float32)

        # Primary path: persistent 1,041-course Chroma index.  Runtime does
        # not build embeddings; an offline ingestion command owns that work.
        # Fetch a small candidate window, then deterministically prefer exact
        # Stage-2 gap tags/titles over an otherwise broad semantic result.
        chroma_courses = query_courses(query_vec.tolist(), top_k=max(25, top_k * 10))
        if chroma_courses:
            ranked_courses = _rerank_chroma_courses(chroma_courses, true_skill_gaps, top_k)
            return [_map_chroma_course(course, true_skill_gaps) for course in ranked_courses]

        # Backward-compatible fallback: the small verified core catalog only.
        if not init_e5_service():
            return _fallback_catalog_courses(true_skill_gaps, top_k)

        # Compute cosine similarity against precomputed course passage embeddings
        scores = compute_cosine_similarity(query_vec, _COURSE_EMBEDDINGS)

        # Sort descending by score
        ranked_indices = np.argsort(scores)[::-1]

        top_courses = []
        k = max(3, min(top_k, len(_COURSE_CATALOG)))

        for idx in ranked_indices[:k]:
            course = dict(_COURSE_CATALOG[idx])
            sim_score = float(scores[idx])
            
            # Formulate response object keeping real URLs and expected frontend fields
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

        logger.info(
            f"E5 ranked {len(top_courses)} courses for gaps '{skills_str}'. Top score: {top_courses[0]['similarity_score']}"
        )
        return top_courses

    except Exception as e:
        logger.error(f"Error during E5 course ranking execution: {e}")
        return _fallback_catalog_courses(true_skill_gaps, top_k)


def _fallback_catalog_courses(true_skill_gaps: List[str], top_k: int) -> Optional[List[Dict[str, Any]]]:
    """Deterministic, URL-safe fallback when E5 or ChromaDB is unavailable."""
    try:
        with open(_get_course_catalog_path(), "r", encoding="utf-8") as source:
            catalog = json.load(source)
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("Course catalog fallback unavailable: %s", exc)
        return None
    gap_keys = [skill.casefold() for skill in true_skill_gaps]
    ranked = []
    for course in catalog:
        haystack = " ".join([course.get("title", ""), course.get("description", "")] + course.get("skills", [])).casefold()
        score = sum(gap in haystack for gap in gap_keys)
        if score:
            ranked.append((score, course))
    ranked.sort(key=lambda item: (-item[0], str(item[1].get("title", ""))))
    return [
        {**course, "provider": course.get("platform", ""), "similarity_score": float(score)}
        for score, course in ranked[:max(3, top_k)]
    ] or None
