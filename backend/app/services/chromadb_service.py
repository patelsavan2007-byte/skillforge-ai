"""Persistent ChromaDB access for Stage 3 course retrieval only."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import settings

logger = logging.getLogger("skillforge.chromadb")

_CLIENT: Any = None


def _get_client() -> Any:
    """Create one process-wide client; never create/re-index data at runtime."""
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT
    if getattr(settings, "LOW_MEMORY_MODE", False) or not getattr(settings, "ENABLE_HEAVY_MODELS", True):
        logger.debug("Low memory mode active: Skipping ChromaDB client initialization.")
        return None
    try:
        import chromadb

        path = Path(settings.CHROMADB_DIR).resolve()
        path.mkdir(parents=True, exist_ok=True)
        _CLIENT = chromadb.PersistentClient(path=str(path))
        return _CLIENT
    except (ImportError, MemoryError, OSError, Exception) as exc:
        logger.warning("ChromaDB is unavailable or memory constrained: %s", exc)
        return None


def get_course_collection(create: bool = False) -> Any:
    """Return the populated collection, optionally creating it for offline ingest."""
    client = _get_client()
    if client is None:
        return None
    try:
        if create:
            return client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
        return client.get_collection(name=settings.CHROMA_COLLECTION_NAME)
    except Exception as exc:
        logger.info("Chroma collection '%s' is not ready: %s", settings.CHROMA_COLLECTION_NAME, exc)
        return None


def query_courses(query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
    """Query the existing index and return metadata with cosine similarity."""
    collection = get_course_collection()
    if collection is None:
        return []
    try:
        if collection.count() == 0:
            return []
        result = collection.query(
            query_embeddings=[query_embedding],
            n_results=max(1, top_k),
            include=["metadatas", "distances"],
        )
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        return [
            {**metadata, "similarity_score": round(1.0 - float(distance), 4)}
            for metadata, distance in zip(metadatas, distances)
            if metadata
        ]
    except Exception as exc:
        logger.warning("ChromaDB course query failed: %s", exc)
        return []


def get_collection_stats() -> Dict[str, Any]:
    collection = get_course_collection()
    return {
        "available": collection is not None,
        "collection": settings.CHROMA_COLLECTION_NAME,
        "count": collection.count() if collection is not None else 0,
        "path": str(Path(settings.CHROMADB_DIR).resolve()),
    }
