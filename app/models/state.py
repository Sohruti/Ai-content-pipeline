"""Pipeline state and data models for the 2OS Content Operating System."""

from typing import Literal

from pydantic import BaseModel, Field


class KnowledgeContext(BaseModel):
    """Output of the Knowledge Agent."""
    company_overview: str = Field(default="", description="Company overview from data sources")
    product_summary: str = Field(default="", description="Product/service description")
    founder_voice: str = Field(default="", description="Founder's writing style and opinions")
    customer_insights: str = Field(default="", description="Customer stories and case studies")
    blog_highlights: str = Field(default="", description="Key blog post themes")
    raw_context: str = Field(default="", description="Combined raw knowledge context")


class ResearchSummary(BaseModel):
    """Output of the Research Agent."""
    topic: str = Field(description="Research topic")
    industry_trends: str = Field(default="", description="Current industry trends")
    ai_news: str = Field(default="", description="Recent AI news relevant to topic")
    competitor_insights: str = Field(default="", description="What competitors are doing")
    market_context: str = Field(default="", description="Broader market context")
    raw_research: str = Field(default="", description="Combined raw research")


class ContentStrategy(BaseModel):
    """Output of the Strategy Agent."""
    business_angle: str = Field(description="The business angle to take")
    target_audience: str = Field(description="Who this content is for")
    messaging: str = Field(description="Core message to convey")
    content_goal: str = Field(description="What this content should achieve")
    cta: str = Field(description="Call to action")
    tone: str = Field(default="authoritative yet approachable", description="Content tone")
    content_type: str = Field(default="thought_leadership", description="Type of content")


class StoryBlueprint(BaseModel):
    """Output of the Story Architect."""
    hook: str = Field(description="Opening hook to grab attention")
    problem: str = Field(description="The problem or challenge being addressed")
    insight: str = Field(description="Key insight or breakthrough")
    business_lesson: str = Field(description="Business lesson or takeaway")
    cta: str = Field(description="Call to action")
    narrative_arc: str = Field(default="", description="Full narrative structure")


class ReviewScore(BaseModel):
    """Output of the Review Agent."""
    founder_voice_score: int = Field(ge=1, le=10, description="How well it matches founder voice")
    business_first_score: int = Field(ge=1, le=10, description="Business-first vs tech-first")
    readability_score: int = Field(ge=1, le=10, description="Readability and clarity")
    authenticity_score: int = Field(ge=1, le=10, description="Authenticity and genuine tone")
    cxo_relevance_score: int = Field(ge=1, le=10, description="Relevance to CXO audience")
    overall_score: float = Field(description="Weighted average score")
    feedback: str = Field(default="", description="Detailed feedback")
    approved: bool = Field(default=False, description="Whether content is approved")
    iteration: int = Field(default=1, description="Current review iteration")


class PipelineState(BaseModel):
    """Main state object flowing through the LangGraph pipeline."""
    topic: str = Field(description="Content topic or theme")
    knowledge: KnowledgeContext = Field(default_factory=KnowledgeContext)
    research: ResearchSummary = Field(default_factory=lambda: ResearchSummary(topic=""))
    strategy: ContentStrategy = Field(
        default_factory=lambda: ContentStrategy(
            business_angle="", target_audience="", messaging="", content_goal="", cta=""
        )
    )
    founder_context: str = Field(default="", description="Retrieved founder context")
    story: StoryBlueprint = Field(
        default_factory=lambda: StoryBlueprint(
            hook="", problem="", insight="", business_lesson="", cta=""
        )
    )
    draft: str = Field(default="", description="Generated LinkedIn post draft")
    review: ReviewScore = Field(
        default_factory=lambda: ReviewScore(
            founder_voice_score=1, business_first_score=1, readability_score=1,
            authenticity_score=1, cxo_relevance_score=1, overall_score=1.0
        )
    )
    final_output: str = Field(default="", description="Final approved LinkedIn post")
    iteration: int = Field(default=1, description="Current pipeline iteration")
