"""Single wrapper for every Ollama call in this project.

Callers never talk to Ollama directly and never handle LLM failures
themselves -- ask_llm() always returns a string, even if the model
hangs, errors, or Ollama isn't running.
"""

import requests
from loguru import logger

from app.config import settings

FALLBACK_MESSAGE = "Sorry, I'm having trouble processing that right now. Please try again."


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
