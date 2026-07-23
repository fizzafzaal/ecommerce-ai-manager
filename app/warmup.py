"""Pre-load the language model so the first real reply isn't a cold start.

phi is loaded into memory lazily on the first request, which makes that
first reply slow (~30-40s). Running this once before a demo pays that
cost up front, in private, so live replies are as fast as they get.

The launcher runs this automatically; you can also run it by hand:
    python -m app.warmup
"""

import sys

from app.config import settings
from app.llm import FALLBACK_MESSAGE, ask_llm


def warmup() -> None:
    if not settings.use_llm:
        print("USE_LLM is false (safe mode) -- no model to warm up. Nothing to do.")
        return

    print(f"Warming up model '{settings.llm_model}' -- loading it into memory...")
    reply = ask_llm("Say OK", max_tokens=5)

    if reply == FALLBACK_MESSAGE:
        print(
            "Warning: the model did not respond. Is Ollama running?\n"
            "Start it, then try again (the launcher does this for you)."
        )
        sys.exit(1)

    print("Model is loaded and ready. Replies will now be as fast as this hardware allows.")


if __name__ == "__main__":
    warmup()
