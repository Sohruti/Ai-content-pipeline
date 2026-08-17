"""LangGraph pipeline for the 2OS Content Operating System."""

from langgraph.graph import END, StateGraph

from app.agents import (
    founder_brain_agent,
    knowledge_agent,
    platform_writer_agent,
    research_agent,
    review_agent,
    story_architect_agent,
    strategy_agent,
)
from app.models.state import PipelineState
from app.services.logger import get_logger

logger = get_logger(__name__)


def _should_continue_review(state: PipelineState) -> str:
    """Decide whether to continue review loop or finish."""
    if state.review.approved:
        logger.info("Review approved, proceeding to final output")
        return "finalize"
    else:
        logger.info(f"Review not approved (iteration {state.iteration}), rewriting...")
        return "rewrite"


def _finalize(state: PipelineState) -> dict:
    """Set the final output from the approved draft."""
    logger.info("Finalizing output")
    return {"final_output": state.draft}


def _rewrite(state: PipelineState) -> dict:
    """Increment iteration counter for rewrite loop."""
    new_iteration = state.iteration + 1
    logger.info(f"Starting rewrite iteration {new_iteration}")
    return {"iteration": new_iteration}


def build_graph() -> StateGraph:
    """Build the LangGraph pipeline.

    Pipeline flow:
    Knowledge -> Research -> Strategy -> Founder Brain -> Story Architect
    -> Platform Writer -> Review -> (approve | rewrite loop)

    Returns:
        Compiled StateGraph ready for execution.
    """
    logger.info("Building LangGraph pipeline")

    graph = StateGraph(PipelineState)

    # Add nodes
    graph.add_node("knowledge", knowledge_agent.run)
    graph.add_node("research", research_agent.run)
    graph.add_node("strategy", strategy_agent.run)
    graph.add_node("founder_brain", founder_brain_agent.run)
    graph.add_node("story_architect", story_architect_agent.run)
    graph.add_node("platform_writer", platform_writer_agent.run)
    graph.add_node("review", review_agent.run)
    graph.add_node("rewrite", _rewrite)
    graph.add_node("finalize", _finalize)

    # Define edges
    graph.set_entry_point("knowledge")
    graph.add_edge("knowledge", "research")
    graph.add_edge("research", "strategy")
    graph.add_edge("strategy", "founder_brain")
    graph.add_edge("founder_brain", "story_architect")
    graph.add_edge("story_architect", "platform_writer")
    graph.add_edge("platform_writer", "review")

    # Conditional edge from review
    graph.add_conditional_edges(
        "review",
        _should_continue_review,
        {
            "finalize": "finalize",
            "rewrite": "rewrite",
        },
    )

    # Rewrite loops back to platform_writer
    graph.add_edge("rewrite", "platform_writer")
    graph.add_edge("finalize", END)

    return graph


def run_pipeline(topic: str) -> PipelineState:
    """Execute the full content pipeline.

    Args:
        topic: The content topic to create about.

    Returns:
        Final PipelineState with all outputs.
    """
    logger.info(f"=== Starting Pipeline: {topic} ===")

    graph = build_graph()
    compiled = graph.compile()

    initial_state = PipelineState(topic=topic)
    final_state = compiled.invoke(initial_state)

    # Convert dict result back to PipelineState
    result = PipelineState(**final_state)

    logger.info(f"=== Pipeline Complete ===")
    logger.info(f"Final output length: {len(result.final_output)} chars")
    logger.info(f"Review score: {result.review.overall_score}/10")
    logger.info(f"Total iterations: {result.iteration}")

    return result
