"""Founder Intelligence Pipeline - Entry Point.

Run this script to refresh the founder knowledge base:

    python founder_ingestion.py

This fetches the founder's latest LinkedIn posts, analyzes their
writing patterns, and generates the knowledge base used by Founder Brain.

The pipeline is completely independent from the main content pipeline.
"""

import sys

from rich.console import Console
from rich.panel import Panel

from app.services.founder_ingestion import run_ingestion
from app.services.logger import get_logger

logger = get_logger(__name__)
console = Console()


def main():
    """Main entry point for founder ingestion."""
    console.print(
        Panel.fit(
            "[bold cyan]Founder Intelligence Pipeline[/bold cyan]\n"
            "[dim]Analyzing founder writing patterns for authentic content[/dim]",
            border_style="blue",
        )
    )

    # Parse arguments
    platform = "linkedin"
    force = False
    limit = 20

    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg in ("--platform", "-p") and i + 1 < len(args):
            platform = args[i + 1]
        elif arg in ("--force", "-f"):
            force = True
        elif arg in ("--limit", "-l") and i + 1 < len(args):
            limit = int(args[i + 1])
        elif arg in ("--help", "-h"):
            console.print("\n[bold]Usage:[/bold]")
            console.print("  python founder_ingestion.py [OPTIONS]\n")
            console.print("[bold]Options:[/bold]")
            console.print("  --platform, -p  Platform to fetch from (default: linkedin)")
            console.print("  --force, -f     Re-analyze even if no new posts")
            console.print("  --limit, -l     Maximum posts to fetch (default: 20)")
            console.print("  --help, -h      Show this help\n")
            return

    console.print(f"\n[bold]Platform:[/bold] {platform}")
    console.print(f"[bold]Limit:[/bold] {limit}")
    console.print(f"[bold]Force:[/bold] {force}\n")

    try:
        success = run_ingestion(platform=platform, force=force, limit=limit)

        if success:
            console.print("\n[bold green]Pipeline completed successfully![/bold green]")
            console.print("[dim]Founder Brain will now use the updated knowledge base.[/dim]")
        else:
            console.print("\n[bold red]Pipeline failed. Check logs for details.[/bold red]")
            sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]Pipeline cancelled by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]")
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
