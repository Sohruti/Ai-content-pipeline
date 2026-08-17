"""Prompt loading service for the 2OS Content Operating System."""

from pathlib import Path

from app.config.settings import BASE_DIR
from app.services.logger import get_logger

logger = get_logger(__name__)

PROMPTS_DIR = BASE_DIR / "prompts"


def load_prompt(name: str) -> str:
    """Load a prompt template by name from the prompts directory.

    Args:
        name: Prompt file name without extension (e.g., 'knowledge', 'research').

    Returns:
        The prompt template content as a string.

    Raises:
        FileNotFoundError: If the prompt file does not exist.
    """
    prompt_path = PROMPTS_DIR / f"{name}.md"

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {prompt_path}")

    content = prompt_path.read_text(encoding="utf-8")
    logger.info(f"Loaded prompt: {name} ({len(content)} chars)")
    return content
