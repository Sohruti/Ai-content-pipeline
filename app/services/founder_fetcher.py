"""Founder fetcher interface and LinkedIn provider.

Uses a provider architecture for extensibility.
LinkedIn fetching uses Apify or configurable scraping service.
"""

import json
from abc import ABC, abstractmethod
from pathlib import Path

from app.config.settings import FOUNDER_LINKEDIN_URL, FOUNDER_NAME
from app.models.founder import FounderPost, FetchedPosts
from app.services.logger import get_logger

logger = get_logger(__name__)


class FounderFetcher(ABC):
    """Abstract interface for fetching founder posts.

    Implement this to add new platforms (X, Medium, Blogs, etc.)
    """

    @abstractmethod
    def fetch(self, limit: int = 20) -> FetchedPosts:
        """Fetch latest posts from the platform.

        Args:
            limit: Maximum number of posts to fetch.

        Returns:
            FetchedPosts with the collected posts.
        """
        ...

    @abstractmethod
    def get_platform(self) -> str:
        """Return the platform name."""
        ...


class LinkedInFetcher(FounderFetcher):
    """Fetch founder posts from LinkedIn.

    Supports multiple fetching methods:
    1. Apify actor (recommended for production)
    2. Local JSON file (for development/testing)

    Configure via environment:
    - LINKEDIN_FETCH_METHOD: "apify" or "local"
    - APIFY_API_KEY: Your Apify API key (if using Apify)
    """

    def __init__(self) -> None:
        import os
        self.fetch_method = os.getenv("LINKEDIN_FETCH_METHOD", "local")
        self.apify_key = os.getenv("APIFY_API_KEY", "")
        self.profile_url = FOUNDER_LINKEDIN_URL
        self.founder_name = FOUNDER_NAME

    def get_platform(self) -> str:
        return "linkedin"

    def fetch(self, limit: int = 20) -> FetchedPosts:
        """Fetch LinkedIn posts using configured method."""
        logger.info(f"Fetching LinkedIn posts for {self.founder_name} (method: {self.fetch_method})")

        if self.fetch_method == "apify":
            return self._fetch_via_apify(limit)
        else:
            return self._fetch_local(limit)

    def _fetch_via_apify(self, limit: int) -> FetchedPosts:
        """Fetch posts via Apify LinkedIn scraper actor."""
        if not self.apify_key:
            logger.warning("APIFY_API_KEY not set, falling back to local fetch")
            return self._fetch_local(limit)

        try:
            import httpx

            # Apify actor for LinkedIn post scraping
            actor_id = "anchor/linkedin-post-scraper"
            run_url = f"https://api.apify.com/v2/acts/{actor_id}/run-sync-get-dataset-items"
            params = {
                "token": self.apify_key,
                "timeout": 120,
            }
            payload = {
                "profileUrls": [self.profile_url],
                "limit": limit,
                "scrapeCompany": False,
            }

            logger.info(f"Calling Apify actor: {actor_id}")
            response = httpx.post(run_url, json=payload, params=params, timeout=180)
            response.raise_for_status()

            data = response.json()
            posts = []
            for item in data[:limit]:
                post = FounderPost(
                    text=item.get("text", ""),
                    date=item.get("postedAt", ""),
                    engagement={
                        "likes": item.get("likesCount", 0),
                        "comments": item.get("commentsCount", 0),
                        "shares": item.get("sharesCount", 0),
                    },
                    url=item.get("url", ""),
                    platform="linkedin",
                    raw_text=item.get("text", ""),
                )
                posts.append(post)

            logger.info(f"Fetched {len(posts)} posts via Apify")
            return FetchedPosts(
                posts=posts,
                platform="linkedin",
                founder_name=self.founder_name,
                total_count=len(posts),
            )

        except Exception as e:
            logger.error(f"Apify fetch failed: {e}")
            logger.info("Falling back to local fetch")
            return self._fetch_local(limit)

    def _fetch_local(self, limit: int) -> FetchedPosts:
        """Load posts from local JSON file (for development/testing)."""
        from app.config.settings import DATA_DIR

        local_file = DATA_DIR / "founder_posts" / "raw" / "linkedin_posts.json"

        if not local_file.exists():
            logger.warning(f"No local LinkedIn posts found at {local_file}")
            return FetchedPosts(
                posts=[],
                platform="linkedin",
                founder_name=self.founder_name,
                total_count=0,
            )

        try:
            data = json.loads(local_file.read_text(encoding="utf-8"))
            posts = []
            for item in data.get("posts", [])[:limit]:
                post = FounderPost(**item)
                posts.append(post)

            logger.info(f"Loaded {len(posts)} posts from local file")
            return FetchedPosts(
                posts=posts,
                platform="linkedin",
                founder_name=self.founder_name,
                total_count=len(posts),
            )

        except Exception as e:
            logger.error(f"Failed to load local posts: {e}")
            return FetchedPosts(
                posts=[],
                platform="linkedin",
                founder_name=self.founder_name,
                total_count=0,
            )


def get_fetcher(platform: str = "linkedin") -> FounderFetcher:
    """Factory function to get the appropriate fetcher.

    Args:
        platform: Platform to fetch from ("linkedin", "x", "medium", etc.)

    Returns:
        FounderFetcher instance for the specified platform.
    """
    fetchers = {
        "linkedin": LinkedInFetcher,
    }

    fetcher_class = fetchers.get(platform)
    if not fetcher_class:
        raise ValueError(f"Unsupported platform: {platform}. Available: {list(fetchers.keys())}")

    return fetcher_class()
