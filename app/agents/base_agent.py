"""Shared parent class for every agent.

Subclasses only implement process(). run() wraps that call with timing,
logging, and a guaranteed timeout + fallback, so a hung or broken agent
can never crash the request -- callers always get a dict back.
"""

import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from typing import Any

from loguru import logger


class BaseAgent(ABC):
    name: str = "base_agent"
    timeout_seconds: float = 30.0

    @abstractmethod
    def process(self, **kwargs) -> dict[str, Any]:
        """Agent-specific logic. Implemented by each subclass."""

    def run(self, **kwargs) -> dict[str, Any]:
        """Call process() with a timeout, logging, and a safe fallback."""
        start = time.monotonic()
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self.process, **kwargs)
                result = future.result(timeout=self.timeout_seconds)
            logger.info(f"{self.name} succeeded in {time.monotonic() - start:.2f}s")
            return result
        except FutureTimeoutError:
            logger.error(f"{self.name} timed out after {self.timeout_seconds}s")
            return self.fallback("timeout")
        except Exception as e:
            logger.error(f"{self.name} failed after {time.monotonic() - start:.2f}s: {e}")
            return self.fallback(str(e))

    def fallback(self, reason: str) -> dict[str, Any]:
        """Safe default result when process() times out or raises. Subclasses may override."""
        return {"success": False, "error": reason}
