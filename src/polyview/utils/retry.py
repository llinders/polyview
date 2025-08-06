import functools
import logging
import re
import time

from google.api_core.exceptions import ResourceExhausted

logger = logging.getLogger(__name__)


def gemini_api_delayed_retry(max_retries=3, fallback_delay_seconds=61):
    """
    A decorator to handle Gemini API rate limiting by retrying with a dynamic
    delay based on the API's feedback.

    Args:
        max_retries (int): The maximum number of times to retry the function.
        fallback_delay_seconds (int): The number of seconds to wait if the API
                                      error response does not specify a delay.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except ResourceExhausted as e:
                    retries += 1
                    if retries >= max_retries:
                        logger.error(
                            f"API rate limit exceeded. Max retries ({max_retries}) reached. Raising exception."
                        )
                        raise e

                    delay = fallback_delay_seconds
                    # Try to extract the retry delay from the exception message
                    error_message = str(e)
                    match = re.search(
                        r"retry_delay {\s*seconds: (\d+)\s*}", error_message
                    )
                    if match:
                        try:
                            delay = int(match.group(1))
                            logger.info(
                                f"API provided specific wait time: {delay} seconds."
                            )
                        except (ValueError, TypeError):
                            logger.warning(
                                "Could not parse retry-after value from exception. Using fallback delay."
                            )

                    logger.warning(
                        f"API rate limit exceeded. Waiting for {delay} seconds before retry {retries}/{max_retries}."
                    )
                    time.sleep(delay)

        return wrapper

    return decorator
