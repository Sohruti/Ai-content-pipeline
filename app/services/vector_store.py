"""FAISS-based vector store service for semantic search."""

import json
from pathlib import Path

import faiss
import numpy as np

from app.config.settings import FAISS_INDEX_PATH
from app.services.embeddings import embed_text, embed_texts
from app.services.logger import get_logger

logger = get_logger(__name__)


class VectorStore:
    """FAISS vector store for founder knowledge retrieval."""

    def __init__(self, index_path: str | None = None) -> None:
        self.index_path = Path(index_path or FAISS_INDEX_PATH)
        self.index: faiss.IndexFlatL2 | None = None
        self.documents: list[str] = []
        self.metadata: list[dict] = []
        self._dimension = 384  # all-MiniLM-L6-v2 dimension

    def build_from_texts(
        self, texts: list[str], metadata: list[dict] | None = None
    ) -> None:
        """Build the index from a list of texts.

        Args:
            texts: List of text chunks to index.
            metadata: Optional metadata for each chunk.
        """
        if not texts:
            logger.warning("No texts provided to build index")
            return

        logger.info(f"Building vector index from {len(texts)} chunks")

        self.documents = texts
        self.metadata = metadata or [{} for _ in texts]

        embeddings = np.array(embed_texts(texts), dtype=np.float32)
        self.index = faiss.IndexFlatL2(self._dimension)
        self.index.add(embeddings)

        logger.info(f"Vector index built: {self.index.ntotal} vectors")

    def search(self, query: str, k: int = 5) -> list[dict]:
        """Search the index for similar texts.

        Args:
            query: Search query.
            k: Number of results to return.

        Returns:
            List of dicts with 'text', 'metadata', and 'score' keys.
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("No index available for search")
            return []

        query_embedding = np.array([embed_text(query)], dtype=np.float32)
        distances, indices = self.index.search(query_embedding, min(k, self.index.ntotal))

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.documents):
                results.append({
                    "text": self.documents[idx],
                    "metadata": self.metadata[idx],
                    "score": float(1 / (1 + dist)),  # Convert distance to similarity
                })

        logger.info(f"Vector search returned {len(results)} results")
        return results

    def save(self) -> None:
        """Save the index and documents to disk."""
        if self.index is None:
            logger.warning("No index to save")
            return

        self.index_path.mkdir(parents=True, exist_ok=True)

        faiss.write_index(self.index, str(self.index_path / "index.faiss"))

        docs_path = self.index_path / "documents.json"
        docs_path.write_text(json.dumps(self.documents), encoding="utf-8")

        meta_path = self.index_path / "metadata.json"
        meta_path.write_text(json.dumps(self.metadata), encoding="utf-8")

        logger.info(f"Vector index saved to {self.index_path}")

    def load(self) -> bool:
        """Load the index from disk.

        Returns:
            True if loaded successfully, False otherwise.
        """
        index_file = self.index_path / "index.faiss"
        docs_file = self.index_path / "documents.json"

        if not index_file.exists() or not docs_file.exists():
            logger.info("No existing vector index found")
            return False

        self.index = faiss.read_index(str(index_file))
        self.documents = json.loads(docs_file.read_text(encoding="utf-8"))

        meta_path = self.index_path / "metadata.json"
        if meta_path.exists():
            self.metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        else:
            self.metadata = [{} for _ in self.documents]

        logger.info(f"Vector index loaded: {self.index.ntotal} vectors")
        return True


_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """Get or create the singleton vector store."""
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
