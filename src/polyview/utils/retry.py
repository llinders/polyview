import asyncio
import functools
import logging
import re
import time

from google.api_core.exceptions import ResourceExhausted

logger = logging.getLogger(__name__)

# langchain_google_genai has an internal retry delay which causes discrepancy with the set delay time
# Delay is adjusted with the below constant to compensate
LANGCHAIN_INTERNAL_RETRY_DELAY = 2  # Observed internal delay from logs


class _RetryHandler:
    """A helper class to manage the state and logic of retrying."""

    def __init__(self, max_retries, fallback_delay):
        self.max_retries = max_retries
        self.fallback_delay = fallback_delay
        self.retries = 0

    def handle_exception(self, e: Exception) -> int:
        """
        Processes the exception, calculates delay, and returns it.
        Raises the exception if max retries are exceeded.
        """
        self.retries += 1
        if self.retries >= self.max_retries:
            logger.error(
                f"API rate limit exceeded. Max retries ({self.max_retries}) reached. Raising exception."
            )
            raise e

        delay = self._calculate_delay(e)
        adjusted_delay = max(0, delay - LANGCHAIN_INTERNAL_RETRY_DELAY)
        logger.warning(
            f"API rate limit exceeded. Waiting for {adjusted_delay} seconds before retry {self.retries}/{self.max_retries}."
        )
        return adjusted_delay

    def _calculate_delay(self, e: Exception) -> int:
        """Extracts the retry delay from the exception message."""
        error_message = str(e)
        logger.debug(f"Full ResourceExhausted error message: {error_message}")
        match = re.search(r"retry_delay {\s*seconds: (\d+)\s*}", error_message)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, TypeError):
                logger.warning(
                    "Could not parse retry-after value from exception. Using fallback delay."
                )
        return self.fallback_delay


def gemini_api_delayed_retry(max_retries=3, fallback_delay_seconds=61):
    """
    A decorator to handle Gemini API rate limiting by retrying with a dynamic
    delay. Supports both sync and async functions.
    """

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            handler = _RetryHandler(max_retries, fallback_delay_seconds)
            while True:
                try:
                    return await func(*args, **kwargs)
                except ResourceExhausted as e:
                    delay = handler.handle_exception(e)
                    await asyncio.sleep(delay)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            handler = _RetryHandler(max_retries, fallback_delay_seconds)
            while True:
                try:
                    return func(*args, **kwargs)
                except ResourceExhausted as e:
                    delay = handler.handle_exception(e)
                    time.sleep(delay)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator
