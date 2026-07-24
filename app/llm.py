"""Single wrapper for every Ollama call in this project.

Callers never talk to Ollama directly and never handle LLM failures
themselves -- ask_llm() always returns a string, even if the model
hangs, errors, or Ollama isn't running.
"""

from functools import lru_cache

import requests
from loguru import logger

from app.config import settings

FALLBACK_MESSAGE = "Sorry, I'm having trouble processing that right now. Please try again."


@lru_cache(maxsize=1)
def _groq_client():
    from groq import Groq

    return Groq(api_key=settings.groq_api_key)


def generate_text(prompt: str, max_tokens: int = 300, temperature: float = 0.7) -> str:
    """Generate free-form text for a single prompt (e.g. marketing copy).

    Uses Groq when a key is configured (fast, higher quality), otherwise the
    local phi model. Never raises -- returns FALLBACK_MESSAGE on failure.
    """
    if settings.groq_enabled:
        try:
            resp = _groq_client().chat.completions.create(
                model=settings.groq_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=30,
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as e:
            logger.error(f"Groq generate_text failed, falling back to phi: {e}")
    return ask_llm(prompt, max_tokens=max_tokens)


def ask_llm(
    prompt: str,
    max_tokens: int = settings.max_tokens,
    timeout: int | None = None,
) -> str:
    """Send a prompt to the local Ollama model and return its reply.

    `timeout` lets a caller cap a specific call more tightly than the
    global default (e.g. intent detection wants to give up quickly and
    fall back to keywords rather than block on a slow cold start).

    On timeout, connection failure, or an unexpected response shape,
    logs the error and returns FALLBACK_MESSAGE instead of raising --
    per the "every LLM call needs a fallback" rule, a slow/broken model
    should never crash the request.
    """
    timeout = timeout if timeout is not None else settings.llm_timeout_seconds
    try:
        response = requests.post(
            f"{settings.ollama_base_url}/api/generate",
            json={
                "model": settings.llm_model,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": max_tokens},
            },
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()["response"].strip()
    except (requests.exceptions.RequestException, KeyError, ValueError) as e:
        logger.error(f"LLM call failed: {e}")
        return FALLBACK_MESSAGE
