"""LLM service with Groq (primary) and Google Gemini (fallback)."""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config.settings import (
    GROQ_API_KEY,
    GROQ_MODEL,
    GOOGLE_API_KEY,
    GOOGLE_MODEL,
)
from app.services.logger import get_logger

logger = get_logger(__name__)

_groq_llm: ChatGroq | None = None
_google_llm: ChatGoogleGenerativeAI | None = None
_use_fallback: bool = False


def _get_groq_llm() -> ChatGroq:
    """Get or create the Groq LLM client."""
    global _groq_llm
    if _groq_llm is None:
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set. Check your .env file.")
        _groq_llm = ChatGroq(
            groq_api_key=GROQ_API_KEY,
            model_name=GROQ_MODEL,
            temperature=0.7,
            max_tokens=2048,
        )
        logger.info(f"Groq LLM initialized: {GROQ_MODEL}")
    return _groq_llm


def _get_google_llm() -> ChatGoogleGenerativeAI:
    """Get or create the Google Gemini LLM client (fallback)."""
    global _google_llm
    if _google_llm is None:
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not set. Check your .env file.")
        _google_llm = ChatGoogleGenerativeAI(
            google_api_key=GOOGLE_API_KEY,
            model=GOOGLE_MODEL,
            temperature=0.7,
            max_output_tokens=2048,
        )
        logger.info(f"Google Gemini fallback LLM initialized: {GOOGLE_MODEL}")
    return _google_llm


def _invoke_with_fallback(messages: list[SystemMessage | HumanMessage]) -> str:
    """Try Groq first, fall back to Google Gemini on rate limit errors.

    Args:
        messages: List of chat messages.

    Returns:
        The LLM response content.

    Raises:
        Exception: If both providers fail.
    """
    global _use_fallback

    # If we already know Groq is rate-limited, skip straight to fallback
    if not _use_fallback:
        try:
            llm = _get_groq_llm()
            response = llm.invoke(messages)
            logger.info(f"Groq response: {len(response.content)} chars")
            return response.content
        except Exception as e:
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ["rate", "limit", "429", "quota", "too many"]):
                logger.warning(f"Groq rate limited, switching to Google Gemini: {e}")
                _use_fallback = True
            else:
                raise

    # Fallback to Google Gemini
    try:
        llm = _get_google_llm()
        response = llm.invoke(messages)
        logger.info(f"Google Gemini ({GOOGLE_MODEL}) response: {len(response.content)} chars")
        return response.content
    except Exception as e:
        logger.error(f"Google Gemini also failed: {e}")
        raise


def invoke_llm(system_prompt: str, user_prompt: str) -> str:
    """Invoke the LLM with a system and user prompt.

    Tries Groq first. If rate-limited, automatically falls back to
    Google Gemini.

    Args:
        system_prompt: System instruction for the LLM.
        user_prompt: User query or context.

    Returns:
        The LLM's response as a string.
    """
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    provider = "Google Gemini" if _use_fallback else "Groq"
    logger.info(f"Invoking LLM ({provider}) - system: {len(system_prompt)} chars, user: {len(user_prompt)} chars")

    content = _invoke_with_fallback(messages)
    logger.info(f"LLM response: {len(content)} chars")
    return content
