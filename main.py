"""2OS GTM Content Operating System - Main Entry Point."""

import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from app.config.settings import OUTPUT_DIR
from app.graphs.pipeline import run_pipeline
from app.services.logger import get_logger

logger = get_logger(__name__)
console = Console()


def save_outputs(state, topic: str) -> None:
    """Save all pipeline outputs to the outputs directory."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUTPUT_DIR / f"{timestamp}_{topic.replace(' ', '_').lower()}"
    run_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "research.md": f"# Research Summary\n\n**Topic:** {state.topic}\n\n## Industry Trends\n\n{state.research.industry_trends}\n\n## Raw Research\n\n{state.research.raw_research}",
        "strategy.md": f"# Content Strategy\n\n**Topic:** {state.topic}\n\n## Business Angle\n\n{state.strategy.business_angle}\n\n## Target Audience\n\n{state.strategy.target_audience}\n\n## Messaging\n\n{state.strategy.messaging}\n\n## Content Goal\n\n{state.strategy.content_goal}\n\n## CTA\n\n{state.strategy.cta}\n\n## Tone\n\n{state.strategy.tone}",
        "story.md": f"# Story Blueprint\n\n**Topic:** {state.topic}\n\n## Hook\n\n{state.story.hook}\n\n## Problem\n\n{state.story.problem}\n\n## Insight\n\n{state.story.insight}\n\n## Business Lesson\n\n{state.story.business_lesson}\n\n## CTA\n\n{state.story.cta}\n\n## Narrative Arc\n\n{state.story.narrative_arc}",
        "linkedin_post.md": f"# LinkedIn Post\n\n**Topic:** {state.topic}\n\n---\n\n{state.final_output}",
        "review.md": f"# Review Report\n\n**Topic:** {state.topic}\n\n## Scores\n\n- Founder Voice: {state.review.founder_voice_score}/10\n- Business-First: {state.review.business_first_score}/10\n- Readability: {state.review.readability_score}/10\n- Authenticity: {state.review.authenticity_score}/10\n- CXO Relevance: {state.review.cxo_relevance_score}/10\n- **Overall: {state.review.overall_score}/10**\n\n## Approved: {state.review.approved}\n\n## Feedback\n\n{state.review.feedback}",
    }

    for filename, content in files.items():
        filepath = run_dir / filename
        filepath.write_text(content, encoding="utf-8")
        logger.info(f"Saved: {filepath}")

    console.print(f"\n[green]Outputs saved to:[/green] {run_dir}")
    return run_dir


def display_results(state) -> None:
    """Display pipeline results in a formatted table."""
    table = Table(title="Pipeline Results", show_header=True, header_style="bold magenta")
    table.add_column("Stage", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details")

    table.add_row("Knowledge", "Complete", f"{len(state.knowledge.company_overview)} chars")
    table.add_row("Research", "Complete", f"{len(state.research.industry_trends)} chars")
    table.add_row("Strategy", "Complete", state.strategy.content_type)
    table.add_row("Founder Brain", "Complete", f"{len(state.founder_context)} chars")
    table.add_row("Story Architect", "Complete", f"Hook: {state.story.hook[:50]}...")
    table.add_row("Platform Writer", "Complete", f"{len(state.draft)} chars")
    table.add_row(
        "Review",
        "Approved" if state.review.approved else "Rejected",
        f"Score: {state.review.overall_score}/10 (Iteration {state.iteration})",
    )

    console.print(table)


def main():
    """Main entry point for the 2OS Content Operating System."""
    console.print(
        Panel.fit(
            "[bold cyan]2OS GTM Content Operating System[/bold cyan]\n"
            "[dim]Enterprise AI Content Pipeline[/dim]",
            border_style="blue",
        )
    )

    # Default topic for demo
    topic = "Private by Architecture"
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])

    console.print(f"\n[bold]Topic:[/bold] {topic}\n")

    try:
        state = run_pipeline(topic)
        display_results(state)
        run_dir = save_outputs(state, topic)

        # Print the final LinkedIn post
        console.print("\n" + "=" * 60)
        console.print("[bold green]FINAL LINKEDIN POST[/bold green]")
        console.print("=" * 60 + "\n")
        console.print(state.final_output)
        console.print("\n" + "=" * 60)

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
