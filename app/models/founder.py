"""Pydantic models for the Founder Intelligence Pipeline."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class FounderPost(BaseModel):
    """A single founder post from any platform."""
    text: str = Field(description="Clean post content")
    date: str = Field(default="", description="Post date (ISO format or readable)")
    engagement: dict = Field(default_factory=dict, description="Likes, comments, shares")
    url: str = Field(default="", description="Original post URL")
    platform: str = Field(default="linkedin", description="Source platform")
    raw_text: str = Field(default="", description="Original uncleaned text")


class FetchedPosts(BaseModel):
    """Collection of fetched posts from a platform."""
    posts: list[FounderPost] = Field(default_factory=list)
    platform: str
    founder_name: str
    fetched_at: datetime = Field(default_factory=datetime.now)
    total_count: int = 0


class WritingStyle(BaseModel):
    """Extracted writing style patterns."""
    avg_sentence_length: int = Field(default=0, description="Average words per sentence")
    avg_paragraph_length: int = Field(default=0, description="Average sentences per paragraph")
    tone: list[str] = Field(default_factory=list, description="Detected tones")
    formality: str = Field(default="conversational", description="Formality level")
    uses_short_sentences: bool = True
    uses_line_breaks: bool = True
    uses_emojis: bool = False
    uses_hashtags: bool = False
    max_hashtags: int = 0


class HookPattern(BaseModel):
    """A detected hook pattern."""
    pattern: str = Field(description="Description of the hook pattern")
    example: str = Field(default="", description="Example from posts")
    frequency: int = Field(default=0, description="How often used")


class FounderOpinion(BaseModel):
    """A detected founder opinion or belief."""
    topic: str = Field(description="What the opinion is about")
    stance: str = Field(description="The founder's position")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class FounderIntelligence(BaseModel):
    """Complete founder intelligence analysis."""
    writing_style: WritingStyle = Field(default_factory=WritingStyle)
    hook_patterns: list[HookPattern] = Field(default_factory=list)
    vocabulary: list[str] = Field(default_factory=list, description="Frequently used words")
    business_themes: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    storytelling_pattern: str = Field(default="")
    cta_patterns: list[str] = Field(default_factory=list)
    business_philosophy: list[str] = Field(default_factory=list)
    opinions: list[FounderOpinion] = Field(default_factory=list)
    product_positioning: list[str] = Field(default_factory=list)
    communication_style: str = Field(default="")
    writing_dos: list[str] = Field(default_factory=list)
    writing_donts: list[str] = Field(default_factory=list)
    posts_analyzed: int = 0
    last_updated: str = Field(default="")
