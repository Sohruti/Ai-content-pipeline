"""Founder Brain Agent - retrieves founder style and knowledge via vector search.

This agent searches the auto-generated founder_posts.md knowledge base.
It NEVER reads raw LinkedIn posts - only the processed intelligence.
"""

from app.config.settings import FOUNDER_MASTER_FILE
from app.models.state import PipelineState
from app.services.logger import get_logger
from app.services.vector_store import get_vector_store

logger = get_logger(__name__)


def run(state: PipelineState) -> dict:
    """Execute the Founder Brain Agent.

    Retrieves relevant founder context using FAISS vector search
    on the auto-generated founder_posts.md knowledge base.
    """
    logger.info("=== Founder Brain Agent Starting ===")

    store = get_vector_store()

    # Try to load existing founder index
    if not store.load():
        logger.info("No existing vector index, building from founder knowledge base...")
        _build_founder_index(store)

    # Build search query from topic + strategy
    search_query = f"{state.topic} {state.strategy.business_angle} {state.strategy.messaging}"
    results = store.search(search_query, k=5)

    # Compile founder context
    context_parts = []
    for result in results:
        text = result["text"]
        # Add section header if not already present
        if not text.startswith("#"):
            text = f"## Relevant Context\n\n{text}"
        context_parts.append(text)

    founder_context = "\n\n---\n\n".join(context_parts) if context_parts else _get_fallback_context()

    logger.info(f"Founder Brain retrieved {len(results)} relevant chunks")
    logger.info("=== Founder Brain Agent Complete ===")
    return {"founder_context": founder_context}


def _build_founder_index(store) -> None:
    """Build vector index from founder_posts.md knowledge base."""
    if not FOUNDER_MASTER_FILE.exists():
        logger.warning(f"Founder knowledge base not found: {FOUNDER_MASTER_FILE}")
        logger.info("Run 'python founder_ingestion.py' to generate it")
        return

    content = FOUNDER_MASTER_FILE.read_text(encoding="utf-8")

    # Split into semantic chunks by section
    chunks = _chunk_by_sections(content)

    if chunks:
        metadata = [{"source": "founder_posts", "chunk_index": i} for i in range(len(chunks))]
        store.build_from_texts(chunks, metadata)
        store.save()
        logger.info(f"Built founder index with {len(chunks)} chunks")
    else:
        logger.warning("No content found in founder_posts.md")


def _chunk_by_sections(text: str, max_chunk_size: int = 800) -> list[str]:
    """Split text by markdown sections, keeping sections together when possible.

    Args:
        text: Full markdown text.
        max_chunk_size: Maximum chunk size in characters.

    Returns:
        List of text chunks.
    """
    chunks = []
    current_chunk = ""

    for line in text.split("\n"):
        # New section starts
        if line.startswith("## ") and current_chunk:
            if len(current_chunk) <= max_chunk_size:
                chunks.append(current_chunk.strip())
            else:
                # Split large sections by paragraphs
                chunks.extend(_split_large_section(current_chunk))
            current_chunk = line + "\n"
        else:
            current_chunk += line + "\n"

    # Don't forget the last chunk
    if current_chunk.strip():
        if len(current_chunk) <= max_chunk_size:
            chunks.append(current_chunk.strip())
        else:
            chunks.extend(_split_large_section(current_chunk))

    return chunks if chunks else [text[:max_chunk_size]]


def _split_large_section(section: str, max_size: int = 800) -> list[str]:
    """Split a large section into smaller chunks."""
    paragraphs = section.split("\n\n")
    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) > max_size and current:
            chunks.append(current.strip())
            current = para + "\n\n"
        else:
            current += para + "\n\n"

    if current.strip():
        chunks.append(current.strip())

    return chunks


def _get_fallback_context() -> str:
    """Provide fallback context when no search results found."""
    return """## Founder Voice Guidelines

- Direct and confident tone
- Uses short, punchy sentences
- Challenges conventional thinking
- Focuses on business outcomes
- Shares real opinions, not generic advice
- Uses examples from real enterprise challenges

## Key Beliefs

- Privacy is an architectural decision, not a feature
- Enterprise AI requires governance first
- Move fast and break things doesn't work with regulated data
- Second-order thinking matters in AI deployment"""
