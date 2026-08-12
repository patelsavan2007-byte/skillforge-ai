import re
import logging
from typing import List, Dict, Any, Optional
from transformers import pipeline

from app.config import settings

logger = logging.getLogger("skillforge.resume_ner")

# Native supported NER labels in oksomu/resume-ner
NATIVE_NER_LABELS = {
    "NAME", "EMAIL", "PHONE", "LOCATION",
    "COMPANY", "TITLE", "DEGREE", "FIELD",
    "INSTITUTION", "SKILL", "CERT", "LANGUAGE"
}


class ResumeNERService:
    _instance: Optional["ResumeNERService"] = None

    def __init__(self):
        self.model_name = getattr(settings, "RESUME_NER_MODEL", "oksomu/resume-ner")
        self.min_confidence = getattr(settings, "RESUME_NER_MIN_CONFIDENCE", 0.60)
        self.pipe = None
        self._load_model()

    @classmethod
    def get_instance(cls) -> "ResumeNERService":
        if cls._instance is None:
            cls._instance = ResumeNERService()
        return cls._instance

    def _load_model(self):
        try:
            logger.info("Initializing Hugging Face NER pipeline with model: %s", self.model_name)
            print(f"Loading Hugging Face model: {self.model_name}...")
            self.pipe = pipeline(
                "token-classification",
                model=self.model_name,
                aggregation_strategy="simple"
            )
            print(f"Model {self.model_name} loaded successfully!")
            logger.info("Model %s loaded successfully", self.model_name)
        except Exception as e:
            logger.error("Failed to load NER model %s: %s", self.model_name, str(e))
            print(f"Error loading NER model {self.model_name}: {e}")
            raise RuntimeError(f"Could not load Hugging Face model {self.model_name}: {e}")

    def preprocess_text(self, text: str) -> str:
        """Normalize resume text before running NER inference."""
        if not text:
            return ""

        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Replace non-standard bullets with simple dashes
        text = re.sub(r"[•▪►★✓✔❖*➢]", "-", text)

        # Normalize excessive tabs and horizontal spaces while preserving line breaks
        lines = []
        for line in text.split("\n"):
            cleaned_line = re.sub(r"[ \t]+", " ", line).strip()
            if cleaned_line:
                lines.append(cleaned_line)

        # Rejoin lines with single newlines
        normalized = "\n".join(lines)
        return normalized

    def chunk_text(self, text: str, max_words_per_chunk: int = 300) -> List[str]:
        """Split long resumes into paragraph-aware chunks within model context limits (512 tokens)."""
        paragraphs = text.split("\n")
        chunks = []
        current_chunk = []
        current_word_count = 0

        for para in paragraphs:
            words = para.split()
            word_count = len(words)

            if word_count > max_words_per_chunk:
                # If a single paragraph is huge, split it by sentence or hard boundary
                if current_chunk:
                    chunks.append("\n".join(current_chunk))
                    current_chunk = []
                    current_word_count = 0

                # Split huge paragraph into word slices
                for i in range(0, word_count, max_words_per_chunk):
                    slice_words = words[i:i + max_words_per_chunk]
                    chunks.append(" ".join(slice_words))
            elif current_word_count + word_count > max_words_per_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = [para]
                current_word_count = word_count
            else:
                current_chunk.append(para)
                current_word_count += word_count

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks if chunks else [text]

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Preprocess text, chunk if long, run model inference, and return clean JSON entities."""
        if not self.pipe:
            self._load_model()

        clean_text = self.preprocess_text(text)
        if not clean_text:
            return []

        chunks = self.chunk_text(clean_text)
        all_raw_entities = []

        for chunk in chunks:
            try:
                raw_results = self.pipe(chunk)
                if raw_results:
                    all_raw_entities.extend(raw_results)
            except Exception as e:
                logger.warning("NER inference error on chunk: %s", str(e))

        processed_entities = []
        seen = set()

        for entity in all_raw_entities:
            # Check label
            label = entity.get("entity_group") or entity.get("entity") or ""
            label = label.upper().strip()

            # Filter non-native or invalid labels
            if label not in NATIVE_NER_LABELS:
                continue

            score = float(entity.get("score", 0.0))
            if score < self.min_confidence:
                continue

            word_text = entity.get("word", "").strip()
            # Clean up token artifacts like ##, subwords, trailing commas
            word_text = re.sub(r"^[^\w]+|[^\w]+$", "", word_text)
            if not word_text or len(word_text) < 2:
                continue

            dedup_key = (word_text.lower(), label)
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            processed_entities.append({
                "text": word_text,
                "label": label,
                "score": round(score, 4)
            })

        return processed_entities


# Helper accessor to reuse singleton instance
def get_ner_service() -> ResumeNERService:
    return ResumeNERService.get_instance()
