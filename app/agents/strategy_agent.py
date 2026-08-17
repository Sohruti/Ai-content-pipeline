"""Strategy Agent - decides the content strategy like a Head of GTM."""

import json

from app.models.state import ContentStrategy, PipelineState
from app.services.llm import invoke_llm
from app.services.logger import get_logger
from app.services.prompt_loader import load_prompt

logger = get_logger(__name__)


def _parse_strategy(response: str) -> ContentStrategy:
    """Parse the LLM response into a ContentStrategy object."""
    try:
        # Try to extract JSON from the response
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end > start:
            data = json.loads(response[start:end])
            return ContentStrategy(**data)
    except (json.JSONDecodeError, KeyError):
        pass

    # Fallback: parse key sections manually
    return ContentStrategy(
        business_angle=_extract_section(response, "Business Angle", "business angle"),
        target_audience=_extract_section(response, "Target Audience", "target audience"),
        messaging=_extract_section(response, "Messaging", "messaging"),
        content_goal=_extract_section(response, "Content Goal", "content goal"),
        cta=_extract_section(response, "CTA", "call to action"),
        tone=_extract_section(response, "Tone", "tone"),
        content_type=_extract_section(response, "Content Type", "content type"),
    )


def _extract_section(text: str, header: str, fallback: str) -> str:
    """Extract a section from the text response."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if header.lower() in line.lower():
            # Get the next non-empty line
            for j in range(i + 1, min(i + 3, len(lines))):
                if lines[j].strip() and lines[j].strip() != header:
                    return lines[j].strip().replace("**", "").replace("- ", "")
    return fallback


def run(state: PipelineState) -> dict:
    """Execute the Strategy Agent.

    Decides the content strategy based on knowledge and research.
    """
    logger.info(f"=== Strategy Agent Starting === Topic: {state.topic}")

    system_prompt = load_prompt("strategy")
    user_prompt = f"""Topic: {state.topic}

## Knowledge Context

{state.knowledge.company_overview[:1500] if state.knowledge.company_overview else "No knowledge context."}

## Research Summary

{state.research.industry_trends[:1500] if state.research.industry_trends else "No research available."}

## Raw Research

{state.research.raw_research[:1000] if state.research.raw_research else "No raw research."}

Based on this information, develop a content strategy for a LinkedIn post. Return your strategy as JSON with these fields:
- business_angle
- target_audience
- messaging
- content_goal
- cta
- tone
- content_type"""

    response = invoke_llm(system_prompt, user_prompt)
    strategy = _parse_strategy(response)

    logger.info(f"Strategy: {strategy.content_type} targeting {strategy.target_audience}")
    logger.info("=== Strategy Agent Complete ===")
    return {"strategy": strategy}
