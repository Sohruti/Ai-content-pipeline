"""Research Agent - gathers external context via Tavily search."""

from app.models.state import PipelineState, ResearchSummary
from app.services.llm import invoke_llm
from app.services.logger import get_logger
from app.services.prompt_loader import load_prompt

logger = get_logger(__name__)


def _tavily_search(query: str) -> str:
    """Perform a Tavily search and return results as text."""
    try:
        from tavily import TavilyClient
        from app.config.settings import TAVILY_API_KEY

        if not TAVILY_API_KEY:
            logger.warning("TAVILY_API_KEY not set, skipping web search")
            return "Web search not available - TAVILY_API_KEY not configured."

        client = TavilyClient(api_key=TAVILY_API_KEY)
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_answer=True,
        )

        results = []
        if response.get("answer"):
            results.append(f"**AI Answer:** {response['answer']}")

        for item in response.get("results", []):
            title = item.get("title", "")
            content = item.get("content", "")
            url = item.get("url", "")
            results.append(f"**{title}**\n{content}\nSource: {url}")

        return "\n\n".join(results) if results else "No search results found."

    except Exception as e:
        logger.error(f"Tavily search failed: {e}")
        return f"Search error: {str(e)}"


def run(state: PipelineState) -> dict:
    """Execute the Research Agent.

    Searches for external context related to the content topic.
    """
    logger.info(f"=== Research Agent Starting === Topic: {state.topic}")

    search_results = _tavily_search(state.topic)

    system_prompt = load_prompt("research")
    user_prompt = f"""Research Topic: {state.topic}

## Search Results

{search_results}

## Company Knowledge Context

{state.knowledge.company_overview[:1000] if state.knowledge.company_overview else "No company context available."}

Analyze this information and provide a structured research summary focused on business implications for Enterprise AI."""

    response = invoke_llm(system_prompt, user_prompt)

    research = ResearchSummary(
        topic=state.topic,
        industry_trends=response,
        ai_news="",
        competitor_insights="",
        market_context="",
        raw_research=search_results,
    )

    logger.info("=== Research Agent Complete ===")
    return {"research": research}
