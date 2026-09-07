"""
LLM / AI Provider — External Service Integration.
Handles generative AI text and chat completions with fallback and error isolation.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from src.config import Settings, setup_logger
from src.helpers import ExternalServiceError

logger = setup_logger(Settings.LOG_DIR / "provider.log", name="app.providers.llm")


def is_llm_configured() -> bool:
    """Check whether an LLM API key or endpoint is configured in Settings."""
    api_key = getattr(Settings, "LLM_API_KEY", None) or getattr(Settings, "OPENAI_API_KEY", None)
    return bool(api_key)


async def generate_text(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
) -> str:
    """
    Generates text completion asynchronously.
    In development mode or when no API key is set, returns a safe simulated response.
    """
    resolved_model = model or getattr(Settings, "LLM_MODEL", "gpt-4o-mini")

    if not is_llm_configured() or Settings.is_development:
        logger.info(
            f"[DEV LLM DISPATCH] Model: {resolved_model} | Temp: {temperature}\n"
            f"System: {system_prompt}\nPrompt: {prompt[:100]}..."
        )
        # Non-blocking async simulation
        await asyncio.sleep(0.05)
        return f"[Simulated response for: {prompt[:50]}...]"

    # Production integration template (e.g. httpx async client or official SDK)
    try:
        # Template hook: insert actual OpenAI/Anthropic/Gemini client execution here
        await asyncio.sleep(0.1)
        return "Generated production completion"
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        raise ExternalServiceError("LLM", f"Generation failed: {e}")
