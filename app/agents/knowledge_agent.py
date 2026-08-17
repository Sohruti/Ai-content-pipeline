"""Knowledge Agent - reads and synthesizes company knowledge."""

from app.models.state import KnowledgeContext, PipelineState
from app.services.llm import invoke_llm
from app.services.logger import get_logger
from app.services.prompt_loader import load_prompt

logger = get_logger(__name__)


def _read_data_sources() -> str:
    """Read all available markdown data sources."""
    from app.config.settings import DATA_SOURCES

    contents = []
    for name, path in DATA_SOURCES.items():
        if path.exists():
            content = path.read_text(encoding="utf-8")
            contents.append(f"## {name.replace('_', ' ').title()}\n\n{content}")
            logger.info(f"Read data source: {name} ({len(content)} chars)")

    return "\n\n---\n\n".join(contents) if contents else "No data sources available."


def run(state: PipelineState) -> dict:
    """Execute the Knowledge Agent.

    Reads company data files and synthesizes knowledge context.
    """
    logger.info("=== Knowledge Agent Starting ===")

    raw_data = _read_data_sources()
    system_prompt = load_prompt("knowledge")

    user_prompt = f"""Analyze the following company knowledge and provide a structured summary.

## Company Data Sources

{raw_data}

Provide a comprehensive knowledge context covering company overview, product summary, founder voice, customer insights, and blog highlights."""

    response = invoke_llm(system_prompt, user_prompt)

    knowledge = KnowledgeContext(
        company_overview=response,
        product_summary="",
        founder_voice="",
        customer_insights="",
        blog_highlights="",
        raw_context=raw_data,
    )

    logger.info("=== Knowledge Agent Complete ===")
    return {"knowledge": knowledge}
