"""Post cleaner service for the Founder Intelligence Pipeline.

Removes noise from fetched posts while preserving content structure.
"""

import re

from app.models.founder import FounderPost, FetchedPosts
from app.services.logger import get_logger

logger = get_logger(__name__)

# Patterns to remove
NOISE_PATTERNS = [
    r"https?://\S+",                    # URLs
    r"See more$",                        # LinkedIn "see more" truncation
    r"…\s*see more$",                    # Ellipsis + see more
    r"\d+\s+comments?\b",               # "3 comments"
    r"\d+\s+reposts?\b",                # "2 reposts"
    r"Like\s+Comment\s+Repost\s+Send",  # LinkedIn action buttons
    r"Write a comment…",                 # LinkedIn comment prompt
    r"•\s*Top",                          # LinkedIn "Top" comments marker
    r"\n{3,}",                           # Excessive newlines (3+)
    r"  +",                              # Multiple spaces
]


def _clean_text(text: str) -> str:
    """Remove noise patterns from post text.

    Args:
        text: Raw post text.

    Returns:
        Cleaned text with noise removed.
    """
    cleaned = text

    for pattern in NOISE_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.MULTILINE | re.IGNORECASE)

    # Remove image metadata patterns like "📸 Image" or "[Image]"
    cleaned = re.sub(r"[📸🖼📷🎬]+\s*\w*", "", cleaned)
    cleaned = re.sub(r"\[Image\d*\]", "", cleaned)

    # Collapse multiple newlines into double newline
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    # Strip leading/trailing whitespace
    cleaned = cleaned.strip()

    return cleaned


def _is_valid_post(text: str) -> bool:
    """Check if a post has meaningful content after cleaning.

    Args:
        text: Cleaned post text.

    Returns:
        True if the post is valid and worth keeping.
    """
    if not text or len(text) < 20:
        return False

    # Skip posts that are mostly links or very short
    words = text.split()
    if len(words) < 10:
        return False

    return True


def clean_posts(fetched: FetchedPosts) -> FetchedPosts:
    """Clean all posts in a FetchedPosts collection.

    Args:
        fetched: Raw fetched posts.

    Returns:
        New FetchedPosts with cleaned text and invalid posts removed.
    """
    logger.info(f"Cleaning {fetched.total_count} posts from {fetched.platform}")

    cleaned_posts = []
    for post in fetched.posts:
        # Store original raw text
        raw = post.text

        # Clean the text
        cleaned_text = _clean_text(raw)

        # Validate
        if _is_valid_post(cleaned_text):
            post.raw_text = raw
            post.text = cleaned_text
            cleaned_posts.append(post)

    removed = fetched.total_count - len(cleaned_posts)
    logger.info(f"Cleaned: {len(cleaned_posts)} valid, {removed} removed")

    return FetchedPosts(
        posts=cleaned_posts,
        platform=fetched.platform,
        founder_name=fetched.founder_name,
        fetched_at=fetched.fetched_at,
        total_count=len(cleaned_posts),
    )


def deduplicate_posts(posts: list[FounderPost]) -> list[FounderPost]:
    """Remove duplicate posts based on text similarity.

    Args:
        posts: List of posts to deduplicate.

    Returns:
        Deduplicated list of posts.
    """
    seen_texts = set()
    unique_posts = []

    for post in posts:
        # Normalize text for comparison
        normalized = post.text.lower().strip()[:200]  # First 200 chars
        if normalized not in seen_texts:
            seen_texts.add(normalized)
            unique_posts.append(post)

    removed = len(posts) - len(unique_posts)
    if removed > 0:
        logger.info(f"Removed {removed} duplicate posts")

    return unique_posts
