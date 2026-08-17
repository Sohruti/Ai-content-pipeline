"""Platform Writer Agent - generates production-quality LinkedIn content."""

from app.models.state import PipelineState
from app.services.llm import invoke_llm
from app.services.logger import get_logger
from app.services.prompt_loader import load_prompt

logger = get_logger(__name__)


def run(state: PipelineState) -> dict:
    """Execute the Platform Writer Agent.

    Generates a production-quality LinkedIn post from the story blueprint.
    """
    logger.info("=== Platform Writer Starting ===")

    system_prompt = load_prompt("writer")
    user_prompt = f"""Write a production-quality LinkedIn post based on this blueprint.

## Story Blueprint

### Hook
{state.story.hook}

### Problem
{state.story.problem}

### Insight
{state.story.insight}

### Business Lesson
{state.story.business_lesson}

### CTA
{state.story.cta}

### Narrative Arc
{state.story.narrative_arc}

## Strategy Context

- Business Angle: {state.strategy.business_angle}
- Target Audience: {state.strategy.target_audience}
- Messaging: {state.strategy.messaging}
- Tone: {state.strategy.tone}

## Founder Voice Reference

{state.founder_context[:1000] if state.founder_context else "Write in a direct, confident founder voice."}

## Company Context

{state.knowledge.company_overview[:500] if state.knowledge.company_overview else ""}

Write the complete LinkedIn post. Make it publication-ready. Match the founder's authentic voice."""

    draft = invoke_llm(system_prompt, user_prompt)

    logger.info(f"Draft generated: {len(draft)} chars")
    logger.info("=== Platform Writer Complete ===")
    return {"draft": draft}
