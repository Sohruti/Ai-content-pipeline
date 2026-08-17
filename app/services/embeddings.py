"""Embeddings service using Sentence Transformers."""

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.config.settings import EMBEDDING_MODEL
from app.services.logger import get_logger

logger = get_logger(__name__)

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    """Lazy-load the sentence transformer model."""
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        _model = SentenceTransformer(EMBEDDING_MODEL)
        logger.info("Embedding model loaded")
    return _model


def embed_text(text: str) -> list[float]:
    """Embed a single text string."""
    model = _get_model()
    embedding = model.encode(text, show_progress_bar=False)
    return embedding.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of text strings."""
    model = _get_model()
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()
