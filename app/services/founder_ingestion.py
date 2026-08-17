"""Founder Ingestion - orchestrates the founder intelligence pipeline.

This module is completely independent from the main content pipeline.
It updates the Founder Knowledge Base that the Founder Brain uses.

Pipeline:
    Fetch latest posts
    → Check for duplicates
    → Store raw JSON
    → Clean
    → Analyze
    → Generate processed markdown
    → Generate founder_posts.md
    → Regenerate embeddings
    → Done
"""

import json
from datetime import datetime
from pathlib import Path

from app.config.settings import (
    FOUNDER_NAME,
    FOUNDER_POSTS_DIR,
    FOUNDER_RAW_DIR,
    FOUNDER_MASTER_FILE,
)
from app.models.founder import FetchedPosts
from app.services.founder_analyzer import (
    analyze_posts,
    generate_master_file,
    generate_processed_files,
)
from app.services.founder_fetcher import get_fetcher
from app.services.logger import get_logger
from app.services.post_cleaner import clean_posts, deduplicate_posts

logger = get_logger(__name__)


def _load_existing_posts() -> list[dict]:
    """Load existing raw posts from JSON file."""
    raw_file = FOUNDER_RAW_DIR / "linkedin_posts.json"

    if not raw_file.exists():
        return []

    try:
        data = json.loads(raw_file.read_text(encoding="utf-8"))
        return data.get("posts", [])
    except Exception as e:
        logger.warning(f"Failed to load existing posts: {e}")
        return []


def _save_raw_posts(posts: list[dict], platform: str) -> None:
    """Save raw posts to JSON file."""
    FOUNDER_RAW_DIR.mkdir(parents=True, exist_ok=True)

    raw_file = FOUNDER_RAW_DIR / f"{platform}_posts.json"
    data = {
        "platform": platform,
        "founder": FOUNDER_NAME,
        "last_updated": datetime.now().isoformat(),
        "posts": posts,
    }

    raw_file.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    logger.info(f"Saved {len(posts)} raw posts to {raw_file}")


def _merge_posts(existing: list[dict], new_posts: list[dict]) -> list[dict]:
    """Merge new posts with existing, avoiding duplicates."""
    existing_texts = {p.get("text", "")[:200] for p in existing}

    merged = existing.copy()
    added = 0

    for post in new_posts:
        text = post.get("text", "")[:200]
        if text not in existing_texts:
            merged.append(post)
            existing_texts.add(text)
            added += 1

    if added > 0:
        logger.info(f"Added {added} new posts (total: {len(merged)})")

    return merged


def run_ingestion(
    platform: str = "linkedin",
    force: bool = False,
    limit: int = 20,
) -> bool:
    """Run the complete founder ingestion pipeline.

    Args:
        platform: Platform to fetch from ("linkedin", "x", "medium").
        force: If True, re-analyze even if no new posts.
        limit: Maximum number of posts to fetch.

    Returns:
        True if successful, False otherwise.
    """
    logger.info(f"{'='*60}")
    logger.info(f"Founder Intelligence Pipeline - {FOUNDER_NAME}")
    logger.info(f"{'='*60}")

    try:
        # Step 1: Fetch
        logger.info("Step 1: Fetching posts...")
        fetcher = get_fetcher(platform)
        fetched = fetcher.fetch(limit=limit)

        if fetched.total_count == 0:
            logger.warning("No posts fetched. Check your configuration.")
            return False

        # Step 2: Load existing and merge
        logger.info("Step 2: Checking for duplicates...")
        existing = _load_existing_posts()
        new_posts = [p.model_dump() for p in fetched.posts]
        merged = _merge_posts(existing, new_posts)

        # Step 3: Save raw data
        logger.info("Step 3: Storing raw data...")
        _save_raw_posts(merged, platform)

        # Step 4: Clean posts
        logger.info("Step 4: Cleaning posts...")
        cleaned = clean_posts(fetched)
        cleaned_posts = deduplicate_posts(cleaned.posts)

        if not cleaned_posts:
            logger.warning("No valid posts after cleaning")
            return False

        # Step 5: Analyze
        logger.info("Step 5: Analyzing writing patterns...")
        post_texts = [p.text for p in cleaned_posts]
        intelligence = analyze_posts(post_texts)

        # Step 6: Generate processed files
        logger.info("Step 6: Generating processed knowledge files...")
        generate_processed_files(intelligence)

        # Step 7: Generate master file
        logger.info("Step 7: Generating master knowledge file...")
        recent_samples = [p.text[:500] for p in cleaned_posts[:5]]
        generate_master_file(intelligence, recent_samples)

        # Step 8: Update embeddings
        logger.info("Step 8: Updating embeddings...")
        _update_embeddings()

        logger.info(f"{'='*60}")
        logger.info("Founder Intelligence Pipeline Complete!")
        logger.info(f"Posts analyzed: {intelligence.posts_analyzed}")
        logger.info(f"Master file: {FOUNDER_MASTER_FILE}")
        logger.info(f"{'='*60}")

        return True

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return False


def _update_embeddings() -> None:
    """Update FAISS embeddings for founder knowledge."""
    from app.services.embeddings import embed_texts
    from app.services.vector_store import get_vector_store

    if not FOUNDER_MASTER_FILE.exists():
        logger.warning("No founder_posts.md to embed")
        return

    content = FOUNDER_MASTER_FILE.read_text(encoding="utf-8")

    # Split into chunks for embedding
    chunks = []
    sections = content.split("\n## ")
    for i, section in enumerate(sections):
        if section.strip():
            chunk = section if i == 0 else f"## {section}"
            chunks.append(chunk)

    if not chunks:
        chunks = [content]

    # Build founder-specific index
    store = get_vector_store()
    store.build_from_texts(
        texts=chunks,
        metadata=[{"source": "founder_posts", "chunk_index": i} for i in range(len(chunks))],
    )
    store.save()
    logger.info(f"Updated embeddings with {len(chunks)} chunks")
