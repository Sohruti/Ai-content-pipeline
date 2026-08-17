"""Review Agent - scores and approves content."""

import json

from app.config.settings import MAX_REVIEW_ITERATIONS, MIN_REVIEW_SCORE
from app.models.state import PipelineState, ReviewScore
from app.services.llm import invoke_llm
from app.services.logger import get_logger
from app.services.prompt_loader import load_prompt

logger = get_logger(__name__)


def _parse_review(response: str) -> ReviewScore:
    """Parse the LLM response into a ReviewScore object."""
    try:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end > start:
            data = json.loads(response[start:end])
            return ReviewScore(**data)
    except (json.JSONDecodeError, KeyError):
        pass

    # Fallback: extract scores
    return ReviewScore(
        founder_voice_score=_extract_score(response, "Founder Voice"),
        business_first_score=_extract_score(response, "Business"),
        readability_score=_extract_score(response, "Readability"),
        authenticity_score=_extract_score(response, "Authenticity"),
        cxo_relevance_score=_extract_score(response, "CXO"),
        overall_score=0.0,
        feedback=response[:500],
        approved=False,
    )


def _extract_score(text: str, keyword: str) -> int:
    """Extract a score from the text."""
    for line in text.split("\n"):
        if keyword.lower() in line.lower():
            # Look for a number
            import re
            numbers = re.findall(r"(\d+)", line)
            if numbers:
                return min(int(numbers[0]), 10)
    return 5


def run(state: PipelineState) -> dict:
    """Execute the Review Agent.

    Scores the generated content and decides if it's approved.
    """
    logger.info(f"=== Review Agent Starting (Iteration {state.iteration}) ===")

    system_prompt = load_prompt("review")
    user_prompt = f"""Review this LinkedIn post for quality and authenticity.

## LinkedIn Post to Review

{state.draft}

## Content Strategy

- Business Angle: {state.strategy.business_angle}
- Target Audience: {state.strategy.target_audience}
- Content Goal: {state.strategy.content_goal}

## Review Criteria

Score each criterion 1-10 and provide an overall score. Return your review as JSON with these fields:
- founder_voice_score
- business_first_score
- readability_score
- authenticity_score
- cxo_relevance_score
- overall_score
- feedback
- approved (true if overall_score >= {MIN_REVIEW_SCORE})
- iteration (set to {state.iteration})"""

    response = invoke_llm(system_prompt, user_prompt)
    review = _parse_review(response)

    # Ensure iteration is tracked
    review.iteration = state.iteration

    # Force approval after max iterations
    if state.iteration >= MAX_REVIEW_ITERATIONS and not review.approved:
        logger.warning(f"Max iterations ({MAX_REVIEW_ITERATIONS}) reached, forcing approval")
        review.approved = True
        review.feedback += "\n\n[Auto-approved after max iterations]"

    if review.approved:
        logger.info(f"Content APPROVED with score {review.overall_score}/10")
    else:
        logger.info(f"Content REJECTED with score {review.overall_score}/10 - Feedback: {review.feedback[:100]}")

    logger.info("=== Review Agent Complete ===")
    return {"review": review}
