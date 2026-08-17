"""Story Architect Agent - creates the story blueprint."""

import json

from app.models.state import PipelineState, StoryBlueprint
from app.services.llm import invoke_llm
from app.services.logger import get_logger
from app.services.prompt_loader import load_prompt

logger = get_logger(__name__)


def _parse_story(response: str) -> StoryBlueprint:
    """Parse the LLM response into a StoryBlueprint object."""
    try:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end > start:
            data = json.loads(response[start:end])
            return StoryBlueprint(**data)
    except (json.JSONDecodeError, KeyError):
        pass

    # Fallback: extract sections
    return StoryBlueprint(
        hook=_extract_section(response, "Hook"),
        problem=_extract_section(response, "Problem"),
        insight=_extract_section(response, "Insight"),
        business_lesson=_extract_section(response, "Business Lesson"),
        cta=_extract_section(response, "CTA"),
        narrative_arc=response[:500],
    )


def _extract_section(text: str, header: str) -> str:
    """Extract a section from the text response."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if header.lower() in line.lower():
            section_lines = []
            for j in range(i + 1, len(lines)):
                if lines[j].strip() and not any(
                    h.lower() in lines[j].lower()
                    for h in ["Hook", "Problem", "Insight", "Business Lesson", "CTA"]
                ):
                    section_lines.append(lines[j].strip())
                else:
                    break
            return " ".join(section_lines).replace("**", "").replace("- ", "")
    return ""


def run(state: PipelineState) -> dict:
    """Execute the Story Architect Agent.

    Creates a story blueprint from the strategy and founder context.
    """
    logger.info("=== Story Architect Starting ===")

    system_prompt = load_prompt("story")
    user_prompt = f"""Topic: {state.topic}

## Content Strategy

- Business Angle: {state.strategy.business_angle}
- Target Audience: {state.strategy.target_audience}
- Messaging: {state.strategy.messaging}
- Content Goal: {state.strategy.content_goal}
- CTA: {state.strategy.cta}
- Tone: {state.strategy.tone}
- Content Type: {state.strategy.content_type}

## Founder Context

{state.founder_context[:1500] if state.founder_context else "No founder context available."}

## Company Knowledge

{state.knowledge.company_overview[:500] if state.knowledge.company_overview else "No company knowledge."}

Create a compelling story blueprint for a LinkedIn post. Return your blueprint as JSON with these fields:
- hook
- problem
- insight
- business_lesson
- cta
- narrative_arc"""

    response = invoke_llm(system_prompt, user_prompt)
    story = _parse_story(response)

    logger.info(f"Story hook: {story.hook[:80]}...")
    logger.info("=== Story Architect Complete ===")
    return {"story": story}
